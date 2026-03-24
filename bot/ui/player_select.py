"""Player selection dropdown for the single night-action button flow."""

from typing import TYPE_CHECKING, Dict, List

import discord

from services.night_actions import NightActionService
from services.role_engine import RoleEngine

if TYPE_CHECKING:
    from services.game_service import GameService


def get_player_display_name(guild: discord.Guild, player_id: int) -> str:
    """
    Format player display as: Display Name (@username)
    
    Args:
        guild: Discord guild
        player_id: User ID to format
        
    Returns:
        Formatted string like "John (@john123)"
    """
    member = guild.get_member(player_id)
    if not member:
        return f"Player {player_id}"
    
    display_name = member.display_name or member.name
    username = member.name
    return f"{display_name} (@{username})"


class NightTargetSelect(discord.ui.Select):
    """Select menu for choosing one valid alive target."""

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
        actor_id: int,
        actor_role: str,
    ):
        self.game_service = game_service
        self.guild = guild
        self.guild_id = guild_id
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.night_action_service = NightActionService(game_service)

        session = self.game_service.get_session(guild_id)
        options: List[discord.SelectOption] = []

        # Get valid targets (alive players, role-aware self-target rule)
        valid_targets = self._get_valid_targets(session)

        # Build dropdown options with proper player format
        for player_id in valid_targets:
            label = get_player_display_name(guild, player_id)
            options.append(discord.SelectOption(label=label, value=str(player_id)))

        has_targets = bool(options)
        if not options:
            options.append(discord.SelectOption(label="No valid targets", value="none", disabled=True))

        super().__init__(
            placeholder="Select a target...",
            min_values=1 if has_targets else 0,
            max_values=1,
            options=options[:25],  # Discord limit
        )

    def _get_valid_targets(self, session: Dict) -> List[int]:
        """Get alive targets and apply role-specific self-target restrictions."""
        valid = []
        bread_players = session.get("bread_players", set())

        for player_id in session["alive_players"]:
            # Exclude self when role rule forbids it.
            if player_id == self.actor_id and not RoleEngine.can_target_self(self.actor_role):
                continue

            # Baker can only give bread once per player.
            if self.actor_role == "baker" and player_id in bread_players:
                continue

            valid.append(player_id)

        return valid

    async def callback(self, interaction: discord.Interaction):
        """Handle target selection.
        
        Validates:
        - Phase is still night
        - User is the action actor
        - User is alive
        - Action hasn't been submitted yet
        - Target is valid
        """
        session = self.game_service.get_session(self.guild_id)

        # Safety checks
        if session["phase"] != "night":
            await interaction.response.send_message(
                "❌ Night phase has ended.",
                ephemeral=True,
            )
            return

        if interaction.user.id != self.actor_id:
            await interaction.response.send_message(
                "❌ This action menu is not for you.",
                ephemeral=True,
            )
            return

        if interaction.user.id not in session["alive_players"]:
            await interaction.response.send_message(
                "❌ Dead players cannot act.",
                ephemeral=True,
            )
            return

        action_key = f"{self.actor_id}:night_action"
        if action_key in session.get("night_actions", {}):
            await interaction.response.send_message(
                "❌ You already acted this night.",
                ephemeral=True,
            )
            return

        if not self.values or self.values[0] == "none":
            await interaction.response.send_message(
                "❌ No valid targets are available for your role right now.",
                ephemeral=True,
            )
            return

        target_id = int(self.values[0])

        ok, message = await self.night_action_service.handle_night_action(
            guild_id=self.guild_id,
            user_id=self.actor_id,
            role=self.actor_role,
            target_id=target_id,
        )
        if not ok:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
            return

        action_type = RoleEngine.get_action_type(self.actor_role)
        target_name = get_player_display_name(self.guild, target_id)
        if self.actor_role == "baker":
            embed = discord.Embed(
                title="Bread delivered 🍞",
                description=f"Target: **{target_name}**",
                color=discord.Color.gold(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action_type == "kill":
            action_text = "Kill"
        elif action_type == "heal":
            action_text = "Protect"
        else:
            action_text = "Investigate"
        await interaction.response.send_message(
            f"✅ {action_text} action submitted.\n\n"
            f"Target: {target_name}",
            ephemeral=True,
        )


class NightTargetView(discord.ui.View):
    """Container view for night target selection dropdown."""

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
        actor_id: int,
        actor_role: str,
    ):
        super().__init__(timeout=45)
        self.add_item(
            NightTargetSelect(
                game_service,
                guild,
                guild_id,
                actor_id,
                actor_role,
            )
        )
