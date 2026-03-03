# 07 - Fee System Validation

## Cel
Weryfikacja konfiguracji oplat: performance fee, management fee, deposit fee.

---

## Stale systemowe

| Stala | Wartosc | Opis |
|-------|---------|------|
| PERFORMANCE_MAX_FEE_IN_PERCENTAGE | 5000 | Max 50% (100 = 1%, 2 decimal precision) |
| MANAGEMENT_MAX_FEE_IN_PERCENTAGE | 500 | Max 5% (100 = 1%, 2 decimal precision) |
| Deposit Fee | 18 decimal precision | 1e18 = 100%, 1e16 = 1% |

### Typy oplat:
- **Performance Fee**: Naliczana przy wzroscie totalAssets (high water mark). Precyzja: 2 decimale (10000 = 100%).
- **Management Fee**: Naliczana ciagle proporcjonalnie do czasu i totalAssets. Precyzja: 2 decimale (10000 = 100%).
- **Deposit Fee**: Naliczana przy depozycie, potrącana z mintowanych shares. Precyzja: 18 decimali (1e18 = 100%).

---

## CRITICAL

### FE-001: Performance Fee Account
- **Warunek**: Performance fee account jest poprawny i aktywny
- **Jak sprawdzic**: `PlasmaVaultGovernance.getPerformanceFeeData()`
- **Oczekiwany wynik**: `feeAccount` != address(0) i jest oczekiwanym adresem FeeManager
- **Uwagi**: address(0) = fees ida donikad; bledny adres = fees idaz do kogosinnego

### FE-002: Performance Fee Percentage
- **Warunek**: Performance fee jest <= 50% i zgodna z zamierzeniem
- **Jak sprawdzic**: `getPerformanceFeeData().feeInPercentage`
- **Oczekiwany wynik**: Wartosc <= 5000 i zgodna z dokumentacja vaulta
- **Uwagi**: 100 = 1%, 5000 = 50% max

### FE-003: Management Fee Account
- **Warunek**: Management fee account jest poprawny
- **Jak sprawdzic**: `PlasmaVaultGovernance.getManagementFeeData()`
- **Oczekiwany wynik**: `feeAccount` != address(0) i jest oczekiwanym adresem
- **Uwagi**: Management fee jest naliczana ciagle

### FE-004: Management Fee Percentage
- **Warunek**: Management fee jest <= 5% i zgodna z zamierzeniem
- **Jak sprawdzic**: `getManagementFeeData().feeInPercentage`
- **Oczekiwany wynik**: Wartosc <= 500 i zgodna z dokumentacja
- **Uwagi**: 100 = 1%, 500 = 5% max

### FE-005: Fee Manager Initialization
- **Warunek**: FeeManager jest zainicjalizowany
- **Jak sprawdzic**: Sprawdz initialization flag FeeManager
- **Oczekiwany wynik**: Zainicjalizowany, nie mozna ponownie
- **Uwagi**: Niezainicjalizowany FeeManager = fees nie dzialaja poprawnie

---

## HIGH

### FE-010: FeeManager Recipients
- **Warunek**: Fee recipients sa poprawnie skonfigurowane w FeeManagerze
- **Jak sprawdzic**: Odczyt recipients z FeeManager
- **Oczekiwany wynik**:
  - DAO fee recipient = poprawny adres IPOR DAO
  - Dodatkowi recipients = zgodne z umowa/dokumentacja
- **Uwagi**: Fee jest dzielone miedzy DAO i dodatkowych recipientow

### FE-011: DAO Fee Values
- **Warunek**: IPOR DAO fee jest ustawione poprawnie
- **Jak sprawdzic**: Odczyt IPOR_DAO_PERFORMANCE_FEE i IPOR_DAO_MANAGEMENT_FEE z FeeManager
- **Oczekiwany wynik**: Zgodne z governance decision
- **Uwagi**: Immutable po deploy - ustalone w FeeManagerFactory

### FE-012: Total Fee Not Exceeding Max
- **Warunek**: Suma performance fee (DAO + recipients) nie przekracza max
- **Jak sprawdzic**: `totalPerformanceFee = daoFee + sum(recipientFees)` <= 5000
- **Oczekiwany wynik**: <= 5000 (50%)
- **Uwagi**: Analogicznie dla management fee <= 500

