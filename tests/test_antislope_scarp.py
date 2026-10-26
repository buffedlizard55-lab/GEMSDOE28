from __future__ import annotations

import numpy as np
import pytest

from gems27.antislope_scarp import build_surface, decode_linear_rank, decode_sqrt_rank


def test_quantization_decoders_respect_missing_and_endpoints() -> None:
    q = np.array([0, 1, 255], dtype=np.uint8)
    assert decode_sqrt_rank(q).tolist() == [0.0, 0.0, 1.0]
    assert decode_linear_rank(q).tolist() == [0.0, 0.0, 1.0]


def test_surface_requires_every_physical_leg_and_valid_lidar() -> None:
    full = np.full((2, 3), 255, dtype=np.uint8)
    surface, legs = build_surface(*([full] * 8))
    assert set(legs) == {"step_strength", "curvature_pair", "antislope_selectivity", "coherence"}
    # Equal up/down/cross faces give antislope selectivity 1/3.
    assert np.allclose(legs["antislope_selectivity"], 1 / 3)
    assert np.all(surface > 0)

    for index in (0, 1, 2, 4, 6, 7):
        bands = [full.copy() for _ in range(8)]
        bands[index][0, 0] = 0
        changed, _ = build_surface(*bands)
        assert changed[0, 0] == 0


def test_surface_rejects_misaligned_inputs() -> None:
    good = np.ones((2, 2), dtype=np.uint8)
    bad = np.ones((3, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="aligned"):
        build_surface(good, good, good, good, good, good, good, bad)
