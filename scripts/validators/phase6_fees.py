"""Phase 6: Fee System (FE-001 to FE-033)."""

from abis import PLASMA_VAULT_ABI
from constants import MANAGEMENT_MAX_FEE_BPS, PERFORMANCE_MAX_FEE_BPS, ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase6Fees(BaseValidator):
    phase_name = "Fee System"
    phase_number = 6

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # FE-001: Performance fee configuration
        ok, perf_data = self.call(vault, "getPerformanceFeeData")
        if ok:
            fee_account, fee_bps = perf_data
            fee_pct = fee_bps / 100  # basis points to percent

            self.ctx["perf_fee_account"] = fee_account
            self.ctx["perf_fee_bps"] = fee_bps

            # FE-002: Fee within limits
            if fee_bps > PERFORMANCE_MAX_FEE_BPS:
                self.add("FE-001", "Performance fee", Status.FAIL,
                         f"{fee_pct:.2f}%",
                         f"Exceeds maximum {PERFORMANCE_MAX_FEE_BPS/100:.0f}%")
            elif fee_bps == 0:
                self.add("FE-001", "Performance fee", Status.INFO,
                         "0%", "No performance fee configured")
            else:
                self.add("FE-001", "Performance fee", Status.PASS,
                         f"{fee_pct:.2f}%",
                         f"Max: {PERFORMANCE_MAX_FEE_BPS/100:.0f}%")

            # FE-003: Fee account
            if self.is_zero(fee_account) and fee_bps > 0:
                self.add("FE-003", "Performance fee account", Status.FAIL,
                         ZERO_ADDRESS, "Fee is set but account is zero — fees will be lost")
            elif not self.is_zero(fee_account):
                self.add("FE-003", "Performance fee account", Status.PASS, fee_account)
            else:
                self.add("FE-003", "Performance fee account", Status.INFO,
                         ZERO_ADDRESS, "Zero address (fee is 0%)")
        else:
            self.add("FE-001", "Performance fee", Status.SKIP, None, "Call failed")

        # FE-010: Management fee configuration
        ok, mgmt_data = self.call(vault, "getManagementFeeData")
        if ok:
            fee_account, fee_bps, last_update = mgmt_data
            fee_pct = fee_bps / 100

            self.ctx["mgmt_fee_account"] = fee_account
            self.ctx["mgmt_fee_bps"] = fee_bps

            # FE-011: Fee within limits
            if fee_bps > MANAGEMENT_MAX_FEE_BPS:
                self.add("FE-010", "Management fee", Status.FAIL,
                         f"{fee_pct:.2f}%",
                         f"Exceeds maximum {MANAGEMENT_MAX_FEE_BPS/100:.1f}%")
            elif fee_bps == 0:
                self.add("FE-010", "Management fee", Status.INFO,
                         "0%", "No management fee configured")
            else:
                self.add("FE-010", "Management fee", Status.PASS,
                         f"{fee_pct:.2f}%",
                         f"Max: {MANAGEMENT_MAX_FEE_BPS/100:.1f}%")

            # FE-012: Fee account
            if self.is_zero(fee_account) and fee_bps > 0:
                self.add("FE-012", "Management fee account", Status.FAIL,
                         ZERO_ADDRESS, "Fee is set but account is zero — fees will be lost")
            elif not self.is_zero(fee_account):
                self.add("FE-012", "Management fee account", Status.PASS, fee_account)
            else:
                self.add("FE-012", "Management fee account", Status.INFO,
                         ZERO_ADDRESS, "Zero address (fee is 0%)")

            # FE-013: Last update timestamp
            if last_update > 0:
                self.add("FE-013", "Management fee last update", Status.INFO,
                         f"Timestamp: {last_update}")
            elif fee_bps > 0:
                self.add("FE-013", "Management fee last update", Status.WARN,
                         "0", "Fee configured but never updated — unrealized fees may accumulate")
        else:
            self.add("FE-010", "Management fee", Status.SKIP, None, "Call failed")

        # FE-020: Unrealized management fee
        ok, unrealized = self.call(vault, "getUnrealizedManagementFee")
        if ok:
            decimals = self.ctx.get("asset_decimals", 18)
            self.add("FE-020", "Unrealized management fee", Status.INFO,
                     f"{self.fmt_wei(unrealized, decimals)} {self.ctx.get('asset_symbol', '')}",
                     f"Raw: {unrealized}")
        else:
            self.add("FE-020", "Unrealized management fee", Status.SKIP, None, "Call failed")

        # FE-025: Fee accounts match (if both set, check if same or different)
        perf_acc = self.ctx.get("perf_fee_account")
        mgmt_acc = self.ctx.get("mgmt_fee_account")
        if perf_acc and mgmt_acc and not self.is_zero(perf_acc) and not self.is_zero(mgmt_acc):
            if perf_acc.lower() == mgmt_acc.lower():
                self.add("FE-025", "Fee accounts", Status.INFO,
                         "Same account for both fees", perf_acc)
            else:
                self.add("FE-025", "Fee accounts", Status.INFO,
                         "Different accounts",
                         f"Performance: {self.fmt_addr(perf_acc)}, Management: {self.fmt_addr(mgmt_acc)}")

        # FE-030: Deposit fee check via previewDeposit
        decimals = self.ctx.get("asset_decimals", 18)
        test_amount = 10 ** decimals  # 1 unit of underlying
        ok, shares = self.call(vault, "previewDeposit", test_amount)
        if ok:
            ok2, assets_back = self.call(vault, "previewRedeem", shares)
            if ok2:
                if assets_back < test_amount:
                    loss_pct = (test_amount - assets_back) / test_amount * 100
                    self.add("FE-030", "Deposit/redeem round-trip", Status.INFO,
                             f"{loss_pct:.4f}% loss",
                             f"Deposit 1 → {shares} shares → redeem {self.fmt_wei(assets_back, decimals)}")
                else:
                    self.add("FE-030", "Deposit/redeem round-trip", Status.PASS,
                             "No loss", f"1 asset → {shares} shares → {self.fmt_wei(assets_back, decimals)} back")

        return self.results
