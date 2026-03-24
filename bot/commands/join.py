"""
Join Command: Adds players to the party lobby.
"""

import logging

from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class JoinCog(commands.Cog):
    """Join party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="join")
    async def join_party(self, ctx: commands.Context):
        """Join the Mafia party lobby."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Try to add player to party
            success = self.party_service.add_player_to_party(ctx.guild.id, ctx.author.id)

            if not success:
                await ctx.send(f"❌ You are already in the party.")
                return

            await ctx.send(f"🎉 {ctx.author.name} joined the party!")
        except Exception as exc:
            logger.error("Error in join command: %s", exc)
            await ctx.send("❌ Failed to join party. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load join cog into bot."""
    await bot.add_cog(JoinCog(bot, party_service))
