from __future__ import annotations

import json
from types import SimpleNamespace

import yaml

from metabolon.organelles.endocytosis_rss.config import restore_config
from metabolon.organelles.endocytosis_rss.discover import _compile_keywords, has_affinity, scout_sources


def _write_sources_with_discovery(config_home):
    sources_path = config_home / "lustro" / "sources.yaml"
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    sources_path.write_text(
        yaml.safe_dump(
            {
                "x_accounts": [
                    {"handle": "@alice", "name": "Alice", "tier": 1},
                ],
                "x_discovery": {
                    "count": 5,
                    "keywords": [r"\bAI\b", r"\bagent"],
                },
            }
        ),
        encoding="utf-8",
    )


def test_keyword_matching():
    keywords = _compile_keywords([r"\bAI\b", r"\bagent"])
    assert has_affinity("This AI launch is huge", keywords) is True
    assert has_affinity("Nothing relevant here", keywords) is False


def test_scout_sources_filters_tracked_handles_and_formats_output(monkeypatch, xdg_env, capsys):
    config_home, _, _ = xdg_env
    _write_sources_with_discovery(config_home)
    cfg = restore_config()

    tweets = [
        {
            "author": {"handle": "bob"},
            "text": "AI agents are shipping fast",
            "created_at": "2026-02-24T10:00:00Z",
        },
        {
            "author": {"handle": "alice"},
            "text": "AI update from tracked account",
            "created_at": "2026-02-24T11:00:00Z",
        },
        {
            "author": {"handle": "charlie"},
            "text": "Completely unrelated sports thread",
            "created_at": "2026-02-24T12:00:00Z",
        },
        {
            "author": {"handle": "bob"},
            "text": "Another agent workflow post",
            "created_at": "2026-02-24T13:00:00Z",
        },
    ]

    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.discover.shutil.which", lambda _name: "/usr/local/bin/bird")
    monkeypatch.setattr(
        "metabolon.organelles.endocytosis_rss.discover.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(tweets),
            stderr="",
        ),
    )

    exit_code = scout_sources(cfg, count=None)

    assert exit_code == 0
    stderr = capsys.readouterr().err
    assert "X Discovery: scanned 4 tweets, 3 matched keywords" in stderr
    assert "@bob (2 matches)" in stderr
    assert "@alice" not in stderr

    log_text = cfg.log_path.read_text(encoding="utf-8")
    assert "### X Discovery (For You)" in log_text
    assert "@bob (2 matches)" in log_text


def test_cmd_discover_uses_count_override(monkeypatch, xdg_env):
    config_home, _, _ = xdg_env
    _write_sources_with_discovery(config_home)
    called = {}
    cfg = restore_config()

    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.discover.shutil.which", lambda _name: "/usr/local/bin/bird")

    def fake_run(cmd, **_kwargs):
        called["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.discover.subprocess.run", fake_run)
    exit_code = scout_sources(cfg, count=20)

    assert exit_code == 0
    assert called["cmd"][:4] == ["/usr/local/bin/bird", "home", "-n", "20"]
