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
- [ ] FV2-001: AAVE_V2_POOL_ADDRESSES_PROVIDER adres jest poprawny (immutable w fuse - pool i data provider pobierane dynamicznie)
- [ ] FV2-002: Pool address z providera jest poprawny
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
- [ ] FV3-001: AAVE_V3_POOL_ADDRESSES_PROVIDER adres poprawny dla danego chaina (immutable w fuse - pool, data provider i oracle sa pobierane dynamicznie z tego providera)
- [ ] FV3-002: Pool address z providera jest poprawny (`provider.getPool()`)
- [ ] FV3-003: Data provider i Price Oracle z providera sa poprawne
- [ ] FV3-004: E-mode category ID jest poprawny (jesli uzywany, < 256)
- [ ] FV3-005: Substrates to tokeny obslugiwane przez Aave V3 na tym chainie
- [ ] FV3-006: Jesli borrow - vault ma odpowiedni collateral
- [ ] FV3-007: Balance fuse uwzglednia zarowno supply jak i debt
- [ ] FV3-008: Istnieje wariant AaveV3WithPriceOracleMiddlewareBalanceFuse - sprawdz ktory balance fuse jest uzyty

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
| MorphoSupplyWithCallBackDataFuse | Supply z callback | Morpho Market IDs | Supply z callback data |
| MorphoFlashLoanFuse | Flash loan | - | Flash loan execution |
| MorphoBalanceFuse | Balance | - | Supply + collateral - borrow |
| MorphoOnlyLiquidityBalanceFuse | Balance (liquidity) | - | Tylko supply liquidity (bez collateral) |

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
| EulerV2ControllerFuse | Controller | Euler vault addresses | Controller enable/disable |
| EulerV2BatchFuse | Batch ops | - | Multi-call execution |
| EulerV2BalanceFuse | Balance | - | Per-vault balance tracking |

**Warunki:**
- [ ] FE-001: EVC (Ethereum Vault Connector) adres poprawny
- [ ] FE-002: Substrates to poprawne adresy Euler V2 vaultow
- [ ] FE-003: SubAccount generation jest deterministyczna i poprawna
- [ ] FE-004: Euler vaults sa aktywne i nie spauzowane

### Moonwell
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| MoonwellSupplyFuse | Supply/Withdraw | Asset addresses | mToken balance check |
| MoonwellBorrowFuse | Borrow/Repay | Asset addresses | Borrow limit check |
| MoonwellEnableMarketFuse | Market enable | Asset addresses | Comptroller enterMarkets |
| MoonwellBalanceFuse | Balance | - | Supply - borrow tracking |

**Warunki:**
- [ ] FMW-001: mToken adresy poprawne
- [ ] FMW-002: Comptroller adres poprawny
- [ ] FMW-003: Market jest wlaczony na Moonwell
- [ ] FMW-004: Jesli borrow - vault ma odpowiedni collateral (enterMarkets wywolane)
- [ ] FMW-005: Balance fuse uwzglednia zarowno supply jak i borrow (net position)

### Silo V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| SiloV2SupplyBorrowableCollateralFuse | Supply (borrowable) | Silo addresses | Borrowable collateral deposit |
| SiloV2SupplyNonBorrowableCollateralFuse | Supply (protected) | Silo addresses | Non-borrowable collateral deposit |
| SiloV2BorrowFuse | Borrow/Repay | Silo addresses | Borrow from silo |
| SiloV2BalanceFuse | Balance | - | Net position tracking |

**Warunki:**
- [ ] FS-001: Silo config adresy poprawne
- [ ] FS-002: Silo index poprawny (borrowable vs non-borrowable)
- [ ] FS-003: Rozroznienie miedzy borrowable i non-borrowable collateral fuse

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

### Aerodrome
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AerodromeLiquidityFuse | Add/Remove LP | Pool addresses | Liquidity provision |
| AerodromeGaugeFuse | Gauge stake/unstake | Gauge addresses | LP staking |
| AerodromeClaimFeesFuse | Collect fees | Pool addresses | Trading fees collection |
| AerodromeBalanceFuse | Balance | - | LP + gauge tracking |

### Aerodrome Slipstream
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AreodromeSlipstreamNewPositionFuse | Create position | Token pairs | CL NFT position mgmt |
| AreodromeSlipstreamModifyPositionFuse | Modify position | Token pairs | Liquidity adjustment |
| AreodromeSlipstreamCollectFuse | Collect fees | - | Fee collection |
| AreodromeSlipstreamCLGaugeFuse | Gauge stake | Gauge addresses | CL gauge staking |
| AreodromeSlipstreamBalanceFuse | Balance | - | Position value tracking |

