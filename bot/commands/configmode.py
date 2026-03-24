"""Config mode command: set game mode per guild."""

import discord
from discord.ext import commands

from services.config_service import ConfigService
from services.game_service import GameService


class ConfigModeCog(commands.Cog):
    """Admin command to update game mode."""

    def __init__(self, bot: commands.Bot, config_service: ConfigService, game_service: GameService):
        self.bot = bot
        self.config_service = config_service
        self.game_service = game_service

    @commands.command(name="configmode")
    @commands.has_permissions(manage_guild=True)
    async def config_mode(self, ctx: commands.Context, mode: str):
        """Set game mode: classic | advanced | chaos."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        normalized = mode.lower().strip()
        if not self.config_service.is_valid_mode(normalized):
            await ctx.send("❌ Invalid mode. Use: classic, advanced, or chaos.")
            return

        # Persist guild config.
        self.config_service.set_mode(ctx.guild.id, normalized)

        # Keep GameService session mode in sync for start flow.
        self.game_service.set_game_mode(ctx.guild.id, normalized)

        mode_title = self.config_service.get_mode_title(normalized)
        desc = self.config_service.get_mode_description(normalized)

        embed = discord.Embed(
            title="Game Mode Updated",
            description=f"**{mode_title}** -> {desc}",
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)
        await ctx.send(f"Game mode set to **{mode_title}**")


async def setup(bot: commands.Bot, config_service: ConfigService, game_service: GameService):
    """Load configmode cog into bot."""
    await bot.add_cog(ConfigModeCog(bot, config_service, game_service))
