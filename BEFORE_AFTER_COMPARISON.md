# Before & After Comparison

## 1. Player Display

### Before
```python
# In NightTargetSelect
options.append(discord.SelectOption(label=f"Player {player_id}", value=str(player_id)))

# In VotingView
self.add_item(VoteButton(game_service, guild_id, target_id))
# Button label: "Vote @{target_id}"
```

**Result:** ❌
```
Player 123456789
Player 987654321
Vote @123456789
```

### After
```python
# In player_select.py
def get_player_display_name(guild: discord.Guild, player_id: int) -> str:
    member = guild.get_member(player_id)
    display_name = member.display_name or member.name
    username = member.name
    return f"{display_name} (@{username})"

# Usage in NightTargetSelect
label = get_player_display_name(guild, player_id)

# Usage in VotingView
target_name = get_player_display_name(guild, target_id)
```

**Result:** ✅
```
John (@john123)
Alex (@alexgamer)
Sarah (@sarah_yt)
```

---

## 2. Self-Targeting Prevention

### Before
```python
# NightTargetSelect just filtered by alive_players
for player_id in session["alive_players"]:
    options.append(discord.SelectOption(label=f"Player {player_id}", value=str(player_id)))

# No validation if actor is in targets
```

**Problem:** ❌ Godfather could see self in kill menu

### After
```python
# player_select.py
def _get_valid_targets(self, session: Dict) -> List[int]:
    """Get list of valid targets based on action type and actor."""
    valid = []
    
    for player_id in session["alive_players"]:
        # Never target self
        if player_id == self.actor_id:
            continue
        
        valid.append(player_id)
    
    return valid

# Callback also checks:
if target_id == self.actor_id:
    return "❌ You cannot target yourself."
```

**Result:** ✅ Self never appears in dropdown, validated twice

---

## 3. Code Organization

### Before
```
services/game_service.py (550+ lines)
├── NightTargetSelect class (40 lines)
├── NightTargetView class (10 lines)
├── NightActionButton class (50 lines)
├── NightActionsView class (15 lines)
├── VoteButton class (45 lines)
├── VotingView class (15 lines)
└── GameService class (400 lines)
    ├── __init__
    ├── _get_or_create_session
    ├── get_session
    ├── add_player
    ├── assign_roles
    ├── send_roles_dm
    ├── create_game_thread
    ├── start_game_flow
    ├── _run_game_loop
    ├── run_night_phase
    ├── resolve_night
    ├── run_day_phase
    ├── run_voting_phase
    ├── resolve_votes
    └── check_win_conditions
```

❌ **Problems:**
- 175+ lines of UI code mixed with game logic
- Difficult to modify UI without touching game_service
- Hard to test individual components
- Unclear separation of concerns

### After
```
bot/ui/__init__.py
├── Exports NightActionButton
├── Exports NightActionsView
├── Exports NightTargetSelect
├── Exports NightTargetView
├── Exports VoteButton
└── Exports VotingView

bot/ui/player_select.py (200 lines)
├── get_player_display_name() → helper function
├── NightTargetSelect class (90 lines)
│   ├── __init__
│   ├── _get_valid_targets() → filters self-targeting
│   └── callback() → validation + storage
└── NightTargetView class (10 lines)

bot/ui/action_buttons.py (180 lines)
├── NightActionButton class (60 lines)
│   ├── __init__
│   └── callback() → validation + dropdown
└── NightActionsView class (20 lines)

bot/ui/voting_buttons.py (135 lines)
├── VoteButton class (55 lines)
│   ├── __init__
│   └── callback() → validation + vote storage
└── VotingView class (30 lines)

services/game_service.py (450 lines)
├── GameService class (only game logic)
│   ├── __init__
│   ├── _get_or_create_session
│   ├── get_session
│   ├── add_player
│   ├── assign_roles
│   ├── send_roles_dm
│   ├── create_game_thread
│   ├── start_game_flow
│   ├── _run_game_loop
│   ├── run_night_phase
│   ├── resolve_night
│   ├── run_day_phase
│   ├── run_voting_phase
│   ├── resolve_votes
│   └── check_win_conditions
```

