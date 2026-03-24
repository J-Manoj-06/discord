"""Party Command: Display the current party lobby with all members."""

import logging

import discord
from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class PartyCog(commands.Cog):
    """Party display command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="party")
    async def show_party(self, ctx: commands.Context):
        """Display the current party lobby with all members."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild_id = ctx.guild.id
        players = self.party_service.get_party_players(guild_id)

        # Create embed
        embed = discord.Embed(
            title="🎭 Mafia Party Lobby",
            color=discord.Color.purple(),
        )

        if not players:
            embed.description = "No players have joined the party yet."
        else:
            # Fetch member objects to get proper names
            player_list = []
            for idx, user_id in enumerate(sorted(players), 1):
                member = ctx.guild.get_member(user_id)
                if member:
                    player_list.append(f"{idx}. {member.mention}")
                else:
                    player_list.append(f"{idx}. <@{user_id}>")

            embed.description = "\n".join(player_list)

        embed.set_footer(text=f"Total Players: {len(players)}")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load party cog into bot."""
    await bot.add_cog(PartyCog(bot, party_service))
