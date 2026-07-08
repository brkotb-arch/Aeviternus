"""
Runtime system tests.
"""


def test_project_structure():

    from pathlib import Path

    required = [
        "app.py",
        "connect.py",
        "db.py",
        "core",
        "docs"
    ]

    for item in required:
        assert Path(item).exists(), f"Missing {item}"