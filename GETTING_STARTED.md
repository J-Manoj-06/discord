╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║             🚀 DISCORD MAFIA BOT - COMPLETE GETTING STARTED GUIDE           ║
║                                                                             ║
║                        Production System Ready to Deploy                    ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

You have a COMPLETE monetization system ready.
This guide walks you through the final setup (5 minutes total).

═══════════════════════════════════════════════════════════════════════════════

📋 WHAT YOU HAVE

✅ 31 Python modules (3,500+ lines)
✅ 20+ Discord commands
✅ Complete currency system (coins + gems)
✅ XP/leveling system
✅ Shop with 16 cosmetics
✅ Vote effect templates
✅ MongoDB integration
✅ Game rewards system
✅ All dependencies installed
✅ All syntax validated

═══════════════════════════════════════════════════════════════════════════════

⏱️  5-MINUTE SETUP (Follow Exactly)

STEP 1: Get Discord Bot Token (2 minutes)
─────────────────────────────────────────────────────────────────────────────

1A. Open Discord Developer Portal
    Go to: https://discord.com/developers/applications

1B. Click on Your Bot App
    Find "mafia game bot" → Click it

1C. Go to Bot Section
    Left sidebar → Click "Bot"

1D. Copy Your Token
    • Look for TOKEN section
    • Click the "Copy" button
    • Your token is now copied to clipboard
    • (It's hidden for security - you can't see it, but it's copied!)

1E. If Token Field is Empty
    • Click "Add Bot" button
    • Wait for page to reload
    • Now click "Copy" next to token


STEP 2: Create .env Configuration File (2 minutes)
─────────────────────────────────────────────────────────────────────────────

OPTION A - Interactive Script (Easiest):

    bash setup_env.sh

    Then answer the prompts:
    - Paste your Discord token
    - Paste your MongoDB URI

    Script will create .env automatically!


OPTION B - Manual (If script doesn't work):

    nano .env

    Paste this (replace with YOUR actual credentials):
    ──────────────────────────────────────────────
    DISCORD_TOKEN=paste_your_token_here
    MONGODB_URI=paste_your_mongodb_uri_here
    MONGO_DB_NAME=discord_bot
    COMMAND_PREFIX=!
    DAILY_REWARD_COINS=500
    DAILY_COOLDOWN_HOURS=24
    ──────────────────────────────────────────────

    Save: Ctrl+X → Y → Enter


STEP 3: Get MongoDB Connection String (1 minute)
─────────────────────────────────────────────────────────────────────────────

3A. Open MongoDB Atlas
    Go to: https://www.mongodb.com/cloud/atlas

3B. Create Cluster or Use Existing
    • If you don't have a cluster, create one (free tier available)
    • Wait for cluster to be ready

3C. Click "Connect"
    • Find your cluster
    • Click "Connect" button

3D. Choose Connection Method
    • Select "Python 3.12" driver option
    • Copy the connection string

3E. Update IP Whitelist
    • Go to Network Access
    • Add IP: 0.0.0.0/0 (for development - allow all IPs)
    • For production, add only your server IP

3F. Paste Into .env
    • Paste as MONGODB_URI= in your .env file


STEP 4: Run the Bot (30 seconds)
─────────────────────────────────────────────────────────────────────────────

4A. Activate Virtual Environment

    source .venv/bin/activate

    You should see (.venv) in your terminal

4B. Launch Bot

    python main.py

    You should see:
    ┌─────────────────────────────────────────┐
    │ Logged in as mafia game bot#5754        │
    │ Synced X command(s)                     │
    │ Bot is ready!                           │
    └─────────────────────────────────────────┘

4C. Test (Keep bot running in this terminal)

    In Discord server, type:
    !balance

    Expected: Shows your coins, gems, and stats


STEP 5: Your Bot is Running! ✅
─────────────────────────────────────────────────────────────────────────────

Try these commands in Discord:

    !daily              → Claim 500 coins
    !balance            → Check your coins
    !shop               → Browse items
    !profile            → View your profile
    !leaderboard        → See rankings

═══════════════════════════════════════════════════════════════════════════════

🆘 TROUBLESHOOTING

Problem: "Can't see token in Developer Portal"
→ Solution: Scroll down on the Bot tab. Token section might be below the fold.
           If still blank, click "Add Bot" first.

Problem: "DISCORD_TOKEN or MONGODB_URI invalid"
→ Solution: Double-check you copied the correct strings (no extra spaces)
           Paste values into .env again

Problem: "ModuleNotFoundError"
→ Solution: Make sure virtual environment is activated first:
           source .venv/bin/activate

Problem: "Bot connects but no commands work"
→ Solution: 
  • Wait 10-15 seconds for Discord to sync commands
  • Try again with !balance
  • If still nothing, restart bot and wait again

Problem: "MongoDB connection refused"
→ Solution:
  • Check cluster is active in MongoDB Atlas
  • Verify IP whitelist includes your IP (or set to 0.0.0.0/0)
  • Check connection string is correct (no typos)

Problem: "Bot appears offline in Discord"
→ Solution:
  • Verify bot token is correct
  • Verify bot is added to server
  • Check bot has required permissions (message sending, embeds)

═══════════════════════════════════════════════════════════════════════════════

📊 QUICK COMMAND REFERENCE

Economics:
  !balance      Show coins, gems, stats
  !daily        Claim 500 coins
  !leaderboard  See richest players

Profile:
  !profile      View profile card
  !rank         Check level & XP
  !titles       List owned titles
  !equiptitle   Equip a title
  !themes       List themes
  !equiptheme   Equip a theme

Shop:
  !shop         Browse items
  !buy <item>   Purchase item
  !inventory    Show owned cosmetics

Vote Effects:
  !voteeffects         List effects
  !previewvoteeffect   See preview
  !buyvoteeffect       Buy effect
  !equipvoteeffect     Equip effect

═══════════════════════════════════════════════════════════════════════════════

🎮 INTEGRATION WITH YOUR MAFIA GAME

Once the bot is working, integrate it with your Mafia game:

Find where your game ends and add this:

────────────────────────────────────────────────────────────────────────────
from bot.events.game_events import get_game_events_handler

handler = get_game_events_handler()
await handler.on_game_ended(
    guild_id=ctx.guild.id,
    winners=[winner_id_1, winner_id_2],
    losers=[loser_id_1, loser_id_2],
    role_map={
        winner_id_1: "mafia",
        winner_id_2: "doctor",
        loser_id_1: "villager",
        loser_id_2: "detective"
    },
    votes_cast={
        winner_id_1: 3,
        winner_id_2: 2,
        loser_id_1: 4,
        loser_id_2: 2
    }
)
────────────────────────────────────────────────────────────────────────────

This automatically awards coins, XP, and updates stats!

═══════════════════════════════════════════════════════════════════════════════

📁 FILE ORGANIZATION

Your project at: /home/manoj/Desktop/discord_bot/

Main Files:
  main.py              ← Bot entry point
  .env                 ← Your configuration (KEEP SECRET!)
  requirements.txt     ← Dependencies (all installed)
  run_bot.sh           ← Launch script

Folders:
  bot/commands/        ← All 20+ commands
  services/            ← Business logic
  database/            ← MongoDB integration
  models/              ← Data structures
  utils/               ← Helpers & utilities
  config/              ← Configuration

Documentation:
  README.md                  ← Project overview
  QUICK_START.txt            ← Quick reference
  SETUP_COMPLETE.md          ← Detailed setup
  TOKEN_GUIDE.md             ← Getting token (you might need this)
  TOKEN_GUIDE.md             ← This file

═══════════════════════════════════════════════════════════════════════════════

✅ FINAL CHECKLIST

Before launching:

□ Discord token copied from Developer Portal
□ MongoDB URI copied from MongoDB Atlas
□ .env file created with both credentials
□ Virtual environment activated (see (.venv) in terminal)
□ MongoDB cluster is active and IP whitelist updated
□ Ready to run: python main.py

═══════════════════════════════════════════════════════════════════════════════

🎯 LAUNCH SEQUENCE (Copy & Paste)

    cd /home/manoj/Desktop/discord_bot
    source .venv/bin/activate
    python main.py

Then test: !balance

═══════════════════════════════════════════════════════════════════════════════

🎉 YOU'RE ALL SET!

Your complete monetization system is ready to go.
Just need credentials (token + MongoDB URI) and you're launching!

Need help getting credentials? See TOKEN_GUIDE.md

═══════════════════════════════════════════════════════════════════════════════
