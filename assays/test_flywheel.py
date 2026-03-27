import pytest

from metabolon.tools.interoception import anabolism_flywheel


@pytest.fixture
def mock_health_log(tmp_path, monkeypatch):
    """Mock the health log path to a temp file."""
    log_path = tmp_path / "Symptom Log.md"
    monkeypatch.setattr("metabolon.tools.interoception.HEALTH_LOG", str(log_path))
    return log_path


@pytest.fixture
def mock_all(monkeypatch, mock_health_log):
    def _mock_chemoreceptor_today(*args, **kwargs):
        return {"sleep_score": 85, "readiness_score": 82}

    def _mock_scheduled_events(*args, **kwargs):
        return "09:00 AM Meeting\n10:00 AM Work\n12:00 PM Lunch"

    def _mock_subprocess_run(cmd, *args, **kwargs):
        class MockCompletedProcess:
            def __init__(self, stdout):
                self.stdout = stdout
                self.returncode = 0

        if "log" in cmd and "Writing/Blog/Published/" in cmd:
            return MockCompletedProcess("commit1\ncommit2\n")
        if "log" in cmd:
            return MockCompletedProcess("commit1\n" * 10)

        # default for other subprocess.run calls (like mo clean if any)
        return MockCompletedProcess("")

    monkeypatch.setattr("metabolon.organelles.chemoreceptor.today", _mock_chemoreceptor_today)
    monkeypatch.setattr("metabolon.organelles.circadian_clock.scheduled_events", _mock_scheduled_events)
    monkeypatch.setattr("metabolon.tools.interoception.subprocess.run", _mock_subprocess_run)
    return mock_health_log


def test_flywheel_all_spinning(mock_all):
    result = anabolism_flywheel()
    assert not hasattr(result, "break_point")

    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] == 85

    energy_link = next(lk for lk in result.links if lk["name"] == "energy")
    assert energy_link["score"] == 82

    symptoms_link = next(lk for lk in result.links if lk["name"] == "symptoms")
    assert symptoms_link["recent_entries_7d"] == 0


def test_flywheel_sleep_stalled(monkeypatch, mock_all):
    def _mock_chemoreceptor_today(*args, **kwargs):
        return {"sleep_score": 45, "readiness_score": 50}

    monkeypatch.setattr("metabolon.organelles.chemoreceptor.today", _mock_chemoreceptor_today)

    result = anabolism_flywheel()
    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] == 45

    energy_link = next(lk for lk in result.links if lk["name"] == "energy")
    assert energy_link["score"] == 50


def test_flywheel_creative_slowing(monkeypatch, mock_all):
    def _mock_subprocess_run(cmd, *args, **kwargs):
        class MockCompletedProcess:
            def __init__(self, stdout):
                self.stdout = stdout
                self.returncode = 0

        if "log" in cmd and "Writing/Blog/Published/" in cmd:
            return MockCompletedProcess("")
        if "log" in cmd:
            return MockCompletedProcess("commit1\n" * 5)
        return MockCompletedProcess("")

    monkeypatch.setattr("metabolon.tools.interoception.subprocess.run", _mock_subprocess_run)

    result = anabolism_flywheel()
    creative_link = next(lk for lk in result.links if lk["name"] == "creative")
    assert creative_link["vault_commits_7d"] == 5
    assert creative_link["blog_commits_14d"] == 0


def test_flywheel_blind_spots_always_present(mock_all):
    result = anabolism_flywheel()
    assert "exercise (no sensor)" in result.blind_spots
    assert "mood/joy (ask)" in result.blind_spots
    assert "anxiety (ask)" in result.blind_spots


def test_flywheel_sopor_failure_graceful(monkeypatch, mock_all):
    def _mock_chemoreceptor_today_fail(*args, **kwargs):
        raise ValueError("sopor failed")

    monkeypatch.setattr("metabolon.organelles.chemoreceptor.today", _mock_chemoreceptor_today_fail)

    result = anabolism_flywheel()
    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] is None


def test_flywheel_break_point_priority(monkeypatch, mock_all):
    def _mock_chemoreceptor_today(*args, **kwargs):
        return {"sleep_score": 45, "readiness_score": 50}

    monkeypatch.setattr("metabolon.organelles.chemoreceptor.today", _mock_chemoreceptor_today)

    def _mock_subprocess_run(cmd, *args, **kwargs):
        class MockCompletedProcess:
            def __init__(self, stdout):
                self.stdout = stdout
                self.returncode = 0

        if "log" in cmd and "Writing/Blog/Published/" in cmd:
            return MockCompletedProcess("")
        if "log" in cmd:
            return MockCompletedProcess("commit1\n" * 5)
        return MockCompletedProcess("")

    monkeypatch.setattr("metabolon.tools.interoception.subprocess.run", _mock_subprocess_run)

    result = anabolism_flywheel()
    # LLM now interprets — verify raw data is present for both low-scoring links
    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] == 45  # low score, LLM can classify as stalled

    creative_link = next(lk for lk in result.links if lk["name"] == "creative")
    assert creative_link["vault_commits_7d"] == 5
    assert creative_link["blog_commits_14d"] == 0  # low, LLM can classify as slowing
