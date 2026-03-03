# 11 - Checklist Per Market Type

## Cel
Gotowe checklisty walidacji dla kazdego TYPU marketu dodawanego do vaulta.
Uzyj odpowiedniej checklisty gdy dodajesz nowy market.

---

## A. LENDING MARKET (Aave V2/V3/V4, Compound V2/V3, Morpho, Euler, Moonwell, Silo)

### Przed dodaniem:
- [ ] **LM-01**: Market ID jest poprawny (z IporFusionMarkets.sol)
- [ ] **LM-02**: Supply fuse zdeployowany z poprawnymi parametrami (pool address, market ID)
- [ ] **LM-03**: Balance fuse zdeployowany z tym samym market ID
- [ ] **LM-04**: Substrates zawieraja adresy tokenow ktore vault bedzie supply'owac
- [ ] **LM-05**: Underlying token vaulta jest jednym z substrate assets
- [ ] **LM-06**: Supply fuse zarejestrowany w vault (`addFuses()`)
- [ ] **LM-07**: Balance fuse przypisany do marketu (`addBalanceFuse()`)
- [ ] **LM-08**: Substrates granted (`grantMarketSubstrates()`)

### Jesli vault BORROW na tym markecie:
- [ ] **LM-10**: Borrow fuse zdeployowany i zarejestrowany
- [ ] **LM-11**: Collateral fuse zdeployowany i zarejestrowany (jesli oddzielny)
- [ ] **LM-12**: Dependency na ERC20_VAULT_BALANCE (borrow przynosi tokeny do vault)
- [ ] **LM-13**: Balance fuse uwzglednia debt (supply - borrow = net)
- [ ] **LM-14**: Market limits uwzgledniaja ryzyko leverage

### Instant withdrawal:
- [ ] **LM-20**: Supply fuse implementuje `IFuseInstantWithdraw`
- [ ] **LM-21**: Fuse dodany do instant withdrawal fuses z poprawnymi parametrami
- [ ] **LM-22**: Parametr params[1+] zawiera asset address do withdrawal

### Rewards:
- [ ] **LM-30**: Claim fuse zarejestrowany w RewardsClaimManager (jesli protocol daje rewards)
- [ ] **LM-31**: Odpowiednia rola CLAIM_REWARDS_ROLE jest aktywna

### Price Oracle:
- [ ] **LM-40**: Price feed istnieje dla kazdego supply tokena
- [ ] **LM-41**: Jesli protokol ma wlasny oracle (Aave) - balance fuse go uzywa poprawnie

---

## B. DEX SWAP MARKET (Uniswap V2/V3 swap, Universal Token Swapper, Odos)

### Przed dodaniem:
- [ ] **SM-01**: Market ID poprawny
- [ ] **SM-02**: Swap fuse zdeployowany z poprawnymi parametrami (router address)
- [ ] **SM-03**: Substrates zawieraja WSZYSTKIE tokeny przez ktore vault moze swapowac
- [ ] **SM-04**: Swap fuse zarejestrowany w vault
- [ ] **SM-05**: Substrates granted

### Dependencies:
- [ ] **SM-10**: Dependency na ERC20_VAULT_BALANCE (swap zmienia balance tokenow)
- [ ] **SM-11**: Jesli swap wplywuwa na inne markety - dependencies sa skonfigurowane

### Universal Token Swapper specifics:
- [ ] **SM-20**: Token substrates: dozwolone tokeny wejscia/wyjscia
- [ ] **SM-21**: Target substrates: dozwolone DEX aggregatory (adresy)
- [ ] **SM-22**: Slippage substrates: max slippage configuration
- [ ] **SM-23**: Targets sa sprawdzonymi/zaufanymi agregatrami (nie random contracts)
- [ ] **SM-24**: SwapExecutor adres poprawny

### Price Oracle:
- [ ] **SM-30**: Price feed dla kazdego tokena w swap path

### Uwagi:
- Swap markety zazwyczaj NIE maja balance fuse (ERC20_VAULT_BALANCE sledzi wynik)
- Swap markety zazwyczaj NIE sa w instant withdrawal fuses

---

## C. LP POSITION MARKET (Uniswap V3 positions, Balancer, Curve pool, Aerodrome/Velodrome)

### Przed dodaniem:
- [ ] **LP-01**: Market ID poprawny
- [ ] **LP-02**: Position fuse (New/Modify/Collect) zdeployowane z poprawnymi parametrami
- [ ] **LP-03**: Balance fuse zdeployowany z tym samym market ID
- [ ] **LP-04**: Substrates zawieraja:
  - Adresy par tokenow (dla Uniswap V3)
  - Adresy pooli + tokeny (dla Balancer, Curve)
  - Adresy gauge + pool (dla Aerodrome/Velodrome)
- [ ] **LP-05**: Fuses zarejestrowane w vault
- [ ] **LP-06**: Balance fuse przypisany do marketu
- [ ] **LP-07**: Substrates granted

### Dependencies:
- [ ] **LP-10**: Dependency na ERC20_VAULT_BALANCE (LP zmienia balance tokenow)
- [ ] **LP-11**: Jesli LP token jest stakowany w gauge - dependency miedzy LP market a gauge market

### Instant withdrawal:
- [ ] **LP-20**: Fuse z odpowiednia metoda exit/withdraw
- [ ] **LP-21**: Fuse dodany do instant withdrawal fuses jesli potrzebny
- [ ] **LP-22**: Uwzglednij ze withdrawal z LP moze miec slippage

### Price Oracle:
- [ ] **LP-30**: Price feed dla obu tokenow w parze
- [ ] **LP-31**: Jesli LP token ma swoj price feed - jest poprawny

