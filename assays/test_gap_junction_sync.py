from __future__ import annotations

"""Tests for effectors/gap_junction_sync — bash wrapper + Python _cli."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "gap_junction_sync"
MODULE = Path(__file__).parent.parent / "metabolon" / "organelles" / "gap_junction.py"


def _load_module():
    """Load gap_junction.py via exec for _cli unit testing."""
    source = MODULE.read_text()
    ns: dict = {"__name__": "gap_junction_test"}
    exec(source, ns)
    return ns


# ── Bash script structure and integration tests ─────────────────────────


class TestBashScript:
    """Tests for the gap_junction_sync bash wrapper."""

    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_shebang_is_bash(self):
        lines = SCRIPT.read_text().splitlines()
        assert lines[0] == "#!/bin/bash"

    def test_sets_pythonpath_to_germline(self):
        content = SCRIPT.read_text()
        assert 'PYTHONPATH="${HOME}/germline' in content

    def test_execs_correct_module(self):
        content = SCRIPT.read_text()
        assert "exec python3 -m metabolon.organelles.gap_junction" in content

    def test_passes_sync_catchup_args(self):
        content = SCRIPT.read_text()
        assert "sync catchup" in content

    def test_no_arg_forwarding(self):
        """Script does not forward caller $@ or $* to python."""
        content = SCRIPT.read_text()
        for line in content.splitlines():
            if line.startswith("#"):
                continue
            assert "$@" not in line
            assert "$*" not in line

    def test_invokes_python3_with_correct_args(self, tmp_path):
        """Verify the script passes -m module sync catchup to python3."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text('#!/bin/bash\necho "INVOKED: $@"\n')
        fake_python.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert "INVOKED: -m metabolon.organelles.gap_junction sync catchup" in r.stdout

    def test_pythonpath_includes_home_germline(self, tmp_path):
        """Verify PYTHONPATH is set to $HOME/germline."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text('#!/bin/bash\necho "PP=$PYTHONPATH"\n')
        fake_python.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
        env["HOME"] = str(tmp_path / "myhome")

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert f"{tmp_path}/myhome/germline" in r.stdout


# ── Python _cli unit tests ─────────────────────────────────────────────


class TestCliSyncCatchup:
    """Tests for _cli() sync catchup behavior via exec."""

    @staticmethod
    def _mod():
        """Fresh module load per test to avoid state pollution."""
        return _load_module()

    def test_success_prints_result(self, capsys):
        """_cli prints wacli sync result on stdout."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="sync complete")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        assert "sync complete" in capsys.readouterr().out

    def test_calls_wacli_with_sync_once(self):
        """_cli calls _wacli(['sync', '--once'], timeout=120)."""
        mod = self._mod()
        mock_wacli = MagicMock(return_value="ok")
        mod["_wacli"] = mock_wacli
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        mock_wacli.assert_called_once_with(["sync", "--once"], timeout=120)

    def test_empty_result_prints_empty_line(self, capsys):
        """_cli prints empty string when sync returns empty."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        out = capsys.readouterr().out
        assert out.strip() == ""

    def test_no_exit_on_success(self):
        """_cli does not call sys.exit on success."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="ok")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()  # no SystemExit raised

    def test_store_locked_exits_0(self):
        """_cli exits 0 when wacli reports store is locked."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("store is locked by daemon"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 0

    def test_store_locked_stderr_message(self, capsys):
        """_cli prints 'daemon is running' to stderr when store is locked."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("store is locked"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        assert "daemon is running" in capsys.readouterr().err

    def test_other_valueerror_exits_1(self):
        """_cli exits 1 for non-locked ValueError."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("connection refused"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 1

    def test_error_message_on_stderr(self, capsys):
        """_cli prints error details to stderr for non-locked errors."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("connection refused"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        assert "connection refused" in capsys.readouterr().err


