"""Markdown report renderer for vault validation results."""

import os
from datetime import datetime, timezone

from validators.base import CheckResult, Status


def overall_status(all_results: list[CheckResult]) -> str:
    statuses = {r.status for r in all_results}
    if Status.FAIL in statuses:
        return "FAIL"
    if Status.WARN in statuses:
        return "PARTIAL"
    return "PASS"


STATUS_EMOJI = {
    Status.PASS: "PASS",
    Status.FAIL: "**FAIL**",
    Status.WARN: "WARN",
    Status.INFO: "INFO",
    Status.SKIP: "SKIP",
}


def render_report(
    vault_address: str,
    chain: str,
    block: int,
    phase_results: list[tuple[str, int, list[CheckResult]]],
    ctx: dict,
) -> str:
    """Render a full markdown report.

    phase_results: list of (phase_name, phase_number, results)
    """
    all_results = [r for _, _, results in phase_results for r in results]
    status = overall_status(all_results)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"# Vault Validation Report")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| **Vault** | `{vault_address}` |")
    lines.append(f"| **Chain** | {chain} |")
    lines.append(f"| **Block** | {block} |")
    lines.append(f"| **Date** | {now} |")

    name = ctx.get("vault_name", "")
    symbol = ctx.get("vault_symbol", "")
    if name:
        lines.append(f"| **Name** | {name} ({symbol}) |")

    asset_sym = ctx.get("asset_symbol", "")
    asset_addr = ctx.get("asset", "")
    if asset_sym:
        lines.append(f"| **Asset** | {asset_sym} (`{asset_addr}`) |")

    lines.append(f"| **Overall** | **{status}** |")
    lines.append("")

    # Summary counts
    counts = {}
    for s in Status:
        counts[s] = sum(1 for r in all_results if r.status == s)
    lines.append(f"**Summary**: {counts[Status.PASS]} passed, {counts[Status.FAIL]} failed, "
                 f"{counts[Status.WARN]} warnings, {counts[Status.INFO]} info, {counts[Status.SKIP]} skipped")
    lines.append("")

    # Critical issues
    fails = [r for r in all_results if r.status == Status.FAIL]
    if fails:
        lines.append("## Critical Issues")
        lines.append("")
        for r in fails:
            lines.append(f"- **{r.condition_id}** — {r.label}: {r.detail or r.value}")
        lines.append("")

    # Warnings
    warns = [r for r in all_results if r.status == Status.WARN]
    if warns:
        lines.append("## Warnings")
        lines.append("")
        for r in warns:
            lines.append(f"- **{r.condition_id}** — {r.label}: {r.detail or r.value}")
        lines.append("")

    # Phase-by-phase details
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    for phase_name, phase_number, results in phase_results:
        lines.append(f"### Phase {phase_number}: {phase_name}")
        lines.append("")
        if not results:
            lines.append("_No results._")
            lines.append("")
            continue

        lines.append("| ID | Check | Status | Value | Detail |")
        lines.append("|-----|-------|--------|-------|--------|")
        for r in results:
            val = str(r.value) if r.value is not None else ""
            # Escape pipes in values
            val = val.replace("|", "\\|")
            detail = (r.detail or "").replace("|", "\\|")
            lines.append(f"| {r.condition_id} | {r.label} | {STATUS_EMOJI[r.status]} | {val} | {detail} |")
        lines.append("")

    # Recommendations
    lines.append("---")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    if fails:
        lines.append("**Critical items require immediate attention before production deployment.**")
        lines.append("")
    if warns:
        lines.append("**Review all warnings to determine if they represent acceptable configuration.**")
        lines.append("")
    if not fails and not warns:
        lines.append("All checks passed. Vault configuration appears correct for production.")
    lines.append("")

    return "\n".join(lines)


def save_report(content: str, vault_address: str, chain: str, block: int, ctx: dict) -> str:
    """Save report to reports/<chain>/<VaultName-first4last4hex>/<block>.md

    Returns the file path.
    """
    name = ctx.get("vault_name", "Vault")
    # Sanitize name for filesystem
    safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in name)
    safe_name = safe_name.replace(" ", "_")
    hex_part = vault_address[2:6] + vault_address[-4:]
    dir_name = f"{safe_name}-{hex_part}"

    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    report_dir = os.path.join(base_dir, chain, dir_name)
    os.makedirs(report_dir, exist_ok=True)

    filepath = os.path.join(report_dir, f"{block}.md")
    with open(filepath, "w") as f:
        f.write(content)

    return filepath
