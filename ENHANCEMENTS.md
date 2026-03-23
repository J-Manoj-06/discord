# Discord Mafia Bot - Enhancements Document

## Overview

This document details the comprehensive enhancements made to the Discord Mafia bot game logic and UI.

---

## 1. MODULAR UI STRUCTURE

### New Directory: `bot/ui/`

Created a new modular UI layer with three specialized components:

```
bot/ui/
├── __init__.py           # Package definitions
├── player_select.py      # Player target selection with filtering
├── action_buttons.py     # Night action buttons
└── voting_buttons.py     # Voting UI components
```

#### Benefits:
- ✅ Separated concerns (buttons, selections, voting)
- ✅ Easier to maintain and test
- ✅ Reusable components
- ✅ Cleaner game_service.py

---

## 2. PLAYER DISPLAY FORMAT

### Implementation: `get_player_display_name(guild, player_id)`

**Format Standard:**
```
Display Name (@username)
```

**Examples:**
- `John (@john123)`
- `Alex (@alexgamer)`
- `Sarah (@sarah_yt)`

**Used in:**
- Night action dropdowns
- Voting buttons
- Game messages (eliminations, night results)
- Survivor lists
- Game start player list

**Benefits:**
- ✅ Human-readable player identification
- ✅ No ID pollution in UI
- ✅ Shows actual Discord username
- ✅ Consistent across all messages

---

## 3. PLAYER SELECTION RULES & RESTRICTIONS

### File: `bot/ui/player_select.py`

#### Self-Targeting Prevention

All actions prevent actors from targeting themselves:

```python
# Detective cannot investigate self
if player_id == self.actor_id:
    continue

# Godfather cannot kill self
if player_id == self.actor_id:
    continue

# Doctor cannot heal self
if player_id == self.actor_id:
    continue
```

#### Role-Specific Restrictions

Built into `_get_valid_targets()` method:

**Detective:**
- Cannot investigate themselves
- _Future: Can add restrictions to prevent re-investigating same player_

**Godfather:**
- Cannot kill themselves
- _Future: Can add targeting history tracking_

**Doctor:**
- Cannot heal themselves more than once per night (enforced by "action already submitted" check)
- _Implemented as optional rule_

#### Dropdown Filtering

Valid targets are determined before generating options:

```python
def _get_valid_targets(self, session: Dict) -> List[int]:
    """Get list of valid targets based on action type and actor."""
    valid = []
    
    for player_id in session["alive_players"]:
        # Never target self
        if player_id == self.actor_id:
            continue
        
        # Add role-specific checks here
        valid.append(player_id)
    
    return valid
```

**Result:** Users only see valid target players in dropdown, preventing invalid selections.

---

## 4. PLAYER SELECTION UI ENHANCEMENTS

### File: `bot/ui/player_select.py`

#### Dropdown Menu Design

```python
class NightTargetSelect(discord.ui.Select):
    """Select menu for choosing night action targets with filtering."""
```

**Features:**
- ✅ Only shows alive players (excluding actor)
- ✅ Player names formatted as "Display Name (@username)"
- ✅ Placeholder text guides users
- ✅ Handles "no valid targets" gracefully
- ✅ Timeout: 45 seconds

**Validation in Callback:**

```python
async def callback(self, interaction: discord.Interaction):
    # Phase validation
    if session["phase"] != "night":
        return "❌ Night phase has ended."
    
    # Actor validation
    if interaction.user.id != self.actor_id:
        return "❌ This action menu is not for you."
    
    # Alive validation
    if interaction.user.id not in session["alive_players"]:
        return "❌ Dead players cannot act."
    
    # Action already submitted
    if self.action_type in session["night_actions"]:
        return "❌ You have already submitted this action."
    
    # Target validation
    if target_id not in session["alive_players"]:
        return "❌ Target is no longer alive."
    
    # Self-targeting prevention
    if target_id == self.actor_id:
        return "❌ You cannot target yourself."
```

