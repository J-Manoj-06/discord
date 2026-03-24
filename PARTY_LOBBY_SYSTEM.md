# Party Lobby System - Complete Documentation

## Overview
The Party Lobby System enables Discord server members to join a game lobby and start Mafia games with role assignments, automatic channels, and proper game flows.

---

## Data Structure

```python
parties = {
    guild_id: {
        "players": set(),        # Set of user IDs in party
        "game_active": bool      # True if game is running, False otherwise
    }
}
```

**Key Features:**
- Persistent party data per guild
- Players remain in party after game ends
- Tracks game active status to prevent modifications during play

---

## Commands

### 1. !join
**Purpose:** Add yourself to the party lobby

**Behavior:**
- Adds your user ID to the party
- Prevents duplicate joins
- Players can join at any time (even after games)
- Responses:
  - ✅ Success: `"🎉 {username} joined the party!"`
  - ❌ Already joined: `"❌ You are already in the party."`

**Usage:**
```
!join
```

**Implementation:** [bot/commands/join.py](bot/commands/join.py)

---

### 2. !party
**Purpose:** Display the current party lobby

**Display Format:**
```
Mafia Party Lobby 🎭

1. PlayerOne
2. PlayerTwo
3. PlayerThree
4. PlayerFour

Total Players: 4
```

**Behavior:**
- Shows all players in the party
- Lists players with numbered index
- Shows total count in footer
- Empty state: `"No players have joined the party yet."`

**Usage:**
```
!party
```

**Implementation:** [bot/commands/party.py](bot/commands/party.py)

---

### 3. !start
**Purpose:** Start the Mafia game with current party players

**Behavior:**
- Validates minimum 4 players required
- Transfers party players to game session
- Assigns roles using RoleManager
- Creates game channel with player permissions
- Sends role info via DM
- Sets `game_active = True`
- Starts game loop

**Responses:**
- ✅ Success: `"🎮 Game has started! Roles have been sent via DM 🌙"`
- ❌ Not enough players: `"❌ At least 4 players are required to start the game."`
- ❌ Game already running: Error message from game_service

**Usage:**
```
!start
```

**Implementation:** [bot/commands/start.py](bot/commands/start.py)

---

### 4. !add @user
**Purpose:** Manually add a player to the party (Admin only)

**Permissions:** `manage_guild`

**Behavior:**
- Requires admin permissions
- Adds mentioned user to party
- Prevents duplicate additions
- Cannot add during active game

**Response:**
- ✅ Success: `"{username} has been added to the party."`

**Usage:**
```
!add @PlayerName
```

**Implementation:** [bot/commands/add.py](bot/commands/add.py)

---

### 5. !kick @user
**Purpose:** Remove a player from the party (Admin only)

**Permissions:** `manage_guild`

**Behavior:**
- Removes mentioned user from party
- Prevents removal during active game
- Validates player is in party

**Response:**
- ✅ Success: `"{username} removed from the party."`

**Safety Checks:**
- Cannot kick during `game_active = True`

**Usage:**
```
!kick @PlayerName
```

**Implementation:** [bot/commands/kick.py](bot/commands/kick.py)

---

### 6. !clearparty
**Purpose:** Remove all players from the party (Admin only)

**Permissions:** `manage_guild`

**Behavior:**
- Clears all players from party
- Shows count of players removed
- Prevents clear during active game

**Response:**
- ✅ Success: `"Party has been cleared."`

**Safety Checks:**
- Cannot clear during `game_active = True`

**Usage:**
```
!clearparty
```

**Implementation:** [bot/commands/clearparty.py](bot/commands/clearparty.py)

---

### 7. !players
**Purpose:** Display alive players during an active game

**Display Format:**
```
Alive Players 👥

1. PlayerOne
2. PlayerTwo
3. PlayerThree

Alive Count: 3
```

**Behavior:**
- Shows players still alive in current game
- Lists by index
- Shows alive count in footer
- Only works during active game

**Usage:**
```
!players
```

**Implementation:** [bot/commands/players.py](bot/commands/players.py)

---

## Service: PartyService

**File:** [services/party_service.py](services/party_service.py)

### Methods

#### `create_party(guild_id: int) -> None`
Creates a new party for a guild.
```python
service.create_party(guild_id=12345)
```

#### `add_player_to_party(guild_id: int, user_id: int) -> bool`
Adds a player to the party. Returns `False` if already present.
```python
success = service.add_player_to_party(guild_id=12345, user_id=67890)
```

#### `remove_player_from_party(guild_id: int, user_id: int) -> bool`
Removes a player from the party. Returns `False` if not in party.
```python
success = service.remove_player_from_party(guild_id=12345, user_id=67890)
```

