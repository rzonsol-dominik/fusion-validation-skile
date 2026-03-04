#!/usr/bin/env python3
"""IPOR Fusion Vault Production Validator.

Usage:
    python3 validate_vault.py --vault 0xABC...DEF --chain arb-mainnet
    python3 validate_vault.py --vault 0xABC...DEF --chain eth-mainnet --block 19876543
    python3 validate_vault.py --vault 0xABC...DEF --chain base-mainnet --phases 1,2,3
"""

import argparse
import sys
import os

# Add scripts dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import CHAINS
from report import render_report, save_report
from rpc import get_block_number, get_w3
from validators import ALL_VALIDATORS


def main():
    parser = argparse.ArgumentParser(description="Validate an IPOR Fusion PlasmaVault for production readiness")
    parser.add_argument("--vault", required=True, help="Vault contract address (0x...)")
    parser.add_argument("--chain", required=True, choices=list(CHAINS.keys()),
                        help="Target chain")
    parser.add_argument("--block", type=int, default=None,
                        help="Pin to specific block number (default: latest)")
    parser.add_argument("--phases", type=str, default=None,
                        help="Comma-separated phase numbers to run (default: all)")
    parser.add_argument("--no-save", action="store_true",
                        help="Print report to stdout instead of saving to file")
    args = parser.parse_args()

    # Parse phases filter
    phase_filter = None
    if args.phases:
        try:
            phase_filter = set(int(p.strip()) for p in args.phases.split(","))
        except ValueError:
            print("Error: --phases must be comma-separated integers (e.g., 1,2,3)")
            sys.exit(1)

    # Connect
    print(f"Connecting to {args.chain}...")
    w3 = get_w3(args.chain, args.block)
    block = get_block_number(w3)
    print(f"Block: {block}")

    # Shared context across phases
    ctx = {
        "chain": args.chain,
        "block": block,
    }

    # Run validators
    phase_results = []
    for validator_cls in ALL_VALIDATORS:
        if phase_filter and validator_cls.phase_number not in phase_filter:
            continue

        phase_label = f"Phase {validator_cls.phase_number}: {validator_cls.phase_name}"
        print(f"Running {phase_label}...")

        try:
            v = validator_cls(w3, args.vault, ctx)
            results = v.run()
            phase_results.append((validator_cls.phase_name, validator_cls.phase_number, results))

            # Count results
            pass_count = sum(1 for r in results if r.status.value == "PASS")
            fail_count = sum(1 for r in results if r.status.value == "FAIL")
            warn_count = sum(1 for r in results if r.status.value == "WARN")
            total = len(results)
            print(f"  → {total} checks: {pass_count} passed, {fail_count} failed, {warn_count} warnings")

        except Exception as e:
            from validators.base import CheckResult, Status
            err_result = CheckResult(
                condition_id=f"PHASE-{validator_cls.phase_number}",
                label=f"Phase {validator_cls.phase_number} execution",
                status=Status.FAIL,
                value=None,
                detail=f"Phase crashed: {e}",
            )
            phase_results.append((validator_cls.phase_name, validator_cls.phase_number, [err_result]))
            print(f"  → Phase FAILED: {e}")

    # Render report
    report = render_report(args.vault, args.chain, block, phase_results, ctx)

    if args.no_save:
        print("\n" + report)
    else:
        filepath = save_report(report, args.vault, args.chain, block, ctx)
        print(f"\nReport saved to: {filepath}")


if __name__ == "__main__":
    main()
