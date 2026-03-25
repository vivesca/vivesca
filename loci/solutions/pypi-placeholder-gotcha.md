# PyPI Placeholder Package Gotcha

## Problem

When securing a PyPI name with a minimal placeholder (0.0.1), `uv tool install <name>` installs the placeholder — which has no entry points — and then immediately removes the tool ("No executables are provided by package").

## Why

`uv tool install` resolves to the latest version. If the placeholder is the only version, that's what gets installed. Since it has no `[project.scripts]`, uv considers it invalid as a tool.

## Fix

After publishing the real version, force-install with the specific version or from the local wheel:

```bash
uv tool install <name>==0.3.0 --force        # if indexed
uv tool install ./dist/<name>-0.3.0.whl --force  # from local build
```

Or just wait for PyPI to index the new version (usually <5 min) before running `uv tool install`.

## Prevention

Publish the placeholder WITH a minimal entry point:

```toml
[project.scripts]
mypackage = "mypackage:main"
```

```python
# mypackage/__init__.py
def main():
    print("This package has been renamed. Install the new version.")
```
