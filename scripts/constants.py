"""Constants for IPOR Fusion vault validation."""

# ---------------------------------------------------------------------------
# Role IDs (from contracts/libraries/Roles.sol)
# ---------------------------------------------------------------------------
ROLES = {
    0: "ADMIN_ROLE",
    1: "OWNER_ROLE",
    2: "GUARDIAN_ROLE",
    3: "TECH_PLASMA_VAULT_ROLE",
    4: "IPOR_DAO_ROLE",
    5: "TECH_CONTEXT_MANAGER_ROLE",
    6: "TECH_WITHDRAW_MANAGER_ROLE",
    7: "TECH_VAULT_TRANSFER_SHARES_ROLE",
    100: "ATOMIST_ROLE",
    200: "ALPHA_ROLE",
    300: "FUSE_MANAGER_ROLE",
    301: "PRE_HOOKS_MANAGER_ROLE",
    400: "TECH_PERFORMANCE_FEE_MANAGER_ROLE",
    500: "TECH_MANAGEMENT_FEE_MANAGER_ROLE",
    600: "CLAIM_REWARDS_ROLE",
    601: "TECH_REWARDS_CLAIM_MANAGER_ROLE",
    700: "TRANSFER_REWARDS_ROLE",
    800: "WHITELIST_ROLE",
    900: "CONFIG_INSTANT_WITHDRAWAL_FUSES_ROLE",
    901: "WITHDRAW_MANAGER_REQUEST_FEE_ROLE",
    902: "WITHDRAW_MANAGER_WITHDRAW_FEE_ROLE",
    1000: "UPDATE_MARKETS_BALANCES_ROLE",
    1100: "UPDATE_REWARDS_BALANCE_ROLE",
    1200: "PRICE_ORACLE_MIDDLEWARE_MANAGER_ROLE",
    # PUBLIC_ROLE = type(uint64).max
    2**64 - 1: "PUBLIC_ROLE",
}

ROLE_IDS = {v: k for k, v in ROLES.items()}

# Roles that should be inspected for holders
INSPECTABLE_ROLES = [0, 1, 2, 3, 100, 200, 300, 301, 400, 500, 600, 601, 700, 800, 900, 1000, 1100, 1200]

# Technical roles (should only be held by contracts, not EOAs)
TECH_ROLES = [3, 4, 5, 6, 7, 400, 500, 601]

# ---------------------------------------------------------------------------
# Market IDs (from contracts/libraries/IporFusionMarkets.sol)
# ---------------------------------------------------------------------------
MARKETS = {
    1: "AAVE_V3",
    2: "COMPOUND_V3_USDC",
    3: "GEARBOX_POOL_V3",
    4: "GEARBOX_FARM_DTOKEN_V3",
    5: "FLUID_INSTADAPP_POOL",
    6: "FLUID_INSTADAPP_STAKING",
    7: "ERC20_VAULT_BALANCE",
    8: "UNISWAP_SWAP_V3_POSITIONS",
    9: "UNISWAP_SWAP_V2",
    10: "UNISWAP_SWAP_V3",
    11: "EULER_V2",
    12: "UNIVERSAL_TOKEN_SWAPPER",
    13: "COMPOUND_V3_USDT",
    14: "MORPHO",
    15: "SPARK",
    16: "CURVE_POOL",
    17: "CURVE_LP_GAUGE",
    18: "RAMSES_V2_POSITIONS",
    19: "MORPHO_FLASH_LOAN",
    20: "AAVE_V3_LIDO",
    21: "MOONWELL",
    22: "MORPHO_REWARDS",
    23: "PENDLE",
    24: "FLUID_REWARDS",
    25: "CURVE_GAUGE_ERC4626",
    26: "COMPOUND_V3_WETH",
    27: "HARVEST_HARD_WORK",
    28: "TAC_STAKING",
    29: "LIQUITY_V2",
    30: "AERODROME",
    31: "VELODROME_SUPERCHAIN",
    32: "VELODROME_SUPERCHAIN_SLIPSTREAM",
    33: "AERODROME_SLIPSTREAM",
    34: "STAKE_DAO_V2",
    35: "SILO_V2",
    36: "BALANCER",
    37: "YIELD_BASIS_LT",
    38: "ENSO",
    39: "EBISU",
    40: "ASYNC_ACTION",
    41: "MORPHO_LIQUIDITY_IN_MARKETS",
    42: "ODOS_SWAPPER",
    43: "VELORA_SWAPPER",
    45: "AAVE_V4",
    46: "NAPIER",
}

