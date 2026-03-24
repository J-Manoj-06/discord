"""Mode command: show current game mode for this guild."""

from discord.ext import commands

from services.config_service import ConfigService


class ModeCog(commands.Cog):
    """Read-only command to display active game mode."""

    def __init__(self, bot: commands.Bot, config_service: ConfigService):
        self.bot = bot
        self.config_service = config_service

    @commands.command(name="mode")
    async def mode(self, ctx: commands.Context):
        """Show current game mode."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        current_mode = self.config_service.get_mode(ctx.guild.id)
        await ctx.send(f"Current Game Mode: {current_mode.capitalize()}")


async def setup(bot: commands.Bot, config_service: ConfigService):
    """Load mode cog into bot."""
    await bot.add_cog(ModeCog(bot, config_service))
