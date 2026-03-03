# 08 - Price Oracle Validation

## Cel
Weryfikacja systemu price oracle, feedow cenowych i konfiguracji PriceOracleMiddleware.

---

## Architektura Oracle

```
PlasmaVault
  └── PriceOracleMiddleware (chain-wide)
        ├── Custom PriceFeed per asset (IPriceFeed)
        │   ├── ERC4626PriceFeed
        │   ├── CurveStableSwapNGPriceFeed
        │   ├── WstETHPriceFeed
        │   ├── SDaiPriceFeed
        │   ├── DualCrossReferencePriceFeed
        │   └── ...
        └── Chainlink Feed Registry (fallback)

  └── PriceOracleMiddlewareManager (vault-specific, opcjonalny)
        ├── Asset → Custom source mapping
        └── Price validation (delta checking)
```

**Kluczowe**: Wszystkie ceny w USD, 18 decimals (WAD). Quote currency = address(0x348).

---

## CRITICAL

### PO-001: Price Oracle Middleware Set
- **Warunek**: Vault ma skonfigurowany PriceOracleMiddleware
- **Jak sprawdzic**: `PlasmaVaultGovernance.getPriceOracleMiddleware()`
- **Oczekiwany wynik**: Poprawny adres (nie address(0))
- **Uwagi**: BEZ oracle vault NIE MOZE przeliczac balansow na USD

### PO-002: Quote Currency = USD
- **Warunek**: Oracle uzywa USD jako quote currency
- **Jak sprawdzic**: Sprawdz QUOTE_CURRENCY w PriceOracleMiddleware == address(0x348)
- **Oczekiwany wynik**: address(0x0000000000000000000000000000000000000348)
- **Uwagi**: ISO-4217 kod USD. Inne quote currency = bledne wyceny

### PO-003: Underlying Token Has Price Feed
- **Warunek**: Underlying token vaulta (asset) ma skonfigurowany price feed
- **Jak sprawdzic**: `PriceOracleMiddleware.getAssetPrice(asset)` nie revertuje
- **Oczekiwany wynik**: Cena > 0, decimals = 18
- **Uwagi**: Bez ceny underlying tokena - konwersja balance USD -> amount jest niemozliwa

### PO-004: All Substrate Assets Have Price Feeds
- **Warunek**: KAZDY asset uzywany w substrates ma price feed
- **Jak sprawdzic**: Dla kazdego tokena w substrates: `getAssetPrice(token)` nie revertuje
- **Oczekiwany wynik**: Cena > 0 dla kazdego assetu
- **Uwagi**: Brak ceny = balance fuse nie moze obliczyc wartosci w USD

### PO-005: Price Feed Accuracy
- **Warunek**: Ceny z oracle sa zblizone do rynkowych
- **Jak sprawdzic**: Porownaj `getAssetPrice()` z aktualna cena rynkowa
- **Oczekiwany wynik**: Odchylenie < 1-2%
- **Uwagi**: Duze odchylenie = bledna wycena sharesow, arbitraz

### PO-006: Price Feed Freshness
- **Warunek**: Ceny nie sa stale (Chainlink heartbeat)
- **Jak sprawdzic**: Sprawdz timestamp ostatniej aktualizacji Chainlink feed
- **Oczekiwany wynik**: Ostatnia aktualizacja < heartbeat interval (np. 1h, 24h)
- **Uwagi**: Stale ceny = bledna wycena

---

## HIGH

### PO-010: Custom Price Feeds Correctness
- **Warunek**: Custom price feeds (ERC4626PriceFeed, WstETHPriceFeed, etc.) sa poprawne
- **Jak sprawdzic**: Dla kazdego assetu z custom feedem:
  - `PriceOracleMiddleware.getSourceOfAssetPrice(asset)` → adres custom feed
  - Sprawdz parametry custom feed (base asset, reference oracle, etc.)
