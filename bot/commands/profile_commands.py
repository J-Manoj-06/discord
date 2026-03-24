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

async def setup(
    bot: commands.Bot,
    profile_service: ProfileService,
    economy_service: EconomyService,
):
    """Load profile cog into bot."""
    await bot.add_cog(ProfileCog(bot, profile_service, economy_service))