class TestCliWrongArgs:
    """Tests for _cli() with invalid arguments."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_no_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_wrong_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "foo", "bar"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_partial_args_exits_2(self):
        """Only 'sync' without 'catchup' is not valid."""
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "sync"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_extra_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "sync", "catchup", "extra"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_usage_message_on_stderr(self, capsys):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        err = capsys.readouterr().err
        assert "usage" in err.lower()
        assert "gap_junction" in err

    def test_wrong_args_does_not_call_wacli(self):
        """_cli never calls _wacli when args are wrong."""
        mod = self._mod()
        mock_wacli = MagicMock()
        original_wacli = mod["_wacli"]
        mod["_wacli"] = mock_wacli
        with patch("sys.argv", ["gap_junction", "bad"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        mock_wacli.assert_not_called()


# ── Pure function tests ─────────────────────────────────────────────────


class TestExtractMessages:
    """Tests for _extract_messages."""

    @staticmethod
    def _fn():
        return _load_module()["_extract_messages"]

    def test_valid_envelope(self):
        raw = {"data": {"messages": [{"MsgID": "1"}, {"MsgID": "2"}]}}
        result = self._fn()(raw)
        assert len(result) == 2
        assert result[0]["MsgID"] == "1"

    def test_missing_data_key(self):
        result = self._fn()({})
        assert result == []

    def test_missing_messages_key(self):
        result = self._fn()({"data": {}})
        assert result == []

    def test_messages_is_none(self):
        result = self._fn()({"data": {"messages": None}})
        assert result == []

    def test_non_dict_input(self):
        result = self._fn()("not a dict")
        assert result == []

    def test_data_is_list(self):
        result = self._fn()({"data": []})
        assert result == []


class TestExtractContacts:
    """Tests for _extract_contacts."""

    @staticmethod
    def _fn():
        return _load_module()["_extract_contacts"]

    def test_valid_envelope(self):
        raw = {"data": [{"JID": "a@s.whatsapp.net"}, {"JID": "b@lid"}]}
        result = self._fn()(raw)
        assert len(result) == 2

    def test_missing_data_key(self):
        result = self._fn()({})
        assert result == []

    def test_data_is_dict_not_list(self):
        result = self._fn()({"data": {"messages": []}})
        assert result == []

    def test_non_dict_input(self):
        result = self._fn()(42)
        assert result == []


class TestDedupSort:
    """Tests for _dedup_sort."""

    @staticmethod
    def _fn():
        return _load_module()["_dedup_sort"]

    def test_dedup_by_msgid(self):
        msgs = [
            {"MsgID": "a", "Timestamp": "2025-01-01"},
            {"MsgID": "a", "Timestamp": "2025-01-01"},
        ]
        result = self._fn()(msgs, 10)
        assert len(result) == 1

    def test_sort_by_timestamp_descending(self):
        msgs = [
            {"MsgID": "a", "Timestamp": "2025-01-01"},
            {"MsgID": "b", "Timestamp": "2025-01-03"},
            {"MsgID": "c", "Timestamp": "2025-01-02"},
        ]
        result = self._fn()(msgs, 10)
        assert [m["MsgID"] for m in result] == ["b", "c", "a"]

    def test_limit_applied(self):
        msgs = [{"MsgID": str(i), "Timestamp": f"2025-01-{i:02d}"} for i in range(1, 11)]
        result = self._fn()(msgs, 3)
        assert len(result) == 3

    def test_empty_msgid_skipped(self):
        msgs = [
            {"MsgID": "", "Timestamp": "2025-01-01"},
            {"MsgID": "a", "Timestamp": "2025-01-02"},
        ]
        result = self._fn()(msgs, 10)
        assert len(result) == 1
        assert result[0]["MsgID"] == "a"

    def test_no_msgid_key_skipped(self):
        msgs = [
            {"Timestamp": "2025-01-01"},
            {"MsgID": "a", "Timestamp": "2025-01-02"},
        ]
        result = self._fn()(msgs, 10)
        assert len(result) == 1

    def test_empty_input(self):
        assert self._fn()([], 10) == []


class TestFormatMessages:
    """Tests for _format_messages."""

    @staticmethod
    def _fn():
        return _load_module()["_format_messages"]

    def test_formats_single_message(self):
        msgs = [{"Timestamp": "2025-01-01T10:30:00Z", "FromMe": True, "Text": "hello"}]
        result = self._fn()(msgs, "tara")
        assert "2025-01-01T10:30:00" in result
        assert "me: hello" in result

    def test_formats_received_message(self):
        msgs = [{"Timestamp": "2025-01-01T10:30:00Z", "FromMe": False, "Text": "hi"}]
        result = self._fn()(msgs, "tara")
        assert "tara: hi" in result

    def test_empty_messages(self):
        result = self._fn()([], "tara")
        assert result == "No messages found"

    def test_timestamp_truncated_to_19_chars(self):
        msgs = [{"Timestamp": "2025-06-15T14:22:33.123456Z", "FromMe": False, "Text": "x"}]
        result = self._fn()(msgs, "bob")
        assert "2025-06-15T14:22:33" in result

    def test_multiple_messages_newline_separated(self):
        msgs = [
            {"Timestamp": "2025-01-01T10:00:00Z", "FromMe": True, "Text": "a"},
            {"Timestamp": "2025-01-01T11:00:00Z", "FromMe": False, "Text": "b"},
        ]
        result = self._fn()(msgs, "tara")
        lines = result.split("\n")
        assert len(lines) == 2

    def test_missing_text_defaults_empty(self):
        msgs = [{"Timestamp": "2025-01-01T10:00:00Z", "FromMe": False}]
        result = self._fn()(msgs, "bob")
        assert "bob: " in result


class TestContactType:
    """Tests for contact_type."""

    @staticmethod
    def _fn():
        return _load_module()["contact_type"]

    def test_gap_junction_contact(self):
        for name in ["tara", "mum", "dad", "brother", "sister", "yujie"]:
            assert self._fn()(name) == "gap_junction"

    def test_gap_junction_case_insensitive(self):
        assert self._fn()("Tara") == "gap_junction"
        assert self._fn()("MUM") == "gap_junction"

    def test_receptor_contact(self):
        assert self._fn()("accountant") == "receptor"
        assert self._fn()("boss") == "receptor"


# ── Higher-level function tests (mocked _wacli) ─────────────────────────


class TestWacliFunction:
    """Tests for _wacli subprocess wrapper."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_success_returns_stdout(self):
        mod = self._mod()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  ok result  \n"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = mod["_wacli"](["test"])
        assert result == "ok result"

    def test_failure_raises_valueerror(self):
        mod = self._mod()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "something broke"
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ValueError, match="wacli failed"):
                mod["_wacli"](["bad"])

    def test_timeout_forwarded(self):
        mod = self._mod()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            mod["_wacli"](["sync", "--once"], timeout=120)
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("timeout") == 120 or call_kwargs[1].get("timeout") == 120


