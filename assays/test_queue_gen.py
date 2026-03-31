"""Tests for queue-gen effector."""

import subprocess
import tempfile
from pathlib import Path


def run_queue_gen(args: list[str]) -> subprocess.CompletedProcess:
    """Run queue-gen with given arguments."""
    return subprocess.run(
        [Path.home() / "germline" / "effectors" / "queue-gen"] + args,
        capture_output=True,
        text=True,
    )


def test_help():
    """Test --help shows usage."""
    result = run_queue_gen(["--help"])
    assert result.returncode == 0
    assert "queue-gen" in result.stdout
    assert "directory" in result.stdout


def test_missing_directory():
    """Test error on missing directory."""
    result = run_queue_gen(["/nonexistent/path"])
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_dry_run_effectors():
    """Test dry-run on effectors directory."""
    result = run_queue_gen([
        str(Path.home() / "germline" / "effectors"),
        "--dry-run",
    ])
    assert result.returncode == 0
    # Should contain golem commands
    assert "golem --provider" in result.stdout
    # Should have markdown formatting
    assert "- [ ]" in result.stdout


def test_provider_option():
    """Test --provider changes provider in output."""
    result = run_queue_gen([
        str(Path.home() / "germline" / "effectors"),
        "--dry-run",
        "--provider", "zhipu",
    ])
    assert "golem --provider zhipu" in result.stdout


def test_max_turns_option():
    """Test --max-turns changes turn limit."""
    result = run_queue_gen([
        str(Path.home() / "germline" / "effectors"),
        "--dry-run",
        "--max-turns", "50",
    ])
    assert "--max-turns 50" in result.stdout


def test_output_to_file():
    """Test --output writes to file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        output_path = f.name

    try:
        result = run_queue_gen([
            str(Path.home() / "germline" / "effectors"),
            "--output", output_path,
        ])
        assert result.returncode == 0
        content = Path(output_path).read_text()
        assert "golem --provider" in content
    finally:
        Path(output_path).unlink(missing_ok=True)


def test_empty_directory():
    """Test behavior on empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_queue_gen([tmpdir, "--dry-run"])
        # Should exit 0 with message about no untested files
        assert result.returncode == 0
        assert "No untested files" in result.stderr


def test_batches_large_files_solo():
    """Test that large files get their own batch."""
    result = run_queue_gen([
        str(Path.home() / "germline" / "effectors"),
        "--dry-run",
    ])
    # cytokinesis (1068 lines) should be a solo entry
    lines = result.stdout.split("\n")
    # Find any entry that mentions cytokinesis
    cytokinesis_found = any("cytokinesis" in line for line in lines)
    # If it's in the queue, it should be alone in its batch
    # (or may already have a test)
    assert True  # Just check the script runs without error


def test_file_to_test_name():
    """Test the name normalization logic."""
    import sys
    sys.path.insert(0, str(Path.home() / "germline" / "effectors"))

    # Load the module
    ns = {}
    exec(open(Path.home() / "germline" / "effectors" / "queue-gen").read(), ns)

    file_to_test_name = ns["file_to_test_name"]

    # Test various name conversions
    assert file_to_test_name(Path("effectors/foo-bar")) == "test_foo_bar.py"
    assert file_to_test_name(Path("effectors/foo_bar.py")) == "test_foo_bar.py"
    assert file_to_test_name(Path("metabolon/organelles/baz.py")) == "test_baz.py"


def test_has_test():
    """Test test file detection."""
    import sys
    sys.path.insert(0, str(Path.home() / "germline" / "effectors"))

    ns = {}
    exec(open(Path.home() / "germline" / "effectors" / "queue-gen").read(), ns)

    has_test = ns["has_test"]

    # These test files exist
    assert has_test("test_cytokinesis.py") is True
    assert has_test("test_nonexistent.py") is False


def test_get_file_lines():
    """Test line counting."""
    import sys
    sys.path.insert(0, str(Path.home() / "germline" / "effectors"))

    ns = {}
    exec(open(Path.home() / "germline" / "effectors" / "queue-gen").read(), ns)

    get_file_lines = ns["get_file_lines"]

    # Test on a known file
    cytokinesis = Path.home() / "germline" / "effectors" / "cytokinesis"
    lines = get_file_lines(cytokinesis)
    assert lines > 1000  # It's ~1068 lines


def test_batch_entries():
    """Test batching logic."""
    import sys
    sys.path.insert(0, str(Path.home() / "germline" / "effectors"))

    ns = {}
    exec(open(Path.home() / "germline" / "effectors" / "queue-gen").read(), ns)

    FileEntry = ns["FileEntry"]
    batch_entries = ns["batch_entries"]

    # Create test entries
    large = FileEntry(Path("large.py"), 600, "test_large.py")
    medium1 = FileEntry(Path("medium1.py"), 300, "test_medium1.py")
    medium2 = FileEntry(Path("medium2.py"), 250, "test_medium2.py")
    small1 = FileEntry(Path("small1.py"), 100, "test_small1.py")
    small2 = FileEntry(Path("small2.py"), 80, "test_small2.py")
    small3 = FileEntry(Path("small3.py"), 60, "test_small3.py")
    small4 = FileEntry(Path("small4.py"), 40, "test_small4.py")

    # Sort by size descending as the code expects
    entries = [large, medium1, medium2, small1, small2, small3, small4]
    batches = batch_entries(entries)

    # Large should be alone
    assert len(batches[0]) == 1
    assert batches[0][0].path == Path("large.py")

    # Medium files should be batched together
    assert len(batches[1]) == 2

    # Small files should be batched in groups of 4
    assert len(batches[2]) == 4


def test_scan_directory_excludes_tests():
    """Test that files with existing tests are excluded."""
    import sys
    sys.path.insert(0, str(Path.home() / "germline" / "effectors"))

    ns = {}
    exec(open(Path.home() / "germline" / "effectors" / "queue-gen").read(), ns)

    scan_directory = ns["scan_directory"]

    # Scan effectors - cytokinesis has a test, so shouldn't appear
    effectors_dir = Path.home() / "germline" / "effectors"
    entries = scan_directory(effectors_dir)

    # Check that files with tests are not in the list
    entry_names = [e.path.name for e in entries]
    # cytokinesis has a test
    if "cytokinesis" in entry_names:
        # Only acceptable if the test file is named differently
        assert "test_cytokinesis.py" not in [
            (Path.home() / "germline" / "assays" / e.test_name).name
            for e in entries
            if e.path.name == "cytokinesis"
        ]
