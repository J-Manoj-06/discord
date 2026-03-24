# Party Lobby System - Complete Code Reference

## File 1: services/party_service.py

```python
"""Party Service: Manages party state, players, and game status across guilds.

Provides a clean separation between party management and game logic.
"""

from typing import Dict, Optional, Set


class PartyService:
    """Manage party lobbies per guild."""

    def __init__(self):
        """Initialize party storage."""
        self.parties: Dict[int, Dict] = {}

    def create_party(self, guild_id: int) -> None:
        """Create or reset party for a guild."""
        self.parties[guild_id] = {
            "players": set(),
            "game_active": False,
        }

    def _get_or_create_party(self, guild_id: int) -> Dict:
        """Get party or create if it doesn't exist."""
        if guild_id not in self.parties:
            self.create_party(guild_id)
        return self.parties[guild_id]

    def add_player_to_party(self, guild_id: int, user_id: int) -> bool:
        """Add a player to the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if added, False if already present
        """
        party = self._get_or_create_party(guild_id)
        if user_id in party["players"]:
            return False
        party["players"].add(user_id)
        return True

    def remove_player_from_party(self, guild_id: int, user_id: int) -> bool:
        """Remove a player from the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if removed, False if not in party
        """
        party = self._get_or_create_party(guild_id)
        if user_id not in party["players"]:
            return False
        party["players"].discard(user_id)
        return True

    def clear_party(self, guild_id: int) -> int:
        """Remove all players from the party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of players removed
        """
        party = self._get_or_create_party(guild_id)
        count = len(party["players"])
        party["players"].clear()
        return count

    def get_party_players(self, guild_id: int) -> Set[int]:
        """Get all players in the party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Set of user IDs in the party
        """
        party = self._get_or_create_party(guild_id)
        return party["players"].copy()

    def get_player_count(self, guild_id: int) -> int:
        """Get number of players in party.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of players
        """
        party = self._get_or_create_party(guild_id)
        return len(party["players"])

    def is_player_in_party(self, guild_id: int, user_id: int) -> bool:
        """Check if a player is in the party.

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID

        Returns:
            True if player is in party
        """
        party = self._get_or_create_party(guild_id)
        return user_id in party["players"]

    def set_game_active(self, guild_id: int, active: bool) -> None:
        """Set game active status.

        Args:
            guild_id: Discord guild ID
            active: Whether game is active
        """
        party = self._get_or_create_party(guild_id)
        party["game_active"] = active

    def is_game_active(self, guild_id: int) -> bool:
        """Check if game is active.

        Args:
            guild_id: Discord guild ID

        Returns:
            True if game is active
        """
        party = self._get_or_create_party(guild_id)
        return party["game_active"]
```

---

## File 2: bot/commands/join.py

```python
"""
Join Command: Adds players to the party lobby.
"""

import logging

from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class JoinCog(commands.Cog):
    """Join party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="join")
    async def join_party(self, ctx: commands.Context):
        """Join the Mafia party lobby."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Try to add player to party
            success = self.party_service.add_player_to_party(ctx.guild.id, ctx.author.id)

            if not success:
                await ctx.send(f"❌ You are already in the party.")
                return

            await ctx.send(f"🎉 {ctx.author.name} joined the party!")
        except Exception as exc:
            logger.error("Error in join command: %s", exc)
            await ctx.send("❌ Failed to join party. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load join cog into bot."""
    await bot.add_cog(JoinCog(bot, party_service))
```

---

## File 3: bot/commands/party.py

```python
"""
Party Command: Displays the current party lobby.
"""

import logging

import discord
from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class PartyCog(commands.Cog):
    """Party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="party")
    async def show_party(self, ctx: commands.Context):
        """Display the current party lobby."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            party_players = self.party_service.get_party_players(ctx.guild.id)

            if not party_players:
                await ctx.send("No players have joined the party yet.")
                return

            # Get player display names
            sorted_players = sorted(party_players)
            player_list = []

            for idx, user_id in enumerate(sorted_players, 1):
                member = ctx.guild.get_member(user_id)
                if member:
                    player_list.append(f"{idx}. {member.name}")
                else:
                    player_list.append(f"{idx}. <Unknown User {user_id}>")

            embed = discord.Embed(
                title="🎭 Mafia Party Lobby",
                description="\n".join(player_list),
                color=discord.Color.purple(),
            )
            embed.set_footer(text=f"Total Players: {len(party_players)}")

            await ctx.send(embed=embed)
        except Exception as exc:
            logger.error("Error in party command: %s", exc)
            await ctx.send("❌ Failed to display party. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load party cog into bot."""
    await bot.add_cog(PartyCog(bot, party_service))
```

---

## File 4: bot/commands/start.py

```python
"""
Start Command: Starts the Mafia game with party players.
"""

import logging

from discord.ext import commands

from services.game_service import GameService
from services.party_service import PartyService

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    """Start game command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService, party_service: PartyService):
        self.bot = bot
        self.game_service = game_service
        self.party_service = party_service

    @commands.command(name="start")
    async def start_game(self, ctx: commands.Context):
        """Start the Mafia game with players from the party."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Get party players
            party_players = self.party_service.get_party_players(ctx.guild.id)
            
            # Check minimum players
            if len(party_players) < 4:
                await ctx.send("❌ At least 4 players are required to start the game.")
                return

            # Get or create game session
            session = self.game_service.get_session(ctx.guild.id)
            
            # Load party players into game session
            session["players"] = list(party_players)
            
            # Mark party as game active
            self.party_service.set_game_active(ctx.guild.id, True)

            # Start the game flow
            success, message = await self.game_service.start_game_flow(ctx)
            
            if not success:
                # Revert game_active if start failed
                self.party_service.set_game_active(ctx.guild.id, False)
                await ctx.send(f"❌ {message}")
                return

            await ctx.send(f"🎮 {message}")
        except Exception as exc:
            logger.error("Error in start command: %s", exc)
            await ctx.send("❌ Failed to start game. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService, party_service: PartyService):
    """Load start cog into bot."""
    await bot.add_cog(StartCog(bot, game_service, party_service))
```

