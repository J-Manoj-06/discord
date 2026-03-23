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
        """Start game if enough players joined and session is waiting."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            session = self.game_service.get_session(ctx.guild.id)

            if session["phase"] != "waiting":
                await ctx.send("❌ Game already started.")
                return

            if len(session["players"]) < self.game_service.MIN_PLAYERS:
                await ctx.send(
                    "❌ Not enough players to start. "
                    f"Need at least {self.game_service.MIN_PLAYERS}."
                )
                return

            success, message, roles = self.game_service.assign_roles(ctx.guild.id)
            if not success:
                await ctx.send(f"❌ {message}")
                return

            failed_user_ids = await self.game_service.send_roles_dm(ctx.guild, roles)

            await ctx.send("Game has started! Roles have been sent via DM 🌙")

            if failed_user_ids:
                failed_mentions = " ".join(f"<@{user_id}>" for user_id in failed_user_ids)
                await ctx.send(
                    "⚠️ Could not DM role to: "
                    f"{failed_mentions}. Please open your DMs and ask host to restart."
                )
        except Exception as exc:
            logger.error("Error in start command: %s", exc)
            await ctx.send("❌ Failed to start game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService):
    """Load start cog into bot."""
    await bot.add_cog(StartCog(bot, game_service))
