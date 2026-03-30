import pytest

from metabolon.enzymes.interoception import interoception


@pytest.fixture
def mock_health_log(tmp_path, monkeypatch):
    log_path = tmp_path / "Symptom Log.md"
    monkeypatch.setattr(
        "metabolon.enzymes.interoception._health_log_path", lambda: str(log_path)
    )
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
            return MockCompletedProcess("commit1")
        else:
            return MockCompletedProcess("")

    monkeypatch.setattr("metabolon.organelles.chemoreceptor.today", _mock_chemoreceptor_today)
    monkeypatch.setattr(
        "metabolon.organelles.circadian_clock.scheduled_events", _mock_scheduled_events
    )
    monkeypatch.setattr("metabolon.enzymes.interoception.subprocess.run", _mock_subprocess_run)


def test_flywheel_basic(mock_all):
    result = interoception("flywheel")
    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] == 85


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

    monkeypatch.setattr("metabolon.enzymes.interoception.subprocess.run", _mock_subprocess_run)

    result = interoception("flywheel")
    sleep_link = next(lk for lk in result.links if lk["name"] == "sleep")
    assert sleep_link["score"] == 45

    creative_link = next(lk for lk in result.links if lk["name"] == "creative")
    assert creative_link["blog_commits_14d"] == 0
