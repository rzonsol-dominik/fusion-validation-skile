# 02 - Access Control Validation

## Cel
Weryfikacja systemu rol, uprawnien i hierarchii w IporFusionAccessManager.

---

## Definicje Rol

| Role ID | Nazwa | Opis | Admin Role |
|---------|-------|------|------------|
| 0 | ADMIN_ROLE | Najwyzszy admin - zarzadza wszystkimi rolami | - |
| 1 | OWNER_ROLE | Zarzadza Guardian/Atomist/Owner | ADMIN |
| 2 | GUARDIAN_ROLE | Emergency pause/cancel | OWNER |
| 3 | TECH_PLASMA_VAULT_ROLE | Systemowa rola PlasmaVault | ADMIN |
| 4 | IPOR_DAO_ROLE | Operacje DAO | self (4) |
| 5 | TECH_CONTEXT_MANAGER_ROLE | Dostep ContextManager | self (5) |
| 6 | TECH_WITHDRAW_MANAGER_ROLE | Dostep WithdrawManager | ADMIN |
| 7 | TECH_VAULT_TRANSFER_SHARES_ROLE | Kontrola transferu shares | ADMIN |
| 100 | ATOMIST_ROLE | Zarzadzanie vaultem | OWNER |
| 200 | ALPHA_ROLE | Wykonywanie fuse actions | ATOMIST |
| 300 | FUSE_MANAGER_ROLE | Dodawanie/usuwanie fuses | ATOMIST |
| 301 | PRE_HOOKS_MANAGER_ROLE | Zarzadzanie pre-hooks | OWNER |
| 400 | TECH_PERFORMANCE_FEE_MANAGER_ROLE | Performance fee | self (400) |
| 500 | TECH_MANAGEMENT_FEE_MANAGER_ROLE | Management fee | self (500) |
| 600 | CLAIM_REWARDS_ROLE | Claimowanie nagrod | ATOMIST |
| 601 | TECH_REWARDS_CLAIM_MANAGER_ROLE | System rewards | ADMIN |
| 700 | TRANSFER_REWARDS_ROLE | Transfer nagrod | ATOMIST |
| 800 | WHITELIST_ROLE | Deposit/withdraw (prywatny vault) | ATOMIST |
| 900 | CONFIG_INSTANT_WITHDRAWAL_FUSES_ROLE | Konfiguracja instant withdrawal | ATOMIST |
| 901 | WITHDRAW_MANAGER_REQUEST_FEE_ROLE | Konfiguracja request fee | ATOMIST |
| 902 | WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE | Konfiguracja withdraw fee | ATOMIST |
| 1000 | UPDATE_MARKETS_BALANCES_ROLE | Aktualizacja balansow marketow | ATOMIST |
| 1100 | UPDATE_REWARDS_BALANCE_ROLE | Aktualizacja balansu nagrod | ATOMIST |
| 1200 | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE | Zarzadzanie oracle | ATOMIST |
| MAX | PUBLIC_ROLE | Brak ograniczen | - |

---

## CRITICAL

### AC-001: ADMIN_ROLE Assignment
- **Warunek**: ADMIN_ROLE jest przypisany do oczekiwanego adresu (multisig/DAO)
- **Jak sprawdzic**: `AccessManager.hasRole(0, address)` dla oczekiwanego admina
- **Oczekiwany wynik**: true
- **Uwagi**: KRYTYCZNE - admin moze zmienic WSZYSTKIE role. Musi byc multisig!

### AC-002: ADMIN_ROLE - brak nieautoryzowanych
- **Warunek**: ADMIN_ROLE NIE jest przypisany do ZADNEGO adresu na produkcji
- **Jak sprawdzic**: Sprawdz logi `RoleGranted` i `RoleRevoked` dla roleId=0. Sprawdz czy po inicjalizacji ADMIN_ROLE zostal odwolany
- **Oczekiwany wynik**: **ZERO holderow ADMIN_ROLE** - docelowo zaden adres nie powinien posiadac ADMIN_ROLE
- **Uwagi**: CRITICAL - Jakikolwiek adres z ADMIN_ROLE na produkcji to sytuacja niepozadana i musi byc zgloszona jako CRITICAL. ADMIN moze zmienic WSZYSTKIE role, wlacznie z TECH_*, co daje pelna kontrole nad vaultem

