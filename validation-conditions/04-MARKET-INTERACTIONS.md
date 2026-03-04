# 04 - Market Interactions Validation

## Purpose
Verify inter-market interactions: dependency graph, market limits, cross-market balance tracking.

---

## CRITICAL

### MI-001: Dependency Balance Graph Configuration
- **Condition**: Markets with mutual dependencies have a configured dependency graph
- **How to check**: `PlasmaVaultGovernance.getDependencyBalanceGraph(marketId)` for each market
- **Expected result**: Correct dependency lists
- **Notes**: WITHOUT dependency graph - balance updates for one market will NOT update related markets

#### Typical dependencies that MUST be configured:

| Market | Depends on | Reason |
|--------|-----------|--------|
| UNISWAP_SWAP_V3 (swap) | ERC20_VAULT_BALANCE | Swap changes token balances in vault |
| UNISWAP_SWAP_V3_POSITIONS | ERC20_VAULT_BALANCE | LP positions use tokens from vault |
| CURVE_POOL | ERC20_VAULT_BALANCE | LP requires tokens |
| CURVE_LP_GAUGE | CURVE_POOL | Gauge stakes LP tokens |
| BALANCER_* | ERC20_VAULT_BALANCE | Pool uses tokens |
| AAVE_V3 (with borrow) | ERC20_VAULT_BALANCE | Borrow adds tokens to vault |
| MORPHO (with borrow) | ERC20_VAULT_BALANCE | Borrow adds tokens to vault |
| GEARBOX_FARM_DTOKEN_V3 | GEARBOX_POOL_V3 | Farm stakes dTokens from pool |
| FLUID_INSTADAPP_STAKING | FLUID_INSTADAPP_POOL | Staking uses pool tokens |
| AERODROME gauge (30) | AERODROME liquidity | Gauge stakes LP tokens |
| AERODROME_SLIPSTREAM gauge (33) | AERODROME_SLIPSTREAM pool | Gauge stakes CL positions |
| VELODROME_SUPERCHAIN gauge (31) | VELODROME_SUPERCHAIN pool | Gauge stakes LP tokens |
| VELODROME_SUPERCHAIN_SLIPSTREAM gauge (32) | VELODROME_SUPERCHAIN_SLIPSTREAM pool | Gauge stakes CL positions |
| BALANCER gauge (36) | BALANCER pool (36) | Gauge stakes BPT tokens (lp_token()) |
| STAKE_DAO_V2 (34) | (price oracle dependency) | Nested ERC4626: reward vault → LP vault → underlying |
| SILO_V2 (35) | (none - self-contained) | Internal bookkeeping via SiloConfig |
| NAPIER (46) | (no balance fuse!) | No balance fuse in code - requires custom tracking |
| Any swap market | ERC20_VAULT_BALANCE | Swap changes balance in vault |

> **NOTE on Slipstream**: Velodrome/Aerodrome Slipstream use FuseStorageLib for tracking NFT position IDs. Max 50 positions per substrate (protection against DoS gas exhaustion).

> **NOTE on Gauge fees**: Velodrome/Aerodrome POOL positions include trading fees. GAUGE positions do NOT include fees (they go to veVELO/veAERO voters). Balance fuse uses index delta mechanism.

### MI-002: Dependency Graph Completeness
- **Condition**: ALL required dependencies are in the graph
- **How to check**: For each market check getDependencyBalanceGraph() and compare with the table above
- **Expected result**: Complete dependency graph
- **Notes**: Missing dependency = phantom balance (vault thinks it has more/less than reality)

### MI-003: No Circular Dependencies
- **Condition**: Dependency graph has no cycles
- **How to check**: DFS graph traversal - check for absence of cycles
- **Expected result**: DAG (directed acyclic graph)
- **Notes**: Cycle = potential infinite loop or incorrect calculations

### MI-004: Market Limits - Active Status
- **Condition**: Market limits are active/inactive as intended
- **How to check**: `PlasmaVaultGovernance.isMarketsLimitsActivated()`
- **Expected result**: true if vault requires concentration limits
- **Notes**: Without limits Alpha can concentrate 100% in a single market