class TestWacliJson:
    """Tests for _wacli_json."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_parses_valid_json(self):
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value='{"success": true, "data": []}')
        result = mod["_wacli_json"](["contacts", "search", "tara", "--json"])
        assert result == {"success": True, "data": []}

    def test_invalid_json_returns_empty_dict(self):
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="not json at all")
        result = mod["_wacli_json"](["test"])
        assert result == {}

    def test_empty_string_returns_empty_dict(self):
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="")
        result = mod["_wacli_json"](["test"])
        assert result == {}


class TestResolveJids:
    """Tests for resolve_jids."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_returns_jids_from_search(self):
        mod = self._mod()
        contacts = {"data": [
            {"JID": "123@s.whatsapp.net", "Name": "tara"},
            {"JID": "123@lid", "Name": "tara"},
        ]}
        mod["_wacli_json"] = MagicMock(return_value=contacts)
        jids = mod["resolve_jids"]("tara")
        assert jids == ["123@s.whatsapp.net", "123@lid"]

    def test_no_contacts_returns_empty(self):
        mod = self._mod()
        mod["_wacli_json"] = MagicMock(return_value={"data": []})
        jids = mod["resolve_jids"]("nobody")
        assert jids == []

    def test_contacts_without_jid_skipped(self):
        mod = self._mod()
        contacts = {"data": [{"Name": "tara"}, {"JID": "123@s.whatsapp.net", "Name": "tara"}]}
        mod["_wacli_json"] = MagicMock(return_value=contacts)
        jids = mod["resolve_jids"]("tara")
        assert jids == ["123@s.whatsapp.net"]


