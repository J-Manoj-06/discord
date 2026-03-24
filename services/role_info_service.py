"""Role info service for command and DM role explanations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import discord

from roles.base_role import MAFIA, NEUTRAL, SPECIAL, VILLAGE
from roles.role_manager import RoleManager


@dataclass(frozen=True)
class RoleInfo:
    """Structured role information used in embeds."""

    role: str
    team: str
    goal: str
    visit_type: str
    abilities: str
    notes: str
    special_interactions: str = "None"


class RoleInfoService:
    """Build role details and embeds for all registered roles."""

    TEAM_GOALS = {
        VILLAGE: "Eliminate all threats to the village.",
        MAFIA: "Outnumber and eliminate the village.",
        NEUTRAL: "Complete your unique personal win condition.",
        SPECIAL: "Use special mechanics to swing the game.",
    }

    VISIT_MAP = {
        "kill": "Active Visit",
        "protect": "Active Visit",
        "investigate": "Active Visit",
        "redirect": "Active Visit",
        "delayed_kill": "Active Visit",
        "utility": "Passive / Utility",
        "block": "Active Visit",
    }

    DISPLAY_NAME_MAP = {
        "serialkiller": "Serial Killer",
        "guardianangel": "Guardian Angel",
        "timetraveler": "Time Traveler",
    }

    ROLE_ABILITIES: Dict[str, str] = {
        "villager": "No night action. Participate in discussion and day voting to find evil roles.",
        "detective": "Investigate one target each night to learn alignment-related information.",
        "doctor": "Protect one target at night to prevent kill effects.",
        "bodyguard": "Guard one target and absorb or prevent attacks directed at them.",
        "sheriff": "Check a target for suspicious behavior and gather alignment clues.",
        "mayor": "Day-focused influence role with stronger social and voting impact.",
        "tracker": "Track one target at night to learn who they visited.",
        "lookout": "Watch one target and learn who visited them during the night.",
        "guardianangel": "Support and protect a designated player with defensive utility.",
        "spy": "Gather hidden action information and expose hostile intent.",
        "medium": "Gain information through spiritual/dead-player interaction mechanics.",
        "godfather": "Lead the mafia faction and submit lethal night action pressure.",
        "mafia": "Work with mafia teammates to control eliminations and outnumber village.",
        "assassin": "High-pressure offensive mafia role focused on efficient eliminations.",
        "framer": "Manipulate investigation outcomes by framing targets as suspicious.",
        "disguiser": "Conceal or alter identity-related information to mislead investigators.",
        "consigliere": "Investigative mafia support role that discovers target role details.",
        "poisoner": "Apply delayed lethal effects that trigger after poison resolution timing.",
        "silencer": "Mute or suppress a target to reduce their day-phase influence.",
        "jester": "Neutral chaos role that aims to be eliminated by vote to win.",
        "serialkiller": "Independent killer who eliminates targets and survives to endgame.",
        "executioner": "Manipulate the game so your assigned target is eliminated.",
        "arsonist": "Douse players and ignite later for multi-target elimination.",
        "vampire": "Neutral conversion role that grows faction strength by transforming others.",
        "submissor": "No active action. First attacker converts you; if master dies, you inherit their role.",
        "baker": "Give bread nightly. Bread applies random effects and supports Baker-specific win condition.",
        "baiter": "Punish or influence players who target you through reactive mechanics.",
        "timetraveler": "Manipulate sequencing/timing to alter expected action outcomes.",
        "gambler": "Risk-reward role with volatile outcomes based on selected plays.",
        "shapeshifter": "Copy or alter role behavior to confuse enemy reads.",
        "magnet": "Redirect or attract actions to specific targets.",
        "trickster": "Deception-focused role that distorts assumptions and information.",
    }

    ROLE_NOTES: Dict[str, str] = {
        "detective": "• Some evil roles can appear innocent depending on modifiers.\n• You cannot investigate yourself.",
        "doctor": "• Self-targeting may be restricted by role rules.\n• Protection does not guarantee safety against every kill type.",
        "godfather": "• Usually appears less suspicious to some investigations.\n• Coordinate with mafia team roles.",
        "baker": "• Bread effects can include heal, distract, extra vote, or no vote.\n• Bread-based effects are phase-limited.",
        "submissor": "• First attack converts instead of killing.\n• Second lethal hit can kill normally.",
    }

    ROLE_SPECIALS: Dict[str, str] = {
        "baker": "Necronomicon: If owned at baker victory trigger, breaded alive players can be poisoned and die.",
        "submissor": "Conversion/Inherit: First attacker becomes your master; when master dies, you inherit their role.",
        "framer": "Framed targets may appear suspicious to investigative checks.",
        "silencer": "Silenced players can lose communication ability during day phases.",
    }

    def __init__(self):
        self.role_manager = RoleManager()

    def normalize_role(self, role_name: str) -> str:
        return role_name.strip().lower().replace(" ", "")

    def role_exists(self, role_name: str) -> bool:
        return self.normalize_role(role_name) in self.role_manager.roles

    def display_name(self, role_name: str) -> str:
        key = self.normalize_role(role_name)
        if key in self.DISPLAY_NAME_MAP:
            return self.DISPLAY_NAME_MAP[key]
        return key.replace("_", " ").title()

    def _goal_for_team(self, team: str) -> str:
        return self.TEAM_GOALS.get(team, "Survive and complete your role objective.")

    def _visit_type(self, action_type: str) -> str:
        return self.VISIT_MAP.get(action_type, "Passive / Utility")

    def get_role_info(self, role_name: str) -> Optional[RoleInfo]:
        key = self.normalize_role(role_name)
        if key not in self.role_manager.roles:
            return None

        role_obj = self.role_manager.create_role(key)
        team = role_obj.team.title()
        goal = self._goal_for_team(role_obj.team)
        visit_type = self._visit_type(getattr(role_obj, "action_type", "utility"))
        abilities = self.ROLE_ABILITIES.get(key, role_obj.description())
        notes = self.ROLE_NOTES.get(key, "• Role interactions can change outcomes based on night resolution order.")
        special_interactions = self.ROLE_SPECIALS.get(key, "None")

        return RoleInfo(
            role=self.display_name(key),
            team=team,
            goal=goal,
            visit_type=visit_type,
            abilities=abilities,
            notes=notes,
            special_interactions=special_interactions,
        )

    def build_embed(self, role_name: str, title: str = "🎭 Role Information") -> Optional[discord.Embed]:
        info = self.get_role_info(role_name)
        if info is None:
            return None

        embed = discord.Embed(title=title, color=discord.Color.dark_red())
        embed.add_field(name="Role", value=info.role, inline=False)
        embed.add_field(name="Team", value=info.team, inline=True)
        embed.add_field(name="Visit Type", value=info.visit_type, inline=True)
        embed.add_field(name="Goal", value=info.goal, inline=False)
        embed.add_field(name="Ability", value=info.abilities, inline=False)
        embed.add_field(name="Special Interactions", value=info.special_interactions, inline=False)
        embed.add_field(name="Notes", value=info.notes, inline=False)
        return embed
