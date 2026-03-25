# Editing PowerPoint Files Programmatically

Consolidated from 4 files (Feb 2026 CV editing sessions).

## Workflow

1. **Quit the app first** (not just close the document — `close every document` doesn't reliably release the file lock):
   ```bash
   osascript -e 'tell application "Keynote" to quit' 2>/dev/null
   osascript -e 'tell application "Microsoft PowerPoint" to quit' 2>/dev/null
   sleep 1
   ```
2. Edit via `uv run --with python-pptx python3 -c '...'` (no venv needed — ephemeral install)
3. Reopen: `open "<path>"`

## Find-and-Replace (text frames AND tables)

Text can live in text frames OR table cells. Must search both:

```python
for slide in prs.slides:
    for shape in slide.shapes:
        text_frames = []
        if shape.has_text_frame:
            text_frames.append(shape.text_frame)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    text_frames.append(cell.text_frame)
        for tf in text_frames:
            for para in tf.paragraphs:
                for run in para.runs:
                    if 'old text' in run.text:
                        run.text = run.text.replace('old text', 'new text')
```

## Table Cell Text (preserving formatting)

```python
cell = table.cell(row_idx, col_idx)
for i, para in enumerate(cell.text_frame.paragraphs):
    if para.runs:
        para.runs[0].text = new_texts[i]  # Set on first run
        for run in para.runs[1:]:          # Remove extras
            run._r.getparent().remove(run._r)
```

## Adding Paragraphs to Table Cells

python-pptx API doesn't support this cleanly. Manipulate XML directly:

```python
from copy import deepcopy
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
txBody = cell.text_frame._txBody
paras = txBody.findall('.//a:p', ns)
new_para = deepcopy(paras[0])  # copy formatting
for r in new_para.findall('.//a:r', ns):
    new_para.remove(r)
new_run = deepcopy(paras[0].findall('.//a:r', ns)[0])
new_run.find('.//a:t', ns).text = "New bullet text"
new_para.append(new_run)
paras[0].addnext(new_para)
```

## Image Replacement in Placeholders

```python
rId = shape._element.blipFill.blip.rEmbed  # NOT .embed
image_part = slide.part.rels[rId].target_part  # NOT .related_parts
with open(photo_path, 'rb') as f:
    image_part._blob = f.read()
```

## Rendering PPTX to Images

`qlmanage -t` only renders slide 1. PowerPoint AppleScript export times out with screen locked. What works:

```bash
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run --with aspose.slides python3 -c "
import aspose.slides as slides
prs = slides.Presentation('file.pptx')
for i in range(prs.slides.length):
    sl = prs.slides[i]
    img = sl.get_image(2.0, 2.0)
    img.save(f'/tmp/slide_{i+1}.png', slides.ImageFormat.PNG)
"
```

Note: Aspose trial adds watermark. Requires `brew install mono-libgdiplus`.

## XML-Based Editing (Anthropic PPTX Skill)

Alternative to python-pptx for text edits — works directly on slide XML:

1. `unpack.py` → pretty-printed XML in `unpacked/`
2. Edit `ppt/slides/slideN.xml` with Edit tool (search `<a:t>` tags)
3. `clean.py` → remove orphans
4. `pack.py --original` → repack with validation

Scripts at: `~/.claude/plugins/cache/anthropic-agent-skills/claude-api/.../skills/pptx/scripts/`

**Advantages:** No python-pptx dependency, preserves all formatting, parallel subagent editing per slide.
**Gotcha:** Must close `</a:t>` tag — easy to miss with Edit tool. Pack validates and catches it.

## Gotchas

- **PowerPoint reload:** `open` on an already-open file is a no-op — PowerPoint keeps its in-memory copy. Must `osascript -e 'tell application "Microsoft PowerPoint" to close every presentation saving no'` then `open` again. Chain with `sleep 1` between.
- **Smart quotes:** Use `\u2019` for right single quote (apostrophe in "bank's"), `\u2018` for left. pptx files use curly quotes; Python strings use straight. `repr()` to debug.
- **SchemeColor has no .rgb:** Accessing `run.font.color.rgb` throws `AttributeError` for theme colors. Deepcopy XML elements to preserve formatting instead of reading properties.
- **Text split across runs:** PowerPoint splits text for formatting. `para.text` is read-only concatenation — work at `run.text` level.
- **screencapture with closed lid:** Returns black. `caffeinate -u` doesn't help without external display.
- **Consulting CV tables:** Templates like Capco's put project details in tables. Searching only `shape.has_text_frame` misses them.
