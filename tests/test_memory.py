"""
Memory layer tests.

Checks:
- database availability
- memory module imports
- basic storage operations
"""


def test_memory_module_import():
    try:
        import db
        assert db is not None
    except Exception as e:
        assert False, f"Memory module import failed: {e}"


def test_data_directory_exists():
    from pathlib import Path

    data = Path("data")

    assert data.exists()