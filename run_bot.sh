#!/bin/bash
# Quick Launch Script
# Save as: /home/manoj/Desktop/discord_bot/run_bot.sh
# Usage: bash run_bot.sh

cd /home/manoj/Desktop/discord_bot
echo "Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "========================================="
echo "Discord Bot - Monetization System"
echo "========================================="
echo ""
echo "Starting bot..."
echo ""

python main.py