---

## File 5: bot/commands/add.py

```python
"""
Add Command: Manually adds players to the party (admin only).
"""

import logging

from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class AddCog(commands.Cog):
    """Add command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add_player(self, ctx: commands.Context):
        """Add a player to the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not ctx.message.mentions:
            await ctx.send("❌ Please mention a player to add.")
            return

        try:
            for member in ctx.message.mentions:
                success = self.party_service.add_player_to_party(ctx.guild.id, member.id)

                if not success:
                    await ctx.send(f"❌ {member.name} is already in the party.")
                    continue

                await ctx.send(f"{member.name} has been added to the party.")
        except Exception as exc:
            logger.error("Error in add command: %s", exc)
            await ctx.send("❌ Failed to add player. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load add cog into bot."""
    await bot.add_cog(AddCog(bot, party_service))
```

---

## File 6: bot/commands/kick.py

```python
"""
Kick Command: Removes a player from the party (admin only).
"""

import logging

from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class KickCog(commands.Cog):
    """Kick command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="kick")
    @commands.has_permissions(manage_guild=True)
    async def kick_player(self, ctx: commands.Context):
        """Remove a player from the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not ctx.message.mentions:
            await ctx.send("❌ Please mention a player to kick.")
            return

        try:
            if self.party_service.is_game_active(ctx.guild.id):
                await ctx.send("❌ Cannot modify party during active game.")
                return

            for member in ctx.message.mentions:
                success = self.party_service.remove_player_from_party(ctx.guild.id, member.id)

                if not success:
                    await ctx.send(f"❌ {member.name} is not in the party.")
                    continue

                await ctx.send(f"{member.name} removed from the party.")
        except Exception as exc:
            logger.error("Error in kick command: %s", exc)
            await ctx.send("❌ Failed to kick player. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load kick cog into bot."""
    await bot.add_cog(KickCog(bot, party_service))
```

---

## File 7: bot/commands/clearparty.py

```python
"""
Clear Party Command: Clears all players from the party (admin only).
"""

import logging

from discord.ext import commands

from services.party_service import PartyService

logger = logging.getLogger(__name__)


class ClearPartyCog(commands.Cog):
    """Clear party command handler."""

    def __init__(self, bot: commands.Bot, party_service: PartyService):
        self.bot = bot
        self.party_service = party_service

    @commands.command(name="clearparty")
    @commands.has_permissions(manage_guild=True)
    async def clear_party(self, ctx: commands.Context):
        """Clear all players from the party (admin only)."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            if self.party_service.is_game_active(ctx.guild.id):
                await ctx.send("❌ Cannot modify party during active game.")
                return

            count = self.party_service.clear_party(ctx.guild.id)
            await ctx.send(f"Party has been cleared. ({count} players removed)")
        except Exception as exc:
            logger.error("Error in clearparty command: %s", exc)
            await ctx.send("❌ Failed to clear party. Please try again.")


async def setup(bot: commands.Bot, party_service: PartyService):
    """Load clearparty cog into bot."""
    await bot.add_cog(ClearPartyCog(bot, party_service))
```

---

## File 8: bot/commands/players.py

```python
"""
Players Command: Displays alive players during an active game.
"""

import logging

import discord
from discord.ext import commands

from services.game_service import GameService

logger = logging.getLogger(__name__)


class PlayersCog(commands.Cog):
    """Players command handler."""

    def __init__(self, bot: commands.Bot, game_service: GameService):
        self.bot = bot
        self.game_service = game_service

    @commands.command(name="players")
    async def show_players(self, ctx: commands.Context):
        """Display alive players in the current game."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            session = self.game_service.get_session(ctx.guild.id)

            if session["phase"] == "waiting":
                await ctx.send("❌ No game is currently active.")
                return

            alive_players = session.get("alive_players", [])

            if not alive_players:
                await ctx.send("❌ No players are alive.")
                return

            # Get player display names
            sorted_players = sorted(alive_players)
            player_list = []

            for idx, user_id in enumerate(sorted_players, 1):
                member = ctx.guild.get_member(user_id)
                if member:
                    player_list.append(f"{idx}. {member.name}")
                else:
                    player_list.append(f"{idx}. <Unknown User {user_id}>")

            embed = discord.Embed(
                title="👥 Alive Players",
                description="\n".join(player_list),
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"Alive Count: {len(alive_players)}")

            await ctx.send(embed=embed)
        except Exception as exc:
            logger.error("Error in players command: %s", exc)
            await ctx.send("❌ Failed to display players. Please try again.")


async def setup(bot: commands.Bot, game_service: GameService):
    """Load players cog into bot."""
    await bot.add_cog(PlayersCog(bot, game_service))
```

---

## Integration in main.py (Key Sections)

**Service Initialization (setup_services method):**
```python
self.party_service = PartyService()
self.game_service = GameService(self.mafia_profile_service)
```

**Command Loading (load_commands method):**
```python
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
```

---

## Quick Start Usage

1. **Players join lobby:**
   ```
   !join
   !join
   !join
   !join
   ```

2. **Check party:**
   ```
   !party
   ```

3. **Start game:**
   ```
   !start
   ```

4. **During game:**
   ```
   !players
   ```

5. **Admin commands:**
   ```
   !add @User
   !kick @User
   !clearparty
   ```

