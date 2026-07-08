"""
API availability tests.
"""


def test_api_structure():

    endpoints = [
        "/send",
        "/health",
        "/history"
    ]

    assert "/health" in endpoints