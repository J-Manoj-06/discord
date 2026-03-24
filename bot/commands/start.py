"""
Start Command: Starts the Mafia game with party players.
"""

import logging

from discord.ext import commands

from services.game_service import GameService
from services.party_service import PartyService

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    """Start game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService, party_service: PartyService):
        self.bot = bot
        self.game_service = game_service
        self.party_service = party_service

    @commands.command(name="start")
    async def start_game(self, ctx: commands.Context):
        """Start the Mafia game with players from the party."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Get party players
            party_players = self.party_service.get_party_players(ctx.guild.id)
            
            # Check minimum players
            if len(party_players) < 4:
                await ctx.send("❌ At least 4 players are required to start the game.")
                return

            # Get or create game session
            session = self.game_service.get_session(ctx.guild.id)
            
            # Load party players into game session
            session["players"] = list(party_players)
            
            # Mark party as game active
            self.party_service.set_game_active(ctx.guild.id, True)

            # Start the game flow
            success, message = await self.game_service.start_game_flow(ctx)
            
            if not success:
                # Revert game_active if start failed
                self.party_service.set_game_active(ctx.guild.id, False)
                await ctx.send(f"❌ {message}")
                return

            # When the game loop task ends (normal finish or cancellation),
            # mark the party as not active so party commands work again.
            task = self.game_service.game_tasks.get(ctx.guild.id)
            if task is not None:
                guild_id = ctx.guild.id
                task.add_done_callback(
                    lambda _task, gid=guild_id: self.party_service.set_game_active(gid, False)
                )

            await ctx.send(f"🎮 {message}")
        except Exception as exc:
            logger.error("Error in start command: %s", exc)
            self.party_service.set_game_active(ctx.guild.id, False)
            await ctx.send("❌ Failed to start game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService, party_service: PartyService):
    """Load start cog into bot."""
    await bot.add_cog(StartCog(bot, game_service, party_service))
