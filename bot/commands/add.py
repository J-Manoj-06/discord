"""Add Command: Manually add a player to the party (admin only)."""

import logging

import discord
from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class AddCog(commands.Cog):
    """Manual add player command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add_player(self, ctx: commands.Context):
        """Manually add a player to the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Check if user is mentioned
        if not ctx.message.mentions:
            await ctx.send("❌ Please mention a user to add.")
            return

        target_user = ctx.message.mentions[0]
        guild_id = ctx.guild.id

        # Check if already in party
        if self.party_service.is_player_in_party(guild_id, target_user.id):
            await ctx.send(f"❌ {target_user.mention} is already in the party.")
            return

        # Add to party
        self.party_service.add_player_to_party(guild_id, target_user.id)
        await ctx.send(f"✅ {target_user.mention} has been added to the party.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load add cog into bot."""
    await bot.add_cog(AddCog(bot, party_service))
