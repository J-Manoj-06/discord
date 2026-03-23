"""Game Service: Complete Mafia game flow with phases and button-based actions."""

import asyncio
import random
from collections import Counter
from typing import Dict, List, Optional, Tuple

import discord
from discord.ext import commands


class NightTargetSelect(discord.ui.Select):
    """Select menu used after clicking a night action button."""

    def __init__(self, game_service: "GameService", guild_id: int, actor_id: int, action_type: str):
        self.game_service = game_service
        self.guild_id = guild_id
        self.actor_id = actor_id
        self.action_type = action_type

        session = self.game_service.get_session(guild_id)
        options: List[discord.SelectOption] = []
        for player_id in session["alive_players"]:
            options.append(discord.SelectOption(label=f"Player {player_id}", value=str(player_id)))

        super().__init__(
            placeholder="Select a target",
            min_values=1,
            max_values=1,
            options=options[:25],
        )

    async def callback(self, interaction: discord.Interaction):
        session = self.game_service.get_session(self.guild_id)
        if session["phase"] != "night":
            await interaction.response.send_message("❌ Night phase already ended.", ephemeral=True)
            return

        if interaction.user.id != self.actor_id:
            await interaction.response.send_message("❌ This action menu is not for you.", ephemeral=True)
            return

        if interaction.user.id not in session["alive_players"]:
            await interaction.response.send_message("❌ Dead players cannot act.", ephemeral=True)
            return

        if self.action_type in session["night_actions"]:
            await interaction.response.send_message("❌ This action has already been submitted.", ephemeral=True)
            return

        target_id = int(self.values[0])
        session["night_actions"][self.action_type] = target_id

        if self.action_type == "investigate":
            target_role = session["roles"].get(target_id, "unknown")
            await interaction.response.send_message(
                f"🔍 Investigation result: <@{target_id}> is **{target_role}**.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ {self.action_type.title()} target saved: <@{target_id}>.",
            ephemeral=True,
        )


class NightTargetView(discord.ui.View):
    """Container view for night target selection."""

    def __init__(self, game_service: "GameService", guild_id: int, actor_id: int, action_type: str):
        super().__init__(timeout=45)
        self.add_item(NightTargetSelect(game_service, guild_id, actor_id, action_type))