class TestReceiveSignals:
    """Tests for receive_signals."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_no_contact_found(self):
        mod = self._mod()
        mod["resolve_jids"] = MagicMock(return_value=[])
        result = mod["receive_signals"]("nobody")
        assert "No contact found" in result

    def test_merges_multiple_jids(self):
        mod = self._mod()
        mod["resolve_jids"] = MagicMock(return_value=["a@s.whatsapp.net", "a@lid"])
        mod["_wacli_json"] = MagicMock(return_value={"data": {"messages": [
            {"MsgID": "1", "Timestamp": "2025-01-01T10:00:00Z", "FromMe": True, "Text": "hi"},
        ]}})
        result = mod["receive_signals"]("tara", limit=5)
        assert "me: hi" in result


class TestSearchSignals:
    """Tests for search_signals."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_global_search_no_name(self):
        mod = self._mod()
        msgs = {"data": {"messages": [
            {"MsgID": "1", "Timestamp": "2025-03-01T12:00:00Z", "FromMe": False, "Text": "lunch?"},
        ]}}
        mod["_wacli_json"] = MagicMock(return_value=msgs)
        result = mod["search_signals"]("lunch")
        assert "them: lunch?" in result

    def test_scoped_search_no_contact(self):
        mod = self._mod()
        mod["resolve_jids"] = MagicMock(return_value=[])
        result = mod["search_signals"]("hello", name="ghost")
        assert "No contact found" in result

    def test_scoped_search_with_jids(self):
        mod = self._mod()
        mod["resolve_jids"] = MagicMock(return_value=["a@s.whatsapp.net"])
        mod["_wacli_json"] = MagicMock(return_value={"data": {"messages": [
            {"MsgID": "2", "Timestamp": "2025-02-01T09:00:00Z", "FromMe": True, "Text": "yo"},
        ]}})
        result = mod["search_signals"]("yo", name="tara")
        assert "me: yo" in result


class TestComposeSignal:
    """Tests for compose_signal (draft only, never sends)."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_returns_wacli_command(self):
        mod = self._mod()
        with patch.object(mod, "resolve_jids", return_value=["123@s.whatsapp.net"]):
            result = mod["compose_signal"]("tara", "hello there")
        assert "wacli send --to '123@s.whatsapp.net'" in result
        assert "hello there" in result

    def test_no_contact_returns_comment(self):
        mod = self._mod()
        with patch.object(mod, "resolve_jids", return_value=[]):
            result = mod["compose_signal"]("ghost", "hello")
        assert result.startswith("# No contact found")

    def test_escapes_single_quotes(self):
        mod = self._mod()
        with patch.object(mod, "resolve_jids", return_value=["123@s.whatsapp.net"]):
            result = mod["compose_signal"]("tara", "it's fine")
        assert "'\\''" in result or "it'\\''s fine" in result

    def test_uses_first_jid_only(self):
        mod = self._mod()
        with patch.object(mod, "resolve_jids", return_value=["a@s.whatsapp.net", "a@lid"]):
            result = mod["compose_signal"]("tara", "hi")
        assert "a@s.whatsapp.net" in result
        assert "a@lid" not in result


class TestActiveJunctions:
    """Tests for active_junctions."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_calls_wacli_with_correct_args(self):
        mod = self._mod()
        with patch.object(mod, "_wacli", return_value="chat list") as mock:
            result = mod["active_junctions"](limit=5)
        mock.assert_called_once_with(["chats", "list", "--limit", "5"])
        assert result == "chat list"


class TestJunctionStatus:
    """Tests for junction_status."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_calls_wacli_sync_status(self):
        mod = self._mod()
        with patch.object(mod, "_wacli", return_value="running") as mock:
            result = mod["junction_status"]()
        mock.assert_called_once_with(["sync", "status"])
        assert result == "running"


class TestSyncCatchup:
    """Tests for sync_catchup."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_calls_wacli_sync_once(self):
        mod = self._mod()
        with patch.object(mod, "_wacli", return_value="synced") as mock:
            result = mod["sync_catchup"]()
        mock.assert_called_once_with(["sync", "--once"], timeout=120)
        assert result == "synced"
