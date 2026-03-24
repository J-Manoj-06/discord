"""Party Service: Manages party state, players, and game status across guilds.

Provides a clean separation between party management and game logic.
"""

from typing import Dict, Optional, Set


class PartyService:
    """Manage party lobbies per guild."""

    def __init__(self):
        """Initialize party storage."""
        self.parties: Dict[int, Dict] = {}

    def create_party(self, guild_id: int) -> None:
        """Create or reset party for a guild."""
        self.parties[guild_id] = {
            "players": set(),
            "game_active": False,
        }

    def _get_or_create_party(self, guild_id: int) -> Dict:
        """Get party or create if it doesn't exist."""
        if guild_id not in self.parties:
            self.create_party(guild_id)
        return self.parties[guild_id]

    def add_player_to_party(self, guild_id: int, user_id: int) -> bool:
        """Add a player to the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if added, False if already present
        """
        party = self._get_or_create_party(guild_id)
        if user_id in party["players"]:
            return False
        party["players"].add(user_id)
        return True

    def remove_player_from_party(self, guild_id: int, user_id: int) -> bool:
        """Remove a player from the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if removed, False if not in party
        """
        party = self._get_or_create_party(guild_id)
        if user_id not in party["players"]:
            return False
        party["players"].discard(user_id)
        return True

    def clear_party(self, guild_id: int) -> int:
        """Remove all players from the party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of players removed
        """
        party = self._get_or_create_party(guild_id)
        count = len(party["players"])
        party["players"].clear()
        return count

    def get_party_players(self, guild_id: int) -> Set[int]:
        """Get all players in the party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Set of user IDs in the party
        """
        party = self._get_or_create_party(guild_id)
        return party["players"].copy()

    def get_player_count(self, guild_id: int) -> int:
        """Get number of players in party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of players
        """
        party = self._get_or_create_party(guild_id)
        return len(party["players"])

    def is_player_in_party(self, guild_id: int, user_id: int) -> bool:
        """Check if a player is in the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if player is in party
        """
        party = self._get_or_create_party(guild_id)
        return user_id in party["players"]

    def set_game_active(self, guild_id: int, active: bool) -> None:
        """Set game active status.

        Args:
            guild_id: Discord guild ID
            active: Whether game is active
        """
        party = self._get_or_create_party(guild_id)
        party["game_active"] = active

    def is_game_active(self, guild_id: int) -> bool:
        """Check if game is active.

        Args:
            guild_id: Discord guild ID

        Returns:
            True if game is active
        """
        party = self._get_or_create_party(guild_id)
        return party["game_active"]
