from __future__ import annotations

import importlib.util
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml


# Allow pytest to collect test files with dots in the name (e.g. test_foo.sh.py).
# The dot makes Python's importer treat "test_foo" as a package, causing
# ModuleNotFoundError.  We use a custom Module subclass that loads via
# importlib.util.spec_from_file_location, bypassing the broken import path.


class _DottedNameModule(pytest.Module):
    """Module collector that loads .sh.py (and other dotted-name) test files
    via importlib.util, skipping the broken package-resolution import."""

    def _getobj(self):
        safe_name = self.path.name.replace(".", "_").removesuffix("_py")
        print(f"[DottedNameModule._getobj] {safe_name} from {self.path}", flush=True)
        if safe_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(safe_name, str(self.path))
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create import spec for {self.path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[safe_name] = mod
            spec.loader.exec_module(mod)
        return sys.modules[safe_name]


def pytest_collect_file(file_path: Path, parent):
    if file_path.suffixes != [".sh", ".py"] or not file_path.name.startswith("test_"):
        return None
    node = _DottedNameModule.from_parent(parent, path=file_path)
    print(f"[conftest] created {type(node).__name__} for {file_path}", flush=True)
    return node


@pytest.fixture
def xdg_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    config_home = tmp_path / "config"
    cache_home = tmp_path / "cache"
    data_home = tmp_path / "data"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.delenv("ENDOCYTOSIS_CONFIG_DIR", raising=False)
    monkeypatch.delenv("ENDOCYTOSIS_CACHE_DIR", raising=False)
    monkeypatch.delenv("ENDOCYTOSIS_DATA_DIR", raising=False)
    return config_home, cache_home, data_home


@pytest.fixture
def sample_state():
    now = datetime.now(UTC)
    return {
        "Source A": (now - timedelta(days=2)).isoformat(),
        "Source B": (now - timedelta(hours=12)).isoformat(),
    }


@pytest.fixture
def sample_sources():
    return {
        "web_sources": [
            {
                "name": "Test Feed",
                "tier": 1,
                "cadence": "daily",
                "rss": "https://example.com/feed.xml",
                "url": "https://example.com",
            }
        ]
    }


@pytest.fixture
def write_sources_file(xdg_env, sample_sources):
    config_home, _, _ = xdg_env
    target = config_home / "endocytosis" / "sources.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(sample_sources), encoding="utf-8")
    return target


@pytest.fixture
def home_dir():
    """Return the user's home directory as a Path (no hardcoded paths in tests)."""
    return Path.home()


@pytest.fixture
def germline_dir(home_dir):
    """Return the germline project root as a Path."""
    return home_dir / "germline"


@pytest.fixture
def effectors_dir(germline_dir):
    """Return the effectors directory as a Path."""
    return germline_dir / "effectors"


@pytest.fixture(scope="session", autouse=True)
def clean_pytest_temp_dirs(pytestconfig: pytest.Config):
    """Remove leftover pytest temporary directories before test session starts.

    This prevents FileExistsError when pytest's tmp_path fixture tries to create
    a directory that already exists and is non-empty.
    """
    import os
    import stat
    import tempfile

    def _force_rmtree(path: Path) -> None:
        """Remove a directory tree, handling permission errors on readonly files."""
        import errno

        def handle_error(func, exc_path, exc_info):
            """Error handler for shutil.rmtree that fixes permissions and retries."""
            if exc_path and os.path.isdir(exc_path):
                os.chmod(exc_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            elif exc_path and os.path.isfile(exc_path):
                os.chmod(exc_path, stat.S_IWRITE | stat.S_IREAD)

        # Use shutil.rmtree with error handler for robust removal
        try:
            shutil.rmtree(path, onerror=handle_error)
        except OSError:
            # Fallback: walk and force-remove
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for name in filenames:
                    f = os.path.join(dirpath, name)
                    try:
                        os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
                        os.unlink(f)
                    except OSError:
                        pass
                for name in dirnames:
                    d = os.path.join(dirpath, name)
                    try:
                        if os.path.islink(d):
                            os.unlink(d)
                        else:
                            os.chmod(d, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                            os.rmdir(d)
                    except OSError:
                        pass
            try:
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.rmdir(path)
            except OSError:
                pass

    tmpdir = Path(tempfile.gettempdir())
    basetemp = pytestconfig.option.basetemp
    active_basetemp = Path(basetemp) if basetemp else None
    temp_paths = list(tmpdir.glob("pytest-*"))
    if active_basetemp is not None:
        temp_paths.append(active_basetemp)
    for path in temp_paths:
        if not path.is_dir():
            continue
        try:
            if active_basetemp is not None and path == active_basetemp:
                for child in list(path.iterdir()):
                    if child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        _force_rmtree(child)
                    else:
                        child.unlink(missing_ok=True)
                continue
            _force_rmtree(path)
        except OSError:
            pass