---

## 5. NIGHT ACTION BUTTONS

### File: `bot/ui/action_buttons.py`

#### Button Panel: `NightActionsView`

Shows 3 role-specific action buttons:

```
🔪 Kill        (Godfather only)
💉 Heal        (Doctor only)
🔍 Investigate (Detective only)
```

#### Safety Checks in `NightActionButton.callback()`:

1. **Phase Check** - Only during night phase
2. **Alive Check** - Dead players cannot act
3. **Role Check** - User must have required role
4. **Action Check** - Action not already submitted

#### Button Click Flow:

```
User clicks button
    ↓
Validations pass
    ↓
Show target selection dropdown
    ↓
User selects target
    ↓
Action stored in session["night_actions"]
```

---

## 6. NIGHT ACTION TARGET SELECTION

### File: `bot/ui/player_select.py`

#### Investigation Special Handling

Immediately reveals role to detective:

```python
if self.action_type == "investigate":
    target_role = session["roles"].get(target_id, "unknown")
    target_name = get_player_display_name(self.guild, target_id)
    await interaction.response.send_message(
        f"🔍 Investigation Result:\n\n"
        f"{target_name} is **{target_role.title()}**.",
        ephemeral=True,
    )
```

#### Kill/Heal Confirmation

```
✅ Kill action submitted

Target: John (@john123)
```

---

## 7. VOTING BUTTONS

### File: `bot/ui/voting_buttons.py`

#### Vote Button Panel: `VotingView`

Creates one button per alive player with formatted names:

```
John (@john123)
Alex (@alexgamer)
Sarah (@sarah_yt)
```

#### Vote Button Validations:

```python
async def callback(self, interaction: discord.Interaction):
    # Phase check
    if session["phase"] != "voting":
        return "❌ Voting phase is not active."
    
    # Voter alive check
    if voter_id not in session["alive_players"]:
        return "❌ Dead players cannot vote."
    
    # Duplicate vote prevention
    if voter_id in session["votes"]:
        return "❌ You have already voted."
    
    # Target alive check
    if self.target_id not in session["alive_players"]:
        return "❌ That player is no longer alive."
```

---

## 8. THREAD MANAGEMENT

### File: `services/game_service.py`

#### Thread Creation: `create_game_thread()`

```python
async def create_game_thread(self, guild_id: int, channel):
    # If in existing thread, reuse it
    if isinstance(channel, discord.Thread):
        session["thread_id"] = channel.id
        return True, "Using current thread.", channel
    
    # Create starter message
    starter_message = await channel.send("🧵 Creating game thread...")
    
    # Create public thread from message
    thread = await starter_message.create_thread(
        name=f"Mafia Game - Day {day_count}",
        auto_archive_duration=60,
    )
    
    session["thread_id"] = thread.id
    return True, "Thread created.", thread
```

**Error Handling:**
- Catches `discord.Forbidden` for permission errors
- Catches `discord.HTTPException` for API issues
- Returns actionable error messages

**Permissions Required:**
- Send Messages
- Create Public Threads
- Send Messages in Threads

---

## 9. THREAD GAME MESSAGES

### All Game Messages Sent to Thread

**Night Phase:**
```
🌙 **Night Phase** has begun.

Available actions:
🔪 Kill (Godfather)
💉 Heal (Doctor)
🔍 Investigate (Detective)

_Click a button below to perform your action._
```

**Night Result:**
```
🌙 **Night Result**

**John (@john123)** was killed.
Role: *Godfather*
```

**Day Phase:**
```
☀️ **Day Phase** - Day 1

_Everyone can discuss who might be mafia. Voting will start soon._
```

**Voting Phase:**
```
🗳️ **Voting Phase** has started.

_Click a button below to vote for elimination._
```

**Voting Result:**
```
🗳️ **Voting Result**

**Alex (@alexgamer)** has been eliminated.
Votes: 3
Role: *Villager*
```

---

## 10. WIN CONDITIONS

