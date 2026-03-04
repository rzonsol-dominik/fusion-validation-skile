# IPOR Fusion - Vault Production Validation Conditions

## Table of Contents

| # | File | Description |
|---|------|-------------|
| 01 | [01-VAULT-CORE.md](./01-VAULT-CORE.md) | Vault base configuration validation conditions |
| 02 | [02-ACCESS-CONTROL.md](./02-ACCESS-CONTROL.md) | Role and permission system validation conditions |
| 03 | [03-MARKET-CONFIGURATION.md](./03-MARKET-CONFIGURATION.md) | Per-market conditions: substrates, fuses, balance fuses |
| 04 | [04-MARKET-INTERACTIONS.md](./04-MARKET-INTERACTIONS.md) | Inter-market interaction conditions (dependency graph, limits) |
| 05 | [05-FUSES-CATALOG.md](./05-FUSES-CATALOG.md) | Complete fuse catalog with per-protocol conditions |
| 06 | [06-WITHDRAWAL-SYSTEM.md](./06-WITHDRAWAL-SYSTEM.md) | Withdrawal system conditions (instant, scheduled, fees) |
| 07 | [07-FEE-SYSTEM.md](./07-FEE-SYSTEM.md) | Fee system conditions (performance, management, deposit) |
| 08 | [08-PRICE-ORACLE.md](./08-PRICE-ORACLE.md) | Price oracle and price feed configuration conditions |
| 09 | [09-BALANCE-TRACKING.md](./09-BALANCE-TRACKING.md) | Balance tracking and totalAssets conditions |
| 10 | [10-REWARDS-SYSTEM.md](./10-REWARDS-SYSTEM.md) | Rewards system conditions (claim, vesting, transfer) |
| 11 | [11-CHECKLIST-PER-MARKET-TYPE.md](./11-CHECKLIST-PER-MARKET-TYPE.md) | Checklist per market type (lending, DEX, staking, etc.) |
| 12 | [12-PRODUCTION-VALIDATION-FLOW.md](./12-PRODUCTION-VALIDATION-FLOW.md) | Production validation sequence |

## How to Use

1. Each file contains **conditions** to verify
2. Conditions are categorized as: CRITICAL / HIGH / MEDIUM
3. Each condition follows this format:
   - **ID**: Unique identifier
   - **Condition**: What must be satisfied
   - **How to check**: On-chain call or verification method
   - **Expected result**: What the result should be
   - **Priority**: CRITICAL / HIGH / MEDIUM

## Inline Comments

You can add comments directly next to conditions using HTML comments:

```markdown
### VC-001: Underlying Token
- **Condition**: Vault has a valid underlying token
- **How to check**: `PlasmaVault.asset()`
<!-- COMMENT: Checked on mainnet 2026-03-03, OK -->
<!-- TODO: Add token decimals check -->
<!-- QUESTION: Does this also apply to wrapped tokens? -->
```

Available tags:
- `<!-- COMMENT: ... -->` - general note
- `<!-- TODO: ... -->` - item to do / fix
- `<!-- QUESTION: ... -->` - question to clarify in the next iteration
- `<!-- ERROR: ... -->` - found error in a condition

In the next iteration Claude will read these comments and incorporate them into the analysis.
