#!/usr/bin/env python3
"""MCP server for reel-scout. One tool: analyze_reel(url).

Register in Claude Code (stdio):
  claude mcp add reel-scout -- ~/reel-scout-env/bin/python ~/FIRST/ops/reel-scout/mcp_server.py
Or in Claude Desktop's claude_desktop_config.json, same command/args.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer  # mcp >= 2.0

import reel_scout

server = MCPServer(
    name="reel-scout",
    instructions=(
        "Give analyze_reel a TikTok / Instagram Reel / YouTube Short / X link (or a local video or "
        "screenshot path). It downloads the post, transcribes the speech, reads the frames and "
        "returns a markdown report: what the post is about, what is shown and said, the product, "
        "place, song or app being talked about, and what the web says about it."
    ),
)


@server.tool()
def analyze_reel(url: str, question: str = "", search: bool = True, cookies_from_browser: str = "") -> str:
    """Analyse a social media video or photo post and report what it is about.

    Args:
        url: post link or a local file path (video, image, screenshot).
        question: optional specific question to answer about the post.
        search: also look the subject up on the web (default true).
        cookies_from_browser: 'chrome', 'safari' or 'firefox' when the platform needs a login.
    """
    try:
        result = reel_scout.analyze(
            url, search=search, question=question,
            cookies_from_browser=cookies_from_browser or None,
        )
    except SystemExit as e:  # reel_scout reports user-facing failures via SystemExit
        return f"reel-scout could not analyse this post: {e}"
    return result["report_markdown"]


if __name__ == "__main__":
    server.run("stdio")
