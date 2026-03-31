"""preflight — pre-operation health validator.

Runs quick deterministic checks before expensive operations.
Returns a PreflightResult with pass/fail and details.
Fails fast on critical issues, warns on degraded state.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
SIGNAL_BUS = HOME / ".local" / "share" / "vivesca" / "signals.jsonl"
INFECTION_LOG = HOME / ".local" / "share" / "vivesca" / "infections.jsonl"
GERMLINE = HOME / "germline"
EPIGENOME = HOME / "epigenome"
GOLEM_LOG = HOME / ".local" / "share" / "vivesca" / "golem.jsonl"

MAX_REPO_AGE_HOURS = 4
MAX_SIGNAL_BUS_AGE_HOURS = 12
MAX_GOLEM_LOG_AGE_HOURS = 24

# Provider config: env var name, base URL (for health check), model for ping
PROVIDER_CONFIG = {
    "zhipu": {"key_var": "ZHIPU_API_KEY", "base_url": "https://open.bigmodel.cn/api/paas/v4/models"},
    "volcano": {"key_var": "VOLCANO_API_KEY", "base_url": "https://ark.cn-beijing.volces.com/api/v3/models"},
    "anthropic": {"key_var": "ANTHROPIC_API_KEY", "base_url": "https://api.anthropic.com/v1/models"},
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, critical


@dataclass
class PreflightResult:
    checks: list[CheckResult] = field(default_factory=list)
    passed: bool = True
    critical_failures: int = 0
    warnings: int = 0

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)
        if not check.passed:
            if check.severity == "critical":
                self.critical_failures += 1
                self.passed = False
            else:
                self.warnings += 1

    def summary(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        lines = [f"Preflight: {passed}/{total} passed"]
        for c in self.checks:
            status = "OK" if c.passed else ("CRITICAL" if c.severity == "critical" else "WARN")
            lines.append(f"  [{status}] {c.name}: {c.message}")
        return "\n".join(lines)


def check_repo_reachable(path: Path, name: str) -> CheckResult:
    """Check that a git repo exists and is reachable."""
    if not path.exists():
        return CheckResult(name=f"{name}_reachable", passed=False, message=f"{path} not found", severity="critical")
    git_dir = path / ".git"
    if not git_dir.exists():
        return CheckResult(name=f"{name}_reachable", passed=False, message=f"{path} is not a git repo", severity="critical")
    return CheckResult(name=f"{name}_reachable", passed=True, message="OK")


def check_repo_freshness(path: Path, name: str, max_hours: float = MAX_REPO_AGE_HOURS) -> CheckResult:
    """Check that repo has been pulled/committed recently."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=5,
            cwd=str(path),
        )
        if result.returncode != 0:
            return CheckResult(name=f"{name}_fresh", passed=False, message="git log failed", severity="warning")
        ts = int(result.stdout.strip())
        age_hours = (time.time() - ts) / 3600
        if age_hours > max_hours:
            return CheckResult(
                name=f"{name}_fresh", passed=False,
                message=f"Last commit {age_hours:.1f}h ago (max {max_hours}h)",
                severity="warning",
            )
        return CheckResult(name=f"{name}_fresh", passed=True, message=f"{age_hours:.1f}h since last commit")
    except Exception as e:
        return CheckResult(name=f"{name}_fresh", passed=False, message=str(e), severity="warning")


def check_signal_bus() -> CheckResult:
    """Check signal bus file exists and is writable."""
    if not SIGNAL_BUS.exists():
        return CheckResult(name="signal_bus", passed=False, message="Signal bus file missing", severity="warning")
    if not os.access(SIGNAL_BUS, os.W_OK):
        return CheckResult(name="signal_bus", passed=False, message="Signal bus not writable", severity="critical")
    age_hours = (time.time() - SIGNAL_BUS.stat().st_mtime) / 3600
    if age_hours > MAX_SIGNAL_BUS_AGE_HOURS:
        return CheckResult(name="signal_bus", passed=False, message=f"Signal bus stale ({age_hours:.1f}h)", severity="warning")
    return CheckResult(name="signal_bus", passed=True, message="OK")


def check_api_key(env_var: str) -> CheckResult:
    """Check that an API key environment variable is set and non-empty."""
    val = os.environ.get(env_var, "")
    if not val:
        return CheckResult(name=f"api_key_{env_var}", passed=False, message=f"${env_var} not set", severity="warning")
    if len(val) < 10:
        return CheckResult(name=f"api_key_{env_var}", passed=False, message=f"${env_var} suspiciously short", severity="warning")
    return CheckResult(name=f"api_key_{env_var}", passed=True, message="Set")


