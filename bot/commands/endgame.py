"""Endgame Command: Force-end an active Mafia game (admin only)."""

import logging

from discord.ext import commands

from services.game_service import GameService
from services.party_service import PartyService

logger = logging.getLogger(__name__)


class EndGameCog(commands.Cog):
    """End game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService, party_service: PartyService):
        self.bot = bot
        self.game_service = game_service
        self.party_service = party_service

    @commands.command(name="endgame")
    @commands.has_permissions(manage_guild=True)
    async def end_game(self, ctx: commands.Context):
        """Force-end the current game, cleanup channel, and reset game session."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id

        # Safety check: only proceed when a real game is running.
        if not self.game_service.has_active_game(guild_id):
            await ctx.send("❌ No game is currently running.")
            return

        try:
            success, message = await self.game_service.end_game(ctx.guild)

            # Party should remain, but the active-game lock must be released.
            self.party_service.set_game_active(guild_id, False)

            if not success:
                await ctx.send(f"❌ {message}")
                return

            await ctx.send(f"✅ {message}")
        except Exception as exc:
            logger.error("Error in endgame command: %s", exc)
            # Fail-safe unlock for party commands even if cleanup partially fails.
            self.party_service.set_game_active(guild_id, False)
            await ctx.send("❌ Failed to end game cleanly. Please check logs.")


async def setup(bot: commands.Bot, game_service: GameService, party_service: PartyService):
    """Load endgame cog into bot."""
    await bot.add_cog(EndGameCog(bot, game_service, party_service))
