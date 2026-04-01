from __future__ import annotations
import pytest
from unittest.mock import patch
import sys

from metabolon.resources.operons import express_operon_map


def test_express_operon_map_import_error():
    """Test that import error returns correct message."""
    # Remove metabolon.operons from sys.modules to force ImportError
    original_module = sys.modules.pop("metabolon.operons", None)
    try:
        result = express_operon_map()
        assert result == "Operon map not available."
    finally:
        if original_module is not None:
            sys.modules["metabolon.operons"] = original_module


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
    
    with patch("metabolon.resources.operons.OPERONS", mock_operons):
        result = express_operon_map()
        
        # Check header
        assert "# Operon Map" in result
        assert "3 operons: 2 expressed, 1 dormant, 1 crystallised" in result
        
        # Check expressed section
        assert "## Expressed" in result
        assert "| **glycolysis** | Glucose degradation pathway | soluble | `hexokinase`, `phosphofructokinase` |" in result
        # Check that long product gets truncated to 60 chars + ...
        assert "Long protein that describes silica biomineralization process with really really long name that sho..." in result
        
        # Check dormant section
        assert "## Dormant" in result
        assert "| **gluconeogenesis** | Glucose synthesis from non-carbohydrate precursors | soluble |" in result
        
        # Check all expected columns are present
        assert "| Operon | Product | Precipitation | Enzymes |" in result
        assert "|--------|---------|---------------|---------|" in result
