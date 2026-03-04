"""Minimal inline ABI definitions for IPOR Fusion contracts.

Only view/pure functions needed for validation are included.
Each ABI is a list of dicts compatible with web3.py contract interface.
"""


def _view(name, inputs=None, outputs=None):
    """Helper to build a minimal ABI entry for a view function."""
    return {
        "type": "function",
        "name": name,
        "stateMutability": "view",
        "inputs": inputs or [],
        "outputs": outputs or [],
    }


def _uint(name=""):
    return {"name": name, "type": "uint256"}


def _addr(name=""):
    return {"name": name, "type": "address"}


def _bool(name=""):
    return {"name": name, "type": "bool"}


def _bytes32(name=""):
    return {"name": name, "type": "bytes32"}


def _bytes4(name=""):
    return {"name": name, "type": "bytes4"}


def _str(name=""):
    return {"name": name, "type": "string"}


def _uint8(name=""):
    return {"name": name, "type": "uint8"}


def _uint16(name=""):
    return {"name": name, "type": "uint16"}


def _uint32(name=""):
    return {"name": name, "type": "uint32"}


def _uint64(name=""):
    return {"name": name, "type": "uint64"}


def _uint48(name=""):
    return {"name": name, "type": "uint48"}


def _addr_arr(name=""):
    return {"name": name, "type": "address[]"}


def _bytes32_arr(name=""):
    return {"name": name, "type": "bytes32[]"}


def _uint_arr(name=""):
    return {"name": name, "type": "uint256[]"}


# ---------------------------------------------------------------------------
# PlasmaVault (ERC4626 + governance view functions)
# ---------------------------------------------------------------------------
PLASMA_VAULT_ABI = [
    # ERC4626 / ERC20
    _view("asset", outputs=[_addr("")]),
    _view("totalAssets", outputs=[_uint("")]),
    _view("totalSupply", outputs=[_uint("")]),
    _view("decimals", outputs=[_uint8("")]),
    _view("name", outputs=[_str("")]),
    _view("symbol", outputs=[_str("")]),
    _view("balanceOf", [_addr("account")], [_uint("")]),
    _view("maxDeposit", [_addr("")], [_uint("")]),
    _view("maxMint", [_addr("")], [_uint("")]),
    _view("maxWithdraw", [_addr("owner")], [_uint("")]),
    _view("previewDeposit", [_uint("assets")], [_uint("")]),
    _view("previewRedeem", [_uint("shares")], [_uint("")]),
    _view("convertToShares", [_uint("assets")], [_uint("")]),
    _view("convertToAssets", [_uint("shares")], [_uint("")]),

    # PlasmaVault-specific
    _view("totalAssetsInMarket", [_uint("marketId")], [_uint("")]),
    _view("getUnrealizedManagementFee", outputs=[_uint("")]),
    _view("PLASMA_VAULT_BASE", outputs=[_addr("")]),

    # Governance reads (IPlasmaVaultGovernance)
    _view("getAccessManagerAddress", outputs=[_addr("")]),
    _view("getPriceOracleMiddleware", outputs=[_addr("")]),
    _view("getRewardsClaimManagerAddress", outputs=[_addr("")]),
    _view("getFuses", outputs=[_addr_arr("")]),
    _view("isFuseSupported", [_addr("fuse")], [_bool("")]),
    _view("getMarketSubstrates", [_uint("marketId")], [_bytes32_arr("")]),
    _view("isMarketSubstrateGranted", [_uint("marketId"), _bytes32("substrate")], [_bool("")]),
    _view("isBalanceFuseSupported", [_uint("marketId"), _addr("fuse")], [_bool("")]),
    _view("getInstantWithdrawalFuses", outputs=[_addr_arr("")]),
    _view("getInstantWithdrawalFusesParams", [_addr("fuse"), _uint("index")], [_bytes32_arr("")]),
    _view("getPerformanceFeeData", outputs=[
        _addr("feeAccount"),
        _uint16("feeInPercentage"),
    ]),
    _view("getManagementFeeData", outputs=[
        _addr("feeAccount"),
        _uint16("feeInPercentage"),
        _uint32("lastUpdateTimestamp"),
    ]),
    _view("getTotalSupplyCap", outputs=[_uint("")]),
    _view("isMarketsLimitsActivated", outputs=[_bool("")]),
    _view("getMarketLimit", [_uint("marketId")], [_uint("")]),
    _view("getDependencyBalanceGraph", [_uint("marketId")], [_uint_arr("")]),

    # Pre-hooks (from CallbackHandler)
    _view("getPreHookConfig", [_addr("target"), _bytes4("selector")], [_addr("hook")]),
]

# ---------------------------------------------------------------------------
# ERC20 (minimal for underlying token)
# ---------------------------------------------------------------------------
ERC20_ABI = [
    _view("name", outputs=[_str("")]),
    _view("symbol", outputs=[_str("")]),
    _view("decimals", outputs=[_uint8("")]),
    _view("totalSupply", outputs=[_uint("")]),
    _view("balanceOf", [_addr("account")], [_uint("")]),
]

