"""Players Command: Display all players currently alive in the game."""

import logging

import discord
from discord.ext import commands

from services.game_service import GameService

logger = logging.getLogger(__name__)


class PlayersCog(commands.Cog):
    """Players (alive) display command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="players")
    async def show_players(self, ctx: commands.Context):
        """Display all players currently alive in the game."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id
        session = self.game_service.get_session(guild_id)

        # Get alive players
        alive_players = session.get("alive_players", [])

        # Create embed
        embed = discord.Embed(
            title="👥 Alive Players",
            color=discord.Color.blue(),
        )

        if not alive_players:
            embed.description = "No game is currently active or no players are alive."
        else:
            # Fetch member objects to get proper names
            player_list = []
            for idx, user_id in enumerate(sorted(alive_players), 1):
                member = ctx.guild.get_member(user_id)
                if member:
                    player_list.append(f"{idx}. {member.mention}")
                else:
                    player_list.append(f"{idx}. <@{user_id}>")

            embed.description = "\n".join(player_list)

        embed.set_footer(text=f"Alive Count: {len(alive_players)}")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot, game_service: GameService):
    """Load players cog into bot."""
    await bot.add_cog(PlayersCog(bot, game_service))
