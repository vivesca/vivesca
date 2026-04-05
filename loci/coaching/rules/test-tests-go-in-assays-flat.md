---
title: Tests go in `assays/` flat
impact: MEDIUM
tags: test
---

## Tests go in `assays/` flat

NEVER mirror source directory structure (e.g., `assays/metabolon/organelles/`). All test files are `assays/test_<name>.py`. For subpackage modules, use a prefix: `assays/test_rss_fetcher.py`, not `assays/metabolon/organelles/endocytosis_rss/test_fetcher.py`.
