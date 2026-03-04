# 02 - Access Control Validation

## Purpose
Verify the role system, permissions, and hierarchy in IporFusionAccessManager.

---

## Role Definitions

| Role ID | Name | Description | Admin Role |
|---------|------|-------------|------------|
| 0 | ADMIN_ROLE | Highest admin - manages all roles | - |
| 1 | OWNER_ROLE | Manages Guardian/Atomist/Owner | ADMIN |
| 2 | GUARDIAN_ROLE | Emergency pause/cancel | OWNER |
| 3 | TECH_PLASMA_VAULT_ROLE | PlasmaVault system role | ADMIN |
| 4 | IPOR_DAO_ROLE | DAO operations | self (4) |
| 5 | TECH_CONTEXT_MANAGER_ROLE | ContextManager access | self (5) |
| 6 | TECH_WITHDRAW_MANAGER_ROLE | WithdrawManager access | ADMIN |
| 7 | TECH_VAULT_TRANSFER_SHARES_ROLE | Share transfer control | ADMIN |
| 100 | ATOMIST_ROLE | Vault management | OWNER |
| 200 | ALPHA_ROLE | Execute fuse actions | ATOMIST |
| 300 | FUSE_MANAGER_ROLE | Add/remove fuses | ATOMIST |
| 301 | PRE_HOOKS_MANAGER_ROLE | Pre-hooks management | OWNER |
| 400 | TECH_PERFORMANCE_FEE_MANAGER_ROLE | Performance fee | self (400) |
| 500 | TECH_MANAGEMENT_FEE_MANAGER_ROLE | Management fee | self (500) |
| 600 | CLAIM_REWARDS_ROLE | Claiming rewards | ATOMIST |
| 601 | TECH_REWARDS_CLAIM_MANAGER_ROLE | Rewards system | ADMIN |
| 700 | TRANSFER_REWARDS_ROLE | Reward transfers | ATOMIST |
| 800 | WHITELIST_ROLE | Deposit/withdraw (private vault) | ATOMIST |
| 900 | CONFIG_INSTANT_WITHDRAWAL_FUSES_ROLE | Instant withdrawal configuration | ATOMIST |
| 901 | WITHDRAW_MANAGER_REQUEST_FEE_ROLE | Request fee configuration | ATOMIST |
| 902 | WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE | Withdraw fee configuration | ATOMIST |
| 1000 | UPDATE_MARKETS_BALANCES_ROLE | Market balance updates | ATOMIST |
| 1100 | UPDATE_REWARDS_BALANCE_ROLE | Rewards balance updates | ATOMIST |
| 1200 | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE | Oracle management | ATOMIST |
| MAX | PUBLIC_ROLE | No restrictions | - |

---

## CRITICAL

### AC-001: ADMIN_ROLE Assignment
- **Condition**: ADMIN_ROLE is assigned to the expected address (multisig/DAO)
- **How to check**: `AccessManager.hasRole(0, address)` for the expected admin
- **Expected result**: true
- **Notes**: CRITICAL - admin can change ALL roles. Must be a multisig!

### AC-002: ADMIN_ROLE - No Unauthorized Holders
- **Condition**: ADMIN_ROLE is NOT assigned to ANY address in production
- **How to check**: Check `RoleGranted` and `RoleRevoked` logs for roleId=0. Verify that after initialization ADMIN_ROLE was revoked
- **Expected result**: **ZERO ADMIN_ROLE holders** - ultimately no address should hold ADMIN_ROLE
- **Notes**: CRITICAL - Any address with ADMIN_ROLE in production is undesirable and must be reported as CRITICAL. ADMIN can change ALL roles, including TECH_*, giving full control over the vault

### AC-003: OWNER_ROLE Assignment
- **Condition**: OWNER_ROLE is assigned to the correct addresses
- **How to check**: `AccessManager.hasRole(1, address)`
- **Expected result**: Only expected addresses (multisig)
- **Notes**: Owner can manage Guardian, Atomist

### AC-004: ATOMIST_ROLE Assignment
- **Condition**: ATOMIST_ROLE is assigned to the expected addresses
- **How to check**: `AccessManager.hasRole(100, address)`
- **Expected result**: Expected atomist addresses
- **Notes**: Atomist controls vault configuration

### AC-005: ALPHA_ROLE Assignment
- **Condition**: ALPHA_ROLE is assigned to the expected addresses (bots/strategies)
- **How to check**: `AccessManager.hasRole(200, address)`
- **Expected result**: Expected alpha executor addresses
- **Notes**: Alpha can execute any fuse actions - must be trusted

