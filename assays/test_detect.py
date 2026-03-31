"""Tests for metabolon.respirometry.detect."""

from metabolon.respirometry.detect import filename_matches, identify_bank


class TestFilenameMatches:
    """Tests for filename_matches."""

from __future__ import annotations

    def test_mox_filename_matches(self) -> None:
        """Mox statement filename matches."""
        filename = "HO-MING-TERRY-LI_202403_123456_Mox_Credit_Statement.pdf"
        assert filename_matches(filename) is True

    def test_hsbc_filename_matches(self) -> None:
        """HSBC eStatement filename matches."""
        filename = "eStatementFile_12345.pdf"
        assert filename_matches(filename) is True
        assert filename_matches("eStatementFile_.pdf") is True

    def test_ccba_filename_matches(self) -> None:
        """CCBA statement filename matches."""
        filename = "ECardPersonalStatement_202403.pdf"
        assert filename_matches(filename) is True

    def test_jp_month_filename_matches(self) -> None:
        """Chinese month filename matches."""
        filename = "03月.pdf"
        assert filename_matches(filename) is True

    def test_random_filename_does_not_match(self) -> None:
        """Random filename doesn't match."""
        filename = "document.pdf"
        assert filename_matches(filename) is False
        assert filename_matches("statement.doc") is False


class TestIdentifyBank:
    """Tests for identify_bank."""

    def test_identify_mox(self) -> None:
        """Identifies Mox bank signature."""
        text = "Some header\nMox Credit statement\nmore text"
        assert identify_bank(text) == "mox"

    def test_identify_hsbc(self) -> None:
        """Identifies HSBC bank signature."""
        text = "HSBC\nVISA SIGNATURE\nstatement"
        assert identify_bank(text) == "hsbc"

    def test_identify_ccba(self) -> None:
        """Identifies CCBA bank signature."""
        text = "eye Credit Card\nstatement"
        assert identify_bank(text) == "ccba"

    def test_identify_scb(self) -> None:
        """Identifies SCB bank signature."""
        text = "SMART CREDIT CARD\nmonthly statement"
        assert identify_bank(text) == "scb"

    def test_identify_boc(self) -> None:
        """Identifies BOC bank signature."""
        text = "BOC Credit Card\nMONTHLY STATEMENT\nblah"
        assert identify_bank(text) == "boc"

    def test_unrecognised_text_returns_none(self) -> None:
        """Unrecognised text returns None."""
        text = "Some random bank statement\nunknown text"
        assert identify_bank(text) is None

    def test_all_signatures_required(self) -> None:
        """All signature phrases must be present."""
        # Only HSBC but not VISA SIGNATURE -> not identified
        text = "HSBC statement"
        assert identify_bank(text) != "hsbc"

        # Only BOC Credit Card but no MONTHLY STATEMENT -> not identified
        text = "BOC Credit Card"
        assert identify_bank(text) != "boc"
