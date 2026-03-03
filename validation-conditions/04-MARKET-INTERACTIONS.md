# 04 - Market Interactions Validation

## Cel
Weryfikacja interakcji miedzy marketami: dependency graph, market limits, cross-market balance tracking.

---

## CRITICAL

### MI-001: Dependency Balance Graph Configuration
- **Warunek**: Markety z wzajemnymi zaleznosci maja skonfigurowany dependency graph
- **Jak sprawdzic**: `PlasmaVaultGovernance.getDependencyBalanceGraph(marketId)` dla kazdego marketu
- **Oczekiwany wynik**: Poprawne listy zaleznosci
- **Uwagi**: BEZ dependency graph - balance updates jednego marketu NIE zaktualizuja powiazanych marketow

#### Typowe zaleznosci ktore MUSZA byc skonfigurowane:

| Market | Zalezy od | Dlaczego |
|--------|-----------|----------|
| UNISWAP_SWAP_V3 (swap) | ERC20_VAULT_BALANCE | Swap zmienia balance tokenow w vaulcie |
| UNISWAP_SWAP_V3_POSITIONS | ERC20_VAULT_BALANCE | LP pozycje uzywaja tokenow z vaulta |
| CURVE_POOL | ERC20_VAULT_BALANCE | LP wymaga tokenow |
| CURVE_LP_GAUGE | CURVE_POOL | Gauge stakuje LP tokeny |
| BALANCER_* | ERC20_VAULT_BALANCE | Pool uzywa tokenow |
| AAVE_V3 (z borrow) | ERC20_VAULT_BALANCE | Borrow dodaje tokeny do vaulta |
| MORPHO (z borrow) | ERC20_VAULT_BALANCE | Borrow dodaje tokeny do vaulta |
| GEARBOX_FARM_DTOKEN_V3 | GEARBOX_POOL_V3 | Farm stakuje dTokeny z pool |
| FLUID_INSTADAPP_STAKING | FLUID_INSTADAPP_POOL | Staking uzywa tokenow pool |
| AERODROME gauge | AERODROME liquidity | Gauge stakuje LP tokeny |
| Dowolny swap market | ERC20_VAULT_BALANCE | Swap zmienia balance w vaulcie |

### MI-002: Dependency Graph Completeness
- **Warunek**: WSZYSTKIE wymagane zaleznosci sa w grafie
- **Jak sprawdzic**: Dla kazdego marketu sprawdz getDependencyBalanceGraph() i porownaj z tabela powyzej
- **Oczekiwany wynik**: Kompletny graf zaleznosci
- **Uwagi**: Brakujaca zaleznosc = phantom balance (vault mysli ze ma wiecej/mniej niz w rzeczywistosci)

### MI-003: No Circular Dependencies
- **Warunek**: Graf zaleznosci nie ma cykli
- **Jak sprawdzic**: Traverse grafu DFS - sprawdz brak cykli
- **Oczekiwany wynik**: DAG (directed acyclic graph)
- **Uwagi**: Cykl = potencjalna nieskonczona petla lub bledne obliczenia

### MI-004: Market Limits - Active Status
- **Warunek**: Market limits sa aktywne/nieaktywne zgodnie z zamierzeniem
- **Jak sprawdzic**: `PlasmaVaultGovernance.isMarketsLimitsActivated()`
- **Oczekiwany wynik**: true jesli vault wymaga limitow koncentracji
- **Uwagi**: Bez limitow Alpha moze skoncentrowac 100% w jednym markecie

### MI-005: Market Limits - Values
- **Warunek**: Kazdy market ma ustawiony limit procentowy zgodny z strategia
- **Jak sprawdzic**: `PlasmaVaultGovernance.getMarketLimit(marketId)` dla kazdego marketu
- **Oczekiwany wynik**: Wartosc w WAD (1e18 = 100%), np. 3e17 = 30%
- **Uwagi**: Suma limitow moze byc > 100% (limity to max per market, nie alokacja)

### MI-006: Market Limits - Coverage
- **Warunek**: WSZYSTKIE aktywne markety maja zdefiniowane limity (jesli system jest aktywny)
- **Jak sprawdzic**: Sprawdz limit dla kazdego aktywnego marketu
- **Oczekiwany wynik**: Kazdy market ma limit > 0 (lub swiadomie 0 = brak limitu)
- **Uwagi**: Market bez limitu = brak ochrony przed koncentracja w tym markecie

