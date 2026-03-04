"""Phase 7: Price Oracle (PO-001 to PO-022)."""

from abis import PRICE_ORACLE_ABI
from constants import USD_QUOTE_CURRENCY, ZERO_ADDRESS

from .base import BaseValidator, Status


class Phase7Oracle(BaseValidator):
    phase_name = "Price Oracle"
    phase_number = 7

    def run(self):
        oracle_addr = self.ctx.get("oracle")
        if not oracle_addr:
            self.add("PO-001", "Price oracle available", Status.SKIP,
                     None, "PriceOracleMiddleware not found in Phase 1")
            return self.results

        oracle = self.contract(oracle_addr, PRICE_ORACLE_ABI)

        # PO-001: Oracle is a contract
        if self.is_contract(oracle_addr):
            self.add("PO-001", "Oracle is a contract", Status.PASS, oracle_addr)
        else:
            self.add("PO-001", "Oracle is a contract", Status.FAIL, oracle_addr)
            return self.results

        # PO-002: Quote currency
        ok, quote = self.call(oracle, "QUOTE_CURRENCY")
        if ok:
            if quote.lower() == USD_QUOTE_CURRENCY.lower():
                self.add("PO-002", "Quote currency", Status.PASS, "USD")
            else:
                self.add("PO-002", "Quote currency", Status.INFO, quote,
                         "Non-standard quote currency")
        else:
            self.add("PO-002", "Quote currency", Status.SKIP, None, "Call failed")

        # PO-003: Quote currency decimals
        ok, qdecimals = self.call(oracle, "QUOTE_CURRENCY_DECIMALS")
        if ok:
            self.ctx["oracle_decimals"] = qdecimals
            if qdecimals in (8, 18):
                self.add("PO-003", "Quote currency decimals", Status.PASS, str(qdecimals))
            else:
                self.add("PO-003", "Quote currency decimals", Status.WARN,
                         str(qdecimals), "Unusual decimals — expected 8 or 18")
        else:
            self.add("PO-003", "Quote currency decimals", Status.SKIP, None, "Call failed")

        # PO-005: Asset price (underlying)
        asset_addr = self.ctx.get("asset")
        if asset_addr:
            ok, result = self.call(oracle, "getAssetPrice", self.w3.to_checksum_address(asset_addr))
            if ok:
                price, price_dec = result
                if price > 0:
                    human = price / (10 ** price_dec)
                    self.add("PO-005", f"Underlying asset price ({self.ctx.get('asset_symbol', '')})",
                             Status.PASS, f"${human:,.6f}")
                else:
                    self.add("PO-005", "Underlying asset price", Status.FAIL,
                             "0", "Zero price from oracle")
            else:
                self.add("PO-005", "Underlying asset price", Status.WARN,
                         None, f"Call failed: {result}")

        # PO-006: Price feed source for underlying
        if asset_addr:
            ok, source = self.call(oracle, "getSourceOfAssetPrice",
                                   self.w3.to_checksum_address(asset_addr))
            if ok:
                if self.is_zero(source):
                    self.add("PO-006", "Underlying price source", Status.INFO,
                             "Default (Chainlink Registry)")
                else:
                    self.add("PO-006", "Underlying price source", Status.INFO,
                             source, "Custom price source")
            else:
                self.add("PO-006", "Underlying price source", Status.SKIP, None, "Call failed")

        # PO-010: Substrate token prices
        market_substrates = self.ctx.get("market_substrates", {})
        checked_tokens = set()

        for market_id, substrates in market_substrates.items():
            for sub in substrates:
                hex_s = sub.hex() if isinstance(sub, bytes) else sub
                # Only check address-like substrates
                if hex_s[:24] == "0" * 24:
                    token_addr = "0x" + hex_s[24:]
                    if token_addr in checked_tokens or self.is_zero(token_addr):
                        continue
                    checked_tokens.add(token_addr)

                    ok, result = self.call(oracle, "getAssetPrice",
                                          self.w3.to_checksum_address(token_addr))
                    if ok:
                        price, price_dec = result
                        if price > 0:
                            human = price / (10 ** price_dec)
                            self.add(f"PO-010-{self.fmt_addr(token_addr)}",
                                     f"Substrate token {self.fmt_addr(token_addr)} price",
                                     Status.PASS, f"${human:,.6f}")
                        else:
                            self.add(f"PO-010-{self.fmt_addr(token_addr)}",
                                     f"Substrate token {self.fmt_addr(token_addr)} price",
                                     Status.WARN, "0",
                                     "Zero price — may be expected for non-token substrates")
                    else:
                        self.add(f"PO-010-{self.fmt_addr(token_addr)}",
                                 f"Substrate token {self.fmt_addr(token_addr)} price",
                                 Status.INFO, "No price feed",
                                 "May be expected for pool/vault substrates")

        if not checked_tokens and not asset_addr:
            self.add("PO-010", "Substrate token prices", Status.SKIP,
                     None, "No substrate tokens to check")

        return self.results
