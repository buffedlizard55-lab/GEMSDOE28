"""Strict evidence JSON: reject ambiguous keys and non-finite numeric values."""
from __future__ import annotations

import json
import math


def reject_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Non-finite JSON number: {value}")
    return number


def loads(text):
    """Parse without last-key-wins behavior or exponent-overflow infinity."""
    return json.loads(text, parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_keys)
