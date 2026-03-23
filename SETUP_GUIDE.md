############################################################################
#                                                                          #
#  DISCORD MAFIA BOT - MONETIZATION & PROGRESSION SYSTEM                  #
#  Complete Integration & Setup Guide                                     #
#                                                                          #
############################################################################

## QUICK START

### 1. Environment Setup

Create .env file at project root:

    DISCORD_TOKEN=your_bot_token_from_discord_dev_portal
    MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/discord_bot?retryWrites=true&w=majority
    MONGO_DB_NAME=discord_bot
    COMMAND_PREFIX=!
    DAILY_REWARD_COINS=500
    DAILY_COOLDOWN_HOURS=24


### 2. Install Dependencies

    pip install -r requirements.txt


### 3. Run the Bot

    python main.py


## ARCHITECTURE OVERVIEW

The system is organized into clean, modular layers:

    database/
    ├── mongodb.py           → Async MongoDB connection
    └── repositories/        → Data access layer (atomic operations)
        ├── wallet_repository.py
        ├── profile_repository.py
        ├── inventory_repository.py
        └── economy_log_repository.py

    services/               → Business logic (transaction, rewards, leveling)
    ├── economy_service.py    → Coins/gems/rewards/stats
    ├── profile_service.py    → Levels/XP/cosmetics/progression
    ├── shop_service.py       → Catalog/purchase validation
    └── vote_effect_service.py → Voting cosmetics rendering

    bot/
    ├── commands/          → Command handlers (thin, validation only)
    │   ├── economy_commands.py
    │   ├── profile_commands.py
    │   ├── shop_commands.py
    │   └── vote_effect_commands.py
    └── events/
        └── game_events.py  → Game end rewards & progression

    models/               → Data structures
    ├── wallet.py
    ├── user_profile.py
    └── cosmetic_item.py

    utils/
    ├── embed_builder.py  → Discord embed styling
    ├── cooldowns.py      → Cooldown management
    └── formatter.py      → Text formatting

    main.py              → Bot entry point


## COMMAND REFERENCE

### Economy Commands
    !balance              Show coins, gems, and game stats
    !daily                Claim 500 coins (24hr cooldown)
    !leaderboard          Top richest and winners

### Profile Commands
    !profile [@user]      Show profile card with stats
    !rank                 Show level and XP progress
    !titles               List owned titles
    !equiptitle <name>    Equip a title
    !themes               List owned themes
    !equiptheme <name>    Equip a theme

### Shop Commands
    !shop [category]      Browse shop items
    !buy <item>          Purchase item with coins/gems
    !inventory           Show owned cosmetics

### Vote Effect Commands
    !voteeffects         List all vote effects
    !previewvoteeffect   See effect preview
    !buyvoteeffect       Purchase effect
    !equipvoteeffect     Equip effect


## INTEGRATION WITH EXISTING MAFIA BOT

Your Mafia game logic must call these two critical hooks:

### 1. Record Votes During Voting Phase

    from bot.events.game_events import get_game_events_handler

    # When user votes:
    handler = get_game_events_handler()
    await handler.on_player_voted(user_id, guild_id)


### 2. Award Rewards & Record Stats When Game Ends

    from bot.events.game_events import get_game_events_handler

    # At game end:
    handler = get_game_events_handler()
    await handler.on_game_ended(
        guild_id=ctx.guild.id,
        winners=[user_id1, user_id2],
        losers=[user_id3, user_id4],
        role_map={
            user_id1: "mafia",
            user_id2: "doctor",
            user_id3: "villager",
            user_id4: "detective",
        },
        votes_cast={
            user_id1: 3,  # votes this player cast
            user_id2: 2,
            user_id3: 4,
            user_id4: 2,
        },
    )


### 3. (Optional) Render Vote Effects

    from services.vote_effect_service import VoteEffectService

    # When displaying a vote in chat:
    vote_text = await vote_effect_service.render_vote(
        user_id=voter_id,
        guild_id=guild_id,
        voter_name=voter.name,
        target_name=target.name,
    )

    # Use vote_text instead of plain "X votes for Y"
    await ctx.send(vote_text)


## REWARD RULES

After **on_game_ended()** is called:

