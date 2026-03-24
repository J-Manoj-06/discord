"""Night action resolution engine for Mafia roles.

This module keeps resolution rules centralized so new roles can be added without
changing game loop logic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Action:
    """A single scheduled night action."""

    actor: int
    target: Optional[int]
    action_type: str
    priority: int
    role_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResolutionState:
    """Mutable state while resolving one night."""

    def __init__(self, game: Dict[str, Any]):
        self.game = game
        self.alive = set(game.get("alive_players", []))
        self.killed: List[int] = []
        self.protected: set[int] = set()
        self.bodyguard_for: Dict[int, int] = {}
        self.framed_targets: set[int] = set(game.get("framed_targets", []))
        self.investigation_results: Dict[int, str] = {}
        self.exact_role_results: Dict[int, str] = {}
        self.blocked: set[int] = set()
        self.redirect_targets: Dict[int, int] = {}
        self.silenced_players: set[int] = set(game.get("silenced_players", []))
        self.messages: List[str] = []
        self.death_causes: Dict[int, str] = {}
        self.submissor_events: List[Dict[str, Any]] = []
        self.bread_events: List[Dict[str, Any]] = []


def _team_from_attacker_role(game: Dict[str, Any], attacker_role: str) -> str:
    """Map attacker role to team label used by submissor conversion state."""
    if attacker_role in game.get("mafia_role_names", set()):
        return "mafia"
    if attacker_role in game.get("village_role_names", set()):
        return "town"
    if attacker_role in game.get("neutral_role_names", set()):
        return "neutral"
    return "neutral"


def _safe_target(action: Action, state: ResolutionState) -> bool:
    """Safety validation for alive/target/self checks."""
    if action.actor not in state.alive:
        return False

    if action.target is None:
        return action.action_type in {"utility", "block", "redirect"}

    if action.target == action.actor:
        # Doctor can self-target in this ruleset.
        if not (action.action_type == "protect" and action.role_name == "doctor"):
            return False

    if action.target not in state.alive:
        return False

    return True


def _tick_delayed_effects(game: Dict[str, Any]) -> List[Action]:
    """Advance queued delayed effects and emit actions that trigger this night."""
    pending = game.setdefault("pending_effects", [])
    next_pending: List[Dict[str, Any]] = []
    emitted: List[Action] = []

    for effect in pending:
        effect_type = effect.get("type")
        if effect_type != "poison":
            next_pending.append(effect)
            continue

        nights_left = int(effect.get("nights_left", 1)) - 1
        if nights_left <= 0:
            emitted.append(
                Action(
                    actor=int(effect.get("source", 0)),
                    target=effect.get("target"),
                    action_type="delayed_kill",
                    priority=5,
                    role_name="poisoner",
                    metadata={"delayed": True},
                )
            )
        else:
            effect["nights_left"] = nights_left
            next_pending.append(effect)

    game["pending_effects"] = next_pending
    return emitted


def execute_action(action: Action, state: ResolutionState) -> None:
    """Execute one action under conflict rules."""
    if action.actor in state.blocked:
        return

    target = action.target
    if target in state.redirect_targets:
        target = state.redirect_targets[target]

    if action.action_type == "protect":
        if action.role_name == "doctor" and target is not None:
            state.protected.add(target)
        elif action.role_name == "bodyguard" and target is not None:
            state.bodyguard_for[target] = action.actor
        elif action.role_name == "guardianangel":
            fixed_target = action.metadata.get("fixed_target")
            if fixed_target in state.alive:
                state.protected.add(fixed_target)
        return

    if action.action_type == "block":
        if target is not None:
            state.blocked.add(target)
        return

    if action.action_type == "redirect":
        if action.role_name == "framer" and target is not None:
            state.framed_targets.add(target)
            return
        if action.role_name == "trickster":
            actor_target_map = state.game.get("trickster_redirect", {})
            if isinstance(actor_target_map, dict):
                state.redirect_targets.update(actor_target_map)
        return

    if action.action_type in {"kill", "delayed_kill"}:
        if target is None or target not in state.alive:
            return

        # Baker heal protects only from mafia attacks.
        if (
            target in state.game.get("bread_heal_targets", set())
            and action.role_name in state.game.get("mafia_role_names", set())
        ):
            return

        target_role = state.game.get("roles", {}).get(target)
        if target_role == "submissor":
            submissor_state = state.game.setdefault("submissor_state", {}).setdefault(
                target,
                {
                    "role": "submissor",
                    "team": "neutral",
                    "alive": True,
                    "converted": False,
                    "master": None,
                    "first_attacker": None,
                    "inherited": False,
                },
            )

            if not submissor_state.get("converted", False):
                attacker_role = state.game.get("roles", {}).get(action.actor, action.role_name)
                submissor_state["converted"] = True
                submissor_state["first_attacker"] = action.actor
                submissor_state["master"] = action.actor
                submissor_state["team"] = _team_from_attacker_role(
                    state.game,
                    attacker_role or "",
                )
                state.submissor_events.append(
                    {
                        "type": "converted",
                        "submissor": target,
                        "attacker": action.actor,
                        "team": submissor_state["team"],
                    }
                )
                # First attack is intercepted and does not kill.
                return

        if target in state.protected:
            return

        guard = state.bodyguard_for.get(target)
        if guard is not None and guard in state.alive:
            if guard not in state.killed:
                state.killed.append(guard)
                state.death_causes[guard] = "bodyguard"
            return

        if target not in state.killed:
            state.killed.append(target)
            state.death_causes[target] = action.role_name or action.action_type

            if target_role == "submissor":
                sub_state = state.game.setdefault("submissor_state", {}).setdefault(target, {})
                sub_state["alive"] = False
        return

    if action.action_type == "delayed_kill_queue":
        if target is not None:
            state.game.setdefault("pending_effects", []).append(
                {
                    "type": "poison",
                    "target": target,
                    "source": action.actor,
                    "nights_left": int(action.metadata.get("nights_left", 1)),
                }
            )
        return

    if action.action_type == "investigate":
        if target is None:
            return

        roles = state.game.get("roles", {})
        role_name = roles.get(target, "unknown")

        if target in state.framed_targets:
            state.investigation_results[action.actor] = "suspicious"
            return

        if role_name == "godfather":
            state.investigation_results[action.actor] = "innocent"
            return

        is_mafia = role_name in state.game.get("mafia_role_names", set())
        state.investigation_results[action.actor] = "suspicious" if is_mafia else "innocent"
        return

    if action.action_type == "investigate_exact":
        if target is None:
            return
        role_name = state.game.get("roles", {}).get(target, "unknown")
        state.exact_role_results[action.actor] = role_name
        return

    if action.action_type == "utility":
        if action.role_name == "baker" and target is not None:
            bread_players = state.game.setdefault("bread_players", set())
            if target in bread_players:
                return

            bread_players.add(target)

            player_states = state.game.setdefault("player_states", {})
            target_state = player_states.setdefault(
                target,
                {
                    "role": state.game.get("roles", {}).get(target, "unknown"),
                    "has_bread": False,
                    "bread_effect": None,
                },
            )
            target_state["has_bread"] = True

            effect = random.choice(["extra_vote", "heal", "distract", "no_vote"])
            target_state["bread_effect"] = effect

            if effect == "heal":
                state.game.setdefault("bread_heal_targets", set()).add(target)
            elif effect == "distract":
                state.blocked.add(target)
            elif effect in {"extra_vote", "no_vote"}:
                state.game.setdefault("bread_vote_effects", {})[target] = effect

            state.bread_events.append(
                {
                    "baker": action.actor,
                    "target": target,
                    "effect": effect,
                }
            )
            return

        if action.role_name == "silencer" and target is not None:
            state.silenced_players.add(target)
        if action.role_name == "timetraveler":
            if not state.game.get("time_travel_used", False):
                history = state.game.get("death_history", [])
                if history:
                    revived = history[-1]
                    if revived not in state.alive:
                        state.alive.add(revived)
                    state.game["time_travel_used"] = True
        if action.role_name == "magnet":
            forced = action.metadata.get("forced_target")
            if forced is not None:
                state.game["forced_vote_target"] = forced
        return


def resolve_actions(actions: List[Action], game: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve all queued actions for the night by priority order."""
    state = ResolutionState(game)

    delayed_actions = _tick_delayed_effects(game)
    all_actions = list(actions) + delayed_actions
    all_actions.sort(key=lambda x: x.priority)

    valid_actions: List[Action] = []
    for action in all_actions:
        if _safe_target(action, state):
            valid_actions.append(action)

    for action in valid_actions:
        execute_action(action, state)

    alive_players = [pid for pid in game.get("alive_players", []) if pid not in set(state.killed)]
    game["alive_players"] = alive_players
    game["framed_targets"] = list(state.framed_targets)
    game["silenced_players"] = list(state.silenced_players)
    game.setdefault("death_history", []).extend(state.killed)

    return {
        "killed": state.killed,
        "investigations": state.investigation_results,
        "exact_role_results": state.exact_role_results,
        "silenced": list(state.silenced_players),
        "messages": state.messages,
        "death_causes": state.death_causes,
        "submissor_events": state.submissor_events,
        "bread_events": state.bread_events,
    }
