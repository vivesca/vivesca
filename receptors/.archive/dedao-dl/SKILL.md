---
name: dedao-dl
description: Download courses, ebooks, and audiobooks from Dedao (得到) via dedao-dl CLI.
user_invocable: false
github_url: https://github.com/yann0917/dedao-dl
github_hash: 7a8097a
---

# Dedao Downloader (得到下载器)

Download courses, ebooks, and audiobooks from the Dedao (得到/iGet) app. Supports MP3 audio, PDF documents, Markdown notes, EPUB ebooks.

**Source:** https://github.com/yann0917/dedao-dl

## Setup Check (Always Run First)

```bash
# Check if dedao-dl is installed
command -v dedao-dl >/dev/null 2>&1 && echo "dedao-dl installed: $(dedao-dl -v)" || echo "NOT INSTALLED"

# Check login status
dedao-dl who 2>/dev/null || echo "NOT LOGGED IN"
```

### If NOT Installed

```bash
# Option 1: Install via Go (requires Go 1.23+)
go install github.com/yann0917/dedao-dl@latest

# Option 2: Download binary from releases
# https://github.com/yann0917/dedao-dl/releases
```

**Dependencies for full functionality:**
- `wkhtmltopdf` - For PDF generation
- `ffmpeg` - For audio processing

```bash
# macOS
brew install wkhtmltopdf ffmpeg

# Linux
sudo apt install wkhtmltopdf ffmpeg
```

### Login

⚠️ **IMPORTANT: QR login doesn't persist!** Use cookie method for permanent login.

```bash
# ❌ QR code login - DOES NOT PERSIST (session lost after command)
dedao-dl login -q

# ✅ Cookie login - PERSISTS to config.json (recommended)
dedao-dl login -c "GAT=<your_token>"
```

**How to get GAT token (persists ~30 days):**
1. Open https://www.dedao.cn in browser
2. Login via QR code scan
3. Open DevTools: `Cmd+Option+I` (Mac) or `F12` (Windows)
4. Go to **Application** → **Cookies** → `https://www.dedao.cn`
5. Find `GAT` cookie, copy its value (starts with `eyJ...`)
6. Run: `dedao-dl login -c "GAT=eyJ...your_token..."`

**Check login status:**
```bash
dedao-dl who   # Shows user info if logged in
```

**Config location:** `~/notes/dedao-courses/config.json` (or current working directory)

## Quick Reference

| Command | Purpose |
|---------|---------|
| `dedao-dl cat` | List categories (courses, ebooks, audiobooks) |
| `dedao-dl course` | List purchased courses |
| `dedao-dl ebook` | List ebook shelf |
| `dedao-dl odob` | List audiobook shelf (每天听本书) |
| `dedao-dl dl ID` | Download course by ID |
| `dedao-dl dle ID` | Download ebook by ID |
| `dedao-dl dlo ID` | Download audiobook by ID |

## Detailed Commands

### List Content

```bash
# View all categories
dedao-dl cat

# List purchased courses
dedao-dl course

# View course details (chapters)
dedao-dl course -i 51

# List ebooks
dedao-dl ebook

# List audiobooks (每天听本书)
dedao-dl odob
```

### Download Courses

```bash
# Download course by ID
dedao-dl dl 51 -t 1        # MP3 audio
dedao-dl dl 51 -t 2        # PDF document
dedao-dl dl 51 -t 3        # Markdown notes

# Options
# -t  Format: 1=MP3, 2=PDF, 3=Markdown
# -m  Merge markdown into single file
# -c  Include popular comments
# -o  Prefix filenames with order number (001., 002., etc)

# Example: Download all with numbered markdown and comments
dedao-dl dl 51 -t 3 -m -c -o
```

### Download Ebooks

```bash
# Download ebook by ID
dedao-dl dle 123 -t 1      # HTML format
dedao-dl dle 123 -t 2      # PDF format
dedao-dl dle 123 -t 3      # EPUB format

# Export reading notes
dedao-dl ebook notes -i 123           # View notes
dedao-dl dle 123 -t 4                 # Download as Markdown
```

### Download Audiobooks (每天听本书)

```bash
# Download audiobook by ID
dedao-dl dlo 456 -t 1      # MP3 audio
dedao-dl dlo 456 -t 2      # PDF transcript
dedao-dl dlo 456 -t 3      # Markdown transcript
```

## Download Formats

| Type | -t 1 | -t 2 | -t 3 | -t 4 |
|------|------|------|------|------|
| Course (dl) | MP3 | PDF | Markdown | - |
| Ebook (dle) | HTML | PDF | EPUB | Markdown notes |
| Audiobook (dlo) | MP3 | PDF | Markdown | - |

## Workflow Examples

### Download a specific course with all materials

```bash
# 1. Find course ID
dedao-dl course | grep "投资"

# 2. View course structure
dedao-dl course -i 51

# 3. Download all formats
dedao-dl dl 51 -t 1 -o     # Audio with numbering
dedao-dl dl 51 -t 3 -m -c  # Merged markdown with comments
```

### Batch download all audiobooks

```bash
# List all audiobook IDs
dedao-dl odob | awk '{print $2}'

# Download each (example loop)
for id in 123 456 789; do
    dedao-dl dlo $id -t 3
done
```

### Export ebook reading notes

```bash
# 1. List ebooks with notes
dedao-dl ebook

# 2. View notes for specific book
dedao-dl ebook notes -i 158162

# 3. Export as markdown
dedao-dl dle 158162 -t 4
```

## Workflow Summary

| User Says | Action |
|-----------|--------|
| "list dedao courses" | `dedao-dl course` |
| "download dedao course X" | Find ID, then `dedao-dl dl ID -t 3 -m -o` |
| "download dedao ebook" | Find ID, then `dedao-dl dle ID -t 3` |
| "export dedao notes" | `dedao-dl ebook notes -i ID` or `dedao-dl dle ID -t 4` |
| "download audiobook" | Find ID, then `dedao-dl dlo ID -t 1` |
| "login to dedao" | Get GAT cookie from browser, then `dedao-dl login -c "GAT=..."` |

## Notes

- **Rate limiting:** PDF generation may trigger captcha if too fast; tool adds random delays
- **Storage:** Downloads save to current directory by default
- **Copyright:** Content is for personal use only; respect intellectual property rights
