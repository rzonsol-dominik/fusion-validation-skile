# 06 - Withdrawal System Validation

## Cel
Weryfikacja systemu wyplat: instant withdrawal fuses, scheduled withdrawals, WithdrawManager.

---

## CRITICAL

### WS-001: Instant Withdrawal Fuses Configured
- **Warunek**: Instant withdrawal fuses sa skonfigurowane dla kazdego marketu z ktorego vault moze musiec wyplacic
- **Jak sprawdzic**: `PlasmaVaultGovernance.getInstantWithdrawalFuses()`
- **Oczekiwany wynik**: Niepusta lista fuse'ow (jesli vault ma assety w marketach)
- **Uwagi**: BEZ instant withdrawal fuses uzytkownik NIE MOZE wyplacic assetow zdeponowanych w protokolach

### WS-002: Instant Withdrawal Fuses Order
- **Warunek**: Kolejnosc fuse'ow jest optymalna (najtansza/najplynniejsza najpierw)
- **Jak sprawdzic**: `getInstantWithdrawalFuses()` + analiza kolejnosci
- **Oczekiwany wynik**:
  1. Najpierw: ERC20 vault balance (najtanszy)
  2. Potem: Najbardziej plynne markety (Aave, Compound)
  3. Na koncu: Mniej plynne (LP pozycje, staking)
- **Uwagi**: Zla kolejnosc = wyzszy gas, gorsze wykonanie

### WS-003: Instant Withdrawal Fuses Parameters
- **Warunek**: Parametry kazdego instant withdrawal fuse sa poprawne
- **Jak sprawdzic**: `getInstantWithdrawalFusesParams(fuse, index)` dla kazdego fuse
- **Oczekiwany wynik**:
  - params[0] = zarezerwowany na kwote (ustawiany dynamicznie)
  - params[1+] = specyficzne parametry fuse (np. adresy assetow, market IDs)
- **Uwagi**: Bledne parametry = withdrawal failuje

### WS-004: Instant Withdrawal Fuses Support IFuseInstantWithdraw
- **Warunek**: Kazdy fuse w liscie implementuje IFuseInstantWithdraw
- **Jak sprawdzic**: Sprawdz czy fuse ma `instantWithdraw(bytes32[])` method
- **Oczekiwany wynik**: Wszystkie fuse supportuja interfejs
- **Uwagi**: Fuse bez tego interfejsu nie bedzie uzywany do wyplat

### WS-005: Withdrawal Coverage
- **Warunek**: Instant withdrawal fuses pokrywaja WSZYSTKIE markety w ktorych vault trzyma assety
- **Jak sprawdzic**: Porownaj markety z balance > 0 z marketami pokrytymi przez instant withdrawal fuses
- **Oczekiwany wynik**: Kazdy market z assetami ma odpowiedni withdrawal fuse
- **Uwagi**: Market bez withdrawal fuse = locked funds (assety niedostepne do wyplaty)

### WS-006: WithdrawManager Connected to Vault
- **Warunek**: WithdrawManager jest poprawnie polaczony z vaultem
- **Jak sprawdzic**: Sprawdz storage vaulta + AccessManager role TECH_WITHDRAW_MANAGER_ROLE
- **Oczekiwany wynik**: WithdrawManager ma TECH_WITHDRAW_MANAGER_ROLE i jest zapisany w vault

---

## HIGH

### WS-010: Withdraw Window Configuration
- **Warunek**: Withdraw window jest skonfigurowany sensownie
- **Jak sprawdzic**: `WithdrawManager.getWithdrawWindow()`
- **Oczekiwany wynik**: Rozsadna wartosc (np. 1 godzina - 7 dni)
- **Uwagi**: Za krotki = uzytkownicy nie zdzaza; za dlugi = capital inefficiency

### WS-011: Request Fee Configuration
- **Warunek**: Request fee jest sensowna
- **Jak sprawdzic**: Odczyt request fee z WithdrawManager
- **Oczekiwany wynik**: Wartosc w WAD (np. 1e15 = 0.1%), musi byc < 100%
- **Uwagi**: Za wysoki fee odstraszy uzytkownikow

### WS-012: Withdraw Fee Configuration
- **Warunek**: Withdraw fee jest sensowna
- **Jak sprawdzic**: Odczyt withdraw fee z WithdrawManager
- **Oczekiwany wynik**: Wartosc w WAD, musi byc < 100%
- **Uwagi**: Stosowana do unallocated withdrawals

### WS-013: ALPHA Can Release Funds
- **Warunek**: Konto z ALPHA_ROLE moze wywolac releaseFunds()
- **Jak sprawdzic**: Sprawdz function-role mapping w AccessManager
- **Oczekiwany wynik**: releaseFunds() wymaga ALPHA_ROLE
- **Uwagi**: Bez mozliwosci release = scheduled withdrawals nie dzialaja

### WS-014: Withdrawal Attempt Limit
- **Warunek**: REDEEM_ATTEMPTS (10) jest wystarczajacy dla liczby marketow
- **Jak sprawdzic**: Ilosc instant withdrawal fuses vs REDEEM_ATTEMPTS constant
- **Oczekiwany wynik**: Ilosc fuses <= 10
- **Uwagi**: Vault probuje max 10 razy wyplacic z roznych fuse'ow

### WS-015: Withdrawal Fuse Duplicate Handling
- **Warunek**: Ten sam fuse moze wystapic wielokrotnie z roznymi parametrami
- **Jak sprawdzic**: Sprawdz czy sa duplikaty w getInstantWithdrawalFuses()
- **Oczekiwany wynik**: Duplikaty sa dopuszczalne (rozne params dla tego samego fuse)
- **Uwagi**: Np. AaveV3SupplyFuse moze byc 2x - raz dla USDC, raz dla DAI

---

## MEDIUM

### WS-020: Withdrawal Gas Estimation
- **Warunek**: Withdrawal z najdluzszej sciezki miesci sie w gas limit
- **Jak sprawdzic**: Estymacja gas dla worst-case withdrawal
- **Oczekiwany wynik**: Gas < block gas limit
- **Uwagi**: Zbyt wiele fuse'ow w chain = withdrawal moze failowac

### WS-021: Slippage on Withdrawal
- **Warunek**: DEFAULT_SLIPPAGE_IN_PERCENTAGE (2%) jest akceptowalny
- **Jak sprawdzic**: Stala w kontrakcie
- **Oczekiwany wynik**: 2% jest sensowne dla danej strategii
- **Uwagi**: Vault probuje wyplacic `amount + 10` (WITHDRAW_FROM_MARKETS_OFFSET) jako cushion

### WS-022: Last Release Funds Timestamp
- **Warunek**: Na produkcji lastReleaseFundsTimestamp jest aktualny
- **Jak sprawdzic**: `WithdrawManager.getLastReleaseFundsTimestamp()`
- **Oczekiwany wynik**: Niedawny timestamp (jesli vault jest aktywny)
