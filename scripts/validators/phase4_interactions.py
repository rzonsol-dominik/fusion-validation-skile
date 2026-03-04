"""Phase 4: Market Interactions & Dependencies (MI-001 to MI-022)."""

from abis import PLASMA_VAULT_ABI
from constants import MARKETS

from .base import BaseValidator, Status


class Phase4Interactions(BaseValidator):
    phase_name = "Market Interactions & Dependencies"
    phase_number = 4

    def run(self):
        vault = self.contract(self.vault_address, PLASMA_VAULT_ABI)
        active_markets = self.ctx.get("active_markets", [])

        if not active_markets:
            self.add("MI-001", "Dependency graph", Status.SKIP,
                     None, "No active markets from Phase 3")
            return self.results

        # MI-001: Dependency balance graph for each market
        dep_graph = {}
        for market_id in active_markets:
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            ok, deps = self.call(vault, "getDependencyBalanceGraph", market_id)
            if ok:
                dep_graph[market_id] = deps
                if deps:
                    dep_names = [MARKETS.get(d, str(d)) for d in deps]
                    self.add(f"MI-001-{market_id}", f"{market_name} dependencies",
                             Status.INFO, ", ".join(dep_names))
                else:
                    self.add(f"MI-001-{market_id}", f"{market_name} dependencies",
                             Status.INFO, "None (independent)")
            else:
                self.add(f"MI-001-{market_id}", f"{market_name} dependencies",
                         Status.SKIP, None, "Call failed")

        self.ctx["dependency_graph"] = dep_graph

        # MI-005: Cycle detection in dependency graph
        if dep_graph:
            cycles = self._detect_cycles(dep_graph)
            if cycles:
                self.add("MI-005", "Dependency cycles", Status.FAIL,
                         f"{len(cycles)} cycle(s) detected",
                         " | ".join(str(c) for c in cycles))
            else:
                self.add("MI-005", "Dependency cycles", Status.PASS, "No cycles detected")

        # MI-010: Dependency completeness — all referenced markets should be active
        for market_id, deps in dep_graph.items():
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            missing = [d for d in deps if d not in active_markets]
            if missing:
                missing_names = [MARKETS.get(d, str(d)) for d in missing]
                self.add(f"MI-010-{market_id}", f"{market_name} dep completeness",
                         Status.WARN, f"Missing: {missing_names}",
                         "Dependencies reference markets without substrates")
            elif deps:
                self.add(f"MI-010-{market_id}", f"{market_name} dep completeness",
                         Status.PASS, f"All {len(deps)} deps are active markets")

        # MI-015: Market limits
        ok, limits_active = self.call(vault, "isMarketsLimitsActivated")
        if ok:
            self.ctx["markets_limits_active"] = limits_active
            self.add("MI-015", "Market limits activated", Status.INFO,
                     "Yes" if limits_active else "No")

            if limits_active:
                for market_id in active_markets:
                    market_name = MARKETS.get(market_id, f"Market({market_id})")
                    ok, limit = self.call(vault, "getMarketLimit", market_id)
                    if ok:
                        max_uint = 2**256 - 1
                        if limit == max_uint:
                            self.add(f"MI-015-{market_id}", f"{market_name} limit",
                                     Status.INFO, "Unlimited")
                        elif limit == 0:
                            self.add(f"MI-015-{market_id}", f"{market_name} limit",
                                     Status.WARN, "0",
                                     "Market limit is zero — no allocation possible")
                        else:
                            decimals = self.ctx.get("asset_decimals", 18)
                            self.add(f"MI-015-{market_id}", f"{market_name} limit",
                                     Status.INFO, self.fmt_wei(limit, decimals))
        else:
            self.add("MI-015", "Market limits", Status.SKIP, None, "Call failed")

        # MI-020: Total assets per market
        for market_id in active_markets:
            market_name = MARKETS.get(market_id, f"Market({market_id})")
            ok, balance = self.call(vault, "totalAssetsInMarket", market_id)
            if ok:
                decimals = self.ctx.get("asset_decimals", 18)
                self.add(f"MI-020-{market_id}", f"{market_name} balance",
                         Status.INFO, f"{self.fmt_wei(balance, decimals)} {self.ctx.get('asset_symbol', '')}",
                         f"Raw: {balance}")
            else:
                self.add(f"MI-020-{market_id}", f"{market_name} balance",
                         Status.SKIP, None, "Call failed")

        return self.results

    def _detect_cycles(self, graph: dict) -> list:
        """Detect cycles in the dependency graph using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {m: WHITE for m in graph}
        cycles = []

        def dfs(node, path):
            color[node] = GRAY
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    color[neighbor] = WHITE
                if color.get(neighbor) == GRAY:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif color.get(neighbor) == WHITE:
                    dfs(neighbor, path)
            path.pop()
            color[node] = BLACK

        for node in list(graph.keys()):
            if color.get(node) == WHITE:
                dfs(node, [])

        return cycles
