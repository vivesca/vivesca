"""Tests for merchant categorisation."""

from metabolon.respirometry.categories import categorise, restore_categories


def test_exact_prefix_match():
    cats = {"GOOGLE": "Tech/Subscriptions", "GITHUB": "Tech/Dev Tools"}
    assert categorise("GOOGLE", cats) == "Tech/Subscriptions"


def test_spending_categories_case_insensitive():
    cats = {"SMARTONE": "Telecom"}
    assert categorise("SmarTone", cats) == "Telecom"
    assert categorise("smartone", cats) == "Telecom"


def test_prefix_match():
    cats = {"PAYPAL *GIVEWELL": "Charity/Donation"}
    assert categorise("PAYPAL *GIVEWELL 4029357733", cats) == "Charity/Donation"


def test_uncategorised():
    cats = {"GOOGLE": "Tech/Subscriptions"}
    assert categorise("UNKNOWN MERCHANT", cats) == "Uncategorised"


def test_first_match_wins():
    cats = {"GOOGLE": "Tech/Subscriptions", "GOOGLE CLOUD": "Tech/Infrastructure"}
    assert categorise("GOOGLE CLOUD PLATFORM", cats) == "Tech/Subscriptions"


def test_restore_categories(tmp_path):
    yaml_file = tmp_path / "categories.yaml"
    yaml_file.write_text("GOOGLE: Tech/Subscriptions\nSMARTONE: Telecom\n")
    cats = restore_categories(yaml_file)
    assert cats["GOOGLE"] == "Tech/Subscriptions"
    assert cats["SMARTONE"] == "Telecom"


def test_restore_categories_missing_file(tmp_path):
    cats = restore_categories(tmp_path / "nonexistent.yaml")
    assert cats == {}
