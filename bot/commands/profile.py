"""Profile Command: Display player game statistics."""

import logging

import discord
from discord.ext import commands

from services.mafia_profile_service import MafiaProfileService

logger = logging.getLogger(__name__)


class MafiaProfileCog(commands.Cog):
    """Player profile command handler for Mafia game stats."""

    def __init__(self, bot: commands.Bot, profile_service: MafiaProfileService):
        self.bot = bot
        self.profile_service = profile_service

    @commands.command(name="mprofile")
    async def view_profile(self, ctx: commands.Context):
        """Display your Mafia game profile and statistics.
        
        Shows:
        - Games played
        - Wins and losses
        - Win rate percentage
        - Last role played
        """
        user_id = ctx.author.id
        user_name = ctx.author.display_name or ctx.author.name

        try:
            # Get player stats with win rate
            stats = await self.profile_service.get_player_with_win_rate(user_id)

            games_played = stats.get("games_played", 0)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            win_rate = stats.get("win_rate", 0.0)
            last_role = stats.get("last_role") or "None"

            # Build embed
            embed = discord.Embed(
                title="🎮 Mafia Game Profile",
                description=f"Statistics for {user_name}",
                color=discord.Color.blue(),
            )

            embed.add_field(name="📊 Games Played", value=str(games_played), inline=True)
            embed.add_field(name="🏆 Wins", value=str(wins), inline=True)
            embed.add_field(name="💀 Losses", value=str(losses), inline=True)
            embed.add_field(
                name="📈 Win Rate",
                value=f"{win_rate:.1f}%" if games_played > 0 else "N/A",
                inline=True,
            )
            embed.add_field(name="🎭 Last Role", value=str(last_role).title(), inline=True)

            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"User ID: {user_id}")

            await ctx.send(embed=embed)

        except Exception as exc:
            logger.error("Error in profile command: %s", exc)
            await ctx.send("❌ Failed to retrieve profile. Please try again.")


async def setup(bot: commands.Bot, profile_service: MafiaProfileService):
    """Load profile cog into bot."""
    await bot.add_cog(MafiaProfileCog(bot, profile_service))
