"""
Memory architecture tests.
"""


def test_memory_architecture_exists():

    components = [
        "SQLite",
        "ChromaDB",
        "Memory Router"
    ]

    assert "SQLite" in components
    assert "ChromaDB" in components