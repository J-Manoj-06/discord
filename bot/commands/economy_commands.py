"""
Economy Commands: Wallet, balance, daily bonus, leaderboard.
"""
import logging

import discord
from discord.ext import commands

from services.economy_service import EconomyService
from utils.embed_builder import EmbedBuilder
from utils.cooldowns import CooldownManager

logger = logging.getLogger(__name__)


class EconomyCog(commands.Cog):
    """Economy commands for coins, gems, and wallet management."""

    def __init__(self, bot: commands.Bot, economy_service: EconomyService):
        self.bot = bot
        self.economy = economy_service
        self.cooldown_mgr = CooldownManager()

    @commands.command(name="balance", aliases=["wallet", "coins", "bal"])
    async def balance(self, ctx: commands.Context):
        """Check your current coin and gem balance."""
        try:
            wallet = await self.economy.get_wallet(ctx.author.id, ctx.guild.id)

            embed = EmbedBuilder.create(
                title="💰 Wallet",
                description=f"{ctx.author.mention}'s account balance",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Coins", value=f"**{wallet.coins:,}**", inline=True)
            embed.add_field(name="Gems", value=f"**{wallet.gems:,}**", inline=True)
            embed.add_field(name="Games Played", value=f"{wallet.games_played}", inline=True)
            embed.add_field(
                name="Wins / Losses",
                value=f"{wallet.total_wins}W / {wallet.total_losses}L",
                inline=True,
            )
            embed.add_field(name="Votes Cast", value=f"{wallet.votes_cast}", inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="daily")
    async def daily_bonus(self, ctx: commands.Context):
        """Claim your daily coin bonus (once per 24 hours)."""
        try:
            success, msg = await self.economy.claim_daily_bonus(
                ctx.author.id, ctx.guild.id
            )

            if success:
                embed = EmbedBuilder.create(
                    title="✨ Daily Bonus Claimed!",
                    description=msg,
                    color=discord.Color.green(),
                )
            else:
                embed = EmbedBuilder.create(
                    title="❌ Daily Bonus",
                    description=msg,
                    color=discord.Color.red(),
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in daily command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="leaderboard", aliases=["lb", "top", "richest"])
    async def leaderboard(self, ctx: commands.Context):
        """Show the richest players and top winners."""
        try:
            # Get top richest
            richest = await self.economy.get_top_richest(ctx.guild.id, limit=10)
            richest_text = "\n".join(
                [
                    f"{i + 1}. <@{w['_id']['user_id']}> - {w['coins']:,} coins"
                    for i, w in enumerate(richest)
                ]
            )

            # Get top winners
            winners = await self.economy.get_top_winners(ctx.guild.id, limit=10)
            winners_text = "\n".join(
                [
                    f"{i + 1}. <@{w['_id']['user_id']}> - {w['total_wins']} wins"
                    for i, w in enumerate(winners)
                ]
            )

            embed = EmbedBuilder.create(
                title="📊 Guild Leaderboard",
                color=discord.Color.blurple(),
            )
            embed.add_field(name="💰 Richest Players", value=richest_text or "None yet", inline=False)
            embed.add_field(name="🏆 Top Winners", value=winners_text or "None yet", inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")


async def setup(bot: commands.Bot, economy_service: EconomyService):
    """Load economy cog into bot."""
    await bot.add_cog(EconomyCog(bot, economy_service))
