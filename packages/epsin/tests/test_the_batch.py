from pathlib import Path

import pytest

from epsin.extractors.the_batch import TheBatchExtractor
from epsin.models import Source


THE_BATCH_HTML = """<!DOCTYPE html>
<html><body>
<div class="post-card">
  <a href="/the-batch/issue-123/">
    <h3>AI Advances in 2026</h3>
  </a>
</div>
<div class="post-card">
  <a href="/the-batch/issue-122/">
    <h3>New Model Releases This Week</h3>
  </a>
</div>
</body></html>
"""


def test_the_batch_extractor_parses_cards():
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(THE_BATCH_HTML, "html.parser")
    cards = soup.select(".post-card")
    assert len(cards) == 2


def test_the_batch_source_snake_name():
    source = Source(name="The Batch", url="https://www.deeplearning.ai/the-batch/", tags=["ai"])
    assert source.snake_name == "the_batch"


def test_extractor_exists():
    from epsin.extractors import resolve
    source = Source(name="The Batch", url="https://www.deeplearning.ai/the-batch/", tags=["ai"])
    extractor = resolve(source)
    assert isinstance(extractor, TheBatchExtractor)
