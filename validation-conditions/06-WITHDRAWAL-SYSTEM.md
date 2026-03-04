# 06 - Withdrawal System Validation

## Purpose
Verify the withdrawal system: instant withdrawal fuses, scheduled withdrawals, WithdrawManager.

---

## CRITICAL

### WS-001: Instant Withdrawal Fuses Configured
- **Condition**: Instant withdrawal fuses are configured for every market from which the vault may need to withdraw
- **How to check**: `PlasmaVaultGovernance.getInstantWithdrawalFuses()`
- **Expected result**: Non-empty list of fuses (if vault has assets in markets)
- **Notes**: WITHOUT instant withdrawal fuses users CANNOT withdraw assets deposited in protocols. If fuses list is empty, see WS-005 for per-market coverage analysis — many vaults operate without instant withdrawal fuses when using scheduled withdrawals via WithdrawManager.

### WS-002: Instant Withdrawal Fuses Order
- **Condition**: Fuse order is optimal (cheapest/most liquid first)
- **How to check**: `getInstantWithdrawalFuses()` + order analysis
- **Expected result**:
  1. First: ERC20 vault balance (cheapest)
  2. Then: Most liquid markets (Aave, Compound)
  3. Last: Less liquid (LP positions, staking)
- **Notes**: Wrong order = higher gas, worse execution

### WS-003: Instant Withdrawal Fuses Parameters
- **Condition**: Parameters for each instant withdrawal fuse are correct
- **How to check**: `getInstantWithdrawalFusesParams(fuse, index)` for each fuse
- **Expected result**:
  - params[0] = reserved for amount (set dynamically)
  - params[1+] = fuse-specific parameters (e.g., asset addresses, market IDs)
- **Notes**: Incorrect parameters = withdrawal fails

### WS-004: Instant Withdrawal Fuses Support IFuseInstantWithdraw
- **Condition**: Every fuse in the list implements IFuseInstantWithdraw
- **How to check**: Check if fuse has `instantWithdraw(bytes32[])` method
- **Expected result**: All fuses support the interface
- **Notes**: Fuse without this interface won't be used for withdrawals

### WS-005: Withdrawal Coverage
- **Condition**: Instant withdrawal fuses cover ALL markets in which the vault holds assets
- **How to check**: Compare markets with balance > 0 against markets covered by instant withdrawal fuses
- **Expected result**: Every market with assets has a corresponding withdrawal fuse
- **Notes**: Market without a withdrawal fuse = locked funds (assets inaccessible for withdrawal)

### WS-006: WithdrawManager Connected to Vault
- **Condition**: WithdrawManager is correctly connected to the vault
- **How to check**: Check vault storage + AccessManager role TECH_WITHDRAW_MANAGER_ROLE
- **Expected result**: WithdrawManager has TECH_WITHDRAW_MANAGER_ROLE and is stored in vault

---

## HIGH

### WS-010: Withdraw Window Configuration
- **Condition**: Withdraw window is configured reasonably
- **How to check**: `WithdrawManager.getWithdrawWindow()`
- **Expected result**: Reasonable value (e.g., 1 hour - 7 days)
- **Notes**: Too short = users can't make it; too long = capital inefficiency

### WS-011: Request Fee Configuration
- **Condition**: Request fee is reasonable
- **How to check**: Read request fee from WithdrawManager
- **Expected result**: Value in WAD (e.g., 1e15 = 0.1%), must be < 100%
- **Notes**: Too high a fee will deter users

### WS-012: Withdraw Fee Configuration
- **Condition**: Withdraw fee is reasonable
- **How to check**: Read withdraw fee from WithdrawManager
- **Expected result**: Value in WAD, must be < 100%
- **Notes**: Applied to unallocated withdrawals

### WS-013: ALPHA Can Release Funds
- **Condition**: Account with ALPHA_ROLE can call releaseFunds()
- **How to check**: Check function-role mapping in AccessManager
- **Expected result**: releaseFunds() requires ALPHA_ROLE
- **Notes**: Without the ability to release = scheduled withdrawals don't work

### WS-014: Withdrawal Attempt Limit
- **Condition**: REDEEM_ATTEMPTS (10) is sufficient for the number of markets
- **How to check**: Number of instant withdrawal fuses vs REDEEM_ATTEMPTS constant
- **Expected result**: Number of fuses <= 10
- **Notes**: Vault tries max 10 times to withdraw from different fuses

### WS-015: Withdrawal Fuse Duplicate Handling
- **Condition**: The same fuse can appear multiple times with different parameters
- **How to check**: Check for duplicates in getInstantWithdrawalFuses()
- **Expected result**: Duplicates are allowed (different params for the same fuse)
- **Notes**: E.g., AaveV3SupplyFuse can appear 2x - once for USDC, once for DAI

---

## MEDIUM

### WS-020: Withdrawal Gas Estimation
- **Condition**: Withdrawal via the longest path fits within gas limit
- **How to check**: Gas estimation for worst-case withdrawal
- **Expected result**: Gas < block gas limit
- **Notes**: Too many fuses in the chain = withdrawal may fail

### WS-021: Slippage on Withdrawal
- **Condition**: DEFAULT_SLIPPAGE_IN_PERCENTAGE (2%) is acceptable
- **How to check**: Constant in the contract
- **Expected result**: 2% is reasonable for the given strategy
- **Notes**: Vault tries to withdraw `amount + 10` (WITHDRAW_FROM_MARKETS_OFFSET) as a cushion

### WS-022: Last Release Funds Timestamp
- **Condition**: In production, lastReleaseFundsTimestamp is current
- **How to check**: `WithdrawManager.getLastReleaseFundsTimestamp()`
- **Expected result**: Recent timestamp (if vault is active)
