#!/usr/bin/env python3
"""imprimatur — produce a corporate paper banner with brand-overlay over MJ atmospheric background.

Usage:
    imprimatur.py "<MJ prompt>" [--moodboard m...] [--variant open|iconic] [--name banner-x] [--output-dir ./]

Pipeline:
    1. Refresh JWT (osascript Chrome → MJ → cookie bridge)
    2. Generate background via limen (no logo prompt — pure atmospheric)
    3. Auto-pick best-of-4 (or expose for user choice)
    4. Composite official HSBC hexagon overlay (open or iconic variant)
    5. Write source + 16:5 retina + 16:5 1x sized variants

Run on soma. Requires:
    - Mac with Chrome logged in to midjourney.com
    - Mac cookie bridge service on port 7743 (porta)
    - limen installed on Mac (~/code/limen)
    - cairosvg + pillow on soma
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cairosvg
from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
SCRIPTS_DIR = SKILL_DIR / "scripts"

OPEN_HEX_SVG = ASSETS_DIR / "hsbc_open_hex_dark.svg"
ICONIC_HEX_SVG = ASSETS_DIR / "hsbc_iconic_hex.svg"
COOKIE_CACHE_PATH = "/Users/terry/.limen/cookies.json"
JWT_NAME = "__Host-Midjourney.AuthUserTokenV3_i"


def ssh(cmd: str, timeout: int = 60) -> str:
    """Run a command on Mac via ssh and return stdout."""
    result = subprocess.run(["ssh", "mac", cmd], capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"ssh stderr: {result.stderr[:500]}", file=sys.stderr)
    return result.stdout


def refresh_jwt_via_chrome():
    """Drive Chrome to MJ to refresh JWT, then bridge cookies."""
    print("[jwt] Driving Chrome to midjourney.com to refresh JWT...")
    ssh(
        'osascript -e "tell application \\"Google Chrome\\" to make new tab at end of tabs of window 1 with properties {URL:\\"https://www.midjourney.com/explore\\"}"'
    )
    time.sleep(8)
    print("[jwt] Bridging cookies via porta cookie bridge (:7743)...")
    bridge_cookies()


def bridge_cookies():
    """Fetch cookies from Mac cookie bridge and write to limen cache."""
    bridge_script = """
import json, urllib.request, time
root = json.loads(urllib.request.urlopen("http://127.0.0.1:7743/cookies?domain=midjourney.com").read())
www = json.loads(urllib.request.urlopen("http://127.0.0.1:7743/cookies?domain=www.midjourney.com").read())
merged = {**root, **www}
cookies = []
for name, value in merged.items():
    is_host = name.startswith("__Host-")
    is_secure_prefix = name.startswith("__Secure-") or is_host
    cookies.append({
        "name": name, "value": value,
        "domain": ".midjourney.com" if not is_host else "www.midjourney.com",
        "path": "/",
        "secure": True if is_secure_prefix else (name.startswith("cf_") or name in ("__cf_bm", "_cfuvid")),
        "httpOnly": is_host or name.startswith("__cf"),
        "sameSite": "Lax",
    })
cache = {"cookies": cookies, "extractedAt": int(time.time() * 1000)}
with open("/Users/terry/.limen/cookies.json", "w") as f:
    json.dump(cache, f, indent=2)
import sys
has_jwt = any(c["name"] == "__Host-Midjourney.AuthUserTokenV3_i" for c in cookies)
print(f"Wrote {len(cookies)} cookies; JWT present: {has_jwt}")
sys.exit(0 if has_jwt else 1)
"""
    # Write script to mac /tmp and run
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(bridge_script)
        local_path = f.name
    subprocess.run(["scp", local_path, "mac:/tmp/imprimatur_bridge.py"], check=True)
    out = ssh("python3 /tmp/imprimatur_bridge.py")
    print(f"[jwt] {out.strip()}")


def jwt_minutes_remaining() -> float:
    """Check how many minutes remain on the cached JWT (negative = expired)."""
    out = ssh(f"""python3 -c '
import json, base64, time
data = json.load(open("{COOKIE_CACHE_PATH}"))
jwt = next((c for c in data["cookies"] if c["name"] == "{JWT_NAME}"), None)
if jwt:
    payload = json.loads(base64.urlsafe_b64decode(jwt["value"].split(".")[1] + "==").decode())
    print((payload["exp"] - time.time()) / 60)
else:
    print(-9999)
'""")
    try:
        return float(out.strip())
    except ValueError:
        return -9999.0


def ensure_fresh_jwt():
    """Ensure JWT is fresh (>5 min remaining); refresh if not."""
    mins = jwt_minutes_remaining()
    print(f"[jwt] Remaining: {mins:.1f} min")
    if mins < 5:
        refresh_jwt_via_chrome()
        mins = jwt_minutes_remaining()
        print(f"[jwt] After refresh: {mins:.1f} min")
        if mins < 5:
            raise RuntimeError("JWT refresh failed — Chrome may not have a logged-in MJ session.")


def generate_via_limen(prompt: str, moodboard: str | None = None) -> list[str]:
    """Call limen on Mac to generate 4 images. Returns list of remote paths."""
    ensure_fresh_jwt()

    mj_cmd = f'"{prompt} --ar 16:5 --style raw --stylize 200'
    if moodboard:
        # Strip any 'm' prefix or full URL the user might pass
        mb = moodboard.split("/")[-1].lstrip("m")
        mj_cmd += f" --p m{mb}"
    mj_cmd += '"'

    print("[limen] Generating via Midjourney (~30-60s)...")
    out = ssh(
        f"cd ~/tmp/imprimatur-bg && mkdir -p . && limen imagine {mj_cmd} --out ~/tmp/imprimatur-bg",
        timeout=240,
    )
    # Parse limen output for filenames
    paths = []
    for line in out.splitlines():
        if "Saved:" in line and ".png" in line:
            paths.append(line.split("Saved:")[1].strip().split(" ")[0])
    print(f"[limen] Generated {len(paths)} images")
    return paths


