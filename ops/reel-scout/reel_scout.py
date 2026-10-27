#!/usr/bin/env python3
"""reel-scout: send it a social video link, get back what the video is about.

Pipeline
  1. download   yt-dlp fetches the post (TikTok, Instagram Reel, YouTube Short,
                X, Facebook ...) plus its caption, hashtags and music info.
                A local video, image or screenshot path works too.
  2. extract    ffmpeg pulls a 16 kHz audio track and N evenly spaced frames
                (a photo post or slideshow uses its images directly).
  3. transcribe faster-whisper (local, free) turns speech into text.
  4. analyze    Claude reads the frames, on-screen text, transcript and caption
                and returns a structured answer: what is shown, what is said,
                the product / place / song / app / model being talked about.
  5. lookup     Claude's web search finds the thing: official page, price,
                where to get it, whether the claim checks out.

Usage
  reel_scout.py <url-or-file> [--no-search] [--json] [--out DIR]
                [--question "..."] [--cookies-from-browser chrome]
                [--whisper small] [--model claude-opus-5-5] [--max-frames 12]
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_WHISPER = "small"
MAX_FRAMES = 12
MAX_IMAGE_SIDE = 1280
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac", ".opus", ".ogg"}

ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "summary", "language", "category", "main_subject", "what_is_shown",
        "what_is_said", "on_screen_text", "subjects", "claims", "call_to_action",
        "looks_sponsored", "search_queries", "confidence",
    ],
    "properties": {
        "summary": {"type": "string", "description": "2-3 plain sentences: what this post is about and why it was made."},
        "language": {"type": "string", "description": "Language(s) spoken or written, e.g. 'French', 'English with French captions'."},
        "category": {
            "type": "string",
            "enum": ["product", "place", "food_recipe", "music", "software_ai", "news_commentary",
                     "tutorial_howto", "entertainment_meme", "person_creator", "event", "service_business", "other"],
        },
        "main_subject": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "type", "one_line", "evidence"],
            "properties": {
                "name": {"type": "string", "description": "The thing they are talking about, named as precisely as possible (brand + model, venue + city, song + artist, app, repo...)."},
                "type": {"type": "string"},
                "one_line": {"type": "string", "description": "One line a busy person can act on."},
                "evidence": {"type": "string", "description": "Where in the frames / transcript / caption this comes from."},
            },
        },
        "what_is_shown": {"type": "string", "description": "Visual description across the frames: setting, people, objects, screen content, editing style."},
        "what_is_said": {"type": "string", "description": "Faithful condensed version of the spoken content. 'No speech (music only)' if applicable."},
        "on_screen_text": {"type": "array", "items": {"type": "string"}, "description": "Every readable caption, overlay, sign, tweet text, URL, handle, price."},
        "subjects": {
            "type": "array",
            "description": "Every identifiable named thing, most important first.",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["name", "type", "confidence", "evidence"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["product", "brand", "place", "person", "song", "app", "ai_model", "website", "repo", "recipe", "event", "book_film", "other"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
            },
        },
        "claims": {"type": "array", "items": {"type": "string"}, "description": "Concrete claims made (numbers, comparisons, promises) worth checking."},
        "call_to_action": {"type": "string", "description": "What the viewer is asked to do (follow, buy, link in bio, visit...). Empty string if none."},
        "looks_sponsored": {"type": "boolean"},
        "search_queries": {"type": "array", "items": {"type": "string"}, "description": "3-6 web searches that would find the main subject and verify the claims."},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "How sure you are about main_subject."},
    },
}

ANALYSIS_SYSTEM = """You analyse short-form social media posts (TikTok, Reels, Shorts, X) for a studio owner who wants to know, fast, what a post is actually about and what thing it is pointing at.

You receive: frames sampled from the video (or the images of a photo post), the speech transcript, and the post's caption, hashtags and music info. Read everything on screen: overlays, tweets, product labels, prices, URLs, handles, menus, UI. Combine visual and spoken evidence; when they disagree, say so in the evidence field.

