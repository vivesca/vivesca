#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml", "httpx", "openai", "yt-dlp", "youtube-transcript-api", "feedparser", "mlx-whisper", "trafilatura"]
# ///
"""
Content Digest — Monthly insight extraction from YouTube channels and podcasts.

Fetches recent episodes via yt-dlp or podcast RSS, extracts transcripts
(YouTube API → yt-dlp subs → podcast audio + Whisper), runs LLM insight
extraction via OpenRouter, and writes digest notes to the Obsidian vault.

Usage:
    digest [source_name] [--days N] [--dry-run]

Examples:
    digest                     # All sources, last 30 days
    digest huberman            # Just Huberman
    digest "lex" --days 60     # Lex Fridman, last 60 days
    digest --dry-run           # List episodes only
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from openai import OpenAI

SKILL_DIR = Path(__file__).resolve().parent
SOURCES_FILE = SKILL_DIR / "sources.yaml"
VAULT_DIR = Path.home() / "notes"

INSIGHT_PROMPT = """\
You are an expert at extracting actionable insights from podcast and video transcripts.
Analyze this transcript and extract ALL insightful, non-trivial points. Be comprehensive.

Structure your output as:

## Key Insights

For each insight:
- **Claim:** What is being asserted
- **Evidence:** [RCT | Meta-analysis | Observational | Animal | Mechanistic | Expert opinion | Anecdotal]
- **Mechanism:** Brief explanation of why/how (if discussed)
- **Actionable takeaway:** What to do with this (if applicable)

## Protocols & Recommendations

Specific actionable protocols mentioned. Include full specifics:
- Substance/practice name
- Dose / intensity / duration
- Timing (time of day, relative to meals, etc.)
- Frequency
- Caveats or contraindications mentioned

## Contrarian or Surprising Points

Anything that contradicts common belief, popular health advice, or might surprise a well-read audience.

## Notable Quotes

2-3 most impactful direct quotes (verbatim from transcript).

## Episode Summary

3-5 sentence overview for quick scanning.