---

## HIGH

### MI-010: Cross-Market Balance Consistency
- **Warunek**: Suma totalAssetsInMarket() po wszystkich marketach + vault balance == totalAssets()
- **Jak sprawdzic**:
  ```
  sum = 0
  for each marketId in activeMarkets:
      sum += vault.totalAssetsInMarket(marketId)
  sum += ERC20(asset).balanceOf(vault)
  sum += rewardsManager.balanceOf() (jesli istnieje)
  assert sum ~= vault.totalAssets() (z tolerancja na rounding)
  ```
- **Oczekiwany wynik**: Rownowaga (z tolerancja +-1 na rounding)
- **Uwagi**: Niezgodnosc = bledne balance fuses lub brakujace markety

### MI-011: Swap Markets Dependencies
- **Warunek**: Markety swap (Uniswap, Universal Token Swapper, Odos) maja dependency na ERC20_VAULT_BALANCE
- **Jak sprawdzic**: getDependencyBalanceGraph() zawiera ERC20_VAULT_BALANCE
- **Oczekiwany wynik**: Zaleznosc istnieje
- **Uwagi**: Swap zmienia balance tokenow - bez dependency nie bedzie zaktualizowany

### MI-012: LP Markets Dependencies
- **Warunek**: Markety LP (Uniswap V3 positions, Curve, Balancer) maja dependencies na tokeny skladowe
- **Jak sprawdzic**: getDependencyBalanceGraph() zawiera odpowiednie markety
- **Oczekiwany wynik**: Zaleznosci na skladowe tokeny
- **Uwagi**: LP pozycja = dwa tokeny, zmiana LP wplywa na oba

### MI-013: Staking/Gauge Dependencies
- **Warunek**: Markety staking/gauge maja dependency na market z LP tokenem
- **Jak sprawdzic**: getDependencyBalanceGraph()
- **Oczekiwany wynik**: Gauge zalezy od odpowiedniego LP pool marketu
- **Uwagi**: Stake/unstake LP tokena zmienia balance LP market

### MI-014: Borrow Market Dependencies
- **Warunek**: Markety z borrow (Aave, Compound, Morpho, Euler) maja dependency na ERC20_VAULT_BALANCE
- **Jak sprawdzic**: getDependencyBalanceGraph()
- **Oczekiwany wynik**: Dependency na ERC20_VAULT_BALANCE
- **Uwagi**: Borrow przynosi tokeny do vaulta, repay je zabiera

### MI-015: Market Limits Sum Reasonability
- **Warunek**: Suma limitow jest rozsadna dla strategii
- **Jak sprawdzic**: Zsumuj limity wszystkich marketow
- **Oczekiwany wynik**: Suma >= 100% (1e18) aby vault mogl w pelni alokowac
- **Uwagi**: Jesli suma < 100% to vault nie moze w pelni alokowac kapitalu

---

## MEDIUM

### MI-020: Dependency Graph Depth
- **Warunek**: Glebokosc grafu zaleznosci nie jest nadmiernie duza
- **Jak sprawdzic**: Zmierz max depth grafu
- **Oczekiwany wynik**: Depth <= 3-4 (rozsadna zlozonosc)
- **Uwagi**: Zbyt gleboki graf = wiecej gas na balance updates

### MI-021: Market Interaction Gas Cost
- **Warunek**: Execute z wieloma marketami miesci sie w block gas limit
- **Jak sprawdzic**: Estymacja gas execute() z typowym zestawem actions
- **Oczekiwany wynik**: Gas < 50% block gas limit
- **Uwagi**: Zbyt kosztowne execute = Alpha nie moze dzialac

### MI-022: Balance Update After Execute
- **Warunek**: Po execute() wszystkie dotkniente markety + dependencies sa zaktualizowane
- **Jak sprawdzic**: Porownaj totalAssetsInMarket() przed i po execute()
- **Oczekiwany wynik**: Wartosci zaktualizowane prawidlowo
- **Uwagi**: Test funkcjonalny na produkcji po pierwszych transakcjach