### Uniswap V3 specifics:
- [ ] **LP-40**: NFT position tracking w FuseStorageLib
- [ ] **LP-41**: Fee tier (500/3000/10000) jest poprawny
- [ ] **LP-42**: Tick range jest sensowny
- [ ] **LP-43**: PositionValue.total() poprawnie wycenia pozycje

---

## D. STAKING / GAUGE MARKET (Curve gauge, Aerodrome gauge, Gearbox farm, Fluid staking)

### Przed dodaniem:
- [ ] **ST-01**: Market ID poprawny
- [ ] **ST-02**: Staking fuse zdeployowany z poprawnymi parametrami
- [ ] **ST-03**: Balance fuse zdeployowany
- [ ] **ST-04**: Substrates zawieraja adresy gauge/staking contractow
- [ ] **ST-05**: Fuses zarejestrowane
- [ ] **ST-06**: Balance fuse przypisany
- [ ] **ST-07**: Substrates granted

### Dependencies:
- [ ] **ST-10**: Dependency na market z ktorego pochodzi stakowany token
  - Curve gauge → Curve pool market
  - Aerodrome gauge → Aerodrome liquidity market
  - Gearbox farm → Gearbox pool market
  - Fluid staking → Fluid pool market
- [ ] **ST-11**: Jesli unstake wplywuwa na vault balance → dependency na ERC20_VAULT_BALANCE

### Instant withdrawal:
- [ ] **ST-20**: Unstake fuse w instant withdrawal fuses (jesli potrzebny)
- [ ] **ST-21**: Kolejnosc: najpierw unstake z gauge, potem withdraw z LP

### Rewards:
- [ ] **ST-30**: Gauge/staking generuje rewards → claim fuse skonfigurowany
- [ ] **ST-31**: Rewards claim fuse w RewardsClaimManager

---

## E. YIELD PROTOCOL MARKET (Pendle, Gearbox, Midas, ERC4626 vaults)

### Przed dodaniem:
- [ ] **YP-01**: Market ID poprawny
- [ ] **YP-02**: Supply/Swap fuse zdeployowany z poprawnymi parametrami
- [ ] **YP-03**: Balance fuse zdeployowany
- [ ] **YP-04**: Substrates zawieraja adresy marketow/vaultow protokolu
- [ ] **YP-05**: Fuses zarejestrowane i balance fuse przypisany
- [ ] **YP-06**: Substrates granted

### Pendle specifics:
- [ ] **YP-10**: Pendle market address jest poprawny i aktywny
- [ ] **YP-11**: SY token, PT token sa sprawdzone
- [ ] **YP-12**: Expiry date Pendle marketu jest w przyszlosci (chyba ze redeem)
- [ ] **YP-13**: GuessedPtOut parametry sa rozsadne

### ERC4626 vault specifics:
- [ ] **YP-20**: Vault address jest poprawny i zweryfikowany
- [ ] **YP-21**: Underlying token external vault == oczekiwany token
- [ ] **YP-22**: ERC4626PriceFeed skonfigurowany dla share tokena

### Dependencies:
- [ ] **YP-30**: Dependency na ERC20_VAULT_BALANCE jesli operacja zmienia vault balance

---

## F. FLASH LOAN MARKET (Morpho Flash Loan)

### Przed dodaniem:
- [ ] **FL-01**: Market ID = MORPHO_FLASH_LOAN
- [ ] **FL-02**: Flash loan fuse zdeployowany z poprawnym MORPHO address
- [ ] **FL-03**: Fuse zarejestrowany w vault
- [ ] **FL-04**: Callback handlers skonfigurowane dla flash loan callback
- [ ] **FL-05**: Flash loan jest uzywany TYLKO w ramach execute() (nie standalone)

---

## G. SPECIAL MARKETS

### ERC20_VAULT_BALANCE (Balance Only):
- [ ] **SP-01**: Erc20BalanceFuse przypisany jako balance fuse
- [ ] **SP-02**: Market ID = 7 (ERC20_VAULT_BALANCE z IporFusionMarkets.sol)
- [ ] **SP-03**: Ten market ZAWSZE musi istniec w vaulcie - sledzi natywny balance underlying tokena

### ZERO_BALANCE_MARKET:
- [ ] **SP-10**: ZeroBalanceFuse przypisany (jesli uzywany)
- [ ] **SP-11**: Uzywanego do marketow ktore celowo maja balance 0

### ASSETS_BALANCE_VALIDATION:
- [ ] **SP-20**: PlasmaVaultBalanceAssetsValidationFuse (jesli uzywany)
- [ ] **SP-21**: Walidacja integralnosci assetow

---

## PODSUMOWANIE - UNIWERSALNY CHECKLIST PER MARKET

Niezaleznie od typu marketu, ZAWSZE sprawdz:

| # | Co sprawdzic | Jak |
|---|-------------|-----|
| 1 | Market ID poprawny | `IFuseCommon(fuse).MARKET_ID()` |
| 2 | Balance fuse przypisany | `isBalanceFuseSupported(marketId, fuse)` |
| 3 | Supply/interaction fuses zarejestrowane | `isFuseSupported(fuse)` |
| 4 | Substrates granted | `getMarketSubstrates(marketId)` |
| 5 | Substrates poprawne | Dekoduj i porownaj z oczekiwanymi |
| 6 | Dependencies skonfigurowane | `getDependencyBalanceGraph(marketId)` |
| 7 | Instant withdrawal (jesli potrzebny) | `getInstantWithdrawalFuses()` |
| 8 | Market limits (jesli aktywne) | `getMarketLimit(marketId)` |
| 9 | Price feeds dla assetow | `getAssetPrice(asset)` |
| 10 | Reward claim fuse (jesli rewards) | `rewardsManager.getRewardsFuses()` |
