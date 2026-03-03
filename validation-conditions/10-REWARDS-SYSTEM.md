# 10 - Rewards System Validation

## Cel
Weryfikacja systemu nagrod: RewardsClaimManager, reward fuses, vesting, transfers.

---

## Architektura Rewards

```
Protokoly (Aave, Morpho, Compound, etc.)
    │ claim rewards
    ▼
RewardsClaimManager
    │ linear vesting
    │ transferVestedTokensToVault()
    ▼
PlasmaVault (underlying token balance)
```

### Proces:
1. **Claim**: Konto z CLAIM_REWARDS_ROLE wywoluje `claimRewards(FuseAction[])` na vaulcie
2. Vault delegatecall do reward fuses → fuse claimuje rewards z protokolu do RewardsClaimManager
3. **Vesting**: Rewards wchodza w linear vesting (configurable duration)
4. **Transfer**: Vested tokeny sa transferowane do vaulta (updateBalance/transferVestedTokensToVault)
5. **Include in totalAssets**: Vested balance jest wliczony do vault.totalAssets()

---

## CRITICAL

### RW-001: RewardsClaimManager Address
- **Warunek**: Jesli vault claimuje rewards - RewardsClaimManager jest skonfigurowany
- **Jak sprawdzic**: `PlasmaVaultGovernance.getRewardsClaimManagerAddress()`
- **Oczekiwany wynik**: Poprawny adres (nie address(0)) jesli vault uzywa rewards
- **Uwagi**: Bez managera rewards nie moga byc claimowane i vestowane

### RW-002: RewardsClaimManager Underlying Token
- **Warunek**: RewardsClaimManager ma ten sam underlying token co vault
- **Jak sprawdzic**: Sprawdz underlying token w RewardsClaimManager
- **Oczekiwany wynik**: Zgodny z `vault.asset()`
- **Uwagi**: Bledny token = rewards transferowane w zlym tokenie

### RW-003: RewardsClaimManager -> Vault Connection
- **Warunek**: RewardsClaimManager jest polaczony z poprawnym vaultem
- **Jak sprawdzic**: Sprawdz PLASMA_VAULT adres w RewardsClaimManager
- **Oczekiwany wynik**: Adres aktualnego vaulta
- **Uwagi**: Bledne polaczenie = rewards ida do zlego vaulta

### RW-004: Reward Fuses Registered
- **Warunek**: Reward fuses sa zarejestrowane w RewardsClaimManager
- **Jak sprawdzic**: `rewardsClaimManager.getRewardsFuses()`
- **Oczekiwany wynik**: Lista zawiera wszystkie potrzebne reward fuses
- **Uwagi**: Niezarejestrowany fuse = claimRewards() zrevertuje

### RW-005: TECH_REWARDS_CLAIM_MANAGER_ROLE
- **Warunek**: TECH_REWARDS_CLAIM_MANAGER_ROLE jest przypisana do RewardsClaimManager
- **Jak sprawdzic**: `AccessManager.hasRole(601, rewardsClaimManagerAddress)`
- **Oczekiwany wynik**: true
- **Uwagi**: Bez tej roli manager nie moze operowac

---

## HIGH

### RW-010: Vesting Time Configuration
- **Warunek**: Vesting time jest skonfigurowany sensownie
- **Jak sprawdzic**: `rewardsClaimManager.getVestingData()`
- **Oczekiwany wynik**: vestingTime > 0 i rozsadny (np. 7 dni, 30 dni)
- **Uwagi**: 0 = natychmiastowy vesting; zbyt dlugi = rewards sa zamrozone

### RW-011: CLAIM_REWARDS_ROLE Assignment
- **Warunek**: CLAIM_REWARDS_ROLE jest przypisana do oczekiwanego konta (bot/keeper)
- **Jak sprawdzic**: `AccessManager.hasRole(600, address)`
- **Oczekiwany wynik**: Oczekiwane konto claimer bota
- **Uwagi**: Tylko to konto moze claimowac rewards

