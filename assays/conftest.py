from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml


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
    import tempfile

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
                for child in path.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                continue
            shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass
