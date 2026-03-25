def test_restore_fork_registry(tmp_path):
    """Registry YAML maps suite names to local and cache paths."""
    from metabolon.tools.mutation_sense import restore_fork_registry

    registry_file = tmp_path / "skill-forks.yaml"
    registry_file.write_text(
        "superpowers:\n"
        "  local: /Users/terry/skills/superpowers\n"
        "  cache: /Users/terry/.claude/plugins/cache/claude-plugins-official/superpowers\n"
        "compound-engineering:\n"
        "  local: /Users/terry/skills/compound-engineering\n"
        "  cache: /Users/terry/.claude/plugins/cache/every-marketplace/compound-engineering\n"
    )

    registry = restore_fork_registry(registry_file)
    assert len(registry) == 2
    assert registry["superpowers"]["local"] == "/Users/terry/skills/superpowers"


def test_find_latest_cache_version(tmp_path):
    """Finds the latest semver directory in cache."""
    from metabolon.tools.mutation_sense import find_latest_cache_version

    cache_dir = tmp_path / "superpowers"
    (cache_dir / "5.0.2" / "skills").mkdir(parents=True)
    (cache_dir / "5.0.5" / "skills").mkdir(parents=True)
    (cache_dir / "5.0.4" / "skills").mkdir(parents=True)
    # Non-semver dirs should be ignored
    (cache_dir / "abc123").mkdir(parents=True)

    result = find_latest_cache_version(cache_dir)
    assert result is not None
    assert "5.0.5" in str(result)


def test_diff_fork(tmp_path):
    """Diffs local fork against cache, reports changed files."""
    from metabolon.tools.mutation_sense import diff_fork

    local = tmp_path / "local"
    cache = tmp_path / "cache"

    # Same file
    (local / "skill-a").mkdir(parents=True)
    (cache / "skill-a").mkdir(parents=True)
    (local / "skill-a" / "SKILL.md").write_text("original content")
    (cache / "skill-a" / "SKILL.md").write_text("original content")

    # Modified upstream
    (local / "skill-b").mkdir(parents=True)
    (cache / "skill-b").mkdir(parents=True)
    (local / "skill-b" / "SKILL.md").write_text("old version")
    (cache / "skill-b" / "SKILL.md").write_text("new version with improvements")

    # New skill upstream
    (cache / "skill-c").mkdir(parents=True)
    (cache / "skill-c" / "SKILL.md").write_text("brand new skill")

    result = diff_fork(local, cache)
    assert result["modified"] == ["skill-b/SKILL.md"]
    assert result["added_upstream"] == ["skill-c/SKILL.md"]
    assert result["total_changes"] == 2


def test_proprioception_skills_no_changes(tmp_path, monkeypatch):
    """When forks match cache, returns silent result."""
    from metabolon.tools.mutation_sense import proprioception_skills

    local = tmp_path / "local"
    cache_base = tmp_path / "cache" / "superpowers"
    cache_ver = cache_base / "1.0.0" / "skills"

    (local / "skill-a").mkdir(parents=True)
    (cache_ver / "skill-a").mkdir(parents=True)
    (local / "skill-a" / "SKILL.md").write_text("same")
    (cache_ver / "skill-a" / "SKILL.md").write_text("same")

    registry = {
        "superpowers": {
            "local": str(local),
            "cache_pattern": str(cache_base),
        }
    }
    monkeypatch.setattr(
        "metabolon.tools.mutation_sense.restore_fork_registry", lambda path=None: registry
    )

    result = proprioception_skills()
    assert result.has_changes is False
    assert result.summary == ""


def test_proprioception_skills_with_changes(tmp_path, monkeypatch):
    """When upstream has changes, surfaces them."""
    from metabolon.tools.mutation_sense import proprioception_skills

    local = tmp_path / "local"
    cache_base = tmp_path / "cache" / "superpowers"
    cache_ver = cache_base / "1.0.0" / "skills"

    (local / "skill-a").mkdir(parents=True)
    (cache_ver / "skill-a").mkdir(parents=True)
    (local / "skill-a" / "SKILL.md").write_text("old")
    (cache_ver / "skill-a" / "SKILL.md").write_text("new improved version")

    registry = {
        "superpowers": {
            "local": str(local),
            "cache_pattern": str(cache_base),
        }
    }
    monkeypatch.setattr(
        "metabolon.tools.mutation_sense.restore_fork_registry", lambda path=None: registry
    )

    result = proprioception_skills()
    assert result.has_changes is True
    assert "superpowers" in result.summary
    assert "skill-a/SKILL.md" in result.summary
