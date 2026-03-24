"""Game Service: Complete Mafia game flow with phases and button-based actions.

Handles:
- Game session state management
- Player and role assignment
- Phase transitions (waiting → night → day → voting → ended)
- Night action resolution (kill/heal/investigate)
- Voting phase and elimination
- Win condition checks
- Game channel creation and deletion
- Game over messaging and profile updates
"""

import asyncio
import logging
from collections import Counter
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import discord
from discord.ext import commands

# Import UI components
from bot.ui.action_buttons import NightActionsView
from bot.ui.voting_buttons import VotingView
from bot.ui.player_select import get_player_display_name
from roles.role_manager import RoleManager
from services.action_resolver import Action, resolve_actions

if TYPE_CHECKING:
    from services.mafia_profile_service import MafiaProfileService

logger = logging.getLogger(__name__)


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

    def __init__(self, profile_service: Optional["MafiaProfileService"] = None):
        """Initialize game service.
        
        Args:
            profile_service: Optional MafiaProfileService for profile updates
        """
        self.game_sessions: Dict[int, Dict] = {}
        self.game_tasks: Dict[int, asyncio.Task] = {}
        self.profile_service = profile_service
        self.role_manager = RoleManager()
        self.mafia_role_names = self.role_manager.mafia_role_names()

    def _get_or_create_session(self, guild_id: int) -> Dict:
        if guild_id not in self.game_sessions:
            self.game_sessions[guild_id] = {
                "players": [],
                "roles": {},
                "role_objects": {},
                "phase": "waiting",
                "game_channel_id": None,
                "channel_id": None,
                "alive_players": [],
                "votes": {},
                "night_actions": {},
                "actions": [],
                "pending_effects": [],
                "framed_targets": [],
                "silenced_players": [],
                "death_history": [],
                "night_reports": {},
                "mode": "classic",
                "day_count": 1,
                "manual_end": False,
            }
        return self.game_sessions[guild_id]

    def has_active_game(self, guild_id: int) -> bool:
        """Check whether a non-waiting game session exists for this guild."""
        session = self.game_sessions.get(guild_id)
        if not session:
            return False
        return session.get("phase", "waiting") != "waiting"

    def get_session(self, guild_id: int) -> Dict:
        return self._get_or_create_session(guild_id)

    def set_game_mode(self, guild_id: int, mode: str) -> Tuple[bool, str]:
        """Set game mode before start. Supported: classic, advanced, chaos."""
        session = self._get_or_create_session(guild_id)
        if session["phase"] != "waiting":
            return False, "Cannot change mode after the game starts."

        normalized = mode.lower().strip()
        if normalized not in {"classic", "advanced", "chaos"}:
            return False, "Invalid mode. Use classic, advanced, or chaos."

        session["mode"] = normalized
        return True, f"Game mode set to {normalized}."

    def add_player(self, guild_id: int, user_id: int) -> Tuple[bool, str]:
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "waiting":
            return False, "Game already started. You cannot join right now."

        if user_id in session["players"]:
            return False, "You already joined this game."

        session["players"].append(user_id)
        return True, "joined"

    def remove_player(self, guild_id: int, user_id: int) -> Tuple[bool, str]:
        """Remove a player from the waiting game session.

        Players can only leave before the game has started.
        """
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "waiting":
            return False, "Game already started. You cannot leave right now."

        if user_id not in session["players"]:
            return False, "You are not in the current game."

        session["players"].remove(user_id)
        return True, "left"

    def assign_roles(self, guild_id: int, mode: str = "classic") -> Tuple[bool, str, Dict[int, str]]:
        session = self._get_or_create_session(guild_id)
        players: List[int] = session["players"]

        if session["phase"] != "waiting":
            return False, "Game already started.", {}

        if len(players) < self.MIN_PLAYERS:
            return False, f"Need at least {self.MIN_PLAYERS} players to start.", {}

        assigned = self.role_manager.assign_roles(players, mode)
        roles: Dict[int, str] = {user_id: role.name for user_id, role in assigned.items()}

        session["roles"] = roles
        session["role_objects"] = assigned
        session["alive_players"] = players[:]
        session["phase"] = "night"
        session["votes"] = {}
        session["night_actions"] = {}
        session["actions"] = []
        session["pending_effects"] = []
        session["framed_targets"] = []
        session["silenced_players"] = []
        session["death_history"] = []
        session["night_reports"] = {}
        session["mode"] = mode
        session["mafia_role_names"] = self.mafia_role_names

        return True, "Roles assigned successfully.", roles

    async def send_roles_dm(self, guild: discord.Guild, roles: Dict[int, str]) -> List[int]:
        async def _dm_one(user_id: int, role_name: str) -> Tuple[int, bool]:
            member = guild.get_member(user_id)
            if member is None:
                return user_id, False

            try:
                role_obj = self.role_manager.create_role(role_name)
                default_msg = self.ROLE_DM_MESSAGES.get(role_name, role_obj.description())
                await member.send(default_msg)
                return user_id, True
            except (discord.Forbidden, discord.HTTPException):
                return user_id, False

        results = await asyncio.gather(*[_dm_one(uid, role) for uid, role in roles.items()])
        return [uid for uid, ok in results if not ok]

    async def create_game_channel(
        self,
        guild: discord.Guild,
        guild_id: int,
    ) -> Tuple[bool, str, Optional[discord.TextChannel]]:
        """Create temporary game channel with player-only permissions.
        
        Args:
            guild: Discord guild
            guild_id: Guild ID
            
        Returns:
            Tuple of (success: bool, message: str, channel: Optional[TextChannel])
        """
        session = self._get_or_create_session(guild_id)

        try:
            # Check if channel already exists (shouldn't happen but safety check)
            existing_channel = discord.utils.find(
                lambda c: c.name == f"mafia-game-{guild_id}",
                guild.text_channels,
            )
            if existing_channel:
                try:
                    await existing_channel.delete()
                except discord.HTTPException:
                    pass

            # Ensure the bot is explicitly allowed to view/send in game channel.
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            }

            if guild.me is not None:
                overwrites[guild.me] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                )

            # Add permissions for each player
            for player_id in session["players"]:
                member = guild.get_member(player_id)
                if member:
                    overwrites[member] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                    )

            # Create the channel
            channel = await guild.create_text_channel(
                name=f"mafia-game-{guild_id}",
                overwrites=overwrites,
                reason="Mafia game channel",
            )

            session["game_channel_id"] = channel.id
            session["channel_id"] = channel.id
            return True, "Game channel created.", channel

        except discord.Forbidden:
            return (
                False,
                "I need permissions: Manage Channels and manage permissions.",
                None,
            )
        except discord.HTTPException as exc:
            return False, f"Failed to create channel: {exc}", None

    async def start_game_flow(self, ctx: commands.Context) -> Tuple[bool, str]:
        """Start complete game flow: channel creation, role assignment, DM notifications.
        
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

        success, message, roles = self.assign_roles(guild_id, mode=session.get("mode", "classic"))
        if not success:
            return False, message

        success, message, channel = await self.create_game_channel(guild, guild_id)
        if not success or channel is None:
            session["phase"] = "waiting"
            session["roles"] = {}
            session["role_objects"] = {}
            session["alive_players"] = []
            return False, message

        # First message in the newly created game channel.
        await channel.send("🎮 Mafia game has started!\nNight phase begins 🌙")

        failed_dms = await self.send_roles_dm(guild, roles)

        # Format player list with mentions
        player_mentions = "\n".join(f"<@{uid}>" for uid in session["players"])

        await channel.send(
            "🎮 Mafia Game Started\n\n"
            f"Players:\n{player_mentions}\n\n"
            "🌙 Night Phase Begins\n\n"
            "Check your DMs for your role."
        )

        if failed_dms:
            failed_mentions = " ".join(f"<@{uid}>" for uid in failed_dms)
            await channel.send(f"⚠️ Could not DM roles to: {failed_mentions}")

        task = asyncio.create_task(self._run_game_loop(guild, channel))
        self.game_tasks[guild_id] = task
        return True, "Game has started! Roles have been sent via DM 🌙"

    async def submit_night_action(
        self,
        guild_id: int,
        actor_id: int,
        target_id: Optional[int],
        action_type: str,
    ) -> Tuple[bool, str]:
        """Validate and queue one night action safely."""
        session = self._get_or_create_session(guild_id)

        if session["phase"] != "night":
            return False, "Night phase has ended."

        if actor_id not in session["alive_players"]:
            return False, "Dead players cannot act."

        action_aliases = {
            "kill": "kill",
            "heal": "protect",
            "investigate": "investigate",
            "utility": "utility",
            "redirect": "redirect",
            "delayed_kill": "delayed_kill",
        }
        internal_action_type = action_aliases.get(action_type)
        if internal_action_type is None:
            return False, "Unsupported action type."

        if target_id is None:
            if internal_action_type in {"kill", "protect", "investigate", "delayed_kill"}:
                return False, "This action requires a target."
        else:
            if target_id not in session["alive_players"]:
                return False, "Target is not alive."
            if actor_id == target_id:
                actor_role = session["roles"].get(actor_id)
                # Doctor may self-protect in this ruleset.
                if actor_role != "doctor":
                    return False, "You cannot target yourself."

        action_key = f"{actor_id}:{action_type}"
        if action_key in session["night_actions"]:
            return False, "You already submitted this action."

        actions: List[Action] = session.setdefault("actions", [])

        role_obj = session.get("role_objects", {}).get(actor_id)
        if role_obj is None:
            role_name = session["roles"].get(actor_id, "villager")
            role_obj = self.role_manager.create_role(role_name)
            session.setdefault("role_objects", {})[actor_id] = role_obj

        if not role_obj.can_use_action(internal_action_type):
            return False, "Your role cannot use this action."

        built_action = await role_obj.perform_action(session, actor_id, target_id)
        if built_action is None:
            return False, "Action could not be submitted for your role."

        if isinstance(built_action, list):
            queued = [a for a in built_action if isinstance(a, Action)]
        else:
            queued = [built_action] if isinstance(built_action, Action) else []

        if not queued:
            return False, "Action could not be submitted for your role."

        allowed_action_types = {
            "kill": {"kill"},
            "protect": {"protect"},
            "investigate": {"investigate", "investigate_exact"},
            "utility": {"utility"},
            "redirect": {"redirect", "utility"},
            "delayed_kill": {"delayed_kill_queue"},
        }
        for action in queued:
            if action.action_type not in allowed_action_types[internal_action_type]:
                return False, "Submitted action does not match role behavior."
            actions.append(action)

        session["night_actions"][action_key] = target_id
        return True, "Action submitted."

    async def _run_game_loop(self, guild: discord.Guild, channel: discord.TextChannel):
        """Main game loop: night → day → voting → repeat.
        
        Continues until win condition is met.
        
        Args:
            guild: Discord guild
            channel: Game channel for messages
        """
        guild_id = guild.id
        session = self._get_or_create_session(guild_id)
        
        try:
            while True:
                game_over = await self.run_night_phase(guild, channel)
                if game_over:
                    break

                await self.run_day_phase(guild_id, channel)

                game_over = await self.run_voting_phase(guild_id, guild, channel)
                if game_over:
                    break

                session = self._get_or_create_session(guild_id)
                session["day_count"] += 1
        finally:
            self.game_tasks.pop(guild_id, None)

            if session.get("manual_end"):
                return

            # Cleanup: delete game channel and session
            try:
                if session.get("game_channel_id"):
                    ch = guild.get_channel(session["game_channel_id"])
                    if ch:
                        await ch.delete()
            except discord.HTTPException as exc:
                logger.error("Failed to delete game channel: %s", exc)
            
            # Clear session
            if guild_id in self.game_sessions:
                del self.game_sessions[guild_id]

    async def end_game(self, guild: discord.Guild) -> Tuple[bool, str]:
        """Force-end a running game, cleanup channel, and reset session."""
        guild_id = guild.id
        session = self.game_sessions.get(guild_id)

        if not session or session.get("phase", "waiting") == "waiting":
            return False, "No game is currently running."

        session["manual_end"] = True

        task = self.game_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.error("Error while cancelling game task: %s", exc)

        channel_id = session.get("game_channel_id") or session.get("channel_id")
        if channel_id:
            game_channel = guild.get_channel(channel_id)
            if game_channel:
                try:
                    await game_channel.send("🏁 Game has been ended by admin.")
                    await asyncio.sleep(3)
                    await game_channel.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    logger.warning("Missing permissions to send/delete game channel during end_game.")
                except discord.HTTPException as exc:
                    logger.error("Failed while ending game channel: %s", exc)

        if guild_id in self.game_sessions:
            del self.game_sessions[guild_id]

        return True, "Game ended and session reset."

    async def run_night_phase(self, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        """Run night phase: show action buttons and wait for submissions.
        
        Args:
            guild: Discord guild
            channel: Game channel for messages
            
        Returns:
            True if game ends, False otherwise
        """
        guild_id = guild.id
        session = self._get_or_create_session(guild_id)
        session["phase"] = "night"
        session["night_actions"] = {}
        session["actions"] = []
        session["night_reports"] = {}

        await channel.send(
            "🌙 **Night Phase** has begun.\n\n"
            "Press **Perform Night Action** below.\n"
            "Your role determines what action is executed automatically.\n\n"
            "_Godfather: eliminate • Doctor: protect • Detective: investigate • Villager: no night action_",
            view=NightActionsView(self, guild, guild_id),
        )

        await asyncio.sleep(self.NIGHT_DURATION_SECONDS)
        await self.resolve_night(guild_id, guild, channel)
        return await self.check_win_conditions(guild_id, guild, channel)

    async def resolve_night(self, guild_id: int, guild: discord.Guild, channel: discord.TextChannel):
        """Resolve night phase: process kill/heal actions.
        
        Kill target dies unless healed.
        Heal target survives kill (if healed and killed same round).
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            channel: Game channel for messages
        """
        session = self._get_or_create_session(guild_id)
        resolution = resolve_actions(session.get("actions", []), session)

        killed_user_ids: List[int] = resolution.get("killed", [])
        investigations = resolution.get("investigations", {})
        exact_roles = resolution.get("exact_role_results", {})

        if not killed_user_ids:
            await channel.send("🌙 **Night Result**\n\nNobody died during the night.")
        else:
            lines = ["🌙 **Night Result**", ""]
            for victim_id in killed_user_ids:
                victim_name = get_player_display_name(guild, victim_id)
                victim_role = session["roles"].get(victim_id, "unknown")
                lines.append(f"**{victim_name}** died. Role: *{victim_role.title()}*")
            await channel.send("\n".join(lines))

        for actor_id, result in investigations.items():
            member = guild.get_member(actor_id)
            if member:
                try:
                    await member.send(f"🔍 Investigation result: **{result.title()}**")
                except (discord.Forbidden, discord.HTTPException):
                    pass

        for actor_id, role_name in exact_roles.items():
            member = guild.get_member(actor_id)
            if member:
                try:
                    await member.send(f"🧠 Consigliere result: target role is **{role_name.title()}**")
                except (discord.Forbidden, discord.HTTPException):
                    pass

    async def run_day_phase(self, guild_id: int, channel: discord.TextChannel):
        """Run day phase: discussion period before voting.
        
        Args:
            guild_id: Guild ID
            channel: Game channel for messages
        """
        session = self._get_or_create_session(guild_id)
        session["phase"] = "day"

        await channel.send(
            f"☀️ **Day Phase** - Day {session['day_count']}\n\n"
            "_Everyone can discuss who might be mafia. "
            "Voting will start soon._"
        )
        await asyncio.sleep(self.DAY_DURATION_SECONDS)

    async def run_voting_phase(self, guild_id: int, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        """Run voting phase: show vote buttons and process votes.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            channel: Game channel for messages
            
        Returns:
            True if game ends, False otherwise
        """
        session = self._get_or_create_session(guild_id)
        session["phase"] = "voting"
        session["votes"] = {}

        await channel.send(
            "🗳️ **Voting Phase** has started.\n\n"
            "_Click a button below to vote for elimination._",
            view=VotingView(self, guild, guild_id),
        )

        await asyncio.sleep(self.VOTING_DURATION_SECONDS)
        await self.resolve_votes(guild_id, guild, channel)
        return await self.check_win_conditions(guild_id, guild, channel)

    async def resolve_votes(self, guild_id: int, guild: discord.Guild, channel: discord.TextChannel):
        """Resolve voting: determine eliminated player by vote count.
        
        Ties are broken by lowest user ID.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            channel: Game channel for messages
        """
        session = self._get_or_create_session(guild_id)
        votes: Dict[int, int] = session["votes"]

        if not votes:
            await channel.send("🗳️ **Voting Result**\n\nNo votes were cast. Nobody is eliminated.")
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

        await channel.send(
            f"🗳️ **Voting Result**\n\n"
            f"**{eliminated_name}** has been eliminated.\n"
            f"Votes: {vote_count}\n"
            f"Role: *{eliminated_role.title()}*"
        )

    async def check_win_conditions(self, guild_id: int, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        """Check if game has ended and determine winner.
        
        Win conditions:
        - Villagers win if Godfather (mafia) is dead
        - Mafia wins if mafia_count >= villager_count
        
        Shows survivors, records stats, and deletes channel after game.
        
        Args:
            guild_id: Guild ID
            guild: Discord guild for member info
            channel: Game channel for messages
            
        Returns:
            True if game ended, False otherwise
        """
        session = self._get_or_create_session(guild_id)

        mafia_alive = []
        villagers_alive = []

        for player_id in session["alive_players"]:
            role = session["roles"].get(player_id)
            if role in self.mafia_role_names:
                mafia_alive.append(player_id)
            else:
                villagers_alive.append(player_id)

        winner: Optional[str] = None

        # Villagers win if Godfather is dead
        if len(mafia_alive) == 0:
            session["phase"] = "ended"
            winner = "Villagers"

        # Mafia wins if mafia >= villagers
        elif len(mafia_alive) >= len(villagers_alive):
            session["phase"] = "ended"
            winner = "Mafia"

        if winner is None:
            return False

        # Build survivor list
        survivor_names = [
            get_player_display_name(guild, pid) for pid in session["alive_players"]
        ]
        survivor_text = "\n".join(survivor_names) if survivor_names else "_None_"

        # Send game over message
        await channel.send(
            f"🏆 **GAME OVER**\n\n"
            f"**Winner: {winner}**\n\n"
            f"Survivors:\n{survivor_text}"
        )

        # Update player profiles if profile service is available
        if self.profile_service:
            try:
                winners = mafia_alive if winner == "Mafia" else villagers_alive
                losers = villagers_alive if winner == "Mafia" else mafia_alive

                await self.profile_service.record_game_end(
                    village_player_ids=villagers_alive,
                    mafia_player_ids=mafia_alive,
                    winner=winner.lower(),
                    roles=session["roles"],
                )
            except Exception as exc:
                logger.error("Failed to record game stats: %s", exc)

        # Wait before deleting channel (gives time to read results)
        await asyncio.sleep(10)

        # Delete the game channel
        try:
            await channel.delete()
        except discord.HTTPException as exc:
            logger.error("Failed to delete game channel: %s", exc)

        return True
