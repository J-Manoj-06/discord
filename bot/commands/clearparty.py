"""Clear Party Command: Remove all players from the party (admin only)."""

import logging

import discord
from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class ClearPartyCog(commands.Cog):
    """Clear party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="clearparty")
    @commands.has_permissions(manage_guild=True)
    async def clear_party(self, ctx: commands.Context):
        """Clear all players from the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id

        # Prevent clearing during active game
        if self.party_service.is_game_active(guild_id):
            await ctx.send("❌ Cannot clear party while a game is active.")
            return

        # Clear the party
        count = self.party_service.clear_party(guild_id)
        await ctx.send(f"✅ Party cleared. ({count} players removed)")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load clearparty cog into bot."""
    await bot.add_cog(ClearPartyCog(bot, party_service))
