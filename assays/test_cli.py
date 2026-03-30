"""Integration tests — CLI end-to-end via Click test runner."""

from click.testing import CliRunner

from metabolon.pore import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.4.1" in result.output


def test_cli_init_creates_project(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init", "demo", "-d", "Demo MCP server"])
        assert result.exit_code == 0
        assert "Created demo/" in result.output

        from pathlib import Path

        assert (Path("demo") / "pyproject.toml").exists()
        assert (Path("demo") / "src" / "demo" / "server.py").exists()


def test_cli_add_tool_in_project(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Init project first
        runner.invoke(cli, ["init", "demo"])

        import os

        os.chdir("demo")

        # Add a tool
        result = runner.invoke(
            cli, ["add", "tool", "weather_fetch", "--description", "Fetch weather"]
        )
        assert result.exit_code == 0
        assert "weather.py" in result.output


def test_cli_check_passes_for_valid_project(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "demo"])

        import os

        os.chdir("demo")

        runner.invoke(cli, ["add", "tool", "weather_fetch"])

        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0
        assert "passed" in result.output.lower()


def test_cli_init_then_add_then_check_roundtrip(tmp_path):
    """Full roundtrip: init → add tool → add prompt → add resource → check."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Init
        result = runner.invoke(cli, ["init", "myapp"])
        assert result.exit_code == 0

        import os

        os.chdir("myapp")

        # Add components
        result = runner.invoke(cli, ["add", "tool", "data_fetch", "--description", "Fetch data"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["add", "prompt", "analyze", "--description", "Analyze data"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["add", "resource", "config", "--description", "App config"])
        assert result.exit_code == 0

        # Verify structure
        from pathlib import Path

        assert (Path("src/myapp/enzymes/data.py")).exists()
        assert (Path("src/myapp/codons/analyze.py")).exists()
        assert (Path("src/myapp/resources/config.py")).exists()

        # Check conventions
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0
