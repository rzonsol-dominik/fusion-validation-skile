# 05 - Fuses Catalog & Per-Protocol Validation

## Purpose
Complete fuse catalog with per-protocol specific validation conditions.

---

## Fuse Architecture

### Base interfaces:
- **IFuse**: `enter()` + `exit()` - main operations
- **IFuseCommon**: `MARKET_ID()` - market identifier
- **IFuseInstantWithdraw**: `instantWithdraw(bytes32[] params)` - instant withdrawals
- **IMarketBalanceFuse**: `balanceOf()` returns uint256 (USD, 18 decimals WAD)

### Validation patterns in fuses:
1. **Substrate validation**: Check if asset/address is allowed in MARKET_ID
2. **Amount validation**: Check that amount > 0 and <= available balance
3. **Approval management**: `forceApprove()` -> operation -> `forceApprove(0)`
4. **Exit error handling**: Caught reverts in instant withdrawal mode (emit event instead of revert)

---

## LENDING PROTOCOLS

### Aave V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AaveV2SupplyFuse | Supply/Withdraw | Asset addresses | aToken balance check |
| AaveV2BalanceFuse | Balance | - | aTokens - stable debt - variable debt |

**Conditions per vault with Aave V2:**
- [ ] FV2-001: AAVE_V2_POOL_ADDRESSES_PROVIDER address is correct (immutable in fuse - pool and data provider fetched dynamically)
- [ ] FV2-002: Pool address from provider is correct
- [ ] FV2-003: Substrates contain ONLY tokens supported by Aave V2
- [ ] FV2-004: Balance fuse correctly reads prices from Aave oracle

### Aave V3
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AaveV3SupplyFuse | Supply/Withdraw | Asset addresses | E-mode category support |
| AaveV3BorrowFuse | Borrow/Repay | Asset addresses | Variable rate only (mode=2) |
| AaveV3CollateralFuse | Collateral | Asset addresses | Enable as collateral |
| AaveV3BalanceFuse | Balance | - | aTokens - debts per substrate |

**Conditions per vault with Aave V3:**
- [ ] FV3-001: AAVE_V3_POOL_ADDRESSES_PROVIDER address correct for the given chain (immutable in fuse - pool, data provider, and oracle are fetched dynamically from this provider)
- [ ] FV3-002: Pool address from provider is correct (`provider.getPool()`)
- [ ] FV3-003: Data provider and Price Oracle from provider are correct
- [ ] FV3-004: E-mode category ID is correct (if used, < 256)
- [ ] FV3-005: Substrates are tokens supported by Aave V3 on this chain
- [ ] FV3-006: If borrow - vault has appropriate collateral
- [ ] FV3-007: Balance fuse accounts for both supply and debt
- [ ] FV3-008: There is a variant AaveV3WithPriceOracleMiddlewareBalanceFuse - check which balance fuse is used

### Compound V3
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| CompoundV3SupplyFuse | Supply/Withdraw | Asset addresses | Base token vs collateral logic |
| CompoundV3BalanceFuse | Balance | - | Comet balance tracking |

**Conditions:**
- [ ] FC3-001: COMET address correct (immutable)
- [ ] FC3-002: COMPOUND_BASE_TOKEN correct
- [ ] FC3-003: Substrates distinguish base token and collateral
- [ ] FC3-004: Balance fuse correctly distinguishes base token and collateral balance

### Morpho Blue
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| MorphoSupplyFuse | Supply/Withdraw | Morpho Market IDs (bytes32) | Market params resolution |
| MorphoBorrowFuse | Borrow/Repay | Morpho Market IDs | Shares vs amount conversion |
| MorphoCollateralFuse | Collateral | Morpho Market IDs | Collateral deposit |
| MorphoSupplyWithCallBackDataFuse | Supply with callback | Morpho Market IDs | Supply with callback data |
| MorphoFlashLoanFuse | Flash loan | - | Flash loan execution |
| MorphoBalanceFuse | Balance | - | Supply + collateral - borrow |
| MorphoOnlyLiquidityBalanceFuse | Balance (liquidity) | - | Supply liquidity only (no collateral) |

