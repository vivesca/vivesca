"""Tests for bank detection from PDF filename and page-1 text."""

from metabolon.respirometry.detect import detect_bank, filename_matches


def test_filename_mox():
    assert filename_matches("HO-MING-TERRY-LI_Jan2025_Mox_Credit_Statement.pdf")


def test_filename_hsbc():
    assert filename_matches("eStatementFile_20250315064205.pdf")


def test_filename_ccba():
    assert filename_matches("ECardPersonalStatement_HK_123_20250908_read.pdf")


def test_filename_random_pdf():
    assert not filename_matches("Terry Li - CV.pdf")


def test_detect_mox_from_text():
    text = "Page 1 of 5\nMox Credit statement\nMox Credit \u6708\u7d50\u55ae"
    assert detect_bank(text) == "mox"


def test_detect_hsbc_from_text():
    text = "HSBC\nSTATEMENT OF HSBC VISA SIGNATURE CARD ACCOUNT"
    assert detect_bank(text) == "hsbc"


def test_detect_ccba_from_text():
    text = "1000sXXCredit Card Statement\neye Credit Card\n4317-8420-0303-6220"
    assert detect_bank(text) == "ccba"


def test_detect_scb_from_text():
    text = "Standard Chartered Bank\nSMART CREDIT CARD\n4325-65XX-XXXX-4415"
    assert detect_bank(text) == "scb"


def test_filename_boc():
    assert filename_matches("02 月.pdf")
    assert filename_matches("12 月.pdf")


def test_detect_boc_from_text():
    text = "BOC Credit Card\n月結單\nMONTHLY STATEMENT\nCard Type: BOC Taobao World Mastercard"
    assert detect_bank(text) == "boc"


def test_detect_unknown():
    text = "Some random PDF text"
    assert detect_bank(text) is None