Be thorough. Extract every non-trivial insight. Better to include too much than too little.\
"""


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------

def load_sources(filter_name: str | None = None) -> list[dict]:
    with open(SOURCES_FILE) as f:
        sources = yaml.safe_load(f)
    if filter_name:
        q = filter_name.lower()
        sources = [
            s for s in sources
            if q in s["name"].lower() or q in s.get("vault_path", "").lower()
        ]
    return sources


# ---------------------------------------------------------------------------
# YouTube video listing (yt-dlp)
# ---------------------------------------------------------------------------

def list_youtube_videos(handle: str, max_items: int = 15) -> list[dict]:
    """List recent videos from a YouTube channel using yt-dlp."""
    url = f"https://www.youtube.com/{handle}/videos"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-download",
        "--playlist-items", f"1-{max_items}",
        "--print", '{"id":"%(id)s","title":"%(title)s","upload_date":"%(upload_date)s","duration":"%(duration)s"}',
        "--no-warnings",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp listing failed: {result.stderr}")

    videos = []
    for line in result.stdout.strip().splitlines():
        try:
            data = json.loads(line)
            upload_date = data.get("upload_date")
            if upload_date and upload_date != "NA":
                data["date"] = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
            else:
                data["date"] = None
            videos.append(data)
        except (json.JSONDecodeError, ValueError):
            continue
    return videos


# ---------------------------------------------------------------------------
# Podcast RSS listing
# ---------------------------------------------------------------------------

def list_podcast_episodes(rss_url: str, max_items: int = 15) -> list[dict]:
    """List recent episodes from a podcast RSS feed."""
    import feedparser

    feed = feedparser.parse(rss_url)
    episodes = []
    for entry in feed.entries[:max_items]:
        # Find audio enclosure
        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio/"):
                audio_url = link["href"]
                break
        if not audio_url:
            for enc in entry.get("enclosures", []):
                if enc.get("type", "").startswith("audio/"):
                    audio_url = enc["href"]
                    break
        if not audio_url:
            continue

        # Parse date
        date = None
        for date_field in ("published_parsed", "updated_parsed"):
            parsed = entry.get(date_field)
            if parsed:
                from time import mktime
                date = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                break

        # Parse duration
        duration_s = "0"
        itunes_dur = entry.get("itunes_duration", "")
        if itunes_dur:
            parts = str(itunes_dur).split(":")
            try:
                if len(parts) == 3:
                    duration_s = str(int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]))
                elif len(parts) == 2:
                    duration_s = str(int(parts[0]) * 60 + int(parts[1]))
                else:
                    duration_s = parts[0]
            except ValueError:
                pass

        episodes.append({
            "id": entry.get("id", audio_url),
            "title": entry.get("title", "Unknown"),
            "date": date,
            "duration": duration_s,
            "audio_url": audio_url,
            "episode_url": entry.get("link"),
        })

    return episodes


def _match_podcast_episode(yt_ep: dict, podcast_eps: list[dict]) -> dict | None:
    """Find matching podcast episode for a YouTube video by title similarity + date + duration.
    Returns dict with audio_url and episode_url, or None."""
    yt_title = re.sub(r"[^a-z0-9 ]", "", yt_ep["title"].lower())
    yt_words = set(yt_title.split())
    yt_date = yt_ep.get("date")

    # Parse YouTube duration
    yt_dur = 0
    try:
        yt_dur = int(float(yt_ep.get("duration", 0)))
    except (ValueError, TypeError):
        pass

    best_match = None
    best_score = 0

    for pep in podcast_eps:
        pod_title = re.sub(r"[^a-z0-9 ]", "", pep["title"].lower())
        pod_words = set(pod_title.split())

        # Jaccard similarity on title words
        if yt_words and pod_words:
            overlap = len(yt_words & pod_words)
            union = len(yt_words | pod_words)
            title_score = overlap / union if union else 0
        else:
            title_score = 0

        # Date proximity bonus (within 3 days = 0.3 bonus)
        date_score = 0
        if yt_date and pep.get("date"):
            day_diff = abs((yt_date - pep["date"]).days)
            if day_diff <= 3:
                date_score = 0.3

        # Duration penalty — reject when duration ratio > 3x
        pod_dur = 0
        try:
            pod_dur = int(float(pep.get("duration", 0)))
        except (ValueError, TypeError):
            pass

        if yt_dur > 0 and pod_dur > 0:
            ratio = max(yt_dur, pod_dur) / min(yt_dur, pod_dur)
            if ratio > 3:
                continue  # Skip — clearly a clip vs full episode mismatch

        score = title_score + date_score
        if score > best_score:
            best_score = score
            best_match = pep

    # Require minimum similarity (at least some title overlap or date match)
    if best_score >= 0.3 and best_match:
        return {"audio_url": best_match["audio_url"], "episode_url": best_match.get("episode_url")}
    return None


def _deduplicate_audio_matches(episodes: list[dict], podcast_eps: list[dict]) -> None:
    """If multiple YouTube videos matched the same podcast audio URL, keep only the best."""
    # Build lookup: audio_url → podcast duration
    pod_dur_by_url = {}
    for pep in podcast_eps:
        try:
            pod_dur_by_url[pep["audio_url"]] = int(float(pep.get("duration", 0)))
        except (ValueError, TypeError):
            pod_dur_by_url[pep["audio_url"]] = 0

    # Group episodes by audio_url
    by_url: dict[str, list[int]] = {}
    for i, ep in enumerate(episodes):
        url = ep.get("audio_url")
        if url:
            by_url.setdefault(url, []).append(i)

    # For each duplicate group, keep only the closest duration match
    for url, indices in by_url.items():
        if len(indices) <= 1:
            continue
        pod_dur = pod_dur_by_url.get(url, 0)
        best_idx = indices[0]
        best_diff = float("inf")
        for idx in indices:
            try:
                yt_dur = int(float(episodes[idx].get("duration", 0)))
            except (ValueError, TypeError):
                yt_dur = 0
            diff = abs(yt_dur - pod_dur) if yt_dur and pod_dur else float("inf")
            if diff < best_diff:
                best_diff = diff
                best_idx = idx
        # Clear audio_url from losers
        for idx in indices:
            if idx != best_idx:
                print(f"  Dedup: skipping RSS fallback for '{episodes[idx]['title'][:50]}' (duplicate audio)", file=sys.stderr)
                episodes[idx]["audio_url"] = None


# ---------------------------------------------------------------------------
# Audio transcription via mlx-whisper (Apple Silicon local)
# ---------------------------------------------------------------------------

def transcribe_audio(audio_url: str) -> str:
    """Download podcast audio and transcribe with mlx-whisper."""
    import httpx

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "episode.mp3")

        # Download audio
        print("  Downloading audio...", file=sys.stderr)
        with httpx.stream("GET", audio_url, follow_redirects=True, timeout=300) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(audio_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r  Downloaded: {downloaded // (1024*1024)}MB / {total // (1024*1024)}MB ({pct}%)", end="", file=sys.stderr)
            print(file=sys.stderr)

        # Transcribe with mlx-whisper
        print("  Transcribing with mlx-whisper (this may take a few minutes)...", file=sys.stderr)
        import mlx_whisper

        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        )
        text = result.get("text", "")
        return _clean_transcript(text) if text.strip() else ""


# ---------------------------------------------------------------------------
# Web transcript extraction (scrape from episode pages)
# ---------------------------------------------------------------------------

def _transcript_from_web(episode_url: str, transcript_url_suffix: str | None = None) -> str | None:
    """Fetch transcript from episode webpage using trafilatura for content extraction."""
    import httpx
    import trafilatura

    url = episode_url
    if transcript_url_suffix:
        # e.g. Lex Fridman: episode_url + "-transcript"
        url = episode_url.rstrip("/") + transcript_url_suffix

    print(f"  Fetching web transcript from {url}...", file=sys.stderr)
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        resp.raise_for_status()
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        if text and len(text) > 500:  # minimum viable transcript length
            return _clean_transcript(text)
        return None
    except Exception as e:
        print(f"  Web transcript failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Whisper API transcription (OpenAI, ~$0.006/min)
# ---------------------------------------------------------------------------

def _transcribe_whisper_api(audio_url: str) -> str:
    """Download audio and transcribe via OpenAI Whisper API."""
    import httpx

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "episode.mp3")

        # Download audio
        print("  Downloading audio for Whisper API...", file=sys.stderr)
        with httpx.stream("GET", audio_url, follow_redirects=True, timeout=300) as resp:
            resp.raise_for_status()
            with open(audio_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)

        # Transcribe via OpenAI Whisper API
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"  Transcribing via Whisper API ({file_size_mb:.0f}MB)...", file=sys.stderr)

        # Whisper API has 25MB limit — split if larger
        if file_size_mb > 25:
            print("  File >25MB, falling back to local Whisper", file=sys.stderr)
            raise RuntimeError("Audio file exceeds Whisper API 25MB limit")

        client = OpenAI(api_key=api_key)
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(model="whisper-1", file=f)
        text = result.text
        return _clean_transcript(text) if text.strip() else ""


# ---------------------------------------------------------------------------
# Transcript extraction (inlined — no external script dependency)
# ---------------------------------------------------------------------------

def extract_transcript(video_id: str, audio_url: str | None = None,
                       episode_url: str | None = None,
                       transcript_url_suffix: str | None = None) -> str:
    """Extract transcript. Fallback chain:
    1. youtube-transcript-api (free, instant)
    2. yt-dlp subtitles (free, instant)
    3. Web transcript scrape (free, fast)
    4. Whisper API (cheap, fast, <25MB files)
    5. Local mlx-whisper (free, slow)
    """
    # Method 1: youtube-transcript-api (clean, no duplication)
    try:
        text = _transcript_via_api(video_id)
        if text:
            return text
    except Exception as e:
        print(f"  youtube-transcript-api failed: {e}", file=sys.stderr)

    # Method 2: yt-dlp subtitle download (may have duplication)
    print("  Falling back to yt-dlp subtitles...", file=sys.stderr)
    try:
        text = _transcript_via_ytdlp(video_id)
        if text:
            return _deduplicate_transcript(text)
    except Exception as e:
        print(f"  yt-dlp subtitles failed: {e}", file=sys.stderr)

    # Method 3: web transcript scrape
    if episode_url:
        print("  Falling back to web transcript...", file=sys.stderr)
        try:
            text = _transcript_from_web(episode_url, transcript_url_suffix)
            if text:
                return text
        except Exception as e:
            print(f"  Web transcript failed: {e}", file=sys.stderr)

    # Method 4: Whisper API (fast, cheap, <25MB files only)
    if audio_url and os.environ.get("OPENAI_API_KEY"):
        print("  Falling back to Whisper API...", file=sys.stderr)
        try:
            text = _transcribe_whisper_api(audio_url)
            if text:
                return text
        except Exception as e:
            print(f"  Whisper API failed: {e}", file=sys.stderr)

    # Method 5: local mlx-whisper (slow but always works)
    if audio_url:
        print("  Falling back to local Whisper...", file=sys.stderr)
        text = transcribe_audio(audio_url)
        if text:
            return text
        raise RuntimeError("Local Whisper transcription returned empty")

    raise RuntimeError("All transcript methods failed")


def _transcript_via_api(video_id: str) -> str | None:
    """Fetch transcript using youtube-transcript-api."""
    from youtube_transcript_api import YouTubeTranscriptApi

    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id, languages=["en"])
    text = " ".join(snippet.text for snippet in transcript)
    return _clean_transcript(text) if text.strip() else None


def _transcript_via_ytdlp(video_id: str) -> str | None:
    """Fetch transcript by downloading VTT subtitles via yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "transcript")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--skip-download",
            "--write-subs", "--write-auto-subs",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "-o", output_template,
            "--no-warnings",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Find VTT file
        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            return None

        vtt_content = vtt_files[0].read_text(encoding="utf-8")
        return _clean_transcript(_parse_vtt(vtt_content))