**Conditions:**
- [ ] FM-001: MORPHO address correct
- [ ] FM-002: Substrates are VALID Morpho market IDs (bytes32)
- [ ] FM-003: Each Morpho market ID exists in Morpho Blue
- [ ] FM-004: Market params (loan token, collateral, oracle, IRM, LLTV) are correct
- [ ] FM-005: Balance fuse accounts for supply shares, collateral AND borrow shares

### Euler V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| EulerV2SupplyFuse | Supply/Withdraw | Euler vault addresses | EVC integration |
| EulerV2BorrowFuse | Borrow/Repay | Euler vault addresses | SubAccount mgmt |
| EulerV2CollateralFuse | Collateral | Euler vault addresses | Controller logic |
| EulerV2ControllerFuse | Controller | Euler vault addresses | Controller enable/disable |
| EulerV2BatchFuse | Batch ops | - | Multi-call execution |
| EulerV2BalanceFuse | Balance | - | Per-vault balance tracking |

**Conditions:**
- [ ] FE-001: EVC (Ethereum Vault Connector) address correct
- [ ] FE-002: Substrates are valid Euler V2 vault addresses
- [ ] FE-003: SubAccount generation is deterministic and correct
- [ ] FE-004: Euler vaults are active and not paused

### Moonwell
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| MoonwellSupplyFuse | Supply/Withdraw | Asset addresses | mToken balance check |
| MoonwellBorrowFuse | Borrow/Repay | Asset addresses | Borrow limit check |
| MoonwellEnableMarketFuse | Market enable | Asset addresses | Comptroller enterMarkets |
| MoonwellBalanceFuse | Balance | - | Supply - borrow tracking |

**Conditions:**
- [ ] FMW-001: mToken addresses correct
- [ ] FMW-002: Comptroller address correct
- [ ] FMW-003: Market is enabled on Moonwell
- [ ] FMW-004: If borrow - vault has appropriate collateral (enterMarkets called)
- [ ] FMW-005: Balance fuse accounts for both supply and borrow (net position)

### Silo V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| SiloV2SupplyBorrowableCollateralFuse | Supply (borrowable) | Silo addresses | Borrowable collateral deposit |
| SiloV2SupplyNonBorrowableCollateralFuse | Supply (protected) | Silo addresses | Non-borrowable collateral deposit |
| SiloV2BorrowFuse | Borrow/Repay | Silo addresses | Borrow from silo |
| SiloV2BalanceFuse | Balance | - | Net position tracking |

**Conditions:**
- [ ] FS-001: Silo config addresses correct
- [ ] FS-002: Silo index correct (borrowable vs non-borrowable)
- [ ] FS-003: Distinction between borrowable and non-borrowable collateral fuse

---

## DEX & LIQUIDITY PROTOCOLS

### Uniswap V3
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| UniswapV3NewPositionFuse | Create/Close | Token pair addresses | NFT position mgmt |
| UniswapV3ModifyPositionFuse | Modify | Token pair addresses | Liquidity adjustment |
| UniswapV3CollectFuse | Collect fees | - | Fee collection |
| UniswapV3SwapFuse | Swap | Asset addresses | Path validation |
| UniswapV3Balance | Balance | - | Position value tracking |

**Conditions:**
- [ ] FU3-001: NonfungiblePositionManager address correct
- [ ] FU3-002: UniversalRouter address correct (for swaps)
- [ ] FU3-003: Substrates contain BOTH tokens of each pair
- [ ] FU3-004: Fee tier is correct (500, 3000, 10000)
- [ ] FU3-005: Tick range is reasonable for the strategy
- [ ] FU3-006: Path encoding contains ONLY allowed tokens

### Balancer V3
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| BalancerLiquidityProportionalFuse | Add/Remove | Pool + token addresses | Proportional liquidity |
| BalancerLiquidityUnbalancedFuse | Unbalanced | Pool + token addresses | Custom ratios |
| BalancerSingleTokenFuse | Single-sided | Pool + token addresses | Single token entry |
| BalancerGaugeFuse | Gauge stake | Gauge addresses | BPT staking |
| BalancerBalanceFuse | Balance | - | BPT + gauge tracking |

