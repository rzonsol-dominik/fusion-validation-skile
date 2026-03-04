"""Event log scanner for AccessManager role discovery with caching.

Scans RoleGranted / RoleRevoked events to build a complete map of role holders.
Cache is stored in data/<chain>/<am_address>/events.json for incremental scans.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import requests
from web3 import Web3

from abis import ACCESS_MANAGER_ABI
from constants import CHAINS


@dataclass
class RoleHolder:
    address: str
    role_id: int
    delay: int = 0
    since: int = 0
    is_contract: Optional[bool] = None
    verified: Optional[bool] = None  # on-chain hasRole check


# ---------------------------------------------------------------------------
# Find contract creation block
# ---------------------------------------------------------------------------

def _find_creation_block_etherscan(address: str, chain: str) -> Optional[int]:
    """Find contract creation block via Etherscan V2 API (getcontractcreation).

    Returns block number or None if unavailable.
    """
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    chain_cfg = CHAINS.get(chain)
    if not api_key or not chain_cfg:
        return None

    try:
        resp = requests.get(
            "https://api.etherscan.io/v2/api",
            params={
                "chainid": chain_cfg["chain_id"],
                "module": "contract",
                "action": "getcontractcreation",
                "contractaddresses": address,
                "apikey": api_key,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") != "1" or not data.get("result"):
            return None
        tx_hash = data["result"][0].get("txHash")
        if not tx_hash:
            return None
        # Look up the transaction to get block number
        tx_resp = requests.get(
            "https://api.etherscan.io/v2/api",
            params={
                "chainid": chain_cfg["chain_id"],
                "module": "proxy",
                "action": "eth_getTransactionByHash",
                "txhash": tx_hash,
                "apikey": api_key,
            },
            timeout=15,
        )
        tx_data = tx_resp.json()
        block_hex = tx_data.get("result", {}).get("blockNumber")
        if block_hex:
            return int(block_hex, 16)
        return None
    except Exception:
        return None


def _find_creation_block_binary(w3: Web3, address: str) -> int:
    """Find contract creation block via binary search on eth_getCode.

    Fallback method (~25 RPC calls). May fail on chains that don't support
    historical eth_getCode (e.g. Arbitrum).
    """
    address = w3.to_checksum_address(address)
    hi = w3.eth.block_number
    lo = 0

    code = w3.eth.get_code(address, block_identifier=hi)
    if len(code) == 0:
        return 0

    code = w3.eth.get_code(address, block_identifier=lo)
    if len(code) > 0:
        return 0

    while lo < hi - 1:
        mid = (lo + hi) // 2
        code = w3.eth.get_code(address, block_identifier=mid)
        if len(code) > 0:
            hi = mid
        else:
            lo = mid

    return hi


def find_creation_block(w3: Web3, address: str, chain: str) -> int:
    """Find the block where a contract was deployed.

    Tries Etherscan API first (fast, works on all chains),
    falls back to binary search on eth_getCode.
    """
    # Try Etherscan first
    block = _find_creation_block_etherscan(address, chain)
    if block is not None:
        print(f"  [events] Creation block from Etherscan: {block}")
        return block

    # Fallback to binary search
    print(f"  [events] Etherscan unavailable, using binary search...")
    return _find_creation_block_binary(w3, address)


# ---------------------------------------------------------------------------
# Chunked event scanning
# ---------------------------------------------------------------------------

# Default chunk sizes per chain (L2s have faster/smaller blocks)
_CHAIN_CHUNK_DEFAULTS = {
    "eth-mainnet": (2_000, 100),
    "arb-mainnet": (5_000_000, 100_000),
    "base-mainnet": (500_000, 10_000),
    "opt-mainnet": (500_000, 10_000),
}


def scan_events(
    w3: Web3,
    am_addr: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 0,
    min_chunk: int = 0,
    chain: str = "",
) -> list[dict]:
    """Scan RoleGranted and RoleRevoked events in chunks.

    Auto-halves chunk size on provider errors (range too large).
    Returns list of event dicts with keys: event, blockNumber, args.
    """
    if chunk_size == 0 or min_chunk == 0:
        defaults = _CHAIN_CHUNK_DEFAULTS.get(chain, (2_000, 100))
        if chunk_size == 0:
            chunk_size = defaults[0]
        if min_chunk == 0:
            min_chunk = defaults[1]

    am_addr = w3.to_checksum_address(am_addr)
    contract = w3.eth.contract(address=am_addr, abi=ACCESS_MANAGER_ABI)

    events = []
    current = from_block
    current_chunk = chunk_size

    while current <= to_block:
        end = min(current + current_chunk - 1, to_block)
        try:
            granted = contract.events.RoleGranted.get_logs(
                from_block=current, to_block=end
            )
            revoked = contract.events.RoleRevoked.get_logs(
                from_block=current, to_block=end
            )

            for e in granted:
                events.append({
                    "event": "RoleGranted",
                    "blockNumber": e["blockNumber"],
                    "transactionIndex": e.get("transactionIndex", 0),
                    "logIndex": e.get("logIndex", 0),
                    "args": {
                        "roleId": e["args"]["roleId"],
                        "account": e["args"]["account"],
                        "delay": e["args"]["delay"],
                        "since": e["args"]["since"],
                        "newMember": e["args"]["newMember"],
                    },
                })

            for e in revoked:
                events.append({
                    "event": "RoleRevoked",
                    "blockNumber": e["blockNumber"],
                    "transactionIndex": e.get("transactionIndex", 0),
                    "logIndex": e.get("logIndex", 0),
                    "args": {
                        "roleId": e["args"]["roleId"],
                        "account": e["args"]["account"],
                    },
                })

            current = end + 1
            # Restore chunk size after success
            if current_chunk < chunk_size:
                current_chunk = min(current_chunk * 2, chunk_size)

        except Exception as exc:
            exc_str = str(exc).lower()
            if current_chunk <= min_chunk:
                # Can't shrink further — skip this range
                print(f"  [events] Skipping blocks {current}-{end}: {exc}")
                current = end + 1
            elif "limit" in exc_str or "range" in exc_str or "too many" in exc_str or "query returned" in exc_str or "exceed" in exc_str or "block range" in exc_str:
                current_chunk = max(current_chunk // 2, min_chunk)
                print(f"  [events] Chunk too large, reducing to {current_chunk} blocks")
            else:
                # Unknown error — also try halving
                current_chunk = max(current_chunk // 2, min_chunk)
                print(f"  [events] Error scanning {current}-{end}, reducing chunk: {exc}")

    # Sort by block number, then transaction index, then log index
    events.sort(key=lambda e: (e["blockNumber"], e["transactionIndex"], e["logIndex"]))
    return events


# ---------------------------------------------------------------------------
# Build role map from events
# ---------------------------------------------------------------------------

def build_role_map(events: list[dict]) -> dict[int, dict[str, RoleHolder]]:
    """Process events chronologically to build {role_id: {address: RoleHolder}}.

    Grants add holders, revocations remove them.
    """
    role_map: dict[int, dict[str, RoleHolder]] = {}

    for e in events:
        role_id = e["args"]["roleId"]
        account = e["args"]["account"]
        role_map.setdefault(role_id, {})

        if e["event"] == "RoleGranted":
            role_map[role_id][account] = RoleHolder(
                address=account,
                role_id=role_id,
                delay=e["args"].get("delay", 0),
                since=e["args"].get("since", 0),
            )
        elif e["event"] == "RoleRevoked":
            role_map[role_id].pop(account, None)

    return role_map


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def _cache_dir(chain: str, am_addr: str) -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    return os.path.join(base, chain, am_addr.lower())


def _cache_path(chain: str, am_addr: str) -> str:
    return os.path.join(_cache_dir(chain, am_addr), "events.json")


def load_cache(chain: str, am_addr: str) -> Optional[dict]:
    """Load cached events. Returns None if cache is missing or corrupt."""
    path = _cache_path(chain, am_addr)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        # Validate structure
        if not isinstance(data.get("events"), list):
            return None
        if not isinstance(data.get("creation_block"), int):
            return None
        if not isinstance(data.get("last_scanned_block"), int):
            return None
        return data
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_cache(chain: str, am_addr: str, data: dict) -> None:
    """Save events cache to disk."""
    dir_path = _cache_dir(chain, am_addr)
    os.makedirs(dir_path, exist_ok=True)
    path = _cache_path(chain, am_addr)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# High-level discovery function
# ---------------------------------------------------------------------------

def discover_role_holders(
    w3: Web3,
    am_addr: str,
    chain: str,
    target_block: Optional[int] = None,
) -> dict[int, dict[str, RoleHolder]]:
    """Discover all role holders via event logs with incremental caching.

    1. Load cache
    2. Scan only new blocks (delta)
    3. Merge and save
    4. Return role_map filtered to target_block
    """
    if target_block is None:
        target_block = w3.eth.block_number

    cache = load_cache(chain, am_addr)

    if cache is not None:
        creation_block = cache["creation_block"]
        last_scanned = cache["last_scanned_block"]
        cached_events = cache["events"]
        print(f"  [events] Cache hit: {len(cached_events)} events up to block {last_scanned}")
    else:
        print(f"  [events] No cache, finding creation block...")
        creation_block = find_creation_block(w3, am_addr, chain)
        print(f"  [events] AccessManager deployed at block {creation_block}")
        last_scanned = creation_block - 1
        cached_events = []

    # Determine scan range
    scan_from = last_scanned + 1
    scan_to = max(target_block, last_scanned)  # Always scan at least up to target

    new_events = []
    if scan_from <= scan_to:
        total_blocks = scan_to - scan_from + 1
        print(f"  [events] Scanning blocks {scan_from} to {scan_to} ({total_blocks:,} blocks)...")
        new_events = scan_events(w3, am_addr, scan_from, scan_to, chain=chain)
        print(f"  [events] Found {len(new_events)} new events")

    # Merge all events
    all_events = cached_events + new_events

    # Update cache (don't truncate even if target_block < last_scanned)
    new_last_scanned = max(last_scanned, scan_to)
    save_cache(chain, am_addr, {
        "creation_block": creation_block,
        "last_scanned_block": new_last_scanned,
        "events": all_events,
    })

    # Filter events to target_block for building role map
    filtered = [e for e in all_events if e["blockNumber"] <= target_block]

    return build_role_map(filtered)