### MI-005: Market Limits - Values
- **Condition**: Each market has a percentage limit set according to strategy
- **How to check**: `PlasmaVaultGovernance.getMarketLimit(marketId)` for each market
- **Expected result**: Value in WAD (1e18 = 100%), e.g., 3e17 = 30%
- **Notes**: Sum of limits can be > 100% (limits are max per market, not allocation)

### MI-006: Market Limits - Coverage
- **Condition**: ALL active markets have defined limits (if the system is active)
- **How to check**: Check limit for each active market
- **Expected result**: Each market has limit > 0 (or intentionally 0 = no limit)
- **Notes**: Market without limit = no concentration protection for that market

---

## HIGH

### MI-010: Cross-Market Balance Consistency
- **Condition**: Sum of totalAssetsInMarket() across all markets + vault balance == totalAssets()
- **How to check**:
  ```
  sum = 0
  for each marketId in activeMarkets:
      sum += vault.totalAssetsInMarket(marketId)
  sum += ERC20(asset).balanceOf(vault)
  sum += rewardsManager.balanceOf() (if exists)
  assert sum ~= vault.totalAssets() (with rounding tolerance)
  ```
- **Expected result**: Balance (with tolerance +-1 for rounding)
- **Notes**: Inconsistency = incorrect balance fuses or missing markets

### MI-011: Swap Markets Dependencies
- **Condition**: Swap markets (Uniswap, Universal Token Swapper, Odos) have dependency on ERC20_VAULT_BALANCE
- **How to check**: getDependencyBalanceGraph() contains ERC20_VAULT_BALANCE
- **Expected result**: Dependency exists
- **Notes**: Swap changes token balances - without dependency it won't be updated

### MI-012: LP Markets Dependencies
- **Condition**: LP markets (Uniswap V3 positions, Curve, Balancer) have dependencies on constituent tokens
- **How to check**: getDependencyBalanceGraph() contains appropriate markets
- **Expected result**: Dependencies on constituent tokens
- **Notes**: LP position = two tokens, LP change affects both

### MI-013: Staking/Gauge Dependencies
- **Condition**: Staking/gauge markets have dependency on the market with the LP token
- **How to check**: getDependencyBalanceGraph()
- **Expected result**: Gauge depends on the corresponding LP pool market
- **Notes**: Stake/unstake of LP token changes LP market balance

### MI-014: Borrow Market Dependencies
- **Condition**: Markets with borrow (Aave, Compound, Morpho, Euler) have dependency on ERC20_VAULT_BALANCE
- **How to check**: getDependencyBalanceGraph()
- **Expected result**: Dependency on ERC20_VAULT_BALANCE
- **Notes**: Borrow brings tokens to vault, repay removes them

### MI-015: Market Limits Sum Reasonability
- **Condition**: Sum of limits is reasonable for the strategy
- **How to check**: Sum all market limits
- **Expected result**: Sum >= 100% (1e18) so vault can fully allocate
- **Notes**: If sum < 100% the vault cannot fully allocate capital

---

## MEDIUM

### MI-020: Dependency Graph Depth
- **Condition**: Dependency graph depth is not excessively large
- **How to check**: Measure max graph depth
- **Expected result**: Depth <= 3-4 (reasonable complexity)
- **Notes**: Too deep graph = more gas for balance updates

### MI-021: Market Interaction Gas Cost
- **Condition**: Execute with multiple markets fits within block gas limit
- **How to check**: Estimate gas for execute() with a typical set of actions
- **Expected result**: Gas < 50% block gas limit
- **Notes**: Too expensive execute = Alpha cannot operate

### MI-022: Balance Update After Execute
- **Condition**: After execute() all affected markets + dependencies are updated
- **How to check**: Compare totalAssetsInMarket() before and after execute()
- **Expected result**: Values updated correctly
- **Notes**: Functional test on production after initial transactions
