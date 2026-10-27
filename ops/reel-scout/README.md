# reel-scout: "what is this reel about?"

Send it a social media link. It tells you what the video is about, what is said, what is
shown on screen, and names the thing they are talking about (product, place, song, app,
AI model, recipe...), then finds that thing on the web.

```
$ reel-scout "https://www.tiktok.com/@hectorjudyfinds/photo/7..."

# Underdog Saluki 27B
**A 2-bit quantised version of Qwen 3.8 27B that fits under 8 GB and keeps ~96% of the benchmarks.**
Type: ai_model · Category: software_ai · Confidence: 92%
...
## Found on the web
**Found:** Underdog Saluki 27B, https://underdog.ai/saluki
...
```

## What it does, step by step

| Step | Tool | Notes |
|---|---|---|
| Download the post + caption, hashtags, music | `yt-dlp` | TikTok, Instagram, YouTube, X, Facebook, Snapchat spotlight... A local video, image or screenshot path works too. |
| Pull audio and frames | `ffmpeg` | 4 to 12 evenly spaced frames (one per ~2.5 s). Photo posts and slideshows use their images. |
| Transcribe | `faster-whisper` (local, free) | Model `small` by default; `medium` is better for French-English mixes. |
| Understand | Claude (`claude-opus-5-5`, vision + structured output) | Reads overlays, tweets, labels, prices, URLs; cross-checks the transcript against on-screen text. |
| Find it | Claude web search | Official page, price, availability, claim check. `--no-search` skips it. |

Output: a markdown report on stdout, plus `~/reel-scout/<date>-<id>/{report.md, analysis.json, frames/}`.

## Install (Mac mini, MacBook, or the Windows PC's Ubuntu)

```bash
cd ~/FIRST && git pull
bash ops/reel-scout/install.sh
```

The script installs ffmpeg, makes a Python venv at `~/reel-scout-env`, puts a `reel-scout`
command in `~/.local/bin`, links the Claude Code skill into `~/.claude/skills/reel-scout`, and
prints the `claude mcp add` line.

Then set the API key once (same place as the Twenty CRM keys, `~/.claude/settings.json` `env`,
or `export ANTHROPIC_API_KEY=...` in `~/.zshrc`). Never commit it.

First run downloads the whisper model (about 500 MB for `small`). On a Mac mini a 60 s reel
takes 30 to 90 s end to end; most of it is whisper.

## Three ways to send it a link

1. **Claude Code / Remote Control (skill).** Just paste the link in a Claude Code session on the
   Mac mini: "what's this about? <link>". The `reel-scout` skill runs the command and answers.
2. **MCP server.** For Claude Desktop, Claude Code on another machine, or any MCP client:
   `claude mcp add reel-scout -- ~/reel-scout-env/bin/python ~/FIRST/ops/reel-scout/mcp_server.py`.
   One tool, `analyze_reel(url, question?, search?, cookies_from_browser?)`, returns the report.
3. **Hermes on Mattermost.** Add a tool wrapper that runs
   `~/.local/bin/reel-scout "$URL" --no-search` and posts stdout back to the channel. Any
   message containing a tiktok.com / instagram.com / youtube.com / x.com link can trigger it.

## Cost

Per post, roughly: 8 to 12 frames at ~1,000 tokens each plus transcript, so about 15k input
tokens and 1k output on Opus 5.5 ($4 / $20 per million): around 8 cents for the analysis, and
a further 10 to 25 cents when the web lookup runs (searches are billed on top). Set
`REEL_SCOUT_MODEL=claude-sonnet-5-5` to halve that. Whisper is free.

## Flags

```
--question "..."             ask something specific about the post
--no-search                  skip the web lookup
--json                       full JSON (metadata, transcript segments, analysis, lookup)
--out DIR                    where to keep reports (default ~/reel-scout, or $REEL_SCOUT_OUT)
--cookies-from-browser NAME  chrome | safari | firefox, for posts that need a login
--cookies FILE               Netscape cookies.txt instead
--whisper NAME               tiny | base | small | medium | large-v3 (or $REEL_SCOUT_WHISPER)
--model ID                   Claude model (or $REEL_SCOUT_MODEL)
--max-frames N               default 12
--keep-download              keep the downloaded media next to the report
```

## When it fails

- **"wants a logged-in session"**: Instagram almost always, TikTok sometimes. Re-run with
  `--cookies-from-browser chrome` on a machine where that browser is signed in.
- **Wrong or vague subject**: look at `frames/` in the output folder. If the frame that matters
  (a product label, a tweet) was missed, raise `--max-frames 20`.
- **No transcript**: the post has music only, or faster-whisper is not in the venv. Analysis
  still runs on frames and caption.
- **Claude declined**: the model's safety filter stopped on this content; the report says why.
  Server-side fallback to another Claude model is enabled by default, so this is rare.

## Files

- `reel_scout.py`: the whole pipeline, usable as a CLI or imported (`reel_scout.analyze(url)`).
- `mcp_server.py`: MCP wrapper (stdio).
- `SKILL.md`: Claude Code skill.
- `install.sh`, `requirements.txt`.
