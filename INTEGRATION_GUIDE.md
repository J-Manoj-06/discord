"""
Integration Guide: How to integrate the Economy & Progression system
into your existing Mafia bot.

This document explains the architecture and integration points.
"""

# ============================================================================
# 1) ARCHITECTURE OVERVIEW
# ============================================================================

The system is built with clean separation of concerns:

├── database/
│   ├── mongodb.py              # MongoDB connection & client
│   └── repositories/           # Data access layer
│       ├── wallet_repository.py
│       ├── profile_repository.py
│       ├── inventory_repository.py
│       └── economy_log_repository.py
│
├── models/                      # Data models (Pydantic/dataclasses)
│   ├── wallet.py
│   ├── user_profile.py
│   └── cosmetic_item.py
│
├── services/                    # Business logic services
│   ├── economy_service.py       # Coins/gems/rewards
│   ├── profile_service.py       # Levels/XP/cosmetics
│   ├── vote_effect_service.py   # Voting cosmetics
│   └── shop_service.py          # Catalog/purchases
│
├── bot/
│   ├── commands/
│   │   ├── economy_commands.py
│   │   ├── profile_commands.py
│   │   ├── shop_commands.py
│   │   └── vote_effect_commands.py
│   └── events/
│       └── game_events.py       # Game reward triggers
│
├── utils/
│   ├── embed_builder.py         # Discord embed styling
│   ├── cooldowns.py             # Cooldown management
│   └── formatter.py             # Text formatting
│
└── main.py                      # Bot entry point


# ============================================================================
# 2) SETUP INSTRUCTIONS
# ============================================================================

BEFORE running the bot:

1. Install dependencies:
   $ pip install -r requirements.txt

2. Create a .env file (copy from .env.example):
   cp .env.example .env
   
3. Add your credentials:
   - DISCORD_TOKEN: Get from Discord Developer Portal
   - MONGODB_URI: Get from MongoDB Atlas
   
4. MongoDB Collections Setup (automatic on first run):
   - users         → User wallets
   - profiles      → User profiles & progression
   - inventory     → Cosmetic ownership
   - economy_logs  → Transaction audit trail

5. Run the bot:
   $ python main.py


# ============================================================================
# 3) INTEGRATING WITH EXISTING MAFIA GAME
# ============================================================================

IN YOUR GAME LOGIC, add these integration points:

A) WHEN A PLAYER VOTES (voting phase):
   
   from bot.events.game_events import get_game_events_handler
   
   handler = get_game_events_handler()
   await handler.on_player_voted(user_id, guild_id)


B) WHEN VOTING EFFECT IS RENDERED:
   
   from bot.events.game_events import get_game_events_handler
   from services.vote_effect_service import VoteEffectService
   
   handler = get_game_events_handler()
   vote_text = await handler.vote_effect_service.render_vote(
       user_id=voter_id,
       guild_id=guild_id,
       voter_name=voter.name,
       target_name=target.name,
   )
   
   # Use vote_text instead of plain "X votes for Y"


C) WHEN GAME ENDS (most important):
   
   from bot.events.game_events import get_game_events_handler
   
   handler = get_game_events_handler()
   await handler.on_game_ended(
       guild_id=ctx.guild.id,
       winners=[user_id1, user_id2],      # IDs of winning players
       losers=[user_id3, user_id4],       # IDs of losing players
       role_map={
           user_id1: "mafia",
           user_id2: "doctor",
           user_id3: "villager",
           user_id4: "detective",
       },
       votes_cast={
           user_id1: 3,                   # Player 1 cast 3 votes
           user_id2: 2,
           user_id3: 4,
           user_id4: 2,
       },
   )
   
   This will:
   - Award coins based on role & participation
   - Award XP for leveling
   - Update game stats (wins/losses)
   - Record transaction log


# ============================================================================
# 4) COMMAND SUMMARY
# ============================================================================

ECONOMY:
  !balance          - Show coins, gems, stats
  !daily            - Claim 500 coins (24hr cooldown)
  !leaderboard      - Top richest and winners

PROFILE:
  !profile          - Show your profile card
  !rank             - Show level and XP progress
  !titles           - List owned titles
  !equiptitle       - Equip a title
  !themes           - List owned themes
  !equiptheme       - Equip a theme

SHOP:
  !shop             - Browse shop items
  !buy <item>       - Purchase item with coins/gems
  !inventory        - Show owned cosmetics