def _parse_vtt(vtt_content: str) -> str:
    """Parse VTT subtitle file to plain text."""
    lines = vtt_content.split("\n")
    text_parts = []
    for line in lines:
        line = line.strip()
        # Skip headers, timestamps, and cue numbers
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or "-->" in line
            or line.isdigit()
        ):
            continue
        # Strip HTML tags
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_parts.append(line)
    return " ".join(text_parts)


def _clean_transcript(text: str) -> str:
    """Remove annotations and speaker labels."""
    text = html.unescape(text)
    text = re.sub(r"\[[^\]]*\]", "", text)  # [Music], [Applause], etc.
    text = re.sub(r"(?:^|\s)>>?\s*[A-Z][A-Z\s]*:", "", text)  # >> SPEAKER:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _deduplicate_transcript(text: str) -> str:
    """Remove consecutive duplicate phrases from yt-dlp auto-caption output."""
    words = text.split()
    if len(words) < 6:
        return text

    result = []
    i = 0
    while i < len(words):
        found_dup = False
        for chunk_size in range(min(20, (len(words) - i) // 2), 2, -1):
            chunk = words[i : i + chunk_size]
            next_chunk = words[i + chunk_size : i + 2 * chunk_size]
            if chunk == next_chunk:
                result.extend(chunk)
                j = i + chunk_size
                while words[j : j + chunk_size] == chunk:
                    j += chunk_size
                i = j
                found_dup = True
                break
        if not found_dup:
            result.append(words[i])
            i += 1

    return " ".join(result)


# ---------------------------------------------------------------------------
# LLM insight extraction
# ---------------------------------------------------------------------------

def extract_insights(transcript: str, title: str, model: str) -> str:
    """Run LLM insight extraction on a transcript via OpenRouter."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": INSIGHT_PROMPT},
            {"role": "user", "content": f"Episode: {title}\n\nTranscript:\n{transcript}"},
        ],
        max_tokens=8000,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Vault output
# ---------------------------------------------------------------------------

def write_digest(source: dict, episodes_insights: list[dict], month_str: str) -> Path:
    """Write digest note to vault."""
    vault_path = VAULT_DIR / source["vault_path"]
    vault_path.mkdir(parents=True, exist_ok=True)

    digest_file = vault_path / f"{month_str} Digest.md"

    lines = [
        f"# {source['name']} — {month_str} Digest",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Episodes: {len(episodes_insights)}",
        "",
    ]

    for ep in episodes_insights:
        duration_s = ep.get("duration")
        if duration_s and duration_s != "NA":
            try:
                mins = int(float(duration_s)) // 60
                duration_str = f" ({mins} min)"
            except (ValueError, TypeError):
                duration_str = ""
        else:
            duration_str = ""

        date_str = ep["date"].strftime("%Y-%m-%d") if ep.get("date") else "unknown"

        # Link to video or podcast
        ep_id = ep.get("id", "")
        if ep_id.startswith("http"):
            link_line = f"**Link:** {ep_id}"
        else:
            link_line = f"**Video:** https://youtube.com/watch?v={ep_id}"

        lines.extend([
            "---",
            "",
            f"## {ep['title']}",
            "",
            f"**Published:** {date_str}{duration_str}",
            link_line,
            "",
            ep["insights"],
            "",
        ])

    digest_file.write_text("\n".join(lines), encoding="utf-8")
    return digest_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Monthly content digest — extract insights from YouTube channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sources configured in ~/skills/digest/sources.yaml",
    )
    parser.add_argument("source", nargs="?", help="Source name filter (partial match)")
    parser.add_argument("--days", type=int, default=30, help="Look back N days (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="List episodes without processing")
    parser.add_argument("--model", default="google/gemini-3-flash-preview", help="OpenRouter model ID")
    parser.add_argument("--max-videos", type=int, default=15, help="Max videos to fetch per channel")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between episodes to avoid YouTube rate limits (default: 5)")
    args = parser.parse_args()

    if not args.dry_run and not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    sources = load_sources(args.source)
    if not sources:
        print(f"No sources found matching '{args.source}'", file=sys.stderr)
        sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    month_str = datetime.now().strftime("%Y-%m")

    for source_idx, source in enumerate(sources):
        # Rate limit: pause between sources to avoid YouTube IP bans
        if source_idx > 0 and args.delay > 0:
            pause = args.delay * 2
            print(f"\nWaiting {pause}s between sources (rate limit)...", file=sys.stderr)
            time.sleep(pause)

        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"Source: {source['name']}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)

        if source["type"] == "youtube":
            try:
                videos = list_youtube_videos(source["handle"], max_items=args.max_videos)
            except Exception as e:
                print(f"Error listing videos: {e}", file=sys.stderr)
                continue

            episodes = [v for v in videos if v.get("date") and v["date"] >= since]

            # Attach podcast audio URLs for fallback if rss_url configured
            if source.get("rss_url"):
                try:
                    podcast_eps = list_podcast_episodes(source["rss_url"], max_items=args.max_videos * 2)
                    for ep in episodes:
                        match = _match_podcast_episode(ep, podcast_eps)
                        if match:
                            ep["audio_url"] = match["audio_url"]
                            ep["episode_url"] = match.get("episode_url")
                            print(f"  RSS fallback ready: {ep['title'][:50]}", file=sys.stderr)
                    # Deduplicate: if multiple YT videos matched the same audio URL,
                    # keep only the one with closest duration and clear the rest
                    _deduplicate_audio_matches(episodes, podcast_eps)
                except Exception as e:
                    print(f"  RSS fallback lookup failed: {e}", file=sys.stderr)

        elif source["type"] == "podcast":
            rss_url = source.get("rss_url")
            if not rss_url:
                print(f"Podcast source '{source['name']}' missing rss_url", file=sys.stderr)
                continue
            try:
                episodes = list_podcast_episodes(rss_url, max_items=args.max_videos)
                episodes = [ep for ep in episodes if ep.get("date") and ep["date"] >= since]
            except Exception as e:
                print(f"Error listing podcast episodes: {e}", file=sys.stderr)
                continue
        else:
            print(f"Unsupported source type: {source['type']}", file=sys.stderr)
            continue

        if not episodes:
            print(f"No episodes in last {args.days} days", file=sys.stderr)
            continue

        print(f"Found {len(episodes)} episodes:", file=sys.stderr)
        for ep in episodes:
            duration_s = ep.get("duration", "0")
            try:
                mins = int(float(duration_s)) // 60
            except (ValueError, TypeError):
                mins = 0
            date_str = ep["date"].strftime("%Y-%m-%d") if ep.get("date") else "?"
            print(f"  [{date_str}] {ep['title']} ({mins}m)", file=sys.stderr)

        if args.dry_run:
            continue

        episodes_insights = []
        for i, ep in enumerate(episodes, 1):
            print(f"\n[{i}/{len(episodes)}] Processing: {ep['title']}", file=sys.stderr)

            try:
                # Rate limit: pause between episodes to avoid YouTube IP bans
                if i > 1 and args.delay > 0:
                    print(f"  Waiting {args.delay}s (rate limit)...", file=sys.stderr)
                    time.sleep(args.delay)

                print("  Extracting transcript...", file=sys.stderr)
                audio_url = ep.get("audio_url")
                episode_url = ep.get("episode_url")
                transcript_url_suffix = source.get("transcript_url_suffix")
                if source["type"] == "podcast":
                    # Pure podcast — try web transcript first, then audio
                    transcript = None
                    if episode_url:
                        transcript = _transcript_from_web(episode_url, transcript_url_suffix)
                    if not transcript:
                        transcript = transcribe_audio(audio_url)
                else:
                    transcript = extract_transcript(
                        ep["id"], audio_url=audio_url,
                        episode_url=episode_url,
                        transcript_url_suffix=transcript_url_suffix,
                    )
                word_count = len(transcript.split())
                print(f"  Transcript: {word_count:,} words", file=sys.stderr)

                print(f"  Extracting insights ({args.model})...", file=sys.stderr)
                insights = extract_insights(transcript, ep["title"], model=args.model)

                episodes_insights.append({
                    **ep,
                    "insights": insights,
                })
                print("  Done.", file=sys.stderr)
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
                continue

        if episodes_insights:
            digest_file = write_digest(source, episodes_insights, month_str)
            print(f"\nDigest written: {digest_file}", file=sys.stderr)
        else:
            print("\nNo episodes processed successfully.", file=sys.stderr)


if __name__ == "__main__":
    main()
