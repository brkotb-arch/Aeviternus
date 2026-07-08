"""
Core architecture tests.
"""


def test_core_modules_exist():

    from pathlib import Path

    core = Path("core")

    modules = [
        "cognitive_engine.py",
        "memory_router.py",
        "identity_layer.py",
        "mood_engine.py",
    ]

    for module in modules:
        assert (core / module).exists()