class NightActionButton(discord.ui.Button):
    """Role-specific button for night action."""

    def __init__(
        self,
        game_service: "GameService",
        guild_id: int,
        action_type: str,
        required_role: str,
        label: str,
        emoji: str,
    ):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
        self.game_service = game_service
        self.guild_id = guild_id
        self.action_type = action_type
        self.required_role = required_role

    async def callback(self, interaction: discord.Interaction):
        session = self.game_service.get_session(self.guild_id)

        if session["phase"] != "night":
            await interaction.response.send_message("❌ Night phase is not active.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in session["alive_players"]:
            await interaction.response.send_message("❌ Dead players cannot act.", ephemeral=True)
            return

        role = session["roles"].get(user_id)
        if role != self.required_role:
            await interaction.response.send_message("❌ You cannot use this action.", ephemeral=True)
            return

        if self.action_type in session["night_actions"]:
            await interaction.response.send_message("❌ This action was already submitted.", ephemeral=True)
            return

        view = NightTargetView(self.game_service, self.guild_id, user_id, self.action_type)
        await interaction.response.send_message("Select your target:", view=view, ephemeral=True)


class NightActionsView(discord.ui.View):
    """Main night action button panel."""

    def __init__(self, game_service: "GameService", guild_id: int):
        super().__init__(timeout=60)
        self.add_item(NightActionButton(game_service, guild_id, "kill", "godfather", "Kill", "🔪"))
        self.add_item(NightActionButton(game_service, guild_id, "heal", "doctor", "Heal", "💉"))
        self.add_item(NightActionButton(game_service, guild_id, "investigate", "detective", "Investigate", "🔍"))


class VoteButton(discord.ui.Button):
    """Vote button for a single target player."""

    def __init__(self, game_service: "GameService", guild_id: int, target_id: int):
        super().__init__(
            label=f"Vote @{target_id}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"vote_{guild_id}_{target_id}",
        )
        self.game_service = game_service
        self.guild_id = guild_id
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        session = self.game_service.get_session(self.guild_id)

        if session["phase"] != "voting":
            await interaction.response.send_message("❌ Voting phase is not active.", ephemeral=True)
            return

        voter_id = interaction.user.id
        if voter_id not in session["alive_players"]:
            await interaction.response.send_message("❌ Dead players cannot vote.", ephemeral=True)
            return

        if voter_id in session["votes"]:
            await interaction.response.send_message("❌ You already voted.", ephemeral=True)
            return

        if self.target_id not in session["alive_players"]:
            await interaction.response.send_message("❌ That player is no longer alive.", ephemeral=True)
            return

        session["votes"][voter_id] = self.target_id
        await interaction.response.send_message(f"✅ Vote submitted for <@{self.target_id}>.", ephemeral=True)


class VotingView(discord.ui.View):
    """Voting panel with one button per alive player."""

    def __init__(self, game_service: "GameService", guild_id: int):
        super().__init__(timeout=60)
        session = game_service.get_session(guild_id)
        for target_id in session["alive_players"][:25]:
            self.add_item(VoteButton(game_service, guild_id, target_id))


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

        player_mentions = "\n".join(f"<@{uid}>" for uid in session["players"])
        await thread.send(
            "🎮 Mafia Game Started!\n\n"
            f"Players:\n{player_mentions}\n\n"
            "The game begins with **Night Phase**.\n\n"
            "Check your DMs for your role."
        )

        if failed_dms:
            failed_mentions = " ".join(f"<@{uid}>" for uid in failed_dms)
            await thread.send(f"⚠️ Could not DM roles to: {failed_mentions}")

        task = asyncio.create_task(self._run_game_loop(guild, thread))
        self.game_tasks[guild_id] = task
        return True, "Game has started! Roles have been sent via DM 🌙"

    async def _run_game_loop(self, guild: discord.Guild, thread: discord.Thread):
        guild_id = guild.id
        try:
            while True:
                game_over = await self.run_night_phase(guild, thread)
                if game_over:
                    break

                await self.run_day_phase(guild_id, thread)

                game_over = await self.run_voting_phase(guild_id, thread)
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
        guild_id = guild.id
        session = self._get_or_create_session(guild_id)
        session["phase"] = "night"
        session["night_actions"] = {}

        await thread.send(
            "🌙 Night Phase has begun.\n"
            "Role actions: 🔪 Kill (Godfather), 💉 Heal (Doctor), 🔍 Investigate (Detective).",
            view=NightActionsView(self, guild_id),
        )

        await asyncio.sleep(self.NIGHT_DURATION_SECONDS)
        await self.resolve_night(guild_id, thread)
        return await self.check_win_conditions(guild_id, thread)

    async def resolve_night(self, guild_id: int, thread: discord.Thread):
        session = self._get_or_create_session(guild_id)
        night_actions = session["night_actions"]

        kill_target = night_actions.get("kill")
        heal_target = night_actions.get("heal")

        killed_user_id: Optional[int] = None
        if kill_target is not None and kill_target != heal_target:
            if kill_target in session["alive_players"]:
                session["alive_players"].remove(kill_target)
                killed_user_id = kill_target

        if killed_user_id is None:
            await thread.send("🌙 Night Result\n\nNobody died during the night.")
        else:
            await thread.send(f"🌙 Night Result\n\n<@{killed_user_id}> was killed during the night.")

    async def run_day_phase(self, guild_id: int, thread: discord.Thread):
        session = self._get_or_create_session(guild_id)
        session["phase"] = "day"
        await thread.send("☀️ Day Phase has begun.\nDiscuss who might be the mafia.")
        await asyncio.sleep(self.DAY_DURATION_SECONDS)

    async def run_voting_phase(self, guild_id: int, thread: discord.Thread) -> bool:
        session = self._get_or_create_session(guild_id)
        session["phase"] = "voting"
        session["votes"] = {}

        await thread.send("🗳️ Voting Phase has started. Choose who to eliminate.", view=VotingView(self, guild_id))

        await asyncio.sleep(self.VOTING_DURATION_SECONDS)
        await self.resolve_votes(guild_id, thread)
        return await self.check_win_conditions(guild_id, thread)

    async def resolve_votes(self, guild_id: int, thread: discord.Thread):
        session = self._get_or_create_session(guild_id)
        votes: Dict[int, int] = session["votes"]

        if not votes:
            await thread.send("🗳️ Voting Result\n\nNo votes were cast. Nobody is eliminated.")
            return

        counts = Counter(votes.values())
        max_votes = max(counts.values())
        top_targets = [target_id for target_id, count in counts.items() if count == max_votes]

        eliminated_id = sorted(top_targets)[0]
        if eliminated_id in session["alive_players"]:
            session["alive_players"].remove(eliminated_id)

        await thread.send(f"🗳️ Voting Result\n\n<@{eliminated_id}> has been eliminated.")

    async def check_win_conditions(self, guild_id: int, thread: discord.Thread) -> bool:
        session = self._get_or_create_session(guild_id)

        mafia_alive = 0
        villager_alive = 0
        for player_id in session["alive_players"]:
            role = session["roles"].get(player_id)
            if role == "godfather":
                mafia_alive += 1
            else:
                villager_alive += 1

        if mafia_alive == 0:
            session["phase"] = "ended"
            await thread.send("🏆 Game Over!\n\nWinner: Villagers")
            return True

        if mafia_alive >= villager_alive:
            session["phase"] = "ended"
            await thread.send("🏆 Game Over!\n\nWinner: Mafia")
            return True

        return False
