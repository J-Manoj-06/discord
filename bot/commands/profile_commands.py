"""
Profile Commands: Display profile, rank, titles, themes.
"""
import logging

import discord
from discord.ext import commands

from services.profile_service import ProfileService
from services.economy_service import EconomyService
from utils.embed_builder import EmbedBuilder

logger = logging.getLogger(__name__)


class ProfileCog(commands.Cog):
    """Profile and progression commands."""

    def __init__(
        self,
        bot: commands.Bot,
        profile_service: ProfileService,
        economy_service: EconomyService,
    ):
        self.bot = bot
        self.profile = profile_service
        self.economy = economy_service

    @commands.command(name="profile")
    async def profile(self, ctx: commands.Context, user: discord.User = None):
        """Show a user's profile card."""
        target = user or ctx.author
        try:
            profile = await self.profile.get_profile(target.id, ctx.guild.id)
            wallet = await self.economy.get_wallet(target.id, ctx.guild.id)
            win_rate = await self.profile.get_win_rate(target.id, ctx.guild.id)

            embed = EmbedBuilder.create(
                title=f"Profile: {profile.display_name or target.name}",
                color=discord.Color.blurple(),
            )

            embed.set_thumbnail(url=target.avatar.url if target.avatar else None)

            # Stats section
            embed.add_field(
                name="📊 Stats",
                value=(
                    f"Level: **{profile.level}**\n"
                    f"XP: {profile.xp} / {(profile.level + 1) * 100}\n"
                    f"Games Played: **{wallet.games_played}**"
                ),
                inline=True,
            )

            embed.add_field(
                name="🏆 Record",
                value=(
                    f"Wins: **{wallet.total_wins}**\n"
                    f"Losses: **{wallet.total_losses}**\n"
                    f"Win Rate: **{win_rate:.1f}%**"
                ),
                inline=True,
            )

            # Economy section
            embed.add_field(
                name="💰 Economy",
                value=(
                    f"Coins: **{wallet.coins:,}**\n"
                    f"Gems: **{wallet.gems:,}**\n"
                    f"Votes Cast: **{wallet.votes_cast}**"
                ),
                inline=True,
            )

            # Equipped cosmetics
            cosmetics_text = (
                f"Title: {profile.equipped_title or 'None'}\n"
                f"Theme: {profile.equipped_theme or 'Classic'}\n"
                f"Favorite Role: {profile.favorite_role or 'None'}"
            )
            embed.add_field(name="🎨 Cosmetics", value=cosmetics_text, inline=True)

            embed.set_footer(text=f"Member since {profile.created_at.strftime('%b %d, %Y')}")

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context):
        """Show your current level and XP progress."""
        try:
            profile = await self.profile.get_profile(ctx.author.id, ctx.guild.id)
            current_xp, xp_needed = self.profile.get_xp_progress(
                profile.xp, profile.level
            )

            # Create progress bar
            bar_length = 20
            progress = int((current_xp / xp_needed) * bar_length)
            bar = "█" * progress + "░" * (bar_length - progress)

            embed = EmbedBuilder.create(
                title=f"Rank: Level {profile.level}",
                description=(
                    f"```\n{bar}\n```\n"
                    f"**{current_xp} / {xp_needed}** XP\n"
                    f"Progress: **{(current_xp / xp_needed) * 100:.1f}%**"
                ),
                color=discord.Color.purple(),
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in rank command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="titles")
    async def titles(self, ctx: commands.Context):
        """List owned titles."""
        try:
            profile = await self.profile.get_profile(ctx.author.id, ctx.guild.id)

            # Example titles (would need inventory integration for full system)
            titles_text = (
                "**Owned Titles:**\n"
                "🎖️ Rookie (default)\n"
                "📝 Detective Mind (purchased)\n\n"
                "Use `!equiptitle <name>` to set a title"
            )

            embed = EmbedBuilder.create(
                title="Titles",
                description=titles_text,
                color=discord.Color.gold(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in titles command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="equiptitle")
    async def equip_title(self, ctx: commands.Context, *, title: str):
        """Equip a title to your profile."""
        try:
            if not title:
                await ctx.send("Usage: `!equiptitle <title name>`")
                return

            success = await self.profile.set_equipped_title(
                ctx.author.id, ctx.guild.id, title
            )

            if success:
                embed = EmbedBuilder.create(
                    title="✨ Title Equipped",
                    description=f"Your title is now: **{title}**",
                    color=discord.Color.green(),
                )
            else:
                embed = EmbedBuilder.create(
                    title="❌ Error",
                    description="Could not equip title",
                    color=discord.Color.red(),
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in equiptitle command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="themes")
    async def themes(self, ctx: commands.Context):
        """List owned profile themes."""
        try:
            themes_text = (
                "**Owned Themes:**\n"
                "🎨 Classic (default)\n"
                "🌙 Midnight (purchased)\n\n"
                "Use `!equiptheme <name>` to set a theme"
            )

            embed = EmbedBuilder.create(
                title="Profile Themes",
                description=themes_text,
                color=discord.Color.blurple(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in themes command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="equiptheme")
    async def equip_theme(self, ctx: commands.Context, *, theme: str):
        """Equip a profile theme."""
        try:
            if not theme:
                await ctx.send("Usage: `!equiptheme <theme name>`")
                return

            success = await self.profile.set_equipped_theme(
                ctx.author.id, ctx.guild.id, theme
            )

            if success:
                embed = EmbedBuilder.create(
                    title="✨ Theme Applied",
                    description=f"Your profile theme is now: **{theme}**",
                    color=discord.Color.green(),
                )
            else:
                embed = EmbedBuilder.create(
                    title="❌ Error",
                    description="Could not equip theme",
                    color=discord.Color.red(),
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in equiptheme command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")


async def setup(
    bot: commands.Bot,
    profile_service: ProfileService,
    economy_service: EconomyService,
):
    """Load profile cog into bot."""
    await bot.add_cog(ProfileCog(bot, profile_service, economy_service))