**Conditions:**
- [ ] FB-001: Router address correct
- [ ] FB-002: Permit2 address correct
- [ ] FB-003: Pool addresses are valid Balancer V3 pools
- [ ] FB-004: Substrates contain pool address + ALL tokens in pool
- [ ] FB-005: Token ordering in substrates matches pool token ordering

### Aerodrome
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AerodromeLiquidityFuse | Add/Remove LP | Pool addresses | Liquidity provision |
| AerodromeGaugeFuse | Gauge stake/unstake | Gauge addresses | LP staking |
| AerodromeClaimFeesFuse | Collect fees | Pool addresses | Trading fees collection |
| AerodromeBalanceFuse | Balance | - | LP + gauge tracking |

### Aerodrome Slipstream
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AreodromeSlipstreamNewPositionFuse | Create position | Token pairs | CL NFT position mgmt |
| AreodromeSlipstreamModifyPositionFuse | Modify position | Token pairs | Liquidity adjustment |
| AreodromeSlipstreamCollectFuse | Collect fees | - | Fee collection |
| AreodromeSlipstreamCLGaugeFuse | Gauge stake | Gauge addresses | CL gauge staking |
| AreodromeSlipstreamBalanceFuse | Balance | - | Position value tracking |

### Velodrome Superchain
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| VelodromeSuperchainLiquidityFuse | Add/Remove LP | Pool addresses | Liquidity provision |
| VelodromeSuperchainGaugeFuse | Gauge stake/unstake | Gauge addresses | LP staking |
| VelodromeSuperchainBalanceFuse | Balance | - | LP + gauge tracking |

### Velodrome Superchain Slipstream
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| VelodromeSuperchainSlipstreamNewPositionFuse | Create position | Token pairs | CL NFT position mgmt |
| VelodromeSuperchainSlipstreamModifyPositionFuse | Modify position | Token pairs | Liquidity adjustment |
| VelodromeSuperchainSlipstreamCollectFuse | Collect fees | - | Fee collection |
| VelodromeSuperchainSlipstreamLeafCLGaugeFuse | Gauge stake | Gauge addresses | CL gauge staking |
| VelodromeSuperchainSlipstreamBalanceFuse | Balance | - | Position value tracking |

**Conditions (Aerodrome / Velodrome common):**
- [ ] FA-001: Gauge addresses correct and active
- [ ] FA-002: Router address correct
- [ ] FA-003: Pool addresses correct
- [ ] FA-004: Substrates distinguish gauge vs pool substrates
- [ ] FA-005: Slipstream - max 50 positions per substrate (DoS gas exhaustion protection)
- [ ] FA-006: Gauge positions do NOT include trading fees (they go to veVELO/veAERO voters)

### Curve Stableswap NG
**Conditions:**
- [ ] FCS-001: Pool address correct
- [ ] FCS-002: Gauge address correct
- [ ] FCS-003: Pool coins match substrates

---

## YIELD PROTOCOLS

### Pendle
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| PendleSwapPTFuse | Swap to/from PT | Pendle market addresses | Complex swap routing |
| PendleRedeemPTAfterMaturityFuse | Redeem matured | Pendle market addresses | Maturity check |

**Conditions:**
- [ ] FP-001: Pendle router (IPActionSwapPTV3) address correct
- [ ] FP-002: Substrates are valid Pendle market addresses
- [ ] FP-003: Pendle markets are not expired/matured (unless redeem)
- [ ] FP-004: SY token, PT token are correct for the given market

### Gearbox V3
**Conditions:**
- [ ] FG-001: FarmPool (farmdToken) addresses correct
- [ ] FG-002: Underlying dToken is correct
- [ ] FG-003: FarmPool is active

---

## SWAP / ROUTER

### Universal Token Swapper
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| UniversalTokenSwapperFuse | Multi-DEX swap | Tokens + Targets + Slippage | USD slippage validation |
| UniversalTokenSwapperEthFuse | Swap with ETH wrapping | Tokens + Targets + Slippage | Same as UTS + WETH wrap/unwrap |
| UniversalTokenSwapperWithVerificationFuse | Swap with verification | Tokens + Targets + Slippage | Additional post-swap verification |
| SwapExecutor | Execution | - | Delegated swap execution |

