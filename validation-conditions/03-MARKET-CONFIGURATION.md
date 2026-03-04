# 03 - Market Configuration Validation

## Purpose
Verify the configuration of individual markets in the vault.
Each market must have: Market ID, Balance Fuse, Substrates, Fuses.

---

## Predefined Market IDs (IporFusionMarkets.sol)

| Market ID | Name | Protocol |
|-----------|------|----------|
| 1 | AAVE_V3 | Aave V3 lending |
| 2 | COMPOUND_V3_USDC | Compound V3 USDC |
| 3 | GEARBOX_POOL_V3 | Gearbox V3 pool |
| 4 | GEARBOX_FARM_DTOKEN_V3 | Gearbox V3 farming |
| 5 | FLUID_INSTADAPP_POOL | Fluid pool |
| 6 | FLUID_INSTADAPP_STAKING | Fluid staking |
| 7 | ERC20_VAULT_BALANCE | Underlying balance in vault |
| 8 | UNISWAP_SWAP_V3_POSITIONS | Uniswap V3 positions |
| 9 | UNISWAP_SWAP_V2 | Uniswap V2 swaps |
| 10 | UNISWAP_SWAP_V3 | Uniswap V3 swaps |
| 11 | EULER_V2 | Euler V2 |
| 12 | UNIVERSAL_TOKEN_SWAPPER | Universal Token Swapper |
| 13 | COMPOUND_V3_USDT | Compound V3 USDT |
| 14 | MORPHO | Morpho Blue |
| 15 | SPARK | Spark (Aave fork) |
| 16 | CURVE_POOL | Curve pool |
| 17 | CURVE_LP_GAUGE | Curve gauge |
| 18 | RAMSES_V2_POSITIONS | Ramses V2 positions |
| 19 | MORPHO_FLASH_LOAN | Morpho flash loan |
| 20 | AAVE_V3_LIDO | Aave V3 Lido |
| 21 | MOONWELL | Moonwell |
| 22 | MORPHO_REWARDS | Morpho rewards |
| 23 | PENDLE | Pendle |
| 24 | FLUID_REWARDS | Fluid rewards |
| 25 | CURVE_GAUGE_ERC4626 | Curve gauge (ERC4626) |
| 26 | COMPOUND_V3_WETH | Compound V3 WETH |
| 27 | HARVEST_HARD_WORK | Harvest yield farming |
| 28 | TAC_STAKING | TAC staking |
| 29 | LIQUITY_V2 | Liquity V2 |
| 30 | AERODROME | Aerodrome |
| 31 | VELODROME_SUPERCHAIN | Velodrome Superchain |
| 32 | VELODROME_SUPERCHAIN_SLIPSTREAM | Velodrome Superchain Slipstream |
| 33 | AREODROME_SLIPSTREAM | Aerodrome Slipstream |
| 34 | STAKE_DAO_V2 | Stake DAO V2 |
| 35 | SILO_V2 | Silo V2 |
| 36 | BALANCER | Balancer V3 |
| 37 | YIELD_BASIS_LT | Yield Basis LT |
| 38 | ENSO | Enso |
| 39 | EBISU | Ebisu |
| 40 | ASYNC_ACTION | Async Action |
| 41 | MORPHO_LIQUIDITY_IN_MARKETS | Morpho liquidity |
| 42 | ODOS_SWAPPER | Odos Swapper |
| 43 | VELORA_SWAPPER | Velora Swapper |
| 45 | AAVE_V4 / MIDAS | Aave V4 / Midas (WARNING: duplicate ID!) |
| 46 | NAPIER | Napier |
| 100_001 - 100_020 | ERC4626_0001 - ERC4626_0020 | Generic ERC4626 vaults |
| 200_001 - 200_010 | META_MORPHO_0001-0010 | MetaMorpho vaults |
| type(uint256).max | ZERO_BALANCE_MARKET | Zero balance (special) |
| type(uint256).max - 1 | ASSETS_BALANCE_VALIDATION | Assets validation (special) |
| type(uint256).max - 2 | EXCHANGE_RATE_VALIDATOR | Exchange rate (special) |

> **WARNING**: Market ID 45 is assigned to both AAVE_V4 and MIDAS in IporFusionMarkets.sol - this is a potential bug in the source code.

---

## CRITICAL - Per Market

### MC-001: Balance Fuse Assigned
- **Condition**: Every active market HAS exactly ONE balance fuse assigned
- **How to check**: `PlasmaVaultGovernance.isBalanceFuseSupported(marketId, expectedFuseAddress)`
- **Expected result**: true for every active market
- **Notes**: WITHOUT a balance fuse the vault CANNOT track balances in that market!

### MC-002: Balance Fuse Market ID Match
- **Condition**: Balance fuse has the same MARKET_ID as the market it's assigned to
- **How to check**: `IFuseCommon(balanceFuse).MARKET_ID()` == expected marketId
- **Expected result**: Market ID match
- **Notes**: Mismatch = incorrect balance readings = incorrect share valuation

