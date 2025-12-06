"""Pytest configuration for OCR tests."""
import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def pytest_addoption(parser):
    """Add command-line options for pytest."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require real credentials"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require real credentials)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests unless --run-integration flag is set."""
    if config.getoption("--run-integration"):
        # --run-integration given in cli: do not skip integration tests
        return

    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
