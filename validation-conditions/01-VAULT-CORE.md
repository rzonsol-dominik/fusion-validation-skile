# 01 - Vault Core Configuration Validation

## Cel
Weryfikacja bazowej konfiguracji PlasmaVault na produkcji.

---

## CRITICAL

### VC-001: Underlying Token
- **Warunek**: Vault ma prawidlowy underlying token (ERC4626 asset)
- **Jak sprawdzic**: `PlasmaVault.asset()`
- **Oczekiwany wynik**: Adres oczekiwanego tokenu (np. USDC, DAI, WETH)
- **Uwagi**: Nie mozna zmienic po deploymencie; musi zgadzac sie z zamierzonym tokenem vaulta

### VC-002: Access Manager Address
- **Warunek**: Vault jest polaczony z poprawnym IporFusionAccessManager
- **Jak sprawdzic**: `PlasmaVaultGovernance.getAccessManagerAddress()`
- **Oczekiwany wynik**: Adres wdrazonego AccessManagera
- **Uwagi**: AccessManager kontroluje CALY system uprawnien

### VC-003: Price Oracle Middleware
- **Warunek**: Vault ma skonfigurowany price oracle
- **Jak sprawdzic**: `PlasmaVaultGovernance.getPriceOracleMiddleware()`
- **Oczekiwany wynik**: Adres wdrazonego PriceOracleMiddleware (nie address(0))
- **Uwagi**: Oracle musi uzywac USD jako quote currency (address(0x348))

### VC-004: PlasmaVaultBase Address
- **Warunek**: Vault ma prawidlowy PlasmaVaultBase (extension contract)
- **Jak sprawdzic**: Odczyt z storage slot PlasmaVaultBase
- **Oczekiwany wynik**: Prawidlowy adres kontraktu PlasmaVaultBase (nie address(0))
- **Uwagi**: Uzywany do delegatecall dla ERC20 voting, permit, supply cap

### VC-005: Proxy Implementation (Minimal Proxy / Clones)
- **Warunek**: Vault jest Minimal Proxy (OpenZeppelin Clones) wskazujacy na poprawna implementacje bazowa
- **Jak sprawdzic**: Odczyt bytecodu proxy - powinien zawierac pattern EIP-1167 Minimal Proxy wskazujacy na base implementation. Alternatywnie: sprawdz PlasmaVaultFactory ktory deployowal vault via `Clones.clone(baseAddress)`
- **Oczekiwany wynik**: Adres biezacej implementacji bazowej PlasmaVault
- **Uwagi**: Vault NIE uzywa UUPS proxy. Uzywa Minimal Proxy (Clones) - kazdy vault to niezalezny klon bazowej implementacji tworzony przez PlasmaVaultFactory

### VC-006: Vault Initialization Status
- **Warunek**: Vault jest w pelni zainicjalizowany
- **Jak sprawdzic**: Probuj wywolac `proxyInitialize()` - powinna zrevertowac
- **Oczekiwany wynik**: Revert (juz zainicjalizowany)
- **Uwagi**: Zapobieganie ponownemu inicjowaniu

---

## HIGH

### VC-010: Total Supply Cap
- **Warunek**: Supply cap jest ustawiony na sensowna wartosc
- **Jak sprawdzic**: `PlasmaVaultGovernance.getTotalSupplyCap()`
- **Oczekiwany wynik**: Wartosc zgodna z oczekiwaniami (domyslnie type(uint256).max)
- **Uwagi**: Jesli vault ma limit wielkosci, wartosc musi byc != max

### VC-011: Share Token Name & Symbol
- **Warunek**: Token ERC20 vaulta ma poprawna nazwe i symbol
- **Jak sprawdzic**: `PlasmaVault.name()`, `PlasmaVault.symbol()`
- **Oczekiwany wynik**: Oczekiwana nazwa i symbol
- **Uwagi**: Czytelne nazwy dla integratorow i UI