**Conditions:**
- [ ] FTS-001: SwapExecutor address correct
- [ ] FTS-002: Substrates contain:
  - Token substrates (allowed tokens)
  - Target substrates (allowed DEX aggregators - 1inch, Odos, etc.)
  - Slippage substrates (max slippage config)
- [ ] FTS-003: Target addresses are valid DEX aggregators
- [ ] FTS-004: Slippage limit is reasonable (default 1% = 1e16 WAD)
- [ ] FTS-005: Price oracle is available for USD slippage validation

### Odos Swapper
**Conditions:**
- [ ] FOS-001: OdosSwapperFuse deployed with correct parameters
- [ ] FOS-002: Odos executor address correct

### Enso
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| EnsoFuse | Multi-protocol execution | Targets + tokens | Delegated execution via Enso |
| EnsoInitExecutorFuse | Init executor | - | Enso executor initialization |
| EnsoBalanceFuse | Balance | - | Enso position tracking |

**Conditions:**
- [ ] FEN-001: EnsoFuse with correct executor address
- [ ] FEN-002: EnsoExecutor address correct
- [ ] FEN-003: EnsoInitExecutorFuse called before using EnsoFuse

---

## ADDITIONAL PROTOCOLS (fuse details)

### Aave V4
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AaveV4SupplyFuse | Supply/Withdraw | Asset addresses | Aave V4 pool |
| AaveV4BorrowFuse | Borrow/Repay | Asset addresses | Variable rate borrow |
| AaveV4EModeFuse | E-Mode | - | E-mode category switch |
| AaveV4BalanceFuse | Balance | - | Supply - debt tracking |

**Conditions:**
- [ ] FV4-001: Pool address correct for Aave V4
- [ ] FV4-002: E-mode category ID correct (if used)
- [ ] FV4-003: Market ID 45 - WARNING: duplicate with MIDAS!

### Midas
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| MidasSupplyFuse | Supply/Withdraw | Asset addresses | Midas vault deposit |
| MidasRequestSupplyFuse | Request-based supply | Asset addresses | Async request-based |
| MidasBalanceFuse | Balance | - | Position tracking |

**Conditions:**
- [ ] FMI-001: Midas vault addresses correct
- [ ] FMI-002: Market ID 45 - WARNING: duplicate with AAVE_V4!

### Napier
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| NapierDepositFuse | Deposit | Napier pool addresses | Pool deposit |
| NapierSupplyFuse | Supply | Napier pool addresses | Supply liquidity |
| NapierRedeemFuse | Redeem | Napier pool addresses | Pool redeem |
| NapierSwapPtFuse | Swap PT | Napier market addresses | PT swap |
| NapierSwapYtFuse | Swap YT | Napier market addresses | YT swap |
| NapierCombineFuse | Combine PT+YT | Napier market addresses | Combine to underlying |
| NapierCollectFuse | Collect fees | - | Fee collection |
| NapierZapDepositFuse | Zap deposit | - | Single-tx deposit |
| NapierUniversalRouterFuse | Router | - | Multi-path routing |

**Conditions:**
- [ ] FN-001: Napier router address correct
- [ ] FN-002: Pool/market addresses correct and active
- [ ] FN-003: WARNING: No balance fuse for Napier in the code! Requires custom tracking

### Ebisu
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| EbisuZapperCreateFuse | Create trove | Asset addresses | Liquity-style trove creation |
| EbisuAdjustTroveFuse | Adjust trove | - | Modify collateral/debt |
| EbisuAdjustInterestRateFuse | Interest rate | - | Rate adjustment |
| EbisuZapperLeverModifyFuse | Leveraged modify | - | Leverage operations |
| EbisuZapperBalanceFuse | Balance | - | Trove value tracking |

**Conditions:**
- [ ] FEB-001: Zapper address correct
- [ ] FEB-002: BoldToken and WETH addresses correct
- [ ] FEB-003: Trove manager address correct

### Liquity V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| LiquityStabilityPoolFuse | Stability Pool | Pool addresses | Deposit/withdraw from SP |
| LiquityBalanceFuse | Balance | - | SP position tracking |

