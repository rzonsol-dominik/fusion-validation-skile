# 09 - Balance Tracking Validation

## Purpose
Verify the balance tracking system: totalAssets, per-market balances, balance fuse correctness.

---

## totalAssets Formula

```
totalAssets() = vault.balance (ERC20 underlying in vault)
              + totalAssetsInAllMarkets (sum across all markets)
              + rewardsClaimManager.balanceOf() (vested rewards)
```

### Update process (PlasmaVaultMarketsLib):
1. Call `balanceFuse.balanceOf()` → value in USD (18 decimals WAD)
2. Fetch underlying asset price from `IPriceOracleMiddleware`
3. Convert: `(balance_usd * 10^asset_decimals) / price_usd`
4. Update delta in `PlasmaVaultLib.getTotalAssetsInMarket(marketId)`
5. Resolve dependencies (update related markets)
6. Validate market limits (if active)

---

## CRITICAL

### BT-001: totalAssets >= Vault ERC20 Balance
- **Condition**: totalAssets is not less than the ERC20 underlying balance in the vault
- **How to check**: `vault.totalAssets()` >= `ERC20(asset).balanceOf(vault)`
- **Expected result**: totalAssets >= balance (difference = assets in markets + rewards)
- **Notes**: totalAssets < balance indicates incorrect balance fuse configuration

### BT-002: totalAssets Consistency
- **Condition**: Sum of individual components == totalAssets()
- **How to check**:
  ```
  calculated = ERC20(asset).balanceOf(vault)
  for each marketId in activeMarkets:
      calculated += vault.totalAssetsInMarket(marketId)
  if rewardsManager != address(0):
      calculated += rewardsManager.balanceOf()
  assert |calculated - vault.totalAssets()| <= rounding_tolerance
  ```
- **Expected result**: Match (tolerance +-1 for rounding per market)
- **Notes**: Mismatch = something is wrong with balance tracking. For leveraged/looping vaults (where totalAssets >> computed sum), a large discrepancy is expected because balance fuses report net positions, not gross collateral — this is informational, not a failure.

### BT-003: Per-Market Balance vs Protocol State
- **Condition**: Each totalAssetsInMarket() reflects the ACTUAL state on the protocol
- **How to check**: For each active market compare:
  - `vault.totalAssetsInMarket(marketId)` (what vault thinks)
  - Actual state on the protocol (e.g., aToken.balanceOf(vault) on Aave)
- **Expected result**: Difference < 0.1% (small difference may exist due to accrued interest)
- **Notes**: Large difference = balance fuse is incorrect or stale

### BT-004: Balance Fuse Returns USD in WAD
- **Condition**: Balance fuse returns value in USD with 18 decimals
- **How to check**: Call `balanceFuse.balanceOf()` and check scale
- **Expected result**: Value in WAD (e.g., 1000 USD = 1000 * 1e18)
- **Notes**: Incorrect scale = totalAssets will be off by orders of magnitude

### BT-005: Share Price Reasonability
- **Condition**: Share price (convertToAssets(1e(decimals))) is reasonable
- **How to check**: `vault.convertToAssets(10 ** vault.decimals())`
- **Expected result**: Value close to 1 underlying token (with profit accumulation over time). For USD-pegged assets, expected range is [0.5, 2.0]. For non-USD assets (ETH, BTC, PAXG, EURC — detected via oracle price >$10 or <$0.10), use wider range [0.01, 100.0].
- **Notes**: Share price radically != 1 (e.g., 0 or 1e30) indicates a problem. Non-USD assets naturally have a different price scale, so the acceptable range is widened accordingly.

---

## HIGH

### BT-010: Balance Update Freshness
- **Condition**: Market balances are regularly updated
- **How to check**: Check MarketBalancesUpdated events or compare with on-chain state
- **Expected result**: Balances updated within the last 24h (or more frequently)
- **Notes**: Stale balances = incorrect share valuation

### BT-011: Balance After Execute
- **Condition**: After execute() balances of affected markets are updated
- **How to check**: Monitor ExecuteFinished events
- **Expected result**: Events contain updated values
- **Notes**: Automatically performed in execute()

### BT-012: Performance Fee Calculation Basis
- **Condition**: Performance fee is calculated on NET total assets (after deducting management fee)
- **How to check**: Logic in execute():
  ```
  netTotalAssets = totalAssets() - getUnrealizedManagementFee()
  // ... execute actions ...
  profit = newNetTotalAssets - netTotalAssets
  fee = profit * performanceFeeRate
  ```
- **Expected result**: Fee only on net profit
- **Notes**: Built into the contract

### BT-013: Rewards Balance Inclusion
- **Condition**: If RewardsClaimManager exists - its balance is included in totalAssets
- **How to check**: `rewardsClaimManager.balanceOf()` > 0 when there are vested rewards
- **Expected result**: Rewards values are included
- **Notes**: Not including them = totalAssets underestimation

### BT-014: Zero Balance Markets
- **Condition**: Markets with balance 0 don't distort totalAssets
- **How to check**: Check that totalAssetsInMarket() == 0 for unused markets
- **Expected result**: 0 for each market without positions
- **Notes**: Phantom balance = overvaluation

### BT-015: Negative Balance Handling (Borrow)
- **Condition**: Markets with borrow correctly deduct debt from supply
- **How to check**: For lending markets with borrow (Aave, Compound, Morpho):
  - Balance fuse should return: supply_value - debt_value
  - If net < 0 (more borrowed than supplied) - check if this is intended
- **Expected result**: Balance = net position (supply - debt) in USD
- **Notes**: Incorrect debt deduction = overvaluation

---

## MEDIUM

### BT-020: Rounding Behavior
- **Condition**: Rounding in conversions favors the correct direction
- **How to check**: Check that vault rounds in vault's favor (not user's) on withdraw
- **Expected result**: Shares rounded up, assets rounded down on withdraw
- **Notes**: ERC4626 standard requires rounding in vault's favor

### BT-021: updateMarketsBalances Permission
- **Condition**: updateMarketsBalances() is available to UPDATE_MARKETS_BALANCES_ROLE
- **How to check**: Check function-role mapping in AccessManager
- **Expected result**: Correct role
- **Notes**: Needed for manual balance updates

### BT-022: Interest Accrual Tracking
- **Condition**: Balance fuses account for accrued interest (aTokens, cTokens)
- **How to check**: Compare balance fuse output with current aToken/cToken balances
- **Expected result**: Balance grows over time (interest accrual)
- **Notes**: Some protocols accrue interest dynamically

### BT-023: LP Position Valuation
- **Condition**: LP positions (Uniswap V3, Balancer, Curve) are correctly valued
- **How to check**: Compare balance fuse output with position value on DEX
- **Expected result**: Value close to actual (accounting for fees, IL)
- **Notes**: LP valuation is complex - may be undervalued by uncollected fees
