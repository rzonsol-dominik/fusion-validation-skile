# 03 - Market Configuration Validation

## Cel
Weryfikacja konfiguracji poszczegolnych marketow w vaulcie.
Kazdy market musi miec: Market ID, Balance Fuse, Substrates, Fuses.

---

## Predefined Market IDs (IporFusionMarkets.sol)

| Market ID | Nazwa | Protokol |
|-----------|-------|----------|
| 1 | AAVE_V3 | Aave V3 lending |
| 2 | COMPOUND_V3_USDC | Compound V3 USDC |
| 3 | GEARBOX_POOL_V3 | Gearbox V3 pool |
| 4 | GEARBOX_FARM_DTOKEN_V3 | Gearbox V3 farming |
| 5 | FLUID_INSTADAPP_POOL | Fluid pool |
| 6 | FLUID_INSTADAPP_STAKING | Fluid staking |
| 8 | UNISWAP_SWAP_V3_POSITIONS | Uniswap V3 positions |
| 9 | UNISWAP_SWAP_V2 | Uniswap V2 swaps |
| 10 | UNISWAP_SWAP_V3 | Uniswap V3 swaps |
| 11 | EULER_V2 | Euler V2 |
| 13 | COMPOUND_V3_USDT | Compound V3 USDT |
| 14 | MORPHO | Morpho Blue |
| 15 | SPARK | Spark (Aave fork) |
| 16 | CURVE_POOL | Curve pool |
| 17 | CURVE_LP_GAUGE | Curve gauge |
| 19 | MORPHO_FLASH_LOAN | Morpho flash loan |
| 20 | AAVE_V3_LIDO | Aave V3 Lido |
| 21 | MOONWELL | Moonwell |
| 22 | MORPHO_REWARDS | Morpho rewards |
| 23 | PENDLE | Pendle |
| 24 | FLUID_REWARDS | Fluid rewards |
| 25 | CURVE_GAUGE_ERC4626 | Curve gauge (ERC4626) |
| 26 | COMPOUND_V3_WETH | Compound V3 WETH |
| 41 | MORPHO_LIQUIDITY_IN_MARKETS | Morpho liquidity |
| 100_001 - 100_020 | ERC4626_0001 - ERC4626_0020 | Generic ERC4626 vaults |
| 200_001 - 200_010 | META_MORPHO_0001-0010 | MetaMorpho vaults |
| type(uint256).max | ZERO_BALANCE_MARKET | Zero balance (special) |
| type(uint256).max - 1 | ASSETS_BALANCE_VALIDATION | Assets validation (special) |
| type(uint256).max - 2 | EXCHANGE_RATE_VALIDATOR | Exchange rate (special) |

---

## CRITICAL - Per Market

### MC-001: Balance Fuse Assigned
- **Warunek**: Kazdy aktywny market MA przypisany dokladnie JEDEN balance fuse
- **Jak sprawdzic**: `PlasmaVaultGovernance.isBalanceFuseSupported(marketId, expectedFuseAddress)`
- **Oczekiwany wynik**: true dla kazdego aktywnego marketu
- **Uwagi**: BEZ balance fuse vault NIE MOZE sledzic balansow w danym markecie!

### MC-002: Balance Fuse Market ID Match
- **Warunek**: Balance fuse ma ten sam MARKET_ID co market do ktorego jest przypisany
- **Jak sprawdzic**: `IFuseCommon(balanceFuse).MARKET_ID()` == oczekiwany marketId
- **Oczekiwany wynik**: Zgodnosc market ID
- **Uwagi**: Mismatch = bledne odczyty balansow = bledna wycena sharesow

### MC-003: Market Substrates Configured
- **Warunek**: Kazdy aktywny market ma skonfigurowane substrates (dozwolone assety/adresy)
- **Jak sprawdzic**: `PlasmaVaultGovernance.getMarketSubstrates(marketId)`
- **Oczekiwany wynik**: Niepusta lista substratow dla kazdego aktywnego marketu
- **Uwagi**: Puste substrates = fuse nie moze operowac na zadnym assecie

### MC-004: Substrate Correctness
- **Warunek**: Substrates zawieraja POPRAWNE adresy/identyfikatory dla danego protokolu
- **Jak sprawdzic**: Dekoduj substrates i porownaj z oczekiwanymi assetami
  - Dla lending: adresy tokenow (USDC, DAI, etc.)
  - Dla Morpho: market IDs (bytes32)
  - Dla Uniswap: adresy par tokenow
  - Dla Balancer: adresy pooli + tokeny
  - Dla Aerdrome: adresy gauge
- **Oczekiwany wynik**: Wszystkie substrates sa poprawnymi adresami/ID
- **Uwagi**: Bledny substrate = operacja na niezamierzonym assecie/rynku

