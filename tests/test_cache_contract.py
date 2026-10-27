"""Prepared-feature NaN is not a submission NaN; never silently impute either."""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from gems27.cache_contract import missingness_counts, validate_missingness


def fixture():
    array = np.array([[1, np.nan], [np.nan, 2], [3, 4]], dtype=np.float32)
    return array, ["field_a", "lidar_b"]


def test_declared_source_nodata_passes_without_changing_any_value():
    array, names = fixture()
    before = array.tobytes()
    declaration = missingness_counts(array, names, chunk_rows=1)
    assert declaration["imputed"] is False
    assert declaration["bands"]["lidar_b"] == {"finite": 2, "nan": 1, "infinity": 0}
    assert validate_missingness(array, names, declaration)["passed"]
    assert array.tobytes() == before


def test_undeclared_nan_fails_but_finite_legacy_cache_still_works():
    array, names = fixture()
    assert not validate_missingness(array, names)["passed"]
    assert validate_missingness(np.nan_to_num(array), names)["passed"]


@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_even_declared_infinity_cannot_pass(value):
    array, names = fixture()
    array[0, 0] = value
    assert not validate_missingness(array, names, missingness_counts(array, names))["passed"]


def test_all_missing_feature_rejected_even_with_matching_metadata():
    array, names = fixture()
    array[:, 0] = np.nan
    result = validate_missingness(array, names, missingness_counts(array, names))
    assert not result["passed"]
    assert any("all-missing" in reason for reason in result["failures"])


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(policy="impute"),
    lambda x: x.update(imputed=True),
    lambda x: x["bands"]["field_a"].update(nan=0),
    lambda x: x["bands"]["field_a"].update(nan=True),
    lambda x: x["bands"].pop("field_a"),
    lambda x: x["bands"].update(extra={"finite": 3, "nan": 0, "infinity": 0}),
])
def test_declaration_must_match_actual_per_band_counts_and_types(mutation):
    array, names = fixture()
    declaration = deepcopy(missingness_counts(array, names))
    mutation(declaration)
    assert not validate_missingness(array, names, declaration)["passed"]


@pytest.mark.parametrize("array,names", [
    (np.zeros((2, 2), np.float64), ["a", "b"]),
    (np.zeros((0, 2), np.float32), ["a", "b"]),
    (np.zeros((2, 0), np.float32), []),
    (np.zeros((2, 2), np.float32), ["a", "a"]),
    (np.zeros((2, 2), np.float32), ["a"]),
    (np.zeros((2, 2), np.float32), ["a", ""]),
])
def test_bad_cache_contract_raises(array, names):
    with pytest.raises(ValueError):
        missingness_counts(array, names)