### AC-003: OWNER_ROLE Assignment
- **Warunek**: OWNER_ROLE jest przypisany do wlasciwych adresow
- **Jak sprawdzic**: `AccessManager.hasRole(1, address)`
- **Oczekiwany wynik**: Tylko oczekiwane adresy (multisig)
- **Uwagi**: Owner moze zarzadzac Guardian, Atomist

### AC-004: ATOMIST_ROLE Assignment
- **Warunek**: ATOMIST_ROLE jest przypisany do oczekiwanych adresow
- **Jak sprawdzic**: `AccessManager.hasRole(100, address)`
- **Oczekiwany wynik**: Oczekiwane adresy atomistow
- **Uwagi**: Atomist kontroluje konfiguracje vaulta

### AC-005: ALPHA_ROLE Assignment
- **Warunek**: ALPHA_ROLE jest przypisany do oczekiwanych adresow (boty/strategie)
- **Jak sprawdzic**: `AccessManager.hasRole(200, address)`
- **Oczekiwany wynik**: Oczekiwane adresy alpha executors
- **Uwagi**: Alpha moze wykonywac dowolne fuse actions - musi byc zaufany

### AC-005b: Role Separation (AC-001 - AC-005)
- **Warunek**: Zaden adres NIE posiada wiecej niz jednej roli sposrod: ADMIN_ROLE, OWNER_ROLE, GUARDIAN_ROLE, ATOMIST_ROLE, ALPHA_ROLE
- **Jak sprawdzic**: Dla kazdego holdera rol AC-001-AC-005 sprawdz czy nie posiada zadnej innej roli z tej grupy
- **Oczekiwany wynik**: Kazdy adres ma dokladnie 1 role (lub 0 w przypadku ADMIN)
- **Uwagi**: CRITICAL - Laczenie rol lamie zasade separation of concerns i umozliwia eskalacje uprawnien. Np. adres z OWNER+ALPHA moze sam sobie nadac role i wykonywac operacje

### AC-006: TECH_PLASMA_VAULT_ROLE
- **Warunek**: TECH_PLASMA_VAULT_ROLE jest przypisany TYLKO do adresu PlasmaVault
- **Jak sprawdzic**: `AccessManager.hasRole(3, vaultAddress)` + sprawdz logi
- **Oczekiwany wynik**: Tylko vault ma te role
- **Uwagi**: Rola systemowa - nie powinna byc przypisana do zadnego innego adresu

### AC-007: GUARDIAN_ROLE Assignment
- **Warunek**: GUARDIAN_ROLE jest przypisany do oczekiwanego adresu
- **Jak sprawdzic**: `AccessManager.hasRole(2, address)`
- **Oczekiwany wynik**: Oczekiwany guardian (moze byc multisig lub EOA do szybkiego reagowania)
- **Uwagi**: Guardian moze pauzoowac vault - wazne na emergency

### AC-008: Function-Role Mappings
- **Warunek**: Kazda funkcja vaulta ma przypisana poprawna role w AccessManager
- **Jak sprawdzic**: `AccessManager.getTargetFunctionRole(vault, selector)` dla kazdego selektora
- **Oczekiwany wynik**: Mappingi zgodne z tabelka ponizej
- **Uwagi**: Bledne mapowanie = nieautoryzowany dostep

#### Wymagane mappingi funkcji:

