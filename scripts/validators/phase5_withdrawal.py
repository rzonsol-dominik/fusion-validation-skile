"""Phase 5: Withdrawal System (WS-001 to WS-022)."""

from abis import PLASMA_VAULT_ABI, WITHDRAW_MANAGER_ABI
from constants import ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase5Withdrawal(BaseValidator):
    phase_name = "Withdrawal System"
    phase_number = 5

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # WS-001: Instant withdrawal fuses
        iw_fuses = self.ctx.get("instant_withdrawal_fuses", [])
        if iw_fuses:
            self.add("WS-001", "Instant withdrawal fuses configured", Status.PASS,
                     f"{len(iw_fuses)} fuse(s)")
        else:
            # Try reading again
            ok, iw_fuses = self.call(vault, "getInstantWithdrawalFuses")
            if ok and iw_fuses:
                self.ctx["instant_withdrawal_fuses"] = iw_fuses
                self.add("WS-001", "Instant withdrawal fuses configured", Status.PASS,
                         f"{len(iw_fuses)} fuse(s)")
            else:
                self.add("WS-001", "Instant withdrawal fuses configured", Status.WARN,
                         "None", "No instant withdrawal fuses — deposits may be irreversible without WithdrawManager")

        # WS-002: Each instant withdrawal fuse is a registered fuse
        all_fuses = self.ctx.get("all_fuses", [])
        for fuse in iw_fuses:
            in_registry = fuse in all_fuses
            is_c = self.is_contract(fuse)
            if in_registry and is_c:
                self.add(f"WS-002-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
                         Status.PASS, "Registered & is contract")
            elif not is_c:
                self.add(f"WS-002-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
                         Status.FAIL, "Not a contract")
            else:
                self.add(f"WS-002-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
                         Status.WARN, "Not in fuse registry",
                         "Fuse is a contract but not in getFuses() list")

        # WS-003: Instant withdrawal fuse params
        for i, fuse in enumerate(iw_fuses):
            ok, params = self.call(vault, "getInstantWithdrawalFusesParams", fuse, i)
            if ok:
                self.add(f"WS-003-{i}", f"IW fuse #{i} params",
                         Status.INFO, f"{len(params)} param(s)")
            else:
                self.add(f"WS-003-{i}", f"IW fuse #{i} params",
                         Status.SKIP, None, "Call failed")

        # WS-005: WithdrawManager — discover address
        # WithdrawManager address isn't exposed via a simple getter on the vault
        # We look for it in the access manager tech role holders or try known patterns
        wm_addr = self.ctx.get("withdraw_manager")

        # Try to find WithdrawManager by checking if any known address responds
        # to WithdrawManager ABI
        if not wm_addr:
            # The WithdrawManager address might need to be discovered via events
            # or configuration. For now, we check if it was already set in ctx
            self.add("WS-005", "WithdrawManager address", Status.INFO, "Not discoverable",
                     "WithdrawManager must be provided via context or discovered via events")
        else:
            self._check_withdraw_manager(wm_addr)

        # WS-010: Coverage check — active markets should have withdrawal paths
        active_markets = self.ctx.get("active_markets", [])
        if active_markets and not iw_fuses and not wm_addr:
            self.add("WS-010", "Withdrawal coverage", Status.WARN,
                     "No withdrawal path",
                     "Active markets exist but no instant withdrawal fuses or WithdrawManager")
        elif active_markets and iw_fuses:
            self.add("WS-010", "Withdrawal coverage", Status.PASS,
                     f"{len(iw_fuses)} instant fuse(s) for {len(active_markets)} market(s)")

        return self.results

    def _check_withdraw_manager(self, wm_addr: str):
        """Validate WithdrawManager configuration."""
        wm = self.contract(wm_addr, WITHDRAW_MANAGER_ABI)

        # WS-005: Basic info
        if self.is_contract(wm_addr):
            self.add("WS-005", "WithdrawManager is contract", Status.PASS, wm_addr)
        else:
            self.add("WS-005", "WithdrawManager is contract", Status.FAIL, wm_addr)
            return

        # WS-006: Points to correct vault
        ok, vault_addr = self.call(wm, "getPlasmaVaultAddress")
        if ok:
            if vault_addr.lower() == self.vault_address.lower():
                self.add("WS-006", "WithdrawManager → vault", Status.PASS, vault_addr)
            else:
                self.add("WS-006", "WithdrawManager → vault", Status.FAIL,
                         vault_addr, f"Expected {self.vault_address}")
        else:
            self.add("WS-006", "WithdrawManager → vault", Status.SKIP, None, "Call failed")

        # WS-007: Withdraw window
        ok, window = self.call(wm, "getWithdrawWindow")
        if ok:
            hours = window / 3600
            status = Status.PASS if window > 0 else Status.WARN
            self.add("WS-007", "Withdraw window", status,
                     f"{window}s ({hours:.1f}h)")
        else:
            self.add("WS-007", "Withdraw window", Status.SKIP, None, "Call failed")

        # WS-008: Fees
        ok, wfee = self.call(wm, "getWithdrawFee")
        if ok:
            fee_pct = wfee / 10**16  # WAD to percent
            self.add("WS-008", "Withdraw fee", Status.INFO, f"{fee_pct:.4f}%")

        ok, rfee = self.call(wm, "getRequestFee")
        if ok:
            fee_pct = rfee / 10**16
            self.add("WS-009", "Request fee", Status.INFO, f"{fee_pct:.4f}%")

        # WS-011: Last release
        ok, ts = self.call(wm, "getLastReleaseFundsTimestamp")
        if ok:
            self.add("WS-011", "Last release timestamp", Status.INFO, str(ts))

        # WS-012: Shares to release
        ok, shares = self.call(wm, "getSharesToRelease")
        if ok:
            self.add("WS-012", "Shares to release", Status.INFO, str(shares))