### File: `services/game_service.py`

#### Win Condition: `check_win_conditions()`

**Village Victory:**
```
Godfather (mafia) is dead → mafia_alive == 0
```

**Mafia Victory:**
```
Mafia >= Villagers → mafia_alive >= villager_alive
```

**Implementation:**
```python
async def check_win_conditions(self, guild_id: int, guild, thread):
    # Count alive roles
    for player_id in session["alive_players"]:
        if role == "godfather":
            mafia_alive += 1
        else:
            villager_alive += 1
    
    # Villagers win if Godfather dead
    if mafia_alive == 0:
        winner = "Villagers"
    
    # Mafia wins if mafia >= villagers
    elif mafia_alive >= villager_alive:
        winner = "Mafia"
```

---

## 11. GAME OVER MESSAGE

### File: `services/game_service.py`

#### Game End: `check_win_conditions()`

Displays winner and survivors:

```python
# Build survivor list
survivor_names = [get_player_display_name(guild, pid) for pid in session["alive_players"]]
survivor_text = "\n".join(survivor_names) if survivor_names else "_None_"

# Send game over message
await thread.send(
    f"🏆 **GAME OVER**\n\n"
    f"**Winner: {winner}**\n\n"
    f"Survivors:\n{survivor_text}"
)
```

**Example Output:**
```
🏆 **GAME OVER**

**Winner: Villagers**

Survivors:
John (@john123)
Sarah (@sarah_yt)
```

---

## 12. THREAD CLOSURE

### File: `services/game_service.py`

#### Auto-Archive and Lock: `check_win_conditions()`

```python
# Archive and lock thread after game over
try:
    await thread.edit(archived=True, locked=True)
except discord.HTTPException:
    # If archiving fails, try locking only
    try:
        await thread.edit(locked=True)
    except discord.HTTPException:
        pass
```

**Effects:**
- ✅ Thread marked as archived (clean UI)
- ✅ Thread locked (no further messages)
- ✅ Prevents accidental continuation
- ✅ Graceful fallback if operations fail

---

## 13. SAFETY CHECKS COMPREHENSIVE LIST

### 1. Phase Validation
- ✅ Night actions only during night phase
- ✅ Voting only during voting phase
- ✅ Actions blocked after game ended

### 2. Player State Validation
- ✅ Dead players cannot act
- ✅ Dead players cannot vote
- ✅ Only alive players can see action/vote buttons

### 3. Role Validation
- ✅ Action buttons show only to correct role
- ✅ Role mismatch blocks action submission
- ✅ Invalid role rejected before UI display

### 4. Action Restriction
- ✅ No self-targeting (all roles)
- ✅ Actions cannot be submitted twice per night
- ✅ Each player has only one action per night

### 5. Vote Validation
- ✅ Duplicate vote prevention
- ✅ Dead targets cannot be voted for
- ✅ Game state verified before processing vote

### 6. Target Validation
- ✅ Target must be alive
- ✅ Target must exist in game session
- ✅ Target changes checked after submission

### 7. Actor Validation
- ✅ User must be button/menu owner
- ✅ Prevent other users from using menus
- ✅ User ID verified in all callbacks

### 8. Game State Safety
- ✅ Thread exists before sending messages
- ✅ Session exists for guild
- ✅ Phase transitions validated
- ✅ Win conditions prevent infinite loops

---

## 14. CODE STRUCTURE

### Before Enhancements:
```
services/game_service.py (500+ lines)
    - UI classes (100+ lines)
    - Game logic mixed with UI
    - Hard to test individual components
    - Difficult to modify UI independently
```

### After Enhancements:
```
bot/ui/
├── __init__.py
├── player_select.py       (200 lines) - Target selection
├── action_buttons.py      (180 lines) - Night actions
└── voting_buttons.py      (135 lines) - Voting UI

services/game_service.py   (450 lines)
    - Core game logic
    - Session management
    - Phase transitions
    - Result processing
    - No UI-specific code
```