VOTE EFFECTS:
  !voteeffects      - List all vote effects
  !previewvoteeffect <name>  - See effect preview
  !buyvoteeffect <name>      - Purchase effect
  !equipvoteeffect <name>    - Equip effect


# ============================================================================
# 5) REWARD RULES
# ============================================================================

When on_game_ended is called:

Winner Rewards:
  - Mafia win:     +150 coins
  - Villager win:  +100 coins
  - Participation: +50 coins (all players)
  - Per vote cast: +10 coins each

Loser Rewards:
  - Participation: +50 coins
  - Per vote cast: +10 coins each

XP:
  - Winner:        +50 XP
  - Loser:         +25 XP
  - No show:       0 XP

Level Threshold:
  - Level N requires: N * 100 XP
  - Level 1: 100 XP
  - Level 2: 200 XP (cumulative)
  - Level 3: 300 XP (cumulative)
  - etc...


# ============================================================================
# 6) ECONOMY MECHANICS
# ============================================================================

CURRENCY:
  Coins  -> Free primary currency, earned in-game
  Gems   -> Premium currency, for special cosmetics (can award manually)

PRICES (example):
  Vote Effects:  200-600 coins or 100 gems (premium)
  Titles:        250-400 coins or 50 gems
  Themes:        300-400 coins or 75 gems

TRANSACTION SAFETY:
  - All coin/gem transactions are atomic (use MongoDB updates)
  - All transactions logged for audit trail
  - Negative balance prevention built-in
  - Daily claim tracked with 24-hour cooldown


# ============================================================================
# 7) COSMETICS & PROGRESSION
# ============================================================================

NO PAY-TO-WIN:
  ✓ Cosmetics only affect visual display
  ✓ Vote effects don't change vote count
  ✓ Titles are decorative
  ✓ Themes are profile styling

PROGRESSION:
  Levels unlock higher status and cosmetic availability
  XP earned from games and voting
  No level caps (scales infinitely)
  Level-up notifications


# ============================================================================
# 8) EXTENDING THE SYSTEM
# ============================================================================

TO ADD A NEW COSMETIC CATEGORY:

1. Add to SHOP_CATALOG in services/shop_service.py
2. Create repository methods in database/repositories/
3. Add command handlers in bot/commands/
4. Update models if needed

Example: Add a new "border" cosmetic

  In shop_service.py:
  "gold_border": CosmeticItem(
      id="gold_border",
      name="Gold Border",
      category="border",
      price_coins=500,
      description="Premium gold profile border",
      rarity="rare",
      unlock_type="purchase",
  )

  In profile_commands.py:
  Add !equipborder command that calls:
  profile.set_equipped_border(user_id, guild_id, border_id)


# ============================================================================
# 9) ERROR HANDLING
# ============================================================================

All services return (success, message) tuples:

success, msg = await economy.add_coins(user_id, guild_id, 100)
if success:
    await ctx.send(msg)
else:
    await ctx.send(f"❌ Error: {msg}")

Exception handling is built into command handlers.
Errors are logged automatically.


# ============================================================================
# 10) TESTING THE SYSTEM
# ============================================================================

Test rewards (in-game):
  1. Have 2+ players
  2. Start a quick test game
  3. End game and check:
     !balance           -> Should show updated coins/stats
     !profile           -> Should show updated wins/losses
     !leaderboard       -> Should show updated rankings

Test shop:
  1. !shop              -> List items
  2. !buyvoteeffect dramatic  -> Buy with coins
  3. !inventory         -> Confirm purchase
  4. !equipvoteeffect dramatic -> Equip it
  5. Test a vote        -> Should show dramatic effect

Test progression:
  1. Play multiple games
  2. !rank              -> Check XP progress
  3. Get to 100 XP -> Should level up (check logs)
  4. !profile           -> Confirm level increased


# ============================================================================
# COMMON ISSUES & TROUBLESHOOTING
# ============================================================================

Q: "MONGODB_URI environment variable not set"
A: Create .env file with MONGODB_URI from MongoDB Atlas

Q: Commands not loading
A: Check that bot/commands/__init__.py exists (can be empty)
   Check bot logs for setup errors

Q: Coins not awarded after game
A: Verify on_game_ended was called with correct parameters
   Check economy logs: !transactionhistory

Q: Database connection errors
A: Verify MongoDB URI is correct
   Check MongoDB Atlas firewall allows bot's IP
   Confirm cluster is active

Q: Votes not showing effect
A: Verify render_vote() is called in vote display logic
   Check that effect ID is valid
   Ensure user owns effect before equipping

"""