def run_preflight(api_keys: list[str] | None = None) -> PreflightResult:
    """Run all preflight checks.

    Args:
        api_keys: List of env var names to check. Defaults to common ones.
    """
    if api_keys is None:
        api_keys = ["ZHIPU_API_KEY", "ANTHROPIC_API_KEY"]

    result = PreflightResult()

    # Repo checks
    result.add(check_repo_reachable(GERMLINE, "germline"))
    result.add(check_repo_reachable(EPIGENOME, "epigenome"))
    result.add(check_repo_freshness(GERMLINE, "germline"))
    result.add(check_repo_freshness(EPIGENOME, "epigenome"))

    # Signal bus
    result.add(check_signal_bus())

    # API keys
    for key in api_keys:
        result.add(check_api_key(key))

    return result


def check_golem_binary() -> CheckResult:
    """Check that the golem binary exists and is executable."""
    golem_path = shutil.which("golem")
    if golem_path is None:
        # Check default location
        default_path = HOME / "germline" / "effectors" / "golem"
        if default_path.exists():
            if os.access(default_path, os.X_OK):
                return CheckResult(name="golem_binary", passed=True, message=f"Found at {default_path}")
            return CheckResult(name="golem_binary", passed=False, message="Golem not executable", severity="critical")
        return CheckResult(name="golem_binary", passed=False, message="Golem binary not found", severity="critical")
    return CheckResult(name="golem_binary", passed=True, message=f"Found at {golem_path}")


def check_golem_api_key(provider: str = "zhipu") -> CheckResult:
    """Check that the API key for the specified provider is set."""
    config = PROVIDER_CONFIG.get(provider)
    if config is None:
        return CheckResult(
            name=f"golem_api_key_{provider}",
            passed=False,
            message=f"Unknown provider: {provider}",
            severity="warning",
        )
    return check_api_key(config["key_var"])


def check_provider_health(provider: str = "zhipu", timeout: float = 5.0) -> CheckResult:
    """Check provider API health by hitting the models endpoint.

    This is a lightweight check that doesn't make actual LLM calls.
    Returns warning on failure (degraded but usable).
    """
    import urllib.request
    import urllib.error

    config = PROVIDER_CONFIG.get(provider)
    if config is None:
        return CheckResult(
            name=f"provider_health_{provider}",
            passed=False,
            message=f"Unknown provider: {provider}",
            severity="warning",
        )

    key = os.environ.get(config["key_var"], "")
    if not key:
        return CheckResult(
            name=f"provider_health_{provider}",
            passed=False,
            message=f"No API key for {provider}",
            severity="warning",
        )

    try:
        req = urllib.request.Request(
            config["base_url"],
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return CheckResult(name=f"provider_health_{provider}", passed=True, message="API reachable")
            return CheckResult(
                name=f"provider_health_{provider}",
                passed=False,
                message=f"API returned status {response.status}",
                severity="warning",
            )
    except urllib.error.URLError as e:
        return CheckResult(
            name=f"provider_health_{provider}",
            passed=False,
            message=f"Network error: {e.reason}",
            severity="warning",
        )
    except TimeoutError:
        return CheckResult(
            name=f"provider_health_{provider}",
            passed=False,
            message="API timeout",
            severity="warning",
        )
    except Exception as e:
        return CheckResult(
            name=f"provider_health_{provider}",
            passed=False,
            message=str(e),
            severity="warning",
        )


def check_golem_log_freshness(max_hours: float = MAX_GOLEM_LOG_AGE_HOURS) -> CheckResult:
    """Check that golem has been used recently (log file freshness)."""
    if not GOLEM_LOG.exists():
        return CheckResult(
            name="golem_log_freshness",
            passed=False,
            message="No golem log found",
            severity="info",
        )
    age_hours = (time.time() - GOLEM_LOG.stat().st_mtime) / 3600
    if age_hours > max_hours:
        return CheckResult(
            name="golem_log_freshness",
            passed=False,
            message=f"Golem last used {age_hours:.1f}h ago",
            severity="info",
        )
    return CheckResult(name="golem_log_freshness", passed=True, message=f"Last used {age_hours:.1f}h ago")


def check_golem_ready(provider: str = "zhipu", skip_health_check: bool = False) -> PreflightResult:
    """Comprehensive golem readiness check.

    Verifies:
    1. Golem binary exists and is executable
    2. API key for the provider is set
    3. Provider API is reachable (optional, can be slow)
    4. Golem has been used recently (info only)

    Args:
        provider: Provider to check (zhipu, volcano, anthropic)
        skip_health_check: Skip network health check (useful for offline mode)

    Returns:
        PreflightResult with all checks.
    """
    result = PreflightResult()

    result.add(check_golem_binary())
    result.add(check_golem_api_key(provider))

    if not skip_health_check:
        result.add(check_provider_health(provider))

    result.add(check_golem_log_freshness())

    return result