### MC-005: Supply/Interaction Fuses Registered
- **Warunek**: Fuses potrzebne do operacji na markecie sa zarejestrowane w vaulcie
- **Jak sprawdzic**: `PlasmaVaultGovernance.isFuseSupported(fuseAddress)` dla kazdego fuse
- **Oczekiwany wynik**: true dla wszystkich wymaganych fuse'ow
- **Uwagi**: Niezarejestrowany fuse = execute() zrevertuje

### MC-006: Fuse Market ID Match
- **Warunek**: Kazdy fuse (supply, borrow, etc.) ma MARKET_ID zgodny z marktem
- **Jak sprawdzic**: `IFuseCommon(fuse).MARKET_ID()` == oczekiwany marketId
- **Oczekiwany wynik**: Zgodnosc
- **Uwagi**: Mismatch = fuse operuje na niewlasciwym markecie

### MC-007: ERC20_VAULT_BALANCE Market
- **Warunek**: Market ERC20_VAULT_BALANCE (ID specjalny) ma balance fuse
- **Jak sprawdzic**: Sprawdz balance fuse dla tego marketu
- **Oczekiwany wynik**: Erc20BalanceFuse jest przypisany
- **Uwagi**: Ten market sledzi natywny balance underlying tokena w vaulcie

---

## HIGH

### MC-010: Fuse Constructor Parameters
- **Warunek**: Fuses sa zdeployowane z poprawnymi parametrami (market ID, adresy protokolow)
- **Jak sprawdzic**: Odczyt immutable zmiennych z fuse'a (np. AAVE_POOL, COMET, MORPHO)
- **Oczekiwany wynik**: Poprawne adresy protokolow na danym chainie
- **Uwagi**: Bledny adres protokolu = operacje failuja lub ida do zlego kontraktu

### MC-011: Substrate Type Consistency
- **Warunek**: Typ substratu jest zgodny z typem oczekiwanym przez fuse
- **Jak sprawdzic**: Weryfikuj format substratow:
  - Asset substrates: `bytes32(uint256(uint160(address)))`
  - Morpho market IDs: raw bytes32 z Morpho
  - Gauge substrates: zakodowane adresy gauge
  - Pool substrates: zakodowane adresy pool
- **Oczekiwany wynik**: Format zgodny z implementacja fuse
- **Uwagi**: Bledny format = fuse nie rozpozna substratu

### MC-012: Active Markets List
- **Warunek**: Lista aktywnych marketow jest zgodna z oczekiwaniami
- **Jak sprawdzic**: `PlasmaVaultGovernance.getActiveMarketsInBalanceFuses()`
- **Oczekiwany wynik**: Wszystkie zamierzone markety sa na liscie
- **Uwagi**: Brakujacy market = nie jest sledzony w totalAssets

### MC-013: All Fuses Listed
- **Warunek**: Wszystkie potrzebne fuses sa w liscie supported fuses
- **Jak sprawdzic**: `PlasmaVaultGovernance.getFuses()`
- **Oczekiwany wynik**: Kompletna lista wszystkich wymaganych fuse'ow
- **Uwagi**: Porownaj z oczekiwana konfiguracja

### MC-014: No Obsolete Fuses
- **Warunek**: Nie ma starych/niepotrzebnych fuse'ow w liscie
- **Jak sprawdzic**: `PlasmaVaultGovernance.getFuses()` - sprawdz kazdy
- **Oczekiwany wynik**: Kazdy fuse jest potrzebny i aktualny
- **Uwagi**: Stary fuse moze miec bugi/luki

### MC-015: Substrate Not Over-Permissive
- **Warunek**: Substrates nie zawieraja niepotrzebnych assetow
- **Jak sprawdzic**: Porownaj substrates z zamierzona strategia
- **Oczekiwany wynik**: Tylko potrzebne assety/rynki
- **Uwagi**: Over-permissive substrates = Alpha moze operowac na niezamierzonych assetach

---

## MEDIUM

### MC-020: Balance Fuse Returns Sensible Value
- **Warunek**: Balance fuse zwraca rozsadna wartosc dla obecnego stanu
- **Jak sprawdzic**: Wywolaj `balanceOf()` na balance fuse (statycznie)
- **Oczekiwany wynik**: Wartosc >= 0 i zgodna z rzeczywistym stanem na protokole
- **Uwagi**: Test funkcjonalny

### MC-021: Supply Fuse Permissions on Protocol
- **Warunek**: Vault ma odpowiednie approvals/permissions na protokole bazowym
- **Jak sprawdzic**: Sprawdz ERC20 allowances vaulta do protokolow
- **Oczekiwany wynik**: Approvals sa ustawiane dynamicznie przez fuse (nie wstepnie)
- **Uwagi**: Fuses powinny robic approve -> interact -> revoke approve

### MC-022: Market ID Uniqueness
- **Warunek**: Kazdy market ID jest uzyty dokladnie raz
- **Jak sprawdzic**: Sprawdz ze nie ma duplikatow w active markets
- **Oczekiwany wynik**: Unikalne market IDs