### Velodrome Superchain
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| VelodromeSuperchainLiquidityFuse | Add/Remove LP | Pool addresses | Liquidity provision |
| VelodromeSuperchainGaugeFuse | Gauge stake/unstake | Gauge addresses | LP staking |
| VelodromeSuperchainBalanceFuse | Balance | - | LP + gauge tracking |

### Velodrome Superchain Slipstream
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| VelodromeSuperchainSlipstreamNewPositionFuse | Create position | Token pairs | CL NFT position mgmt |
| VelodromeSuperchainSlipstreamModifyPositionFuse | Modify position | Token pairs | Liquidity adjustment |
| VelodromeSuperchainSlipstreamCollectFuse | Collect fees | - | Fee collection |
| VelodromeSuperchainSlipstreamLeafCLGaugeFuse | Gauge stake | Gauge addresses | CL gauge staking |
| VelodromeSuperchainSlipstreamBalanceFuse | Balance | - | Position value tracking |

**Warunki (Aerodrome / Velodrome wspolne):**
- [ ] FA-001: Gauge adresy poprawne i aktywne
- [ ] FA-002: Router adres poprawny
- [ ] FA-003: Pool adresy poprawne
- [ ] FA-004: Substrates rozrozniaja gauge vs pool substrates
- [ ] FA-005: Slipstream - max 50 pozycji per substrate (ochrona DoS gas exhaustion)
- [ ] FA-006: Gauge positions NIE wliczaja trading fees (ida do veVELO/veAERO voters)

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
| UniversalTokenSwapperEthFuse | Swap z ETH wrapping | Tokens + Targets + Slippage | Jak UTS + WETH wrap/unwrap |
| UniversalTokenSwapperWithVerificationFuse | Swap z weryfikacja | Tokens + Targets + Slippage | Dodatkowa weryfikacja po swapie |
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

### Odos Swapper
**Warunki:**
- [ ] FOS-001: OdosSwapperFuse zdeployowany z poprawnymi parametrami
- [ ] FOS-002: Odos executor adres poprawny

### Enso
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| EnsoFuse | Multi-protocol execution | Targets + tokens | Delegated execution via Enso |
| EnsoInitExecutorFuse | Init executor | - | Inicjalizacja Enso executora |
| EnsoBalanceFuse | Balance | - | Tracking pozycji Enso |

**Warunki:**
- [ ] FEN-001: EnsoFuse z poprawnym executor adresem
- [ ] FEN-002: EnsoExecutor adres poprawny
- [ ] FEN-003: EnsoInitExecutorFuse wywolany przed uzyciem EnsoFuse

---

## DODATKOWE PROTOKOLY (szczegoly fuse'ow)

### Aave V4
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AaveV4SupplyFuse | Supply/Withdraw | Asset addresses | Aave V4 pool |
| AaveV4BorrowFuse | Borrow/Repay | Asset addresses | Variable rate borrow |
| AaveV4EModeFuse | E-Mode | - | E-mode category switch |
| AaveV4BalanceFuse | Balance | - | Supply - debt tracking |

**Warunki:**
- [ ] FV4-001: Pool adres poprawny dla Aave V4
- [ ] FV4-002: E-mode category ID poprawny (jesli uzywany)
- [ ] FV4-003: Market ID 45 - UWAGA: duplikat z MIDAS!

### Midas
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| MidasSupplyFuse | Supply/Withdraw | Asset addresses | Midas vault deposit |
| MidasRequestSupplyFuse | Request-based supply | Asset addresses | Async request-based |
| MidasBalanceFuse | Balance | - | Position tracking |

**Warunki:**
- [ ] FMI-001: Midas vault adresy poprawne
- [ ] FMI-002: Market ID 45 - UWAGA: duplikat z AAVE_V4!

### Napier
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| NapierDepositFuse | Deposit | Napier pool addresses | Deposit do pool |
| NapierSupplyFuse | Supply | Napier pool addresses | Supply liquidity |
| NapierRedeemFuse | Redeem | Napier pool addresses | Redeem z pool |
| NapierSwapPtFuse | Swap PT | Napier market addresses | PT swap |
| NapierSwapYtFuse | Swap YT | Napier market addresses | YT swap |
| NapierCombineFuse | Combine PT+YT | Napier market addresses | Combine to underlying |
| NapierCollectFuse | Collect fees | - | Fee collection |
| NapierZapDepositFuse | Zap deposit | - | Single-tx deposit |
| NapierUniversalRouterFuse | Router | - | Multi-path routing |

