# Task 8: Multi-Step Workflow

1. Read the file `~/germline/effectors/cg` (a small bash wrapper script).
2. Write a Python file `test_cg_config.py` that:
   - Extracts the ANTHROPIC_BASE_URL value from the cg script (by reading the file, not hardcoding)
   - Validates the URL is reachable with a HEAD request (use urllib, not requests)
   - Extracts the model name from the script
   - Writes all findings to `cg_report.json` with keys: `base_url`, `model`, `url_reachable` (bool)
3. Run the test script: `python3 test_cg_config.py`
4. Verify `cg_report.json` was created with correct values.
