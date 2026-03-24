"""
Player Profile Command: Display player stats, games, wins, losses, and favorite role.
"""
import logging

import discord
from discord.ext import commands

from services.profile_service import ProfileService

logger = logging.getLogger(__name__)


class ProfileCog(commands.Cog):
    """Player profile command for viewing Mafia game statistics."""

    def __init__(self, bot: commands.Bot, profile_service: ProfileService):
        self.bot = bot
        self.profile_service = profile_service

    @commands.command(name="profile", aliases=["prof", "p"])
    async def profile(self, ctx: commands.Context, user: discord.User = None):
        """
        Display a player's Mafia profile and game statistics.
        
        Usage:
            !profile          - Show your profile
            !profile @user    - Show another player's profile
        
        Displays:
            - Games Played
            - Wins and Losses
            - Win Ratio (%)
            - Favorite Role (most played)
            - Join Date
        """
        target_user = user or ctx.author
        
        try:
            # Get player profile
            profile = await self.profile_service.get_profile(target_user.id, ctx.guild.id)
            
            # Calculate statistics
            games_played = profile.games_played
            wins = profile.wins
            losses = profile.losses
            
            # Calculate win ratio (avoid division by zero)
            win_ratio = (wins / games_played * 100) if games_played > 0 else 0.0
            
            # Get favorite role
            favorite_role = await self.profile_service.get_favorite_role(target_user.id, ctx.guild.id)
            favorite_role_display = favorite_role.title() if favorite_role else "None"
            
            # Format join date
            join_date_str = profile.created_at.strftime("%b %d, %Y") if profile.created_at else "Unknown"
            
            # Build embed
            embed = discord.Embed(
                title="🎭 Mafia Player Profile",
                description=f"Statistics for {target_user.name}",
                color=discord.Color.blurple(),
            )
            
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
            
            # Games and stats section
            embed.add_field(
                name="📊 Games",
                value=(
                    f"**Played:** {games_played}\n"
                    f"**Wins:** {wins}\n"
                    f"**Losses:** {losses}"
                ),
                inline=True,
            )
            
            # Win ratio section
            embed.add_field(
                name="📈 Statistics",
                value=(
                    f"**Win Ratio:** {win_ratio:.1f}%\n"
                    f"**Favorite Role:** {favorite_role_display}\n"
                    f"**Level:** {profile.level}"
                ),
                inline=True,
            )
            
            # Info section
            embed.add_field(
                name="ℹ️ Info",
                value=f"**Joined Bot:** {join_date_str}",
                inline=False,
            )
            
            # Show role breakdown if player has played games
            if games_played > 0 and profile.roles_played:
                roles_breakdown = "\n".join(
                    [f"{role.title()}: {count}" for role, count in sorted(profile.roles_played.items(), key=lambda x: x[1], reverse=True)]
                )
                embed.add_field(
                    name="🎮 Roles Played",
                    value=roles_breakdown,
                    inline=False,
                )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await ctx.send(f"❌ Error retrieving profile: {str(e)}")


async def setup(bot: commands.Bot, profile_service: ProfileService):
    """Load profile cog into bot."""
    await bot.add_cog(ProfileCog(bot, profile_service))