**Warunki:**
- [ ] FN-001: Napier router adres poprawny
- [ ] FN-002: Pool/market adresy poprawne i aktywne
- [ ] FN-003: UWAGA: Brak balance fuse dla Napier w kodzie! Wymaga custom tracking

### Ebisu
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| EbisuZapperCreateFuse | Create trove | Asset addresses | Liquity-style trove creation |
| EbisuAdjustTroveFuse | Adjust trove | - | Modify collateral/debt |
| EbisuAdjustInterestRateFuse | Interest rate | - | Rate adjustment |
| EbisuZapperLeverModifyFuse | Leveraged modify | - | Leverage operations |
| EbisuZapperBalanceFuse | Balance | - | Trove value tracking |

**Warunki:**
- [ ] FEB-001: Zapper adres poprawny
- [ ] FEB-002: BoldToken i WETH adresy poprawne
- [ ] FEB-003: Trove manager adres poprawny

### Liquity V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| LiquityStabilityPoolFuse | Stability Pool | Pool addresses | Deposit/withdraw z SP |
| LiquityBalanceFuse | Balance | - | SP position tracking |

**Warunki:**
- [ ] FL2-001: Stability Pool adres poprawny
- [ ] FL2-002: BOLD token adres poprawny

### TAC Staking
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| TacStakingBalanceFuse | Balance | - | Staked position tracking |
| TacStakingDelegateFuse | Delegate | Validator addresses | Delegate stake |
| TacStakingRedelegateFuse | Redelegate | Validator addresses | Move stake |
| TacStakingEmergencyFuse | Emergency | - | Emergency unstake |

**Warunki:**
- [ ] FTC-001: TAC staking contract adres poprawny
- [ ] FTC-002: Validator adresy sa poprawne i aktywne

### Stake DAO V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| StakeDaoV2SupplyFuse | Supply/Withdraw | Vault addresses | Stake DAO vault deposit |
| StakeDaoV2BalanceFuse | Balance | - | Nested ERC4626 tracking |

**Warunki:**
- [ ] FSD-001: Stake DAO vault adresy poprawne
- [ ] FSD-002: Nested vault chain: reward vault → LP vault → underlying

### Yield Basis
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| YieldBasisLtSupplyFuse | Supply/Withdraw | YB pool addresses | YB LT deposit |
| YieldBasisLtBalanceFuse | Balance | - | Position tracking |

**Warunki:**
- [ ] FYB-001: Yield Basis pool adres poprawny

### Async Action
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| AsyncActionFuse | Async execution | Target addresses | Asynchroniczne operacje |
| AsyncActionBalanceFuse | Balance | - | Async result tracking |

**Warunki:**
- [ ] FAA-001: Target adresy poprawne i zaufane
- [ ] FAA-002: Callback handlers skonfigurowane dla async callbacks

### Compound V2
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| CompoundV2SupplyFuse | Supply/Withdraw | Asset addresses | cToken interaction |
| CompoundV2BalanceFuse | Balance | - | cToken balance tracking |

**Warunki:**
- [ ] FC2-001: cToken adresy poprawne
- [ ] FC2-002: Comptroller adres poprawny

### Lido (chain-specific: Ethereum)
| Fuse | Typ | Substrates | Walidacja specyficzna |
|------|-----|------------|----------------------|
| StEthWrapperFuse | Wrap/Unwrap | - | stETH <-> wstETH conversion |

**Warunki:**
- [ ] FLI-001: stETH i wstETH adresy poprawne
- [ ] FLI-002: Tylko na Ethereum mainnet

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
- **UpdateWithdrawManagerMaintenanceFuse**: Aktualizacja adresu WithdrawManager
- **BurnRequestFeeFuse**: Spalanie request fee shares
- **TransientStorageSetInputsFuse**: Ustawienie danych w transient storage
- **TransientStorageMapperFuse**: Mapowanie danych w transient storage
- **TransientStorageChainReaderFuse**: Odczyt danych z transient storage

### PlasmaVault-specific Fuses
- **PlasmaVaultRequestSharesFuse**: Request shares do scheduled withdrawal
- **PlasmaVaultRedeemFromRequestFuse**: Redeem z requestu
- **PlasmaVaultBalanceAssetsValidationFuse**: Walidacja integralnosci assetow

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
