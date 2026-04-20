"""Tests for epistasis linkage analyzer."""

import tempfile
from pathlib import Path
import sys

# Add the effectors directory to path
sys.path.insert(0, str(Path.home() / "germline" / "effectors" / "epistasis"))

from epistasis import parse_frontmatter, extract_keywords, match_skills_to_epistemics

def test_parse_frontmatter_brackets():
    """Test parsing frontmatter with comma-separated brackets."""
    content = """---
situations: [debug, design, evaluate]
titer-hits: 5
titer-last-seen: 2026-04-15
---
# Content goes here
"""
    result = parse_frontmatter(content)
    assert result['situations'] == {'debug', 'design', 'evaluate'}
    assert result['titer-hits'] == 5
    assert result['titer-last-seen'] == '2026-04-15'

def test_parse_frontmatter_bullets():
    """Test parsing frontmatter with bullet list."""
    content = """
situations:
  - debug
  - test
  - refactor
titer-hits: 0
"""
    result = parse_frontmatter(content)
    assert result['situations'] == {'debug', 'test', 'refactor'}
    assert result['titer-hits'] == 0
    assert result['titer-last-seen'] is None

def test_parse_frontmatter_no_situations():
    """Test parsing when no situations tag exists."""
    content = """# Just content
"""
    result = parse_frontmatter(content)
    assert result['situations'] == set()
    assert result['titer-hits'] == 0

def test_extract_keywords():
    """Test keyword extraction from text."""
    text = "Ribosome testing and debugging"
    keywords = extract_keywords(text)
    assert 'ribosome' in keywords
    assert 'testing' in keywords
    assert 'debugging' in keywords
    # Short words (len <= 3) should be excluded
    assert 'and' not in keywords

def test_matching_algorithm():
    """Test skill-epistemic matching."""
    # Mock epistemics
    epistemics = [
        {
            'situations': {'debug', 'test'},
            'stem_keywords': {'debug', 'utils'},
            'stem': 'debug-utils',
            'filename': 'debug-utils.md'
        },
        {
            'situations': {'design', 'architecture'},
            'stem_keywords': {'design', 'patterns'},
            'stem': 'design-patterns',
            'filename': 'design-patterns.md'
        }
    ]
    
    # Mock skills
    skills = [
        {
            'name': 'debugging',
            'keywords': {'debug', 'testing', 'ribosome'}
        },
        {
            'name': 'system-design',
            'keywords': {'design', 'architecture', 'patterns'}
        }
    ]
    
    matches = match_skills_to_epistemics(skills, epistemics)
    
    # Debugging skill should match first epistemic with score 2 (debug + test)
    assert 'debugging' in matches
    debug_matches = matches['debugging']
    assert len(debug_matches) == 1
    assert debug_matches[0][0]['stem'] == 'debug-utils'
    assert debug_matches[0][1] == 2
    
    # System design should match second epistemic with score 4
    assert 'system-design' in matches
    design_matches = matches['system-design']
    assert len(design_matches) == 1
    assert design_matches[0][0]['stem'] == 'design-patterns'
    assert design_matches[0][1] == 4

def test_titer_parsing():
    """Test titer data parsing from frontmatter."""
    content = """---
situations: [analysis]
titer-hits: 12
titer-last-seen: 2026-04-10
---
"""
    result = parse_frontmatter(content)
    assert result['titer-hits'] == 12
    assert result['titer-last-seen'] == '2026-04-10'

def test_no_titer_data():
    """Test default values when no titer data."""
    content = """situations: [refactor]"""
    result = parse_frontmatter(content)
    assert result['titer-hits'] == 0
    assert result['titer-last-seen'] is None

if __name__ == '__main__':
    # Run all tests
    tests = [
        test_parse_frontmatter_brackets,
        test_parse_frontmatter_bullets,
        test_parse_frontmatter_no_situations,
        test_extract_keywords,
        test_matching_algorithm,
        test_titer_parsing,
        test_no_titer_data,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print(f"✓ {test.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} FAILED: {e}")
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(failed)
