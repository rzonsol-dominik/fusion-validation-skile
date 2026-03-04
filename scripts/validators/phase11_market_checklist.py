"""Phase 11 — Per-Market-Type Checklist.

Classifies each active market by type and runs type-specific validations:
lending substrate checks, dependency advisories, staking origin links, etc.
"""

from __future__ import annotations

from .base import BaseValidator, Status
from .phase3_markets import _decode_substrate
from constants import (
    MARKETS,
    MARKET_TYPE_BY_ID,
    MARKET_TYPES,
    STAKING_ORIGIN,
    WRAPPED_ASSET_EQUIVALENTS,
)


class Phase11MarketChecklist(BaseValidator):
    phase_name = "Per-Market-Type Checklist"
    phase_number = 11

    def run(self):
        active_markets: list[int] = self.ctx.get("active_markets", [])
        dep_graph: dict[int, list[int]] = self.ctx.get("dependency_graph", {})
        asset: str = self.ctx.get("asset", "").lower()
        iw_fuses: list = self.ctx.get("instant_withdrawal_fuses", [])
        rcm: str = self.ctx.get("rewards_manager", "")

        # --- SP-03: ERC20_VAULT_BALANCE must exist ---
        if 7 in active_markets:
            self.add("SP-03", "ERC20_VAULT_BALANCE market present", Status.PASS)
        elif not active_markets:
            self.add("SP-03", "ERC20_VAULT_BALANCE market present", Status.WARN,
                     detail="Vault has no active markets (unconfigured) — market 7 absent")
        else:
            self.add("SP-03", "ERC20_VAULT_BALANCE market present", Status.FAIL,
                     detail="Market 7 (ERC20_VAULT_BALANCE) MUST exist in every configured vault")

        # --- MTC: classify each market ---
        type_counts: dict[str, int] = {t: 0 for t in MARKET_TYPES}
        for mid in sorted(active_markets):
            mname = MARKETS.get(mid, f"MARKET_{mid}")
            mtype = MARKET_TYPE_BY_ID.get(mid, "UNKNOWN")
            self.add(f"MTC-{mid}", f"Market {mid} ({mname}) classification",
                     Status.INFO, value=mtype)
            if mtype in type_counts:
                type_counts[mtype] += 1

        summary_parts = [f"{t}: {c}" for t, c in type_counts.items() if c > 0]
        self.add("MTC-SUM", "Market type summary", Status.INFO,
                 value=", ".join(summary_parts) if summary_parts else "no classified markets")

        # --- Type-specific checks ---
        for mid in sorted(active_markets):
            mtype = MARKET_TYPE_BY_ID.get(mid)
            mname = MARKETS.get(mid, f"MARKET_{mid}")

            if mtype == "LENDING":
                self._check_lending(mid, mname, asset, iw_fuses)
            elif mtype == "DEX_SWAP":
                self._check_depends_on_erc20(mid, mname, "SM-10", dep_graph)
            elif mtype == "LP_POSITION":
                self._check_depends_on_erc20(mid, mname, "LP-10", dep_graph)
            elif mtype == "STAKING":
                self._check_staking(mid, mname, dep_graph)
            elif mtype == "YIELD":
                self._check_depends_on_erc20(mid, mname, "YP-30", dep_graph,
                                             advisory=True)
            elif mtype == "FLASH_LOAN":
                self.add(f"FL-01-{mid}", f"Flash loan market {mname}",
                         Status.INFO,
                         detail="Flash loan presence noted; see Phase 10 for callback handler checks")
            elif mtype == "SPECIAL":
                self._check_special(mid, mname, rcm)

        return self.results

    # ------------------------------------------------------------------
    # Lending checks
    # ------------------------------------------------------------------
    # Markets where substrates reference protocol vaults/pools, not the underlying token.
    # LM-05 should be INFO (not WARN) when asset is absent from these markets.
    _INDIRECT_SUBSTRATE_MARKETS = {
        3,   # GEARBOX_POOL_V3 — substrates are dToken pool addresses
        5,   # FLUID_INSTADAPP_POOL — substrates are Fluid pool addresses
        11,  # EULER_V2 — substrates are e-vault addresses
        14,  # MORPHO — substrates are Morpho market IDs
        15,  # SPARK — substrates are Spark pool addresses
        21,  # MOONWELL — substrates are mToken addresses
        29,  # LIQUITY_V2 — substrates are trove addresses
        35,  # SILO_V2 — substrates are silo vault addresses
        45,  # AAVE_V4 — substrates use type-flag encoding (spoke/asset addresses)
    }

    def _check_lending(self, mid: int, mname: str, asset: str, iw_fuses: list):
        substrates = self.ctx.get("market_substrates", {}).get(mid, [])
        # LM-05: vault underlying in substrates
        # Use market-aware decoding so non-standard encodings (Euler, Enso, etc.) are handled
        if substrates and asset:
            asset_lower = asset.replace("0x", "").lower()
            # Build set of acceptable addresses: underlying + any wrapped equivalents
            acceptable = {asset_lower}
            # Look up equivalents using full 0x-prefixed lowercase address
            asset_full = "0x" + asset_lower
            equivalents = WRAPPED_ASSET_EQUIVALENTS.get(asset_full, set())
            for eq in equivalents:
                acceptable.add(eq.replace("0x", "").lower())

            found = False
            found_equivalent = False
            for s in substrates:
                hex_s = s.hex() if isinstance(s, bytes) else s
                addr, _ = _decode_substrate(hex_s, mid)
                if addr:
                    addr_clean = addr.replace("0x", "").lower()
                    if addr_clean == asset_lower:
                        found = True
                        break
                    elif addr_clean in acceptable:
                        found_equivalent = True
            if found:
                self.add(f"LM-05-{mid}", f"Lending {mname}: underlying in substrates",
                         Status.PASS)
            elif found_equivalent:
                self.add(f"LM-05-{mid}", f"Lending {mname}: underlying in substrates",
                         Status.PASS,
                         detail="Wrapped equivalent of underlying token found in substrates")
            elif mid in self._INDIRECT_SUBSTRATE_MARKETS:
                self.add(f"LM-05-{mid}", f"Lending {mname}: underlying in substrates",
                         Status.INFO,
                         detail="Substrates reference protocol vaults/pools, not underlying token directly")
            else:
                self.add(f"LM-05-{mid}", f"Lending {mname}: underlying in substrates",
                         Status.WARN,
                         detail="Vault underlying asset not found among market substrates")
        else:
            self.add(f"LM-05-{mid}", f"Lending {mname}: underlying in substrates",
                     Status.WARN,
                     detail="No substrates or asset address to compare")

        # LM-20: instant withdrawal advisory
        has_iw = len(iw_fuses) > 0
        self.add(f"LM-20-{mid}", f"Lending {mname}: instant withdrawal",
                 Status.INFO,
                 detail="IW fuses configured" if has_iw else "No instant withdrawal fuses — verify if intentional")

    # ------------------------------------------------------------------
    # Shared helper: dependency on ERC20_VAULT_BALANCE
    # ------------------------------------------------------------------
    def _check_depends_on_erc20(self, mid: int, mname: str, prefix: str,
                                dep_graph: dict, *, advisory: bool = False):
        deps = dep_graph.get(mid, [])
        if 7 in deps:
            self.add(f"{prefix}-{mid}", f"{mname}: depends on ERC20_VAULT_BALANCE",
                     Status.PASS if not advisory else Status.INFO)
        else:
            status = Status.INFO if advisory else Status.WARN
            self.add(f"{prefix}-{mid}", f"{mname}: depends on ERC20_VAULT_BALANCE",
                     status,
                     detail="ERC20_VAULT_BALANCE (7) not in dependency graph for this market")

    # ------------------------------------------------------------------
    # Staking checks
    # ------------------------------------------------------------------
    def _check_staking(self, mid: int, mname: str, dep_graph: dict):
        deps = dep_graph.get(mid, [])

        # ST-10: depends on origin market
        origin = STAKING_ORIGIN.get(mid)
        if origin is not None:
            origin_name = MARKETS.get(origin, f"MARKET_{origin}")
            if origin in deps:
                self.add(f"ST-10-{mid}",
                         f"Staking {mname}: depends on origin {origin_name}",
                         Status.PASS)
            else:
                self.add(f"ST-10-{mid}",
                         f"Staking {mname}: depends on origin {origin_name}",
                         Status.WARN,
                         detail=f"Origin market {origin} ({origin_name}) not in dependency graph")
        else:
            self.add(f"ST-10-{mid}",
                     f"Staking {mname}: origin market mapping",
                     Status.INFO,
                     detail="No known origin mapping for this staking market")

        # ST-11: depends on ERC20_VAULT_BALANCE
        self._check_depends_on_erc20(mid, mname, "ST-11", dep_graph)

    # ------------------------------------------------------------------
    # Special market checks
    # ------------------------------------------------------------------
    def _check_special(self, mid: int, mname: str, rcm: str):
        # Reward-related special markets: check that RCM exists
        reward_markets = {22, 24}  # MORPHO_REWARDS, FLUID_REWARDS
        if mid in reward_markets:
            if rcm and not self.is_zero(rcm):
                self.add(f"SP-{mid}", f"Special {mname}: RewardsClaimManager set",
                         Status.INFO,
                         detail=f"RCM = {self.fmt_addr(rcm)}")
            else:
                self.add(f"SP-{mid}", f"Special {mname}: RewardsClaimManager set",
                         Status.WARN,
                         detail="Reward market active but no RewardsClaimManager configured")
        else:
            self.add(f"SP-{mid}", f"Special market {mname}", Status.INFO)
