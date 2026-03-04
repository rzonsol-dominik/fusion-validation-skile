from .phase1_vault_id import Phase1VaultIdentity
from .phase2_access import Phase2AccessControl
from .phase3_markets import Phase3Markets
from .phase4_interactions import Phase4Interactions
from .phase5_withdrawal import Phase5Withdrawal
from .phase6_fees import Phase6Fees
from .phase7_oracle import Phase7Oracle
from .phase8_balance import Phase8Balance
from .phase9_rewards import Phase9Rewards
from .phase10_hooks import Phase10Hooks
from .phase11_market_checklist import Phase11MarketChecklist

ALL_VALIDATORS = [
    Phase1VaultIdentity,
    Phase2AccessControl,
    Phase3Markets,
    Phase4Interactions,
    Phase5Withdrawal,
    Phase6Fees,
    Phase7Oracle,
    Phase8Balance,
    Phase9Rewards,
    Phase10Hooks,
    Phase11MarketChecklist,
]
