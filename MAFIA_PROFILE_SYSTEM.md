# Mafia Profile System Implementation

## Overview
Complete implementation of player profiles and game statistics tracking for the Discord Mafia bot using MongoDB persistent storage.

## Features Implemented

### 1. Game Statistics Tracking
- **Games Played**: Total number of Mafia games participated in
- **Wins**: Total number of games won (village or mafia depending on role)
- **Losses**: Total number of games lost
- **Win Rate**: Percentage of games won (automatically calculated)
- **Last Role**: Last role played in a Mafia game (Godfather, Medic, Cop, Villager)

### 2. MongoDB Database Structure
**Collection**: `mafia_game_stats` (auto-created on first use)

```json
{
  "user_id": 140903874832,
  "games_played": 12,
  "wins": 7,
  "losses": 5,
  "last_role": "godfather"
}
```

### 3. Profile Command
**Command Name**: `!mprofile` (renamed to avoid conflict with existing `!profile` economy command)

**Usage**: `!mprofile` or `!mprofile @username`

**Output**: Discord Embed showing:
```
🎮 Mafia Game Profile
Statistics for PlayerName

📊 Games Played: 12
🏆 Wins: 7
💀 Losses: 5
📈 Win Rate: 58.3%
🎭 Last Role: Godfather
User ID: 123456789
```

## Files Created/Modified

### New Files
1. **`database/repositories/mafia_game_stats_repository.py`**
   - MongoDB repository for game statistics
   - Methods: get_or_create_stats, increment_game_played, increment_win/loss, update_last_role
   - Batch operations: batch_increment_wins, batch_increment_losses

2. **`services/mafia_profile_service.py`**
   - Service layer for profile logic
   - Methods: get_player_stats, calculate_win_rate, record_game_end, get_leaderboard
   - Handles all stat updates and calculations

3. **`bot/commands/profile.py`**
   - Discord command cog for `!mprofile` command
   - Uses MafiaProfileService to fetch and display stats
   - Rich embed formatting with user avatar

### Modified Files
1. **`services/game_service.py`**
   - Added `profile_service` parameter to constructor
   - Updated `check_win_conditions()` to call `record_game_end()` on game completion
   - Records stats for both winning and losing players
   - Passes role information to profile service

2. **`main.py`**
   - Imported MafiaGameStatsRepository, MafiaProfileService, and profile cog
   - Added `mafia_game_stats_repo` and `mafia_profile_service` attributes to bot instance
   - Initialized stats repository in `setup_services()`
   - Created profile service and passed to GameService
   - Loaded profile command cog in `load_commands()`

## Integration Flow

```
Game Ends → check_win_conditions()
    ↓
Determine winners/losers
    ↓
profile_service.record_game_end(winning_ids, losing_ids, role_dict)
    ↓
For each winner: increment_win(user_id) + update last role
For each loser: increment_loss(user_id) + update last role
    ↓
Wait 10 seconds, delete channel, clear session
```

## Database Operations

### Recording Game Results
```python
await self.mafia_profile_service.record_game_end(
    village_ids=[123, 456],
    mafia_ids=[789],
    winner="village",  # or "mafia"
    roles={"123": "Villager", "456": "Medic", "789": "Godfather"}
)
```

### Retrieving Player Stats
```python
stats = await profile_service.get_player_with_win_rate(user_id)
# Returns: {
#     "user_id": 123,
#     "games_played": 10,
#     "wins": 6,
#     "losses": 4,
#     "last_role": "godfather",
#     "win_rate": 60.0
# }
```

### Leaderboard (Top Players)
```python
top_players = await profile_service.get_leaderboard(limit=10)
```

## Testing Checklist

- [x] Profile repository compiles without errors
- [x] Profile service compiles without errors
- [x] Profile command compiles without errors
- [x] game_service.py integrates with profile service
- [x] main.py loads all cogs successfully
- [x] Bot connects to Discord gateway
- [x] MongoDB connection successful

## Runtime Testing Recommendations

1. **Start a Game**:
   - `!join` (4+ players)
   - `!start`
   - Verify channel `mafia-game-{guild_id}` creates
   - Play to completion

2. **Check Profile After Game**:
   - `!mprofile` 
   - Verify stats updated (games_played, wins/losses)
   - Verify win_rate calculated
   - Verify last_role recorded

3. **Test Multiple Games**:
   - Run several games
   - Verify incremental stat updates
   - Verify win_rate accuracy

## Known Limitations

- Stats are player-wide across all servers (MongoDB is guild-agnostic unless filtered)
- In-memory game session cleared on restart (but MongoDB record persists)
- Channel auto-deletes after 10 seconds (players can screenshot results)

## Future Enhancements

- Guild-specific leaderboards
- Stat breakdown by role
- Achievement badges
- Win-loss streaks
- Monthly/seasonal stats reset
