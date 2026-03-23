"""Night action buttons for Mafia game.

Provides role-specific action buttons:
- 🔪 Kill (Godfather only)
- 💉 Heal (Doctor only)
- 🔍 Investigate (Detective only)

Enforces:
- Phase restrictions (night phase only)
- Role restrictions (correct role only)
- Alive player restriction
- Action already submitted prevention
"""

from typing import TYPE_CHECKING

import discord

from .player_select import NightTargetView

if TYPE_CHECKING:
    from services.game_service import GameService


class NightActionButton(discord.ui.Button):
    """Role-specific button for initiating night actions.
    
    Args:
        game_service: GameService instance for session state
        guild: Discord guild
        guild_id: Guild ID
        action_type: "kill" | "heal" | "investigate"
        required_role: Role required to use this button
        label: Button label text
        emoji: Button emoji
    """

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
        action_type: str,
        required_role: str,
        label: str,
        emoji: str,
    ):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
        self.game_service = game_service
        self.guild = guild
        self.guild_id = guild_id
        self.action_type = action_type
        self.required_role = required_role

    async def callback(self, interaction: discord.Interaction):
        """Handle button click to show target selection menu.
        
        Validates:
        - Night phase is active
        - User has correct role
        - User is alive
        - User hasn't submitted this action yet
        """
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

        # Check user has correct role
        user_role = session["roles"].get(user_id)
        if user_role != self.required_role:
            await interaction.response.send_message(
                f"❌ Only {self.required_role.title()}s can use this action.",
                ephemeral=True,
            )
            return

        # Check action not already submitted
        if self.action_type in session["night_actions"]:
            await interaction.response.send_message(
                "❌ You have already submitted this action.",
                ephemeral=True,
            )
            return

        # Show target selection menu
        view = NightTargetView(
            self.game_service,
            self.guild,
            self.guild_id,
            user_id,
            self.action_type,
            user_role,
        )
        await interaction.response.send_message(
            f"🎯 Select a target for {self.action_type.title()}:",
            view=view,
            ephemeral=True,
        )


class NightActionsView(discord.ui.View):
    """Main night action button panel.
    
    Shows all available night actions:
    - Kill (Godfather)
    - Heal (Doctor)
    - Investigate (Detective)
    """

    def __init__(self, game_service: "GameService", guild: discord.Guild, guild_id: int):
        super().__init__(timeout=60)

        self.add_item(
            NightActionButton(
                game_service,
                guild,
                guild_id,
                "kill",
                "godfather",
                "Kill",
                "🔪",
            )
        )
        self.add_item(
            NightActionButton(
                game_service,
                guild,
                guild_id,
                "heal",
                "doctor",
                "Heal",
                "💉",
            )
        )
        self.add_item(
            NightActionButton(
                game_service,
                guild,
                guild_id,
                "investigate",
                "detective",
                "Investigate",
                "🔍",
            )
        )
