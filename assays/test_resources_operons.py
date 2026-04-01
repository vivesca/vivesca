from __future__ import annotations
import pytest
from unittest.mock import patch
import sys
import types
import builtins

from metabolon.resources.operons import express_operon_map


def test_express_operon_map_import_error():
    """Test that import error returns correct message."""
    original_import = builtins.__import__

    def mocked_import(name, *args, **kwargs):
        if name == "metabolon.operons":
            raise ImportError
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mocked_import):
        result = express_operon_map()
        assert result == "Operon map not available."


class MockOperon:
    """Mock operon for testing."""
    def __init__(self, reaction, product, expressed, precipitation, enzymes=None):
        self.reaction = reaction
        self.product = product
        self.expressed = expressed
        self.precipitation = precipitation
        self.enzymes = enzymes or []


def test_express_operon_map_success():
    """Test operon map generation with mock data."""
    mock_operons = [
        MockOperon(
            reaction="glycolysis",
            product="Glucose degradation pathway",
            expressed=True,
            precipitation="soluble",
            enzymes=["hexokinase", "phosphofructokinase"]
        ),
        MockOperon(
            reaction="gluconeogenesis",
            product="Glucose synthesis from non-carbohydrate precursors",
            expressed=False,
            precipitation="soluble"
        ),
        MockOperon(
            reaction="silica_biomineralization",
            product="Long protein that describes silica biomineralization process with really really long name that should get truncated",
            expressed=True,
            precipitation="crystallised",
            enzymes=["silicatein"]
        ),
    ]
    
    # Create mock module
    mock_module = types.ModuleType("metabolon.operons")
    mock_module.OPERONS = mock_operons
    
    # Save original module and inject mock
    original_module = sys.modules.pop("metabolon.operons", None)
    sys.modules["metabolon.operons"] = mock_module
    
    try:
        result = express_operon_map()
        
        # Check header
        assert "# Operon Map" in result
        assert "**3**" in result
        assert "2 expressed" in result
        assert "1 dormant" in result
        assert "1 crystallised" in result
        
        # Check expressed section
        assert "## Expressed" in result
        assert "glycolysis" in result
        assert "hexokinase" in result
        
        # Check that long product gets truncated to 60 chars + ...
        product_length = len("Long protein that describes silica biomineralization process with really really long name that should get truncated")
        assert product_length > 60
        assert "..." in result
        # Truncated to 60 chars + "...", so total length of product in output is 63
        assert "should get truncated" not in result  # It's beyond 60 chars, so gets cut off
        
        # Check dormant section
        assert "## Dormant" in result
        assert "gluconeogenesis" in result
        
        # Check that crystallised is counted correctly
        crystallised_count = sum(1 for e in mock_operons if e.precipitation == "crystallised")
        assert crystallised_count == 1
        assert str(crystallised_count) in result
    finally:
        # Restore original module
        if original_module is not None:
            sys.modules["metabolon.operons"] = original_module
        else:
            sys.modules.pop("metabolon.operons", None)
