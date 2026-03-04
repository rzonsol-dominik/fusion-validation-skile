# CLAUDE.md — fusion-validation-skile

## Project Overview

Production validation framework for [IPOR Fusion](https://github.com/IPOR-Labs/ipor-fusion) — a yield optimization DeFi protocol built on PlasmaVault (ERC4626 + UUPS proxy).

## Structure

- `validation-conditions/` — 12 numbered Markdown files (00–12) with structured validation conditions for production deployment
- `ipor-fusion/` — Cloned Fusion smart contract repo (Foundry-based Solidity). Gitignored; used for cross-referencing.

## Validation Conditions Format

Each condition follows this structure:
- **ID**: Unique identifier (e.g., `VAULT-CORE-001`)
- **Condition**: What must hold true
- **How to check**: On-chain call or verification method
- **Expected result**: What the check should return
- **Priority**: CRITICAL / HIGH / MEDIUM

Inline HTML comments are used for annotations:
- `<!-- COMMENT: ... -->` — notes
- `<!-- TODO: ... -->` — improvements needed
- `<!-- QUESTION: ... -->` — open questions
- `<!-- ERROR: ... -->` — found errors

## Key Conventions

- **All content must be written in English.** This includes validation conditions, comments, documentation, and any new files.
- "Fusion" always means IPOR Fusion.
- When verifying conditions against code, reference the local clone at `ipor-fusion/`.
- Validation files are numbered for reading order — maintain this ordering.

## Fusion Architecture Quick Reference

- **PlasmaVault**: ERC4626 vault with multi-market DeFi strategies
- **Fuses**: Protocol integration contracts executed via delegatecall (135+ fuses, 30+ protocols)
- **Markets**: Identified by `uint256` IDs from `IporFusionMarkets.sol`; each has a balance fuse + substrates
- **Roles**: ADMIN(0), OWNER(1), GUARDIAN(2), ATOMIST(100), ALPHA(200), FUSE_MANAGER(300)
- **Fees**: Performance (max 50%), Management (max 5%) — immutable constants in `PlasmaVaultLib.sol`
- **Withdrawals**: Instant via fuses in configured order; scheduled via `WithdrawManager`
- **Balance**: `totalAssets = vault.balance + Σ(market balances) + rewards vesting`
