"""Phase 9: Rewards System (RW-001 to RW-035)."""

from abis import ACCESS_MANAGER_ABI, REWARDS_CLAIM_MANAGER_ABI
from constants import ROLES, ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase9Rewards(BaseValidator):
    phase_name = "Rewards System"
    phase_number = 9

    def run(self):
        rcm_addr = self.ctx.get("rewards_manager")
        if not rcm_addr:
            self.add("RW-001", "RewardsClaimManager", Status.INFO,
                     "Not configured", "Vault has no RewardsClaimManager — rewards not managed")
            return self.results

        if self.is_zero(rcm_addr):
            self.add("RW-001", "RewardsClaimManager", Status.INFO,
                     "Zero address", "Not configured")
            return self.results

        rcm = self.contract(rcm_addr, REWARDS_CLAIM_MANAGER_ABI)

        # RW-001: Is contract
        if self.is_contract(rcm_addr):
            self.add("RW-001", "RewardsClaimManager is contract", Status.PASS, rcm_addr)
        else:
            self.add("RW-001", "RewardsClaimManager is contract", Status.FAIL, rcm_addr)
            return self.results

        # RW-002: Underlying token matches vault asset
        ok, rcm_token = self.call(rcm, "UNDERLYING_TOKEN")
        if ok:
            asset = self.ctx.get("asset", "")
            if asset and rcm_token.lower() == asset.lower():
                self.add("RW-002", "RCM underlying token", Status.PASS,
                         rcm_token, "Matches vault asset")
            elif asset:
                self.add("RW-002", "RCM underlying token", Status.WARN,
                         rcm_token, f"Does not match vault asset {asset}")
            else:
                self.add("RW-002", "RCM underlying token", Status.INFO, rcm_token)
        else:
            self.add("RW-002", "RCM underlying token", Status.SKIP, None, "Call failed")

        # RW-003: Points to correct vault
        ok, vault_ref = self.call(rcm, "PLASMA_VAULT")
        if ok:
            if vault_ref.lower() == self.vault_address.lower():
                self.add("RW-003", "RCM → vault reference", Status.PASS, vault_ref)
            else:
                self.add("RW-003", "RCM → vault reference", Status.FAIL,
                         vault_ref, f"Expected {self.vault_address}")
        else:
            self.add("RW-003", "RCM → vault reference", Status.SKIP, None, "Call failed")

        # RW-004: Reward fuses
        ok, reward_fuses = self.call(rcm, "getRewardsFuses")
        if ok:
            self.ctx["reward_fuses"] = reward_fuses
            if reward_fuses:
                self.add("RW-004", "Reward fuses", Status.PASS,
                         f"{len(reward_fuses)} fuse(s)",
                         ", ".join(self.fmt_addr_named(f) for f in reward_fuses[:10]))

                # RW-034: Each reward fuse is supported
                for fuse in reward_fuses:
                    ok_s, supported = self.call(rcm, "isRewardFuseSupported", fuse)
                    if ok_s and not supported:
                        self.add(f"RW-034-{self.fmt_addr(fuse)}",
                                 f"Reward fuse {self.fmt_addr(fuse)} supported",
                                 Status.WARN, "Not supported",
                                 "Fuse in list but not marked as supported")

                # RW-035: Each reward fuse is a contract
                for fuse in reward_fuses:
                    if not self.is_contract(fuse):
                        self.add(f"RW-035-{self.fmt_addr(fuse)}",
                                 f"Reward fuse {self.fmt_addr(fuse)} is contract",
                                 Status.FAIL, "Not a contract")
            else:
                self.add("RW-004", "Reward fuses", Status.INFO,
                         "None configured", "No reward fuses — rewards cannot be claimed")
        else:
            self.add("RW-004", "Reward fuses", Status.SKIP, None, "Call failed")

        # RW-005: TECH_REWARDS_CLAIM_MANAGER_ROLE (601) — RCM should hold this role
        am_addr = self.ctx.get("access_manager")
        if am_addr:
            am = self.contract(am_addr, ACCESS_MANAGER_ABI)
            ok, result = self.call(am, "hasRole", 601, self.w3.to_checksum_address(rcm_addr))
            if ok:
                is_member, exec_delay = result
                if is_member:
                    self.add("RW-005", "TECH_REWARDS_CLAIM_MANAGER_ROLE(601)", Status.PASS,
                             f"RCM holds role 601 (delay={exec_delay}s)")
                else:
                    self.add("RW-005", "TECH_REWARDS_CLAIM_MANAGER_ROLE(601)", Status.FAIL,
                             "RCM does not hold role 601",
                             "RewardsClaimManager must have TECH_REWARDS_CLAIM_MANAGER_ROLE")
            else:
                self.add("RW-005", "TECH_REWARDS_CLAIM_MANAGER_ROLE(601)", Status.SKIP,
                         None, "hasRole call failed")
        else:
            self.add("RW-005", "TECH_REWARDS_CLAIM_MANAGER_ROLE(601)", Status.SKIP,
                     None, "AccessManager not available")

        # RW-010: Vesting data
        ok, vesting = self.call(rcm, "getVestingData")
        if ok:
            vesting_time, update_ts, transferred, last_balance = vesting
            self.add("RW-010", "Vesting time", Status.INFO,
                     f"{vesting_time}s ({vesting_time/3600:.1f}h)")
            self.add("RW-030", "Last balance update", Status.INFO,
                     f"Timestamp: {update_ts}")
            self.add("RW-031", "Transferred tokens", Status.INFO,
                     str(transferred))
            self.add("RW-032", "Last update balance", Status.INFO,
                     str(last_balance))
        else:
            self.add("RW-010", "Vesting data", Status.SKIP, None, "Call failed")

        # RW-033: Available vested balance
        ok, balance = self.call(rcm, "balanceOf")
        if ok:
            decimals = self.ctx.get("asset_decimals", 18)
            self.add("RW-033", "Available vested balance", Status.INFO,
                     f"{self.fmt_wei(balance, decimals)} {self.ctx.get('asset_symbol', '')}",
                     f"Raw: {balance}")
        else:
            self.add("RW-033", "Available vested balance", Status.SKIP, None, "Call failed")

        return self.results
