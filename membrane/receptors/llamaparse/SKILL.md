---
name: llamaparse
description: Parse unstructured documents (PDF, PPTX, DOCX, XLSX) into markdown via LlamaParse. Use when extracting prose/tables/figures from a document for chromatin reference, paper grounding, or downstream analysis.
compatibility: Needs `LLAMA_CLOUD_API_KEY` in environment and `@llamaindex/llama-cloud@latest` installed (TS path) OR `llama-cloud` Python package via `uvx`.
license: MIT
metadata:
  author: LlamaIndex
  version: "1.0.0"
# vivesca endosymbiont tracking — managed by `competence` skill drift detection
upstream: run-llama/llamaparse-agent-skills
upstream_path: skills/llamaparse
upstream_commit: 3288ff045f57
upstream_check: 2026-04-28
upstream_license: MIT
endosymbiont: true
triggers:
  - parse pdf
  - parse document
  - llamaparse
  - extract pdf
  - convert pdf to markdown
  - parse annual report
  - parse regulation
---


# LlamaParse Skill

Parse unstructured documents (such as PDF, DOCX, PPTX, XLSX) with LlamaParse and extract their contents (text, markdown, images...).

## Initial Setup

When this skill is invoked, respond with:

```
I'm ready to use LlamaParse to parse files. Before we begin, please confirm that:

- `LLAMA_CLOUD_API_KEY` is set as environment variable within the current environment
- `@llamaindex/llama-cloud@latest` is installed and available within the current Node environment

If both of them are set, please provide:

1. One or more files to be parsed
2. Specific parsing options, such as tier, API version, custom prompt, processing options...
3. Any requests you might have regarding the parsed content of the file.

I will produce a Typescript script to run the parsing job and, once you approved its execution, I will report the results back to you based on your request.
```

Then wait for the user's input.

---

## Step 0 — Install `llama-cloud` (optional)

If the user does not have the `@llamaindex/llama-cloud` package installed, add it to the current environment by running:

```bash
npm install @llamaindex/llama-cloud@latest
```

## Step 1 — Produce a Typescript Script

Once the user confirms the environment variables are set and provides the necessary details for the parsing job, produce a **typescript script**.

As a source of truth for the TS script, you can:

- Refer to the [example.ts](scripts/example.ts) script, which covers most of the necessary configurations for LlamaParse
- Refer to the complete LlamaParse Documentation, fetching the `https://developers.llamaindex.ai/python/cloud/llamaparse/api-v2-guide/` page.

### Scripting Best Practices

Follow these guidelines when generating scripts:

#### 1. Always Use the Top-Level `LlamaCloud` Client

Use `LlamaCloud` (the API client) for all parsing operations:

```typescript
import LlamaCloud from "@llamaindex/llama-cloud";

// Define a client
const client = new LlamaCloud({
  apiKey: process.env["LLAMA_CLOUD_API_KEY"], // This is the default and can be omitted
});

```

#### 2. Two-Step Upload → Parse Pattern

Always upload first to get a file ID, then parse using the file ID. Never pass raw file bytes directly to `parse()`.

```typescript
import { readFile, writeFile } from "fs/promises";
import { basename } from "path";

// 1. Convert the file path into a File object
const buffer = await readFile(filePath);
const fileName = basename(filePath);
const file = new File([buffer], fileName);
// 2. Upload the file to the cloud
const fileObj = await client.files.create({
  file: file,
  purpose: "parse",
});
// 3. Get the file ID
const fileId = fileObj.id;
// 4. Use the file ID to parse the file
const result = await client.parsing.parse({
  tier: "agentic",
  version: "latest",
  file_id: fileId,
  ...
});
```

If the user already has a file ID (e.g. from a prior upload), skip the upload step and use it directly.

#### 3. Choose the Right Tier

| Tier | When to Use |
|------|-------------|
| `fast` | Speed is the priority; simple documents |
| `cost_effective` | Budget-conscious; straightforward text extraction |
| `agentic` | Complex layouts, tables, mixed content (default recommendation) |
| `agentic_plus` | Advanced analysis, highest accuracy |

Default to `agentic` unless the user specifies otherwise or the document is simple.

#### 4. Always Include the `expand` Parameter

The `expand` parameter controls what content is returned. Omitting it returns minimal data. Always specify exactly what you need:

| Value | Returns |
|-------|---------|
| `text_full` | Plain text via `result.text_full` |
| `markdown_full` | Markdown via `result.markdown_full` |
| `items` | Page-level JSON via `result.items.pages` |
| `text_content_metadata` | Per-page text metadata |
| `markdown_content_metadata` | Per-page markdown metadata |
| `items_content_metadata` | Per-page items metadata |
| `images_content_metadata` | Image list with presigned URLs |
| `output_pdf_content_metadata` | Output PDF metadata |
| `xlsx_content_metadata` | Excel-specific metadata |

Only request metadata `*_content_metadata` variants when you need presigned URLs or per-page detail — they increase payload size.

#### 5. Handle None Results Defensively

`result.text_full`, `result.markdown_full`, and `result.items` may be `undefined` on failure. Always guard against this:

```typescript
const text = result.text_full ?? "";
const markdown = result.markdown_full ?? "";
```

#### 6. Use Structured Options for Advanced Configuration

Group options using the correct nested keys:

```typescript
const result = await client.parsing.parse({
  tier: "agentic",
  version: "latest",
  file_id: fileId,
  input_options: {
    presentation: {
      skip_embedded_data: false,
    },
  },
  output_options: {
    images_to_save: ["screenshot"],
    markdown: {
      tables: { output_tables_as_markdown: true },
      annotate_links: true,
    },
  },
  processing_options: {
    specialized_chart_parsing: "agentic",
    ocr_parameters: { languages: ["de", "en"] },
  },
  agentic_options: {
    custom_prompt:
      "Extract text from the provided file and translate it from German to English.",
  },
  expand: [
    "markdown_full",
    "images_content_metadata",
    "markdown_content_metadata",
  ],
});
```

