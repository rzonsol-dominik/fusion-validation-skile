"""Phase 6: Fee System (FE-001 to FE-035)."""

from abis import FEE_MANAGER_ABI, PLASMA_VAULT_ABI
from constants import (
    MANAGEMENT_MAX_FEE_BPS,
    PERFORMANCE_MAX_FEE_BPS,
    ROLES,
    ZERO_ADDRESS,
)

from .base import BaseValidator, Status


class Phase6Fees(BaseValidator):
    phase_name = "Fee System"
    phase_number = 6

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # --- Vault-level fee data (FE-001 through FE-004) ---
        self._check_performance_fee(vault)
        self._check_management_fee(vault)

        # --- FeeManager discovery and checks (FE-005 through FE-016) ---
        fm_addr = self._discover_fee_manager()
        if fm_addr:
            self._check_fee_manager(fm_addr)
        else:
            # FE-013: Emit even without FeeManager (data comes from vault)
            last_update = self.ctx.get("mgmt_fee_last_update")
            mgmt_bps = self.ctx.get("mgmt_fee_bps")
            if last_update is not None:
                if last_update > 0:
                    self.add("FE-013", "Management fee last update", Status.INFO,
                             f"Timestamp: {last_update}")
                elif mgmt_bps and mgmt_bps > 0:
                    self.add("FE-013", "Management fee last update", Status.WARN,
                             "0", "Fee configured but never updated — unrealized fees may accumulate")

        # --- Unrealized management fee (FE-020) ---
        self._check_unrealized_fee(vault)

        # --- Fee accounts comparison (FE-025) ---
        self._check_fee_accounts_match()

        # --- Deposit fee (FE-030, FE-033) ---
        if fm_addr:
            self._check_deposit_fee(fm_addr)

        # --- Deposit/redeem round-trip (FE-035) ---
        self._check_round_trip(vault)

        return self.results

    # -----------------------------------------------------------------
    # Vault-level fee reads
    # -----------------------------------------------------------------

    def _check_performance_fee(self, vault):
        """FE-001/FE-002: Performance fee configuration from vault."""
        ok, perf_data = self.call(vault, "getPerformanceFeeData")
        if not ok:
            self.add("FE-001", "Performance fee", Status.SKIP, None, "Call failed")
            return

        fee_account, fee_bps = perf_data
        fee_pct = fee_bps / 100

        self.ctx["perf_fee_account"] = fee_account
        self.ctx["perf_fee_bps"] = fee_bps

        # FE-001: Fee account
        if self.is_zero(fee_account) and fee_bps > 0:
            self.add("FE-001", "Performance fee account", Status.FAIL,
                     ZERO_ADDRESS, "Fee is set but account is zero — fees will be lost")
        elif not self.is_zero(fee_account):
            self.add("FE-001", "Performance fee account", Status.PASS, fee_account)
        else:
            self.add("FE-001", "Performance fee account", Status.INFO,
                     ZERO_ADDRESS, "Zero address (fee is 0%)")

        # FE-002: Fee within limits
        if fee_bps > PERFORMANCE_MAX_FEE_BPS:
            self.add("FE-002", "Performance fee", Status.FAIL,
                     f"{fee_pct:.2f}%",
                     f"Exceeds maximum {PERFORMANCE_MAX_FEE_BPS / 100:.0f}%")
        elif fee_bps == 0:
            self.add("FE-002", "Performance fee", Status.INFO,
                     "0%", "No performance fee configured")
        else:
            self.add("FE-002", "Performance fee", Status.PASS,
                     f"{fee_pct:.2f}%",
                     f"Max: {PERFORMANCE_MAX_FEE_BPS / 100:.0f}%")

    def _check_management_fee(self, vault):
        """FE-003/FE-004: Management fee configuration from vault."""
        ok, mgmt_data = self.call(vault, "getManagementFeeData")
        if not ok:
            self.add("FE-003", "Management fee", Status.SKIP, None, "Call failed")
            return

        fee_account, fee_bps, last_update = mgmt_data
        fee_pct = fee_bps / 100

        self.ctx["mgmt_fee_account"] = fee_account
        self.ctx["mgmt_fee_bps"] = fee_bps
        self.ctx["mgmt_fee_last_update"] = last_update

        # FE-003: Fee account
        if self.is_zero(fee_account) and fee_bps > 0:
            self.add("FE-003", "Management fee account", Status.FAIL,
                     ZERO_ADDRESS, "Fee is set but account is zero — fees will be lost")
        elif not self.is_zero(fee_account):
            self.add("FE-003", "Management fee account", Status.PASS, fee_account)
        else:
            self.add("FE-003", "Management fee account", Status.INFO,
                     ZERO_ADDRESS, "Zero address (fee is 0%)")

        # FE-004: Fee within limits
        if fee_bps > MANAGEMENT_MAX_FEE_BPS:
            self.add("FE-004", "Management fee", Status.FAIL,
                     f"{fee_pct:.2f}%",
                     f"Exceeds maximum {MANAGEMENT_MAX_FEE_BPS / 100:.1f}%")
        elif fee_bps == 0:
            self.add("FE-004", "Management fee", Status.INFO,
                     "0%", "No management fee configured")
        else:
            self.add("FE-004", "Management fee", Status.PASS,
                     f"{fee_pct:.2f}%",
                     f"Max: {MANAGEMENT_MAX_FEE_BPS / 100:.1f}%")

    # -----------------------------------------------------------------
    # FeeManager discovery from TECH role holders
    # -----------------------------------------------------------------

    def _discover_fee_manager(self):
        """Find FeeManager address from TECH role holders (400 / 500)."""
        detailed = self.ctx.get("role_holders_detailed", {})
        holders_400 = detailed.get(400, [])
        holders_500 = detailed.get(500, [])

        # Extract contract holders from role 400
        contract_holders_400 = [h for h in holders_400 if h.is_contract]
        contract_holders_500 = [h for h in holders_500 if h.is_contract]

        if not contract_holders_400 and not contract_holders_500:
            self.add("FE-005", "FeeManager discovered", Status.SKIP,
                     None, "No FeeManager found (TECH roles 400/500 have no contract holders)")
            return None

        # Use role 400 holder as primary, fall back to 500
        if contract_holders_400:
            fm_addr = contract_holders_400[0].address
        else:
            fm_addr = contract_holders_500[0].address

        self.ctx["fee_manager_address"] = fm_addr
        return fm_addr

    # -----------------------------------------------------------------
    # FeeManager checks
    # -----------------------------------------------------------------

    def _check_fee_manager(self, fm_addr):
        """FE-005 through FE-016: Validate FeeManager contract."""
        fm = self.contract(fm_addr, FEE_MANAGER_ABI)

        # FE-005: FeeManager is a contract
        if self.is_contract(fm_addr):
            self.add("FE-005", "FeeManager is a contract", Status.PASS, fm_addr)
        else:
            self.add("FE-005", "FeeManager is a contract", Status.FAIL,
                     fm_addr, "Address has no code")
            return

        # FE-006 / FE-007: TECH role exclusivity
        self._check_tech_role_exclusivity(fm_addr)

        # FE-010: Total fees from FeeManager match vault configuration
        vault_perf_bps = self.ctx.get("perf_fee_bps")
        ok, fm_total_perf = self.call(fm, "getTotalPerformanceFee")
        if ok and vault_perf_bps is not None:
            if fm_total_perf == vault_perf_bps:
                self.add("FE-010", "FeeManager perf fee matches vault", Status.PASS,
                         f"{fm_total_perf / 100:.2f}%")
            else:
                self.add("FE-010", "FeeManager perf fee matches vault", Status.WARN,
                         f"FeeManager: {fm_total_perf / 100:.2f}%, Vault: {vault_perf_bps / 100:.2f}%",
                         "Mismatch between FeeManager total and vault config")

        vault_mgmt_bps = self.ctx.get("mgmt_fee_bps")
        ok, fm_total_mgmt = self.call(fm, "getTotalManagementFee")
        if ok and vault_mgmt_bps is not None:
            if fm_total_mgmt == vault_mgmt_bps:
                self.add("FE-010", "FeeManager mgmt fee matches vault", Status.PASS,
                         f"{fm_total_mgmt / 100:.2f}%")
            else:
                self.add("FE-010", "FeeManager mgmt fee matches vault", Status.WARN,
                         f"FeeManager: {fm_total_mgmt / 100:.2f}%, Vault: {vault_mgmt_bps / 100:.2f}%",
                         "Mismatch between FeeManager total and vault config")

        # FE-011: DAO fee values (immutable)
        for fn_name, label in [
            ("IPOR_DAO_MANAGEMENT_FEE", "DAO management fee"),
            ("IPOR_DAO_PERFORMANCE_FEE", "DAO performance fee"),
        ]:
            ok, dao_fee = self.call(fm, fn_name)
            if ok:
                fee_pct = dao_fee / 100  # 2-decimal precision: 100 = 1%
                self.add("FE-011", label, Status.INFO,
                         f"{fee_pct:.2f}% (raw: {dao_fee})",
                         "Immutable — set at deploy")
            else:
                self.add("FE-011", label, Status.SKIP, None, f"{fn_name}() call failed")

        # FE-012: Total fees from FeeManager vs max
        self._check_total_fees(fm)

        # FE-013: Management fee last update timestamp
        last_update = self.ctx.get("mgmt_fee_last_update")
        mgmt_bps = self.ctx.get("mgmt_fee_bps")
        if last_update is not None:
            if last_update > 0:
                self.add("FE-013", "Management fee last update", Status.INFO,
                         f"Timestamp: {last_update}")
            elif mgmt_bps and mgmt_bps > 0:
                self.add("FE-013", "Management fee last update", Status.WARN,
                         "0", "Fee configured but never updated — unrealized fees may accumulate")

        # FE-014: FeeManager → vault connection
        ok, vault_from_fm = self.call(fm, "PLASMA_VAULT")
        if ok:
            if vault_from_fm.lower() == self.vault_address.lower():
                self.add("FE-014", "FeeManager → vault connection", Status.PASS,
                         vault_from_fm)
            else:
                self.add("FE-014", "FeeManager → vault connection", Status.FAIL,
                         vault_from_fm,
                         f"Expected {self.vault_address}")
        else:
            self.add("FE-014", "FeeManager → vault connection", Status.SKIP,
                     None, "PLASMA_VAULT() call failed")

        # FE-015: Fee accounts are contracts
        for fn_name, label in [
            ("PERFORMANCE_FEE_ACCOUNT", "Performance fee account"),
            ("MANAGEMENT_FEE_ACCOUNT", "Management fee account"),
        ]:
            ok, acct = self.call(fm, fn_name)
            if ok:
                if self.is_zero(acct):
                    self.add("FE-015", f"{label} from FeeManager", Status.INFO,
                             ZERO_ADDRESS, "Not set (zero address)")
                elif self.is_contract(acct):
                    self.add("FE-015", f"{label} from FeeManager", Status.PASS, acct)
                else:
                    self.add("FE-015", f"{label} from FeeManager", Status.INFO,
                             acct, "EOA (not a contract)")
            else:
                self.add("FE-015", f"{label} from FeeManager", Status.SKIP,
                         None, f"{fn_name}() call failed")

        # FE-016: DAO fee recipient
        ok, dao_recipient = self.call(fm, "getIporDaoFeeRecipientAddress")
        if ok:
            if self.is_zero(dao_recipient):
                self.add("FE-016", "DAO fee recipient", Status.WARN,
                         ZERO_ADDRESS, "DAO fee recipient is zero — DAO fees will be lost")
            else:
                self.add("FE-016", "DAO fee recipient", Status.PASS, dao_recipient)
        else:
            self.add("FE-016", "DAO fee recipient", Status.SKIP,
                     None, "getIporDaoFeeRecipientAddress() call failed")

    def _check_tech_role_exclusivity(self, fm_addr):
        """FE-006/FE-007: Only FeeManager should hold TECH fee roles."""
        detailed = self.ctx.get("role_holders_detailed", {})
        fm_lower = fm_addr.lower()

        for role_id, check_id in [(400, "FE-006"), (500, "FE-007")]:
            role_name = ROLES.get(role_id, f"Role({role_id})")
            holders = detailed.get(role_id, [])

            if not holders:
                self.add(check_id, f"{role_name} exclusivity", Status.INFO,
                         "No holders", "Role not assigned")
                continue

            unexpected = [h for h in holders if h.address.lower() != fm_lower]
            if unexpected:
                addrs = ", ".join(h.address for h in unexpected)
                self.add(check_id, f"{role_name} exclusivity", Status.FAIL,
                         f"{len(unexpected)} unexpected holder(s)",
                         f"Unauthorized: {addrs}")
            else:
                self.add(check_id, f"{role_name} exclusivity", Status.PASS,
                         "Only FeeManager", fm_addr)

    def _check_total_fees(self, fm):
        """FE-012: Total fees from FeeManager do not exceed maximums."""
        # Total performance fee
        ok, total_perf = self.call(fm, "getTotalPerformanceFee")
        if ok:
            perf_pct = total_perf / 100
            if total_perf > PERFORMANCE_MAX_FEE_BPS:
                self.add("FE-012", "Total performance fee (FeeManager)", Status.FAIL,
                         f"{perf_pct:.2f}%",
                         f"Exceeds max {PERFORMANCE_MAX_FEE_BPS / 100:.0f}%")
            else:
                self.add("FE-012", "Total performance fee (FeeManager)", Status.PASS,
                         f"{perf_pct:.2f}%",
                         f"Max: {PERFORMANCE_MAX_FEE_BPS / 100:.0f}%")
        else:
            self.add("FE-012", "Total performance fee (FeeManager)", Status.SKIP,
                     None, "getTotalPerformanceFee() call failed")

        # Total management fee
        ok, total_mgmt = self.call(fm, "getTotalManagementFee")
        if ok:
            mgmt_pct = total_mgmt / 100
            if total_mgmt > MANAGEMENT_MAX_FEE_BPS:
                self.add("FE-012", "Total management fee (FeeManager)", Status.FAIL,
                         f"{mgmt_pct:.2f}%",
                         f"Exceeds max {MANAGEMENT_MAX_FEE_BPS / 100:.1f}%")
            else:
                self.add("FE-012", "Total management fee (FeeManager)", Status.PASS,
                         f"{mgmt_pct:.2f}%",
                         f"Max: {MANAGEMENT_MAX_FEE_BPS / 100:.1f}%")
        else:
            self.add("FE-012", "Total management fee (FeeManager)", Status.SKIP,
                     None, "getTotalManagementFee() call failed")

    # -----------------------------------------------------------------
    # Unrealized fee / fee accounts comparison
    # -----------------------------------------------------------------

    def _check_unrealized_fee(self, vault):
        """FE-020: Unrealized management fee."""
        ok, unrealized = self.call(vault, "getUnrealizedManagementFee")
        if ok:
            decimals = self.ctx.get("asset_decimals", 18)
            self.add("FE-020", "Unrealized management fee", Status.INFO,
                     f"{self.fmt_wei(unrealized, decimals)} {self.ctx.get('asset_symbol', '')}",
                     f"Raw: {unrealized}")
        else:
            self.add("FE-020", "Unrealized management fee", Status.SKIP, None, "Call failed")

    def _check_fee_accounts_match(self):
        """FE-025: Compare fee accounts between vault performance & management."""
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

    # -----------------------------------------------------------------
    # Deposit fee checks
    # -----------------------------------------------------------------

    def _check_deposit_fee(self, fm_addr):
        """FE-030/FE-033: Deposit fee from FeeManager."""
        fm = self.contract(fm_addr, FEE_MANAGER_ABI)
        ok, deposit_fee = self.call(fm, "getDepositFee")
        if not ok:
            self.add("FE-030", "Deposit fee", Status.SKIP, None, "getDepositFee() call failed")
            return

        # FE-030: Deposit fee value (18 decimals: 1e18 = 100%, 1e16 = 1%)
        if deposit_fee == 0:
            self.add("FE-030", "Deposit fee", Status.INFO,
                     "0%", "No deposit fee")
        else:
            fee_pct = deposit_fee / 1e16  # convert to percentage
            self.add("FE-030", "Deposit fee", Status.INFO,
                     f"{fee_pct:.4f}%",
                     f"Raw: {deposit_fee} (18-decimal precision)")

        # FE-033: Deposit fee max guard — warn if > 10%
        threshold = 10 ** 17  # 10% in 18-decimal
        if deposit_fee > threshold:
            fee_pct = deposit_fee / 1e16
            self.add("FE-033", "Deposit fee max guard", Status.WARN,
                     f"{fee_pct:.2f}%",
                     "Deposit fee exceeds 10% — verify this is intentional")
        elif deposit_fee > 0:
            self.add("FE-033", "Deposit fee max guard", Status.PASS,
                     f"{deposit_fee / 1e16:.4f}%", "Below 10% threshold")

    # -----------------------------------------------------------------
    # Round-trip check
    # -----------------------------------------------------------------

    def _check_round_trip(self, vault):
        """FE-035: Deposit/redeem round-trip loss check."""
        decimals = self.ctx.get("asset_decimals", 18)
        test_amount = 10 ** decimals  # 1 unit of underlying
        ok, shares = self.call(vault, "previewDeposit", test_amount)
        if not ok:
            return

        ok2, assets_back = self.call(vault, "previewRedeem", shares)
        if not ok2:
            return

        if assets_back < test_amount:
            loss_pct = (test_amount - assets_back) / test_amount * 100
            self.add("FE-035", "Deposit/redeem round-trip", Status.INFO,
                     f"{loss_pct:.4f}% loss",
                     f"Deposit 1 → {shares} shares → redeem {self.fmt_wei(assets_back, decimals)}")
        else:
            self.add("FE-035", "Deposit/redeem round-trip", Status.PASS,
                     "No loss",
                     f"1 asset → {shares} shares → {self.fmt_wei(assets_back, decimals)} back")
