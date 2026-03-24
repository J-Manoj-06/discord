"""Role registry, mode presets, and role assignment logic."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Tuple

from .base_role import MAFIA, NEUTRAL, SPECIAL, VILLAGE, Role
from .mafia_roles import Assassin, Consigliere, Disguiser, Framer, Godfather, Mafia, Poisoner, Silencer
from .neutral_roles import Arsonist, Executioner, Jester, SerialKiller, Vampire
from .special_roles import Gambler, Magnet, Shapeshifter, TimeTraveler, Trickster
from .village_roles import Bodyguard, Detective, Doctor, GuardianAngel, Lookout, Mayor, Medium, Sheriff, Spy, Tracker, Villager


GAME_MODES = {
    "classic": [
        "godfather", "mafia", "detective", "doctor", "villager",
    ],
    "advanced": [
        "godfather", "mafia", "detective", "doctor", "bodyguard", "framer", "jester",
    ],
    "chaos": "ALL",
}


class RoleManager:
    """Creates role objects and assigns balanced sets by mode."""

    def __init__(self):
        self.roles = {
            "villager": Villager,
            "detective": Detective,
            "doctor": Doctor,
            "bodyguard": Bodyguard,
            "sheriff": Sheriff,
            "mayor": Mayor,
            "tracker": Tracker,
            "lookout": Lookout,
            "guardianangel": GuardianAngel,
            "spy": Spy,
            "medium": Medium,
            "godfather": Godfather,
            "mafia": Mafia,
            "assassin": Assassin,
            "framer": Framer,
            "disguiser": Disguiser,
            "consigliere": Consigliere,
            "poisoner": Poisoner,
            "silencer": Silencer,
            "jester": Jester,
            "serialkiller": SerialKiller,
            "executioner": Executioner,
            "arsonist": Arsonist,
            "vampire": Vampire,
            "timetraveler": TimeTraveler,
            "gambler": Gambler,
            "shapeshifter": Shapeshifter,
            "magnet": Magnet,
            "trickster": Trickster,
        }

    def create_role(self, role_name: str) -> Role:
        role_cls = self.roles.get(role_name.lower())
        if role_cls is None:
            raise ValueError(f"Unknown role: {role_name}")
        return role_cls()

    def role_team(self, role_name: str) -> str:
        return self.create_role(role_name).team

    def mafia_role_names(self) -> set[str]:
        names = set()
        for role_name in self.roles:
            if self.role_team(role_name) == MAFIA:
                names.add(role_name)
        return names

    def _all_role_names(self) -> List[str]:
        return list(self.roles.keys())

    def _team_bucket(self, team: str) -> List[str]:
        return [name for name in self.roles if self.role_team(name) == team]

    def _balanced_counts(self, player_count: int) -> Tuple[int, int, int, int]:
        """Return mafia, village, neutral, special counts for chaos mode.

        Targets:
        - mafia: 25-30%
        - village: 50-60%
        - neutral: 10-20%
        - special: remainder for variety
        """
        mafia = max(1, round(player_count * 0.27))
        village = max(1, round(player_count * 0.53))
        neutral = max(0, round(player_count * 0.15))

        total = mafia + village + neutral
        special = player_count - total

        if special < 0:
            neutral = max(0, neutral + special)
            special = 0

        while mafia + village + neutral + special < player_count:
            village += 1

        return mafia, village, neutral, special

    def _is_unique_role(self, role_name: str) -> bool:
        return self.create_role(role_name).unique

    def _expand_mode_pool(self, mode: str, player_count: int) -> List[str]:
        mode = mode.lower()
        configured = GAME_MODES.get(mode, GAME_MODES["classic"])

        if configured == "ALL":
            return self._build_chaos_pool(player_count)

        pool = list(configured)
        while len(pool) < player_count:
            pool.append("villager")
        return pool[:player_count]

    def _build_chaos_pool(self, player_count: int) -> List[str]:
        mafia_count, village_count, neutral_count, special_count = self._balanced_counts(player_count)

        pool: List[str] = []
        pool.extend(self._pick_from_bucket(self._team_bucket(MAFIA), mafia_count))
        pool.extend(self._pick_from_bucket(self._team_bucket(VILLAGE), village_count))
        pool.extend(self._pick_from_bucket(self._team_bucket(NEUTRAL), neutral_count))
        pool.extend(self._pick_from_bucket(self._team_bucket(SPECIAL), special_count))

        while len(pool) < player_count:
            pool.append("villager")

        random.shuffle(pool)
        return pool[:player_count]

    def _pick_from_bucket(self, bucket: Iterable[str], amount: int) -> List[str]:
        names = list(bucket)
        unique_roles = [name for name in names if self._is_unique_role(name)]
        non_unique_roles = [name for name in names if not self._is_unique_role(name)]

        picks: List[str] = []
        if amount <= 0:
            return picks

        random.shuffle(unique_roles)
        picks.extend(unique_roles[: min(len(unique_roles), amount)])

        while len(picks) < amount:
            if non_unique_roles:
                picks.append(random.choice(non_unique_roles))
            elif unique_roles:
                # Fallback when bucket only has unique roles.
                picks.append(random.choice(unique_roles))
            else:
                break

        return picks

    def assign_roles(self, players: List[int], mode: str = "classic") -> Dict[int, Role]:
        """Select and assign role objects for each player by mode."""
        if not players:
            return {}

        shuffled_players = players[:]
        random.shuffle(shuffled_players)

        role_names = self._expand_mode_pool(mode, len(players))
        random.shuffle(role_names)

        assigned: Dict[int, Role] = {}
        used_unique: set[str] = set()

        for player_id, role_name in zip(shuffled_players, role_names):
            role_name = role_name.lower()
            if self._is_unique_role(role_name) and role_name in used_unique:
                role_name = "villager"

            role_obj = self.create_role(role_name)
            assigned[player_id] = role_obj
            if role_obj.unique:
                used_unique.add(role_obj.name)

        return assigned