### MC-003: Market Substrates Configured
- **Condition**: Every active market has configured substrates (allowed assets/addresses)
- **How to check**: `PlasmaVaultGovernance.getMarketSubstrates(marketId)`
- **Expected result**: Non-empty substrate list for every active market
- **Notes**: Empty substrates = fuse cannot operate on any asset

### MC-004: Substrate Correctness
- **Condition**: Substrates contain CORRECT addresses/identifiers for the given protocol
- **How to check**: Decode substrates and compare with expected assets
  - For lending: token addresses (USDC, DAI, etc.)
  - For Morpho: market IDs (bytes32)
  - For Uniswap: token pair addresses
  - For Balancer: pool addresses + tokens
  - For Aerodrome: gauge addresses
- **Expected result**: All substrates are valid addresses/IDs
- **Notes**: Incorrect substrate = operation on unintended asset/market

### MC-005: Supply/Interaction Fuses Registered
- **Condition**: Fuses needed for market operations are registered in the vault
- **How to check**: `PlasmaVaultGovernance.isFuseSupported(fuseAddress)` for each fuse
- **Expected result**: true for all required fuses
- **Notes**: Unregistered fuse = execute() will revert

### MC-006: Fuse Market ID Match
- **Condition**: Every fuse (supply, borrow, etc.) has a MARKET_ID matching its market
- **How to check**: `IFuseCommon(fuse).MARKET_ID()` == expected marketId
- **Expected result**: Match
- **Notes**: Mismatch = fuse operates on the wrong market

### MC-007: ERC20_VAULT_BALANCE Market
- **Condition**: ERC20_VAULT_BALANCE market (special ID) has a balance fuse
- **How to check**: Check balance fuse for this market
- **Expected result**: Erc20BalanceFuse is assigned
- **Notes**: This market tracks the native underlying token balance in the vault

---

## HIGH

### MC-010: Fuse Constructor Parameters
- **Condition**: Fuses are deployed with correct parameters (market ID, protocol addresses)
- **How to check**: Read immutable variables from the fuse (e.g., AAVE_POOL, COMET, MORPHO)
- **Expected result**: Correct protocol addresses on the given chain
- **Notes**: Incorrect protocol address = operations fail or go to the wrong contract

### MC-011: Substrate Type Consistency
- **Condition**: Substrate type matches the type expected by the fuse
- **How to check**: Verify substrate formats:
  - Asset substrates: `bytes32(uint256(uint160(address)))`
  - Morpho market IDs: raw bytes32 from Morpho
  - Gauge substrates: encoded gauge addresses
  - Pool substrates: encoded pool addresses
- **Expected result**: Format matches the fuse implementation
- **Notes**: Incorrect format = fuse won't recognize the substrate

### MC-012: Active Markets List
- **Condition**: Active markets list matches expectations
- **How to check**: `PlasmaVaultGovernance.getActiveMarketsInBalanceFuses()`
- **Expected result**: All intended markets are on the list
- **Notes**: Missing market = not tracked in totalAssets

### MC-013: All Fuses Listed
- **Condition**: All required fuses are in the supported fuses list
- **How to check**: `PlasmaVaultGovernance.getFuses()`
- **Expected result**: Complete list of all required fuses
- **Notes**: Compare with expected configuration

### MC-014: No Obsolete Fuses
- **Condition**: No old/unnecessary fuses remain in the list
- **How to check**: `PlasmaVaultGovernance.getFuses()` - check each one
- **Expected result**: Every fuse is needed and up-to-date
- **Notes**: Old fuses may have bugs/vulnerabilities

### MC-015: Substrate Not Over-Permissive
- **Condition**: Substrates don't contain unnecessary assets
- **How to check**: Compare substrates with intended strategy
- **Expected result**: Only needed assets/markets
- **Notes**: Over-permissive substrates = Alpha can operate on unintended assets

---

## MEDIUM

### MC-020: Balance Fuse Returns Sensible Value
- **Condition**: Balance fuse returns a reasonable value for the current state
- **How to check**: Call `balanceOf()` on the balance fuse (statically)
- **Expected result**: Value >= 0 and consistent with the actual state on the protocol
- **Notes**: Functional test

### MC-021: Supply Fuse Permissions on Protocol
- **Condition**: Vault has appropriate approvals/permissions on the underlying protocol
- **How to check**: Check ERC20 allowances from vault to protocols
- **Expected result**: Approvals are set dynamically by the fuse (not pre-set)
- **Notes**: Fuses should do approve -> interact -> revoke approve

### MC-022: Market ID Uniqueness
- **Condition**: Each market ID is used exactly once
- **How to check**: Verify no duplicates in active markets
- **Expected result**: Unique market IDs
