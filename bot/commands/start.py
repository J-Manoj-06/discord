"""
Start Command: Starts the Mafia game with party players.
"""

import logging

from discord.ext import commands

from services.config_service import ConfigService
from services.game_service import GameService
from services.party_service import PartyService

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    """Start game command handler."""

    def __init__(
        self,
        bot: commands.Bot,
        game_service: GameService,
        party_service: PartyService,
        config_service: ConfigService,
    ):
        self.bot = bot
        self.game_service = game_service
        self.party_service = party_service
        self.config_service = config_service

    @commands.command(name="start")
    async def start_game(self, ctx: commands.Context):
        """Start the Mafia game with players from the party."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Get party players
            party_players = self.party_service.get_party_players(ctx.guild.id)

            mode = self.config_service.get_mode(ctx.guild.id)
            min_players = self.config_service.get_min_players(mode)

            # Check minimum players based on configured mode.
            if len(party_players) < min_players:
                await ctx.send("❌ Not enough players for this mode.")
                return

            # Ensure game session uses the configured mode before assignment.
            self.game_service.set_game_mode(ctx.guild.id, mode)

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


async def setup(
    bot: commands.Bot,
    game_service: GameService,
    party_service: PartyService,
    config_service: ConfigService,
):
    """Load start cog into bot."""
    await bot.add_cog(StartCog(bot, game_service, party_service, config_service))