# ---------------------------------------------------------------------------
# Market type classification
# ---------------------------------------------------------------------------
MARKET_TYPES: dict[str, set[int]] = {
    "LENDING": {1, 2, 3, 5, 11, 13, 14, 15, 20, 21, 26, 29, 35, 45},
    "DEX_SWAP": {9, 10, 12, 42, 43, 38},
    "LP_POSITION": {8, 16, 18, 30, 31, 32, 33, 36},
    "STAKING": {4, 6, 17, 25, 28, 34},
    "YIELD": {23, 37, 46},
    "FLASH_LOAN": {19},
    "SPECIAL": {7, 22, 24, 27, 39, 40, 41},
}

# Reverse lookup: market_id → type name
MARKET_TYPE_BY_ID: dict[int, str] = {
    mid: tname for tname, mids in MARKET_TYPES.items() for mid in mids
}

# Staking → origin market mapping (staking market depends on this origin market)
STAKING_ORIGIN: dict[int, int] = {
    4: 3,    # GEARBOX_FARM_DTOKEN_V3 → GEARBOX_POOL_V3
    6: 5,    # FLUID_INSTADAPP_STAKING → FLUID_INSTADAPP_POOL
    17: 16,  # CURVE_LP_GAUGE → CURVE_POOL
    25: 16,  # CURVE_GAUGE_ERC4626 → CURVE_POOL
}

# ERC4626 vault markets range
ERC4626_VAULT_MARKET_START = 100_001
ERC4626_VAULT_MARKET_END = 100_020

# Meta Morpho markets range
META_MORPHO_MARKET_START = 200_001
META_MORPHO_MARKET_END = 200_010

# Special markets
EXCHANGE_RATE_VALIDATOR = 2**256 - 3
ASSETS_BALANCE_VALIDATION = 2**256 - 2
ZERO_BALANCE_MARKET = 2**256 - 1

# ---------------------------------------------------------------------------
# Fee constants (from PlasmaVaultLib.sol)
# ---------------------------------------------------------------------------
PERFORMANCE_MAX_FEE_BPS = 5000  # 50%
MANAGEMENT_MAX_FEE_BPS = 500    # 5%
DECIMALS_OFFSET = 2

# ---------------------------------------------------------------------------
# Chain configurations
# ---------------------------------------------------------------------------
CHAINS = {
    "eth-mainnet": {
        "chain_id": 1,
        "alchemy_network": "eth-mainnet",
        "etherscan_url": "https://api.etherscan.io/api",
        "explorer_url": "https://etherscan.io",
    },
    "arb-mainnet": {
        "chain_id": 42161,
        "alchemy_network": "arb-mainnet",
        "etherscan_url": "https://api.arbiscan.io/api",
        "explorer_url": "https://arbiscan.io",
    },
    "base-mainnet": {
        "chain_id": 8453,
        "alchemy_network": "base-mainnet",
        "etherscan_url": "https://api.basescan.org/api",
        "explorer_url": "https://basescan.org",
    },
    "opt-mainnet": {
        "chain_id": 10,
        "alchemy_network": "opt-mainnet",
        "etherscan_url": "https://api-optimistic.etherscan.io/api",
        "explorer_url": "https://optimistic.etherscan.io",
    },
    "plasma-mainnet": {
        "chain_id": 9745,
        "alchemy_network": "plasma-mainnet",
        "etherscan_url": "https://plasmascan.to/api",
        "explorer_url": "https://plasmascan.to",
    },
}

