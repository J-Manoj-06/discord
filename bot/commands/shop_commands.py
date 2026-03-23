"""
Shop Commands: Buy items, view inventory, manage cosmetics.
"""
import logging

import discord
from discord.ext import commands

from services.shop_service import ShopService
from services.economy_service import EconomyService
from services.profile_service import ProfileService
from utils.embed_builder import EmbedBuilder

logger = logging.getLogger(__name__)


class ShopCog(commands.Cog):
    """Shop and inventory commands."""

    def __init__(
        self,
        bot: commands.Bot,
        shop_service: ShopService,
        economy_service: EconomyService,
        profile_service: ProfileService,
    ):
        self.bot = bot
        self.shop = shop_service
        self.economy = economy_service
        self.profile = profile_service

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context, category: str = None):
        """Browse the shop."""
        try:
            if category:
                items = self.shop.list_by_category(category)
                if not items:
                    await ctx.send(f"No items in category: {category}")
                    return
            else:
                items = self.shop.list_purchasable()

            # Create paginated shop display
            embed = EmbedBuilder.create(
                title="🏪 Shop",
                description=(
                    "Browse available cosmetics and upgrades\n"
                    "Use `!buy <item>` to purchase"
                ),
                color=discord.Color.greyple(),
            )

            for item in items[:15]:  # Limit to 15 items per page
                embed.add_field(
                    name=self.shop.get_item_format(item),
                    value="",
                    inline=False,
                )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in shop command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="buy")
    async def buy(self, ctx: commands.Context, *, item_name: str):
        """Purchase an item from the shop."""
        try:
            if not item_name:
                await ctx.send("Usage: `!buy <item name>`")
                return

            # Find item in catalog
            item = None
            for cat_item in self.shop.get_catalog().values():
                if cat_item.name.lower() == item_name.lower():
                    item = cat_item
                    break

            if not item:
                await ctx.send(f"❌ Item not found: {item_name}")
                return

            # Get user wallet
            wallet = await self.economy.get_wallet(ctx.author.id, ctx.guild.id)

            # Validate purchase
            can_buy, currency = await self.shop.purchase_item(
                ctx.author.id, ctx.guild.id, item.id, wallet.coins, wallet.gems
            )

            if not can_buy:
                embed = EmbedBuilder.create(
                    title="❌ Purchase Failed",
                    description=currency,
                    color=discord.Color.red(),
                )
                await ctx.send(embed=embed)
                return

            # Process payment
            if currency == "coin":
                success, msg = await self.economy.remove_coins(
                    ctx.author.id, ctx.guild.id, item.price_coins, f"purchase_{item.id}"
                )
            else:
                success, msg = await self.economy.remove_gems(
                    ctx.author.id, ctx.guild.id, item.price_gems, f"purchase_{item.id}"
                )

            if not success:
                await ctx.send(f"❌ {msg}")
                return

            # Add to inventory
            await self.profile.add_unlocked_cosmetic(
                ctx.author.id, ctx.guild.id, item.id
            )

            embed = EmbedBuilder.create(
                title="✨ Purchase Successful!",
                description=(
                    f"You bought: **{item.name}**\n"
                    f"Cost: {item.price_coins or item.price_gems} "
                    f"{'coins' if item.price_coins else 'gems'}"
                ),
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed)
            logger.info(
                f"User {ctx.author.id} purchased {item.id} for {item.price_coins or item.price_gems}"
            )
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx: commands.Context):
        """Check your owned cosmetics."""
        try:
            profile = await self.profile.get_profile(ctx.author.id, ctx.guild.id)

            cosmetics_text = "\n".join(profile.unlocked_cosmetics) or "None yet"

            embed = EmbedBuilder.create(
                title="📦 Inventory",
                description=f"**Owned Items ({len(profile.unlocked_cosmetics)}):**\n{cosmetics_text}",
                color=discord.Color.blue(),
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in inventory command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")


async def setup(
    bot: commands.Bot,
    shop_service: ShopService,
    economy_service: EconomyService,
    profile_service: ProfileService,
):
    """Load shop cog into bot."""
    await bot.add_cog(ShopCog(bot, shop_service, economy_service, profile_service))
