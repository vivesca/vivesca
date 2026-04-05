---
title: Not needed on Python 3.14+
impact: MEDIUM
tags: fileops
---

## Not needed on Python 3.14+

Union types (`X | Y`) work natively since 3.10. Don't add this import to new files. Existing files will be cleaned up over time.
