"""HygieneSubstrate — metabolism of the organism's own tooling health.

Senses dependency freshness, pre-commit hook versions, test suite health,
and Python version. Proposes or executes upgrades for safe changes.
"""

import re
import subprocess
import sys
from pathlib import Path


def _run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command, return CompletedProcess. Never raises."""
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr=f"timeout after {timeout}s"
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr=f"command not found: {cmd[0]}"
        )


class HygieneSubstrate:
    """Substrate for dependency and tooling health."""

    name: str = "hygiene"

    def __init__(self, project_root: Path | None = None):
        self.root = project_root or Path.cwd()

    def sense(self, days: int = 30) -> list[dict]:
        """Collect tooling health signals."""
        health_signals: list[dict] = []
        health_signals.extend(self._sense_deps())
        health_signals.extend(self._sense_hooks())
        health_signals.extend(self._sense_tests())
        health_signals.extend(self._sense_python())
        return health_signals

    def _sense_deps(self) -> list[dict]:
        """Check for outdated dependencies via uv."""
        result = _run(["uv", "lock", "--upgrade", "--dry-run"], cwd=self.root)
        if result.returncode != 0:
            return [{"kind": "deps", "error": result.stderr.strip()[:200]}]

        health_signals: list[dict] = []
        # Parse lines like: "Updated foo v1.0.0 -> v1.1.0"
        for line in result.stderr.splitlines() + result.stdout.splitlines():
            m = re.search(r"(?:Updated|Would update)\s+(\S+)\s+v?(\S+)\s*->\s*v?(\S+)", line)
            if m:
                pkg, current, available = m.group(1), m.group(2), m.group(3)
                major_bump = current.split(".")[0] != available.split(".")[0]
                health_signals.append(
                    {
                        "kind": "dep",
                        "package": pkg,
                        "current": current,
                        "available": available,
                        "major": major_bump,
                    }
                )
        return health_signals

    def _sense_hooks(self) -> list[dict]:
        """Check for outdated pre-commit hooks.

        Runs autoupdate, diffs the config, then restores the original.
        This is a true dry-run since pre-commit lacks --dry-run.
        """
        config = self.root / ".pre-commit-config.yaml"
        if not config.exists():
            return []

        original = config.read_text()
        result = _run(["pre-commit", "autoupdate"], cwd=self.root)

        if result.returncode != 0:
            config.write_text(original)  # restore on failure
            return [{"kind": "hooks", "error": result.stderr.strip()[:200]}]

        updated = config.read_text()
        config.write_text(original)  # always restore — act() will re-run if needed

        if original == updated:
            return []

        health_signals: list[dict] = []
        # Parse output for "updating repo -> rev"
        for line in result.stdout.splitlines() + result.stderr.splitlines():
            m = re.search(r"updating\s+(\S+)\s.*->\s*(\S+)", line, re.IGNORECASE)
            if m:
                repo, new_rev = m.group(1), m.group(2)
                health_signals.append(
                    {
                        "kind": "hook",
                        "repo": repo,
                        "new_rev": new_rev,
                    }
                )

        # Fallback: if output didn't parse but config changed
        if not health_signals and original != updated:
            health_signals.append({"kind": "hook", "repo": "(unknown)", "new_rev": "(changed)"})

        return health_signals

    def _sense_tests(self) -> list[dict]:
        """Run test suite and capture pass/fail counts.

        Skips if VIVESCA_HYGIENE_NO_TESTS is set to prevent recursive pytest runs.
        """
        import os

        if os.environ.get("VIVESCA_HYGIENE_NO_TESTS"):
            return [
                {
                    "kind": "tests",
                    "passed": 0,
                    "failed": 0,
                    "errors": 0,
                    "healthy": True,
                    "skipped": True,
                }
            ]

        # Set guard to prevent recursion when hygiene runs inside pytest
        env = {**os.environ, "VIVESCA_HYGIENE_NO_TESTS": "1"}
        result = _run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header"],
            cwd=self.root,
            env=env,
        )
        output = result.stdout + result.stderr
        # Parse "210 passed" or "3 failed, 207 passed"
        passed = 0
        failed = 0
        errors = 0
        for m in re.finditer(r"(\d+)\s+(passed|failed|error)", output):
            count, kind = int(m.group(1)), m.group(2)
            if kind == "passed":
                passed = count
            elif kind == "failed":
                failed = count
            elif kind == "error":
                errors = count

        return [
            {
                "kind": "tests",
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "healthy": failed == 0 and errors == 0,
            }
        ]

    def _sense_python(self) -> list[dict]:
        """Check Python version against requires-python."""
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        requires = ""
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            m = re.search(r'requires-python\s*=\s*"([^"]+)"', pyproject.read_text())
            if m:
                requires = m.group(1)

        return [
            {
                "kind": "python",
                "current": current,
                "requires": requires,
            }
        ]

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Filter to actionable items."""
        actionable: list[dict] = []
        for item in sensed:
            kind = item.get("kind")
            if (
                (kind == "dep" and item.get("available"))
                or (kind == "hook" and item.get("new_rev"))
                or (kind == "tests" and not item.get("healthy"))
                or (kind in ("deps", "hooks") and item.get("error"))
            ):
                actionable.append(item)
        return actionable

    def act(self, candidate: dict) -> str:
        """Execute safe upgrades, propose risky ones."""
        kind = candidate.get("kind")

        if kind == "dep":
            pkg = candidate["package"]
            available = candidate["available"]
            if candidate.get("major"):
                return f"propose: upgrade {pkg} to {available} (MAJOR — check changelog)"
            # Minor/patch: execute
            result = _run(
                ["uv", "lock", "--upgrade-package", pkg],
                cwd=self.root,
            )
            if result.returncode == 0:
                return f"upgraded: {pkg} {candidate['current']} -> {available}"
            return f"failed: {pkg} upgrade — {result.stderr.strip()[:100]}"

        elif kind == "hook":
            repo = candidate["repo"]
            new_rev = candidate["new_rev"]
            result = _run(["pre-commit", "autoupdate"], cwd=self.root)
            if result.returncode == 0:
                return f"updated: {repo} -> {new_rev}"
            return f"failed: hook update — {result.stderr.strip()[:100]}"

        elif kind == "tests":
            failed = candidate.get("failed", 0)
            errors = candidate.get("errors", 0)
            return f"propose: investigate {failed} test failure(s), {errors} error(s)"

        elif candidate.get("error"):
            return f"propose: fix {kind} sensing — {candidate['error'][:100]}"

        return f"unknown: {kind}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a hygiene report."""
        lines: list[str] = []
        lines.append(f"Hygiene substrate: {len(sensed)} artifact(s) sensed")
        lines.append("")

        # Group by kind
        deps = [s for s in sensed if s.get("kind") == "dep"]
        hooks = [s for s in sensed if s.get("kind") == "hook"]
        tests = [s for s in sensed if s.get("kind") == "tests"]
        python = [s for s in sensed if s.get("kind") == "python"]
        errs = [s for s in sensed if s.get("error")]

        if deps:
            lines.append(f"-- Dependencies ({len(deps)} upgradable) --")
            for d in deps:
                flag = " [MAJOR]" if d.get("major") else ""
                lines.append(f"  {d['package']}: {d['current']} -> {d['available']}{flag}")
        else:
            lines.append("-- Dependencies: all fresh --")

        if hooks:
            lines.append(f"\n-- Pre-commit hooks ({len(hooks)} outdated) --")
            for h in hooks:
                lines.append(f"  {h['repo']} -> {h['new_rev']}")
        else:
            lines.append("\n-- Pre-commit hooks: up to date --")

        if tests:
            t = tests[0]
            status = "healthy" if t.get("healthy") else "UNHEALTHY"
            lines.append(f"\n-- Tests: {status} --")
            lines.append(
                f"  {t.get('passed', 0)} passed, {t.get('failed', 0)} failed, {t.get('errors', 0)} errors"
            )

        if python:
            p = python[0]
            lines.append(f"\n-- Python: {p['current']} (requires {p['requires']}) --")

        if errs:
            lines.append("\n-- Errors --")
            for e in errs:
                lines.append(f"  {e.get('kind')}: {e['error']}")

        if acted:
            lines.append("\n-- Actions --")
            for action in acted:
                lines.append(f"  {action}")

        return "\n".join(lines)
