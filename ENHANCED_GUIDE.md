# Quick Reference: Enhanced Mafia Bot

## Game Flow Summary

```
!join (4+ players)
    ↓
!start
    ↓
[Thread created: "Mafia Game - Day 1"]
    ↓
Night Phase (60s)
├─ Godfather: 🔪 Kill (target dropdown)
├─ Doctor: 💉 Heal (target dropdown)
└─ Detective: 🔍 Investigate (shows role)
    ↓
Night Result (elimination shown)
    ↓
Day Phase (60s) [Discussion period]
    ↓
Voting Phase (60s)
├─ All alive players: Vote buttons
└─ Majority vote determines elimination
    ↓
Result (elimination shown with role)
    ↓
Win Check:
├─ Godfather dead? → Villagers win ✓
└─ Mafia >= Villagers? → Mafia wins ✓
    ↓
Game Over (survivors listed)
    ↓
[Thread auto-archived and locked]
```

## Player Display Format

**Format:** `Display Name (@username)`

**Examples:**
- `John (@john123)`
- `Alex Player (@alexgamer)`
- `Sarah (@sarah_yt)`

**Where Used:**
- Night action target dropdowns
- Voting buttons
- Game messages (results, eliminations)
- Survivor list
- DM notifications

## Night Actions

### 🔪 Kill (Godfather)

1. Click "Kill" button
2. Select target from dropdown
3. Target is killed (unless healed)
4. Result shown after night ends

**Cannot target:** Self

### 💉 Heal (Doctor)

1. Click "Heal" button
2. Select target from dropdown
3. If killed, target survives
4. Can only heal once per night

**Cannot target:** Self

### 🔍 Investigate (Detective)

1. Click "Investigate" button
2. Select target from dropdown
3. **Immediate result:** Role revealed in DM
4. Other players don't see result

**Cannot target:** Self

## Voting Phase

1. Click player name button
2. Vote submitted (ephemeral confirmation)
3. Cannot vote twice
4. Majority vote wins
5. Ties broken by lowest ID

**Cannot vote for:** Dead players

## Safety Features

| Feature | Details |
|---------|---------|
| **Self-Targeting Block** | All players excluded from own target menus |
| **Dead Player Protection** | Cannot act, cannot vote |
| **Duplicate Action Prevention** | Each action submitted once per night |
| **Duplicate Vote Prevention** | Each player votes once per voting phase |
| **Phase Validation** | Actions only work during correct phase |
| **Role Validation** | Actions only available to correct role |
| **Target Validation** | Cannot target dead or non-existent players |
| **Game Over Lock** | Thread archived/locked, no further messages |

## Thread Messages

### Game Start
```
🎮 **Mafia Game Started!**

**Players:**
John (@john123)
Alex (@alexgamer)
Sarah (@sarah_yt)

The game begins with **Night Phase**.
Check your **DMs** for your role.
```

### Night Phase
```
🌙 **Night Phase** has begun.

Available actions:
🔪 Kill (Godfather)
💉 Heal (Doctor)
🔍 Investigate (Detective)

_Click a button below to perform your action._
```

### Night Result
```
🌙 **Night Result**

**John (@john123)** was killed.
Role: *Godfather*
```

### Day Phase
```
☀️ **Day Phase** - Day 1

_Everyone can discuss who might be mafia. Voting will start soon._
```

### Voting Phase
```
🗳️ **Voting Phase** has started.

_Click a button below to vote for elimination._
```

### Voting Result
```
🗳️ **Voting Result**

**Sarah (@sarah_yt)** has been eliminated.
Votes: 3
Role: *Villager*
```

### Game Over
```
🏆 **GAME OVER**

**Winner: Villagers**

Survivors:
Alex (@alexgamer)
Sarah (@sarah_yt)
```

## Role Guide

### Godfather (Mafia) 🕶️
- **Goal:** Mafia >= Villagers
- **Night Action:** Kill one player
- **Cannot Target:** Self
- **Loss Condition:** Eliminated

### Doctor 💉
- **Goal:** Eliminate Godfather
- **Night Action:** Heal one player (save from kill)
- **Cannot Target:** Self
- **Special:** One heal per night

### Detective 🔍
- **Goal:** Eliminate Godfather
- **Night Action:** Investigate one player (reveal role)
- **Cannot Target:** Self
- **Special:** Role revealed immediately

### Villager 👤
- **Goal:** Eliminate Godfather
- **Night Action:** None
- **Day Action:** Vote during voting phase

## Win Conditions

| Winner | Condition |
|--------|-----------|
| **Villagers** | Godfather eliminated AND mafia_alive == 0 |
| **Mafia** | mafia_alive >= villager_alive |

## File Structure

```
bot/
├── ui/                    [NEW]
│   ├── __init__.py       [NEW]
│   ├── player_select.py  [NEW] - Target selection with filtering
│   ├── action_buttons.py [NEW] - Night action buttons
│   └── voting_buttons.py [NEW] - Voting UI
├── commands/
│   ├── join.py
│   └── start.py
└── ...

services/
└── game_service.py       [UPDATED] - Import UI modules, core logic

ENHANCEMENTS.md           [NEW] - Full documentation
```

## Known Limitations

1. **In-Memory State** - Game data lost if bot restarts
2. **No Persistence** - Game history not stored in MongoDB
3. **UI Timeout** - Buttons timeout after 60 seconds
4. **Max Players** - UI limited to 25 players (Discord limit)
5. **Fixed Timers** - Phase durations hardcoded (60s each)

## Testing Commands

```bash
# Compile check
python3 -m py_compile bot/ui/*.py services/game_service.py

# Start bot
source .venv/bin/activate
python main.py

# In Discord
!join      # Players join
!start     # Start game
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Thread not created** | Check bot permissions: Send Messages, Create Public Threads, Send Messages in Threads |
| **No role DMs** | Check user DM settings, bot user permissions |
| **Target menu empty** | No valid targets (only actor exists) |
| **Votes not showing** | Voting phase may have ended, run next round |
| **Thread not locking** | Bot may lack permission; will still complete game |
| **Players showing as IDs** | Display name lookup failed; fallback to ID |

## Quick Commands

```
!join              Join current game
!start             Start game with joined players
!economy bal       Check your coins
!profile view      View your profile
!shop list         View shop items
```

---

For full technical details, see ENHANCEMENTS.md
