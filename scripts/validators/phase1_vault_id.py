"""Phase 1: Vault Identity & Core Configuration (VC-001 to VC-056)."""

from abis import ACCESS_MANAGER_ABI, EIP1967_IMPLEMENTATION_SLOT, ERC20_ABI, PLASMA_VAULT_ABI, PRICE_ORACLE_ABI
from constants import ROLES, ZERO_ADDRESS

from .base import BaseValidator, Status

# Storage slot for WithdrawManager address in PlasmaVault
# keccak256(abi.encode(uint256(keccak256("ipor-fusion.plasma-vault.withdraw-manager.storage")) - 1)) & ~bytes32(uint256(0xff))
WITHDRAW_MANAGER_STORAGE_SLOT = "0x465d0d3e233965c3bc20e1506c3ce7a0e5d19f655c6cc5067a3f28bc10083100"

# ERC4626 deposit selector: deposit(uint256,address)
DEPOSIT_SELECTOR = bytes.fromhex("6e553f65")

# ERC20 transfer selector: transfer(address,uint256)
TRANSFER_SELECTOR = bytes.fromhex("a9059cbb")

# PUBLIC_ROLE = type(uint64).max
PUBLIC_ROLE = 2**64 - 1


class Phase1VaultIdentity(BaseValidator):
    phase_name = "Vault Identity & Core Configuration"
    phase_number = 1

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)

        # VC-001: Underlying asset
        ok, asset = self.call(vault, "asset")
        if ok and not self.is_zero(asset):
            self.ctx["asset"] = asset
            token = self.contract(asset, ERC20_ABI)
            _, token_symbol = self.call(token, "symbol")
            _, token_decimals = self.call(token, "decimals")
            self.ctx["asset_symbol"] = token_symbol or "UNKNOWN"
            self.ctx["asset_decimals"] = token_decimals or 18
            self.add("VC-001", "Underlying asset", Status.PASS,
                     f"{token_symbol} ({asset})",
                     f"Decimals: {token_decimals}")
        else:
            self.add("VC-001", "Underlying asset", Status.FAIL, asset,
                     "Could not read asset() or address is zero")

        # VC-002: AccessManager
        ok, am = self.call(vault, "getAccessManagerAddress")
        if ok and not self.is_zero(am):
            self.ctx["access_manager"] = am
            is_c = self.is_contract(am)
            self.add("VC-002", "AccessManager", Status.PASS if is_c else Status.WARN,
                     am, "Contract" if is_c else "WARNING: not a contract")
        else:
            self.add("VC-002", "AccessManager", Status.FAIL, am,
                     "Zero address or call failed")

        # VC-003: Price Oracle
        ok, oracle = self.call(vault, "getPriceOracleMiddleware")
        if ok and not self.is_zero(oracle):
            self.ctx["oracle"] = oracle
            self.add("VC-003", "PriceOracleMiddleware", Status.PASS, oracle)
        else:
            status = Status.WARN if ok else Status.FAIL
            self.add("VC-003", "PriceOracleMiddleware", status, oracle,
                     "Not configured" if ok else "Call failed")

        # VC-004: PlasmaVaultBase
        ok, base = self.call(vault, "PLASMA_VAULT_BASE")
        if ok:
            if self.is_zero(base):
                self.add("VC-004", "PlasmaVaultBase", Status.WARN, base, "Zero address")
            else:
                self.ctx["vault_base"] = base
                self.add("VC-004", "PlasmaVaultBase", Status.PASS, base)
        else:
            self.add("VC-004", "PlasmaVaultBase", Status.INFO, None, "Function not available (may be older version)")

        # VC-005: UUPS Implementation slot
        try:
            impl_raw = self.w3.eth.get_storage_at(self.vault_address, EIP1967_IMPLEMENTATION_SLOT)
            impl_addr = "0x" + impl_raw[-20:].hex()
            if self.is_zero(impl_addr):
                self.add("VC-005", "UUPS implementation", Status.INFO, None,
                         "No EIP-1967 implementation slot (may not be a proxy)")
            else:
                self.ctx["implementation"] = impl_addr
                is_c = self.is_contract(impl_addr)
                self.add("VC-005", "UUPS implementation", Status.PASS if is_c else Status.WARN,
                         impl_addr, "Contract" if is_c else "WARNING: not a contract")
        except Exception as e:
            self.add("VC-005", "UUPS implementation", Status.SKIP, None, str(e))

        # VC-006: Vault initialized (CRITICAL)
        # Call proxyInitialize with zero args — should revert if already initialized
        try:
            selector = self.w3.keccak(text="proxyInitialize(address,address)")[:4]
            data = selector + b'\x00' * 64  # two zero-address params
            self.w3.eth.call({"to": self.vault_address, "data": data})
            # If call succeeds, vault is NOT properly initialized
            self.add("VC-006", "Vault initialized", Status.FAIL,
                     "proxyInitialize did not revert",
                     "Vault may not be initialized — re-initialization possible")
        except Exception:
            # Revert is expected — vault is initialized
            self.add("VC-006", "Vault initialized", Status.PASS,
                     "proxyInitialize reverts", "Vault is properly initialized")

        # VC-010: Total supply cap
        ok, cap = self.call(vault, "getTotalSupplyCap")
        if ok:
            max_uint = 2**256 - 1
            if cap == max_uint:
                self.add("VC-010", "Supply cap", Status.INFO, "Unlimited (type(uint256).max)")
            elif cap == 0:
                self.add("VC-010", "Supply cap", Status.WARN, "0",
                         "Supply cap is zero — no deposits possible")
            else:
                decimals = self.ctx.get("asset_decimals", 18)
                self.add("VC-010", "Supply cap", Status.PASS,
                         self.fmt_wei(cap, decimals),
                         f"Raw: {cap}")
        else:
            self.add("VC-010", "Supply cap", Status.SKIP, None, "Call failed")

        # VC-011: Name & Symbol
        ok_n, name = self.call(vault, "name")
        ok_s, symbol = self.call(vault, "symbol")
        if ok_n and ok_s:
            self.ctx["vault_name"] = name
            self.ctx["vault_symbol"] = symbol
            self.add("VC-011", "Name & symbol", Status.PASS, f"{name} ({symbol})")
        else:
            self.add("VC-011", "Name & symbol", Status.WARN,
                     f"name={'?' if not ok_n else name}, symbol={'?' if not ok_s else symbol}")

        # VC-012: Decimals
        ok, decimals = self.call(vault, "decimals")
        if ok:
            underlying_dec = self.ctx.get("asset_decimals", 18)
            expected = underlying_dec + 2  # DECIMALS_OFFSET = 2
            if decimals == expected:
                self.add("VC-012", "Decimals", Status.PASS, decimals,
                         f"Underlying ({underlying_dec}) + offset (2) = {expected}")
            else:
                self.add("VC-012", "Decimals", Status.WARN, decimals,
                         f"Expected {expected} (underlying {underlying_dec} + 2)")
        else:
            self.add("VC-012", "Decimals", Status.SKIP, None, "Call failed")

        # VC-013: WithdrawManager (read from storage)
        try:
            wm_raw = self.w3.eth.get_storage_at(self.vault_address, WITHDRAW_MANAGER_STORAGE_SLOT)
            wm_addr = "0x" + wm_raw[-20:].hex()
            if not self.is_zero(wm_addr):
                self.ctx["withdraw_manager"] = wm_addr
                is_c = self.is_contract(wm_addr)
                self.add("VC-013", "WithdrawManager", Status.PASS if is_c else Status.WARN,
                         wm_addr, "Contract" if is_c else "WARNING: not a contract")
            else:
                self.add("VC-013", "WithdrawManager", Status.INFO, "Not configured",
                         "No WithdrawManager set (zero address in storage)")
        except Exception as e:
            self.add("VC-013", "WithdrawManager", Status.SKIP, None, str(e))

        # VC-014: Public vault status
        am_addr = self.ctx.get("access_manager")
        if am_addr:
            am = self.contract(am_addr, ACCESS_MANAGER_ABI)
            ok, role_id = self.call(am, "getTargetFunctionRole", self.vault_address, DEPOSIT_SELECTOR)
            if ok:
                if role_id == PUBLIC_ROLE:
                    self.add("VC-014", "Public vault status", Status.INFO,
                             "Public", "deposit() has PUBLIC_ROLE — anyone can deposit")
                else:
                    role_name = ROLES.get(role_id, f"Role({role_id})")
                    self.add("VC-014", "Public vault status", Status.INFO,
                             f"Restricted ({role_name})",
                             f"deposit() requires role {role_id}")
            else:
                self.add("VC-014", "Public vault status", Status.SKIP, None, "Call failed")

            # VC-015: Share transfers
            ok, role_id = self.call(am, "getTargetFunctionRole", self.vault_address, TRANSFER_SELECTOR)
            if ok:
                if role_id == PUBLIC_ROLE:
                    self.add("VC-015", "Share transfers", Status.INFO,
                             "Enabled", "transfer() has PUBLIC_ROLE — shares are transferable")
                else:
                    role_name = ROLES.get(role_id, f"Role({role_id})")
                    self.add("VC-015", "Share transfers", Status.INFO,
                             f"Restricted ({role_name})",
                             f"transfer() requires role {role_id}")
            else:
                self.add("VC-015", "Share transfers", Status.SKIP, None, "Call failed")
        else:
            self.add("VC-014", "Public vault status", Status.SKIP, None, "AccessManager not available")
            self.add("VC-015", "Share transfers", Status.SKIP, None, "AccessManager not available")

        # VC-016: RewardsClaimManager
        ok, rcm = self.call(vault, "getRewardsClaimManagerAddress")
        if ok:
            if self.is_zero(rcm):
                self.ctx["rewards_manager"] = None
                self.add("VC-016", "RewardsClaimManager", Status.INFO, "Not configured")
            else:
                self.ctx["rewards_manager"] = rcm
                self.add("VC-016", "RewardsClaimManager", Status.PASS, rcm)
        else:
            self.add("VC-016", "RewardsClaimManager", Status.SKIP, None, "Call failed")

        # VC-050: Total supply
        ok, supply = self.call(vault, "totalSupply")
        if ok:
            self.ctx["total_supply"] = supply
            decimals = self.ctx.get("asset_decimals", 18) + 2
            self.add("VC-050", "Total supply", Status.INFO,
                     self.fmt_wei(supply, decimals), f"Raw: {supply}")
        else:
            self.add("VC-050", "Total supply", Status.SKIP, None, "Call failed")

        # VC-051: Total assets
        ok, total_assets = self.call(vault, "totalAssets")
        if ok:
            self.ctx["total_assets"] = total_assets
            decimals = self.ctx.get("asset_decimals", 18)
            self.add("VC-051", "Total assets", Status.INFO,
                     f"{self.fmt_wei(total_assets, decimals)} {self.ctx.get('asset_symbol', '')}",
                     f"Raw: {total_assets}")
        else:
            self.add("VC-051", "Total assets", Status.SKIP, None, "Call failed")

        # VC-052: Share price sanity
        supply = self.ctx.get("total_supply")
        total_assets = self.ctx.get("total_assets")
        if supply is not None and total_assets is not None and supply > 0:
            ok, shares = self.call(vault, "convertToShares", 10**self.ctx.get("asset_decimals", 18))
            if ok and shares > 0:
                price = (10**self.ctx.get("asset_decimals", 18)) / (shares / 10**(self.ctx.get("asset_decimals", 18) + 2))
                self.add("VC-052", "Share price sanity", Status.PASS,
                         f"1 asset ≈ {shares} shares")
            else:
                self.add("VC-052", "Share price sanity", Status.INFO, None, "Could not compute share price")
        elif supply == 0:
            self.add("VC-052", "Share price sanity", Status.INFO, "N/A", "No shares minted yet")
        else:
            self.add("VC-052", "Share price sanity", Status.SKIP)

        # VC-053: Fuses list
        ok, fuses = self.call(vault, "getFuses")
        if ok:
            self.ctx["all_fuses"] = fuses
            self.add("VC-053", "Registered fuses", Status.PASS if len(fuses) > 0 else Status.WARN,
                     f"{len(fuses)} fuse(s)",
                     ", ".join(self.fmt_addr_named(f) for f in fuses[:10]) + ("..." if len(fuses) > 10 else ""))
        else:
            self.add("VC-053", "Registered fuses", Status.SKIP, None, "Call failed")

        # VC-054: Instant withdrawal fuses
        ok, iw_fuses = self.call(vault, "getInstantWithdrawalFuses")
        if ok:
            self.ctx["instant_withdrawal_fuses"] = iw_fuses
            self.add("VC-054", "Instant withdrawal fuses", Status.PASS if len(iw_fuses) > 0 else Status.WARN,
                     f"{len(iw_fuses)} fuse(s)",
                     ", ".join(self.fmt_addr_named(f) for f in iw_fuses[:10]))
        else:
            self.add("VC-054", "Instant withdrawal fuses", Status.SKIP, None, "Call failed")

        # VC-055: Asset price in oracle
        oracle_addr = self.ctx.get("oracle")
        asset_addr = self.ctx.get("asset")
        if oracle_addr and asset_addr:
            oracle_contract = self.contract(oracle_addr, PRICE_ORACLE_ABI)
            ok, result = self.call(oracle_contract, "getAssetPrice", self.w3.to_checksum_address(asset_addr))
            if ok:
                price, price_decimals = result
                if price > 0:
                    human_price = price / (10 ** price_decimals)
                    self.add("VC-055", "Asset price in oracle", Status.PASS,
                             f"${human_price:,.4f}",
                             f"Raw: {price}, decimals: {price_decimals}")
                else:
                    self.add("VC-055", "Asset price in oracle", Status.FAIL,
                             "0", "Price is zero — oracle misconfigured")
            else:
                self.add("VC-055", "Asset price in oracle", Status.WARN, None,
                         f"Oracle call failed: {result}")
        else:
            self.add("VC-055", "Asset price in oracle", Status.SKIP, None,
                     "Oracle or asset not available")

        # VC-056: Vault is a contract (basic sanity)
        if self.is_contract(self.vault_address):
            self.add("VC-056", "Vault is a contract", Status.PASS, self.vault_address)
        else:
            self.add("VC-056", "Vault is a contract", Status.FAIL, self.vault_address,
                     "Address has no code — not a contract")

        return self.results
