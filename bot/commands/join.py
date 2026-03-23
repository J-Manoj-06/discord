"""
Join Command: Adds players to the current guild game session.
"""

import logging

from discord.ext import commands

from services.game_service import GameService

logger = logging.getLogger(__name__)


class JoinCog(commands.Cog):
    """Join game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="join")
    async def join_game(self, ctx: commands.Context):
        """Join the current waiting Mafia game session."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            success, message = self.game_service.add_player(ctx.guild.id, ctx.author.id)

            if not success:
                await ctx.send(f"❌ {message}")
                return

            await ctx.send(f"{ctx.author.mention} joined the game")
        except Exception as exc:
            logger.error("Error in join command: %s", exc)
            await ctx.send("❌ Failed to join game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService):
    """Load join cog into bot."""
    await bot.add_cog(JoinCog(bot, game_service))
