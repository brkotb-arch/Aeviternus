"""
Identity layer tests.
"""


def test_identity_core():

    identity = {
        "name": "Aeviternus",
        "layer": "identity"
    }

    assert identity["name"] == "Aeviternus"
    assert identity["layer"] == "identity"