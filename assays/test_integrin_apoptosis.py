"""Tests for integrin_apoptosis_check -- stay-alive signal for dormant receptors."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from metabolon.enzymes.integrin import (
    ApoptosisResult,
    _log_anoikis_candidates,
    integrin_apoptosis_check,
)

# -- Helpers ------------------------------------------------------------------


def _make_skill(receptors_dir: Path, name: str, binaries: list[str]) -> None:
    """Create a minimal receptor directory with a SKILL.md listing binaries."""
    receptor_dir = receptors_dir / name
    receptor_dir.mkdir(parents=True, exist_ok=True)
    bash_block = "```bash\n" + "\n".join(binaries) + "\n```\n"
    (receptor_dir / "SKILL.md").write_text(bash_block)


def _usage_tsv(entries: list[tuple[str, int]]) -> str:
    """Build a skill-usage.tsv string. entries = [(receptor_name, days_ago), ...]"""
    lines = []
    for name, days_ago in entries:
        ts = datetime.now() - timedelta(days=days_ago)
        lines.append(f"{ts.isoformat()}\t{name}")
    return "\n".join(lines)


# -- _log_anoikis_candidates --------------------------------------------------


class TestLogAnoikisCandidates:
    def test_empty_list_returns_false(self, tmp_path):
        log = tmp_path / "retirement.md"
        result = _log_anoikis_candidates([], retirement_log=log)
        assert result is False
        assert not log.exists()

    def test_writes_candidates_to_log(self, tmp_path):
        log = tmp_path / "notes" / "receptor-retirement.md"
        candidates = ["old-skill", "another-skill"]
        result = _log_anoikis_candidates(candidates, retirement_log=log)
        assert result is True
        content = log.read_text()
        assert "old-skill" in content
        assert "another-skill" in content
        assert "anoikis candidates" in content

    def test_appends_on_second_call(self, tmp_path):
        log = tmp_path / "retirement.md"
        _log_anoikis_candidates(["first-skill"], retirement_log=log)
        _log_anoikis_candidates(["second-skill"], retirement_log=log)
        content = log.read_text()
        assert "first-skill" in content
        assert "second-skill" in content

    def test_creates_parent_dirs(self, tmp_path):
        log = tmp_path / "deep" / "nested" / "retirement.md"
        assert not log.parent.exists()
        result = _log_anoikis_candidates(["some-skill"], retirement_log=log)
        assert result is True
        assert log.exists()

    def test_candidates_sorted_alphabetically(self, tmp_path):
        log = tmp_path / "retirement.md"
        _log_anoikis_candidates(["zebra-skill", "alpha-skill"], retirement_log=log)
        content = log.read_text()
        alpha_pos = content.index("alpha-skill")
        zebra_pos = content.index("zebra-skill")
        assert alpha_pos < zebra_pos


# -- integrin_apoptosis_check -------------------------------------------------


class TestIntegrinApoptosisCheck:
    """Integration-level tests via monkeypatching module-level constants."""

    def _patch_dirs(self, receptors_dir: Path, usage_tsv: str, retirement_log: Path):
        """Return a context manager that patches all three module constants."""
        import metabolon.enzymes.integrin as integrin_mod

        return [
            patch.object(integrin_mod, "SKILLS_DIR", receptors_dir),
            patch.object(integrin_mod, "SKILL_USAGE_LOG", receptors_dir / "usage.tsv"),
            patch.object(integrin_mod, "RECEPTOR_RETIREMENT_LOG", retirement_log),
        ]

    def _run(
        self,
        tmp_path: Path,
        receptors: dict[str, list[str]],
        usage: list[tuple[str, int]],
        *,
        binary_exists: bool = True,
    ) -> ApoptosisResult:
        """Set up fixtures and call integrin_apoptosis_check."""
        receptors_dir = tmp_path / "receptors"
        retirement_log = tmp_path / "retirement.md"
        usage_file = receptors_dir / "usage.tsv"

        receptors_dir.mkdir()
        for name, binaries in receptors.items():
            _make_skill(receptors_dir, name, binaries)
        if usage:
            usage_file.write_text(_usage_tsv(usage))

        import metabolon.enzymes.integrin as integrin_mod

        with (
            patch.object(integrin_mod, "SKILLS_DIR", receptors_dir),
            patch.object(integrin_mod, "SKILL_USAGE_LOG", usage_file),
            patch.object(integrin_mod, "RECEPTOR_RETIREMENT_LOG", retirement_log),
            patch("shutil.which", return_value=("/usr/bin/fake" if binary_exists else None)),
            patch.object(integrin_mod, "_probe_responsiveness", return_value=binary_exists),
        ):
            return integrin_apoptosis_check()

    def test_returns_apoptosis_result(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={"my-skill": ["sometool"]},
            usage=[("my-skill", 1)],
        )
        assert type(result).__name__ == "ApoptosisResult"

    def test_open_receptor_counted(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={"fresh-skill": ["sometool"]},
            usage=[("fresh-skill", 2)],  # 2 days ago = open
        )
        assert result.open_count == 1
        assert result.extended_count == 0
        assert result.bent_count == 0

    def test_extended_receptor_noted(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={"recent-skill": ["sometool"]},
            usage=[("recent-skill", 15)],  # 15 days ago = extended
        )
        assert result.extended_count == 1
        assert "recent-skill" in result.extended
        assert result.anoikis_candidate_count == 0

    def test_bent_quiescent_receptor(self, tmp_path):
        """Bent receptor with healthy ligands -> quiescent, not anoikis."""
        result = self._run(
            tmp_path,
            receptors={"old-skill": ["sometool"]},
            usage=[("old-skill", 45)],  # >30 days = bent
            binary_exists=True,  # ligand is healthy
        )
        assert result.bent_count == 1
        assert result.anoikis_candidate_count == 0
        assert "old-skill" in result.quiescent

    def test_bent_anoikis_candidate(self, tmp_path):
        """Bent receptor with all ligands detached -> anoikis candidate."""
        result = self._run(
            tmp_path,
            receptors={"dead-skill": ["missingbinary"]},
            usage=[("dead-skill", 45)],  # >30 days = bent
            binary_exists=False,  # ligand detached
        )
        assert result.bent_count == 1
        assert result.anoikis_candidate_count == 1
        assert "dead-skill" in result.anoikis_candidates

    def test_never_used_receptor_is_bent(self, tmp_path):
        """Receptor with no usage log entry is bent."""
        result = self._run(
            tmp_path,
            receptors={"ghost-skill": ["sometool"]},
            usage=[],  # no usage at all
        )
        assert result.bent_count == 1

    def test_anoikis_candidates_logged_to_retirement(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={"forgotten-skill": ["nosuchbinary"]},
            usage=[("forgotten-skill", 60)],
            binary_exists=False,
        )
        assert result.retirement_log_updated is True
        retirement_log = tmp_path / "retirement.md"
        assert retirement_log.exists()
        content = retirement_log.read_text()
        assert "forgotten-skill" in content

    def test_no_anoikis_candidates_no_log_write(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={"active-skill": ["sometool"]},
            usage=[("active-skill", 1)],
            binary_exists=True,
        )
        assert result.retirement_log_updated is False
        assert not (tmp_path / "retirement.md").exists()

    def test_summary_contains_counts(self, tmp_path):
        result = self._run(
            tmp_path,
            receptors={
                "open-skill": ["sometool"],
                "extended-skill": ["sometool"],
                "bent-skill": ["sometool"],
            },
            usage=[
                ("open-skill", 1),
                ("extended-skill", 15),
                ("bent-skill", 45),
            ],
        )
        assert "open" in result.summary
        assert "extended" in result.summary
        assert "bent" in result.summary

    def test_empty_receptors_dir(self, tmp_path):
        receptors_dir = tmp_path / "receptors"
        receptors_dir.mkdir()
        retirement_log = tmp_path / "retirement.md"
        usage_file = receptors_dir / "usage.tsv"

        import metabolon.enzymes.integrin as integrin_mod

        with (
            patch.object(integrin_mod, "SKILLS_DIR", receptors_dir),
            patch.object(integrin_mod, "SKILL_USAGE_LOG", usage_file),
            patch.object(integrin_mod, "RECEPTOR_RETIREMENT_LOG", retirement_log),
        ):
            result = integrin_apoptosis_check()

        assert result.open_count == 0
        assert result.extended_count == 0
        assert result.bent_count == 0
        assert result.anoikis_candidate_count == 0

    def test_mixed_population(self, tmp_path):
        """Mixed population correctly partitions all three states."""
        result = self._run(
            tmp_path,
            receptors={
                "alpha": ["presentbinary"],
                "beta": ["presentbinary"],
                "gamma": ["presentbinary"],
                "delta": ["missingbinary"],
            },
            usage=[
                ("alpha", 2),  # open
                ("beta", 14),  # extended
                ("gamma", 50),  # bent, ligand healthy -> quiescent
                ("delta", 50),  # bent, ligand missing -> anoikis
            ],
            binary_exists=True,
        )
        # delta has no binary -- we need to simulate it differently
        # Re-run with a selective mock
        import metabolon.enzymes.integrin as integrin_mod

        receptors_dir = tmp_path / "receptors2"
        retirement_log = tmp_path / "retirement2.md"
        usage_file = receptors_dir / "usage2.tsv"
        receptors_dir.mkdir()
        for name in ["alpha", "beta", "gamma"]:
            _make_skill(receptors_dir, name, ["presentbinary"])
        _make_skill(receptors_dir, "delta", ["missingbinary"])
        usage_file.write_text(
            _usage_tsv(
                [
                    ("alpha", 2),
                    ("beta", 14),
                    ("gamma", 50),
                    ("delta", 50),
                ]
            )
        )

        def selective_which(cmd):
            return "/usr/bin/fake" if cmd == "presentbinary" else None

        with (
            patch.object(integrin_mod, "SKILLS_DIR", receptors_dir),
            patch.object(integrin_mod, "SKILL_USAGE_LOG", usage_file),
            patch.object(integrin_mod, "RECEPTOR_RETIREMENT_LOG", retirement_log),
            patch("shutil.which", side_effect=selective_which),
            patch.object(integrin_mod, "_probe_responsiveness", return_value=True),
        ):
            result = integrin_apoptosis_check()

        assert result.open_count == 1
        assert result.extended_count == 1
        assert result.bent_count == 2  # gamma (quiescent) + delta (anoikis)
        assert result.anoikis_candidate_count == 1
        assert "delta" in result.anoikis_candidates
        assert "gamma" in result.quiescent
