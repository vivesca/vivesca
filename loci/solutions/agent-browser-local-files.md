# agent-browser: Can't open file:// URLs

## Problem

`agent-browser open "file:///path/to/file.html"` fails — it silently upgrades `file://` to `https://file///...` which hits `ERR_NAME_NOT_RESOLVED`.

## Fix

Serve locally first:

```bash
python3 -m http.server 8787 -d /path/to/dir &
sleep 2
agent-browser open "http://localhost:8787"
```

## Also useful

- `agent-browser upload '#fileInput' file1.txt file2.txt` works for hidden `<input type="file">` elements
- `agent-browser --headed` flag doesn't help — same issue
