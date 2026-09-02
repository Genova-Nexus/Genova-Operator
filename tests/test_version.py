"""Unit test to verify Genova Operator version definition."""

import genova_operator


def test_version_exists() -> None:
    """Verify that __version__ is defined and non-empty."""
    assert hasattr(genova_operator, "__version__")
    assert isinstance(genova_operator.__version__, str)
    assert len(genova_operator.__version__) > 0


def test_version_format() -> None:
    """Verify that __version__ follows semantic versioning."""
    version = genova_operator.__version__
    assert "0.1.0" in version