| Funkcja | Oczekiwana rola |
|---------|-----------------|
| `execute(FuseAction[])` | ALPHA_ROLE (200) |
| `deposit(uint256,address)` | WHITELIST_ROLE (800) lub PUBLIC_ROLE (zalezy od isPublic) |
| `mint(uint256,address)` | WHITELIST_ROLE (800) lub PUBLIC_ROLE (zalezy od isPublic) |
| `depositWithPermit(...)` | WHITELIST_ROLE (800) lub PUBLIC_ROLE (zalezy od isPublic) |
| `withdraw(uint256,address,address)` | PUBLIC_ROLE |
| `redeem(uint256,address,address)` | PUBLIC_ROLE |
| `redeemFromRequest(...)` | PUBLIC_ROLE |
| `addFuses(address[])` | FUSE_MANAGER_ROLE (300) |
| `removeFuses(address[])` | FUSE_MANAGER_ROLE (300) |
| `addBalanceFuse(uint256,address)` | FUSE_MANAGER_ROLE (300) |
| `removeBalanceFuse(uint256,address)` | FUSE_MANAGER_ROLE (300) |
| `grantMarketSubstrates(...)` | FUSE_MANAGER_ROLE (300) |
| `updateDependencyBalanceGraphs(...)` | FUSE_MANAGER_ROLE (300) |
| `updateCallbackHandler(...)` | FUSE_MANAGER_ROLE (300) |
| `setupMarketsLimits(...)` | ATOMIST_ROLE (100) |
| `activateMarketsLimits()` | ATOMIST_ROLE (100) |
| `deactivateMarketsLimits()` | ATOMIST_ROLE (100) |
| `setPriceOracleMiddleware(...)` | ATOMIST_ROLE (100) |
| `setTotalSupplyCap(...)` | ATOMIST_ROLE (100) |
| `convertToPublicVault()` | ATOMIST_ROLE (100) |
| `enableTransferShares()` | ATOMIST_ROLE (100) |
| `setPreHookImplementations(...)` | PRE_HOOKS_MANAGER_ROLE (301) |
| `claimRewards(FuseAction[])` | TECH_REWARDS_CLAIM_MANAGER_ROLE (601) |
| `setRewardsClaimManagerAddress(...)` | TECH_REWARDS_CLAIM_MANAGER_ROLE (601) |
| `updateMarketsBalances(uint256[])` | UPDATE_MARKETS_BALANCES_ROLE (1000) |
| `configureInstantWithdrawalFuses(...)` | CONFIG_INSTANT_WITHDRAWAL_FUSES_ROLE (900) |
| `configurePerformanceFee(...)` | TECH_PERFORMANCE_FEE_MANAGER_ROLE (400) |
| `configureManagementFee(...)` | TECH_MANAGEMENT_FEE_MANAGER_ROLE (500) |
| `transfer(address,uint256)` | TECH_VAULT_TRANSFER_SHARES_ROLE (7) (domyslnie) lub PUBLIC_ROLE (po enableTransferShares) |
| `transferFrom(...)` | TECH_VAULT_TRANSFER_SHARES_ROLE (7) (domyslnie) lub PUBLIC_ROLE (po enableTransferShares) |
| `transferRequestSharesFee(...)` | TECH_WITHDRAW_MANAGER_ROLE (6) |
| `setMinimalExecutionDelaysForRoles(...)` | OWNER_ROLE (1) |

#### Mappingi na AccessManager (nie vault):

| Funkcja | Oczekiwana rola |
|---------|-----------------|
| `AccessManager.initialize(...)` | ADMIN_ROLE (0) |
| `AccessManager.convertToPublicVault(address)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.enableTransferShares(address)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.setMinimalExecutionDelaysForRoles(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.cancel(...)` | GUARDIAN_ROLE (2) |
| `AccessManager.updateTargetClosed(...)` | GUARDIAN_ROLE (2) |
| `AccessManager.canCallAndUpdate(...)` | TECH_PLASMA_VAULT_ROLE (3) |

#### Mappingi na WithdrawManager (jesli wdrozony):

