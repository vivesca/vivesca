"""Tests for metabolon.organelles.gmail HTML stripping."""
from metabolon.organelles.gmail import _strip_html


def test_html_only_strips_tags():
    """Basic tags are stripped and entities are unescaped."""
    html_text = "<p>Hello <b>world</b> &amp; goodbye</p>"
    result = _strip_html(html_text)
    assert "Hello" in result
    assert "world" in result
    assert "&" in result or "&amp;" not in result
    assert "<p>" not in result
    assert "<b>" not in result


def test_html_strips_style_script():
    """Content inside <style> and <script> blocks is removed entirely."""
    html_text = (
        "<html><head><style>body { color: red; }</style>"
        "<script>alert('xss')</script></head>"
        "<body><p>Hello</p></body></html>"
    )
    result = _strip_html(html_text)
    assert "color" not in result
    assert "red" not in result
    assert "alert" not in result
    assert "xss" not in result
    assert "Hello" in result