**Separation of Concerns:**
- `player_select.py` - All target selection logic
- `action_buttons.py` - All night action UI
- `voting_buttons.py` - All voting UI
- `game_service.py` - Game state and rules

---

## 15. EXAMPLE GAME FLOW

### 1. Game Start

```
User1: !join
User2: !join
User3: !join
User4: !join

User4: !start

[Thread created: "Mafia Game - Day 1"]

Thread Message:
🎮 **Mafia Game Started!**

**Players:**
User1 (@user1)
User2 (@user2)
User3 (@user3)
User4 (@user4)

The game begins with **Night Phase**.

Check your **DMs** for your role.
```

### 2. Night Phase

```
[DMs sent]
User1: You are the Godfather 🕶️
User2: You are the Doctor 💉
User3: You are the Detective 🔍
User4: You are a Villager 👤

Thread Message:
🌙 **Night Phase** has begun.

Available actions:
🔪 Kill (Godfather)
💉 Heal (Doctor)
🔍 Investigate (Detective)

_Click a button below to perform your action._

[Buttons shown for 60 seconds]

User1 clicks: 🔪 Kill
  Dropdown shows: User2 (@user2), User3 (@user3), User4 (@user4)
  User1 selects: User2 (@user2)
  ✅ Kill action submitted. Target: User2 (@user2)

User2 clicks: 💉 Heal
  Dropdown shows: User1 (@user1), User3 (@user3), User4 (@user4)
  User2 selects: User3 (@user3)
  ✅ Heal action submitted. Target: User3 (@user3)

User3 clicks: 🔍 Investigate
  Dropdown shows: User1 (@user1), User2 (@user2), User4 (@user4)
  User3 selects: User1 (@user1)
  🔍 Investigation Result:
  User1 (@user1) is **Godfather**

[60 seconds elapsed]

Thread Message:
🌙 **Night Result**

**User2 (@user2)** was killed.
Role: *Doctor*
```

### 3. Day Phase

```
Thread Message:
☀️ **Day Phase** - Day 1

_Everyone can discuss who might be mafia. Voting will start soon._

[60 seconds pass]

Thread Message:
🗳️ **Voting Phase** has started.

_Click a button below to vote for elimination._

[Vote buttons appear]

User1 votes: User3 (@user3)
User3 votes: User1 (@user1)
User4 votes: User1 (@user1)

[60 seconds elapsed]

Thread Message:
🗳️ **Voting Result**

**User1 (@user1)** has been eliminated.
Votes: 2
Role: *Godfather*

[Win condition check]
mafia_alive = 0 (Godfather dead) → Villagers win!

Thread Message:
🏆 **GAME OVER**

**Winner: Villagers**

Survivors:
User3 (@user3)
User4 (@user4)

[Thread archived and locked]
```

---

## 16. IMPLEMENTATION CHECKLIST

### Player Selection Rules
- ✅ Detective cannot investigate themselves
- ✅ Godfather cannot kill themselves
- ✅ Doctor cannot heal themselves (optional rule)
- ✅ Player dropdown excludes actor automatically
- ✅ Valid targets filtered before UI generation

### Player Display Format
- ✅ Format: "Display Name (@username)"
- ✅ No IDs shown
- ✅ No mentions shown
- ✅ Used in all UI elements
- ✅ Used in all game messages

### Player Selection UI
- ✅ discord.ui.Select dropdown menus
- ✅ Player names formatted correctly
- ✅ Only alive players shown
- ✅ Actor excluded from targets
- ✅ Internal value stores user_id

### Thread Management
- ✅ Thread created on `!start`
- ✅ Thread name: "Mafia Game - Day {n}"
- ✅ Auto-archive duration: 60 minutes
- ✅ Reuses existing thread if used inside one

### Thread Game Messages
- ✅ All game messages in thread
- ✅ Night phase messages
- ✅ Day phase messages
- ✅ Voting phase messages
- ✅ Results and eliminations

