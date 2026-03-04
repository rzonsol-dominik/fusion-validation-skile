# 01 - Vault Core Configuration Validation

## Purpose
Verify the base configuration of PlasmaVault in production.

---

## CRITICAL

### VC-001: Underlying Token
- **Condition**: Vault has a valid underlying token (ERC4626 asset)
- **How to check**:
  1. `PlasmaVault.asset()` → token address
  2. `PriceOracleMiddleware.getAssetPrice(asset)` → price must exist and be > 0
- **Expected result**: Address of the expected token (e.g., USDC, DAI, WETH) AND price available in oracle
- **Notes**: Cannot be changed after deployment; must match the vault's intended token. Underlying token WITHOUT a price in PriceOracleMiddleware = USD → amount balance conversion is impossible (totalAssets will be incorrect)

### VC-002: Access Manager Address
- **Condition**: Vault is connected to the correct IporFusionAccessManager
- **How to check**: `PlasmaVaultGovernance.getAccessManagerAddress()`
- **Expected result**: Address of the deployed AccessManager
- **Notes**: AccessManager controls the ENTIRE permission system. Function `getAccessManagerAddress()` exists in `PlasmaVaultGovernance.sol:454` (confirmed in code)

### VC-003: Price Oracle Middleware
- **Condition**: Vault has a configured price oracle
- **How to check**: `PlasmaVaultGovernance.getPriceOracleMiddleware()`
- **Expected result**: Address of the deployed PriceOracleMiddleware (not address(0))
- **Notes**: Oracle must use USD as quote currency (address(0x348))

### VC-004: PlasmaVaultBase Address
- **Condition**: Vault has a valid PlasmaVaultBase (extension contract)
- **How to check**: Read from storage slot PlasmaVaultBase
- **Expected result**: Valid PlasmaVaultBase contract address (not address(0))
- **Notes**: Used for delegatecall for ERC20 voting, permit, supply cap

### VC-005: Proxy Implementation (Minimal Proxy / Clones)
- **Condition**: Vault is a Minimal Proxy (OpenZeppelin Clones) pointing to a valid base implementation
- **How to check**: Read proxy bytecode - should contain EIP-1167 Minimal Proxy pattern pointing to the base implementation. Alternatively: check PlasmaVaultFactory which deployed the vault via `Clones.clone(baseAddress)`
- **Expected result**: Address of the current base PlasmaVault implementation
- **Notes**: Vault does NOT use UUPS proxy. It uses Minimal Proxy (Clones) - each vault is an independent clone of the base implementation created by PlasmaVaultFactory

### VC-006: Vault Initialization Status
- **Condition**: Vault is fully initialized
- **How to check**: Try calling `proxyInitialize()` - should revert
- **Expected result**: Revert (already initialized)
- **Notes**: Prevents re-initialization

---

## HIGH

### VC-010: Total Supply Cap
- **Condition**: Supply cap is set to a reasonable value
- **How to check**: `PlasmaVaultGovernance.getTotalSupplyCap()`
- **Expected result**: Value consistent with expectations (default type(uint256).max)
- **Notes**: If vault has a size limit, the value must be != max

### VC-011: Share Token Name & Symbol
- **Condition**: Vault's ERC20 token has a correct name and symbol
- **How to check**: `PlasmaVault.name()`, `PlasmaVault.symbol()`
- **Expected result**: Expected name and symbol
- **Notes**: Readable names for integrators and UI

### VC-012: Decimals Offset
- **Condition**: Vault has a valid decimals offset (DECIMALS_OFFSET = 2)
- **How to check**: `PlasmaVault.decimals()`
- **Expected result**: `underlying.decimals() + 2` (e.g., USDC 6 + 2 = 8)
- **Notes**: Built into the contract, consistency verification

### VC-013: Withdraw Manager
- **Condition**: WithdrawManager is correctly connected
- **How to check**: Read WithdrawManager address from vault storage
- **Expected result**: Valid WithdrawManager address (not address(0))
- **Notes**: Controls withdrawals and the request queue

### VC-014: Public Vault Status
- **Condition**: Vault is public or private as intended
- **How to check**: Check if `deposit()` and `mint()` have PUBLIC_ROLE in AccessManager
- **Expected result**: PUBLIC_ROLE if vault should be public, WHITELIST_ROLE if private
- **Notes**: `convertToPublicVault()` changes this to PUBLIC_ROLE