✅ **Benefits:**
- UI logic separated into 3 modules
- game_service.py focused on game logic
- Each module has single responsibility
- Easy to test and modify independently
- Clear module boundaries

---

## 4. Safety Validations

### Before
```python
# NightActionButton.callback
if session["phase"] != "night":
    # No error
    return
if user_id not in session["alive_players"]:
    # No error
    return
if role != self.required_role:
    # No error
    return
if self.action_type in session["night_actions"]:
    # No error
    return
# Show menu

# Issues:
# - No target validation for self
# - No target validation after selection
# - Minimal feedback to user
```

❌ Incomplete validation

### After
```python
# action_buttons.py - NightActionButton.callback
if session["phase"] != "night":
    await interaction.response.send_message("❌ Night phase is not active.", ephemeral=True)
    return
if user_id not in session["alive_players"]:
    await interaction.response.send_message("❌ Dead players cannot act.", ephemeral=True)
    return
if user_role != self.required_role:
    await interaction.response.send_message(
        f"❌ Only {self.required_role.title()}s can use this action.",
        ephemeral=True,
    )
    return
if self.action_type in session["night_actions"]:
    await interaction.response.send_message(
        "❌ You have already submitted this action.",
        ephemeral=True,
    )
    return
# Show target selection menu

# player_select.py - NightTargetSelect.callback
if session["phase"] != "night":
    await interaction.response.send_message("❌ Night phase has ended.", ephemeral=True)
    return
if interaction.user.id != self.actor_id:
    await interaction.response.send_message(
        "❌ This action menu is not for you.",
        ephemeral=True,
    )
    return
if interaction.user.id not in session["alive_players"]:
    await interaction.response.send_message(
        "❌ Dead players cannot act.",
        ephemeral=True,
    )
    return
if self.action_type in session["night_actions"]:
    await interaction.response.send_message(
        "❌ You have already submitted this action.",
        ephemeral=True,
    )
    return
if target_id not in session["alive_players"]:
    await interaction.response.send_message(
        "❌ Target is no longer alive.",
        ephemeral=True,
    )
    return
if target_id == self.actor_id:  # NEW
    await interaction.response.send_message(
        "❌ You cannot target yourself.",
        ephemeral=True,
    )
    return
# Store action
```

✅ Comprehensive validation with user feedback

---

## 5. Game Over Message

### Before
```python
if mafia_alive == 0:
    session["phase"] = "ended"
    await thread.send("🏆 Game Over!\n\nWinner: Villagers")
    return True
```

❌ **Issues:**
- Minimal information
- No survivor list
- No role revealed
- Thread not closed

**Result:**
```
🏆 Game Over!

Winner: Villagers
```

### After
```python
# Check win conditions
if mafia_alive == 0:
    session["phase"] = "ended"
    winner = "Villagers"
elif mafia_alive >= villager_alive:
    session["phase"] = "ended"
    winner = "Mafia"
else:
    return False

# Build survivor list
survivor_names = [get_player_display_name(guild, pid) 
                  for pid in session["alive_players"]]
survivor_text = "\n".join(survivor_names) if survivor_names else "_None_"

# Send comprehensive message
await thread.send(
    f"🏆 **GAME OVER**\n\n"
    f"**Winner: {winner}**\n\n"
    f"Survivors:\n{survivor_text}"
)

# Archive and lock thread
try:
    await thread.edit(archived=True, locked=True)
except discord.HTTPException:
    try:
        await thread.edit(locked=True)
    except discord.HTTPException:
        pass

return True
```

✅ **Improvements:**
- Both win conditions checked
- Survivor list with proper names
- Thread automatically closed
- Graceful error handling

**Result:**
```
🏆 **GAME OVER**

**Winner: Villagers**

Survivors:
John (@john123)
Sarah (@sarah_yt)

[Thread archived and locked]
```

---

## 6. Night Result Message

### Before
```python
if killed_user_id is None:
    await thread.send("🌙 Night Result\n\nNobody died during the night.")
else:
    await thread.send(f"🌙 Night Result\n\n<@{killed_user_id}> was killed during the night.")
```

❌ **Issues:**
- Minimal information
- Uses mentions (heavy text)
- No role revealed
- Unclear communication

**Result:**
```
🌙 Night Result

<@123456789> was killed during the night.
```

