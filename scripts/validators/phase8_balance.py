"""Phase 8: Balance Tracking (BT-001 to BT-023)."""

from abis import ERC20_ABI, PLASMA_VAULT_ABI
from constants import MARKETS

from .base import BaseValidator, Status


class Phase8Balance(BaseValidator):
    phase_name = "Balance Tracking"
    phase_number = 8

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)
        active_markets = self.ctx.get("active_markets", [])
        decimals = self.ctx.get("asset_decimals", 18)
        asset_sym = self.ctx.get("asset_symbol", "")

        # BT-001: Total assets
        ok, total_assets = self.call(vault, "totalAssets")
        if not ok:
            self.add("BT-001", "Total assets", Status.SKIP, None, "Call failed")
            return self.results

        self.add("BT-001", "Total assets", Status.INFO,
                 f"{self.fmt_wei(total_assets, decimals)} {asset_sym}",
                 f"Raw: {total_assets}")

        # BT-002: Vault's own ERC20 balance of underlying
        asset_addr = self.ctx.get("asset")
        vault_balance = 0
        if asset_addr:
            token = self.contract(asset_addr, ERC20_ABI)
            ok_b, vault_balance = self.call(token, "balanceOf", self.vault_address)
            if ok_b:
                self.add("BT-002", "Vault idle balance", Status.INFO,
                         f"{self.fmt_wei(vault_balance, decimals)} {asset_sym}",
                         f"Raw: {vault_balance}")
            else:
                self.add("BT-002", "Vault idle balance", Status.SKIP, None, "Call failed")
                vault_balance = 0

        # BT-003: Sum of market balances
        market_sum = 0
        market_balances = {}
        for market_id in active_markets:
            ok_m, bal = self.call(vault, "totalAssetsInMarket", market_id)
            if ok_m:
                market_balances[market_id] = bal
                market_sum += bal

        self.add("BT-003", "Sum of market balances", Status.INFO,
                 f"{self.fmt_wei(market_sum, decimals)} {asset_sym}",
                 f"Across {len(market_balances)} market(s)")

        # BT-005: Unrealized management fee
        ok, unrealized_fee = self.call(vault, "getUnrealizedManagementFee")
        unrealized_fee = unrealized_fee if ok else 0

        # BT-010: Balance consistency check
        # totalAssets ≈ vault_balance + market_sum + rewards_vesting - unrealized_fee
        computed = vault_balance + market_sum
        # Allow 0.1% tolerance for rounding
        if total_assets > 0:
            diff = abs(total_assets - computed)
            pct_diff = diff / total_assets * 100

            if unrealized_fee > 0:
                # Account for management fee in the comparison
                computed_with_fee = computed - unrealized_fee
                diff_with_fee = abs(total_assets - computed_with_fee)
                pct_diff_with_fee = diff_with_fee / total_assets * 100 if total_assets > 0 else 0

                if pct_diff_with_fee < pct_diff:
                    pct_diff = pct_diff_with_fee
                    diff = diff_with_fee
                    computed = computed_with_fee

            if pct_diff <= 0.1:
                self.add("BT-010", "Balance consistency", Status.PASS,
                         f"Diff: {pct_diff:.4f}%",
                         f"totalAssets={total_assets}, computed={computed}, diff={diff}")
            elif pct_diff <= 1.0:
                self.add("BT-010", "Balance consistency", Status.WARN,
                         f"Diff: {pct_diff:.4f}%",
                         f"totalAssets={total_assets}, computed={computed}, diff={diff}. "
                         "May be due to rewards vesting or pending operations")
            else:
                self.add("BT-010", "Balance consistency", Status.WARN,
                         f"Diff: {pct_diff:.2f}%",
                         f"totalAssets={total_assets}, computed={computed}, diff={diff}. "
                         "Large discrepancy — investigate rewards, pending fees, or oracle issues")
        elif total_assets == 0:
            self.add("BT-010", "Balance consistency", Status.INFO,
                     "N/A", "Total assets is 0")

        # BT-015: Share price sanity
        ok, supply = self.call(vault, "totalSupply")
        if ok and supply > 0 and total_assets > 0:
            share_decimals = decimals + 2  # DECIMALS_OFFSET = 2
            # Price = totalAssets / (totalSupply / 10^share_decimals) * 10^decimals
            # Simplified: price per share in underlying units
            price_per_share = total_assets * (10 ** share_decimals) / supply

            if 0.5 <= price_per_share / (10 ** decimals) <= 2.0:
                self.add("BT-015", "Share price sanity", Status.PASS,
                         f"{price_per_share / (10 ** decimals):.6f} {asset_sym}/share",
                         "Within expected range [0.5, 2.0]")
            elif 0.1 <= price_per_share / (10 ** decimals) <= 10.0:
                self.add("BT-015", "Share price sanity", Status.WARN,
                         f"{price_per_share / (10 ** decimals):.6f} {asset_sym}/share",
                         "Outside normal range but within tolerance")
            else:
                self.add("BT-015", "Share price sanity", Status.WARN,
                         f"{price_per_share / (10 ** decimals):.6f} {asset_sym}/share",
                         "Significantly outside expected range — investigate")
        elif ok and supply == 0:
            self.add("BT-015", "Share price sanity", Status.INFO,
                     "N/A", "No shares minted")
        else:
            self.add("BT-015", "Share price sanity", Status.SKIP, None, "Could not compute")

        # BT-020: Per-market balance breakdown
        for market_id, bal in market_balances.items():
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            pct = (bal / total_assets * 100) if total_assets > 0 else 0
            self.add(f"BT-020-{market_id}", f"{market_name} allocation",
                     Status.INFO,
                     f"{self.fmt_wei(bal, decimals)} {asset_sym} ({pct:.1f}%)")

        # Idle balance percentage
        if total_assets > 0 and vault_balance >= 0:
            idle_pct = vault_balance / total_assets * 100
            self.add("BT-020-idle", "Idle balance allocation",
                     Status.INFO,
                     f"{self.fmt_wei(vault_balance, decimals)} {asset_sym} ({idle_pct:.1f}%)")

        return self.results