### AC-005b: Role Separation (AC-001 - AC-005)
- **Condition**: No address holds more than one role among: ADMIN_ROLE, OWNER_ROLE, GUARDIAN_ROLE, ATOMIST_ROLE, ALPHA_ROLE
- **How to check**: For each role holder from AC-001-AC-005, verify they don't hold any other role from this group
- **Expected result**: Each address has exactly 1 role (or 0 in the case of ADMIN)
- **Notes**: CRITICAL - Combining roles violates separation of concerns and enables privilege escalation. E.g., an address with OWNER+ALPHA can grant itself roles and execute operations

### AC-006: TECH_PLASMA_VAULT_ROLE
- **Condition**: TECH_PLASMA_VAULT_ROLE is assigned ONLY to the PlasmaVault address
- **How to check**: `AccessManager.hasRole(3, vaultAddress)` + check logs
- **Expected result**: Only the vault has this role
- **Notes**: System role - should not be assigned to any other address

### AC-007: GUARDIAN_ROLE Assignment
- **Condition**: GUARDIAN_ROLE is assigned to the expected address
- **How to check**: `AccessManager.hasRole(2, address)`
- **Expected result**: Expected guardian (may be multisig or EOA for fast response)
- **Notes**: Guardian can pause the vault - important for emergencies

### AC-008: Function-Role Mappings
- **Condition**: Each vault function has the correct role assigned in AccessManager
- **How to check**: `AccessManager.getTargetFunctionRole(vault, selector)` for each selector
- **Expected result**: Mappings match the table below
- **Notes**: Incorrect mapping = unauthorized access

#### Required function mappings:

| Function | Expected Role |
|----------|---------------|
| `execute(FuseAction[])` | ALPHA_ROLE (200) |
| `deposit(uint256,address)` | WHITELIST_ROLE (800) or PUBLIC_ROLE (depends on isPublic) |
| `mint(uint256,address)` | WHITELIST_ROLE (800) or PUBLIC_ROLE (depends on isPublic) |
| `depositWithPermit(...)` | WHITELIST_ROLE (800) or PUBLIC_ROLE (depends on isPublic) |
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
| `transfer(address,uint256)` | TECH_VAULT_TRANSFER_SHARES_ROLE (7) (default) or PUBLIC_ROLE (after enableTransferShares) |
| `transferFrom(...)` | TECH_VAULT_TRANSFER_SHARES_ROLE (7) (default) or PUBLIC_ROLE (after enableTransferShares) |
| `transferRequestSharesFee(...)` | TECH_WITHDRAW_MANAGER_ROLE (6) |
| `setMinimalExecutionDelaysForRoles(...)` | OWNER_ROLE (1) |

#### AccessManager mappings (not vault):