### RW-012: TRANSFER_REWARDS_ROLE Assignment
- **Warunek**: TRANSFER_REWARDS_ROLE jest przypisana do oczekiwanego konta
- **Jak sprawdzic**: `AccessManager.hasRole(700, address)`
- **Oczekiwany wynik**: Oczekiwane konto
- **Uwagi**: Rola do transferu non-underlying reward tokenow

### RW-013: UPDATE_REWARDS_BALANCE_ROLE Assignment
- **Warunek**: UPDATE_REWARDS_BALANCE_ROLE jest przypisana do oczekiwanego konta
- **Jak sprawdzic**: `AccessManager.hasRole(1100, address)`
- **Oczekiwany wynik**: Oczekiwane konto (keeper/bot)
- **Uwagi**: Potrzebne do aktualizacji balansu rewards w totalAssets

### RW-014: Reward Fuse Protocol Match
- **Warunek**: Reward fuses odpowiadaja protokolom uzywanym przez vault
- **Jak sprawdzic**: Porownaj reward fuses z aktywnymi marketami wedlug tabeli:

| Market / Protokol | Wymagany Reward Claim Fuse |
|-------------------|---------------------------|
| Aave V3/V3 Lido | (Aave rewards via Merkl lub dedykowany) |
| Compound V3 | CompoundV3ClaimFuse |
| Morpho | MorphoClaimFuse |
| Curve gauge | CurveGaugeTokenClaimFuse |
| Aerodrome | AerodromeGaugeClaimFuse |
| Aerodrome Slipstream | AreodromeSlipstreamGaugeClaimFuse |
| Euler V2 | RewardEulerTokenClaimFuse |
| Fluid Instadapp | FluidInstadappClaimFuse lub FluidProofClaimFuse |
| Gearbox V3 | GearboxV3FarmDTokenClaimFuse |
| Merkl (uniwersalny) | MerklClaimFuse |
| Moonwell | MoonwellClaimFuse |
| Ramses | RamsesClaimFuse |
| Stake DAO V2 | StakeDaoV2ClaimFuse |
| Syrup | SyrupClaimFuse |
| Velodrome Superchain | VelodromeSuperchainGaugeClaimFuse |
| Velodrome Slipstream | VelodromeSuperchainSlipstreamGaugeClaimFuse |

- **Oczekiwany wynik**: Kazdy market z rewards ma odpowiedni claim fuse
- **Uwagi**: Brak claim fuse = rewards nie sa claimowane (utrata wartosci). Lacznie 16 typow reward fuse'ow w kodzie

### RW-015: Vesting Balance Correctness
- **Warunek**: balanceOf() w RewardsClaimManager odzwierciedla prawidlowo vested tokens
- **Jak sprawdzic**: `rewardsClaimManager.balanceOf()`
- **Oczekiwany wynik**: Wartosc >= 0 i <= total claimed rewards
- **Uwagi**: Sprawdz formule: `(lastUpdateBalance * elapsed / vestingTime) - transferred`

---

## MEDIUM

### RW-020: Reward Token Handling (non-underlying)
- **Warunek**: Nagrody w tokenach != underlying (np. COMP, AAVE, CRV) sa prawidlowo handlowane
- **Jak sprawdzic**: Sprawdz czy istnieje mechanizm konwersji reward tokenow na underlying
- **Oczekiwany wynik**: Swap fuse lub manual process do konwersji
- **Uwagi**: Rewards w non-underlying tokenach musza byc skonwertowane

### RW-021: Reward Claim Frequency
- **Warunek**: Rewards sa claimowane z rozsadna czestotliwoscia
- **Jak sprawdzic**: Sprawdz eventy claimRewards na produkcji
- **Oczekiwany wynik**: Regularne claimowanie (np. raz dziennie/tygodniowo)
- **Uwagi**: Rzadkie claimowanie = strata na compound effect

### RW-022: Merkle Proof Claims (Morpho, etc.)
- **Warunek**: Dla protokolow z merkle proof claims - proofs sa aktualne
- **Jak sprawdzic**: Weryfikacja ze claimRewards() z aktualnymi proofs dziala
- **Oczekiwany wynik**: Claim nie revertuje
- **Uwagi**: Stare merkle proofs moga byc nieaktualne