Use `agentic_options.custom_prompt` whenever the user wants to guide extraction (translation, summarization, structured extraction, etc.).

#### 7. Downloading Images Requires `httpx` and Auth

When `images_content_metadata` is in `expand`, download images via presigned URLs with Bearer auth:

```typescript
if (result.images_content_metadata) {
  for (const image of result.images_content_metadata.images) {
    if (image.presigned_url) {
      const response = await fetch(image.presigned_url, {
        headers: {
          Authorization: `Bearer ${process.env["LLAMA_CLOUD_API_KEY"]}`,
        },
      });
      if (response.ok) {
        const content = await response.bytes();
        await writeFile(image.filename, content);
      }
    }
  }
}
```

#### 8. Use the Node shebang

Every generated script should include the node shebang:

```typescript
#!/usr/bin/env node
```

---

## Step 2 — Execute the Typescript Script

Once the typescript script has been produced, you should:

1. Present the script to the user and ask for permissions to run it (depending on the current permissions settings)
2. Once you obtained permission to run, execute the script
3. Explore the results based on the user's requests

> In order to run typescript scripts, it is highly recommended to use: `npx tsx script.ts`.

---

<!-- VIVESCA OVERLAY — preserve through upstream sync. Drift detection in `competence` skill diffs only the upstream-managed lines above this marker. -->

## Vivesca Conventions (post-upstream)

**API key.** Always resolved from 1Password — never paste keys into scripts or env files in cleartext.

```bash
echo 'LLAMA_CLOUD_API_KEY=op://Agents/LlamaParse/credential' > /tmp/llamaparse.env
chmod 600 /tmp/llamaparse.env
op run --env-file=/tmp/llamaparse.env -- <command>
```

**Python over TypeScript for one-shots.** Upstream defaults to TS; for ad-hoc parsing prefer Python via `uvx --with llama-cloud`. TS is required only when the workflow is part of a Node project. Working template at the AR extraction precedent (28 Apr 2026) — fetch URL → upload → parse → save markdown to chromatin path.

**Output destination.** Parsed documents land in `~/epigenome/chromatin/immunity/` (private repo) with frontmatter recording source URL, extraction date, parser version, and `purpose:` describing why grounded.

**Tier selection.** `agentic` for board-quality references (annual reports, regulations, committee papers we ground in); cheaper tier for one-off quick extractions where verbatim quotation isn't load-bearing.

**Cost discipline.** Free tier is 1000 pages/day. A 372-page annual report uses ~37% of daily quota. Batch parses across multiple days when possible; check `https://cloud.llamaindex.ai/usage` before large batches.

**Verbatim retention.** When parsing a document we'll later quote verbatim in a paper (per `feedback_preserve_verbatim_from_primary_sources`), preserve the LlamaParse output as the source-of-truth file in chromatin. Do not re-parse for stylistic improvements — the parsed file IS the citable source.

**Used by.** `induction` skill (HSBC AR house-style reference at `chromatin/immunity/hsbc-ar2025-full-markdown.md`); future committee papers; controls paper series; regulator submissions; any client AR for new pitch context.

**TS dispatch gotchas (filed 2026-04-28).**
- **Top-level `await` fails under `npx tsx`** because tsx defaults to CJS output. Always wrap script body in async IIFE: `(async () => { ... })();`. Upstream skill examples don't show this wrapper; the failure mode is a transform-time error, not runtime. Easy to miss.
- **Module resolution from `/tmp`** doesn't pick up globally-installed npm packages by default. Either install local (cd to a project dir with package.json), or set `NODE_PATH=$(npm root -g)` before invoking. Global install at `~/.local/npm/lib/node_modules` is NOT auto-discovered.
- **Combined invocation pattern** that works on soma: `NODE_PATH=$(npm root -g) op run --env-file=/tmp/llamaparse.env -- npx tsx /path/to/script.ts`.

**Source URL extension gotcha (filed 2026-04-28, see `finding_llamaparse_arxiv_pdf_suffix_required.md`).** LlamaParse `source_url=...` downloads to a temp file using the URL basename and rejects the file if no recognisable extension. arxiv `/pdf/<id>` URLs (no `.pdf` suffix) fail with "not of a supported file type." Append `.pdf` — arxiv serves the same bytes. Same trap for DOI redirects and regulator URLs with opaque IDs. Fallback: two-step upload via `client.files.create(...)` then `parse(file_id=...)`.

**Config exploration findings (filed 2026-04-28, see `finding_llamaparse_config_exploration_2026-04-28.md`).**
- **Custom prompts are the highest-leverage feature.** Use `agentic_options.custom_prompt` for table-heavy docs, multilingual extraction, or structured-data passes. Empirically the clearest win in the three tested configs.
- **`agentic_plus` shows no clear delta over `agentic`** on prose + simple chart-box pages. Only worth the quota cost on dense financial tables; test before defaulting to it.
- **Presigned-URL auth is broken in upstream skill examples.** The pattern `headers: { Authorization: Bearer ... }` on `image.presigned_url` returns HTTP 400. Presigned URLs auth via signature in the URL itself; adding headers breaks signature validation. Drop the Bearer header for presigned-URL fetches.
- **Verification screenshots from `pdftoppm` must be ≥200dpi.** CC's own visual reading at 150dpi can introduce OCR-equivalent errors on small-font figures (e.g., misreading 9 as 6). Use `pdftoppm -r 200` minimum, 300dpi when ambiguous.
