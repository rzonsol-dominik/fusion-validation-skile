# 08 - Price Oracle Validation

## Purpose
Verify the price oracle system, price feeds, and PriceOracleMiddleware configuration.

---

## Oracle Architecture

```
PlasmaVault
  └── PriceOracleMiddleware (chain-wide)
        ├── Custom PriceFeed per asset (IPriceFeed)
        │   ├── ERC4626PriceFeed
        │   ├── CurveStableSwapNGPriceFeed
        │   ├── WstETHPriceFeed
        │   ├── SDaiPriceFeed
        │   ├── DualCrossReferencePriceFeed
        │   └── ...
        └── Chainlink Feed Registry (fallback)

  └── PriceOracleMiddlewareManager (vault-specific, optional)
        ├── Asset → Custom source mapping
        └── Price validation (delta checking)
```

**Key**: All prices in USD, 18 decimals (WAD). Quote currency = address(0x348).

---

## CRITICAL

### PO-001: Price Oracle Middleware Set
- **Condition**: Vault has a configured PriceOracleMiddleware
- **How to check**: `PlasmaVaultGovernance.getPriceOracleMiddleware()`
- **Expected result**: Valid address (not address(0))
- **Notes**: WITHOUT oracle the vault CANNOT convert balances to USD

### PO-002: Quote Currency = USD
- **Condition**: Oracle uses USD as quote currency
- **How to check**: Check QUOTE_CURRENCY in PriceOracleMiddleware == address(0x348)
- **Expected result**: address(0x0000000000000000000000000000000000000348)
- **Notes**: ISO-4217 USD code. Different quote currency = incorrect valuations

### PO-003: Underlying Token Has Price Feed
- **Condition**: Vault's underlying token (asset) has a configured price feed
- **How to check**: `PriceOracleMiddleware.getAssetPrice(asset)` doesn't revert
- **Expected result**: Price > 0, decimals = 18
- **Notes**: Without the underlying token's price - USD → amount balance conversion is impossible

### PO-004: All Substrate Assets Have Price Feeds
- **Condition**: EVERY asset used in substrates has a price feed
- **How to check**: For each token in substrates: `getAssetPrice(token)` doesn't revert
- **Expected result**: Price > 0 for every asset
- **Notes**: Missing price = balance fuse cannot calculate USD value

### PO-005: Price Feed Accuracy
- **Condition**: Oracle prices are close to market prices
- **How to check**: Compare `getAssetPrice()` with current market price
- **Expected result**: Deviation < 1-2%
- **Notes**: Large deviation = incorrect share valuation, arbitrage

### PO-006: Price Feed Freshness
- **Condition**: Prices are not stale (Chainlink heartbeat)
- **How to check**: Check timestamp of last Chainlink feed update
- **Expected result**: Last update < heartbeat interval (e.g., 1h, 24h)
- **Notes**: Stale prices = incorrect valuation

---

## HIGH

### PO-010: Custom Price Feeds Correctness
- **Condition**: Custom price feeds (ERC4626PriceFeed, WstETHPriceFeed, etc.) are correct
- **How to check**: For each asset with a custom feed:
  - `PriceOracleMiddleware.getSourceOfAssetPrice(asset)` → custom feed address
  - Check custom feed parameters (base asset, reference oracle, etc.)
- **Expected result**: Correct parameters
- **Notes**: Incorrect custom feed = systematically incorrect valuation

### PO-011: Derivative Asset Price Feeds
- **Condition**: Derivative assets (wstETH, sDAI, LP tokens) have appropriate price feeds
- **How to check**: Check the price feed type for each derivative asset
- **Expected result**:
  - wstETH → WstETHPriceFeed (uses wstETH/stETH rate + stETH/USD)
  - sDAI → SDaiPriceFeed (uses sDAI/DAI rate + DAI/USD)
  - LP tokens → appropriate LP price feed
  - ERC4626 shares → ERC4626PriceFeed (uses convertToAssets + asset price)
- **Notes**: A simple Chainlink feed for a derivative may not exist

### PO-012: Price Oracle Decimals Consistency
- **Condition**: All prices are in 18 decimals
- **How to check**: `getAssetPrice(asset)` returns (price, decimals) - decimals == 18
- **Expected result**: decimals = 18 for every asset
- **Notes**: Different decimals = incorrect calculations in balance fuses

### PO-013: Chainlink Feed Registry (Ethereum)
- **Condition**: On Ethereum - Chainlink Feed Registry is available as fallback
- **How to check**: Check if PriceOracleMiddleware has a configured registry
- **Expected result**: Valid Chainlink Feed Registry address (if on Ethereum)
- **Notes**: On L2 (Arbitrum, Base) Feed Registry may not be available

### PO-014: PriceOracleMiddlewareManager Setup (if used)
- **Condition**: If vault uses PriceOracleMiddlewareManager - it is correctly configured
- **How to check**: Check configured assets and their sources
- **Expected result**: All needed assets have price sources
- **Notes**: Manager overrides the default middleware

### PO-015: Price Validation Configuration (if used)
- **Condition**: If using price validation - max delta is reasonable
- **How to check**: `getPriceValidationInfo(asset)` in PriceOracleMiddlewareManager
- **Expected result**: Max delta consistent with asset volatility (e.g., 5% for stablecoin, 20% for volatile)
- **Notes**: Too tight delta = blocks operations; too loose = no protection

---

## MEDIUM

### PO-020: Oracle Manipulation Resistance
- **Condition**: Price feeds are resistant to manipulation (TWAP, Chainlink, not spot)
- **How to check**: Check the oracle type used by each feed
- **Expected result**: Chainlink, TWAP, or trusted source (not AMM spot price)
- **Notes**: AMM spot price can be manipulated via flash loans

### PO-021: Multi-hop Price Feeds
- **Condition**: Multi-hop price feeds (token → intermediate → USD) are correct
- **How to check**: Check the price chain for each multi-hop feed
- **Expected result**: Each step has a correct source
- **Notes**: DualCrossReferencePriceFeed uses two sources - both must be correct

### PO-022: Price Oracle Immutability
- **Condition**: Price oracle cannot be changed without governance delay
- **How to check**: Check who can call `setPriceOracleMiddleware()`
- **Expected result**: ATOMIST_ROLE with appropriate execution delay
- **Notes**: Changing the oracle = changing the valuation of all assets