**Conditions:**
- [ ] FL2-001: Stability Pool address correct
- [ ] FL2-002: BOLD token address correct

### TAC Staking
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| TacStakingBalanceFuse | Balance | - | Staked position tracking |
| TacStakingDelegateFuse | Delegate | Validator addresses | Delegate stake |
| TacStakingRedelegateFuse | Redelegate | Validator addresses | Move stake |
| TacStakingEmergencyFuse | Emergency | - | Emergency unstake |

**Conditions:**
- [ ] FTC-001: TAC staking contract address correct
- [ ] FTC-002: Validator addresses are correct and active

### Stake DAO V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| StakeDaoV2SupplyFuse | Supply/Withdraw | Vault addresses | Stake DAO vault deposit |
| StakeDaoV2BalanceFuse | Balance | - | Nested ERC4626 tracking |

**Conditions:**
- [ ] FSD-001: Stake DAO vault addresses correct
- [ ] FSD-002: Nested vault chain: reward vault → LP vault → underlying

### Yield Basis
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| YieldBasisLtSupplyFuse | Supply/Withdraw | YB pool addresses | YB LT deposit |
| YieldBasisLtBalanceFuse | Balance | - | Position tracking |

**Conditions:**
- [ ] FYB-001: Yield Basis pool address correct

### Async Action
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| AsyncActionFuse | Async execution | Target addresses | Asynchronous operations |
| AsyncActionBalanceFuse | Balance | - | Async result tracking |

**Conditions:**
- [ ] FAA-001: Target addresses correct and trusted
- [ ] FAA-002: Callback handlers configured for async callbacks

### Compound V2
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| CompoundV2SupplyFuse | Supply/Withdraw | Asset addresses | cToken interaction |
| CompoundV2BalanceFuse | Balance | - | cToken balance tracking |

**Conditions:**
- [ ] FC2-001: cToken addresses correct
- [ ] FC2-002: Comptroller address correct

### Lido (chain-specific: Ethereum)
| Fuse | Type | Substrates | Specific validation |
|------|------|------------|---------------------|
| StEthWrapperFuse | Wrap/Unwrap | - | stETH <-> wstETH conversion |

**Conditions:**
- [ ] FLI-001: stETH and wstETH addresses correct
- [ ] FLI-002: Only on Ethereum mainnet

---

## UTILITY FUSES

### Balance-only Fuses
- **Erc20BalanceFuse**: Simple ERC20 token balance
- **Erc4626BalanceFuse**: Share balance in ERC4626 vault
- **ZeroBalanceFuse**: Always returns 0
- **AsyncActionBalanceFuse**: Async action results

### Maintenance Fuses
- **UpdateMarketsBalancesFuse**: Batch balance update
- **ConfigureInstantWithdrawalFuse**: Withdrawal configuration
- **UpdateWithdrawManagerMaintenanceFuse**: WithdrawManager address update
- **BurnRequestFeeFuse**: Request fee shares burning
- **TransientStorageSetInputsFuse**: Set data in transient storage
- **TransientStorageMapperFuse**: Map data in transient storage
- **TransientStorageChainReaderFuse**: Read data from transient storage

### PlasmaVault-specific Fuses
- **PlasmaVaultRequestSharesFuse**: Request shares for scheduled withdrawal
- **PlasmaVaultRedeemFromRequestFuse**: Redeem from request
- **PlasmaVaultBalanceAssetsValidationFuse**: Asset integrity validation

---

## GENERAL CONDITIONS FOR ALL FUSES

### FG-001: Fuse Code Verification
- **Condition**: Fuse code is verified on a block explorer
- **How to check**: Etherscan/Basescan verified contract
- **Expected result**: Verified source code

### FG-002: Fuse Immutable Parameters
- **Condition**: Fuse immutable parameters (MARKET_ID, protocol addresses) are correct
- **How to check**: Read public immutable getters
- **Expected result**: All match expectations

### FG-003: Fuse Not Upgradeable
- **Condition**: Fuse is NOT a proxy (unless intended)
- **How to check**: Check if address is an EOA/immutable contract
- **Expected result**: No proxy pattern
- **Notes**: Fuse is called via delegatecall - an upgradeable fuse is a risk
