"""Phase 3: Market Configuration (MC-001 to MC-022)."""

from abis import PLASMA_VAULT_ABI
from constants import ERC4626_VAULT_MARKET_END, ERC4626_VAULT_MARKET_START, MARKETS, META_MORPHO_MARKET_END, META_MORPHO_MARKET_START

from .base import BaseValidator, Status

# ---------------------------------------------------------------------------
# Market-aware substrate encoding patterns
# See ipor-fusion/contracts/fuses/*/...SubstrateLib.sol for details
# ---------------------------------------------------------------------------

# Markets that use type-flag encoding: top byte = type, address at bits 159..0
# (UniversalTokenSwapper, Odos, Velora, AaveV4)
_TYPE_FLAG_MARKETS = {12, 42, 43, 45}
_UTS_TYPES = {0: "Unknown", 1: "Token", 2: "Target", 3: "Slippage"}
_ODOS_TYPES = {0: "Unknown", 1: "Token", 2: "Slippage"}
_VELORA_TYPES = {0: "Unknown", 1: "Token", 2: "Slippage"}
_AAVEV4_TYPES = {0: "Undefined", 1: "Asset", 2: "Spoke"}
_TYPE_FLAG_LABELS = {12: _UTS_TYPES, 42: _ODOS_TYPES, 43: _VELORA_TYPES, 45: _AAVEV4_TYPES}

# Markets that use type+address encoding: type at bits 167..160, address at bits 159..0
# (Balancer, Aerodrome, Aerodrome Slipstream, Velodrome Superchain Slipstream,
#  Ebisu, Midas)
_TYPE_ADDR_MARKETS = {30, 33, 32, 36, 39}
_AERODROME_TYPES = {0: "UNDEFINED", 1: "Gauge", 2: "Pool"}
_BALANCER_TYPES = {0: "UNDEFINED", 1: "GAUGE", 2: "POOL", 3: "TOKEN"}
_EBISU_TYPES = {0: "UNDEFINED", 1: "ZAPPER", 2: "REGISTRY"}
_TYPE_ADDR_LABELS = {
    30: _AERODROME_TYPES, 33: _AERODROME_TYPES, 32: _AERODROME_TYPES,
    36: _BALANCER_TYPES, 39: _EBISU_TYPES,
}

# Euler V2 (market 11): address(20B) | isCollateral(1B) | canBorrow(1B) | subAccounts(1B)
_EULER_MARKET = 11

# Enso (market 38): address(20B) | functionSelector(4B) | padding(8B)
_ENSO_MARKET = 38


def _decode_substrate(hex_s: str, market_id: int):
    """Decode a bytes32 substrate and return (address_or_none, label).

    Returns a tuple of (address for name resolution, human-readable label).
    """
    # --- Euler V2: custom packed struct ---
    if market_id == _EULER_MARKET:
        addr = "0x" + hex_s[:40]
        is_collateral = int(hex_s[40:42], 16) & 1
        can_borrow = int(hex_s[42:44], 16) & 1
        sub_accounts = hex_s[44:46]
        flags = []
        if is_collateral:
            flags.append("collateral")
        if can_borrow:
            flags.append("borrow")
        flags_str = "+".join(flags) if flags else "supply-only"
        return addr, f"subAcc=0x{sub_accounts}, {flags_str}"

    # --- Enso: address + function selector ---
    if market_id == _ENSO_MARKET:
        addr = "0x" + hex_s[:40]
        selector = "0x" + hex_s[40:48]
        return addr, f"selector={selector}"

    # --- Type-flag encoding (top byte = type) ---
    if market_id in _TYPE_FLAG_MARKETS:
        type_byte = int(hex_s[:2], 16)
        if type_byte > 0:
            labels = _TYPE_FLAG_LABELS.get(market_id, {})
            type_name = labels.get(type_byte, f"type={type_byte}")
            if type_name == "Slippage":
                raw_val = int(hex_s[2:], 16)
                return None, f"[Slippage] {raw_val / 1e18:.4f}"
            addr = "0x" + hex_s[24:]
            return addr, f"[{type_name}]"
        # type=0 means plain left-padded address (no tag needed)

    # --- Type+Address encoding (type at bit 167) ---
    if market_id in _TYPE_ADDR_MARKETS:
        addr = "0x" + hex_s[24:]
        type_byte = int(hex_s[20:22], 16)
        if type_byte > 0:
            labels = _TYPE_ADDR_LABELS.get(market_id, {})
            type_name = labels.get(type_byte, f"type={type_byte}")
            return addr, f"[{type_name}]"

    # --- Default: left-padded address ---
    if hex_s[:24] == "0" * 24:
        addr = "0x" + hex_s[24:]
        return addr, ""

    # --- Fallback: right-padded address (trailing mostly zeros) ---
    if hex_s[40:] == "0" * 24 or (hex_s[46:] == "0" * 18):
        addr = "0x" + hex_s[:40]
        return addr, ""

    # Unknown encoding — show raw
    return None, ""


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

            # Decode substrates using market-aware logic
            sub_parts = []
            for s in substrates[:5]:
                hex_s = s.hex() if isinstance(s, bytes) else s
                addr, label = _decode_substrate(hex_s, market_id)

                if addr and len(addr) == 42:
                    name = self.resolve_name(addr)
                    part = f"{name} (`{addr}`)" if name else f"`{addr}`"
                    if label:
                        part += f" {label}"
                else:
                    if label:
                        part = label
                    else:
                        part = f"`0x{hex_s[:16]}...`"
                sub_parts.append(part)

            sub_str = ", ".join(sub_parts)
            if len(substrates) > 5:
                sub_str += f" (+{len(substrates)-5} more)"

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
