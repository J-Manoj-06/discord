"""Player selection UI for night actions.

Handles target selection with role-specific restrictions:
- Detective: Cannot investigate themselves
- Godfather: Cannot kill themselves
- Doctor: Cannot heal themselves more than once per night
"""

from typing import List, Optional, Dict

import discord


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
    """Select menu for choosing night action targets with filtering.
    
    Prevents self-targeting and applies role-specific restrictions:
    - Excludes the actor from available targets
    - Enforces detective cannot target self
    - Enforces godfather cannot target self
    - Enforces doctor cannot heal self (optional rule)
    """

    def __init__(
        self,
        game_service: "GameService",
        guild: discord.Guild,
        guild_id: int,
        actor_id: int,
        action_type: str,
        actor_role: str,
    ):
        self.game_service = game_service
        self.guild = guild
        self.guild_id = guild_id
        self.actor_id = actor_id
        self.action_type = action_type
        self.actor_role = actor_role

        session = self.game_service.get_session(guild_id)
        options: List[discord.SelectOption] = []

        # Get valid targets (exclude actor, only alive players)
        valid_targets = self._get_valid_targets(session)

        # Build dropdown options with proper player format
        for player_id in valid_targets:
            label = get_player_display_name(guild, player_id)
            options.append(discord.SelectOption(label=label, value=str(player_id)))

        if not options:
            options.append(discord.SelectOption(label="No valid targets", value="none", disabled=True))

        super().__init__(
            placeholder="Select a target...",
            min_values=1 if "no valid targets" not in str(options) else 0,
            max_values=1,
            options=options[:25],  # Discord limit
        )

    def _get_valid_targets(self, session: Dict) -> List[int]:
        """Get list of valid targets based on action type and actor.
        
        Args:
            session: Game session dict
            
        Returns:
            List of valid target player IDs
        """
        valid = []

        for player_id in session["alive_players"]:
            # Never target self
            if player_id == self.actor_id:
                continue

            # Role-specific restrictions
            role = session["roles"].get(player_id, "unknown")

            # Detective cannot investigate themselves (already excluded above)
            # Godfather cannot kill themselves (already excluded above)
            # Doctor: optional rule - cannot heal themselves more than once per night
            if self.action_type == "heal" and self.actor_role == "doctor":
                # Check if doctor already healed this round (optional safety)
                # Already prevented by "action already submitted" check in callback
                pass

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

        if self.action_type in session["night_actions"]:
            await interaction.response.send_message(
                "❌ You have already submitted this action.",
                ephemeral=True,
            )
            return

        target_id = int(self.values[0])

        # Verify target is still valid
        if target_id not in session["alive_players"]:
            await interaction.response.send_message(
                "❌ Target is no longer alive.",
                ephemeral=True,
            )
            return

        # Prevent self-targeting
        if target_id == self.actor_id:
            await interaction.response.send_message(
                "❌ You cannot target yourself.",
                ephemeral=True,
            )
            return

        # Store the action
        session["night_actions"][self.action_type] = target_id

        # Special handling for investigation (reveal role immediately)
        if self.action_type == "investigate":
            target_role = session["roles"].get(target_id, "unknown")
            target_name = get_player_display_name(self.guild, target_id)
            await interaction.response.send_message(
                f"🔍 Investigation Result:\n\n"
                f"{target_name} is **{target_role.title()}**.",
                ephemeral=True,
            )
            return

        # For kill/heal actions
        target_name = get_player_display_name(self.guild, target_id)
        action_text = "Kill" if self.action_type == "kill" else "Heal"
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
        action_type: str,
        actor_role: str,
    ):
        super().__init__(timeout=45)
        self.add_item(
            NightTargetSelect(
                game_service,
                guild,
                guild_id,
                actor_id,
                action_type,
                actor_role,
            )
        )
