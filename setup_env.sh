#!/bin/bash
# setup_env.sh - Interactive .env file creation
# Usage: bash setup_env.sh

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Discord Bot - Environment Setup Script             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. Your existing .env is safe."
        exit 1
    fi
fi

echo ""
echo "📝 Enter your Discord Bot Token"
echo "(Get it from: https://discord.com/developers/applications → Your App → Bot → Copy Token)"
echo ""
read -p "Discord Token: " DISCORD_TOKEN

if [ -z "$DISCORD_TOKEN" ]; then
    echo "❌ Token cannot be empty!"
    exit 1
fi

echo ""
echo "📝 Enter your MongoDB Connection String"
echo "(Get it from: https://www.mongodb.com/cloud/atlas → Cluster → Connect → Python)"
echo ""
read -p "MongoDB URI: " MONGODB_URI

if [ -z "$MONGODB_URI" ]; then
    echo "❌ MongoDB URI cannot be empty!"
    exit 1
fi

echo ""
echo "Creating .env file..."
echo ""

cat > .env << EOF
# Discord Bot Configuration
DISCORD_TOKEN=$DISCORD_TOKEN

# MongoDB Configuration
MONGODB_URI=$MONGODB_URI
MONGO_DB_NAME=discord_bot

# Bot Settings
COMMAND_PREFIX=!
DAILY_REWARD_COINS=500
DAILY_COOLDOWN_HOURS=24
EOF

echo "✅ .env file created successfully!"
echo ""
echo "Contents:"
echo "──────────────────────────────────────────────"
cat .env
echo "──────────────────────────────────────────────"
echo ""
echo "🚀 Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Run bot: python main.py"
echo "  3. Test in Discord: !balance"