Name things precisely (brand and model, venue and city, song and artist, app name, model name and version). Do not invent names that are not supported by what you see or hear; if the exact name is not visible, give the best description and lower the confidence. Transcripts can contain recognition errors, so cross-check names against on-screen text."""

LOOKUP_SYSTEM = """You help a studio owner act on a social media post. You are given a structured analysis of the post. Use web search to find the main subject and check the key claims. Prefer official sources (the maker's site, the venue's page, the app store, the GitHub repo, the artist's page).

Reply in short markdown with these sections, and nothing else:
**Found:** the thing, with the best link.
**Details:** price / availability / location / how to get it, whatever applies, as bullets.
**Claims check:** one bullet per claim: holds, overstated, or could not verify, with a link.
**Also relevant:** at most 3 bullets, only if useful.
Keep it under 250 words. Say plainly when something could not be found."""


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"[reel-scout] {msg}", file=sys.stderr, flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def need(binary: str) -> str:
    # look next to the running interpreter first (the venv's bin), then on PATH
    path = shutil.which(binary, path=str(Path(sys.executable).parent)) or shutil.which(binary)
    if not path:
        raise SystemExit(f"{binary} is not installed. See ops/reel-scout/README.md")
    return path


def fmt_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def slug(text: str, n: int = 40) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:n] or "post"


@dataclass
class Media:
    source: str
    kind: str                      # video | images | audio
    videos: list[Path] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    audio: Path | None = None
    info: dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------------
# 1. download
# ----------------------------------------------------------------------------

def fetch_media(source: str, workdir: Path, cookies_from_browser: str | None, cookies_file: str | None) -> Media:
    p = Path(source).expanduser()
    if p.exists():
        ext = p.suffix.lower()
        if ext in IMAGE_EXT:
            return Media(source, "images", images=[p], info={"title": p.name})
        if ext in AUDIO_EXT:
            return Media(source, "audio", audio=p, info={"title": p.name})
        return Media(source, "video", videos=[p], info={"title": p.name})

    ytdlp = need("yt-dlp")
    dl = workdir / "dl"
    dl.mkdir(parents=True, exist_ok=True)
    cmd = [
        ytdlp, "--no-playlist", "--no-warnings", "--write-info-json",
        "--write-thumbnail", "--convert-thumbnails", "jpg",
        "-f", "bv*[height<=720]+ba/b[height<=720]/b",
        "--merge-output-format", "mp4",
        "-o", str(dl / "%(id)s.%(ext)s"),
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    if cookies_file:
        cmd += ["--cookies", cookies_file]
    cmd.append(source)
    log("downloading with yt-dlp ...")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout).strip().splitlines()
        tail = "\n".join(err[-4:])
        hint = ""
        if re.search(r"login|cookies|private|rate.?limit|sign in", tail, re.I):
            hint = ("\nThis platform wants a logged-in session. Re-run with "
                    "--cookies-from-browser chrome (or safari / firefox).")
        raise SystemExit(f"yt-dlp failed:\n{tail}{hint}")

    info: dict[str, Any] = {}
    for j in dl.glob("*.info.json"):
        with open(j, encoding="utf-8") as fh:
            info = json.load(fh)
        break
    videos = sorted(f for f in dl.iterdir() if f.suffix.lower() in VIDEO_EXT)
    images = sorted(f for f in dl.iterdir() if f.suffix.lower() in IMAGE_EXT)
    audio = next((f for f in dl.iterdir() if f.suffix.lower() in AUDIO_EXT), None)
    if videos:
        return Media(source, "video", videos=videos[:1], info=info)
    if len(images) > 0:
        # photo post / slideshow: the thumbnail is one of the images, keep them all
        return Media(source, "images", images=images, audio=audio, info=info)
    if audio:
        return Media(source, "audio", audio=audio, info=info)
    raise SystemExit("yt-dlp finished but produced no video or image files")


def post_metadata(info: dict[str, Any]) -> dict[str, Any]:
    keep = ["extractor_key", "webpage_url", "title", "description", "uploader", "uploader_id",
            "channel", "upload_date", "duration", "view_count", "like_count", "comment_count",
            "track", "artist", "album", "tags", "categories", "location"]
    meta = {k: info[k] for k in keep if info.get(k) not in (None, "", [], {})}
    desc = str(info.get("description") or "")
    hashtags = sorted(set(re.findall(r"#(\w+)", desc)))
    if hashtags:
        meta["hashtags"] = hashtags
    return meta


# ----------------------------------------------------------------------------
# 2. extract frames + audio
# ----------------------------------------------------------------------------

def probe_duration(video: Path) -> float:
    out = run([need("ffprobe"), "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(video)]).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def has_audio(video: Path) -> bool:
    out = run([need("ffprobe"), "-v", "error", "-select_streams", "a", "-show_entries",
               "stream=codec_type", "-of", "csv=p=0", str(video)]).stdout
    return "audio" in out


def extract_frames(video: Path, outdir: Path, max_frames: int) -> list[tuple[float, Path]]:
    ffmpeg = need("ffmpeg")
    outdir.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(video)
    if duration <= 0:
        duration = 30.0
    # one frame per ~2.5 s, between 4 and max_frames, never the very first/last frame
    n = max(4, min(max_frames, math.ceil(duration / 2.5)))
    frames: list[tuple[float, Path]] = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        out = outdir / f"frame_{i:02d}.jpg"
        run([ffmpeg, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", f"scale='min({MAX_IMAGE_SIDE},iw)':-2", "-q:v", "4", str(out)])
        if out.exists():
            frames.append((t, out))
    return frames


def normalise_images(images: list[Path], outdir: Path) -> list[tuple[float, Path]]:
    """Re-encode any image (webp, heic, huge png ...) to a bounded jpeg."""
    ffmpeg = need("ffmpeg")
    outdir.mkdir(parents=True, exist_ok=True)
    out: list[tuple[float, Path]] = []
    for i, img in enumerate(images[:MAX_FRAMES * 2]):
        dst = outdir / f"image_{i:02d}.jpg"
        try:
            run([ffmpeg, "-v", "error", "-y", "-i", str(img),
                 "-vf", f"scale='min({MAX_IMAGE_SIDE},iw)':-2", "-q:v", "3", str(dst)])
            out.append((float(i), dst))
        except subprocess.CalledProcessError:
            log(f"could not read {img.name}, skipping")
    return out


def extract_audio(src: Path, outdir: Path) -> Path | None:
    ffmpeg = need("ffmpeg")
    outdir.mkdir(parents=True, exist_ok=True)
    wav = outdir / "audio.wav"
    try:
        run([ffmpeg, "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    except subprocess.CalledProcessError:
        return None
    return wav if wav.exists() and wav.stat().st_size > 1000 else None


# ----------------------------------------------------------------------------
# 3. transcribe
# ----------------------------------------------------------------------------

def transcribe(wav: Path, whisper_model: str) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        log("faster-whisper not installed, skipping transcript (pip install faster-whisper)")
        return {"available": False, "text": "", "segments": [], "language": None}
    log(f"transcribing with faster-whisper '{whisper_model}' ...")
    try:
        model = WhisperModel(whisper_model, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(wav), vad_filter=True, beam_size=5)
        segs = [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segments]
    except Exception as e:  # model download blocked, corrupt audio ...: analyse without speech
        log(f"whisper failed ({type(e).__name__}: {str(e)[:120]}), continuing without transcript")
        return {"available": False, "text": "", "segments": [], "language": None, "error": str(e)[:200]}
    text = " ".join(s["text"] for s in segs).strip()
    return {"available": True, "text": text, "segments": segs,
            "language": info.language, "language_probability": round(info.language_probability, 2)}


# ----------------------------------------------------------------------------
# 4 + 5. Claude
# ----------------------------------------------------------------------------

def _client():
    import anthropic  # imported late so --help works without the SDK
    return anthropic, anthropic.Anthropic()


def _image_block(path: Path) -> dict[str, Any]:
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}}


def build_analysis_content(frames: list[tuple[float, Path]], kind: str, transcript: dict[str, Any],
                           meta: dict[str, Any], question: str) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for i, (t, path) in enumerate(frames):
        label = f"Image {i + 1} of {len(frames)}" if kind == "images" else f"Frame {i + 1} of {len(frames)} at {fmt_ts(t)}"
        content.append({"type": "text", "text": label})
        content.append(_image_block(path))
    if transcript.get("available"):
        if transcript["text"]:
            lines = [f"[{fmt_ts(s['start'])}] {s['text']}" for s in transcript["segments"]]
            content.append({"type": "text", "text": "TRANSCRIPT (faster-whisper, language "
                            f"{transcript.get('language')}):\n" + "\n".join(lines)})
        else:
            content.append({"type": "text", "text": "TRANSCRIPT: no speech detected (music or silence)."})
    else:
        content.append({"type": "text", "text": "TRANSCRIPT: not available for this post."})
    content.append({"type": "text", "text": "POST METADATA (from the platform):\n" + json.dumps(meta, ensure_ascii=False, indent=1)})
    ask = "Analyse this post and fill the schema."
    if question:
        ask += f"\nThe owner also asks: {question}\nAnswer that inside 'summary' as well."
    content.append({"type": "text", "text": ask})
    return content


def analyse_with_claude(content: list[dict[str, Any]], model: str) -> dict[str, Any]:
    anthropic, client = _client()
    log(f"asking {model} to analyse the post ...")
    try:
        resp = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": ANALYSIS_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.RateLimitError as e:
        raise SystemExit(f"Rate limited by the Claude API; retry in {e.response.headers.get('retry-after', '60')}s")
    except anthropic.APIStatusError as e:
        raise SystemExit(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise SystemExit("Could not reach the Claude API (network).")
    if resp.stop_reason == "refusal":
        why = getattr(resp.stop_details, "explanation", "") if resp.stop_details else ""
        raise SystemExit(f"Claude declined to analyse this post. {why}".strip())
    if resp.stop_reason == "max_tokens":
        raise SystemExit("Claude's answer was cut off (max_tokens); try again with fewer frames.")
    text = next(b.text for b in resp.content if b.type == "text")
    data = json.loads(text)
    data["_model"] = resp.model
    data["_usage"] = {"input": resp.usage.input_tokens, "output": resp.usage.output_tokens}
    return data


def lookup_with_claude(analysis: dict[str, Any], model: str, max_searches: int = 8) -> dict[str, Any]:
    anthropic, client = _client()
    log(f"asking {model} to find it on the web ...")
    brief = {k: analysis.get(k) for k in ("summary", "main_subject", "subjects", "claims", "on_screen_text", "search_queries")}
    messages: list[dict[str, Any]] = [{"role": "user", "content":
        "Analysis of the post:\n" + json.dumps(brief, ensure_ascii=False, indent=1) +
        "\n\nFind the main subject and check the claims."}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches}]
    sources: list[str] = []
    text_parts: list[str] = []
    for _ in range(4):  # pause_turn resumes
        try:
            resp = client.beta.messages.create(
                model=model, max_tokens=16000, system=LOOKUP_SYSTEM,
                messages=messages, tools=tools,
                output_config={"effort": "medium"},
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            )
        except anthropic.APIStatusError as e:
            return {"text": f"_Web lookup failed: API error {e.status_code}: {e.message}_", "sources": []}
        except anthropic.APIConnectionError:
            return {"text": "_Web lookup failed: network error._", "sources": []}
        for block in resp.content:
            if block.type == "web_search_tool_result" and isinstance(block.content, list):
                for r in block.content:
                    url = getattr(r, "url", None)
                    if url and url not in sources:
                        sources.append(url)
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        if resp.stop_reason == "refusal":
            return {"text": "_Claude declined the web lookup._", "sources": sources}
        text_parts = [b.text for b in resp.content if b.type == "text"]
        break
    return {"text": "".join(text_parts).strip(), "sources": sources}


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def render_report(result: dict[str, Any]) -> str:
    a = result["analysis"]
    meta = result["metadata"]
    ms = a["main_subject"]
    lines = [f"# {ms['name']}", ""]
    lines.append(f"**{ms['one_line']}**  ")
    lines.append(f"Type: {ms['type']} · Category: {a['category']} · Confidence: {a['confidence']:.0%}"
                 + (" · looks sponsored" if a.get("looks_sponsored") else ""))
    lines.append("")
    src = meta.get("webpage_url") or result["source"]
    who = meta.get("uploader") or meta.get("channel") or ""
    lines.append(f"Source: {src}" + (f" by {who}" if who else "") +
                 (f" · {meta['duration']:.0f}s" if isinstance(meta.get("duration"), (int, float)) else ""))
    lines.append("")
    lines += ["## What it's about", a["summary"], ""]
    lines += ["## What is shown", a["what_is_shown"], ""]
    lines += ["## What is said", a["what_is_said"], ""]
    if a.get("on_screen_text"):
        lines += ["## On-screen text"] + [f"- {t}" for t in a["on_screen_text"]] + [""]
    if a.get("subjects"):
        lines += ["## Named things", "| Thing | Type | Confidence | Evidence |", "|---|---|---|---|"]
        for s in a["subjects"]:
            lines.append(f"| {s['name']} | {s['type']} | {s['confidence']:.0%} | {s['evidence']} |")
        lines.append("")
    if a.get("claims"):
        lines += ["## Claims made"] + [f"- {c}" for c in a["claims"]] + [""]
    if a.get("call_to_action"):
        lines += ["## Call to action", a["call_to_action"], ""]
    if result.get("lookup"):
        lines += ["## Found on the web", result["lookup"]["text"], ""]
        if result["lookup"].get("sources"):
            lines += ["Sources:"] + [f"- {u}" for u in result["lookup"]["sources"][:10]] + [""]
    tr = result.get("transcript", {})
    if tr.get("text"):
        lines += ["<details><summary>Full transcript</summary>", ""]
        lines += [f"[{fmt_ts(s['start'])}] {s['text']}  " for s in tr["segments"]]
        lines += ["", "</details>", ""]
    lines.append(f"_Language: {a['language']} · Model: {a.get('_model', '')} · Files: {result['out_dir']}_")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# orchestration
# ----------------------------------------------------------------------------

def analyze(source: str, *, out_root: Path | None = None, model: str = DEFAULT_MODEL,
            whisper_model: str = DEFAULT_WHISPER, search: bool = True, question: str = "",
            cookies_from_browser: str | None = None, cookies_file: str | None = None,
            max_frames: int = MAX_FRAMES, keep_download: bool = False) -> dict[str, Any]:
    t0 = time.time()
    out_root = out_root or Path(os.environ.get("REEL_SCOUT_OUT", "~/reel-scout")).expanduser()
    tmp = Path(tempfile.mkdtemp(prefix="reel-scout-"))
    try:
        media = fetch_media(source, tmp, cookies_from_browser, cookies_file)
        meta = post_metadata(media.info)
        post_id = str(media.info.get("id") or slug(Path(source).stem if Path(source).exists() else source))
        out_dir = out_root / f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(post_id, 30)}"
        out_dir.mkdir(parents=True, exist_ok=True)

        frames: list[tuple[float, Path]] = []
        wav: Path | None = None
        if media.kind == "video":
            v = media.videos[0]
            frames = extract_frames(v, out_dir / "frames", max_frames)
            if has_audio(v):
                wav = extract_audio(v, out_dir)
        elif media.kind == "images":
            frames = normalise_images(media.images, out_dir / "frames")
            if media.audio:
                wav = extract_audio(media.audio, out_dir)
        elif media.kind == "audio" and media.audio:
            wav = extract_audio(media.audio, out_dir)
        log(f"{len(frames)} frame(s), audio: {'yes' if wav else 'no'}")

        transcript = transcribe(wav, whisper_model) if wav else {"available": True, "text": "", "segments": [], "language": None}
        if transcript.get("text"):
            log(f"transcript: {len(transcript['text'].split())} words ({transcript.get('language')})")

        content = build_analysis_content(frames, media.kind, transcript, meta, question)
        analysis = analyse_with_claude(content, model)
        result: dict[str, Any] = {
            "source": source, "kind": media.kind, "metadata": meta, "transcript": transcript,
            "analysis": analysis, "lookup": None, "out_dir": str(out_dir),
        }
        if search:
            result["lookup"] = lookup_with_claude(analysis, model)
        result["seconds"] = round(time.time() - t0, 1)
        report = render_report(result)
        result["report_markdown"] = report
        (out_dir / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "report.md").write_text(report, encoding="utf-8")
        if keep_download and (tmp / "dl").exists():
            shutil.copytree(tmp / "dl", out_dir / "download", dirs_exist_ok=True)
        if wav and wav.exists():
            wav.unlink()
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reel-scout", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="post URL (TikTok, Instagram, YouTube, X ...) or a local video/image file")
    ap.add_argument("--no-search", action="store_true", help="skip the web lookup step")
    ap.add_argument("--json", action="store_true", help="print the full JSON instead of the markdown report")
    ap.add_argument("--out", type=Path, help="folder for reports and frames (default ~/reel-scout or $REEL_SCOUT_OUT)")
    ap.add_argument("--question", default="", help="a specific question to answer about the post")
    ap.add_argument("--cookies-from-browser", help="chrome | safari | firefox, for posts that need a login")
    ap.add_argument("--cookies", help="path to a Netscape cookies.txt")
    ap.add_argument("--whisper", default=os.environ.get("REEL_SCOUT_WHISPER", DEFAULT_WHISPER), help="faster-whisper model: tiny, base, small, medium, large-v3")
    ap.add_argument("--model", default=os.environ.get("REEL_SCOUT_MODEL", DEFAULT_MODEL), help="Claude model id")
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES)
    ap.add_argument("--keep-download", action="store_true", help="keep the downloaded media next to the report")
    args = ap.parse_args(argv)

    result = analyze(args.source, out_root=args.out, model=args.model, whisper_model=args.whisper,
                     search=not args.no_search, question=args.question,
                     cookies_from_browser=args.cookies_from_browser, cookies_file=args.cookies,
                     max_frames=args.max_frames, keep_download=args.keep_download)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(result["report_markdown"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
