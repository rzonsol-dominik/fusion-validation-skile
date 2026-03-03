# 09 - Balance Tracking Validation

## Cel
Weryfikacja systemu sledzenia balansow: totalAssets, per-market balances, balance fuse correctness.

---

## Formuła totalAssets

```
totalAssets() = vault.balance (ERC20 underlying w vaulcie)
              + totalAssetsInAllMarkets (suma po wszystkich marketach)
              + rewardsClaimManager.balanceOf() (vested rewards)
```

### Proces aktualizacji (PlasmaVaultMarketsLib):
1. Wywolaj `balanceFuse.balanceOf()` → wartosc w USD (18 decimals WAD)
2. Pobierz cene underlying asset z `IPriceOracleMiddleware`
3. Konwertuj: `(balance_usd * 10^asset_decimals) / price_usd`
4. Zaktualizuj delta w `PlasmaVaultLib.getTotalAssetsInMarket(marketId)`
5. Rozwiaz dependencies (zaktualizuj powiazane markety)
6. Waliduj market limits (jesli aktywne)

---

## CRITICAL

### BT-001: totalAssets >= Vault ERC20 Balance
- **Warunek**: totalAssets nie jest mniejszy niz balance ERC20 underlying w vaulcie
- **Jak sprawdzic**: `vault.totalAssets()` >= `ERC20(asset).balanceOf(vault)`
- **Oczekiwany wynik**: totalAssets >= balance (roznica = assety w marketach + rewards)
- **Uwagi**: totalAssets < balance wskazuje na bledna konfiguracje balance fuses

### BT-002: totalAssets Consistency
- **Warunek**: Suma poszczegolnych skladnikow == totalAssets()
- **Jak sprawdzic**:
  ```
  calculated = ERC20(asset).balanceOf(vault)
  for each marketId in activeMarkets:
      calculated += vault.totalAssetsInMarket(marketId)
  if rewardsManager != address(0):
      calculated += rewardsManager.balanceOf()
  assert |calculated - vault.totalAssets()| <= rounding_tolerance
  ```
- **Oczekiwany wynik**: Zgodnosc (tolerancja +-1 na rounding per market)
- **Uwagi**: Niezgodnosc = cos jest nie tak z balance tracking

### BT-003: Per-Market Balance vs Protocol State
- **Warunek**: Kazdy totalAssetsInMarket() odzwierciedla RZECZYWISTY stan na protokole
- **Jak sprawdzic**: Dla kazdego aktywnego marketu porownaj:
  - `vault.totalAssetsInMarket(marketId)` (co vault mysli)
  - Rzeczywisty stan na protokole (np. aToken.balanceOf(vault) na Aave)
- **Oczekiwany wynik**: Roznica < 0.1% (moze byc drobna roznica z powodu accrued interest)
- **Uwagi**: Duza roznica = balance fuse jest bledny lub nieaktualny

### BT-004: Balance Fuse Returns USD in WAD
- **Warunek**: Balance fuse zwraca wartosc w USD z 18 decimals
- **Jak sprawdzic**: Wywolaj `balanceFuse.balanceOf()` i sprawdz skale
- **Oczekiwany wynik**: Wartosc w WAD (np. 1000 USD = 1000 * 1e18)
- **Uwagi**: Bledna skala = totalAssets bedzie o rzedy wielkosci bledny

### BT-005: Share Price Reasonability
- **Warunek**: Cena share (convertToAssets(1e(decimals))) jest rozsadna
- **Jak sprawdzic**: `vault.convertToAssets(10 ** vault.decimals())`
- **Oczekiwany wynik**: Wartosc bliska 1 underlying tokena (z akumulacja zysku w czasie)
- **Uwagi**: Cena share radykalnie != 1 (np. 0 lub 1e30) wskazuje na problem

---

## HIGH

### BT-010: Balance Update Freshness
- **Warunek**: Balansy marketow sa regularnie aktualizowane
- **Jak sprawdzic**: Sprawdz eventy MarketBalancesUpdated lub porownaj z on-chain state
- **Oczekiwany wynik**: Balansy zaktualizowane w ciagu ostatnich 24h (lub czesciej)
- **Uwagi**: Stale balansy = bledna wycena sharesow

