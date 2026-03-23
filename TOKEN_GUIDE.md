🔐 HOW TO GET YOUR DISCORD BOT TOKEN
═══════════════════════════════════════════════════════════════════

STEP-BY-STEP VISUAL GUIDE

STEP 1: Open Discord Developer Portal
────────────────────────────────────────────────────────────────
Go to: https://discord.com/developers/applications
(This is where you already are in your screenshots)

STEP 2: Select Your Bot Application
────────────────────────────────────────────────────────────────
Look for "mafia game bot" in the left sidebar
Click on it to select it

STEP 3: Click "Bot" in Left Sidebar
────────────────────────────────────────────────────────────────
In left sidebar under your app name, you'll see:
  • Overview
  • General Information
  • Installation
  • OAuth2
  • Bot ← CLICK HERE
  • Emojis
  • Webhooks
  • Rich Presence
  • App Testers
  • App Verification
  • Games
  • Activities
  • Monetization

STEP 4: Find the TOKEN Section
────────────────────────────────────────────────────────────────
Once you click "Bot", scroll down to find a section labeled:

    TOKEN
    ┌─────────────────────────────────────────────────────┐
    │ For security purposes, tokens can only be viewed    │
    │ once, when created. If you forgot or lost access to │
    │ your token, please regenerate a new one.            │
    │                                                       │
    │ [Reset Token] button                                │
    └─────────────────────────────────────────────────────┘

STEP 5: Click "Copy Token" Button
────────────────────────────────────────────────────────────────
Next to the token field, there's a button that says:
    [Copy]

Click "Copy" - this copies the hidden token to your clipboard

STEP 6: Create .env File
────────────────────────────────────────────────────────────────
In your terminal:

    cd /home/manoj/Desktop/discord_bot
    nano .env

STEP 7: Paste Token
────────────────────────────────────────────────────────────────
Right-click or Ctrl+V to paste your token. Your .env should look like:

    DISCORD_TOKEN=MzI4NDUyMzM2NzMwOTAwOTkyLjG5xjH.GDm_KA.P9z1z9z9z9z9z9z9z9z9z9z9z9z9z9z9z9z9z9z
    MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
    MONGO_DB_NAME=discord_bot
    COMMAND_PREFIX=!
    DAILY_REWARD_COINS=500
    DAILY_COOLDOWN_HOURS=24

STEP 8: Save File
────────────────────────────────────────────────────────────────
Press: Ctrl+X
Then: Y
Then: Enter

✅ Done! Your token is now saved.

═══════════════════════════════════════════════════════════════════

WHAT IF YOU STILL DON'T SEE THE TOKEN?

Problem: The token field appears blank or empty

Solution:
  1. Go to "Bot" section (if not already there)
  2. Look for an "Add Bot" or "Create Bot" button
  3. Click it to create a bot user
  4. Now the token should appear

═══════════════════════════════════════════════════════════════════

TROUBLESHOOTING

Q: I clicked Copy but nothing happened
A: The button worked - the token is in your clipboard. Paste it in .env with Ctrl+V

Q: The token looks like: MzI4NDUxMzM2NzMwOTAwOTky.GXXxxx...
A: That's correct! Long strings with dots are normal Discord tokens.

Q: Can I see the token after copying?
A: No - Discord only shows tokens once for security. If you lose it, click "Reset Token"

Q: What if I reset the token?
A: A new one is generated. You'll need to update it in your .env file.

═══════════════════════════════════════════════════════════════════

NEXT STEPS

Once you have DISCORD_TOKEN in .env:

1. Activate virtual environment:
   source .venv/bin/activate

2. Run the bot:
   python main.py

3. Test in Discord:
   !balance

═══════════════════════════════════════════════════════════════════

SCREENSHOT REFERENCE

You showed two screenshots:

Screenshot 1 (OAuth2/Authorization tab):
  - Shows "Reset Token" button
  - This is NOT the token itself
  - You need to find the actual token field

Screenshot 2 (Bot tab):
  - Shows bot icon and username "mafia game bot"
  - Scroll DOWN past the Icon and Banner sections
  - The TOKEN section should be below

Look further down on the Bot page - the token field should be visible!

═══════════════════════════════════════════════════════════════════

QUICK CHECKLIST

□ Open https://discord.com/developers/applications
□ Click "mafia game bot" (select your app)
□ Click "Bot" in left sidebar
□ Scroll down to find TOKEN section
□ Click "Copy" button next to token
□ Create .env file in: /home/manoj/Desktop/discord_bot/
□ Paste token as: DISCORD_TOKEN=<your_token>
□ Add MongoDB URI
□ Save file (Ctrl+X, Y, Enter)
□ Run: source .venv/bin/activate
□ Run: python main.py

═══════════════════════════════════════════════════════════════════
