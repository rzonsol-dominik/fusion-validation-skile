# 11 - Checklist Per Market Type

## Purpose
Ready-to-use validation checklists for each MARKET TYPE added to the vault.
Use the appropriate checklist when adding a new market.

---

## A. LENDING MARKET (Aave V2/V3/V4, Compound V2/V3, Morpho, Euler, Moonwell, Silo)

### Before adding:
- [ ] **LM-01**: Market ID is correct (from IporFusionMarkets.sol)
- [ ] **LM-02**: Supply fuse deployed with correct parameters (pool address, market ID)
- [ ] **LM-03**: Balance fuse deployed with the same market ID
- [ ] **LM-04**: Substrates contain addresses of tokens the vault will supply
- [ ] **LM-05**: Vault's underlying token (or a wrapped equivalent, e.g. stETH→wstETH) is one of the substrate assets. For indirect-substrate markets (Morpho, Euler V2, Gearbox, Fluid, Spark, Moonwell, Liquity V2, Silo V2, AAVE V4), substrates reference protocol pools/vaults, not the underlying token directly — this is expected and informational only.
- [ ] **LM-06**: Supply fuse registered in vault (`addFuses()`)
- [ ] **LM-07**: Balance fuse assigned to market (`addBalanceFuse()`)
- [ ] **LM-08**: Substrates granted (`grantMarketSubstrates()`)

### If vault BORROWS on this market:
- [ ] **LM-10**: Borrow fuse deployed and registered
- [ ] **LM-11**: Collateral fuse deployed and registered (if separate)
- [ ] **LM-12**: Dependency on ERC20_VAULT_BALANCE (borrow brings tokens to vault)
- [ ] **LM-13**: Balance fuse accounts for debt (supply - borrow = net)
- [ ] **LM-14**: Market limits account for leverage risk

### Instant withdrawal:
- [ ] **LM-20**: Supply fuse implements `IFuseInstantWithdraw`
- [ ] **LM-21**: Fuse added to instant withdrawal fuses with correct parameters
- [ ] **LM-22**: Parameter params[1+] contains asset address for withdrawal

### Rewards:
- [ ] **LM-30**: Claim fuse registered in RewardsClaimManager (if protocol gives rewards)
- [ ] **LM-31**: Appropriate CLAIM_REWARDS_ROLE is active

### Price Oracle:
- [ ] **LM-40**: Price feed exists for each supply token
- [ ] **LM-41**: If protocol has its own oracle (Aave) - balance fuse uses it correctly

---

## B. DEX SWAP MARKET (Uniswap V2/V3 swap, Universal Token Swapper, Odos)

### Before adding:
- [ ] **SM-01**: Market ID correct
- [ ] **SM-02**: Swap fuse deployed with correct parameters (router address)
- [ ] **SM-03**: Substrates contain ALL tokens the vault may swap through
- [ ] **SM-04**: Swap fuse registered in vault
- [ ] **SM-05**: Substrates granted

### Dependencies:
- [ ] **SM-10**: Dependency on ERC20_VAULT_BALANCE (swap changes token balances)
- [ ] **SM-11**: If swap affects other markets - dependencies are configured

### Universal Token Swapper specifics:
- [ ] **SM-20**: Token substrates: allowed input/output tokens
- [ ] **SM-21**: Target substrates: allowed DEX aggregators (addresses)
- [ ] **SM-22**: Slippage substrates: max slippage configuration
- [ ] **SM-23**: Targets are verified/trusted aggregators (not random contracts)
- [ ] **SM-24**: SwapExecutor address correct

### Price Oracle:
- [ ] **SM-30**: Price feed for each token in swap path

### Notes:
- Swap markets usually do NOT have a balance fuse (ERC20_VAULT_BALANCE tracks the result)
- Swap markets usually are NOT in instant withdrawal fuses

---

## C. LP POSITION MARKET (Uniswap V3 positions, Balancer, Curve pool, Aerodrome/Velodrome)

### Before adding:
- [ ] **LP-01**: Market ID correct
- [ ] **LP-02**: Position fuses (New/Modify/Collect) deployed with correct parameters
- [ ] **LP-03**: Balance fuse deployed with the same market ID
- [ ] **LP-04**: Substrates contain:
  - Token pair addresses (for Uniswap V3)
  - Pool addresses + tokens (for Balancer, Curve)
  - Gauge + pool addresses (for Aerodrome/Velodrome)
- [ ] **LP-05**: Fuses registered in vault
- [ ] **LP-06**: Balance fuse assigned to market
- [ ] **LP-07**: Substrates granted

### Dependencies:
- [ ] **LP-10**: Dependency on ERC20_VAULT_BALANCE (LP changes token balances)
- [ ] **LP-11**: If LP token is staked in gauge - dependency between LP market and gauge market

### Instant withdrawal:
- [ ] **LP-20**: Fuse with appropriate exit/withdraw method
- [ ] **LP-21**: Fuse added to instant withdrawal fuses if needed
- [ ] **LP-22**: Consider that withdrawal from LP may have slippage

### Price Oracle:
- [ ] **LP-30**: Price feed for both tokens in the pair
- [ ] **LP-31**: If LP token has its own price feed - it is correct

