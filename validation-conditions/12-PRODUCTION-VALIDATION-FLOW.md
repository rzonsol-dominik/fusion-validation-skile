# 12 - Production Validation Flow

## Cel
Kolejnosc walidacji na produkcji. Krok po kroku jak sprawdzic vault.

---

## FAZA 1: Identyfikacja Vaulta

```
INPUT: Adres PlasmaVault na produkcji
```

### Krok 1.1: Podstawowe dane
```
vault.asset()                     → underlying token
vault.name()                      → share token name
vault.symbol()                    → share token symbol
vault.decimals()                  → decimals (asset + 2)
vault.totalSupply()               → total shares
vault.totalAssets()               → total assets under management
```

### Krok 1.2: Kluczowe adresy
```
PlasmaVaultGovernance.getAccessManagerAddress()      → AccessManager
PlasmaVaultGovernance.getPriceOracleMiddleware()      → PriceOracle
PlasmaVaultGovernance.getRewardsClaimManagerAddress() → RewardsClaimManager
WithdrawManager address (z vault storage)             → WithdrawManager
Implementation slot read                              → Implementation contract
PlasmaVaultBase address (z vault storage)             → Base extension
```

---

## FAZA 2: Access Control (02-ACCESS-CONTROL.md)

### Krok 2.1: Role krytyczne
```
Dla kazdej roli z tabeli:
  AccessManager.hasRole(roleId, expectedAddress) → true/false

Sprawdz:
  - ADMIN_ROLE (0) → multisig
  - OWNER_ROLE (1) → multisig
  - GUARDIAN_ROLE (2) → emergency responder
  - ATOMIST_ROLE (100) → governance
  - ALPHA_ROLE (200) → executor bot
  - TECH_PLASMA_VAULT_ROLE (3) → only vault
```

### Krok 2.2: Function mappings
```
Dla kazdej publicznej funkcji vaulta:
  AccessManager.getTargetFunctionRole(vault, selector) → roleId
  Porownaj z oczekiwana rola
```

### Krok 2.3: Vault status
```
AccessManager.isTargetClosed(vault) → false (jesli aktywny)
```

---

## FAZA 3: Konfiguracja Marketow (03-MARKET-CONFIGURATION.md)

### Krok 3.1: Lista aktywnych marketow
```
PlasmaVaultGovernance.getActiveMarketsInBalanceFuses() → uint256[]
```

### Krok 3.2: Per market validation
```
Dla kazdego marketId z listy:

  a) Balance fuse:
     PlasmaVaultGovernance.isBalanceFuseSupported(marketId, fuseAddr) → true
     IFuseCommon(fuse).MARKET_ID() == marketId

  b) Substrates:
     PlasmaVaultGovernance.getMarketSubstrates(marketId) → bytes32[]
     Dekoduj i sprawdz poprawnosc adresow/ID

  c) Market balance:
     vault.totalAssetsInMarket(marketId) → uint256
```

### Krok 3.3: Lista fuse'ow
```
PlasmaVaultGovernance.getFuses() → address[]
Dla kazdego fuse:
  IFuseCommon(fuse).MARKET_ID() → marketId
  Sprawdz ze market jest aktywny
```

---

## FAZA 4: Interakcje Miedzy Marketami (04-MARKET-INTERACTIONS.md)

### Krok 4.1: Dependency graph
```
Dla kazdego aktywnego marketId:
  PlasmaVaultGovernance.getDependencyBalanceGraph(marketId) → uint256[]
  Sprawdz kompletnosc (tabela zaleznosci w 04-MARKET-INTERACTIONS.md)
```

### Krok 4.2: Market limits
```
PlasmaVaultGovernance.isMarketsLimitsActivated() → bool

Jesli true:
  Dla kazdego marketId:
    PlasmaVaultGovernance.getMarketLimit(marketId) → uint256 (WAD)
```

---

## FAZA 5: Withdrawal System (06-WITHDRAWAL-SYSTEM.md)

### Krok 5.1: Instant withdrawal fuses
```
PlasmaVaultGovernance.getInstantWithdrawalFuses() → address[]

Dla kazdego fuse i index:
  PlasmaVaultGovernance.getInstantWithdrawalFusesParams(fuse, index) → bytes32[]
  Sprawdz parametry
```

