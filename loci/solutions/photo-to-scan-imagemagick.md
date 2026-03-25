# Photo-to-Scan with ImageMagick

Convert phone photos of documents into clean, scanner-quality PDFs using `magick`.

## The Recipe (v7 — final)

```bash
magick input.jpeg \
    -fuzz 18% -fill white -draw "color 0,0 floodfill" \
    -fuzz 18% -fill white -draw "color %[fx:w-1],0 floodfill" \
    -fuzz 18% -fill white -draw "color 0,%[fx:h-1] floodfill" \
    -fuzz 18% -fill white -draw "color %[fx:w-1],%[fx:h-1] floodfill" \
    -deskew 40% \
    -brightness-contrast 30x30 \
    -white-threshold 75% \
    -sharpen 0x1 \
    -resize 2480x3508! \
    -density 300 -units PixelsPerInch \
    -quality 95 \
    output.jpg
```

## Combine into multi-page PDF

```bash
magick page1.jpg page2.jpg page3.jpg \
    -compress JPEG -quality 90 -density 300 \
    output.pdf
```

## What Each Step Does

| Step | Purpose |
|------|---------|
| `-fuzz 18% -fill white -draw "color 0,0 floodfill"` | Flood-fill background from each corner with white. 18% fuzz matches brown/grey surfaces without eating into paper edge |
| `-deskew 40%` | Straighten tilted documents |
| `-brightness-contrast 30x30` | Push light greys (form shading, paper tone) toward white |
| `-white-threshold 75%` | Anything lighter than 75% grey → pure white. Kills form header shading |
| `-sharpen 0x1` | Light sharpen for crisp text |
| `-resize 2480x3508!` | Force to exact A4 at 300 DPI (2480×3508 px). `!` ignores aspect ratio |
| `-density 300` | Embed 300 DPI metadata |

## Key Lessons (from 7 iterations)

1. **Don't trim A4 documents.** `-trim` removes the paper's natural margins, then you have to add artificial ones back. Just flood-fill the background and resize to A4.

2. **Flood-fill corners, not edge detection.** `-fuzz 18%` from all 4 corners reliably removes table/desk backgrounds regardless of colour. Higher fuzz (25%) can eat into white paper edges.

3. **`-normalize` and `-level` crush form shading.** These make light grey header rows into dark blocks. Use `-brightness-contrast` + `-white-threshold` instead — pushes greys to white while keeping text dark.

4. **Don't go grayscale unless needed.** `-colorspace Gray` + `-sigmoidal-contrast` looked "scanned" but too aggressive. Colour mode with brightness boost is cleaner.

5. **`-resize WxH!` (with bang) for exact dimensions.** Without `!`, ImageMagick preserves aspect ratio and leaves white bars. Documents are already roughly A4, so the slight stretch is invisible.

## Export from Photos App (AppleScript)

```bash
# List recent photos
osascript -e '
tell application "Photos"
    set allItems to media items
    set itemCount to count of allItems
    set startIdx to itemCount - 9
    set output to ""
    repeat with i from startIdx to itemCount
        set p to item i of allItems
        set output to output & (id of p) & tab & (filename of p) & tab & (date of p) & linefeed
    end repeat
    return output
end tell'

# Export by ID
osascript -e '
tell application "Photos"
    set ids to {"PHOTO-ID-HERE"}
    set exportFolder to POSIX file "/tmp/export"
    set photosToExport to {}
    repeat with pid in ids
        set end of photosToExport to (media item id pid)
    end repeat
    export photosToExport to exportFolder
end tell'
```

Note: `photos.py` requires Full Disk Access on the parent process (sshd/Ghostty). AppleScript via `osascript` works without FDA.

## File Delivery to Phone

- `~/Documents/` syncs to iCloud Drive → Files app → Documents
- Direct iCloud Drive path (`com~apple~CloudDocs/`) has permission issues from CLI — use `~/Documents/` instead
