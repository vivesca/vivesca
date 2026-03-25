"""Tests for vivesca epigenome scaffold command.

Each test exercises one facet of the epigenome phenotype expression:
directory structure, template transcription, gitignore, and git init.
"""

import subprocess

import pytest


def test_epigenome_creates_directory(tmp_path):
    """Epigenome scaffold produces the expected top-level directory."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    result = scaffold_epigenome(tmp_path / "epigenome")
    assert result.exists()
    assert result.is_dir()


def test_epigenome_creates_compartments(tmp_path):
    """Scaffold lays down all three organelle compartments."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    assert (target / "credentials").is_dir()
    assert (target / "config").is_dir()
    assert (target / "launchd").is_dir()


def test_epigenome_transcribes_credential_template(tmp_path):
    """credentials/.env.template contains required env var names."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    env_tpl = target / "credentials" / ".env.template"
    assert env_tpl.exists()
    content = env_tpl.read_text()
    assert "ANTHROPIC_API_KEY" in content
    assert "OURA_TOKEN" in content


def test_epigenome_transcribes_server_config(tmp_path):
    """config/server.yaml contains host and port defaults."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    server_cfg = target / "config" / "server.yaml"
    assert server_cfg.exists()
    content = server_cfg.read_text()
    assert "host" in content
    assert "port" in content


def test_epigenome_transcribes_config_yaml(tmp_path):
    """config/config.yaml contains user and paths sections."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    cfg = target / "config" / "config.yaml"
    assert cfg.exists()
    content = cfg.read_text()
    assert "user" in content
    assert "paths" in content


def test_epigenome_transcribes_constitution(tmp_path):
    """genome.md is present and contains override comment."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    constitution = target / "genome.md"
    assert constitution.exists()
    content = constitution.read_text()
    assert "Override with your own rules" in content


def test_epigenome_transcribes_gitignore(tmp_path):
    """Gitignore ignores credentials and .env files."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    gitignore = target / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text()
    assert "credentials/*.key" in content
    assert ".env" in content


def test_epigenome_transcribes_readme(tmp_path):
    """README.md explains epigenome/genome relationship."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    readme = target / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "epigenome" in content.lower()
    assert "genome" in content.lower()


def test_epigenome_transcribes_launchd_readme(tmp_path):
    """launchd/README.md contains LaunchAgent usage guide."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    launchd_readme = target / "launchd" / "README.md"
    assert launchd_readme.exists()
    content = launchd_readme.read_text()
    assert "LaunchAgent" in content


def test_epigenome_initialises_git_repo(tmp_path):
    """Scaffold initialises a git repo with an initial commit."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    scaffold_epigenome(target)

    # .git directory must exist for a valid repo.
    assert (target / ".git").is_dir()

    # There should be exactly one commit.
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=target,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "epigenome" in lines[0]


def test_epigenome_refuses_non_empty_directory(tmp_path):
    """Scaffold refuses to overwrite a non-empty directory."""
    import click
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    target.mkdir()
    (target / "existing.txt").write_text("occupied")

    with pytest.raises(click.exceptions.ClickException):
        scaffold_epigenome(target)


def test_epigenome_returns_path(tmp_path):
    """scaffold_epigenome returns the target path."""
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = tmp_path / "epigenome"
    result = scaffold_epigenome(target)
    assert result == target


def test_epigenome_default_name_via_cli(tmp_path):
    """CLI command defaults to 'epigenome' when no name given."""
    from click.testing import CliRunner
    from metabolon.pore import cli

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["epigenome"])

    assert result.exit_code == 0
    assert "Epigenome created" in result.output


def test_epigenome_custom_name_via_cli(tmp_path):
    """CLI command accepts a custom name argument."""
    from click.testing import CliRunner
    from metabolon.pore import cli

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["epigenome", "my-instance"])

    assert result.exit_code == 0
    assert "my-instance" in result.output