#### `clear_party(guild_id: int) -> int`
Removes all players. Returns count removed.
```python
count = service.clear_party(guild_id=12345)
```

#### `get_party_players(guild_id: int) -> Set[int]`
Returns a copy of all player IDs in party.
```python
players = service.get_party_players(guild_id=12345)
```

#### `get_player_count(guild_id: int) -> int`
Returns number of players in party.
```python
count = service.get_player_count(guild_id=12345)
```

#### `is_player_in_party(guild_id: int, user_id: int) -> bool`
Checks if a player is in the party.
```python
in_party = service.is_player_in_party(guild_id=12345, user_id=67890)
```

#### `set_game_active(guild_id: int, active: bool) -> None`
Sets game active status (prevents modifications during games).
```python
service.set_game_active(guild_id=12345, active=True)
```

#### `is_game_active(guild_id: int) -> bool`
Checks if a game is currently active.
```python
active = service.is_game_active(guild_id=12345)
```

---

## Integration Points

### main.py Setup
```python
# Services initialized in setup_services()
self.party_service = PartyService()
self.game_service = GameService(self.mafia_profile_service)

# Commands loaded in load_commands()
await join.setup(self, self.party_service)
await start.setup(self, self.game_service, self.party_service)
await add.setup(self, self.party_service)
await kick.setup(self, self.party_service)
await clearparty.setup(self, self.party_service)
await party.setup(self, self.party_service)
await players.setup(self, self.game_service)
```

### GameService Integration
When `!start` is called:
1. Party players are transferred to game session: `session["players"] = list(party_players)`
2. Game active flag is set: `party_service.set_game_active(guild_id, True)`
3. Game flow begins (roles, DMs, channel creation)
4. After game ends, party remains intact, `game_active` is set to `False`

---

## Workflow Example

### 1. Game Setup
```
User1: !join              → Added to party
User2: !join              → Added to party
User3: !join              → Added to party
User4: !join              → Added to party

Admin: !party             → Shows 4 players

Admin: !start             → Game starts with 4 players
```

### 2. During Game
- Game channel created: `mafia-game-{guild_id}`
- Roles assigned and sent via DM
- Night phase begins
- Cannot kick/clearparty/add during game

### 3. After Game
- Game ends and channel deleted
- `game_active = False`
- Party remains intact with all 4 players
- Can continue or add more players
- Can start new game with same party

---

## Safety Features

### Duplicate Prevention
- `!join` prevents joining twice
- `!add` prevents manual duplicates
- `add_player_to_party()` returns `False` if already in party

### Game Integrity
- Cannot kick/clearparty during `game_active = True`
- Cannot remove non-existent players
- Cannot start game with < 4 players

### Permission Guards
- `!add`, `!kick`, `!clearparty` require `manage_guild`
- Regular users can only `!join` and `!party`

### State Management
- Party data persists across games
- Game active flag prevents conflicts
- Automatic cleanup after game ends

---

## File Structure

```
bot/
├── commands/
│   ├── join.py           # !join command
│   ├── start.py          # !start command
│   ├── add.py            # !add @user command
│   ├── kick.py           # !kick @user command
│   ├── clearparty.py     # !clearparty command
│   ├── party.py          # !party command
│   └── players.py        # !players command
│
└── services/
    ├── party_service.py  # PartyService class
    └── game_service.py   # GameService class (modified)

main.py                    # Updated with party service setup
```

---

## Testing Checklist

- [ ] `!join` adds player and prevents duplicates
- [ ] `!party` shows correct player list with count
- [ ] `!start` requires minimum 4 players
- [ ] `!start` creates game channel and assigns roles
- [ ] `!add @user` requires admin and adds player
- [ ] `!kick @user` prevents kick during game
- [ ] `!clearparty` prevents clear during game
- [ ] `!players` shows alive players during game
- [ ] Party persists after game ends
- [ ] New game can start with same party

---

## Error Scenarios

| Scenario | Response |
|----------|----------|
| Join twice | "❌ You are already in the party." |
| Start with < 4 players | "❌ At least 4 players are required to start the game." |
| Kick during game | "Cannot modify party during active game" |
| Clear during game | "Cannot modify party during active game" |
| Invalid target on kick | "❌ Player not found in party" |

---

## Performance Notes

- **Time Complexity:** O(1) for all party operations (using sets)
- **Space Complexity:** O(n) where n = number of players per guild
- **Scalability:** Supports unlimited guilds and parties independently

---

## Version History

- **v1.0** - Initial Party Lobby System
  - 7 commands (join, party, start, add, kick, clearparty, players)
  - PartyService with full CRUD operations
  - Integrated with GameService
  - Full permission guards and safety checks