def pull_images_to_local(remote_paths: list[str]) -> list[Path]:
    """scp images from Mac to soma local /tmp/imprimatur/."""
    local_dir = Path("/tmp/imprimatur")
    local_dir.mkdir(exist_ok=True)
    local_paths = []
    for rp in remote_paths:
        name = Path(rp).name
        lp = local_dir / name
        subprocess.run(["scp", f"mac:{rp}", str(lp)], check=True, capture_output=True)
        local_paths.append(lp)
    return local_paths


def render_hex_overlay(variant: str, output_width: int = 800) -> Image.Image:
    """Render Open or Iconic Hexagon SVG to a PIL Image with transparency."""
    svg_path = OPEN_HEX_SVG if variant == "open" else ICONIC_HEX_SVG
    png_data = cairosvg.svg2png(url=str(svg_path), output_width=output_width)
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")
    # Trim to hexagon-only bounds (drop wordmark area on right; svg viewBox is 170.1 wide, hex is 0-127.6)
    hex_only = img.crop((0, 0, int(output_width * 127.6 / 170.1), img.height))
    return hex_only


def composite_banner(
    bg_path: Path, hex_overlay: Image.Image, hex_size_frac: float = 0.55
) -> Image.Image:
    """Composite hexagon overlay at centre of background."""
    bg = Image.open(bg_path).convert("RGBA")
    bg_w, bg_h = bg.size
    target_h = int(bg_h * hex_size_frac)
    aspect = hex_overlay.size[0] / hex_overlay.size[1]
    target_w = int(target_h * aspect)
    hex_resized = hex_overlay.resize((target_w, target_h), Image.Resampling.LANCZOS)
    pos_x = (bg_w - target_w) // 2
    pos_y = (bg_h - target_h) // 2
    composite = bg.copy()
    composite.alpha_composite(hex_resized, (pos_x, pos_y))
    return composite.convert("RGB")


def write_sized_variants(source_img: Image.Image, base_name: str, output_dir: Path):
    """Write source + 16:5 retina (1424x445) + 16:5 1x (712x222) variants."""
    output_dir.mkdir(parents=True, exist_ok=True)
    src_path = output_dir / f"{base_name}.png"
    source_img.save(src_path, "PNG", optimize=True)
    print(f"[output] source: {src_path} {source_img.size}")

    retina = source_img.resize((1424, 445), Image.Resampling.LANCZOS)
    retina_path = output_dir / f"{base_name}-16x5-retina-1424x445.png"
    retina.save(retina_path, "PNG", optimize=True)
    print(f"[output] retina (recommended for Word): {retina_path}")

    one_x = source_img.resize((712, 222), Image.Resampling.LANCZOS)
    one_x_path = output_dir / f"{base_name}-16x5-1x-712x222.png"
    one_x.save(one_x_path, "PNG", optimize=True)
    print(f"[output] 1x: {one_x_path}")

    return src_path, retina_path, one_x_path


def main():
    ap = argparse.ArgumentParser(
        description="Produce a corporate paper banner with HSBC brand overlay."
    )
    ap.add_argument(
        "prompt", help="Midjourney prompt (background only — do NOT mention hexagon/logo)"
    )
    ap.add_argument(
        "--moodboard",
        "-p",
        default=None,
        help="Midjourney moodboard code (e.g. m7426636666346930219)",
    )
    ap.add_argument(
        "--variant",
        "-v",
        choices=["open", "iconic"],
        default="open",
        help="Hexagon variant: open (transparent center, dark red, atmospheric bg) | iconic (white center, standard mark, light bg)",
    )
    ap.add_argument("--name", "-n", required=True, help="Output base filename (no extension)")
    ap.add_argument("--output-dir", "-o", default=".", help="Output directory")
    ap.add_argument(
        "--pick",
        type=int,
        default=None,
        help="Auto-pick image N (1-4); else save all 4 composites for manual choice",
    )
    ap.add_argument(
        "--hex-size",
        type=float,
        default=0.55,
        help="Hexagon height as fraction of background height",
    )
    args = ap.parse_args()

    output_dir = Path(args.output_dir).resolve()

    # Step 1-2: ensure JWT + generate via limen
    remote_paths = generate_via_limen(args.prompt, args.moodboard)
    local_paths = pull_images_to_local(remote_paths)

    # Step 3: composite hex overlay
    hex_overlay = render_hex_overlay(args.variant)
    print(f"[composite] Hex overlay rendered: {hex_overlay.size}, variant={args.variant}")

    if args.pick:
        bg_path = local_paths[args.pick - 1]
        composite = composite_banner(bg_path, hex_overlay, args.hex_size)
        write_sized_variants(composite, args.name, output_dir)
    else:
        # Save all 4 composites for manual review
        for i, bg_path in enumerate(local_paths, 1):
            composite = composite_banner(bg_path, hex_overlay, args.hex_size)
            base = f"{args.name}-pick{i}"
            out_path = output_dir / f"{base}.png"
            output_dir.mkdir(parents=True, exist_ok=True)
            composite.save(out_path, "PNG", optimize=True)
            print(f"[review] composite {i}/4: {out_path}")
        print(
            "\nReview the 4 composites and re-run with --pick N to generate sized variants for the chosen one."
        )


if __name__ == "__main__":
    main()