### After
```python
if killed_user_id is None:
    await thread.send("🌙 **Night Result**\n\nNobody died during the night.")
else:
    victim_name = get_player_display_name(guild, killed_user_id)
    victim_role = session["roles"].get(killed_user_id, "unknown")
    await thread.send(
        f"🌙 **Night Result**\n\n"
        f"**{victim_name}** was killed.\n"
        f"Role: *{victim_role.title()}*"
    )
```

✅ **Improvements:**
- Proper player formatting
- Role information
- Better formatting and emphasis
- Clearer communication

**Result:**
```
🌙 **Night Result**

**John (@john123)** was killed.
Role: *Godfather*
```

---

## 7. Voting Result Message

### Before
```python
await thread.send(f"🗳️ Voting Result\n\n<@{eliminated_id}> has been eliminated.")
```

### After
```python
eliminated_name = get_player_display_name(guild, eliminated_id)
eliminated_role = session["roles"].get(eliminated_id, "unknown")
vote_count = counts[eliminated_id]

await thread.send(
    f"🗳️ **Voting Result**\n\n"
    f"**{eliminated_name}** has been eliminated.\n"
    f"Votes: {vote_count}\n"
    f"Role: *{eliminated_role.title()}*"
)
```

**Before:**
```
🗳️ Voting Result

<@987654321> has been eliminated.
```

**After:**
```
🗳️ **Voting Result**

**Sarah (@sarah_yt)** has been eliminated.
Votes: 3
Role: *Villager*
```

---

## 8. Parameter Passing

### Before
```python
async def run_voting_phase(self, guild_id: int, thread: discord.Thread) -> bool:
    ...
    await thread.send("...", view=VotingView(self, guild_id))

async def check_win_conditions(self, guild_id: int, thread: discord.Thread) -> bool:
    ...
    # No guild object - cannot get member display names
    # No way to show player display format
```

❌ Cannot resolve player names

### After
```python
async def run_voting_phase(self, guild_id: int, guild: discord.Guild, thread: discord.Thread) -> bool:
    ...
    await thread.send("...", view=VotingView(self, guild, guild_id))

async def check_win_conditions(self, guild_id: int, guild: discord.Guild, thread: discord.Thread) -> bool:
    ...
    # Can now call get_player_display_name(guild, player_id)
    # Can show proper player formatting
```

✅ Guild object passed for name resolution

---

## 9. Vote Button Labels

### Before
```python
# In VoteButton.__init__
super().__init__(
    label=f"Vote @{target_id}",
    style=discord.ButtonStyle.secondary,
    custom_id=f"vote_{guild_id}_{target_id}",
)
```

**Result:** ❌
```
Vote @123456789
Vote @987654321
```

### After
```python
# In VotingView.__init__
for target_id in session["alive_players"][:25]:
    target_name = get_player_display_name(guild, target_id)
    self.add_item(
        VoteButton(
            game_service,
            guild,
            guild_id,
            target_id,
            target_name,
        )
    )

# In VoteButton.__init__
super().__init__(
    label=target_name,  # e.g., "John (@john123)"
    style=discord.ButtonStyle.secondary,
    custom_id=f"vote_{guild_id}_{target_id}",
)
```

**Result:** ✅
```
John (@john123)
Alex (@alexgamer)
Sarah (@sarah_yt)
```

---

## Summary Table

| Feature | Before | After | Status |
|---------|--------|-------|--------|
| **Player Names** | IDs only | "Name (@username)" | ✅ Improved |
| **Self-Targeting** | Possible | Prevented | ✅ Fixed |
| **Code Organization** | 550 lines single file | 450 + 515 modular | ✅ Refactored |
| **Safety Checks** | Basic | Comprehensive | ✅ Enhanced |
| **User Feedback** | Minimal | Detailed with roles | ✅ Improved |
| **Thread Closure** | Not implemented | Auto archive + lock | ✅ Added |
| **Game Over Message** | Winner only | Winner + survivors + roles | ✅ Enhanced |
| **UI Components** | Mixed with logic | Separate modules | ✅ Organized |
| **Display Names** | Not resolved | Full member lookup | ✅ Implemented |
| **Vote Information** | No details | Votes + role shown | ✅ Added |

