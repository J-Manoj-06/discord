"""Single-button night action UI for Mafia game.

Shows exactly one button: "Perform Night Action".
When clicked, role rules decide target eligibility and action behavior.
"""

from typing import TYPE_CHECKING

import discord

from services.role_engine import RoleEngine
from .player_select import NightTargetView

if TYPE_CHECKING:
    from services.game_service import GameService


class NightActionButton(discord.ui.Button):
    """Single night-action button that adapts behavior by role."""

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
    ):
        super().__init__(
            label="Perform Night Action",
            emoji="🌙",
            style=discord.ButtonStyle.primary,
        )
        self.game_service = game_service
        self.guild = guild
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        """Handle the single action button interaction."""
        session = self.game_service.get_session(self.guild_id)

        # Validate phase
        if session["phase"] != "night":
            await interaction.response.send_message(
                "❌ Night phase is not active.",
                ephemeral=True,
            )
            return

        user_id = interaction.user.id

        # Validate user is alive
        if user_id not in session["alive_players"]:
            await interaction.response.send_message(
                "❌ Dead players cannot act.",
                ephemeral=True,
            )
            return

        user_role = session["roles"].get(user_id)
        if not RoleEngine.has_night_action(user_role):
            await interaction.response.send_message(
                "❌ You have no night action.",
                ephemeral=True,
            )
            return

        # Single-action rule: one action per actor per night.
        action_key = f"{user_id}:night_action"
        if action_key in session.get("night_actions", {}):
            await interaction.response.send_message(
                "❌ You already acted this night.",
                ephemeral=True,
            )
            return

        # Show target selection menu
        view = NightTargetView(
            self.game_service,
            self.guild,
            self.guild_id,
            user_id,
            user_role,
        )
        await interaction.response.send_message(
            "🎯 Select your target:",
            view=view,
            ephemeral=True,
        )


class NightActionsView(discord.ui.View):
    """Main night panel with a single role-driven action button."""

    def __init__(self, game_service: "GameService", guild: discord.Guild, guild_id: int):
        super().__init__(timeout=60)
        self.add_item(NightActionButton(game_service, guild, guild_id))
