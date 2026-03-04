# 12 - Production Validation Flow

## Purpose
Production validation sequence. Step-by-step guide to verify a vault.

---

## PHASE 1: Vault Identification

```
INPUT: PlasmaVault address in production
```

### Step 1.1: Basic data
```
vault.asset()                     → underlying token
vault.name()                      → share token name
vault.symbol()                    → share token symbol
vault.decimals()                  → decimals (asset + 2)
vault.totalSupply()               → total shares
vault.totalAssets()               → total assets under management
```

### Step 1.2: Key addresses
```
PlasmaVaultGovernance.getAccessManagerAddress()      → AccessManager
PlasmaVaultGovernance.getPriceOracleMiddleware()      → PriceOracle
PlasmaVaultGovernance.getRewardsClaimManagerAddress() → RewardsClaimManager
WithdrawManager address (from vault storage)          → WithdrawManager
Implementation slot read                              → Implementation contract
PlasmaVaultBase address (from vault storage)          → Base extension
```

---

## PHASE 2: Access Control (02-ACCESS-CONTROL.md)

### Step 2.1: Critical roles
```
For each role in the table:
  AccessManager.hasRole(roleId, expectedAddress) → true/false

Check:
  - ADMIN_ROLE (0) → multisig
  - OWNER_ROLE (1) → multisig
  - GUARDIAN_ROLE (2) → emergency responder
  - ATOMIST_ROLE (100) → governance
  - ALPHA_ROLE (200) → executor bot
  - TECH_PLASMA_VAULT_ROLE (3) → only vault
```

### Step 2.2: Function mappings
```
For each public vault function:
  AccessManager.getTargetFunctionRole(vault, selector) → roleId
  Compare with expected role
```

### Step 2.3: Vault status
```
AccessManager.isTargetClosed(vault) → false (if active)
```

### Step 2.4: Redemption Delay
```
AccessManager.REDEMPTION_DELAY_IN_SECONDS() → uint256
Check: > 0 and <= 604800 (7 days max)
Protects against deposit-withdraw sandwich attacks
```

---

## PHASE 3: Market Configuration (03-MARKET-CONFIGURATION.md)

### Step 3.1: Active markets list
```
PlasmaVaultGovernance.getActiveMarketsInBalanceFuses() → uint256[]
```

### Step 3.2: Per market validation
```
For each marketId in list:

  a) Balance fuse:
     PlasmaVaultGovernance.isBalanceFuseSupported(marketId, fuseAddr) → true
     IFuseCommon(fuse).MARKET_ID() == marketId

  b) Substrates:
     PlasmaVaultGovernance.getMarketSubstrates(marketId) → bytes32[]
     Decode and verify address/ID correctness

  c) Market balance:
     vault.totalAssetsInMarket(marketId) → uint256
```

### Step 3.3: Fuses list
```
PlasmaVaultGovernance.getFuses() → address[]
For each fuse:
  IFuseCommon(fuse).MARKET_ID() → marketId
  Verify market is active
```

---

## PHASE 4: Inter-Market Interactions (04-MARKET-INTERACTIONS.md)

### Step 4.1: Dependency graph
```
For each active marketId:
  PlasmaVaultGovernance.getDependencyBalanceGraph(marketId) → uint256[]
  Check completeness (dependency table in 04-MARKET-INTERACTIONS.md)
```

### Step 4.2: Market limits
```
PlasmaVaultGovernance.isMarketsLimitsActivated() → bool

If true:
  For each marketId:
    PlasmaVaultGovernance.getMarketLimit(marketId) → uint256 (WAD)
```

---

## PHASE 5: Withdrawal System (06-WITHDRAWAL-SYSTEM.md)

### Step 5.1: Instant withdrawal fuses
```
PlasmaVaultGovernance.getInstantWithdrawalFuses() → address[]

For each fuse and index:
  PlasmaVaultGovernance.getInstantWithdrawalFusesParams(fuse, index) → bytes32[]
  Verify parameters
```

### Step 5.2: WithdrawManager config
```
WithdrawManager.getWithdrawWindow() → uint256
Request fee and withdraw fee
```

---

## PHASE 6: Fee System (07-FEE-SYSTEM.md)

### Step 6.1: Fee data
```
PlasmaVaultGovernance.getPerformanceFeeData() → (feeAccount, feeInPercentage)
PlasmaVaultGovernance.getManagementFeeData() → (feeAccount, feeInPercentage, lastUpdateTimestamp)
```

