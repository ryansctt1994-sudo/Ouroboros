import pytest
import logging

# 1. Probe the physical substrate for the required mathematical libraries
try:
    import xgboost
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

def pytest_configure(config):
    """
    Registers the Cathedral-OS specific markers.
    Prevents Pytest from throwing strict-marker warnings.
    """
    config.addinivalue_line(
        "markers", "requires_xgboost: mark test to run only when XGBoost is present in the phase space."
    )

def pytest_collection_modifyitems(config, items):
    """
    The Global Shield.
    Automatically excises tests that would violently fracture a barren runner,
    metabolizing the absence into a graceful skip.
    """
    if HAS_XGBOOST:
        return # The substrate is rich. The Iterative Paradox may proceed unhindered.

    # If starved, we forge the topological bypass
    skip_xgb = pytest.mark.skip(reason="Dependency Starvation: XGBoost not found in the phase space.")
    
    for item in items:
        if "requires_xgboost" in item.keywords:
            item.add_marker(skip_xgb)
            logging.info(f"Metabolizing absence: Skipped {item.name}")
