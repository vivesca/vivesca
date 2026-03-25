
## ERR-20260306-001: libgdk-pixbuf2.0-0 renamed in Bookworm

**Symptom:** Railway build fails with `E: Package 'libgdk-pixbuf2.0-0' has no installation candidate`

**Cause:** Debian Bookworm renamed the package. Old name worked on Buster/Bullseye.
- Old: `libgdk-pixbuf2.0-0`
- New: `libgdk-pixbuf-2.0-0` (hyphen before 2)

**Fix:** Update apt-get install line in Dockerfile.

**Context:** python:3.11-slim switched to Bookworm base. Affected all Railway builds silently — old deployment kept running while new ones failed.