- **Oczekiwany wynik**: Poprawne parametry
- **Uwagi**: Bledny custom feed = systematycznie bledna wycena

### PO-011: Derivative Asset Price Feeds
- **Warunek**: Assety pochodne (wstETH, sDAI, LP tokeny) maja odpowiednie price feeds
- **Jak sprawdzic**: Sprawdz typ price feed dla kazdego derivative assetu
- **Oczekiwany wynik**:
  - wstETH → WstETHPriceFeed (uzywa kursu wstETH/stETH + stETH/USD)
  - sDAI → SDaiPriceFeed (uzywa kursu sDAI/DAI + DAI/USD)
  - LP tokens → odpowiedni LP price feed
  - ERC4626 shares → ERC4626PriceFeed (uzywa convertToAssets + asset price)
- **Uwagi**: Prosty Chainlink feed dla derivative moze nie istniec

### PO-012: Price Oracle Decimals Consistency
- **Warunek**: Wszystkie ceny sa w 18 decimals
- **Jak sprawdzic**: `getAssetPrice(asset)` returns (price, decimals) - decimals == 18
- **Oczekiwany wynik**: decimals = 18 dla kazdego assetu
- **Uwagi**: Rozne decimals = bledne obliczenia w balance fuses

### PO-013: Chainlink Feed Registry (Ethereum)
- **Warunek**: Na Ethereum - Chainlink Feed Registry jest dostepny jako fallback
- **Jak sprawdzic**: Sprawdz czy PriceOracleMiddleware ma skonfigurowany registry
- **Oczekiwany wynik**: Poprawny adres Chainlink Feed Registry (jesli na Ethereum)
- **Uwagi**: Na L2 (Arbitrum, Base) moze nie byc Feed Registry

### PO-014: PriceOracleMiddlewareManager Setup (if used)
- **Warunek**: Jesli vault uzywa PriceOracleMiddlewareManager - jest poprawnie skonfigurowany
- **Jak sprawdzic**: Sprawdz configured assets i ich sources
- **Oczekiwany wynik**: Wszystkie potrzebne assety maja zrodla cen
- **Uwagi**: Manager nadpisuje domyslny middleware

### PO-015: Price Validation Configuration (if used)
- **Warunek**: Jesli uzywa price validation - max delta jest sensowna
- **Jak sprawdzic**: `getPriceValidationInfo(asset)` w PriceOracleMiddlewareManager
- **Oczekiwany wynik**: Max delta zgodna z zmiennoscia assetu (np. 5% dla stablecoin, 20% dla volatile)
- **Uwagi**: Za ciasna delta = blokuje operacje; za luźna = brak ochrony

---

## MEDIUM

### PO-020: Oracle Manipulation Resistance
- **Warunek**: Price feeds sa odporne na manipulacje (TWAP, Chainlink, nie spot)
- **Jak sprawdzic**: Sprawdz typ oracle uzywanego przez kazdy feed
- **Oczekiwany wynik**: Chainlink, TWAP lub zaufany zrodlo (nie AMM spot price)
- **Uwagi**: AMM spot price moze byc manipulowany flash loanami

### PO-021: Multi-hop Price Feeds
- **Warunek**: Wieloetapowe price feeds (token → intermediate → USD) sa poprawne
- **Jak sprawdzic**: Sprawdz lancuch cenowy dla kazdego multi-hop feed
- **Oczekiwany wynik**: Kazdy krok ma poprawne zrodlo
- **Uwagi**: DualCrossReferencePriceFeed uzywa dwoch zrodel - oba musza byc poprawne

### PO-022: Price Oracle Immutability
- **Warunek**: Price oracle nie moze byc zmieniony bez governance delay
- **Jak sprawdzic**: Sprawdz kto moze wywolac `setPriceOracleMiddleware()`
- **Oczekiwany wynik**: ATOMIST_ROLE z odpowiednim execution delay
- **Uwagi**: Zmiana oracle = zmiana wyceny wszystkich assetow
