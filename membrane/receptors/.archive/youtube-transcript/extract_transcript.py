#!/usr/bin/env python3
# /// script
# dependencies = ["yt-dlp", "youtube-transcript-api"]
# ///
"""
YouTube Transcript Extractor

Extract transcripts from YouTube videos using yt-dlp (primary) with youtube-transcript-api as fallback.

Usage:
    uv run extract_transcript.py <video_id_or_url> [options]

Examples:
    uv run extract_transcript.py dQw4w9WgXcQ
    uv run extract_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
    uv run extract_transcript.py VIDEO_ID --browser chrome  # Use Chrome cookies
    uv run extract_transcript.py VIDEO_ID --cookies /path/to/cookies.txt  # Use exported cookies
"""

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from URL or return as-is if already an ID."""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id.strip()


def clean_transcript_text(text: str, remove_annotations: bool = True) -> str:
    """Clean transcript text by removing artifacts."""
    text = html.unescape(text)
    if remove_annotations:
        text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"(?:^|\s)>>?\s*[A-Z][A-Z\s]*:", "", text)
    text = re.sub(r"(?:^|\s)SPEAKER\s*\d*:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:^|\s)-\s*[A-Za-z]+:", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_vtt_to_text(vtt_content: str, include_timestamps: bool = False) -> str:
    """Parse VTT subtitle content to plain text."""
    lines = vtt_content.split("\n")
    result = []
    current_text = []
    current_timestamp = None

    for line in lines:
        line = line.strip()
        if (
            line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or not line
        ):
            if current_text:
                if include_timestamps and current_timestamp:
                    result.append(f"[{current_timestamp}] {' '.join(current_text)}")
                else:
                    result.append(" ".join(current_text))
                current_text = []
            continue
        if "-->" in line:
            if current_text:
                if include_timestamps and current_timestamp:
                    result.append(f"[{current_timestamp}] {' '.join(current_text)}")
                else:
                    result.append(" ".join(current_text))
                current_text = []
            start_time = line.split("-->")[0].strip()
            parts = start_time.split(":")
            if len(parts) == 3:
                mins = int(parts[0]) * 60 + int(parts[1])
                secs = parts[2].split(".")[0]
                current_timestamp = f"{mins:02d}:{secs}"
            else:
                mins = parts[0]
                secs = parts[1].split(".")[0]
                current_timestamp = f"{mins}:{secs}"
            continue
        if line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            current_text.append(line)

    if current_text:
        if include_timestamps and current_timestamp:
            result.append(f"[{current_timestamp}] {' '.join(current_text)}")
        else:
            result.append(" ".join(current_text))

    return "\n".join(result) if include_timestamps else " ".join(result)


def get_transcript_ytdlp(
    video_id: str,
    languages: list[str] = None,
    include_timestamps: bool = False,
    browser: str = None,
    cookies_file: str = None,
) -> tuple[str, dict]:
    """Fetch transcript using yt-dlp."""
    if languages is None:
        languages = ["en"]

    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "transcript")

        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang",
            ",".join(languages),
            "--sub-format",
            "vtt",
            "-o",
            output_template,
        ]

        # Add authentication if specified
        if cookies_file:
            cmd.extend(["--cookies", cookies_file])
        elif browser:
            cmd.extend(["--cookies-from-browser", browser])

        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            raise RuntimeError("yt-dlp not found. Install with: pip install yt-dlp")
        except subprocess.TimeoutExpired:
            raise RuntimeError("yt-dlp timed out")

        # Find subtitle file
        subtitle_file = None
        for lang in languages:
            for pattern in [f"transcript.{lang}.vtt", f"transcript.{lang}.*.vtt"]:
                matches = list(Path(tmpdir).glob(pattern))
                if matches:
                    subtitle_file = matches[0]
                    break
            if subtitle_file:
                break

        if not subtitle_file:
            files = list(Path(tmpdir).glob("*.vtt"))
            if files:
                subtitle_file = files[0]
            else:
                raise RuntimeError(f"No subtitles found. yt-dlp stderr: {result.stderr}")

        vtt_content = subtitle_file.read_text(encoding="utf-8")
        transcript_text = parse_vtt_to_text(vtt_content, include_timestamps)

        lang_match = re.search(r"\.([a-z]{2})\.", subtitle_file.name)
        detected_lang = lang_match.group(1) if lang_match else languages[0]
        is_auto = ".auto." in subtitle_file.name

        return transcript_text, {
            "video_id": video_id,
            "language": detected_lang,
            "language_code": detected_lang,
            "is_generated": is_auto,
            "method": "yt-dlp",
        }


def get_transcript_api(
    video_id: str, languages: list[str] = None, include_timestamps: bool = False
) -> tuple[str, dict]:
    """Fetch transcript using youtube-transcript-api (fallback)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("youtube-transcript-api not installed")

    if languages is None:
        languages = ["en"]

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=languages)

    if include_timestamps:
        lines = []
        for snippet in transcript:
            minutes = int(snippet.start // 60)
            seconds = int(snippet.start % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {snippet.text}")
        text = "\n".join(lines)
    else:
        text = " ".join([snippet.text for snippet in transcript])

    return text, {
        "video_id": transcript.video_id,
        "language": transcript.language,
        "language_code": transcript.language_code,
        "is_generated": transcript.is_generated,
        "method": "youtube-transcript-api",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract transcripts from YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("video", help="YouTube video ID or URL")
    parser.add_argument(
        "-l",
        "--language",
        nargs="+",
        default=["en"],
        help="Language code(s) in priority order (default: en)",
    )
    parser.add_argument(
        "-t", "--timestamps", action="store_true", help="Include timestamps in output"
    )
    parser.add_argument(
        "-c", "--clean", action="store_true", help="Clean transcript text (remove [Music], etc.)"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--method",
        choices=["auto", "ytdlp", "api"],
        default="auto",
        help="Method: auto, ytdlp, or api",
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox", "safari", "edge", "brave"],
        help="Browser to extract cookies from (for yt-dlp auth)",
    )
    parser.add_argument("--cookies", help="Path to Netscape-format cookies.txt file")

    args = parser.parse_args()
    video_id = extract_video_id(args.video)

    try:
        text = None
        metadata = None

        # Try yt-dlp first
        if args.method in ["auto", "ytdlp"]:
            try:
                text, metadata = get_transcript_ytdlp(
                    video_id,
                    args.language,
                    args.timestamps,
                    browser=args.browser,
                    cookies_file=args.cookies,
                )
                print("[Using yt-dlp]", file=sys.stderr)
            except Exception as e:
                if args.method == "ytdlp":
                    raise
                print(f"[yt-dlp failed: {e}]", file=sys.stderr)
                print("[Trying youtube-transcript-api...]", file=sys.stderr)

        # Fallback to API
        if text is None and args.method in ["auto", "api"]:
            text, metadata = get_transcript_api(video_id, args.language, args.timestamps)
            print("[Using youtube-transcript-api]", file=sys.stderr)

        if text is None:
            print("Error: Could not fetch transcript", file=sys.stderr)
            sys.exit(1)

        if args.clean:
            text = clean_transcript_text(text)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved to {args.output}", file=sys.stderr)
        else:
            print(text)

        print("\n--- Metadata ---", file=sys.stderr)
        print(f"Video ID: {metadata['video_id']}", file=sys.stderr)
        print(f"Language: {metadata.get('language', 'unknown')}", file=sys.stderr)
        print(f"Auto-generated: {metadata.get('is_generated', 'unknown')}", file=sys.stderr)
        print(f"Method: {metadata.get('method', 'unknown')}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
