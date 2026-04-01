#!/usr/bin/env python3
"""Tests for effectors/golem-health — golem provider health check."""

import json
import subprocess
import sys
import types
from pathlib import Path
from unittest import mock

import pytest

GOLEM_HEALTH_PATH = Path(__file__).resolve().parents[1] / "effectors" / "golem-health"


def _load_module():
    """Load golem-health effector into a module object via exec()."""
    ns: dict = {"__name__": "golem_health", "__file__": str(GOLEM_HEALTH_PATH)}
    exec(GOLEM_HEALTH_PATH.read_text(), ns)
    mod = types.SimpleNamespace(**ns)
    return mod


# ── Script structure tests ────────────────────────────────────────────────────


class TestGolemHealthScript:
    def test_script_exists(self):
        """Test golem-health script exists."""
        assert GOLEM_HEALTH_PATH.exists()

    def test_script_is_executable(self):
        """Test golem-health script is executable."""
        assert GOLEM_HEALTH_PATH.stat().st_mode & 0o111

    def test_script_has_shebang(self):
        """Test golem-health script has Python shebang."""
        first_line = GOLEM_HEALTH_PATH.read_text().splitlines()[0]
        assert "python" in first_line.lower()


# ── Argument parsing tests ────────────────────────────────────────────────────


