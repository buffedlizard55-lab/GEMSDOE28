"""One shared contract for prepared-feature missingness, without imputing the cache.

Missing LiDAR/source coverage is represented by NaN in the existing preparation
pipeline. HistGradientBoosting accepts missing values; infinity is never allowed.
A declared NaN mask/count is not evidence that a geological model is leakage-free.
"""
from __future__ import annotations

import numpy as np

POLICY = "preserve-source-nodata-v1"


def missingness_counts(array, names, *, chunk_rows=65536):
    if (not isinstance(array, np.ndarray) or array.ndim != 2 or not array.shape[0]
            or not isinstance(names, list) or not names or len(names) != array.shape[1]
            or not all(isinstance(x, str) and x for x in names) or len(set(names)) != len(names)):
        raise ValueError("Nonempty 2-D feature array and unique column names required")
    if (isinstance(chunk_rows, bool) or not isinstance(chunk_rows, int) or chunk_rows < 1
            or array.dtype != np.dtype("float32")):
        raise ValueError("Positive chunk size and float32 cache required")
    counts = np.zeros((3, len(names)), dtype=np.int64)
    for start in range(0, len(array), chunk_rows):
        part = array[start:start + chunk_rows]
        counts[0] += np.isfinite(part).sum(axis=0)
        counts[1] += np.isnan(part).sum(axis=0)
        counts[2] += np.isinf(part).sum(axis=0)
    return {
        "policy": POLICY,
        "imputed": False,
        "bands": {
            name: {"finite": int(counts[0, i]), "nan": int(counts[1, i]), "infinity": int(counts[2, i])}
            for i, name in enumerate(names)
        },
    }


def validate_missingness(array, names, declared=None):
    """Verify all cells. Undeclared NaN, any infinity or all-missing columns fail.

    Finite legacy caches may omit the new declaration. Existing NaN caches must
    be re-described by the shared prepare_data.py path, not privately imputed.
    """
    actual = missingness_counts(array, names)
    bands = actual["bands"]
    failures = []
    if any(x["infinity"] for x in bands.values()):
        failures.append("Cached feature stack contains NaN or infinity")
    if any(not x["finite"] for x in bands.values()):
        failures.append("Cached feature stack contains an all-missing feature")
    if declared is None:
        if any(x["nan"] for x in bands.values()):
            failures.append("Cached feature stack contains NaN or infinity")
    else:
        valid = (isinstance(declared, dict) and declared.get("policy") == POLICY
                 and declared.get("imputed") is False and isinstance(declared.get("bands"), dict)
                 and set(declared["bands"]) == set(names))
        if valid:
            for stats in declared["bands"].values():
                valid = valid and (isinstance(stats, dict) and set(stats) == {"finite", "nan", "infinity"}
                                   and all(type(x) is int and x >= 0 for x in stats.values()))
        if not valid or declared != actual:
            failures.append("Cached feature missingness declaration does not match every band")
    return {"passed": not failures, "failures": failures, "actual": actual}
