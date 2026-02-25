#!/bin/bash
# SPX Day Trader - Local Launcher
# Double-click the desktop shortcut or run: bash start_bot.sh

set -e

PROJECT_DIR="/mnt/c/Users/gmroa/spy-options-employee"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  SPX Day Trader - Starting Up"
echo "=========================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "[OK] Virtual environment activated"
else
    echo "[ERROR] .venv not found at $PROJECT_DIR/.venv"
    echo "Create it with: python3 -m venv .venv && pip install -r requirements.txt"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for .env
if [ ! -f ".env" ]; then
    echo "[ERROR] No .env file found!"
    echo "Copy .env.template to .env and fill in your API keys."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check DISCORD_TOKEN is set
if ! grep -q "DISCORD_TOKEN=." .env 2>/dev/null; then
    echo "[ERROR] DISCORD_TOKEN not set in .env"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[OK] .env file found"
echo ""
echo "Starting bot + webhook server on port 8000..."
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

python3 -m src.main
