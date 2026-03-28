import json

import pytest

from metabolon.lysin.fetch import BioArticle
from metabolon.lysin.format import format_json, format_text


@pytest.fixture
def sample_article():
    return BioArticle(
        title="Endocytosis",
        definition="Endocytosis is a cellular process.",
        mechanism="Endocytosis is a cellular process. It is cool.",
        url="http://example.com/Endocytosis",
        sections=[{"title": "Types", "text": "Phagocytosis and pinocytosis."}],
    )


def test_format_text_summary(sample_article):
    text = format_text(sample_article)
    assert "LYSIN: Endocytosis" in text
    assert "DEFINITION" in text
    assert "Endocytosis is a cellular process." in text
    assert "MECHANISM" in text
    assert "Endocytosis is a cellular process. It is cool." in text
    assert "URL\nhttp://example.com/Endocytosis" in text
    assert "SECTIONS" not in text


def test_format_text_full(sample_article):
    text = format_text(sample_article, full=True)
    assert "SECTIONS" in text
    assert "## Types" in text
    assert "Phagocytosis and pinocytosis." in text


def test_format_json_summary(sample_article):
    json_str = format_json(sample_article)
    data = json.loads(json_str)
    assert data["title"] == "Endocytosis"
    assert data["definition"] == "Endocytosis is a cellular process."
    assert "sections" not in data


def test_format_json_full(sample_article):
    json_str = format_json(sample_article, full=True)
    data = json.loads(json_str)
    assert "sections" in data
    assert data["sections"][0]["title"] == "Types"
