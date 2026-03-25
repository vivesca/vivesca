# Stream-from-Archive: Directory-at-a-Time Processing

When an archive (ZIP, tar) exceeds available disk space, process it one directory at a time instead of extracting everything.

## Pattern

```
Phase 1: Index   — Read archive metadata, group entries by directory. Zero disk I/O.
Phase 2: Process — For each directory: extract → analyze → act → delete temp files.
Phase 3: Persist — Write results to a manifest for resume capability.
```

Peak disk = size of largest directory (~1-2GB), not the full archive (~50GB+).

## Key Design Decision: Analysis vs Action Separation

When files in the same directory have relationships (e.g., photo+video live pairs, source+header, data+schema), you must extract ALL related files for correct analysis — even files you won't act on.

Use a `should_import` / `should_process` flag to separate "needed for analysis" from "needs action":

```rust
struct ArchiveEntry {
    index: usize,
    relative_path: String,
    should_process: bool,  // false = extract for analysis only, skip during action phase
}
```

**Without this:** On resume runs, a video whose paired photo was already imported would be processed as a standalone file (duplicate). The pairing relationship is only discoverable when both files are on disk.

## Applicability

- Archive size > free disk space
- Processing logic is directory-scoped (sidecar matching, paired files, schema validation)
- Resume capability needed (manifest tracks completed items)

## Implementation: photoferry

`~/code/photoferry/src/main.rs` — `process_zip_streaming()`. Uses Rust `zip` crate's `ZipArchive::by_index_raw()` for zero-cost metadata reads in Phase 1, `by_index()` for extraction in Phase 2.

See also: `~/docs/solutions/photoferry-reference.md`
