"""Roles Command: show available Mafia roles in an embed."""

import discord
from discord.ext import commands


class RolesCog(commands.Cog):
    """Roles list command handler."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="roles")
    async def roles(self, ctx: commands.Context):
        """Display available core roles and their abilities."""
        embed = discord.Embed(
            title="🎭 Available Roles",
            color=discord.Color.dark_red(),
        )

        embed.add_field(
            name="🕶️ Godfather",
            value="Leader of the mafia. Eliminates one player each night.",
            inline=False,
        )
        embed.add_field(
            name="🔍 Detective",
            value="Investigates one player each night to determine if they are mafia.",
            inline=False,
        )
        embed.add_field(
            name="💉 Doctor",
            value="Protects one player from being killed each night.",
            inline=False,
        )
        embed.add_field(
            name="👤 Villager",
            value="No night ability. Must vote during the day.",
            inline=False,
        )
        embed.add_field(
            name="🍞 Baker (Neutral Role)",
            value=(
                "Each night give bread to one alive player. Bread grants a random effect. "
                "Win by feeding the required number of alive players while you remain alive."
            ),
            inline=False,
        )
        embed.add_field(
            name="🛐 Submissor (Neutral Role)",
            value=(
                "You have no abilities. The first player who attacks you converts "
                "you to their side. If they die, you inherit their role."
            ),
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load roles cog into bot."""
    await bot.add_cog(RolesCog(bot))
