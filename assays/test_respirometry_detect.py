from __future__ import annotations

"""Tests for metabolon.respirometry.detect."""

from metabolon.respirometry.detect import filename_matches, identify_bank


# ── filename_matches ────────────────────────────────────────────────

class TestFilenameMatches:
    """Positive and negative cases for each filename pattern."""

    # Mox
    def test_mox_statement(self):
        assert filename_matches("HO-MING-TERRY-LI_202501_Mox_Credit_Statement.pdf")

    def test_mox_statement_other_name(self):
        assert filename_matches("HO-MING-TERRY-LI_202412_Mox_Credit_Statement.pdf")

    def test_mox_wrong_prefix(self):
        assert not filename_matches("OTHER_202501_Mox_Credit_Statement.pdf")

    # eStatementFile
    def test_estatement_file_underscore(self):
        assert filename_matches("eStatementFile_202501.pdf")

    def test_estatement_file_dot(self):
        assert filename_matches("eStatementFile.202501.pdf")

    def test_estatement_wrong_prefix(self):
        assert not filename_matches("StatementFile_202501.pdf")

    # ECardPersonalStatement
    def test_ecard_personal(self):
        assert filename_matches("ECardPersonalStatement_01_2025.pdf")

    def test_ecard_no_suffix(self):
        assert filename_matches("ECardPersonalStatement.pdf")

    # Chinese month pattern: N月.pdf
    def test_chinese_month_single_digit(self):
        assert filename_matches("01 月.pdf")

    def test_chinese_month_double_digit(self):
        assert filename_matches("12月.pdf")

    def test_chinese_month_no_space(self):
        assert filename_matches("3月.pdf")

    def test_chinese_month_wrong_extension(self):
        assert not filename_matches("12月.txt")

    # Generic negatives
    def test_random_filename(self):
        assert not filename_matches("random_document.pdf")

    def test_empty_string(self):
        assert not filename_matches("")

    def test_non_pdf(self):
        assert not filename_matches("statement.docx")


# ── identify_bank ───────────────────────────────────────────────────

class TestIdentifyBank:
    """Signature-based bank detection from page-1 text."""

    # Mox
    def test_mox(self):
        text = "Mox Credit statement for January 2025"
        assert identify_bank(text) == "mox"

    def test_mox_case_sensitive(self):
        """Signature matching is case-sensitive."""
        assert identify_bank("mox credit statement") is None

    # HSBC
    def test_hsbc(self):
        text = "HSBC VISA SIGNATURE card statement"
        assert identify_bank(text) == "hsbc"

    def test_hsbc_missing_visa_signature(self):
        assert identify_bank("HSBC platinum card") is None

    # CBA (eye Credit Card)
    def test_ccba(self):
        text = "Your eye Credit Card statement"
        assert identify_bank(text) == "ccba"

    def test_ccba_case_sensitive(self):
        assert identify_bank("Eye credit card statement") is None

    # Standard Chartered
    def test_scb(self):
        text = "SMART CREDIT CARD statement"
        assert identify_bank(text) == "scb"

    def test_scb_case_sensitive(self):
        assert identify_bank("Smart Credit Card") is None

    # BOC
    def test_boc(self):
        text = "BOC Credit Card MONTHLY STATEMENT"
        assert identify_bank(text) == "boc"

    def test_boc_missing_monthly(self):
        assert identify_bank("BOC Credit Card summary") is None

    # Unrecognised
    def test_unknown_bank(self):
        assert identify_bank("Some random text") is None

    def test_empty_string(self):
        assert identify_bank("") is None

    # Priority: first match wins
    def test_first_match_wins(self):
        """If text matches multiple banks, the first in _BANK_SIGNATURES wins."""
        text = "Mox Credit statement HSBC VISA SIGNATURE"
        assert identify_bank(text) == "mox"
