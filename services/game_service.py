"""
Game Service: In-memory game session manager for Mafia matches.

Handles joining, role assignment, and role DM delivery.
"""

import asyncio
import random
from typing import Dict, List, Tuple

import discord


class GameService:
    """Service layer for game session state and role management."""

    REQUIRED_ROLES = ["detective", "godfather", "doctor", "villager"]
    MIN_PLAYERS = 4

    ROLE_DM_MESSAGES = {
        "godfather": "You are the Godfather 🕶️. Lead the mafia and eliminate others.",
        "doctor": "You are the Doctor 💉. You can save one player each night.",
        "detective": "You are the Detective 🔍. You can investigate players.",
        "villager": "You are a Villager 👤. Find and eliminate the mafia.",
    }

    def __init__(self):
        self.game_sessions: Dict[int, Dict] = {}

    def _get_or_create_session(self, guild_id: int) -> Dict:
        """Return session for guild, creating default waiting session if needed."""
        if guild_id not in self.game_sessions:
            self.game_sessions[guild_id] = {
                "players": [],
                "roles": {},
                "phase": "waiting",
            }
        return self.game_sessions[guild_id]

    def add_player(self, guild_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Add a user to the waiting game session.

        Returns:
            (success, message)
        """
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "waiting":
            return False, "Game already started. You cannot join right now."

        if user_id in session["players"]:
            return False, "You already joined this game."

        session["players"].append(user_id)
        return True, "joined"

    def get_session(self, guild_id: int) -> Dict:
        """Public session accessor used by command layer for status checks."""
        return self._get_or_create_session(guild_id)

    def assign_roles(self, guild_id: int) -> Tuple[bool, str, Dict[int, str]]:
        """
        Assign Mafia roles for a guild session.

        Assignment:
        - 1 godfather
        - 1 doctor
        - 1 detective
        - rest villagers
        """
        session = self._get_or_create_session(guild_id)
        players: List[int] = session["players"]

        if session["phase"] != "waiting":
            return False, "Game already started.", {}

        if len(players) < self.MIN_PLAYERS:
            return (
                False,
                f"Need at least {self.MIN_PLAYERS} players to start. Current: {len(players)}",
                {},
            )

        shuffled_players = players[:]
        random.shuffle(shuffled_players)

        roles: Dict[int, str] = {}
        roles[shuffled_players[0]] = "godfather"
        roles[shuffled_players[1]] = "doctor"
        roles[shuffled_players[2]] = "detective"

        for user_id in shuffled_players[3:]:
            roles[user_id] = "villager"

        session["roles"] = roles
        session["phase"] = "night"

        return True, "Roles assigned successfully.", roles

    async def send_roles_dm(
        self,
        guild: discord.Guild,
        roles: Dict[int, str],
    ) -> List[int]:
        """
        DM each player their assigned role.

        Returns:
            List of user IDs that failed to receive DM.
        """

        async def _dm_one(user_id: int, role_name: str) -> Tuple[int, bool]:
            member = guild.get_member(user_id)
            if member is None:
                return user_id, False

            dm_message = self.ROLE_DM_MESSAGES.get(
                role_name,
                "You have been assigned a role.",
            )

            try:
                await member.send(dm_message)
                return user_id, True
            except (discord.Forbidden, discord.HTTPException):
                return user_id, False

        tasks = [_dm_one(user_id, role) for user_id, role in roles.items()]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        failed_user_ids: List[int] = [user_id for user_id, ok in results if not ok]
        return failed_user_ids
