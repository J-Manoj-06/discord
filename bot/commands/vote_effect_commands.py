"""
Vote Effect Commands: List, equip, preview, and purchase vote effects.
"""
import logging

import discord
from discord.ext import commands

from services.vote_effect_service import VoteEffectService
from services.economy_service import EconomyService
from services.profile_service import ProfileService
from utils.embed_builder import EmbedBuilder

logger = logging.getLogger(__name__)


class VoteEffectCog(commands.Cog):
    """Voting effect cosmetics commands."""

    def __init__(
        self,
        bot: commands.Bot,
        vote_effect_service: VoteEffectService,
        economy_service: EconomyService,
        profile_service: ProfileService,
    ):
        self.bot = bot
        self.vote_effect = vote_effect_service
        self.economy = economy_service
        self.profile = profile_service

    @commands.command(name="voteeffects", aliases=["veffects"])
    async def vote_effects(self, ctx: commands.Context):
        """List all available vote effects."""
        try:
            effects = self.vote_effect.get_effect_catalog()

            embed = EmbedBuilder.create(
                title="🗳️ Vote Effects",
                description=(
                    "Customize how your votes appear in chat!\n"
                    "Use `!previewvoteeffect <name>` to see an effect\n"
                    "Use `!buyvoteeffect <name>` to purchase"
                ),
                color=discord.Color.blurple(),
            )

            for effect_id, effect in list(effects.items())[:12]:
                if effect_id == "default":
                    continue
                price_str = (
                    f"{effect.price_coins} coins"
                    if effect.price_coins
                    else f"{effect.price_gems} gems"
                )
                embed.add_field(
                    name=f"{effect.name} ({effect.rarity})",
                    value=f"{effect.description}\n**Price:** {price_str}",
                    inline=False,
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in voteeffects command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="previewvoteeffect", aliases=["pveffect"])
    async def preview_vote_effect(self, ctx: commands.Context, *, effect_name: str):
        """Preview how a vote effect looks."""
        try:
            if not effect_name:
                await ctx.send("Usage: `!previewvoteeffect <effect name>`")
                return

            # Find effect
            effect = None
            for eff_id, eff in self.vote_effect.get_effect_catalog().items():
                if eff.name.lower() == effect_name.lower():
                    effect = eff
                    break

            if not effect:
                await ctx.send(f"❌ Effect not found: {effect_name}")
                return

            preview = await self.vote_effect.preview_effect(effect.id)

            embed = EmbedBuilder.create(
                title=f"Preview: {effect.name}",
                description=f"```\n{preview}\n```\n{effect.description}",
                color=discord.Color.purple(),
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in previewvoteeffect command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="buyvoteeffect", aliases=["buyveffect"])
    async def buy_vote_effect(self, ctx: commands.Context, *, effect_name: str):
        """Purchase a vote effect."""
        try:
            if not effect_name:
                await ctx.send("Usage: `!buyvoteeffect <effect name>`")
                return

            # Find effect
            effect = None
            for eff_id, eff in self.vote_effect.get_effect_catalog().items():
                if eff.name.lower() == effect_name.lower():
                    effect = eff
                    break

            if not effect:
                await ctx.send(f"❌ Effect not found: {effect_name}")
                return

            if effect.id == "default":
                await ctx.send("❌ You already have the default effect!")
                return

            # Check wallet
            wallet = await self.economy.get_wallet(ctx.author.id, ctx.guild.id)

            # Validate purchase
            if effect.price_coins > 0:
                if wallet.coins < effect.price_coins:
                    await ctx.send(
                        f"❌ Insufficient coins. Need {effect.price_coins}, you have {wallet.coins}"
                    )
                    return

                # Deduct coins
                success, msg = await self.economy.remove_coins(
                    ctx.author.id,
                    ctx.guild.id,
                    effect.price_coins,
                    f"voteeffect_{effect.id}",
                )
            else:
                if wallet.gems < effect.price_gems:
                    await ctx.send(
                        f"❌ Insufficient gems. Need {effect.price_gems}, you have {wallet.gems}"
                    )
                    return

                # Deduct gems
                success, msg = await self.economy.remove_gems(
                    ctx.author.id,
                    ctx.guild.id,
                    effect.price_gems,
                    f"voteeffect_{effect.id}",
                )

            if not success:
                await ctx.send(f"❌ {msg}")
                return

            # Unlock effect
            await self.vote_effect.unlock_effect(
                ctx.author.id, ctx.guild.id, effect.id
            )

            embed = EmbedBuilder.create(
                title="✨ Vote Effect Purchased!",
                description=f"You now have: **{effect.name}**\n{effect.description}",
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed)
            logger.info(f"User {ctx.author.id} bought vote effect {effect.id}")
        except Exception as e:
            logger.error(f"Error in buyvoteeffect command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="equipvoteeffect", aliases=["equipeeffect"])
    async def equip_vote_effect(self, ctx: commands.Context, *, effect_name: str):
        """Equip a vote effect."""
        try:
            if not effect_name:
                await ctx.send("Usage: `!equipvoteeffect <effect name>`")
                return

            # Find effect
            effect = None
            for eff_id, eff in self.vote_effect.get_effect_catalog().items():
                if eff.name.lower() == effect_name.lower():
                    effect = eff
                    break

            if not effect:
                await ctx.send(f"❌ Effect not found: {effect_name}")
                return

            # Check ownership
            has_effect = await self.profile.has_cosmetic(
                ctx.author.id, ctx.guild.id, effect.id
            )

            if not has_effect and effect.id != "default":
                await ctx.send(
                    f"❌ You don't own this effect. Use `!buyvoteeffect {effect.name}` to purchase."
                )
                return

            # Equip
            success = await self.vote_effect.equip_effect(
                ctx.author.id, ctx.guild.id, effect.id
            )

            if success:
                embed = EmbedBuilder.create(
                    title="✨ Vote Effect Equipped",
                    description=f"Active vote effect: **{effect.name}**",
                    color=discord.Color.green(),
                )
            else:
                embed = EmbedBuilder.create(
                    title="❌ Error",
                    description="Could not equip effect",
                    color=discord.Color.red(),
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in equipvoteeffect command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")


async def setup(
    bot: commands.Bot,
    vote_effect_service: VoteEffectService,
    economy_service: EconomyService,
    profile_service: ProfileService,
):
    """Load vote effect cog into bot."""
    await bot.add_cog(
        VoteEffectCog(bot, vote_effect_service, economy_service, profile_service)
    )
