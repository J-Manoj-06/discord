"""Voting buttons for Mafia game day phase.

Provides one vote button per alive player with proper formatting:
- Display Name (@username) format
- Prevents dead players from voting
- Prevents voting twice
- Validates target is still alive
"""

from typing import TYPE_CHECKING

import discord

from .player_select import get_player_display_name

if TYPE_CHECKING:
    from services.game_service import GameService


class VoteButton(discord.ui.Button):
    """Vote button for eliminating a single player during day phase.
    
    Args:
        game_service: GameService instance
        guild: Discord guild
        guild_id: Guild ID
        target_id: Player ID to vote for
        target_name: Formatted player name for label
    """

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
        target_id: int,
        target_name: str,
    ):
        super().__init__(
            label=target_name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"vote_{guild_id}_{target_id}",
        )
        self.game_service = game_service
        self.guild = guild
        self.guild_id = guild_id
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        """Handle vote submission.
        
        Validates:
        - Voting phase is active
        - Voter is alive
        - Voter hasn't already voted
        - Target is still alive
        """
        session = self.game_service.get_session(self.guild_id)

        # Validate voting phase
        if session["phase"] != "voting":
            await interaction.response.send_message(
                "❌ Voting phase is not active.",
                ephemeral=True,
            )
            return

        voter_id = interaction.user.id

        # Validate voter is alive
        if voter_id not in session["alive_players"]:
            await interaction.response.send_message(
                "❌ Dead players cannot vote.",
                ephemeral=True,
            )
            return

        # Prevent voting twice
        if voter_id in session["votes"]:
            await interaction.response.send_message(
                "❌ You have already voted.",
                ephemeral=True,
            )
            return

        # Validate target is still alive
        if self.target_id not in session["alive_players"]:
            await interaction.response.send_message(
                "❌ That player is no longer alive.",
                ephemeral=True,
            )
            return

        # Record vote
        session["votes"][voter_id] = self.target_id

        target_name = get_player_display_name(self.guild, self.target_id)
        await interaction.response.send_message(
            f"✅ Vote submitted for **{target_name}**.",
            ephemeral=True,
        )


class VotingView(discord.ui.View):
    """Voting panel with one button per alive player.
    
    Displays formatted player names (Display Name (@username))
    and creates vote buttons for all alive players.
    """

    def __init__(self, game_service: "GameService", guild: discord.Guild, guild_id: int):
        super().__init__(timeout=60)

        session = game_service.get_session(guild_id)

        # Create one vote button per alive player (limit 25 for Discord)
        for target_id in session["alive_players"][:25]:
            target_name = get_player_display_name(guild, target_id)
            self.add_item(
                VoteButton(
                    game_service,
                    guild,
                    guild_id,
                    target_id,
                    target_name,
                )
            )
