"""Roles Command: show available Mafia roles in an embed."""

import discord
from discord.ext import commands

from roles.role_manager import RoleManager


class RolesCog(commands.Cog):
    """Roles list command handler."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.role_manager = RoleManager()

    @staticmethod
    def _display_role_name(role_name: str) -> str:
        """Convert role keys like 'serialkiller' to display names."""
        aliases = {
            "serialkiller": "Serial Killer",
            "guardianangel": "Guardian Angel",
            "timetraveler": "Time Traveler",
        }
        return aliases.get(role_name, role_name.replace("_", " ").title())

    @commands.command(name="roles", aliases=["role"])
    async def roles(self, ctx: commands.Context):
        """Display all available roles grouped by team."""
        embed = discord.Embed(
            title="🎭 Available Roles",
            color=discord.Color.dark_red(),
        )

        village_roles = sorted(
            [self._display_role_name(name) for name in self.role_manager.village_role_names()]
        )
        mafia_roles = sorted(
            [self._display_role_name(name) for name in self.role_manager.mafia_role_names()]
        )
        neutral_roles = sorted(
            [self._display_role_name(name) for name in self.role_manager.neutral_role_names()]
        )

        special_roles = sorted(
            [
                self._display_role_name(name)
                for name in self.role_manager.roles.keys()
                if name
                not in self.role_manager.village_role_names()
                and name not in self.role_manager.mafia_role_names()
                and name not in self.role_manager.neutral_role_names()
            ]
        )

        embed.add_field(
            name="🏘️ Village Roles",
            value=", ".join(village_roles) if village_roles else "None",
            inline=False,
        )
        embed.add_field(
            name="🕶️ Mafia Roles",
            value=", ".join(mafia_roles) if mafia_roles else "None",
            inline=False,
        )
        embed.add_field(
            name="🎲 Neutral Roles",
            value=", ".join(neutral_roles) if neutral_roles else "None",
            inline=False,
        )

        if special_roles:
            embed.add_field(
                name="✨ Special Roles",
                value=", ".join(special_roles),
                inline=False,
            )

        embed.set_footer(text="Use !roles or !role")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load roles cog into bot."""
    await bot.add_cog(RolesCog(bot))
