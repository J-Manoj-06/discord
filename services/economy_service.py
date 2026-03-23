"""
Economy Service: Handles all coin/gem transactions, rewards, and balance updates.
Provides atomic MongoDB operations and transaction logging.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from database.repositories.wallet_repository import WalletRepository
from database.repositories.economy_log_repository import EconomyLogRepository
from models.wallet import Wallet

logger = logging.getLogger(__name__)


class EconomyService:
    """Service for managing user economy, coins, gems, and rewards."""

    def __init__(self, wallet_repo: WalletRepository, log_repo: EconomyLogRepository):
        self.wallet_repo = wallet_repo
        self.log_repo = log_repo

    async def get_wallet(self, user_id: int, guild_id: int) -> Wallet:
        """Get or create a user's wallet."""
        wallet = await self.wallet_repo.find_by_user_guild(user_id, guild_id)
        if not wallet:
            wallet = await self.wallet_repo.create(user_id, guild_id)
            logger.info(f"Created wallet for user {user_id} in guild {guild_id}")
        return wallet

    async def add_coins(
        self,
        user_id: int,
        guild_id: int,
        amount: int,
        reason: str = "manual",
    ) -> Tuple[bool, str]:
        """Add coins to a user's wallet. Returns (success, message)."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(user_id, guild_id)
        new_balance = wallet.coins + amount

        updated = await self.wallet_repo.update_coins(user_id, guild_id, new_balance)
        if updated:
            await self.log_repo.log_transaction(
                user_id, guild_id, "coin_add", amount, reason
            )
            logger.info(f"Added {amount} coins to user {user_id}")
            return True, f"Added {amount} coins (+{amount})"
        return False, "Failed to add coins"

    async def remove_coins(
        self,
        user_id: int,
        guild_id: int,
        amount: int,
        reason: str = "manual",
    ) -> Tuple[bool, str]:
        """Remove coins from a user's wallet. Returns (success, message)."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(user_id, guild_id)
        if wallet.coins < amount:
            return False, f"Insufficient coins. You have {wallet.coins}, need {amount}"

        new_balance = wallet.coins - amount
        updated = await self.wallet_repo.update_coins(user_id, guild_id, new_balance)
        if updated:
            await self.log_repo.log_transaction(
                user_id, guild_id, "coin_remove", amount, reason
            )
            logger.info(f"Removed {amount} coins from user {user_id}")
            return True, f"Removed {amount} coins (-{amount})"
        return False, "Failed to remove coins"

    async def add_gems(
        self,
        user_id: int,
        guild_id: int,
        amount: int,
        reason: str = "manual",
    ) -> Tuple[bool, str]:
        """Add gems to a user's wallet. Returns (success, message)."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(user_id, guild_id)
        new_balance = wallet.gems + amount

        updated = await self.wallet_repo.update_gems(user_id, guild_id, new_balance)
        if updated:
            await self.log_repo.log_transaction(
                user_id, guild_id, "gem_add", amount, reason
            )
            logger.info(f"Added {amount} gems to user {user_id}")
            return True, f"Added {amount} gems (+{amount})"
        return False, "Failed to add gems"

    async def remove_gems(
        self,
        user_id: int,
        guild_id: int,
        amount: int,
        reason: str = "manual",
    ) -> Tuple[bool, str]:
        """Remove gems from a user's wallet. Returns (success, message)."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(user_id, guild_id)
        if wallet.gems < amount:
            return False, f"Insufficient gems. You have {wallet.gems}, need {amount}"

        new_balance = wallet.gems - amount
        updated = await self.wallet_repo.update_gems(user_id, guild_id, new_balance)
        if updated:
            await self.log_repo.log_transaction(
                user_id, guild_id, "gem_remove", amount, reason
            )
            logger.info(f"Removed {amount} gems from user {user_id}")
            return True, f"Removed {amount} gems (-{amount})"
        return False, "Failed to remove gems"

    async def can_afford_coins(self, user_id: int, guild_id: int, amount: int) -> bool:
        """Check if user can afford an amount of coins."""
        wallet = await self.get_wallet(user_id, guild_id)
        return wallet.coins >= amount

    async def can_afford_gems(self, user_id: int, guild_id: int, amount: int) -> bool:
        """Check if user can afford an amount of gems."""
        wallet = await self.get_wallet(user_id, guild_id)
        return wallet.gems >= amount

    async def claim_daily_bonus(self, user_id: int, guild_id: int) -> Tuple[bool, str]:
        """Claim daily coin bonus. Returns (success, message)."""
        wallet = await self.get_wallet(user_id, guild_id)

        # Check cooldown
        if wallet.last_daily_claim:
            next_claim = wallet.last_daily_claim + timedelta(hours=24)
            if datetime.utcnow() < next_claim:
                hours_remaining = (next_claim - datetime.utcnow()).total_seconds() / 3600
                return False, f"Daily bonus available in {hours_remaining:.1f} hours"

        # Award coins
        daily_amount = 500
        success, msg = await self.add_coins(user_id, guild_id, daily_amount, "daily_bonus")

        if success:
            await self.wallet_repo.update_last_daily_claim(user_id, guild_id)
            logger.info(f"Daily bonus claimed by user {user_id}")
            return True, f"Claimed {daily_amount} coins! ✨"

        return False, msg

    async def add_game_rewards(
        self,
        user_id: int,
        guild_id: int,
        is_winner: bool,
        is_mafia: bool,
        participated: bool,
        votes_cast: int = 0,
    ) -> Tuple[bool, str]:
        """
        Award coins based on game outcome.
        Returns (success, message with breakdown).
        """
        total_reward = 0
        breakdown = []

        # Participation bonus
        if participated:
            participation_bonus = 50
            total_reward += participation_bonus
            breakdown.append(f"Participation: +{participation_bonus}")

        # Win bonus
        if is_winner:
            win_bonus = 150 if is_mafia else 100
            total_reward += win_bonus
            breakdown.append(f"Victory ({'Mafia' if is_mafia else 'Village'}): +{win_bonus}")

        # Voting bonus
        if votes_cast > 0:
            voting_bonus = votes_cast * 10
            total_reward += voting_bonus
            breakdown.append(f"Voting ({votes_cast} votes): +{voting_bonus}")

        if total_reward > 0:
            success, msg = await self.add_coins(
                user_id, guild_id, total_reward, "game_reward"
            )
            if success:
                breakdown_text = "\n".join([f"  • {b}" for b in breakdown])
                return (
                    True,
                    f"Game Reward: +{total_reward} coins\n{breakdown_text}",
                )
            return False, msg

        return True, "No reward earned"

    async def record_game_stat(
        self,
        user_id: int,
        guild_id: int,
        is_winner: bool,
    ) -> None:
        """Record game win/loss stats."""
        wallet = await self.get_wallet(user_id, guild_id)

        if is_winner:
            await self.wallet_repo.update_total_wins(
                user_id, guild_id, wallet.total_wins + 1
            )
        else:
            await self.wallet_repo.update_total_losses(
                user_id, guild_id, wallet.total_losses + 1
            )

        await self.wallet_repo.update_games_played(
            user_id, guild_id, wallet.games_played + 1
        )

    async def get_top_richest(self, guild_id: int, limit: int = 10) -> list:
        """Get richest users in guild."""
        return await self.wallet_repo.find_top_by_coins(guild_id, limit)

    async def get_top_winners(self, guild_id: int, limit: int = 10) -> list:
        """Get top winners in guild."""
        return await self.wallet_repo.find_top_by_wins(guild_id, limit)

    async def get_transaction_history(
        self, user_id: int, guild_id: int, limit: int = 10
    ) -> list:
        """Get recent transactions for a user."""
        return await self.log_repo.find_by_user_guild(user_id, guild_id, limit)