### Coins Awarded:

    Mafia Win:          +150 coins
    Villager Win:       +100 coins
    Participation:      +50 coins (all players)
    Per Vote Cast:      +10 coins each

### XP Awarded:

    Winner:             +50 XP
    Loser:              +25 XP
    No Show:            0 XP

### Level System:

    Level 1:            0-100 XP
    Level 2:            100-200 XP (cumulative)
    Level 3:            200-300 XP (cumulative)
    No cap              Scales infinitely


## DATABASE SCHEMA

MongoDB collections auto-created on startup:

### wallets
    {
      user_id: number,
      guild_id: number,
      coins: number,
      gems: number,
      total_wins: number,
      total_losses: number,
      games_played: number,
      votes_cast: number,
      created_at: date,
      last_daily_claim: date
    }

### profiles
    {
      user_id: number,
      guild_id: number,
      display_name: string,
      avatar_url: string,
      level: number,
      xp: number,
      wins: number,
      losses: number,
      games_played: number,
      equipped_title: string,
      equipped_theme: string,
      votes_cast: number,
      unlocked_cosmetics: [string],
      favorite_role: string,
      created_at: date,
      updated_at: date
    }

### inventory
    {
      user_id: number,
      guild_id: number,
      owned_item_ids: [string],
      equipped_vote_effect: string,
      created_at: date,
      updated_at: date
    }

### economy_logs
    {
      user_id: number,
      guild_id: number,
      tx_type: string,
      amount: number,
      reason: string,
      created_at: date
    }


## SHOP CATALOG

### Vote Effects: [Common to Epic]
    default_vote          0 coins     (free)
    dramatic_vote         200 coins
    stylish_vote          300 coins
    fire_vote             400 coins
    shadow_vote           500 coins
    royal_vote            600 coins
    glitch_vote           400 coins
    neon_vote             500 coins
    premium_gold_vote     100 gems    (premium)

### Titles: [Common to Epic]
    rookie_title           0 coins     (free)
    detective_mind_title   250 coins
    night_hunter_title     400 coins
    town_hero_title        50 gems     (premium)

### Themes: [Common to Epic]
    classic_theme          0 coins     (free)
    midnight_theme         300 coins
    ember_theme            400 coins
    aurora_theme           75 gems     (premium)


## SERVICE API REFERENCE

### EconomyService

    async get_wallet(user_id, guild_id) → Wallet
    async add_coins(user_id, guild_id, amount, reason) → (bool, str)
    async remove_coins(user_id, guild_id, amount, reason) → (bool, str)
    async add_gems(user_id, guild_id, amount, reason) → (bool, str)
    async remove_gems(user_id, guild_id, amount, reason) → (bool, str)
    async can_afford_coins(user_id, guild_id, amount) → bool
    async can_afford_gems(user_id, guild_id, amount) → bool
    async claim_daily_bonus(user_id, guild_id) → (bool, str)
    async add_game_rewards(...) → (bool, str)
    async record_game_stat(user_id, guild_id, is_winner) → None
    async get_top_richest(guild_id, limit=10) → list
    async get_top_winners(guild_id, limit=10) → list
    async get_transaction_history(user_id, guild_id, limit=10) → list


### ProfileService

    async get_profile(user_id, guild_id) → UserProfile
    async add_xp(user_id, guild_id, amount) → (bool, new_level or None)
    async add_game_xp(user_id, guild_id, is_winner, participated) → (bool, new_level or None)
    async get_win_rate(user_id, guild_id) → float
    async set_equipped_title(user_id, guild_id, title) → bool
    async set_equipped_theme(user_id, guild_id, theme) → bool
    async set_display_name(user_id, guild_id, name) → bool
    async set_favorite_role(user_id, guild_id, role) → bool
    async increment_votes_cast(user_id, guild_id) → bool
    async add_unlocked_cosmetic(user_id, guild_id, cosmetic_id) → bool
    async has_cosmetic(user_id, guild_id, cosmetic_id) → bool


### VoteEffectService

    def get_effect_catalog() → dict
    def get_effect(effect_id) → CosmeticItem or None
    def list_purchasable_effects() → list
    async unlock_effect(user_id, guild_id, effect_id) → bool
    async equip_effect(user_id, guild_id, effect_id) → bool
    async get_equipped_effect(user_id, guild_id) → str (effect_id)
    async render_vote(user_id, guild_id, voter_name, target_name) → str
    async preview_effect(effect_id) → str