### FE-013: Management Fee Timestamp
- **Warunek**: lastUpdateTimestamp w management fee jest aktualny
- **Jak sprawdzic**: `getManagementFeeData().lastUpdateTimestamp`
- **Oczekiwany wynik**: Niedawny timestamp
- **Uwagi**: Stary timestamp = duze narosle fees przy nastepnej operacji

### FE-014: Fee Manager -> Vault Connection
- **Warunek**: FeeManager jest polaczony z poprawnym vaultem
- **Jak sprawdzic**: Odczyt PlasmaVault address z FeeManager
- **Oczekiwany wynik**: Adres vaulta
- **Uwagi**: Bledne polaczenie = fees nie beda mintowane

### FE-015: TECH Fee Roles Assignment
- **Warunek**: TECH_PERFORMANCE_FEE_MANAGER_ROLE i TECH_MANAGEMENT_FEE_MANAGER_ROLE sa przypisane TYLKO do FeeManagera
- **Jak sprawdzic**: Sprawdz holderow tych rol w AccessManager
- **Oczekiwany wynik**: Tylko FeeManager ma te role
- **Uwagi**: Nieautoryzowany holder moze zmienic fee konfiguracje

---

## MEDIUM

### FE-020: Unrealized Management Fee
- **Warunek**: Unrealized management fee jest rozsadna
- **Jak sprawdzic**: `PlasmaVault.getUnrealizedManagementFee()`
- **Oczekiwany wynik**: Wartosc proporcjonalna do totalAssets * fee% * czas
- **Uwagi**: Bardzo duza wartosc moze wskazywac na problem

### FE-021: Performance Fee Only on Profit
- **Warunek**: Performance fee jest naliczana TYLKO przy wzroscie totalAssets
- **Jak sprawdzic**: Weryfikacja logiki w execute() - fee mintowane tylko gdy totalAssetsAfter > totalAssetsBefore
- **Oczekiwany wynik**: Brak fee mintowania przy stratach
- **Uwagi**: Wbudowane w kontrakt

### FE-022: Zero Fee Config (if intended)
- **Warunek**: Jesli vault ma byc zero-fee - wszystkie fee sa 0
- **Jak sprawdzic**: getPerformanceFeeData, getManagementFeeData, FeeManager.getDepositFee()
- **Oczekiwany wynik**: feeInPercentage == 0 dla wszystkich trzech typow

---

## DEPOSIT FEE

### FE-030: Deposit Fee Value
- **Warunek**: Deposit fee jest ustawiony na sensowna wartosc
- **Jak sprawdzic**: `FeeManager.getDepositFee()`
- **Oczekiwany wynik**: Wartosc zgodna z zamierzeniem (0 jesli brak oplat, np. 1e16 = 1%)
- **Uwagi**: Precyzja 18 decimali (1e18 = 100%). Zbyt wysoka wartosc = odstraszanie deponentow

### FE-031: Deposit Fee Calculation
- **Warunek**: Deposit fee jest poprawnie potrącana z mintowanych shares
- **Jak sprawdzic**: `FeeManager.calculateDepositFee(shares)` - powinno zwrocic `shares * depositFee / 1e18`
- **Oczekiwany wynik**: Wartosc proporcjonalna do shares i deposit fee
- **Uwagi**: Fee jest potrącana z shares (deponent dostaje mniej shares)

### FE-032: Deposit Fee Mutability
- **Warunek**: Deposit fee moze byc zmieniony przez ATOMIST_ROLE
- **Jak sprawdzic**: `FeeManager.setDepositFee()` wymaga odpowiedniej roli
- **Oczekiwany wynik**: Tylko ATOMIST moze zmieniac deposit fee
- **Uwagi**: W przeciwienstwie do DAO fees (immutable), deposit fee jest mutable

### FE-033: Deposit Fee Max Guard
- **Warunek**: Deposit fee nie przekracza rozsadnej wartosci
- **Jak sprawdzic**: `FeeManager.getDepositFee()` < 1e18
- **Oczekiwany wynik**: Wartosc znacznie ponizej 1e18 (100%). Kod pozwala na max 1e18 bez ograniczenia gornego!
- **Uwagi**: Brak hardcoded max w kontrakcie - ATOMIST moze ustawic dowolna wartosc do 1e18. Walidacja manualna wymagana
