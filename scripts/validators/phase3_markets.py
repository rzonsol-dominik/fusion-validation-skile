"""Phase 3: Market Configuration (MC-001 to MC-022)."""

from abis import PLASMA_VAULT_ABI
from constants import ERC4626_VAULT_MARKET_END, ERC4626_VAULT_MARKET_START, MARKETS, META_MORPHO_MARKET_END, META_MORPHO_MARKET_START

from .base import BaseValidator, Status


class Phase3Markets(BaseValidator):
    phase_name = "Market Configuration"
    phase_number = 3

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # MC-001: Discover active markets by probing known market IDs
        active_markets = []
        market_substrates = {}
        market_balance_fuses = {}

        # Probe standard markets
        all_market_ids = list(MARKETS.keys())

        # Also probe ERC4626 and MetaMorpho ranges
        all_market_ids.extend(range(ERC4626_VAULT_MARKET_START, ERC4626_VAULT_MARKET_END + 1))
        all_market_ids.extend(range(META_MORPHO_MARKET_START, META_MORPHO_MARKET_END + 1))

        for market_id in all_market_ids:
            ok, substrates = self.call(vault, "getMarketSubstrates", market_id)
            if ok and len(substrates) > 0:
                market_name = MARKETS.get(market_id, f"Market({market_id})")
                active_markets.append(market_id)
                market_substrates[market_id] = substrates

        self.ctx["active_markets"] = active_markets
        self.ctx["market_substrates"] = market_substrates

        if active_markets:
            market_names = [f"{MARKETS.get(m, str(m))}({m})" for m in active_markets]
            self.add("MC-001", "Active markets discovered", Status.PASS,
                     f"{len(active_markets)} market(s)",
                     ", ".join(market_names))
        else:
            self.add("MC-001", "Active markets discovered", Status.WARN,
                     "0 markets", "No active markets found — vault may be unconfigured")

        # MC-002: Per-market substrate details
        for market_id in active_markets:
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            substrates = market_substrates.get(market_id, [])

            # Decode substrates — they are bytes32, often zero-padded addresses
            decoded = []
            for s in substrates:
                hex_s = s.hex() if isinstance(s, bytes) else s
                # Check if it looks like an address (first 12 bytes are zero)
                if hex_s[:24] == "0" * 24:
                    addr = "0x" + hex_s[24:]
                    decoded.append(addr)
                else:
                    decoded.append("0x" + hex_s)

            sub_str = ", ".join(f"`{d[:10]}...`" for d in decoded[:5])
            if len(decoded) > 5:
                sub_str += f" (+{len(decoded)-5} more)"

            self.add(f"MC-002-{market_id}", f"{market_name} substrates",
                     Status.INFO, f"{len(substrates)} substrate(s)", sub_str)

        # MC-005: Balance fuse check per market
        # Balance fuses are stored separately from action fuses (getFuses()).
        # We verify balance fuse presence by calling totalAssetsInMarket() —
        # if it succeeds, a balance fuse is configured for that market.
        all_fuses = self.ctx.get("all_fuses", [])
        for market_id in active_markets:
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            ok, balance = self.call(vault, "totalAssetsInMarket", market_id)
            if ok:
                market_balance_fuses[market_id] = True
                decimals = self.ctx.get("asset_decimals", 18)
                self.add(f"MC-005-{market_id}", f"{market_name} balance fuse",
                         Status.PASS, f"Active (balance: {self.fmt_wei(balance, decimals)})")
            else:
                self.add(f"MC-005-{market_id}", f"{market_name} balance fuse",
                         Status.WARN, "Not configured or call failed",
                         "totalAssetsInMarket() reverted — no balance fuse registered")

        self.ctx["market_balance_fuses"] = market_balance_fuses

        # MC-010: Fuse registration — all fuses are contracts
        for fuse in all_fuses:
            if not self.is_contract(fuse):
                self.add("MC-010", f"Fuse {self.fmt_addr(fuse)} is contract",
                         Status.FAIL, fuse, "Registered fuse has no code")
                break
        else:
            if all_fuses:
                self.add("MC-010", "All registered fuses are contracts", Status.PASS,
                         f"{len(all_fuses)} fuse(s) verified")

        # MC-015: Substrate verification — each substrate granted check
        for market_id in active_markets:
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            substrates = market_substrates.get(market_id, [])
            all_granted = True
            for sub in substrates:
                ok, granted = self.call(vault, "isMarketSubstrateGranted", market_id, sub)
                if not ok or not granted:
                    all_granted = False
                    break

            if substrates:
                self.add(f"MC-015-{market_id}", f"{market_name} substrates granted",
                         Status.PASS if all_granted else Status.WARN,
                         f"{len(substrates)} substrate(s)",
                         "" if all_granted else "Some substrates not granted")

        # MC-020: Fuse support check — all fuses in list are supported
        unsupported = []
        for fuse in all_fuses:
            ok, supported = self.call(vault, "isFuseSupported", fuse)
            if ok and not supported:
                unsupported.append(fuse)

        if unsupported:
            self.add("MC-020", "Unsupported fuses in registry", Status.WARN,
                     f"{len(unsupported)} unsupported",
                     ", ".join(self.fmt_addr(f) for f in unsupported))
        elif all_fuses:
            self.add("MC-020", "All fuses marked as supported", Status.PASS,
                     f"{len(all_fuses)} fuse(s)")

        return self.results
