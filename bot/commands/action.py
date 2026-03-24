"""Action Command: utility command to display the single night-action button."""

import discord
from discord.ext import commands

from bot.ui.action_buttons import NightActionsView
from services.game_service import GameService


class ActionCog(commands.Cog):
    """Manual action panel command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="action")
    async def action(self, ctx: commands.Context):
        """Show the single night-action button during night phase."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        session = self.game_service.get_session(ctx.guild.id)
        if session.get("phase") != "night":
            await ctx.send("❌ Night phase is not active.")
            return

        await ctx.send(
            "🌙 Press the button to perform your role-based night action.",
            view=NightActionsView(self.game_service, ctx.guild, ctx.guild.id),
        )


async def setup(bot: commands.Bot, game_service: GameService):
    """Load action cog into bot."""
    await bot.add_cog(ActionCog(bot, game_service))
