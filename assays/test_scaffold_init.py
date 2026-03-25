"""Tests for vivesca init command."""


def test_init_creates_project_directory(tmp_path):
    from metabolon.gastrulation.init import scaffold_project

    scaffold_project("myserver", target=tmp_path / "myserver", description="Test server")
    project_dir = tmp_path / "myserver"

    assert project_dir.exists()
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "src" / "myserver" / "server.py").exists()
    assert (project_dir / "src" / "myserver" / "__init__.py").exists()
    assert (project_dir / "src" / "myserver" / "__main__.py").exists()
    assert (project_dir / "assays" / "test_handshake.py").exists()


def test_init_creates_component_dirs(tmp_path):
    from metabolon.gastrulation.init import scaffold_project

    scaffold_project("myserver", target=tmp_path / "myserver", description="Test server")
    src = tmp_path / "myserver" / "src" / "myserver"

    assert (src / "tools").is_dir()
    assert (src / "codons").is_dir()
    assert (src / "resources").is_dir()
    assert (src / "morphology").is_dir()


def test_init_pyproject_contains_name(tmp_path):
    from metabolon.gastrulation.init import scaffold_project

    scaffold_project("myserver", target=tmp_path / "myserver", description="Test server")
    content = (tmp_path / "myserver" / "pyproject.toml").read_text()

    assert 'name = "myserver"' in content
    assert "fastmcp" in content
    assert "vivesca" in content


def test_init_server_contains_name(tmp_path):
    from metabolon.gastrulation.init import scaffold_project

    scaffold_project("myserver", target=tmp_path / "myserver", description="Test server")
    content = (tmp_path / "myserver" / "src" / "myserver" / "server.py").read_text()

    assert '"myserver"' in content
    assert "FastMCP" in content
    assert "FileSystemProvider" in content


def test_init_handles_hyphenated_name(tmp_path):
    from metabolon.gastrulation.init import scaffold_project

    scaffold_project("my-server", target=tmp_path / "my-server", description="Test")
    src = tmp_path / "my-server" / "src" / "my_server"

    assert src.exists()
    assert (src / "server.py").exists()

    content = (tmp_path / "my-server" / "pyproject.toml").read_text()
    assert 'name = "my-server"' in content
    assert 'packages = ["src/my_server"]' in content


def test_init_refuses_existing_directory(tmp_path):
    import click
    import pytest

    from metabolon.gastrulation.init import scaffold_project

    target = tmp_path / "existing"
    target.mkdir()
    (target / "somefile.txt").write_text("existing content")

    with pytest.raises(click.exceptions.ClickException):
        scaffold_project("existing", target=target, description="Test")
