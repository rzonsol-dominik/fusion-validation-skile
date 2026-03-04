"""Phase 10: Pre-hooks & Etherscan Verification (VC-025/027/028/029)."""

from abis import PLASMA_VAULT_ABI
from rpc import is_verified_on_etherscan

from .base import BaseValidator, Status


class Phase10Hooks(BaseValidator):
    phase_name = "Pre-hooks & Verification"
    phase_number = 10

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)
        chain = self.ctx.get("chain", "")

        # HC-001: Etherscan verification of vault
        verified = is_verified_on_etherscan(self.vault_address, chain)
        if verified is True:
            self.add("HC-001", "Vault verified on explorer", Status.PASS, "Verified")
        elif verified is False:
            self.add("HC-001", "Vault verified on explorer", Status.FAIL,
                     "Not verified", "Source code not verified on block explorer")
        else:
            self.add("HC-001", "Vault verified on explorer", Status.SKIP,
                     None, "ETHERSCAN_API_KEY not set or API call failed")

        # HC-002: Etherscan verification of AccessManager
        am_addr = self.ctx.get("access_manager")
        if am_addr:
            verified = is_verified_on_etherscan(am_addr, chain)
            if verified is True:
                self.add("HC-002", "AccessManager verified on explorer", Status.PASS, "Verified")
            elif verified is False:
                self.add("HC-002", "AccessManager verified on explorer", Status.FAIL,
                         "Not verified")
            else:
                self.add("HC-002", "AccessManager verified on explorer", Status.SKIP,
                         None, "API key not set or call failed")

        # HC-003: Etherscan verification of implementation
        impl = self.ctx.get("implementation")
        if impl:
            verified = is_verified_on_etherscan(impl, chain)
            if verified is True:
                self.add("HC-003", "Implementation verified on explorer", Status.PASS, "Verified")
            elif verified is False:
                self.add("HC-003", "Implementation verified on explorer", Status.FAIL,
                         "Not verified")
            else:
                self.add("HC-003", "Implementation verified on explorer", Status.SKIP,
                         None, "API key not set or call failed")

        # HC-005: Verify key fuses on explorer
        all_fuses = self.ctx.get("all_fuses", [])
        if all_fuses:
            verified_count = 0
            unverified = []
            skipped = 0

            for fuse in all_fuses[:20]:  # Limit to avoid API rate limits
                v = is_verified_on_etherscan(fuse, chain)
                if v is True:
                    verified_count += 1
                elif v is False:
                    unverified.append(fuse)
                else:
                    skipped += 1

            if unverified:
                self.add("HC-005", "Fuse verification on explorer", Status.FAIL,
                         f"{verified_count} verified, {len(unverified)} unverified",
                         "Unverified: " + ", ".join(self.fmt_addr(f) for f in unverified[:5]))
            elif skipped == len(all_fuses[:20]):
                self.add("HC-005", "Fuse verification on explorer", Status.SKIP,
                         None, "API key not set")
            else:
                self.add("HC-005", "Fuse verification on explorer", Status.PASS,
                         f"All {verified_count} checked fuse(s) verified")

        # HC-010: Pre-hooks configuration check
        # Check a few known selectors for pre-hooks
        known_selectors = [
            ("execute(FuseAction[])", "0x1cff79cd"),
            ("deposit(uint256,address)", "0x6e553f65"),
            ("withdraw(uint256,address,address)", "0xb460af94"),
            ("redeem(uint256,address,address)", "0xba087652"),
        ]

        hooks_found = []
        for fn_name, selector_hex in known_selectors:
            selector_bytes = bytes.fromhex(selector_hex[2:])
            ok, hook_addr = self.call(vault, "getPreHookConfig", self.vault_address, selector_bytes)
            if ok and not self.is_zero(str(hook_addr)):
                hooks_found.append((fn_name, hook_addr))

        if hooks_found:
            for fn_name, hook_addr in hooks_found:
                is_c = self.is_contract(str(hook_addr))
                self.add(f"HC-010-{fn_name.split('(')[0]}", f"Pre-hook on {fn_name.split('(')[0]}",
                         Status.PASS if is_c else Status.WARN,
                         str(hook_addr),
                         "Contract" if is_c else "Not a contract!")
        else:
            self.add("HC-010", "Pre-hooks", Status.INFO,
                     "None configured", "No pre-hooks found on common selectors")

        # HC-015: Oracle verified
        oracle = self.ctx.get("oracle")
        if oracle:
            verified = is_verified_on_etherscan(oracle, chain)
            if verified is True:
                self.add("HC-015", "Oracle verified on explorer", Status.PASS, "Verified")
            elif verified is False:
                self.add("HC-015", "Oracle verified on explorer", Status.FAIL, "Not verified")
            else:
                self.add("HC-015", "Oracle verified on explorer", Status.SKIP,
                         None, "API key not set or call failed")

        return self.results
