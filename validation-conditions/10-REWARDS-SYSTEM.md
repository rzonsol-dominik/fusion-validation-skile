# 10 - Rewards System Validation

## Purpose
Verify the rewards system: RewardsClaimManager, reward fuses, vesting, transfers.

---

## Rewards Architecture

```
Protocols (Aave, Morpho, Compound, etc.)
    │ claim rewards
    ▼
RewardsClaimManager
    │ linear vesting
    │ transferVestedTokensToVault()
    ▼
PlasmaVault (underlying token balance)
```

### Process:
1. **Claim**: Account with CLAIM_REWARDS_ROLE calls `claimRewards(FuseAction[])` on the vault
2. Vault delegatecall to reward fuses → fuse claims rewards from the protocol to RewardsClaimManager
3. **Vesting**: Rewards enter linear vesting (configurable duration)
4. **Transfer**: Vested tokens are transferred to the vault (updateBalance/transferVestedTokensToVault)
5. **Include in totalAssets**: Vested balance is included in vault.totalAssets()

---

## CRITICAL

### RW-001: RewardsClaimManager Address
- **Condition**: If vault claims rewards - RewardsClaimManager is configured
- **How to check**: `PlasmaVaultGovernance.getRewardsClaimManagerAddress()`
- **Expected result**: Valid address (not address(0)) if vault uses rewards
- **Notes**: Without the manager, rewards cannot be claimed and vested

### RW-002: RewardsClaimManager Underlying Token
- **Condition**: RewardsClaimManager has the same underlying token as the vault
- **How to check**: Check underlying token in RewardsClaimManager
- **Expected result**: Matches `vault.asset()`
- **Notes**: Wrong token = rewards transferred in the wrong token

### RW-003: RewardsClaimManager -> Vault Connection
- **Condition**: RewardsClaimManager is connected to the correct vault
- **How to check**: Check PLASMA_VAULT address in RewardsClaimManager
- **Expected result**: Address of the current vault
- **Notes**: Wrong connection = rewards go to the wrong vault

### RW-004: Reward Fuses Registered
- **Condition**: Reward fuses are registered in RewardsClaimManager
- **How to check**: `rewardsClaimManager.getRewardsFuses()`
- **Expected result**: List contains all required reward fuses
- **Notes**: Unregistered fuse = claimRewards() will revert

### RW-005: TECH_REWARDS_CLAIM_MANAGER_ROLE
- **Condition**: TECH_REWARDS_CLAIM_MANAGER_ROLE is assigned to RewardsClaimManager
- **How to check**: `AccessManager.hasRole(601, rewardsClaimManagerAddress)`
- **Expected result**: true
- **Notes**: Without this role the manager cannot operate

---

## HIGH

### RW-010: Vesting Time Configuration
- **Condition**: Vesting time is configured reasonably
- **How to check**: `rewardsClaimManager.getVestingData()`
- **Expected result**: vestingTime > 1 and reasonable (e.g., 7 days = 604800s, 30 days = 2592000s)
- **Notes**: Default after deployment = 1 second! Must be changed via `setupVestingTime()`. 0 = instant vesting; too long = rewards are frozen

### RW-011: CLAIM_REWARDS_ROLE Assignment
- **Condition**: CLAIM_REWARDS_ROLE is assigned to the expected account (bot/keeper)
- **How to check**: `AccessManager.hasRole(600, address)`
- **Expected result**: Expected claimer bot account
- **Notes**: Only this account can claim rewards

### RW-012: TRANSFER_REWARDS_ROLE Assignment
- **Condition**: TRANSFER_REWARDS_ROLE is assigned to the expected account
- **How to check**: `AccessManager.hasRole(700, address)`
- **Expected result**: Expected account
- **Notes**: Role for transferring non-underlying reward tokens

### RW-013: UPDATE_REWARDS_BALANCE_ROLE Assignment
- **Condition**: UPDATE_REWARDS_BALANCE_ROLE is assigned to the expected account
- **How to check**: `AccessManager.hasRole(1100, address)`
- **Expected result**: Expected account (keeper/bot)
- **Notes**: Needed for updating the rewards balance in totalAssets

### RW-014: Reward Fuse Protocol Match
- **Condition**: Reward fuses correspond to the protocols used by the vault
- **How to check**: Compare reward fuses with active markets according to the table:

| Market / Protocol | Required Reward Claim Fuse |
|-------------------|---------------------------|
| Aave V3/V3 Lido | (Aave rewards via Merkl or dedicated) |
| Compound V3 | CompoundV3ClaimFuse |
| Morpho | MorphoClaimFuse |
| Curve gauge | CurveGaugeTokenClaimFuse |
| Aerodrome | AerodromeGaugeClaimFuse |
| Aerodrome Slipstream | AreodromeSlipstreamGaugeClaimFuse |
| Euler V2 | RewardEulerTokenClaimFuse |
| Fluid Instadapp | FluidInstadappClaimFuse or FluidProofClaimFuse |
| Gearbox V3 | GearboxV3FarmDTokenClaimFuse |
| Merkl (universal) | MerklClaimFuse |
| Moonwell | MoonwellClaimFuse |
| Ramses | RamsesClaimFuse |
| Stake DAO V2 | StakeDaoV2ClaimFuse |
| Syrup | SyrupClaimFuse |
| Velodrome Superchain | VelodromeSuperchainGaugeClaimFuse |
| Velodrome Slipstream | VelodromeSuperchainSlipstreamGaugeClaimFuse |

- **Expected result**: Each market with rewards has a corresponding claim fuse
- **Notes**: Missing claim fuse = rewards are not claimed (loss of value). 16 types of reward fuses in the codebase total

### RW-015: Vesting Balance Correctness
- **Condition**: balanceOf() in RewardsClaimManager correctly reflects vested tokens
- **How to check**: `rewardsClaimManager.balanceOf()`
- **Expected result**: Value >= 0 and <= total claimed rewards
- **Notes**: Check formula: `(lastUpdateBalance * elapsed / vestingTime) - transferred`

---

## MEDIUM

### RW-020: Reward Token Handling (non-underlying)
- **Condition**: Rewards in tokens != underlying (e.g., COMP, AAVE, CRV) are properly handled
- **How to check**: Check if there is a mechanism to convert reward tokens to underlying
- **Expected result**: Swap fuse or manual process for conversion
- **Notes**: Rewards in non-underlying tokens must be converted

### RW-021: Reward Claim Frequency
- **Condition**: Rewards are claimed with reasonable frequency
- **How to check**: Check claimRewards events in production
- **Expected result**: Regular claiming (e.g., daily/weekly)
- **Notes**: Infrequent claiming = loss of compounding effect

### RW-022: Merkle Proof Claims (Morpho, etc.)
- **Condition**: For protocols with merkle proof claims - proofs are current
- **How to check**: Verify that claimRewards() with current proofs works
- **Expected result**: Claim doesn't revert
- **Notes**: Old merkle proofs may be outdated