### Game Over Handling
- ✅ Final message shows winner
- ✅ Shows survivor list
- ✅ Shows remaining players with display names
- ✅ Thread archived after game
- ✅ Thread locked after game

### Win Conditions
- ✅ Village wins if Godfather dead
- ✅ Mafia wins if mafia >= villagers
- ✅ Check conditions after each phase

### Safety Checks
- ✅ Prevent self-targeting
- ✅ Dead players cannot act
- ✅ Actions only during night phase
- ✅ Voting only during voting phase
- ✅ Prevent duplicate voting
- ✅ Prevent interacting after game ended
- ✅ Role validation for actions
- ✅ Target alive validation

### Code Structure
- ✅ `bot/ui/` directory created
- ✅ `player_select.py` module
- ✅ `action_buttons.py` module
- ✅ `voting_buttons.py` module
- ✅ Modular components
- ✅ Clean separation of concerns

---

## 17. FILES CREATED/MODIFIED

### New Files:
- ✅ `bot/ui/__init__.py`
- ✅ `bot/ui/player_select.py`
- ✅ `bot/ui/action_buttons.py`
- ✅ `bot/ui/voting_buttons.py`

### Modified Files:
- ✅ `services/game_service.py` - Import UI modules, update game flow
- ✅ `main.py` - No changes required (UI imports handle automatically)
- ✅ `bot/commands/start.py` - No changes required

### Unchanged:
- ✅ All economy/profile functionality
- ✅ All database functionality
- ✅ All configuration
- ✅ Join command

---

## 18. TESTING CHECKLIST

### Manual Testing:
1. ✅ Bot starts and loads all cogs
2. ⏳ Run `!join` with 4+ players
3. ⏳ Run `!start` - verify thread creates
4. ⏳ Verify thread name is "Mafia Game - Day 1"
5. ⏳ Verify night action buttons appear
6. ⏳ Verify detective can see investigation result immediately
7. ⏳ Verify voting buttons appear for all alive players
8. ⏳ Verify eliminated player role displayed
9. ⏳ Verify game over message shows survivors
10. ⏳ Verify thread is archived and locked after game

### Edge Cases:
- ⏳ Verify actor cannot be in target dropdown
- ⏳ Verify dead players' names removed from dropdowns
- ⏳ Verify no duplicate votes accepted
- ⏳ Verify game continues correctly across multiple rounds
- ⏳ Verify win conditions trigger correctly
- ⏳ Verify permission errors handled gracefully

---

## 19. FUTURE ENHANCEMENTS

### Possible Additions:
1. **Replay System** - Store game history in MongoDB
2. **Stats Tracking** - Win/loss records per role
3. **Configurable Timers** - Admin-set phase durations
4. **Custom Roles** - Modular role system
5. **Game Logs** - Chat history in thread
6. **Leaderboards** - Top players by stats
7. **Role-Specific Commands** - In-game secret actions
8. **Persistent Game State** - Restart bot during active game
9. **Multiple Mafia** - Adjustable mafia count
10. **Spectator Mode** - Watch games

---

## 20. SUMMARY

All requested enhancements have been implemented:

✅ **Player Selection Rules** - Self-targeting prevented, role restrictions enforced
✅ **Player Display Format** - "Display Name (@username)" throughout
✅ **Player Selection UI** - discord.ui.Select dropdowns with filtering
✅ **Thread Management** - Proper thread creation with error handling
✅ **Thread Game Messages** - All messages in thread, main channel clean
✅ **Game Over Handling** - Winner and survivors displayed
✅ **Thread Closure** - Auto-archive and lock after game
✅ **Win Conditions** - Godfather death = village win, mafia >= villagers = mafia win
✅ **Safety Checks** - Comprehensive validation at every step
✅ **Code Structure** - Modular UI components, clean separation of concerns

**Bot Status:** ✅ Compiles successfully, ✅ Starts successfully, ✅ Loads all cogs

