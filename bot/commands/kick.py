"""Kick Command: Remove a player from the party (admin only)."""

import logging

import discord
from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class KickCog(commands.Cog):
    """Kick player from party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="kick")
    @commands.has_permissions(manage_guild=True)
    async def kick_player(self, ctx: commands.Context):
        """Remove a player from the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Check if user is mentioned
        if not ctx.message.mentions:
            await ctx.send("❌ Please mention a user to kick.")
            return

        target_user = ctx.message.mentions[0]
        guild_id = ctx.guild.id

        # Prevent kicking during active game
        if self.party_service.is_game_active(guild_id):
            await ctx.send("❌ Cannot kick players while a game is active.")
            return

        # Check if in party
        if not self.party_service.is_player_in_party(guild_id, target_user.id):
            await ctx.send(f"❌ {target_user.mention} is not in the party.")
            return

        # Remove from party
        self.party_service.remove_player_from_party(guild_id, target_user.id)
        await ctx.send(f"✅ {target_user.mention} has been removed from the party.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load kick cog into bot."""
    await bot.add_cog(KickCog(bot, party_service))