# ---------------------------------------------------------------------------
# Well-known function selectors for access control checks
# ---------------------------------------------------------------------------
# Computed via keccak256 of canonical ABI signatures from PlasmaVaultGovernance.sol
# Struct params use tuple form: InstantWithdrawalFusesParamsStruct → (address,bytes32[])
GOVERNANCE_SELECTORS = {
    "addFuses(address[])": "0x3e3a86e0",
    "removeFuses(address[])": "0x30b75244",
    "addBalanceFuse(uint256,address)": "0x0c63abc6",
    "removeBalanceFuse(uint256,address)": "0x48e37c55",
    "grantMarketSubstrates(uint256,bytes32[])": "0xd1dffb88",
    "updateDependencyBalanceGraphs(uint256[],uint256[][])": "0x1ce56e7e",
    "configureInstantWithdrawalFuses((address,bytes32[])[])": "0xf2d888df",
    "setPriceOracleMiddleware(address)": "0x38923d00",
    "setRewardsClaimManagerAddress(address)": "0xcc53727b",
    "setTotalSupplyCap(uint256)": "0x31d05b11",
    "configurePerformanceFee(address,uint256)": "0x09f75ba0",
    "configureManagementFee(address,uint256)": "0xafb83531",
    "setupMarketsLimits((uint256,uint256)[])": "0x27d9e8b2",
    "activateMarketsLimits()": "0xf1a93fdc",
    "deactivateMarketsLimits()": "0xe52e29e7",
    "convertToPublicVault()": "0x926e07e5",
    "enableTransferShares()": "0xd6b4f680",
    "setPreHookImplementations(bytes4[],address[],bytes32[][])": "0x7f676d15",
    "updateCallbackHandler(address,address,bytes4)": "0x9879f043",
    "setMinimalExecutionDelaysForRoles(uint64[],uint256[])": "0x67d92011",
}

# Expected role assignments from IporFusionAccessManagerInitializerLibV1.sol
EXPECTED_FUNCTION_ROLES = {
    "addFuses(address[])": [300],                                          # FUSE_MANAGER
    "removeFuses(address[])": [300],                                       # FUSE_MANAGER
    "addBalanceFuse(uint256,address)": [300],                              # FUSE_MANAGER
    "removeBalanceFuse(uint256,address)": [300],                           # FUSE_MANAGER
    "grantMarketSubstrates(uint256,bytes32[])": [300],                     # FUSE_MANAGER
    "updateDependencyBalanceGraphs(uint256[],uint256[][])": [300],         # FUSE_MANAGER
    "updateCallbackHandler(address,address,bytes4)": [300],                # FUSE_MANAGER
    "configureInstantWithdrawalFuses((address,bytes32[])[])": [900],       # CONFIG_INSTANT_WITHDRAWAL_FUSES
    "setPriceOracleMiddleware(address)": [100],                            # ATOMIST
    "setRewardsClaimManagerAddress(address)": [601],                       # TECH_REWARDS_CLAIM_MANAGER
    "setTotalSupplyCap(uint256)": [100],                                   # ATOMIST
    "configurePerformanceFee(address,uint256)": [400],                     # TECH_PERFORMANCE_FEE_MANAGER
    "configureManagementFee(address,uint256)": [500],                      # TECH_MANAGEMENT_FEE_MANAGER
    "setupMarketsLimits((uint256,uint256)[])": [100],                      # ATOMIST
    "activateMarketsLimits()": [100],                                      # ATOMIST
    "deactivateMarketsLimits()": [100],                                    # ATOMIST
    "setPreHookImplementations(bytes4[],address[],bytes32[][])": [301],    # PRE_HOOKS_MANAGER
    "setMinimalExecutionDelaysForRoles(uint64[],uint256[])": [1],          # OWNER
}

# Zero address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# USD quote currency address used by PriceOracleMiddleware
USD_QUOTE_CURRENCY = "0x0000000000000000000000000000000000000348"

# REDEMPTION_DELAY_IN_SECONDS max (7 days)
MAX_REDEMPTION_DELAY = 7 * 24 * 3600

# ---------------------------------------------------------------------------
# Wrapped-asset equivalences (Ethereum mainnet)
# Maps underlying token → set of accepted wrapper addresses.
# Used by LM-05 to accept wstETH substrates when vault underlying is stETH, etc.
# ---------------------------------------------------------------------------
WRAPPED_ASSET_EQUIVALENTS = {
    # stETH → wstETH, WETH (AAVE accepts wstETH for stETH vaults)
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": {
        "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",  # wstETH
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    },
    # WETH → wstETH, stETH
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
        "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",  # wstETH
        "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # stETH
    },
}
