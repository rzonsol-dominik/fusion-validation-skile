"""Base classes for vault validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List


class Status(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    INFO = "INFO"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    condition_id: str
    label: str
    status: Status
    value: Any = None
    detail: str = ""


class BaseValidator:
    """Base class for all phase validators.

    Subclasses must set `phase_name` and implement `run()`.
    """

    phase_name: str = ""
    phase_number: int = 0

    def __init__(self, w3, vault_address: str, ctx: dict):
        self.w3 = w3
        self.vault_address = w3.to_checksum_address(vault_address)
        self.ctx = ctx
        self.results: List[CheckResult] = []

    def run(self) -> list[CheckResult]:
        raise NotImplementedError

    def add(self, condition_id: str, label: str, status: Status, value: Any = None, detail: str = "") -> CheckResult:
        r = CheckResult(condition_id, label, status, value, detail)
        self.results.append(r)
        return r

    def call(self, contract, fn_name: str, *args):
        """Safe RPC call wrapper. Returns (success, value)."""
        try:
            fn = contract.functions[fn_name](*args)
            result = fn.call()
            return True, result
        except Exception as e:
            return False, str(e)

    def contract(self, address: str, abi: list) -> Any:
        """Create a web3 contract instance."""
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(address),
            abi=abi,
        )

    def is_zero(self, address: str) -> bool:
        return address == "0x" + "0" * 40

    def is_contract(self, address: str) -> bool:
        try:
            code = self.w3.eth.get_code(self.w3.to_checksum_address(address))
            return len(code) > 0
        except Exception:
            return False

    def resolve_name(self, address: str) -> str:
        """Resolve a human-readable name for an address.

        Tries: ctx cache -> ERC20 symbol() -> Etherscan contract name.
        """
        cache = self.ctx.setdefault("_name_cache", {})
        key = address.lower()
        if key in cache:
            return cache[key]

        # Try ERC20 symbol
        from abis import ERC20_ABI
        token = self.contract(address, ERC20_ABI)
        ok, symbol = self.call(token, "symbol")
        if ok and symbol:
            cache[key] = symbol
            return symbol

        # Try Etherscan contract name
        chain = self.ctx.get("chain", "")
        if chain:
            from rpc import get_contract_name
            name = get_contract_name(address, chain)
            if name:
                cache[key] = name
                return name

        cache[key] = ""
        return ""

    def fmt_addr_named(self, address: str) -> str:
        """Format address with resolved name: 'Name (`0xaddr`)' or '`0xaddr`'."""
        name = self.resolve_name(address)
        if name:
            return f"{name} ({self.fmt_addr(address)})"
        return self.fmt_addr(address)

    def fmt_addr(self, address: str) -> str:
        return f"`{address}`"

    def fmt_wei(self, value: int, decimals: int = 18) -> str:
        """Format a wei value to human-readable with decimals."""
        if value == 0:
            return "0"
        human = value / (10 ** decimals)
        if human >= 1_000_000:
            return f"{human:,.2f}"
        if human >= 1:
            return f"{human:.4f}"
        return f"{human:.8f}"
