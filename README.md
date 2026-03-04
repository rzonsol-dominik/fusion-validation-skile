# IPOR Fusion Vault Validator

Production validation framework for [IPOR Fusion](https://github.com/IPOR-Labs/ipor-fusion) — a yield optimization DeFi protocol built on PlasmaVault (ERC4626 + UUPS proxy).

Runs automated on-chain checks against deployed vaults and produces Markdown reports with pass/fail/warn status for each condition.

## Quick Start

### Prerequisites

- Python 3.9+
- Alchemy API key
- Etherscan API key (for contract verification checks)

### Setup

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys:
#   ALCHEMY_API_KEY=...
#   ETHERSCAN_API_KEY=...
```

### Run Validation

```bash
# Full validation (all phases, saves report)
python3 scripts/validate_vault.py \
  --vault 0x604117f0c94561231060f56cd2ddd16245d434c5 \
  --chain eth-mainnet

# Specific phases only, print to stdout
python3 scripts/validate_vault.py \
  --vault 0x3F97CEa640B8B93472143f87a96d5A86f1F5167F \
  --chain arb-mainnet \
  --phases 1,3,4,11 \
  --no-save

# Pin to a specific block
python3 scripts/validate_vault.py \
  --vault 0x604117f0c94561231060f56cd2ddd16245d434c5 \
  --chain eth-mainnet \
  --block 24500000
```

### CLI Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--vault` | Yes | Vault contract address |
| `--chain` | Yes | Target chain: `eth-mainnet`, `arb-mainnet`, `base-mainnet`, `opt-mainnet` |
| `--block` | No | Pin to specific block number (default: latest) |
| `--phases` | No | Comma-separated phase numbers to run (default: all) |
| `--no-save` | No | Print report to stdout instead of saving to file |

## Validation Phases

| # | Phase | What it checks |
|---|-------|----------------|
| 1 | Vault Identity & Core | Asset, AccessManager, oracle, supply cap, fuses, share price |
| 2 | Access Control | Role assignments, admin hierarchy, function permissions, timelocks |
| 3 | Market Configuration | Active markets, substrates, balance fuses, fuse registration |
| 4 | Market Interactions | Dependency graphs, cycle detection, market limits |
| 5 | Withdrawal System | Instant withdrawal fuses, WithdrawManager, redemption delays |
| 6 | Fee System | Performance/management fees, recipients, fee caps |
| 7 | Price Oracle | Oracle middleware, per-asset price feeds, staleness |
| 8 | Balance Tracking | totalAssets consistency, per-market balances |
| 9 | Rewards System | RewardsClaimManager, reward fuses, vesting |
| 10 | Pre-hooks & Verification | Callback handlers, Etherscan verification |
| 11 | Per-Market-Type Checklist | Market classification, type-specific dependency and substrate checks |

## Project Structure

```
fusion-validation-skile/
├── validation-conditions/     # Validation requirements (Markdown)
│   ├── 00-INDEX.md
│   ├── 01-VAULT-CORE.md
│   ├── 02-ACCESS-CONTROL.md
│   ├── ...
│   └── 12-PRODUCTION-VALIDATION-FLOW.md
├── scripts/                   # Validation engine
│   ├── validate_vault.py      # CLI entry point
│   ├── constants.py           # Roles, markets, chains, selectors
│   ├── abis.py                # Contract ABIs
│   ├── rpc.py                 # Web3 + Etherscan client
│   ├── events.py              # AccessManager event decoding
│   ├── report.py              # Markdown report renderer
│   ├── requirements.txt
│   └── validators/            # Phase validators
│       ├── base.py            # BaseValidator, Status, CheckResult
│       ├── phase1_vault_id.py
│       ├── ...
│       └── phase11_market_checklist.py
├── data/                      # Cached event data (per chain/contract)
├── reports/                   # Generated reports (gitignored)
├── ipor-fusion/               # Cloned Fusion repo for reference (gitignored)
└── .env                       # API keys (gitignored)
```

## Validation Conditions

The `validation-conditions/` directory contains 12 numbered Markdown files that define **what** must be validated. Each condition follows this format:

```markdown
- **ID**: VAULT-CORE-001
- **Condition**: What must hold true
- **How to check**: On-chain call or verification method
- **Expected result**: What the check should return
- **Priority**: CRITICAL / HIGH / MEDIUM
```

### Adding New Conditions

1. Open the appropriate file in `validation-conditions/` (or create a new numbered file)
2. Add conditions using the format above
3. Use inline HTML comments for annotations:
   - `<!-- COMMENT: ... -->` — notes
   - `<!-- TODO: ... -->` — improvements needed
   - `<!-- QUESTION: ... -->` — open questions

### Implementing New Checks

1. Find or create the validator in `scripts/validators/` matching the phase
2. Use `self.add(check_id, label, status, value, detail)` to record results
3. Available statuses: `PASS`, `FAIL`, `WARN`, `INFO`, `SKIP`
4. Register new validators in `scripts/validators/__init__.py`

Example:

```python
from .base import BaseValidator, Status

class Phase12NewPhase(BaseValidator):
    phase_name = "My New Phase"
    phase_number = 12

    def run(self):
        # Read shared context from prior phases
        active_markets = self.ctx.get("active_markets", [])

        # Make on-chain calls
        vault = self.contract(self.vault_address, MY_ABI)
        ok, value = self.call(vault, "someFunction", arg1)

        if ok:
            self.add("NEW-001", "Some check", Status.PASS, value)
        else:
            self.add("NEW-001", "Some check", Status.FAIL,
                     detail="Call reverted")

        return self.results
```

## Supported Chains

| Chain | Chain ID |
|-------|----------|
| `eth-mainnet` | 1 |
| `arb-mainnet` | 42161 |
| `base-mainnet` | 8453 |
| `opt-mainnet` | 10 |

## IPOR Fusion Architecture

- **PlasmaVault**: ERC4626 vault with multi-market DeFi strategies
- **Fuses**: Protocol integration contracts executed via delegatecall (135+ fuses, 30+ protocols)
- **Markets**: Identified by `uint256` IDs; each has a balance fuse + substrates
- **Roles**: ADMIN(0), OWNER(1), GUARDIAN(2), ATOMIST(100), ALPHA(200), FUSE_MANAGER(300)
- **Fees**: Performance (max 50%), Management (max 5%)
- **Withdrawals**: Instant via fuses in configured order; scheduled via WithdrawManager