### VC-015: Share Transfers Status
- **Condition**: Share transfers are enabled/disabled as intended
- **How to check**: `AccessManager.getTargetFunctionRole(vault, transfer.selector)` - check assigned role
- **Expected result**:
  - Default: TECH_VAULT_TRANSFER_SHARES_ROLE (7) - transfers blocked for regular users
  - After `enableTransferShares()`: PUBLIC_ROLE - transfers enabled
- **Notes**: `enableTransferShares()` changes the role for transfer/transferFrom to PUBLIC_ROLE. Requires ATOMIST_ROLE

### VC-016: RewardsClaimManager Address
- **Condition**: If vault uses rewards - RewardsClaimManager is configured
- **How to check**: `PlasmaVaultGovernance.getRewardsClaimManagerAddress()`
- **Expected result**: Valid address or address(0) if not used
- **Notes**: Required for claiming and vesting rewards

---

## MEDIUM

### VC-020: ERC4626 Compliance - maxDeposit
- **Condition**: maxDeposit returns a reasonable value
- **How to check**: `PlasmaVault.maxDeposit(someAddress)`
- **Expected result**: > 0 if vault accepts deposits

### VC-021: ERC4626 Compliance - maxMint
- **Condition**: maxMint returns a reasonable value
- **How to check**: `PlasmaVault.maxMint(someAddress)`
- **Expected result**: > 0 if vault accepts deposits

### VC-022: ERC4626 Compliance - totalAssets
- **Condition**: totalAssets is >= vault balance
- **How to check**: `PlasmaVault.totalAssets()` vs `ERC20(asset).balanceOf(vault)`
- **Expected result**: totalAssets >= balanceOf (because it includes market balances + rewards)

### VC-023: VotesPlugin Configuration
- **Condition**: If vault uses voting - PlasmaVaultVotesPlugin is configured
- **How to check**: Read from vault storage
- **Expected result**: Valid address or address(0) if not used

### VC-024: Callback Handlers
- **Condition**: Callback handlers are configured for required protocols
- **How to check**: Read callback handler mapping
- **Expected result**: Valid handlers for used protocols

### VC-025: Pre-Hooks Configuration
- **Condition**: Pre-hooks are configured as intended
- **How to check**: Read pre-hooks mapping (selector → implementation)
- **Expected result**: Appropriate pre-hooks for required selectors
- **Notes**: Available pre-hooks:
  - **PauseFunctionPreHook** - emergency pause per-function (reverts with `FunctionPaused`)
  - **ExchangeRateValidatorPreHook** - exchange rate drift validation with configurable threshold
  - **UpdateBalancesPreHook** - balance update before operation
  - **UpdateBalancesIgnoreDustPreHook** - update with dust tolerance
  - **ValidateAllAssetsPricesPreHook** - asset price validation via oracle
  - **EIP7702DelegateValidationPreHook** - EIP-7702 delegate tx validation

### VC-026: PlasmaVaultInitData Verification
- **Condition**: Vault initialization parameters are correct
- **How to check**: Check events from proxyInitialize() or read stored values:
  - `assetName` / `assetSymbol` - share token name and symbol
  - `underlyingToken` - underlying ERC20 address
  - `priceOracleMiddleware` - oracle address
  - `accessManager` - AccessManager address
  - `plasmaVaultBase` - PlasmaVaultBase extension address
  - `withdrawManager` - WithdrawManager address (address(0) = disabled)
  - `feeConfig` - performance and management fee configuration
- **Expected result**: All parameters match the intended values

### VC-027: Exchange Rate Validator (if used)
- **Condition**: ExchangeRateValidatorPreHook has a reasonable threshold
- **How to check**: Read substrates pre-hook for ExchangeRateValidator
- **Expected result**: Threshold consistent with expected vault volatility (e.g., 1-5%)
- **Notes**: Too tight threshold = blocks normal operations; too loose = no protection

### VC-028: ERC721 Receiver Support
- **Condition**: Vault implements onERC721Received (if using NFT positions - Uniswap V3, Ramses, Slipstream)
- **How to check**: Vault responds to `onERC721Received()` with the correct selector
- **Expected result**: Returns `IERC721Receiver.onERC721Received.selector`
- **Notes**: Without this, vault cannot receive NFT positions from Uniswap V3 / Ramses / Aerodrome Slipstream

### VC-029: WithdrawManager Initialization
- **Condition**: WithdrawManager is initialized (if used)
- **How to check**: WithdrawManager.getPlasmaVaultAddress() returns the vault address
- **Expected result**: Correct vault address (not address(0))
- **Notes**: WithdrawManager must point to the correct vault. Can be changed via updatePlasmaVaultAddress() (ATOMIST_ROLE)
