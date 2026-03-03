# 05 - Fuses Catalog & Per-Protocol Validation

## Cel
Kompletny katalog fuse'ow z warunkami walidacji specyficznymi per protokol.

---

## Architektura Fuse

### Interfejsy bazowe:
- **IFuse**: `enter()` + `exit()` - glowne operacje
- **IFuseCommon**: `MARKET_ID()` - identyfikator marketu
- **IFuseInstantWithdraw**: `instantWithdraw(bytes32[] params)` - natychmiastowe wyplaty
- **IMarketBalanceFuse**: `balanceOf()` returns uint256 (USD, 18 decimals WAD)

### Wzorce walidacji w fuse'ach:
1. **Substrate validation**: Sprawdzenie czy asset/adres jest dozwolony w MARKET_ID
2. **Amount validation**: Sprawdzenie ze kwota > 0 i <= dostepny balance
3. **Approval management**: `forceApprove()` -> operacja -> `forceApprove(0)`
4. **Exit error handling**: Catchowane revert w trybie instant withdrawal (emit event zamiast revert)

---

## LENDING PROTOCOLS

### Aave V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AaveV2SupplyFuse | Supply/Withdraw | Asset addresses | aToken balance check |
| AaveV2BalanceFuse | Balance | - | aTokens - stable debt - variable debt |

**Warunki per-vault z Aave V2:**
- [ ] FV2-001: AAVE_POOL_V2 adres jest poprawny (immutable w fuse)
- [ ] FV2-002: AAVE_POOL_DATA_PROVIDER adres poprawny
- [ ] FV2-003: Substrates zawieraja TYLKO tokeny obslugiwane przez Aave V2
- [ ] FV2-004: Balance fuse prawidlowo odczytuje ceny z Aave oracle

### Aave V3
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AaveV3SupplyFuse | Supply/Withdraw | Asset addresses | E-mode category support |
| AaveV3BorrowFuse | Borrow/Repay | Asset addresses | Variable rate only (mode=2) |
| AaveV3CollateralFuse | Collateral | Asset addresses | Enable as collateral |
| AaveV3BalanceFuse | Balance | - | aTokens - debts per substrate |

**Warunki per-vault z Aave V3:**
- [ ] FV3-001: AAVE_POOL adres poprawny dla danego chaina
- [ ] FV3-002: AAVE_POOL_DATA_PROVIDER poprawny
- [ ] FV3-003: AAVE_PRICE_ORACLE poprawny
- [ ] FV3-004: E-mode category ID jest poprawny (jesli uzywany, < 256)
- [ ] FV3-005: Substrates to tokeny obslugiwane przez Aave V3 na tym chainie
- [ ] FV3-006: Jesli borrow - vault ma odpowiedni collateral
- [ ] FV3-007: Balance fuse uwzglednia zarowno supply jak i debt

### Compound V3
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| CompoundV3SupplyFuse | Supply/Withdraw | Asset addresses | Base token vs collateral logic |
| CompoundV3BalanceFuse | Balance | - | Comet balance tracking |

**Warunki:**
- [ ] FC3-001: COMET adres poprawny (immutable)
- [ ] FC3-002: COMPOUND_BASE_TOKEN poprawny
- [ ] FC3-003: Substrates rozrozniaja base token i collateral
- [ ] FC3-004: Balance fuse poprawnie rozroznia base token i collateral balance

### Morpho Blue
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| MorphoSupplyFuse | Supply/Withdraw | Morpho Market IDs (bytes32) | Market params resolution |
| MorphoBorrowFuse | Borrow/Repay | Morpho Market IDs | Shares vs amount conversion |
| MorphoCollateralFuse | Collateral | Morpho Market IDs | Collateral deposit |
| MorphoFlashLoanFuse | Flash loan | - | Flash loan execution |
| MorphoBalanceFuse | Balance | - | Supply + collateral - borrow |

**Warunki:**
- [ ] FM-001: MORPHO adres poprawny
- [ ] FM-002: Substrates to POPRAWNE Morpho market IDs (bytes32)
- [ ] FM-003: Kazdy Morpho market ID istnieje w Morpho Blue
- [ ] FM-004: Market params (loan token, collateral, oracle, IRM, LLTV) sa poprawne
- [ ] FM-005: Balance fuse uwzglednia supply shares, collateral I borrow shares

### Euler V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| EulerV2SupplyFuse | Supply/Withdraw | Euler vault addresses | EVC integration |
| EulerV2BorrowFuse | Borrow/Repay | Euler vault addresses | SubAccount mgmt |
| EulerV2CollateralFuse | Collateral | Euler vault addresses | Controller logic |
| EulerV2BatchFuse | Batch ops | - | Multi-call execution |
| EulerV2BalanceFuse | Balance | - | Per-vault balance tracking |

**Warunki:**
- [ ] FE-001: EVC (Ethereum Vault Connector) adres poprawny
- [ ] FE-002: Substrates to poprawne adresy Euler V2 vaultow
- [ ] FE-003: SubAccount generation jest deterministyczna i poprawna
- [ ] FE-004: Euler vaults sa aktywne i nie spauzowane

### Moonwell
**Warunki:**
- [ ] FMW-001: mToken adresy poprawne
- [ ] FMW-002: Comptroller adres poprawny
- [ ] FMW-003: Market jest wlaczony na Moonwell

### Silo V2
**Warunki:**
- [ ] FS-001: Silo config adresy poprawne
- [ ] FS-002: Silo index poprawny (borrowable vs non-borrowable)

---

## DEX & LIQUIDITY PROTOCOLS

