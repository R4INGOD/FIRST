---
name: reel-scout
description: Find out what a TikTok, Instagram Reel, YouTube Short or X video is about. Use whenever someone pastes a social media link (or a screenshot of a post) and asks what it is, what they're talking about, what product / place / song / app / AI model is in it, or to transcribe it.
---

# reel-scout

`reel-scout` downloads the post, transcribes the speech with whisper, reads the frames with
Claude, and looks the subject up on the web. Installed by `ops/reel-scout/install.sh`.

## Run it

```bash
reel-scout "<link>"                       # markdown report on stdout
reel-scout "<link>" --question "what's the price?"
reel-scout "<link>" --no-search           # skip the web lookup (faster, cheaper)
reel-scout ~/Desktop/screenshot.png       # a screenshot or a downloaded video works too
reel-scout "<link>" --cookies-from-browser chrome   # Instagram, private or age-gated posts
reel-scout "<link>" --json                # everything, including the transcript segments
```

Reports and frames are kept under `~/reel-scout/<date>-<post id>/` (`report.md`, `analysis.json`, `frames/`).

## How to answer

- Run the command, then give the person the answer in two or three lines: the thing being
  talked about, the one-line takeaway, the best link from "Found on the web". Then paste
  the rest of the report only if they asked for detail or a transcript.
- Several links in one message: run them one after the other, one short block per link.
- If yt-dlp says the platform wants a login, re-run with `--cookies-from-browser chrome`
  (Safari: `safari`). Do not try other download tools.
- If the report's confidence is under 50%, say so and quote the on-screen text so the
  person can judge.
- Never paste `ANTHROPIC_API_KEY` or cookies into a message or a file.
