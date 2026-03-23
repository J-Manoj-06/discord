"""Mafia Profile Service: Handle player profiles and game statistics."""

from typing import Dict, List, Optional

from database.repositories.mafia_game_stats_repository import MafiaGameStatsRepository


class MafiaProfileService:
    """Service layer for Mafia game profiles and statistics."""

    def __init__(self, stats_repository: MafiaGameStatsRepository):
        """Initialize profile service.
        
        Args:
            stats_repository: MafiaGameStatsRepository instance
        """
        self.stats_repo = stats_repository

    async def initialize(self):
        """Initialize service (ensure indexes)."""
        await self.stats_repo.initialize()

    async def get_player_stats(self, user_id: int) -> Dict:
        """Get player game statistics.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Stats dict with games_played, wins, losses, last_role
        """
        stats = await self.stats_repo.get_or_create_stats(user_id)
        return stats

    async def calculate_win_rate(self, user_id: int) -> float:
        """Calculate player's win rate percentage.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Win rate as percentage (0-100), or 0 if no games played
        """
        stats = await self.stats_repo.get_stats(user_id)
        if stats is None or stats.get("games_played", 0) == 0:
            return 0.0

        games = stats.get("games_played", 1)
        wins = stats.get("wins", 0)
        return (wins / games) * 100

    async def record_game_end(
        self,
        village_player_ids: List[int],
        mafia_player_ids: List[int],
        winner: str,
        roles: Dict[int, str],
    ):
        """Record game end and update all player stats.
        
        Args:
            village_player_ids: List of villager player IDs (not including godfather)
            mafia_player_ids: List of mafia player IDs (godfather)
            winner: "villagers" or "mafia"
            roles: Dict mapping player_id to role name
        """
        # Determine winners and losers
        if winner == "villagers":
            winners = village_player_ids
            losers = mafia_player_ids
        else:  # "mafia"
            winners = mafia_player_ids
            losers = village_player_ids

        # Ensure all players have stats created
        all_players = set(list(village_player_ids) + list(mafia_player_ids))
        for player_id in all_players:
            await self.stats_repo.get_or_create_stats(player_id)

        # Update winners
        for player_id in winners:
            await self.stats_repo.increment_win(player_id)
            role = roles.get(player_id)
            if role:
                await self.stats_repo.update_last_role(player_id, role)

        # Update losers
        for player_id in losers:
            await self.stats_repo.increment_loss(player_id)
            role = roles.get(player_id)
            if role:
                await self.stats_repo.update_last_role(player_id, role)

    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by wins.
        
        Args:
            limit: Number of top players to return
            
        Returns:
            List of player stats dicts sorted by wins
        """
        leaderboard = await self.stats_repo.collection.find(
            {"games_played": {"$gte": 1}}
        ).sort("wins", -1).limit(limit).to_list(length=limit)

        return leaderboard

    async def get_player_with_win_rate(self, user_id: int) -> Dict:
        """Get player stats with calculated win rate.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Stats dict with added win_rate field
        """
        stats = await self.stats_repo.get_or_create_stats(user_id)
        win_rate = await self.calculate_win_rate(user_id)

        stats["win_rate"] = win_rate
        return stats
