from pathlib import Path

import pytest
from click.testing import CliRunner

from epsin.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "fetch" in result.output
    assert "sources" in result.output


def test_fetch_help():
    runner = CliRunner()
    result = runner.invoke(main, ["fetch", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--tag" in result.output
    assert "--since" in result.output
    assert "--full" in result.output


def test_sources_list():
    runner = CliRunner()
    result = runner.invoke(main, ["sources", "list"])
    assert result.exit_code == 0
    assert "Simon Willison" in result.output


def test_sources_list_with_config(tmp_path: Path):
    import yaml
    config = tmp_path / "sources.yaml"
    config.write_text(yaml.dump({
        "sources": [
            {"name": "Test Source", "url": "https://test.com/", "tags": ["test"]}
        ]
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config), "sources", "list"])
    assert result.exit_code == 0
    assert "Test Source" in result.output


def test_fetch_with_invalid_since():
    runner = CliRunner()
    result = runner.invoke(main, ["fetch", "--since", "not-a-date"])
    assert result.exit_code == 1
    assert "Invalid" in result.output


def test_sources_add_not_implemented():
    runner = CliRunner()
    result = runner.invoke(main, ["sources", "add", "https://example.com/"])
    assert result.exit_code == 1