### ShopService

    def get_catalog() → dict
    def get_item(item_id) → CosmeticItem or None
    def list_by_category(category) → list
    def list_purchasable() → list
    async purchase_item(user_id, guild_id, item_id, user_coins, user_gems) → (bool, str)
    def get_item_format(item) → str


## ERROR HANDLING

All service methods use pattern: `(success: bool, message: str)`

Example:

    success, msg = await economy.add_coins(user_id, guild_id, 100)
    if success:
        await ctx.send(f"✓ {msg}")
    else:
        await ctx.send(f"❌ {msg}")


## IMPORTANT NOTES

### Safety & Fairness

✓ Cosmetics are visual-only, do not affect gameplay
✓ Vote effects don't change vote counts or elimination logic
✓ All coin/gem transactions are atomic (MongoDB updates)
✓ Daily bonus includes 24-hour cooldown
✓ No negative balances allowed
✓ Automatic transaction audit logging


### Production Readiness

✓ All MongoDB operations use atomic updates
✓ Upsert enabled for consistency
✓ Indexes created on all queryable fields
✓ Connection pooling via Motor
✓ Async/await throughout
✓ Logging integrated
✓ Error handling in all services


## TESTING

Test workflow:

    1. Create .env with valid MongoDB and Discord Bot token
    2. pip install -r requirements.txt
    3. python main.py
    4. In Discord:
       !balance              → Show 0 coins (new user)
       !daily                → Claim 500 coins
       !balance              → Show 500 coins
       !shop                 → Browse items
       !buy "Dramatic Vote"  → Purchase effect
       !inventory            → Confirm ownership
       !voteeffects          → List effects
       !equipvoteeffect dramatic  → Equip it
       !profile              → Show updated stats
       !leaderboard          → Show richest/winners

    5. Complete a test game with rewards enabled


## TROUBLESHOOTING

❌ "MongoDB connection failed"
✓ Check MONGODB_URI is correct
✓ Verify cluster is active in MongoDB Atlas
✓ Check IP whitelist in MongoDB Atlas allows your IP

❌ "Commands not loading"
✓ Check bot/commands/__init__.py exists
✓ Review main.py logs for setup errors
✓ Verify all imports in command files work

❌ "No coins awarded after game"
✓ Verify on_game_ended() is being called
✓ Check role_map and winners/losers lists are populated
✓ Review economy logs: missing entries indicate no call happened

❌ "Wallet creation failed"
✓ Check MongoDB wallets collection exists
✓ Verify user_id and guild_id are valid integers
✓ Review MongoDB error logs


## EXTENDING THE SYSTEM

To add a new cosmetic:

1. Add to SHOP_CATALOG in services/shop_service.py:

       "my_new_effect": CosmeticItem(
           id="my_new_effect",
           name="My Effect",
           category="vote_effect",
           price_coins=250,
           description="Cool effect!",
           rarity="uncommon",
           unlock_type="purchase",
       )

2. Add render template to VoteEffectService.render_vote()

3. Optionally add command to handle it

4. That's it! Auto-available in !shop


## FILES GENERATED

Core Implementation:
  ✓ database/mongodb.py
  ✓ database/repositories/*.py
  ✓ services/*.py
  ✓ models/*.py
  ✓ bot/commands/*.py
  ✓ utils/*.py
  ✓ config/settings.py
  ✓ bot/events/game_events.py
  ✓ main.py

Configuration:
  ✓ requirements.txt
  ✓ .env.example
  ✓ INTEGRATION_GUIDE.md (this file)


## NEXT STEPS

1. Configure .env with your MongoDB and Discord token
2. Install requirements: pip install -r requirements.txt
3. Review main.py to understand bot initialization
4. Integrate on_game_ended() into your Mafia game logic
5. Test with !daily, !shop, !balance commands
6. Launch in Discord!


---

Built for production with clean, maintainable, modular architecture.
Ready to scale and extend.

Questions? Review the service docstrings and type hints throughout codebase.
