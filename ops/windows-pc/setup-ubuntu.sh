#!/usr/bin/env bash
# Milestone lead bot: Windows PC setup, part 2 of 2. Run inside Ubuntu (WSL):
#   bash setup-ubuntu.sh
set -euo pipefail

echo "== Ubuntu packages =="
sudo apt-get update
sudo apt-get install -y git curl jq unzip

echo "== Claude Code =="
if ! command -v claude >/dev/null 2>&1; then
  curl -fsSL https://claude.ai/install.sh | bash
fi

mkdir -p ~/milestone-leads

echo "== Start the bot at every Windows sign-in (restarts it if it stops) =="
appdata_win=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d '\r')
startup="$(wslpath "$appdata_win")/Microsoft/Windows/Start Menu/Programs/Startup"
printf '%s\r\n' \
  '@echo off' \
  'title Milestone lead bot - leave this window open' \
  ':loop' \
  'wsl.exe -d Ubuntu --cd ~ -- bash -lc "cd ~/milestone-leads && claude remote-control"' \
  'timeout /t 30 /nobreak >nul' \
  'goto loop' > "$startup/milestone-lead-bot.cmd"

echo
echo "Part 2 done. Last steps:"
echo "  1. Run:  cd ~/milestone-leads && ~/.local/bin/claude"
echo "     Sign in with the Milestone Claude account, accept the folder, then type /exit"
echo "  2. Restart the PC. The 'Milestone lead bot' window opens by itself."
