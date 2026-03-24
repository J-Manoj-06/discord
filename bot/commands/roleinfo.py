"""Role info command for detailed role descriptions."""

from __future__ import annotations

from discord.ext import commands

from services.role_info_service import RoleInfoService


class RoleInfoCog(commands.Cog):
    """Provide detailed info for a specific role."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.role_info = RoleInfoService()

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx: commands.Context, *, role_name: str | None = None):
        """Show detailed role information: !roleinfo <rolename>."""
        if not role_name:
            await ctx.send("Usage: `!roleinfo <rolename>`")
            return

        embed = self.role_info.build_embed(role_name, title="🎭 Role Information")
        if embed is None:
            await ctx.send("❌ Role not found. Use !roles to see all available roles.")
            return

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load role info cog into bot."""
    await bot.add_cog(RoleInfoCog(bot))
