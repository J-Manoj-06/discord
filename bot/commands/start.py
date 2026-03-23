"""
Start Command: Starts a Mafia game, assigns roles, and sends role DMs.
"""

import logging

from discord.ext import commands

from services.game_service import GameService

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    """Start game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="start")
    async def start_game(self, ctx: commands.Context):
        """Start full Mafia game flow (thread, phases, actions, and voting)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            success, message = await self.game_service.start_game_flow(ctx)
            if not success:
                await ctx.send(f"❌ {message}")
                return

            await ctx.send(message)
        except Exception as exc:
            logger.error("Error in start command: %s", exc)
            await ctx.send("❌ Failed to start game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService):
    """Load start cog into bot."""
    await bot.add_cog(StartCog(bot, game_service))