### Step 6.2: Fee Manager details
```
FeeManager address from fee account
FeeManager recipients and fee splits
Total fee <= max
```

---

## PHASE 7: Price Oracle (08-PRICE-ORACLE.md)

### Step 7.1: Oracle test
```
For each token in substrates:
  PriceOracleMiddleware.getAssetPrice(token) → (price, decimals)
  Check: price > 0, decimals == 18
  Compare with market price
```

---

## PHASE 8: Balance Tracking (09-BALANCE-TRACKING.md)

### Step 8.1: Balance consistency check
```
calculated = ERC20(asset).balanceOf(vault)
for each marketId:
    calculated += vault.totalAssetsInMarket(marketId)
if rewardsManager != address(0):
    calculated += rewardsManager.balanceOf()

assert |calculated - vault.totalAssets()| <= tolerance
```

### Step 8.2: Share price sanity
```
vault.convertToAssets(10 ** vault.decimals()) → ~1 underlying token
vault.convertToShares(10 ** assetDecimals) → ~1e(vault.decimals()) shares
```

---

## PHASE 9: Rewards (10-REWARDS-SYSTEM.md)

### Step 9.1: Rewards config (if used)
```
rewardsManager.getVestingData() → vestingTime, balances
rewardsManager.getRewardsFuses() → registered fuses
rewardsManager.balanceOf() → current vested balance
```

---

## PHASE 10: Pre-Hooks (01-VAULT-CORE.md VC-025/VC-027)

### Step 10.1: Pre-hooks configuration
```
Read pre-hooks mapping (selector → implementation):
  - Check if required pre-hooks are configured
  - PauseFunctionPreHook - emergency pause per-function
  - ExchangeRateValidatorPreHook - exchange rate drift validation
  - UpdateBalancesPreHook / UpdateBalancesIgnoreDustPreHook
  - ValidateAllAssetsPricesPreHook
  - EIP7702DelegateValidationPreHook
```

### Step 10.2: Exchange Rate Validator (if used)
```
Read substrates pre-hook for ExchangeRateValidator:
  - threshold consistent with expected volatility (e.g., 1-5%)
  - Too tight = blocks normal operations
  - Too loose = no protection
```

---

## PHASE 10b: Additional Vault Core Conditions (01-VAULT-CORE.md VC-028/VC-029)

### Step 10b.1: ERC721 Receiver (if vault uses NFT positions)
```
If vault uses Uniswap V3, Ramses V2, or Slipstream:
  vault.onERC721Received(address,address,uint256,bytes) → should return selector
```

### Step 10b.2: WithdrawManager initialization
```
WithdrawManager.getPlasmaVaultAddress() → vault address
Verify it is correct
```

---

## PHASE 11: Smoke Test (optional)

### Step 11.1: Test deposit
```
1. Approve underlying token to vault
2. vault.deposit(smallAmount, testAddress)
3. Check: shares received > 0
4. vault.totalAssets() increased
```

### Step 11.2: Test withdraw
```
1. vault.withdraw(smallAmount, testAddress, testAddress)
2. Check: underlying received
3. vault.totalAssets() decreased
```

### Step 11.3: Test execute (requires ALPHA_ROLE)
```
1. Prepare FuseAction for the simplest market
2. vault.execute([action])
3. Check: totalAssetsInMarket() updated
```

---

## FINAL REPORT

After completing validation, create a report:

```
# Vault Validation Report
- Vault Address: 0x...
- Chain: Ethereum / Arbitrum / Base / ...
- Date: YYYY-MM-DD
- Validator: ...

## Status: PASS / FAIL / PARTIAL

## Critical Issues Found:
- [ ] Issue 1
- [ ] Issue 2

## Warnings:
- [ ] Warning 1

## Conditions Checked:
- [x] VC-001: Underlying Token ✓
- [x] VC-002: Access Manager ✓
- [ ] AC-001: ADMIN_ROLE ✗ (ISSUE: ...)
...

## Recommendations:
1. ...
2. ...
```

---

## AUTOMATION

It is possible to write a script that automatically checks most conditions:

### Required RPC calls:
- ~15 calls for phases 1-2 (including redemption delay)
- ~5 * N calls for phase 3 (N = number of markets)
- ~3 * M calls for phase 5 (M = number of withdrawal fuses)
- ~K calls for phase 7 (K = number of unique tokens)
- ~P calls for phase 10 (P = number of pre-hooks)

### Tools:
- cast (foundry) for on-chain calls
- Etherscan/Basescan API for code verification
- Custom script in Solidity/Python/TypeScript
