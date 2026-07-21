# core/identity_layer.py

import json

IDENTITY_PATH = "DI_CORE/IDENTITY.txt"

identity_weights = {
    "warmth": 0.5,
    "edge": 0.5,
    "curiosity": 0.5,
    "stability": 0.5
}

def load_identity():
    with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def update_identity_from_mood(mood):

    if mood == "positive":
        identity_weights["warmth"] += 0.02

    if mood == "negative":
        identity_weights["edge"] += 0.03
        identity_weights["warmth"] -= 0.01

    if mood == "curious":
        identity_weights["curiosity"] += 0.03

    normalize()


def normalize():
    for k in identity_weights:
        identity_weights[k] = max(0.0, min(1.0, identity_weights[k]))


def get_identity_overlay():
    """
    НЕ заменяет IDENTITY.txt
    только влияет на поведение
    """
    return identity_weights

def get_identity_snapshot():

    return identity_weights.copy()