
## LRN-20260312-001: Deep/xpol runs should auto-save to vault

**Problem:** Launched `consilium --deep --xpol` without `--vault`. Output location unclear after run completes.

**Fix:** Auto-enable `--vault` when `--deep` or `--xpol` is passed. Quick runs (`--quick`) stay throwaway. Deep deliberations are always worth keeping.

**Implementation:** In the CLI arg parser, if `deep` or `xpol` is set and `no_save` is not set, default `vault` to true.

## LRN-20260312-002: Long consilium runs truncate when launched from CC background

**Problem:** `run_in_background: true` in Claude Code captures stdout into a pipe. For long consilium runs (5+ models, 2 rounds, xpol), the pipe buffer overflows or CC truncates. Result: partial output (only prompt captured), no synthesis.

**Root cause:** CC background tasks use pipes, not file redirects. `stdout_is_file_redirect()` returned false, so consilium streamed everything to the pipe.

**Fixed (v0.5.3):** Added `stdout_is_pipe()` detection + `SilentOutput`. When piped: suppress stdout entirely, rely on session auto-save, print only the session file path at exit. CC gets back one line (the path) and can `cat` it. File redirects (`> file`) still get full streaming output.

**Usage from CC background:** Run consilium normally. `TaskOutput` will show the session path. Then `cat <path>` to read the full result.