| Funkcja | Oczekiwana rola |
|---------|-----------------|
| `requestShares(...)` | PUBLIC_ROLE (publiczny dostep do requestow) |
| `releaseFunds(...)` | ALPHA_ROLE (200) |
| `updateWithdrawWindow(...)` | ATOMIST_ROLE (100) |
| `updatePlasmaVaultAddress(...)` | ATOMIST_ROLE (100) |
| `canWithdrawFromRequest(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `canWithdrawFromUnallocated(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `updateWithdrawFee(...)` | WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE (902) |
| `updateRequestFee(...)` | WITHDRAW_MANAGER_REQUEST_FEE_ROLE (901) |

#### Mappingi na PriceOracleMiddlewareManager (jesli wdrozony):

| Funkcja | Oczekiwana rola |
|---------|-----------------|
| `setAssetsPriceSources(...)` | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE (1200) |
| `removeAssetsPriceSources(...)` | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE (1200) |
| `setPriceOracleMiddleware(...)` | ATOMIST_ROLE (100) |
| `updatePriceValidation(...)` | ATOMIST_ROLE (100) |
| `removePriceValidation(...)` | ATOMIST_ROLE (100) |
| `validateAllAssetsPrices(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `validateAssetsPrices(...)` | TECH_PLASMA_VAULT_ROLE (3) |

#### Mappingi na RewardsClaimManager (jesli wdrozony):

| Funkcja | Oczekiwana rola |
|---------|-----------------|
| `claimRewards(...)` | CLAIM_REWARDS_ROLE (600) |
| `transfer(...)` | TRANSFER_REWARDS_ROLE (700) |
| `updateBalance(...)` | UPDATE_REWARDS_BALANCE_ROLE (1100) |
| `setupVestingTime(...)` | ATOMIST_ROLE (100) |
| `addRewardFuses(...)` | FUSE_MANAGER_ROLE (300) |
| `removeRewardFuses(...)` | FUSE_MANAGER_ROLE (300) |
| `transferVestedTokensToVault(...)` | PUBLIC_ROLE |

---

## HIGH

### AC-010: Role Admin Hierarchy
- **Warunek**: Kazda rola ma poprawna admin role
- **Jak sprawdzic**: Weryfikacja ustawien admin role dla kazdej roli
- **Oczekiwany wynik**:
  - OWNER_ROLE (1) admin = OWNER_ROLE (1) (self-administering)
  - GUARDIAN_ROLE (2) admin = OWNER_ROLE (1)
  - PRE_HOOKS_MANAGER_ROLE (301) admin = OWNER_ROLE (1)
  - ATOMIST_ROLE (100) admin = OWNER_ROLE (1)
  - ALPHA_ROLE (200) admin = ATOMIST_ROLE (100)
  - WHITELIST_ROLE (800) admin = ATOMIST_ROLE (100)
  - CONFIG_INSTANT_WITHDRAWAL_FUSES_ROLE (900) admin = ATOMIST_ROLE (100)
  - WITHDRAW_MANAGER_REQUEST_FEE_ROLE (901) admin = ATOMIST_ROLE (100)
  - WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE (902) admin = ATOMIST_ROLE (100)
  - UPDATE_MARKETS_BALANCES_ROLE (1000) admin = ATOMIST_ROLE (100)
  - UPDATE_REWARDS_BALANCE_ROLE (1100) admin = ATOMIST_ROLE (100)
  - TRANSFER_REWARDS_ROLE (700) admin = ATOMIST_ROLE (100)
  - CLAIM_REWARDS_ROLE (600) admin = ATOMIST_ROLE (100)
  - FUSE_MANAGER_ROLE (300) admin = ATOMIST_ROLE (100)
  - PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE (1200) admin = ATOMIST_ROLE (100)
  - TECH_PERFORMANCE_FEE_MANAGER_ROLE (400) admin = self (400)
  - TECH_MANAGEMENT_FEE_MANAGER_ROLE (500) admin = self (500)
  - TECH_REWARDS_CLAIM_MANAGER_ROLE (601) admin = ADMIN_ROLE (0)
  - IPOR_DAO_ROLE (4) admin = self (4)
  - TECH_CONTEXT_MANAGER_ROLE (5) admin = self (5)
- **Uwagi**: Bledna hierarchia = eskalacja uprawnien. Role TECH_* z self-admin sa niezmienne po inicjalizacji

### AC-011: Execution Delays
- **Warunek**: Role z execution delay maja ustawione minimalne opoznienia
- **Jak sprawdzic**: Sprawdz delay per rola w AccessManager
- **Oczekiwany wynik**: Zgodne z governance policy (np. ATOMIST 24h delay)
- **Uwagi**: Delays chronia przed atakami flash-loan na governance

### AC-012: Redemption Delay
- **Warunek**: REDEMPTION_DELAY_IN_SECONDS jest ustawiony sensownie
- **Jak sprawdzic**: Odczyt z AccessManager
- **Oczekiwany wynik**: > 0 i <= 7 dni (604800 sekund)
- **Uwagi**: Chroni przed sandwich attacks deposit-withdraw

### AC-013: Target Closed Status
- **Warunek**: Vault NIE jest w stanie paused (chyba ze zamierzony)
- **Jak sprawdzic**: `AccessManager.isTargetClosed(vaultAddress)`
- **Oczekiwany wynik**: false (jesli vault powinien byc aktywny)
- **Uwagi**: Guardian moze zamknac vault w emergency

### AC-014: TECH roles - Immutability and Correctness
- **Warunek**: Role TECH_* sa przypisane TYLKO do systemowych kontraktow I te kontrakty sa poprawnymi komponentami stacku vaulta
- **Jak sprawdzic**: Dla kazdej roli TECH_*:
  1. Sprawdz holdera roli (kto ja posiada)
  2. Zweryfikuj ze holder jest poprawnym kontraktem stacku vaulta (nie obcym adresem)
  3. Sprawdz ze holder jest powiazany z TYM vaultem (nie innym)
- **Oczekiwany wynik**:
  - TECH_PLASMA_VAULT_ROLE (3) → holder == adres TEGO PlasmaVault
  - TECH_WITHDRAW_MANAGER_ROLE (6) → holder == WithdrawManager TEGO vaulta (zgodny z vault storage)
  - TECH_CONTEXT_MANAGER_ROLE (5) → holder == ContextManager TEGO vaulta
  - TECH_PERFORMANCE_FEE_MANAGER_ROLE (400) → holder == FeeManager TEGO vaulta (zgodny z getPerformanceFeeData().feeAccount)
  - TECH_MANAGEMENT_FEE_MANAGER_ROLE (500) → holder == FeeManager TEGO vaulta (zgodny z getManagementFeeData().feeAccount)
  - TECH_REWARDS_CLAIM_MANAGER_ROLE (601) → holder == RewardsClaimManager TEGO vaulta (zgodny z getRewardsClaimManagerAddress())
- **Uwagi**: CRITICAL jesli holder nie zgadza sie z adresem zapisanym w vaulcie. Te role nie powinny byc nigdy reassignowane do innych kontraktow

### AC-015: FUSE_MANAGER_ROLE Assignment
- **Warunek**: FUSE_MANAGER_ROLE przypisany do oczekiwanych adresow
- **Jak sprawdzic**: `AccessManager.hasRole(300, address)`
- **Oczekiwany wynik**: Tylko autoryzowane adresy
- **Uwagi**: Fuse manager moze dodawac/usuwac fuse - wplyw na strategie

### AC-016: No Unauthorized Role Holders
- **Warunek**: Zadna rola nie ma nieautoryzowanych holderow
- **Jak sprawdzic**: Analiza eventow `RoleGranted` i `RoleRevoked` z AccessManagera
- **Oczekiwany wynik**: Kazdy holder jest oczekiwany
- **Uwagi**: Regularna weryfikacja wszystkich rol

---

## MEDIUM

### AC-020: ContextManager Approved Targets
- **Warunek**: Jesli ContextManager jest uzywany - approved targets to TYLKO kontrakty ze stacku danego vaulta
- **Jak sprawdzic**: `ContextManager.getApprovedTargets()` → lista adresow. Kazdy adres musi byc jednym z: PlasmaVault, WithdrawManager, FeeManager, RewardsClaimManager, PriceOracleMiddleware lub PriceOracleMiddlewareManager tego vaulta
- **Oczekiwany wynik**: Tylko adresy kontraktow nalezacych do stacku tego vaulta. Zaden obcy adres
- **Uwagi**: Approved target spoza stacku vaulta = potencjalna eskalacja uprawnien przez context manipulation

### AC-021: AccessManager Initialization
- **Warunek**: AccessManager jest zainicjalizowany (nie mozna ponownie)
- **Jak sprawdzic**: Sprobuj wywolac `initialize()` - powinno zrevertowac
- **Oczekiwany wynik**: Revert

### AC-022: Pre-Hooks Configuration and Origin
- **Warunek**: Pre-hooks sa skonfigurowane poprawnie I ich kontrakty pochodza z zaufanego zrodla
- **Jak sprawdzic**:
  1. Odczyt pre-hooks mappingu z vault (selector → implementation)
  2. Dla kazdego pre-hook kontraktu sprawdz:
     - Czy kod jest zweryfikowany na block explorerze
     - Czy kontrakt zostal zdeployowany przez IPOR deployer (sprawdz tx deployer address)
     - Lub czy kod kontraktu odpowiada kodowi z repozytorium ipor-fusion (porownaj bytecode)
- **Oczekiwany wynik**: Wszystkie pre-hook implementacje sa znanymi kontraktami z repo IPOR Fusion, zdeployowanymi przez zaufany deployer
- **Uwagi**: Pre-hook wykonywany jest PRZED kazda operacja vaulta. Obcy/niezweryfikowany pre-hook moze blokowac lub manipulowac operacjami
