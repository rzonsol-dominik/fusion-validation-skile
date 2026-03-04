"""Web3 connection and Etherscan client."""

from __future__ import annotations

import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv
from web3 import Web3

from constants import CHAINS

load_dotenv()


def get_w3(chain: str, block: Optional[int] = None) -> Web3:
    """Create a Web3 instance for the given chain.

    Uses ALCHEMY_API_KEY from environment to build the RPC URL.
    If block is specified, sets default block for all calls.
    """
    if chain not in CHAINS:
        print(f"Error: unknown chain '{chain}'. Supported: {', '.join(CHAINS)}")
        sys.exit(1)

    api_key = os.environ.get("ALCHEMY_API_KEY")
    rpc_url = os.environ.get("RPC_URL")

    if not api_key and not rpc_url:
        print("Error: set ALCHEMY_API_KEY or RPC_URL in environment or .env file")
        sys.exit(1)

    if not rpc_url:
        network = CHAINS[chain]["alchemy_network"]
        rpc_url = f"https://{network}.g.alchemy.com/v2/{api_key}"

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print(f"Error: cannot connect to RPC at {rpc_url}")
        sys.exit(1)

    actual_chain_id = w3.eth.chain_id
    expected_chain_id = CHAINS[chain]["chain_id"]
    if actual_chain_id != expected_chain_id:
        print(f"Error: chain ID mismatch. Expected {expected_chain_id} ({chain}), got {actual_chain_id}")
        sys.exit(1)

    if block is not None:
        w3.eth.default_block = block

    return w3


def get_block_number(w3: Web3) -> int:
    """Get the block number being used for queries."""
    if isinstance(w3.eth.default_block, int):
        return w3.eth.default_block
    return w3.eth.block_number


def is_verified_on_etherscan(address: str, chain: str) -> Optional[bool]:
    """Check if a contract is verified on Etherscan/block explorer.

    Uses Etherscan V2 API with chainid parameter.
    Returns True/False, or None if the API key is not set or the call fails.
    """
    chain_cfg = CHAINS.get(chain)
    if not chain_cfg:
        return None

    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://api.etherscan.io/v2/api",
            params={
                "chainid": chain_cfg["chain_id"],
                "module": "contract",
                "action": "getabi",
                "address": address,
                "apikey": api_key,
            },
            timeout=10,
        )
        data = resp.json()
        return data.get("status") == "1"
    except Exception:
        return None