### VC-012: Decimals Offset
- **Warunek**: Vault ma prawidlowy offset decymali (DECIMALS_OFFSET = 2)
- **Jak sprawdzic**: `PlasmaVault.decimals()`
- **Oczekiwany wynik**: `underlying.decimals() + 2` (np. USDC 6 + 2 = 8)
- **Uwagi**: Wbudowane w kontrakt, weryfikacja zgodnosci

### VC-013: Withdraw Manager
- **Warunek**: WithdrawManager jest poprawnie podlaczony
- **Jak sprawdzic**: Odczyt adresu WithdrawManager z vault storage
- **Oczekiwany wynik**: Prawidlowy adres WithdrawManager (nie address(0))
- **Uwagi**: Kontroluje wyplaty i kolejke requestow

### VC-014: Public Vault Status
- **Warunek**: Vault jest public lub private zgodnie z zamierzeniem
- **Jak sprawdzic**: Sprawdz czy `deposit()` i `mint()` maja PUBLIC_ROLE w AccessManager
- **Oczekiwany wynik**: PUBLIC_ROLE jesli vault ma byc publiczny, WHITELIST_ROLE jesli prywatny
- **Uwagi**: `convertToPublicVault()` zmienia to na PUBLIC_ROLE

### VC-015: Share Transfers Status
- **Warunek**: Transfery sharesow sa wlaczone/wylaczone zgodnie z zamierzeniem
- **Jak sprawdzic**: `AccessManager.getTargetFunctionRole(vault, transfer.selector)` - sprawdz przypisana role
- **Oczekiwany wynik**:
  - Domyslnie: TECH_VAULT_TRANSFER_SHARES_ROLE (7) - transfery zablokowane dla zwyklych userow
  - Po `enableTransferShares()`: PUBLIC_ROLE - transfery wlaczone
- **Uwagi**: `enableTransferShares()` zmienia role transfer/transferFrom na PUBLIC_ROLE. Wywolanie wymaga ATOMIST_ROLE

### VC-016: RewardsClaimManager Address
- **Warunek**: Jesli vault uzywa rewards - RewardsClaimManager jest skonfigurowany
- **Jak sprawdzic**: `PlasmaVaultGovernance.getRewardsClaimManagerAddress()`
- **Oczekiwany wynik**: Prawidlowy adres lub address(0) jesli nie uzywany
- **Uwagi**: Wymagany do claimowania i vestingu nagrod

---

## MEDIUM

### VC-020: ERC4626 Compliance - maxDeposit
- **Warunek**: maxDeposit zwraca sensowna wartosc
- **Jak sprawdzic**: `PlasmaVault.maxDeposit(someAddress)`
- **Oczekiwany wynik**: > 0 jesli vault przyjmuje depozyty

### VC-021: ERC4626 Compliance - maxMint
- **Warunek**: maxMint zwraca sensowna wartosc
- **Jak sprawdzic**: `PlasmaVault.maxMint(someAddress)`
- **Oczekiwany wynik**: > 0 jesli vault przyjmuje depozyty

### VC-022: ERC4626 Compliance - totalAssets
- **Warunek**: totalAssets jest >= balance vaulta
- **Jak sprawdzic**: `PlasmaVault.totalAssets()` vs `ERC20(asset).balanceOf(vault)`
- **Oczekiwany wynik**: totalAssets >= balanceOf (bo zawiera market balances + rewards)

### VC-023: VotesPlugin Configuration
- **Warunek**: Jesli vault uzywa voting - PlasmaVaultVotesPlugin jest skonfigurowany
- **Jak sprawdzic**: Odczyt z vault storage
- **Oczekiwany wynik**: Prawidlowy adres lub address(0) jesli nieuzywany

### VC-024: Callback Handlers
- **Warunek**: Callback handlery sa skonfigurowane dla wymaganych protokolow
- **Jak sprawdzic**: Odczyt callback handler mappingu
- **Oczekiwany wynik**: Prawidlowe handlery dla uzywanych protokolow