# ---------------------------------------------------------------------------
# IporFusionAccessManager (OpenZeppelin AccessManager + IPOR extensions)
# ---------------------------------------------------------------------------
ACCESS_MANAGER_ABI = [
    _view("REDEMPTION_DELAY_IN_SECONDS", outputs=[_uint("")]),
    _view("getMinimalExecutionDelayForRole", [_uint64("roleId")], [_uint("")]),
    _view("getAccountLockTime", [_addr("account")], [_uint("")]),
    _view("isConsumingScheduledOp", outputs=[_bytes4("")]),

    # OpenZeppelin AccessManager view functions
    _view("hasRole", [_uint64("roleId"), _addr("account")], [_bool("isMember"), _uint32("executionDelay")]),
    _view("canCall", [_addr("caller"), _addr("target"), _bytes4("selector")], [_bool("allowed"), _uint32("delay")]),
    _view("getRoleAdmin", [_uint64("roleId")], [_uint64("")]),
    _view("getRoleGuardian", [_uint64("roleId")], [_uint64("")]),
    _view("getTargetFunctionRole", [_addr("target"), _bytes4("selector")], [_uint64("")]),
    _view("getTargetAdminDelay", [_addr("target")], [_uint32("")]),
    _view("isTargetClosed", [_addr("target")], [_bool("")]),
    _view("getSchedule", [_bytes32("id")], [_uint48("")]),
    _view("getGrantDelay", [_uint64("roleId")], [_uint32("")]),
    _view("getRoleGrantDelay", [_uint64("roleId")], [_uint32("")]),

    # Events for role holder discovery
    {
        "type": "event",
        "name": "RoleGranted",
        "anonymous": False,
        "inputs": [
            {"name": "roleId", "type": "uint64", "indexed": True},
            {"name": "account", "type": "address", "indexed": True},
            {"name": "delay", "type": "uint32", "indexed": False},
            {"name": "since", "type": "uint48", "indexed": False},
            {"name": "newMember", "type": "bool", "indexed": False},
        ],
    },
    {
        "type": "event",
        "name": "RoleRevoked",
        "anonymous": False,
        "inputs": [
            {"name": "roleId", "type": "uint64", "indexed": True},
            {"name": "account", "type": "address", "indexed": True},
        ],
    },
]

# ---------------------------------------------------------------------------
# WithdrawManager
# ---------------------------------------------------------------------------
WITHDRAW_MANAGER_ABI = [
    _view("getLastReleaseFundsTimestamp", outputs=[_uint("")]),
    _view("getSharesToRelease", outputs=[_uint("")]),
    _view("getWithdrawWindow", outputs=[_uint("")]),
    _view("getWithdrawFee", outputs=[_uint("")]),
    _view("getRequestFee", outputs=[_uint("")]),
    _view("getPlasmaVaultAddress", outputs=[_addr("")]),
    _view("requestInfo", [_addr("account")], [
        _uint("shares"),
        _uint("endWithdrawWindowTimestamp"),
        _bool("canWithdraw"),
        _uint("withdrawWindowInSeconds"),
    ]),
]

# ---------------------------------------------------------------------------
# RewardsClaimManager
# ---------------------------------------------------------------------------
REWARDS_CLAIM_MANAGER_ABI = [
    _view("balanceOf", outputs=[_uint("")]),
    _view("isRewardFuseSupported", [_addr("fuse")], [_bool("")]),
    _view("getVestingData", outputs=[
        _uint32("vestingTime"),
        _uint32("updateBalanceTimestamp"),
        {"name": "transferredTokens", "type": "uint128"},
        {"name": "lastUpdateBalance", "type": "uint128"},
    ]),
    _view("getRewardsFuses", outputs=[_addr_arr("")]),
    _view("UNDERLYING_TOKEN", outputs=[_addr("")]),
    _view("PLASMA_VAULT", outputs=[_addr("")]),
]

# ---------------------------------------------------------------------------
# PriceOracleMiddleware
# ---------------------------------------------------------------------------
PRICE_ORACLE_ABI = [
    _view("getAssetPrice", [_addr("asset")], [_uint("assetPrice"), _uint("decimals")]),
    _view("getSourceOfAssetPrice", [_addr("asset")], [_addr("")]),
    _view("QUOTE_CURRENCY", outputs=[_addr("")]),
    _view("QUOTE_CURRENCY_DECIMALS", outputs=[_uint("")]),
]

# ---------------------------------------------------------------------------
# FeeManager (performance / management fee manager contracts)
# ---------------------------------------------------------------------------
FEE_MANAGER_ABI = [
    _view("getPlasmaVaultAddress", outputs=[_addr("")]),

    # Immutables
    _view("PLASMA_VAULT", outputs=[_addr("")]),
    _view("PERFORMANCE_FEE_ACCOUNT", outputs=[_addr("")]),
    _view("MANAGEMENT_FEE_ACCOUNT", outputs=[_addr("")]),
    _view("IPOR_DAO_MANAGEMENT_FEE", outputs=[_uint("")]),
    _view("IPOR_DAO_PERFORMANCE_FEE", outputs=[_uint("")]),

    # Fee queries
    _view("getDepositFee", outputs=[_uint("")]),
    _view("getTotalManagementFee", outputs=[_uint("")]),
    _view("getTotalPerformanceFee", outputs=[_uint("")]),
    _view("getIporDaoFeeRecipientAddress", outputs=[_addr("")]),
]

# ---------------------------------------------------------------------------
# EIP-1967 storage slots
# ---------------------------------------------------------------------------
# Implementation slot: bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1)
EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

# Admin slot: bytes32(uint256(keccak256('eip1967.proxy.admin')) - 1)
EIP1967_ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
