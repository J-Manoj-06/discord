"""
Leave Command: Removes players from the current guild waiting game session.
"""

import logging

from discord.ext import commands

from services.game_service import GameService

logger = logging.getLogger(__name__)


class LeaveCog(commands.Cog):
    """Leave game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="leave")
    async def leave_game(self, ctx: commands.Context):
        """Leave the current waiting Mafia game session."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            success, message = self.game_service.remove_player(ctx.guild.id, ctx.author.id)

            if not success:
                await ctx.send(f"❌ {message}")
                return

            await ctx.send(f"{ctx.author.mention} left the game")
        except Exception as exc:
            logger.error("Error in leave command: %s", exc)
            await ctx.send("❌ Failed to leave game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService):
    """Load leave cog into bot."""
    await bot.add_cog(LeaveCog(bot, game_service))
