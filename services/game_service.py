"""Game Service: Complete Mafia game flow with phases and button-based actions.

Handles:
- Game session state management
- Player and role assignment
- Phase transitions (waiting → night → day → voting → ended)
- Night action resolution (kill/heal/investigate)
- Voting phase and elimination
- Win condition checks
- Thread creation and closure
- Game over messaging
"""

import asyncio
import random
from collections import Counter
from typing import Dict, List, Optional, Tuple

import discord
from discord.ext import commands

# Import UI components
from bot.ui.action_buttons import NightActionsView
from bot.ui.voting_buttons import VotingView
from bot.ui.player_select import get_player_display_name


class GameService:
    """Service layer for game session state, phases, and action resolution."""

    REQUIRED_ROLES = ["detective", "godfather", "doctor", "villager"]
    MIN_PLAYERS = 4
    NIGHT_DURATION_SECONDS = 60
    DAY_DURATION_SECONDS = 60
    VOTING_DURATION_SECONDS = 60

    ROLE_DM_MESSAGES = {
        "godfather": "You are the Godfather 🕶️. Lead the mafia and eliminate others.",
        "doctor": "You are the Doctor 💉. You can save one player each night.",
        "detective": "You are the Detective 🔍. You can investigate players.",
        "villager": "You are a Villager 👤. Find and eliminate the mafia.",
    }

    def __init__(self):
        self.game_sessions: Dict[int, Dict] = {}
        self.game_tasks: Dict[int, asyncio.Task] = {}

    def _get_or_create_session(self, guild_id: int) -> Dict:
        if guild_id not in self.game_sessions:
            self.game_sessions[guild_id] = {
                "players": [],
                "roles": {},
                "phase": "waiting",
                "thread_id": None,
                "alive_players": [],
                "votes": {},
                "night_actions": {},
                "day_count": 1,
            }
        return self.game_sessions[guild_id]

    def get_session(self, guild_id: int) -> Dict:
        return self._get_or_create_session(guild_id)

    def add_player(self, guild_id: int, user_id: int) -> Tuple[bool, str]:
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "waiting":
            return False, "Game already started. You cannot join right now."

        if user_id in session["players"]:
            return False, "You already joined this game."

        session["players"].append(user_id)
        return True, "joined"

    def assign_roles(self, guild_id: int) -> Tuple[bool, str, Dict[int, str]]:
        session = self._get_or_create_session(guild_id)
        players: List[int] = session["players"]

        if session["phase"] != "waiting":
            return False, "Game already started.", {}

        if len(players) < self.MIN_PLAYERS:
            return False, f"Need at least {self.MIN_PLAYERS} players to start.", {}

        shuffled_players = players[:]
        random.shuffle(shuffled_players)

        roles: Dict[int, str] = {
            shuffled_players[0]: "godfather",
            shuffled_players[1]: "doctor",
            shuffled_players[2]: "detective",
        }

        for user_id in shuffled_players[3:]:
            roles[user_id] = "villager"

        session["roles"] = roles
        session["alive_players"] = players[:]
        session["phase"] = "night"
        session["votes"] = {}
        session["night_actions"] = {}

        return True, "Roles assigned successfully.", roles

    async def send_roles_dm(self, guild: discord.Guild, roles: Dict[int, str]) -> List[int]:
        async def _dm_one(user_id: int, role_name: str) -> Tuple[int, bool]:
            member = guild.get_member(user_id)
            if member is None:
                return user_id, False

            try:
                await member.send(self.ROLE_DM_MESSAGES.get(role_name, "You have been assigned a role."))
                return user_id, True
            except (discord.Forbidden, discord.HTTPException):
                return user_id, False

        results = await asyncio.gather(*[_dm_one(uid, role) for uid, role in roles.items()])
        return [uid for uid, ok in results if not ok]

    async def create_game_thread(
        self,
        guild_id: int,
        channel: discord.abc.GuildChannel,
    ) -> Tuple[bool, str, Optional[discord.Thread]]:
        session = self._get_or_create_session(guild_id)
        day_count = session.get("day_count", 1)

        # If command is used inside an existing thread, reuse it.
        if isinstance(channel, discord.Thread):
            session["thread_id"] = channel.id
            return True, "Using current thread.", channel

        if not isinstance(channel, discord.TextChannel):
            return False, "Start command must be used in a text channel.", None

        try:
            # In regular text channels, public threads must be started from a message.
            starter_message = await channel.send("🧵 Creating game thread...")
            thread = await starter_message.create_thread(
                name=f"Mafia Game - Day {day_count}",
                auto_archive_duration=60,
            )
        except discord.Forbidden:
            return (
                False,
                "I need permissions: Send Messages, Create Public Threads, and Send Messages in Threads.",
                None,
            )
        except discord.HTTPException as exc:
            return False, f"Failed to create thread: {exc}", None

        session["thread_id"] = thread.id
        return True, "Thread created.", thread

    async def start_game_flow(self, ctx: commands.Context) -> Tuple[bool, str]:
        """Start complete game flow: thread creation, role assignment, DM notifications.
        
        Args:
            ctx: Discord context with user, guild, and channel info
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        guild = ctx.guild
        if guild is None:
            return False, "This command can only be used in a server."

        guild_id = guild.id
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "waiting":
            return False, "Game already started."

        if len(session["players"]) < self.MIN_PLAYERS:
            return False, f"Need at least {self.MIN_PLAYERS} players to start."

        success, message, roles = self.assign_roles(guild_id)
        if not success:
            return False, message

        success, message, thread = await self.create_game_thread(guild_id, ctx.channel)
        if not success or thread is None:
            session["phase"] = "waiting"
            session["roles"] = {}
            session["alive_players"] = []
            return False, message

        failed_dms = await self.send_roles_dm(guild, roles)

        # Format player list with display names
        player_names = [get_player_display_name(guild, uid) for uid in session["players"]]
        player_list = "\n".join(player_names)

        await thread.send(
            "🎮 **Mafia Game Started!**\n\n"
            f"**Players:**\n{player_list}\n\n"
            "The game begins with **Night Phase**.\n\n"
            "Check your **DMs** for your role."
        )

        if failed_dms:
            failed_names = [get_player_display_name(guild, uid) for uid in failed_dms]
            failed_list = ", ".join(failed_names)
            await thread.send(f"⚠️ Could not DM roles to: {failed_list}")

        task = asyncio.create_task(self._run_game_loop(guild, thread))
        self.game_tasks[guild_id] = task
        return True, "Game has started! Roles have been sent via DM 🌙"

    async def _run_game_loop(self, guild: discord.Guild, thread: discord.Thread):
        """Main game loop: night → day → voting → repeat.
        
        Continues until win condition is met.
        
        Args:
            guild: Discord guild
            thread: Game thread for messages
        """
        guild_id = guild.id
        try:
            while True:
                game_over = await self.run_night_phase(guild, thread)
                if game_over:
                    break

                await self.run_day_phase(guild_id, thread)

                game_over = await self.run_voting_phase(guild_id, guild, thread)
                if game_over:
                    break

                session = self._get_or_create_session(guild_id)
                session["day_count"] += 1
                try:
                    await thread.edit(name=f"Mafia Game - Day {session['day_count']}")
                except discord.HTTPException:
                    pass
        finally:
            self.game_tasks.pop(guild_id, None)

    async def run_night_phase(self, guild: discord.Guild, thread: discord.Thread) -> bool:
        """Run night phase: show action buttons and wait for submissions.
        
        Args:
            guild: Discord guild
            thread: Game thread for messages
            
        Returns:
            True if game ends, False otherwise
        """
        guild_id = guild.id
        session = self._get_or_create_session(guild_id)
        session["phase"] = "night"
        session["night_actions"] = {}

        await thread.send(
            "🌙 **Night Phase** has begun.\n\n"
            "Available actions:\n"
            "🔪 Kill (Godfather)\n"
            "💉 Heal (Doctor)\n"
            "🔍 Investigate (Detective)\n\n"
            "_Click a button below to perform your action._",
            view=NightActionsView(self, guild, guild_id),
        )

        await asyncio.sleep(self.NIGHT_DURATION_SECONDS)
        await self.resolve_night(guild_id, guild, thread)
        return await self.check_win_conditions(guild_id, guild, thread)

    async def resolve_night(self, guild_id: int, guild: discord.Guild, thread: discord.Thread):
        """Resolve night phase: process kill/heal actions.
        
        Kill target dies unless healed.
        Heal target survives kill (if healed and killed same round).
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            thread: Game thread for messages
        """
        session = self._get_or_create_session(guild_id)
        night_actions = session["night_actions"]

        kill_target = night_actions.get("kill")
        heal_target = night_actions.get("heal")

        killed_user_id: Optional[int] = None
        
        # Kill succeeds only if target is not healed
        if kill_target is not None and kill_target != heal_target:
            if kill_target in session["alive_players"]:
                session["alive_players"].remove(kill_target)
                killed_user_id = kill_target

        if killed_user_id is None:
            await thread.send("🌙 **Night Result**\n\nNobody died during the night.")
        else:
            victim_name = get_player_display_name(guild, killed_user_id)
            victim_role = session["roles"].get(killed_user_id, "unknown")
            await thread.send(
                f"🌙 **Night Result**\n\n"
                f"**{victim_name}** was killed.\n"
                f"Role: *{victim_role.title()}*"
            )

    async def run_day_phase(self, guild_id: int, thread: discord.Thread):
        """Run day phase: discussion period before voting.
        
        Args:
            guild_id: Guild ID
            thread: Game thread for messages
        """
        session = self._get_or_create_session(guild_id)
        session["phase"] = "day"
        
        await thread.send(
            f"☀️ **Day Phase** - Day {session['day_count']}\n\n"
            "_Everyone can discuss who might be mafia. "
            "Voting will start soon._"
        )
        await asyncio.sleep(self.DAY_DURATION_SECONDS)

    async def run_voting_phase(self, guild_id: int, guild: discord.Guild, thread: discord.Thread) -> bool:
        """Run voting phase: show vote buttons and process votes.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            thread: Game thread for messages
            
        Returns:
            True if game ends, False otherwise
        """
        session = self._get_or_create_session(guild_id)
        session["phase"] = "voting"
        session["votes"] = {}

        await thread.send(
            "🗳️ **Voting Phase** has started.\n\n"
            "_Click a button below to vote for elimination._",
            view=VotingView(self, guild, guild_id),
        )

        await asyncio.sleep(self.VOTING_DURATION_SECONDS)
        await self.resolve_votes(guild_id, guild, thread)
        return await self.check_win_conditions(guild_id, guild, thread)

    async def resolve_votes(self, guild_id: int, guild: discord.Guild, thread: discord.Thread):
        """Resolve voting: determine eliminated player by vote count.
        
        Ties are broken by lowest user ID.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            thread: Game thread for messages
        """
        session = self._get_or_create_session(guild_id)
        votes: Dict[int, int] = session["votes"]

        if not votes:
            await thread.send("🗳️ **Voting Result**\n\nNo votes were cast. Nobody is eliminated.")
            return

        counts = Counter(votes.values())
        max_votes = max(counts.values())
        top_targets = [target_id for target_id, count in counts.items() if count == max_votes]

        # Break ties using lowest ID
        eliminated_id = sorted(top_targets)[0]
        
        if eliminated_id in session["alive_players"]:
            session["alive_players"].remove(eliminated_id)

        eliminated_name = get_player_display_name(guild, eliminated_id)
        eliminated_role = session["roles"].get(eliminated_id, "unknown")
        vote_count = counts[eliminated_id]
        
        await thread.send(
            f"🗳️ **Voting Result**\n\n"
            f"**{eliminated_name}** has been eliminated.\n"
            f"Votes: {vote_count}\n"
            f"Role: *{eliminated_role.title()}*"
        )

    async def check_win_conditions(self, guild_id: int, guild: discord.Guild, thread: discord.Thread) -> bool:
        """Check if game has ended and determine winner.
        
        Win conditions:
        - Villagers win if Godfather (mafia) is dead
        - Mafia wins if mafia_count >= villager_count
        
        Shows survivors and game results before closing thread.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            thread: Game thread for messages
            
        Returns:
            True if game ended, False otherwise
        """
        session = self._get_or_create_session(guild_id)

        mafia_alive = 0
        villager_alive = 0
        for player_id in session["alive_players"]:
            role = session["roles"].get(player_id)
            if role == "godfather":
                mafia_alive += 1
            else:
                villager_alive += 1

        winner: Optional[str] = None

        # Villagers win if Godfather is dead
        if mafia_alive == 0:
            session["phase"] = "ended"
            winner = "Villagers"

        # Mafia wins if mafia >= villagers
        elif mafia_alive >= villager_alive:
            session["phase"] = "ended"
            winner = "Mafia"

        if winner is None:
            return False

        # Build survivor list
        survivor_names = [get_player_display_name(guild, pid) for pid in session["alive_players"]]
        survivor_text = "\n".join(survivor_names) if survivor_names else "_None_"

        # Send game over message
        await thread.send(
            f"🏆 **GAME OVER**\n\n"
            f"**Winner: {winner}**\n\n"
            f"Survivors:\n{survivor_text}"
        )

        # Archive and lock thread
        try:
            await thread.edit(archived=True, locked=True)
        except discord.HTTPException:
            # If archiving fails, try locking only
            try:
                await thread.edit(locked=True)
            except discord.HTTPException:
                pass

        return True
