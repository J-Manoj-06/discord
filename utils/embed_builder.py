"""
Embed Builder: Utility for creating consistent embeds across the bot.
"""
import discord
from typing import Optional


class EmbedBuilder:
    """Utility class for creating styled embeds."""

    @staticmethod
    def create(
        title: str = "",
        description: str = "",
        color: discord.Color = None,
        thumbnail: str = None,
        image: str = None,
        footer_text: str = None,
    ) -> discord.Embed:
        """Create a base embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or discord.Color.blurple(),
        )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)
        if footer_text:
            embed.set_footer(text=footer_text)

        return embed

    @staticmethod
    def economy(title: str = "", description: str = "") -> discord.Embed:
        """Create an economy-themed embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.gold())

    @staticmethod
    def profile(title: str = "", description: str = "") -> discord.Embed:
        """Create a profile-themed embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.blue())

    @staticmethod
    def shop(title: str = "", description: str = "") -> discord.Embed:
        """Create a shop-themed embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.teal())

    @staticmethod
    def success(title: str = "", description: str = "") -> discord.Embed:
        """Create a success embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.green())

    @staticmethod
    def error(title: str = "", description: str = "") -> discord.Embed:
        """Create an error embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.red())

    @staticmethod
    def warning(title: str = "", description: str = "") -> discord.Embed:
        """Create a warning embed."""
        return EmbedBuilder.create(title, description, color=discord.Color.orange())


# Legacy functions for backward compatibility
def economy_embed(title: str, description: str) -> discord.Embed:
    return EmbedBuilder.economy(title, description)


def profile_embed(title: str, description: str) -> discord.Embed:
    return EmbedBuilder.profile(title, description)


def shop_embed(title: str, description: str) -> discord.Embed:
    return EmbedBuilder.shop(title, description)


def success_embed(title: str, description: str) -> discord.Embed:
    return EmbedBuilder.success(title, description)


def error_embed(title: str, description: str) -> discord.Embed:
    return EmbedBuilder.error(title, description)