class TestArgumentParsing:
    def test_help_runs(self):
        """Test --help runs without error."""
        result = subprocess.run(
            [sys.executable, str(GOLEM_HEALTH_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "provider" in result.stdout.lower()

    def test_invalid_provider_fails(self):
        """Test invalid provider name is rejected."""
        result = subprocess.run(
            [sys.executable, str(GOLEM_HEALTH_PATH), "--provider", "invalid"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "choice" in result.stderr.lower()


# ─── Module import and function tests ────────────────────────────────────────────


class TestSourceEnvFile:
    """Test the source_env_file function."""

    def test_source_env_file_missing(self, tmp_path):
        """Test sourcing a non-existent file returns empty dict."""
        module = _load_module()

        result = module.source_env_file(tmp_path / "nonexistent.env")
        assert result == {}

    def test_source_env_file_basic(self, tmp_path):
        """Test sourcing a basic env file."""
        module = _load_module()

        env_file = tmp_path / "test.env"
        env_file.write_text("export TEST_VAR=hello\nexport ANOTHER_VAR=world\n")

        result = module.source_env_file(env_file)
        assert result.get("TEST_VAR") == "hello"
        assert result.get("ANOTHER_VAR") == "world"


class TestHealthResult:
    """Test the HealthResult dataclass."""

    def test_health_result_creation(self):
        """Test HealthResult can be created."""
        module = _load_module()

        result = module.HealthResult(
            provider="test",
            status="OK",
            latency_ms=100,
            model="test-model",
            exit_code=0,
            has_output=True,
        )
        assert result.provider == "test"
        assert result.status == "OK"
        assert result.latency_ms == 100
        assert result.model == "test-model"
        assert result.error is None


class TestCheckProvider:
    """Test the check_provider function with mocked subprocess."""

    def test_check_provider_unknown(self):
        """Test check_provider with unknown provider name."""
        module = _load_module()

        result = module.check_provider(
            provider="unknown",
            env={},
            golem_path=Path("/fake/golem"),
        )
        assert result.status == "ERROR"
        assert "Unknown provider" in (result.error or "")

    def test_check_provider_missing_key(self):
        """Test check_provider when API key is missing."""
        module = _load_module()

        result = module.check_provider(
            provider="zhipu",
            env={},  # No ZHIPU_API_KEY
            golem_path=Path("/fake/golem"),
        )
        assert result.status == "FAIL"
        assert "ZHIPU_API_KEY" in (result.error or "")

    @mock.patch("subprocess.run")
    def test_check_provider_success(self, mock_run):
        """Test check_provider with successful golem run."""
        import importlib.util

        # Mock successful subprocess run
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout="Hello! I'm ready to help.",
            stderr="",
        )

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.check_provider(
            provider="zhipu",
            env={"ZHIPU_API_KEY": "test-key"},
            golem_path=Path("/fake/golem"),
        )
        assert result.status == "OK"
        assert result.exit_code == 0
        assert result.has_output is True

    @mock.patch("subprocess.run")
    def test_check_provider_failure(self, mock_run):
        """Test check_provider when golem fails."""
        import importlib.util

        # Mock failed subprocess run
        mock_run.return_value = mock.Mock(
            returncode=1,
            stdout="",
            stderr="API error",
        )

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.check_provider(
            provider="zhipu",
            env={"ZHIPU_API_KEY": "test-key"},
            golem_path=Path("/fake/golem"),
        )
        assert result.status == "FAIL"
        assert result.exit_code == 1

    @mock.patch("subprocess.run")
    def test_check_provider_timeout(self, mock_run):
        """Test check_provider when golem times out."""
        import importlib.util

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="golem", timeout=60)

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.check_provider(
            provider="zhipu",
            env={"ZHIPU_API_KEY": "test-key"},
            golem_path=Path("/fake/golem"),
        )
        assert result.status == "FAIL"
        assert "timeout" in (result.error or "").lower()


class TestOutputFormatting:
    """Test output formatting functions."""

    def test_print_table(self, capsys):
        """Test print_table outputs expected format."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        results = [
            module.HealthResult(
                provider="zhipu",
                status="OK",
                latency_ms=150,
                model="GLM-5.1",
                exit_code=0,
                has_output=True,
            ),
            module.HealthResult(
                provider="volcano",
                status="FAIL",
                latency_ms=0,
                model="ark-code-latest",
                exit_code=1,
                has_output=False,
                error="API error",
            ),
        ]
        module.print_table(results)
        captured = capsys.readouterr()
        assert "zhipu" in captured.out
        assert "OK" in captured.out
        assert "volcano" in captured.out
        assert "FAIL" in captured.out
        assert "GLM-5.1" in captured.out
        assert "ark-code-latest" in captured.out

    def test_print_json(self, capsys):
        """Test print_json outputs valid JSON."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        results = [
            module.HealthResult(
                provider="zhipu",
                status="OK",
                latency_ms=150,
                model="GLM-5.1",
                exit_code=0,
                has_output=True,
            ),
        ]
        module.print_json(results)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["provider"] == "zhipu"
        assert data[0]["status"] == "OK"
        assert data[0]["latency_ms"] == 150


class TestProviderConfig:
    """Test provider configuration."""

    def test_all_providers_have_model(self):
        """Test all providers have model defined."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for provider, config in module.PROVIDERS.items():
            assert "model" in config
            assert config["model"], f"Provider {provider} missing model"

    def test_all_providers_have_key_var(self):
        """Test all providers have key_var defined."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for provider, config in module.PROVIDERS.items():
            assert "key_var" in config
            assert config["key_var"], f"Provider {provider} missing key_var"

    def test_expected_providers_exist(self):
        """Test expected providers are configured."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        expected = {"zhipu", "infini", "volcano"}
        assert set(module.PROVIDERS.keys()) == expected


class TestMainFunction:
    """Test the main function."""

    @mock.patch("subprocess.run")
    def test_main_returns_zero_on_success(self, mock_run):
        """Test main returns 0 when all providers succeed."""
        import importlib.util

        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout="Hello!",
            stderr="",
        )

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Mock the golem path check
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.object(Path, "__truediv__", return_value=Path("/fake/golem")):
                # Patch source_env_file to return keys
                with mock.patch.object(module, "source_env_file", return_value={
                    "ZHIPU_API_KEY": "key",
                    "INFINI_API_KEY": "key",
                    "VOLCANO_API_KEY": "key",
                }):
                    exit_code = module.main(["--provider", "zhipu", "--json"])
        assert exit_code == 0

    @mock.patch("subprocess.run")
    def test_main_returns_one_on_failure(self, mock_run):
        """Test main returns 1 when provider fails."""
        import importlib.util

        mock_run.return_value = mock.Mock(
            returncode=1,
            stdout="",
            stderr="Error",
        )

        spec = importlib.util.spec_from_file_location("golem_health", GOLEM_HEALTH_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.object(module, "source_env_file", return_value={
                "ZHIPU_API_KEY": "key",
            }):
                exit_code = module.main(["--provider", "zhipu", "--json"])
        assert exit_code == 1
