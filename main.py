"""
Main Discord Mafia Bot with Economy & Progression System.

This is the entry point that initializes the bot, loads services,
and registers command handlers.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

import discord
from discord.ext import commands

# Import config
from config.settings import Settings

# Import database and repositories
from database.mongodb import MongoDBClient
from database.repositories.wallet_repository import WalletRepository
from database.repositories.economy_log_repository import EconomyLogRepository
from database.repositories.profile_repository import ProfileRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.mafia_game_stats_repository import MafiaGameStatsRepository

# Import services
from services.economy_service import EconomyService
from services.profile_service import ProfileService
from services.vote_effect_service import VoteEffectService
from services.shop_service import ShopService
from services.game_service import GameService
from services.party_service import PartyService
from services.mafia_profile_service import MafiaProfileService

# Import command cogs
from bot.commands import (
    economy_commands,
    profile_commands,
    shop_commands,
    vote_effect_commands,
    join,
    leave,
    start,
    profile,
    add,
    kick,
    clearparty,
    party,
    players,
    endgame,
    roles,
    action,
)

logger = logging.getLogger(__name__)


class MafiaBot(commands.Bot):
    """Discord Mafia Bot with economy and progression systems."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings: Optional[Settings] = None
        self.mongo_client: Optional[MongoDBClient] = None
        self.wallet_repo: Optional[WalletRepository] = None
        self.economy_log_repo: Optional[EconomyLogRepository] = None
        self.profile_repo: Optional[ProfileRepository] = None
        self.inventory_repo: Optional[InventoryRepository] = None
        self.mafia_game_stats_repo: Optional[MafiaGameStatsRepository] = None
        self.economy_service: Optional[EconomyService] = None
        self.profile_service: Optional[ProfileService] = None
        self.vote_effect_service: Optional[VoteEffectService] = None
        self.shop_service: Optional[ShopService] = None
        self.game_service: Optional[GameService] = None
        self.party_service: Optional[PartyService] = None
        self.mafia_profile_service: Optional[MafiaProfileService] = None

    async def setup_services(self):
        """Initialize database and services."""
        logger.info("Setting up services...")

        # Load configuration
        self.settings = Settings.from_env()

        # Initialize MongoDB
        self.mongo_client = MongoDBClient(self.settings.mongo_uri)
        await self.mongo_client.connect()

        # Initialize repositories
        self.wallet_repo = WalletRepository(self.mongo_client)
        self.economy_log_repo = EconomyLogRepository(self.mongo_client)
        self.profile_repo = ProfileRepository(self.mongo_client)
        self.inventory_repo = InventoryRepository(self.mongo_client)
        self.mafia_game_stats_repo = MafiaGameStatsRepository(self.mongo_client)

        # Create indexes
        await self.wallet_repo.create_indexes()
        await self.profile_repo.create_indexes()
        await self.inventory_repo.create_indexes()
        await self.mafia_game_stats_repo.initialize()

        # Initialize services
        self.economy_service = EconomyService(self.wallet_repo, self.economy_log_repo)
        self.profile_service = ProfileService(self.profile_repo)
        self.vote_effect_service = VoteEffectService(self.inventory_repo)
        self.shop_service = ShopService(self.inventory_repo)
        self.party_service = PartyService()
        self.mafia_profile_service = MafiaProfileService(self.mafia_game_stats_repo)
        self.game_service = GameService(self.mafia_profile_service)

        logger.info("Services initialized successfully")

    async def load_commands(self):
        """Load command cogs."""
        logger.info("Loading command cogs...")

        # Load economy commands
        await economy_commands.setup(self, self.economy_service)
        logger.info("✓ Economy commands loaded")

        # Load profile commands
        await profile_commands.setup(self, self.profile_service, self.economy_service)
        logger.info("✓ Profile commands loaded")

        # Load shop commands
        await shop_commands.setup(
            self,
            self.shop_service,
            self.economy_service,
            self.profile_service,
        )
        logger.info("✓ Shop commands loaded")

        # Load vote effect commands
        await vote_effect_commands.setup(
            self,
            self.vote_effect_service,
            self.economy_service,
            self.profile_service,
        )
        logger.info("✓ Vote effect commands loaded")

        # Load game flow commands
        await join.setup(self, self.party_service)
        logger.info("✓ Join command loaded")

        await leave.setup(self, self.game_service)
        logger.info("✓ Leave command loaded")

        await start.setup(self, self.game_service, self.party_service)
        logger.info("✓ Start command loaded")

        # Load Mafia game profile command
        await profile.setup(self, self.mafia_profile_service)
        logger.info("✓ Mafia profile command loaded")

        # Load party management commands
        await add.setup(self, self.party_service)
        logger.info("✓ Add command loaded")

        await kick.setup(self, self.party_service)
        logger.info("✓ Kick command loaded")

        await clearparty.setup(self, self.party_service)
        logger.info("✓ Clearparty command loaded")

        await party.setup(self, self.party_service)
        logger.info("✓ Party command loaded")

        await players.setup(self, self.game_service)
        logger.info("✓ Players command loaded")

        await roles.setup(self)
        logger.info("✓ Roles command loaded")

        await action.setup(self, self.game_service)
        logger.info("✓ Action command loaded")

        await endgame.setup(self, self.game_service, self.party_service)
        logger.info("✓ Endgame command loaded")

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Set activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="the Mafia 🎭 | !help",
        )
        await self.change_presence(activity=activity)

    async def setup_hook(self):
        """Called before login, used for async initialization."""
        await self.setup_services()
        await self.load_commands()

    async def close(self):
        """Close database connections before shutting down."""
        if self.mongo_client:
            await self.mongo_client.close()
            logger.info("Database connection closed")
        await super().close()


def create_bot() -> MafiaBot:
    """Create and configure the bot instance."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = MafiaBot(
        command_prefix="!",
        intents=intents,
        help_command=commands.DefaultHelpCommand(),
    )

    return bot


async def main():
    """Main bot startup function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Discord Mafia Bot...")

    # Create bot
    bot = create_bot()

    # Get token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set!")
        return

    # Start bot
    try:
        async with bot:
            await bot.start(token)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
