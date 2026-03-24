from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class UserProfile:
    user_id: int
    guild_id: int
    display_name: str = "Unknown"
    avatar_url: str = ""
    level: int = 1
    xp: int = 0
    current_title: Optional[str] = None
    selected_profile_theme: str = "default"
    selected_vote_effect: str = "default"
    unlocked_cosmetics: List[str] = field(default_factory=lambda: ["title:rookie", "theme:default", "vote_effect:default"])
    favorite_role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    wins: int = 0
    losses: int = 0
    games_played: int = 0
    equipped_title: Optional[str] = None
    equipped_theme: str = "classic_theme"
    votes_cast: int = 0
    roles_played: Dict[str, int] = field(default_factory=dict)