### BT-011: Balance After Execute
- **Warunek**: Po execute() balansy dotkientych marketow sa zaktualizowane
- **Jak sprawdzic**: Monitoruj eventy ExecuteFinished
- **Oczekiwany wynik**: Eventy zawieraja zaktualizowane wartosci
- **Uwagi**: Automatycznie realizowane w execute()

### BT-012: Performance Fee Calculation Basis
- **Warunek**: Performance fee jest obliczana na bazie NET total assets (po odjieciu management fee)
- **Jak sprawdzic**: Logika w execute():
  ```
  netTotalAssets = totalAssets() - getUnrealizedManagementFee()
  // ... execute actions ...
  profit = newNetTotalAssets - netTotalAssets
  fee = profit * performanceFeeRate
  ```
- **Oczekiwany wynik**: Fee only on net profit
- **Uwagi**: Wbudowane w kontrakt

### BT-013: Rewards Balance Inclusion
- **Warunek**: Jesli RewardsClaimManager istnieje - jego balance jest wliczony do totalAssets
- **Jak sprawdzic**: `rewardsClaimManager.balanceOf()` > 0 gdy sa vested rewards
- **Oczekiwany wynik**: Wartosci rewards sa wliczone
- **Uwagi**: Brak wliczenia = niedoszacowanie totalAssets

### BT-014: Zero Balance Markets
- **Warunek**: Markety z balance 0 nie znieksztalcaja totalAssets
- **Jak sprawdzic**: Sprawdz czy totalAssetsInMarket() == 0 dla nieuzywanych marketow
- **Oczekiwany wynik**: 0 dla kazdego marketu bez pozycji
- **Uwagi**: Phantom balance = zawyzona wycena

### BT-015: Negative Balance Handling (Borrow)
- **Warunek**: Markety z borrow poprawnie odejmuja debt od supply
- **Jak sprawdzic**: Dla marketow lending z borrow (Aave, Compound, Morpho):
  - Balance fuse powinien zwracac: supply_value - debt_value
  - Jesli net < 0 (wiecej borrowed niz supplied) - sprawdz czy to zamierzone
- **Oczekiwany wynik**: Balance = net position (supply - debt) w USD
- **Uwagi**: Bledne odejmowanie debt = zawyzona wycena

---

## MEDIUM

### BT-020: Rounding Behavior
- **Warunek**: Rounding w konwersjach jest w wlasciwym kierunku
- **Jak sprawdzic**: Sprawdz czy vault zaokragla na korzysc vaulta (nie usera) przy withdraw
- **Oczekiwany wynik**: Shares rounded up, assets rounded down przy withdraw
- **Uwagi**: ERC4626 standard wymaga roundowania na korzysc vaulta

### BT-021: updateMarketsBalances Permission
- **Warunek**: updateMarketsBalances() jest dostepne dla UPDATE_MARKETS_BALANCES_ROLE
- **Jak sprawdzic**: Sprawdz function-role mapping w AccessManager
- **Oczekiwany wynik**: Poprawna rola
- **Uwagi**: Potrzebne do recznej aktualizacji balansow

### BT-022: Interest Accrual Tracking
- **Warunek**: Balance fuses uwzgledniaja narosly interest (aTokens, cTokens)
- **Jak sprawdzic**: Porownaj balance fuse output z aktualnymi aToken/cToken balansami
- **Oczekiwany wynik**: Balance rosi z czasem (interest accrual)
- **Uwagi**: Niektorzy protokoly naliczaja interest dynamicznie

### BT-023: LP Position Valuation
- **Warunek**: LP pozycje (Uniswap V3, Balancer, Curve) sa poprawnie wyceniane
- **Jak sprawdzic**: Porownaj balance fuse output z wartoscia pozycji na DEX
- **Oczekiwany wynik**: Wartosc zblizona do rzeczywistej (z uwzglednieniem fees, IL)
- **Uwagi**: LP valuation jest zlozna - moze byc niedoszacowana o uncollected fees
