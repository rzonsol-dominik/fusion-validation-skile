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

    def fmt_addr(self, address: str) -> str:
        return f"`{address[:6]}...{address[-4:]}`"

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