| Function | Expected Role |
|----------|---------------|
| `AccessManager.initialize(...)` | ADMIN_ROLE (0) |
| `AccessManager.convertToPublicVault(address)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.enableTransferShares(address)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.setMinimalExecutionDelaysForRoles(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `AccessManager.cancel(...)` | GUARDIAN_ROLE (2) |
| `AccessManager.updateTargetClosed(...)` | GUARDIAN_ROLE (2) |
| `AccessManager.canCallAndUpdate(...)` | TECH_PLASMA_VAULT_ROLE (3) |

#### WithdrawManager mappings (if deployed):

| Function | Expected Role |
|----------|---------------|
| `requestShares(...)` | PUBLIC_ROLE (public access to requests) |
| `releaseFunds(...)` | ALPHA_ROLE (200) |
| `updateWithdrawWindow(...)` | ATOMIST_ROLE (100) |
| `updatePlasmaVaultAddress(...)` | ATOMIST_ROLE (100) |
| `canWithdrawFromRequest(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `canWithdrawFromUnallocated(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `updateWithdrawFee(...)` | WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE (902) |
| `updateRequestFee(...)` | WITHDRAW_MANAGER_REQUEST_FEE_ROLE (901) |

#### PriceOracleMiddlewareManager mappings (if deployed):

| Function | Expected Role |
|----------|---------------|
| `setAssetsPriceSources(...)` | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE (1200) |
| `removeAssetsPriceSources(...)` | PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE (1200) |
| `setPriceOracleMiddleware(...)` | ATOMIST_ROLE (100) |
| `updatePriceValidation(...)` | ATOMIST_ROLE (100) |
| `removePriceValidation(...)` | ATOMIST_ROLE (100) |
| `validateAllAssetsPrices(...)` | TECH_PLASMA_VAULT_ROLE (3) |
| `validateAssetsPrices(...)` | TECH_PLASMA_VAULT_ROLE (3) |

#### RewardsClaimManager mappings (if deployed):

| Function | Expected Role |
|----------|---------------|
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
- **Condition**: Each role has the correct admin role
- **How to check**: Verify admin role settings for each role
- **Expected result**:
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
- **Notes**: Incorrect hierarchy = privilege escalation. TECH_* roles with self-admin are immutable after initialization

### AC-011: Execution Delays
- **Condition**: Roles with execution delay have minimum delays set
- **How to check**: Check delay per role in AccessManager
- **Expected result**: Consistent with governance policy (e.g., ATOMIST 24h delay)
- **Notes**: Delays protect against flash-loan governance attacks. For ADMIN_ROLE (0), zero delay is informational (not a warning) when no address holds the role — an empty ADMIN with zero delay poses no risk.

### AC-012: Redemption Delay
- **Condition**: REDEMPTION_DELAY_IN_SECONDS is set reasonably
- **How to check**: Read from AccessManager
- **Expected result**: > 0 and <= 7 days (604800 seconds)
- **Notes**: Protects against deposit-withdraw sandwich attacks

### AC-013: Target Closed Status
- **Condition**: Vault is NOT in paused state (unless intended)
- **How to check**: `AccessManager.isTargetClosed(vaultAddress)`
- **Expected result**: false (if vault should be active)
- **Notes**: Guardian can close the vault in an emergency

### AC-014: TECH roles - Immutability and Correctness
- **Condition**: TECH_* roles are assigned ONLY to system contracts AND those contracts are valid components of the vault stack
- **How to check**: For each TECH_* role:
  1. Check the role holder (who holds it)
  2. Verify the holder is a valid contract in the vault stack (not a foreign address)
  3. Verify the holder is associated with THIS vault (not another one)
- **Expected result**:
  - TECH_PLASMA_VAULT_ROLE (3) → holder == address of THIS PlasmaVault
  - TECH_WITHDRAW_MANAGER_ROLE (6) → holder == WithdrawManager of THIS vault (matches vault storage)
  - TECH_CONTEXT_MANAGER_ROLE (5) → holder == ContextManager of THIS vault
  - TECH_PERFORMANCE_FEE_MANAGER_ROLE (400) → holder == FeeManager of THIS vault (matches getPerformanceFeeData().feeAccount)
  - TECH_MANAGEMENT_FEE_MANAGER_ROLE (500) → holder == FeeManager of THIS vault (matches getManagementFeeData().feeAccount)
  - TECH_REWARDS_CLAIM_MANAGER_ROLE (601) → holder == RewardsClaimManager of THIS vault (matches getRewardsClaimManagerAddress())
- **Notes**: CRITICAL if the holder doesn't match the address stored in the vault. These roles should never be reassigned to other contracts

### AC-015: FUSE_MANAGER_ROLE Assignment
- **Condition**: FUSE_MANAGER_ROLE is assigned to expected addresses
- **How to check**: `AccessManager.hasRole(300, address)`
- **Expected result**: Only authorized addresses
- **Notes**: Fuse manager can add/remove fuses - impacts strategy

### AC-016: No Unauthorized Role Holders
- **Condition**: No role has unauthorized holders
- **How to check**: Analyze `RoleGranted` and `RoleRevoked` events from AccessManager
- **Expected result**: Every holder is expected
- **Notes**: Regular verification of all roles

---

## MEDIUM

### AC-020: ContextManager Approved Targets
- **Condition**: If ContextManager is used - approved targets are ONLY contracts from this vault's stack
- **How to check**: `ContextManager.getApprovedTargets()` → list of addresses. Each address must be one of: PlasmaVault, WithdrawManager, FeeManager, RewardsClaimManager, PriceOracleMiddleware, or PriceOracleMiddlewareManager of this vault
- **Expected result**: Only addresses of contracts belonging to this vault's stack. No foreign addresses
- **Notes**: Approved target outside the vault stack = potential privilege escalation via context manipulation

### AC-021: AccessManager Initialization
- **Condition**: AccessManager is initialized (cannot be re-initialized)
- **How to check**: Try calling `initialize()` - should revert
- **Expected result**: Revert

### AC-022: Pre-Hooks Configuration and Origin
- **Condition**: Pre-hooks are configured correctly AND their contracts originate from a trusted source
- **How to check**:
  1. Read pre-hooks mapping from vault (selector → implementation)
  2. For each pre-hook contract verify:
     - Code is verified on a block explorer
     - Contract was deployed by the IPOR deployer (check tx deployer address)
     - Or contract code matches the code from the ipor-fusion repository (compare bytecode)
- **Expected result**: All pre-hook implementations are known contracts from the IPOR Fusion repo, deployed by a trusted deployer
- **Notes**: Pre-hook is executed BEFORE every vault operation. A foreign/unverified pre-hook can block or manipulate operations
