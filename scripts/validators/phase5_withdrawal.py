"""Phase 5: Withdrawal System (WS-001 to WS-030)."""

from abis import PLASMA_VAULT_ABI, WITHDRAW_MANAGER_ABI
from constants import ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase5Withdrawal(BaseValidator):
    phase_name = "Withdrawal System"
    phase_number = 5

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # WS-001: Instant withdrawal fuses (informational — WS-005 checks actual coverage)
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
                self.add("WS-001", "Instant withdrawal fuses configured", Status.INFO,
                         "None", "No instant withdrawal fuses — see WS-005 for coverage check")

        # WS-004: IFuseInstantWithdraw interface check
        # Verify each IW fuse bytecode contains the instantWithdraw(bytes32[]) selector
        if iw_fuses:
            iw_selector = self.w3.keccak(text="instantWithdraw(bytes32[])")[:4].hex()
            for fuse in iw_fuses:
                try:
                    code = self.w3.eth.get_code(self.w3.to_checksum_address(fuse))
                    if iw_selector in code.hex():
                        self.add(f"WS-004-{self.fmt_addr(fuse)}",
                                 f"IW fuse {self.fmt_addr(fuse)} implements instantWithdraw",
                                 Status.PASS, "Selector found in bytecode")
                    else:
                        self.add(f"WS-004-{self.fmt_addr(fuse)}",
                                 f"IW fuse {self.fmt_addr(fuse)} implements instantWithdraw",
                                 Status.WARN, "Selector not found",
                                 "Fuse may not implement IFuseInstantWithdraw interface")
                except Exception:
                    self.add(f"WS-004-{self.fmt_addr(fuse)}",
                             f"IW fuse {self.fmt_addr(fuse)} implements instantWithdraw",
                             Status.SKIP, None, "Could not read bytecode")

        # WS-015: Each instant withdrawal fuse is a registered fuse
        all_fuses = self.ctx.get("all_fuses", [])
        for fuse in iw_fuses:
            in_registry = fuse in all_fuses
            is_c = self.is_contract(fuse)
            if in_registry and is_c:
                self.add(f"WS-015-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
                         Status.PASS, "Registered & is contract")
            elif not is_c:
                self.add(f"WS-015-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
                         Status.FAIL, "Not a contract")
            else:
                self.add(f"WS-015-{self.fmt_addr(fuse)}", f"IW fuse {self.fmt_addr(fuse)}",
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

        # WS-006b: WithdrawManager — discover address
        wm_addr = self.ctx.get("withdraw_manager")

        if not wm_addr:
            self.add("WS-006b", "WithdrawManager address", Status.INFO, "Not discoverable",
                     "WithdrawManager not found in storage (Phase 1 VC-013)")
        else:
            self._check_withdraw_manager(wm_addr)

        # WS-005: Coverage check — active markets should have withdrawal paths
        active_markets = self.ctx.get("active_markets", [])
        if active_markets and not iw_fuses and not wm_addr:
            self.add("WS-005", "Withdrawal coverage", Status.WARN,
                     "No withdrawal path",
                     "Active markets exist but no instant withdrawal fuses or WithdrawManager")
        elif active_markets and iw_fuses:
            self.add("WS-005", "Withdrawal coverage", Status.PASS,
                     f"{len(iw_fuses)} instant fuse(s) for {len(active_markets)} market(s)")

        return self.results

    def _check_withdraw_manager(self, wm_addr: str):
        """Validate WithdrawManager configuration."""
        wm = self.contract(wm_addr, WITHDRAW_MANAGER_ABI)

        # WS-006b: Basic info
        if self.is_contract(wm_addr):
            self.add("WS-006b", "WithdrawManager is contract", Status.PASS, wm_addr)
        else:
            self.add("WS-006b", "WithdrawManager is contract", Status.FAIL, wm_addr)
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

        # WS-010: Withdraw window
        ok, window = self.call(wm, "getWithdrawWindow")
        if ok:
            hours = window / 3600
            status = Status.PASS if window > 0 else Status.WARN
            self.add("WS-010", "Withdraw window", status,
                     f"{window}s ({hours:.1f}h)")
        else:
            self.add("WS-010", "Withdraw window", Status.SKIP, None, "Call failed")

        # WS-011: Request fee
        ok, rfee = self.call(wm, "getRequestFee")
        if ok:
            fee_pct = rfee / 10**16
            self.add("WS-011", "Request fee", Status.INFO, f"{fee_pct:.4f}%")

        # WS-012: Withdraw fee
        ok, wfee = self.call(wm, "getWithdrawFee")
        if ok:
            fee_pct = wfee / 10**16  # WAD to percent
            self.add("WS-012", "Withdraw fee", Status.INFO, f"{fee_pct:.4f}%")

        # WS-022: Last release
        ok, ts = self.call(wm, "getLastReleaseFundsTimestamp")
        if ok:
            self.add("WS-022", "Last release timestamp", Status.INFO, str(ts))

        # WS-030: Shares to release
        ok, shares = self.call(wm, "getSharesToRelease")
        if ok:
            self.add("WS-030", "Shares to release", Status.INFO, str(shares))
