import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    discord_token: str
    mongo_uri: str
    mongo_db_name: str
    command_prefix: str = "!"
    daily_reward_coins: int = 500
    daily_cooldown_hours: int = 24
    level_up_coin_reward: int = 50


    @classmethod
    def from_env(cls) -> "Settings":
        discord_token = os.getenv("DISCORD_TOKEN", "")
        mongo_uri = os.getenv("MONGODB_URI", "")
        mongo_db_name = os.getenv("MONGO_DB_NAME", "discord_bot")
        command_prefix = os.getenv("COMMAND_PREFIX", "!")

        daily_reward_coins = int(os.getenv("DAILY_REWARD_COINS", "500"))
        daily_cooldown_hours = int(os.getenv("DAILY_COOLDOWN_HOURS", "24"))
        level_up_coin_reward = int(os.getenv("LEVEL_UP_COIN_REWARD", "50"))

        if not discord_token:
            raise ValueError("DISCORD_TOKEN is required")
        if not mongo_uri:
            raise ValueError("MONGODB_URI is required")

        return cls(
            discord_token=discord_token,
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            command_prefix=command_prefix,
            daily_reward_coins=daily_reward_coins,
            daily_cooldown_hours=daily_cooldown_hours,
            level_up_coin_reward=level_up_coin_reward,
        )
