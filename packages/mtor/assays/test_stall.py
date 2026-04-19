from mtor.stall import StallSignal, detect_stall, format_stall_marker


def test_success_no_stall():
    signal = detect_stall(exit_code=0, duration_seconds=120, output_length=500, files_created=3)
    assert not signal.is_stalled


def test_self_reported_stall():
    signal = detect_stall(
        exit_code=1,
        duration_seconds=300,
        output_length=1000,
        files_created=0,
        self_report="STALL: import error loop",
    )
    assert signal.is_stalled
    assert signal.stall_type == "self-reported"


def test_built_nothing():
    signal = detect_stall(exit_code=1, duration_seconds=120, output_length=200, files_created=0)
    assert signal.stall_type == "built-nothing"


def test_monologue():
    signal = detect_stall(exit_code=1, duration_seconds=600, output_length=10000, files_created=0)
    assert signal.stall_type == "monologue"


def test_failed_but_produced_files():
    signal = detect_stall(exit_code=1, duration_seconds=300, output_length=5000, files_created=2)
    assert not signal.is_stalled


def test_format_marker():
    signal = StallSignal(stall_type="built-nothing", detail="ran 120s, 0 files")
    marker = format_stall_marker("zhipu", signal, 120)
    assert "RIBOSOME_STALL:" in marker and "zhipu" in marker
