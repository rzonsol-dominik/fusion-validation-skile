# 07 - Fee System Validation

## Purpose
Verify fee configuration: performance fee, management fee, deposit fee.

---

## System Constants

| Constant | Value | Description |
|----------|-------|-------------|
| PERFORMANCE_MAX_FEE_IN_PERCENTAGE | 5000 | Max 50% (100 = 1%, 2 decimal precision) |
| MANAGEMENT_MAX_FEE_IN_PERCENTAGE | 500 | Max 5% (100 = 1%, 2 decimal precision) |
| Deposit Fee | 18 decimal precision | 1e18 = 100%, 1e16 = 1% |

### Fee types:
- **Performance Fee**: Charged on totalAssets growth (high water mark). Precision: 2 decimals (10000 = 100%).
- **Management Fee**: Charged continuously proportional to time and totalAssets. Precision: 2 decimals (10000 = 100%).
- **Deposit Fee**: Charged on deposit, deducted from minted shares. Precision: 18 decimals (1e18 = 100%).

---

## CRITICAL

### FE-001: Performance Fee Account
- **Condition**: Performance fee account is correct and active
- **How to check**: `PlasmaVaultGovernance.getPerformanceFeeData()`
- **Expected result**: `feeAccount` != address(0) and is the expected FeeManager address
- **Notes**: address(0) = fees go nowhere; wrong address = fees go to someone else

### FE-002: Performance Fee Percentage
- **Condition**: Performance fee is <= 50% and matches intended value
- **How to check**: `getPerformanceFeeData().feeInPercentage`
- **Expected result**: Value <= 5000 and consistent with vault documentation
- **Notes**: 100 = 1%, 5000 = 50% max

### FE-003: Management Fee Account
- **Condition**: Management fee account is correct
- **How to check**: `PlasmaVaultGovernance.getManagementFeeData()`
- **Expected result**: `feeAccount` != address(0) and is the expected address
- **Notes**: Management fee is charged continuously

### FE-004: Management Fee Percentage
- **Condition**: Management fee is <= 5% and matches intended value
- **How to check**: `getManagementFeeData().feeInPercentage`
- **Expected result**: Value <= 500 and consistent with documentation
- **Notes**: 100 = 1%, 500 = 5% max

### FE-005: Fee Manager Initialization
- **Condition**: FeeManager is initialized
- **How to check**: Check FeeManager initialization flag
- **Expected result**: Initialized, cannot be re-initialized
- **Notes**: Uninitialized FeeManager = fees don't work correctly

---

## HIGH

### FE-010: FeeManager Recipients
- **Condition**: Fee recipients are correctly configured in FeeManager
- **How to check**: Read recipients from FeeManager
- **Expected result**:
  - DAO fee recipient = correct IPOR DAO address
  - Additional recipients = consistent with agreement/documentation
- **Notes**: Fee is split between DAO and additional recipients - all should be despley in raport

### FE-011: DAO Fee Values
- **Condition**: IPOR DAO fee is set correctly
- **How to check**: Read IPOR_DAO_PERFORMANCE_FEE and IPOR_DAO_MANAGEMENT_FEE from FeeManager
- **Expected result**: Consistent with governance decision
- **Notes**: Immutable after deploy - set in FeeManagerFactory

### FE-012: Total Fee Not Exceeding Max
- **Condition**: Total performance fee (DAO + recipients) does not exceed max
- **How to check**: `totalPerformanceFee = daoFee + sum(recipientFees)` <= 5000
- **Expected result**: <= 5000 (50%)
- **Notes**: Similarly for management fee <= 500

### FE-013: Management Fee Timestamp
- **Condition**: lastUpdateTimestamp in management fee is current
- **How to check**: `getManagementFeeData().lastUpdateTimestamp`
- **Expected result**: Recent timestamp
- **Notes**: Stale timestamp = large accrued fees on next operation

### FE-014: Fee Manager -> Vault Connection
- **Condition**: FeeManager is connected to the correct vault
- **How to check**: Read PlasmaVault address from FeeManager
- **Expected result**: Vault address
- **Notes**: Incorrect connection = fees won't be minted

### FE-015: TECH Fee Roles Assignment
- **Condition**: TECH_PERFORMANCE_FEE_MANAGER_ROLE and TECH_MANAGEMENT_FEE_MANAGER_ROLE are assigned ONLY to FeeManager
- **How to check**: Check holders of these roles in AccessManager
- **Expected result**: Only FeeManager has these roles
- **Notes**: Unauthorized holder can change fee configuration

---

## MEDIUM

### FE-020: Unrealized Management Fee
- **Condition**: Unrealized management fee is reasonable
- **How to check**: `PlasmaVault.getUnrealizedManagementFee()`
- **Expected result**: Value proportional to totalAssets * fee% * time
- **Notes**: Very large value may indicate a problem

### FE-021: Performance Fee Only on Profit
- **Condition**: Performance fee is charged ONLY on totalAssets growth
- **How to check**: Verify logic in execute() - fee minted only when totalAssetsAfter > totalAssetsBefore
- **Expected result**: No fee minting on losses
- **Notes**: Built into the contract

### FE-022: Zero Fee Config (if intended)
- **Condition**: If vault should be zero-fee - all fees are 0
- **How to check**: getPerformanceFeeData, getManagementFeeData, FeeManager.getDepositFee()
- **Expected result**: feeInPercentage == 0 for all three types

---

## DEPOSIT FEE

### FE-030: Deposit Fee Value
- **Condition**: Deposit fee is set to a reasonable value
- **How to check**: `FeeManager.getDepositFee()`
- **Expected result**: Value consistent with intent (0 if no fees, e.g., 1e16 = 1%)
- **Notes**: Precision is 18 decimals (1e18 = 100%). Too high = deters depositors

### FE-031: Deposit Fee Calculation
- **Condition**: Deposit fee is correctly deducted from minted shares
- **How to check**: `FeeManager.calculateDepositFee(shares)` - should return `shares * depositFee / 1e18`
- **Expected result**: Value proportional to shares and deposit fee
- **Notes**: Fee is deducted from shares (depositor receives fewer shares)

### FE-032: Deposit Fee Mutability
- **Condition**: Deposit fee can be changed by ATOMIST_ROLE
- **How to check**: `FeeManager.setDepositFee()` requires the appropriate role
- **Expected result**: Only ATOMIST can change deposit fee
- **Notes**: Unlike DAO fees (immutable), deposit fee is mutable

### FE-033: Deposit Fee Max Guard
- **Condition**: Deposit fee does not exceed a reasonable value
- **How to check**: `FeeManager.getDepositFee()` < 1e18
- **Expected result**: Value well below 1e18 (100%). Code allows max 1e18 without an upper limit!
- **Notes**: No hardcoded max in the contract - ATOMIST can set any value up to 1e18. Manual validation required
