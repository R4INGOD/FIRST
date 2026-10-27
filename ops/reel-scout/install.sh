#!/usr/bin/env bash
# One-time setup for reel-scout on a Mac (mini or MacBook) or Ubuntu/WSL.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV="${REEL_SCOUT_ENV:-$HOME/reel-scout-env}"

if [[ "$(uname)" == "Darwin" ]]; then
  command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
  brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
  brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
  PY="$(brew --prefix python@3.12)/bin/python3.12"
else
  sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg python3-venv
  PY=python3
fi

"$PY" -m venv "$ENV"
"$ENV/bin/pip" install -q --upgrade pip
"$ENV/bin/pip" install -q -r "$HERE/requirements.txt"

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/reel-scout" <<WRAP
#!/usr/bin/env bash
exec "$ENV/bin/python" "$HERE/reel_scout.py" "\$@"
WRAP
chmod +x "$HOME/.local/bin/reel-scout"

mkdir -p "$HOME/.claude/skills"
ln -sfn "$HERE" "$HOME/.claude/skills/reel-scout"

echo
echo "reel-scout installed."
echo "  CLI:   ~/.local/bin/reel-scout <link>        (add ~/.local/bin to PATH if needed)"
echo "  Skill: ~/.claude/skills/reel-scout -> $HERE"
echo "  MCP:   claude mcp add reel-scout -- $ENV/bin/python $HERE/mcp_server.py"
echo
echo "Set ANTHROPIC_API_KEY in your shell profile (or ~/.claude/settings.json env) before the first run."
echo "The first run downloads the whisper model (~500 MB for 'small')."