### Uniswap V3 specifics:
- [ ] **LP-40**: NFT position tracking in FuseStorageLib
- [ ] **LP-41**: Fee tier (500/3000/10000) is correct
- [ ] **LP-42**: Tick range is reasonable
- [ ] **LP-43**: PositionValue.total() correctly values positions

---

## D. STAKING / GAUGE MARKET (Curve gauge, Aerodrome gauge, Gearbox farm, Fluid staking)

### Before adding:
- [ ] **ST-01**: Market ID correct
- [ ] **ST-02**: Staking fuse deployed with correct parameters
- [ ] **ST-03**: Balance fuse deployed
- [ ] **ST-04**: Substrates contain gauge/staking contract addresses
- [ ] **ST-05**: Fuses registered
- [ ] **ST-06**: Balance fuse assigned
- [ ] **ST-07**: Substrates granted

### Dependencies:
- [ ] **ST-10**: Dependency on the market from which the staked token originates
  - Curve gauge → Curve pool market
  - Aerodrome gauge → Aerodrome liquidity market
  - Gearbox farm → Gearbox pool market
  - Fluid staking → Fluid pool market
- [ ] **ST-11**: If unstake affects vault balance → dependency on ERC20_VAULT_BALANCE

### Instant withdrawal:
- [ ] **ST-20**: Unstake fuse in instant withdrawal fuses (if needed)
- [ ] **ST-21**: Order: first unstake from gauge, then withdraw from LP

### Rewards:
- [ ] **ST-30**: Gauge/staking generates rewards → claim fuse configured
- [ ] **ST-31**: Rewards claim fuse in RewardsClaimManager

---

## E. YIELD PROTOCOL MARKET (Pendle, Gearbox, Midas, ERC4626 vaults)

### Before adding:
- [ ] **YP-01**: Market ID correct
- [ ] **YP-02**: Supply/Swap fuse deployed with correct parameters
- [ ] **YP-03**: Balance fuse deployed
- [ ] **YP-04**: Substrates contain protocol market/vault addresses
- [ ] **YP-05**: Fuses registered and balance fuse assigned
- [ ] **YP-06**: Substrates granted

### Pendle specifics:
- [ ] **YP-10**: Pendle market address is correct and active
- [ ] **YP-11**: SY token, PT token are verified
- [ ] **YP-12**: Pendle market expiry date is in the future (unless redeem)
- [ ] **YP-13**: GuessedPtOut parameters are reasonable

### ERC4626 vault specifics:
- [ ] **YP-20**: Vault address is correct and verified
- [ ] **YP-21**: External vault underlying token == expected token
- [ ] **YP-22**: ERC4626PriceFeed configured for the share token

### Dependencies:
- [ ] **YP-30**: Dependency on ERC20_VAULT_BALANCE if operation changes vault balance

---

## F. FLASH LOAN MARKET (Morpho Flash Loan)

### Before adding:
- [ ] **FL-01**: Market ID = MORPHO_FLASH_LOAN
- [ ] **FL-02**: Flash loan fuse deployed with correct MORPHO address
- [ ] **FL-03**: Fuse registered in vault
- [ ] **FL-04**: Callback handlers configured for flash loan callback
- [ ] **FL-05**: Flash loan is used ONLY within execute() (not standalone)

---

## G. SPECIAL MARKETS

### ERC20_VAULT_BALANCE (Balance Only):
- [ ] **SP-01**: Erc20BalanceFuse assigned as balance fuse
- [ ] **SP-02**: Market ID = 7 (ERC20_VAULT_BALANCE from IporFusionMarkets.sol)
- [ ] **SP-03**: This market MUST ALWAYS exist in configured vaults — tracks native underlying token balance. For unconfigured vaults (zero active markets), absence is a WARN, not FAIL.

### ZERO_BALANCE_MARKET:
- [ ] **SP-10**: ZeroBalanceFuse assigned (if used)
- [ ] **SP-11**: Used for markets that intentionally have balance 0

### ASSETS_BALANCE_VALIDATION:
- [ ] **SP-20**: PlasmaVaultBalanceAssetsValidationFuse (if used)
- [ ] **SP-21**: Asset integrity validation

---

## SUMMARY - UNIVERSAL CHECKLIST PER MARKET

Regardless of market type, ALWAYS check:

| # | What to check | How |
|---|--------------|-----|
| 1 | Market ID correct | `IFuseCommon(fuse).MARKET_ID()` |
| 2 | Balance fuse assigned | `isBalanceFuseSupported(marketId, fuse)` |
| 3 | Supply/interaction fuses registered | `isFuseSupported(fuse)` |
| 4 | Substrates granted | `getMarketSubstrates(marketId)` |
| 5 | Substrates correct | Decode and compare with expected |
| 6 | Dependencies configured | `getDependencyBalanceGraph(marketId)` |
| 7 | Instant withdrawal (if needed) | `getInstantWithdrawalFuses()` |
| 8 | Market limits (if active) | `getMarketLimit(marketId)` |
| 9 | Price feeds for assets | `getAssetPrice(asset)` |
| 10 | Reward claim fuse (if rewards) | `rewardsManager.getRewardsFuses()` |
