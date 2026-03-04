"""Phase 2: Access Control (AC-001 to AC-022)."""

from abis import ACCESS_MANAGER_ABI
from constants import GOVERNANCE_SELECTORS, INSPECTABLE_ROLES, ROLES, TECH_ROLES, ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase2AccessControl(BaseValidator):
    phase_name = "Access Control"
    phase_number = 2

    def run(self):
        am_addr = self.ctx.get("access_manager")
        if not am_addr:
            self.add("AC-001", "AccessManager available", Status.SKIP,
                     None, "AccessManager not found in Phase 1")
            return self.results

        am = self.contract(am_addr, ACCESS_MANAGER_ABI)

        # AC-001: AccessManager is a contract
        if self.is_contract(am_addr):
            self.add("AC-001", "AccessManager is a contract", Status.PASS, am_addr)
        else:
            self.add("AC-001", "AccessManager is a contract", Status.FAIL, am_addr)
            return self.results

        # AC-002: ADMIN_ROLE holders — discover via hasRole probing
        # We can't enumerate all holders directly, but we check known patterns
        self._discover_role_holders(am)

        # AC-005: Role admin hierarchy
        self._check_role_hierarchy(am)

        # AC-010: Function-role mappings on vault
        self._check_function_roles(am)

        # AC-015: Redemption delay
        ok, delay = self.call(am, "REDEMPTION_DELAY_IN_SECONDS")
        if ok:
            days = delay / 86400
            self.add("AC-015", "Max redemption delay constant", Status.PASS,
                     f"{delay}s ({days:.1f} days)")
        else:
            self.add("AC-015", "Max redemption delay constant", Status.SKIP, None, "Call failed")

        # AC-016: Minimal execution delays for key roles
        for role_id in [0, 1, 2, 100, 200, 300]:
            role_name = ROLES.get(role_id, f"Role({role_id})")
            ok, min_delay = self.call(am, "getMinimalExecutionDelayForRole", role_id)
            if ok:
                status = Status.PASS
                detail = ""
                if role_id == 0 and min_delay == 0:
                    status = Status.WARN
                    detail = "ADMIN has zero delay — high risk"
                self.add(f"AC-016-{role_id}", f"Min execution delay for {role_name}",
                         status, f"{min_delay}s", detail)
            else:
                self.add(f"AC-016-{role_id}", f"Min execution delay for {role_name}",
                         Status.SKIP, None, "Call failed")

        # AC-017: Target closed check (vault should not be closed)
        ok, closed = self.call(am, "isTargetClosed", self.vault_address)
        if ok:
            if closed:
                self.add("AC-017", "Vault target closed", Status.FAIL, "CLOSED",
                         "Vault is closed in AccessManager — no functions callable")
            else:
                self.add("AC-017", "Vault target closed", Status.PASS, "Open")
        else:
            self.add("AC-017", "Vault target closed", Status.SKIP, None, "Call failed")

        # AC-018: Target admin delay for vault
        ok, admin_delay = self.call(am, "getTargetAdminDelay", self.vault_address)
        if ok:
            self.add("AC-018", "Vault target admin delay", Status.INFO,
                     f"{admin_delay}s", f"Admin delay for changing vault permissions")
        else:
            self.add("AC-018", "Vault target admin delay", Status.SKIP, None, "Call failed")

        # AC-020: Grant delays for critical roles
        for role_id in [0, 1, 2, 100]:
            role_name = ROLES.get(role_id, f"Role({role_id})")
            ok, grant_delay = self.call(am, "getRoleGrantDelay", role_id)
            if ok:
                status = Status.INFO
                if role_id in [0, 1] and grant_delay == 0:
                    status = Status.WARN
                self.add(f"AC-020-{role_id}", f"Grant delay for {role_name}",
                         status, f"{grant_delay}s")

        return self.results

    def _discover_role_holders(self, am):
        """Try to discover role holders for key roles.

        Since AccessManager doesn't expose an enumeration function,
        we check if the vault itself and the AccessManager hold roles,
        and report what we find.
        """
        known_addresses = [self.vault_address]
        am_addr = self.ctx.get("access_manager", "")
        if am_addr:
            known_addresses.append(am_addr)

        # Also check other known contract addresses from ctx
        for key in ["oracle", "rewards_manager", "vault_base", "implementation"]:
            addr = self.ctx.get(key)
            if addr and not self.is_zero(addr):
                known_addresses.append(addr)

        role_holders = {}
        for role_id in INSPECTABLE_ROLES:
            role_name = ROLES.get(role_id, f"Role({role_id})")
            holders = []
            for addr in known_addresses:
                try:
                    ok, result = self.call(am, "hasRole", role_id, self.w3.to_checksum_address(addr))
                    if ok:
                        is_member, exec_delay = result
                        if is_member:
                            holders.append((addr, exec_delay))
                except Exception:
                    pass

            role_holders[role_id] = holders

            if role_id in [0, 1, 2, 100, 200, 300]:
                if holders:
                    holder_strs = [f"{self.fmt_addr(h[0])} (delay={h[1]}s)" for h in holders]
                    status = Status.PASS
                    # ADMIN_ROLE held by non-AccessManager contracts is suspicious
                    if role_id == 0:
                        status = Status.INFO
                    self.add(f"AC-002-{role_id}", f"{role_name} holders (known contracts)",
                             status, "; ".join(holder_strs))
                else:
                    status = Status.INFO
                    if role_id in [100]:  # ATOMIST should have at least one holder
                        status = Status.WARN
                    self.add(f"AC-002-{role_id}", f"{role_name} holders (known contracts)",
                             status, "No holders found among known contracts",
                             "Note: EOA holders not discoverable without events")

        self.ctx["role_holders"] = role_holders

    def _check_role_hierarchy(self, am):
        """Check role admin and guardian assignments."""
        for role_id in [1, 2, 100, 200, 300, 600, 700, 800, 900, 1000, 1100, 1200]:
            role_name = ROLES.get(role_id, f"Role({role_id})")

            ok_admin, admin_role = self.call(am, "getRoleAdmin", role_id)
            ok_guard, guardian_role = self.call(am, "getRoleGuardian", role_id)

            if ok_admin:
                admin_name = ROLES.get(admin_role, f"Role({admin_role})")
                detail = ""
                status = Status.INFO

                # OWNER should be admin of most roles
                if role_id in [2, 100, 200, 300] and admin_role != 1:
                    status = Status.WARN
                    detail = f"Expected OWNER_ROLE(1) as admin, got {admin_name}"

                guardian_info = ""
                if ok_guard:
                    guardian_name = ROLES.get(guardian_role, f"Role({guardian_role})")
                    guardian_info = f", guardian={guardian_name}({guardian_role})"

                self.add(f"AC-005-{role_id}", f"{role_name} admin hierarchy",
                         status, f"admin={admin_name}({admin_role}){guardian_info}", detail)

    def _check_function_roles(self, am):
        """Check which roles are required for key governance functions."""
        mappings = []
        for fn_sig, selector in GOVERNANCE_SELECTORS.items():
            selector_bytes = bytes.fromhex(selector[2:])
            ok, role_id = self.call(am, "getTargetFunctionRole", self.vault_address, selector_bytes)
            if ok:
                role_name = ROLES.get(role_id, f"Role({role_id})")
                mappings.append((fn_sig, role_id, role_name))

        if mappings:
            # Group by role
            by_role = {}
            for fn_sig, role_id, role_name in mappings:
                by_role.setdefault(role_name, []).append(fn_sig)

            for role_name, fns in sorted(by_role.items()):
                fn_list = ", ".join(f.split("(")[0] for f in fns)
                self.add("AC-010", f"Functions requiring {role_name}",
                         Status.INFO, fn_list)

            # Check critical functions have appropriate roles
            critical_fns = {
                "addFuses(address[])": [300],         # FUSE_MANAGER
                "removeFuses(address[])": [300],      # FUSE_MANAGER
                "setPriceOracleMiddleware(address)": [1200],  # PRICE_ORACLE_MIDDLEWARE_MANAGER
                "configurePerformanceFee(address,uint256)": [1, 0],  # OWNER or ADMIN
                "configureManagementFee(address,uint256)": [1, 0],   # OWNER or ADMIN
            }
            for fn_sig, expected_roles in critical_fns.items():
                for fn_s, role_id, role_name in mappings:
                    if fn_s == fn_sig:
                        if role_id in expected_roles:
                            self.add(f"AC-010-{fn_sig.split('(')[0]}", f"{fn_sig.split('(')[0]} role",
                                     Status.PASS, role_name)
                        else:
                            self.add(f"AC-010-{fn_sig.split('(')[0]}", f"{fn_sig.split('(')[0]} role",
                                     Status.WARN, role_name,
                                     f"Expected one of {[ROLES.get(r, r) for r in expected_roles]}")
                        break
        else:
            self.add("AC-010", "Function-role mappings", Status.SKIP, None,
                     "Could not read function role mappings")