### Uniswap V3
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| UniswapV3NewPositionFuse | Create/Close | Token pair addresses | NFT position mgmt |
| UniswapV3ModifyPositionFuse | Modify | Token pair addresses | Liquidity adjustment |
| UniswapV3CollectFuse | Collect fees | - | Fee collection |
| UniswapV3SwapFuse | Swap | Asset addresses | Path validation |
| UniswapV3Balance | Balance | - | Position value tracking |

**Warunki:**
- [ ] FU3-001: NonfungiblePositionManager adres poprawny
- [ ] FU3-002: UniversalRouter adres poprawny (dla swapow)
- [ ] FU3-003: Substrates zawieraja OBA tokeny kazdej pary
- [ ] FU3-004: Fee tier jest poprawny (500, 3000, 10000)
- [ ] FU3-005: Tick range jest sensowny dla strategii
- [ ] FU3-006: Path encoding zawiera TYLKO dozwolone tokeny

### Balancer V3
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| BalancerLiquidityProportionalFuse | Add/Remove | Pool + token addresses | Proportional liquidity |
| BalancerLiquidityUnbalancedFuse | Unbalanced | Pool + token addresses | Custom ratios |
| BalancerSingleTokenFuse | Single-sided | Pool + token addresses | Single token entry |
| BalancerGaugeFuse | Gauge stake | Gauge addresses | BPT staking |
| BalancerBalanceFuse | Balance | - | BPT + gauge tracking |

**Warunki:**
- [ ] FB-001: Router adres poprawny
- [ ] FB-002: Permit2 adres poprawny
- [ ] FB-003: Pool adresy sa poprawnymi poolami Balancer V3
- [ ] FB-004: Substrates zawieraja adres pool + WSZYSTKIE tokeny w pool
- [ ] FB-005: Token ordering w substrates zgadza sie z pool token ordering

### Aerodrome / Velodrome
**Warunki:**
- [ ] FA-001: Gauge adresy poprawne i aktywne
- [ ] FA-002: Router adres poprawny
- [ ] FA-003: Pool adresy poprawne
- [ ] FA-004: Substrates rozrozniaja gauge vs pool substrates

### Curve Stableswap NG
**Warunki:**
- [ ] FCS-001: Pool adres poprawny
- [ ] FCS-002: Gauge adres poprawny
- [ ] FCS-003: Pool coins sa zgodne z substrates

---

## YIELD PROTOCOLS

### Pendle
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| PendleSwapPTFuse | Swap to/from PT | Pendle market addresses | Complex swap routing |
| PendleRedeemPTAfterMaturityFuse | Redeem matured | Pendle market addresses | Maturity check |

**Warunki:**
- [ ] FP-001: Pendle router (IPActionSwapPTV3) adres poprawny
- [ ] FP-002: Substrates to poprawne adresy Pendle markets
- [ ] FP-003: Pendle markets nie sa expired/matured (chyba ze redeem)
- [ ] FP-004: SY token, PT token sa poprawne dla danego market

### Gearbox V3
**Warunki:**
- [ ] FG-001: FarmPool (farmdToken) adresy poprawne
- [ ] FG-002: Underlying dToken jest poprawny
- [ ] FG-003: FarmPool jest aktywny

---

## SWAP / ROUTER

### Universal Token Swapper
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| UniversalTokenSwapperFuse | Multi-DEX swap | Tokens + Targets + Slippage | USD slippage validation |
| SwapExecutor | Execution | - | Delegated swap execution |

**Warunki:**
- [ ] FTS-001: SwapExecutor adres poprawny
- [ ] FTS-002: Substrates zawieraja:
  - Token substrates (dozwolone tokeny)
  - Target substrates (dozwolone DEX aggregatory - 1inch, Odos, etc.)
  - Slippage substrates (max slippage config)
- [ ] FTS-003: Target addresses sa poprawnymi DEX aggregatorami
- [ ] FTS-004: Slippage limit jest sensowny (domyslnie 1% = 1e16 WAD)
- [ ] FTS-005: Price oracle jest dostepny dla walidacji slippage USD

---

## UTILITY FUSES

### Balance-only Fuses
- **Erc20BalanceFuse**: Prosty balance ERC20 tokena
- **Erc4626BalanceFuse**: Balance shares w ERC4626 vault
- **ZeroBalanceFuse**: Zawsze zwraca 0
- **AsyncActionBalanceFuse**: Async action results

### Maintenance Fuses
- **UpdateMarketsBalancesFuse**: Batch update balansow
- **ConfigureInstantWithdrawalFuse**: Konfiguracja wyplat
- **TransientStorage*Fuse**: Transient storage operations

---

## OGOLNE WARUNKI DLA WSZYSTKICH FUSE'OW

### FG-001: Fuse Code Verification
- **Warunek**: Kod fuse'a jest zweryfikowany na block explorerze
- **Jak sprawdzic**: Etherscan/Basescan verified contract
- **Oczekiwany wynik**: Verified source code

### FG-002: Fuse Immutable Parameters
- **Warunek**: Immutable parametry fuse'a (MARKET_ID, adresy protokolow) sa poprawne
- **Jak sprawdzic**: Odczyt publicznych immutable getterow
- **Oczekiwany wynik**: Wszystkie zgodne z oczekiwaniami

### FG-003: Fuse Not Upgradeable
- **Warunek**: Fuse NIE jest proxy (chyba ze zamierzony)
- **Jak sprawdzic**: Sprawdz czy adres jest EOA/immutable contract
- **Oczekiwany wynik**: Brak proxy pattern
- **Uwagi**: Fuse jest wywolywany przez delegatecall - upgradeable fuse to ryzyko
