# gog gmail attachment: --out and --name flags

## Syntax

```bash
gog gmail attachment <messageId> <attachmentId> --out <path> --name <filename>
```

Both `messageId` and `attachmentId` are **positional** (not flags). The attachmentId is the long base64 string from `gog gmail read` output.

## Gotcha: --out with directory vs file

- `--out ~/dir/` + `--name file.pdf` — works correctly (v0.11.0+)
- `--out ~/dir/file.pdf` (no --name) — works correctly
- `--out ~/dir/` (no --name) — silent failure, creates 64-byte metadata file

**Rule:** Always pair `--out <dir>` with `--name <filename>`, or use `--out <full-path>`.

## Reply to email with quoted original

```bash
gog gmail send \
  --reply-to-message-id <messageId> \
  --to "recipient@example.com" \
  --subject "Re: Original Subject" \
  --body "Reply text" \
  --quote
```

- `--quote` includes the original message below the reply
- `--reply-all` auto-populates recipients from original (skip `--to`)
- `--dry-run` to preview before sending

## Tags

gog, gmail, attachment, download, reply, send, cli