### Krok 5.2: WithdrawManager config
```
WithdrawManager.getWithdrawWindow() → uint256
Request fee i withdraw fee
```

---

## FAZA 6: Fee System (07-FEE-SYSTEM.md)

### Krok 6.1: Fee data
```
PlasmaVaultGovernance.getPerformanceFeeData() → (feeAccount, feeInPercentage)
PlasmaVaultGovernance.getManagementFeeData() → (feeAccount, feeInPercentage, lastUpdateTimestamp)
```

### Krok 6.2: Fee Manager details
```
FeeManager address z fee account
FeeManager recipients and fee splits
Total fee <= max
```

---

## FAZA 7: Price Oracle (08-PRICE-ORACLE.md)

### Krok 7.1: Oracle test
```
Dla kazdego tokena w substrates:
  PriceOracleMiddleware.getAssetPrice(token) → (price, decimals)
  Sprawdz: price > 0, decimals == 18
  Porownaj z rynkowa cena
```

---

## FAZA 8: Balance Tracking (09-BALANCE-TRACKING.md)

### Krok 8.1: Balance consistency check
```
calculated = ERC20(asset).balanceOf(vault)
for each marketId:
    calculated += vault.totalAssetsInMarket(marketId)
if rewardsManager != address(0):
    calculated += rewardsManager.balanceOf()

assert |calculated - vault.totalAssets()| <= tolerance
```

### Krok 8.2: Share price sanity
```
vault.convertToAssets(10 ** vault.decimals()) → ~1 underlying token
vault.convertToShares(10 ** assetDecimals) → ~1e(vault.decimals()) shares
```

---

## FAZA 9: Rewards (10-REWARDS-SYSTEM.md)

### Krok 9.1: Rewards config (jesli uzywany)
```
rewardsManager.getVestingData() → vestingTime, balances
rewardsManager.getRewardsFuses() → registered fuses
rewardsManager.balanceOf() → current vested balance
```

---

## FAZA 10: Smoke Test (opcjonalny)

### Krok 10.1: Test deposit
```
1. Approve underlying token to vault
2. vault.deposit(smallAmount, testAddress)
3. Sprawdz: shares received > 0
4. vault.totalAssets() increased
```

### Krok 10.2: Test withdraw
```
1. vault.withdraw(smallAmount, testAddress, testAddress)
2. Sprawdz: underlying received
3. vault.totalAssets() decreased
```

### Krok 10.3: Test execute (wymaga ALPHA_ROLE)
```
1. Przygotuj FuseAction dla najprostszego marketu
2. vault.execute([action])
3. Sprawdz: totalAssetsInMarket() updated
```

---

## RAPORT KONCOWY

Po zakonczeniu walidacji stworz raport:

```
# Vault Validation Report
- Vault Address: 0x...
- Chain: Ethereum / Arbitrum / Base / ...
- Date: YYYY-MM-DD
- Validator: ...

## Status: PASS / FAIL / PARTIAL

## Critical Issues Found:
- [ ] Issue 1
- [ ] Issue 2

## Warnings:
- [ ] Warning 1

## Conditions Checked:
- [x] VC-001: Underlying Token ✓
- [x] VC-002: Access Manager ✓
- [ ] AC-001: ADMIN_ROLE ✗ (ISSUE: ...)
...

## Recommendations:
1. ...
2. ...
```

---

## AUTOMATYZACJA

Mozliwe jest napisanie skryptu ktory automatycznie sprawdza wiekszosc warunkow:

### Wymagane RPC calls:
- ~10 wywolan na faze 1-2
- ~5 * N wywolan na faze 3 (N = liczba marketow)
- ~3 * M wywolan na faze 5 (M = liczba withdrawal fuses)
- ~K wywolan na faze 7 (K = liczba unikalnych tokenow)

### Narzedzia:
- cast (foundry) do on-chain calls
- Etherscan/Basescan API do weryfikacji kodu
- Custom skrypt w Solidity/Python/TypeScript
