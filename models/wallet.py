from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Wallet:
    user_id: int
    guild_id: int
    coins: int = 0
    gems: int = 0
    total_wins: int = 0
    total_losses: int = 0
    games_played: int = 0
    votes_cast: int = 0
    created_at: Optional[datetime] = None
    last_daily_claim: Optional[datetime] = None
