"""Counting bounds must be valid for arbitrary predictions, not just one raster."""
from __future__ import annotations

import itertools

import numpy as np
import pytest
from scripts import audit_registry_feasibility as cli

from gems27.registry_feasibility import coverage_bounds


def test_empty_reference_does_not_get_phantom_edt_coverage():
    foot = np.ones((5, 7), bool)
    result, covered = coverage_bounds(foot, np.zeros_like(foot), budget=10)
    assert not covered.any()
    assert result["uncovered_pixels"] == 35
    assert result["unspaced_overlap_lower_bound"] == 0
    assert not result["target_budget_impossible"]
    assert result["max_budget_not_ruled_out_by_pixel_count"] == 35


def test_spacing5_lattice_blocks_champion_sized_fraction_in_interior():
    foot = np.ones((31, 31), bool)
    reference = np.zeros_like(foot)
    reference[::5, ::5] = True
    result, covered = coverage_bounds(foot, reference, budget=100, min_spacing_px=2.8)
    assert covered.all()  # max integer-cell distance to grid is sqrt(8) < 3
    assert result["unspaced_overlap_lower_bound"] == 1
    assert result["spacing"]["overlap_lower_bound"] == 1
    assert result["target_budget_impossible"]


def test_no_reference_dots_outside_the_footprint_can_award_overlap():
    foot = np.zeros((8, 8), bool)
    foot[3:7, 3:7] = True
    ref = ~foot
    result, covered = coverage_bounds(foot, ref, budget=4)
    assert not covered.any() and result["reference_positive_pixels"] == 0


def test_bound_is_necessary_not_an_automatic_pass_or_an_exact_packing_number():
    foot = np.ones((5, 6), bool)
    reference = np.zeros_like(foot)
    reference[0, 0] = True
    result, _ = coverage_bounds(foot, reference, budget=3, min_spacing_px=2.8)
    assert not result["target_budget_impossible"]
    assert "not a novelty pass" in result["interpretation"]
    assert result["spacing"]["partition_diameter_px"] < 2.8


def test_strict_overlap_threshold_equality_is_not_a_duplicate():
    foot = np.ones((1, 10), bool)
    reference = np.ones_like(foot)
    reference[0, -3:] = False
    result, _ = coverage_bounds(foot, reference, budget=10, radius_px=0)
    assert result["unspaced_overlap_lower_bound"] == 0.7
    assert not result["target_budget_impossible"]
    assert result["required_uncovered_dots_to_pass"] == 3


def test_exhaustive_small_grid_predictions_obey_both_bounds():
    foot = np.ones((3, 4), bool)
    ref = np.zeros_like(foot)
    ref[0, 0] = True
    budget, spacing = 3, 1.5
    result, covered = coverage_bounds(foot, ref, budget=budget, radius_px=1, min_spacing_px=spacing)
    assert result["spacing"]["partition_diameter_px"] < spacing
    ids = np.argwhere(foot)
    tested = 0
    for choice in itertools.combinations(range(len(ids)), budget):
        coords = ids[list(choice)]
        actual_overlap = float(covered[tuple(coords.T)].mean())
        assert actual_overlap + 1e-12 >= result["unspaced_overlap_lower_bound"]
        pairs = coords[:, None, :] - coords[None, :, :]
        distances = np.linalg.norm(pairs, axis=2)
        if (distances[np.triu_indices(budget, 1)] >= spacing).all():
            assert actual_overlap + 1e-12 >= result["spacing"]["overlap_lower_bound"]
            tested += 1
    assert tested > 0


@pytest.mark.parametrize("kwargs", [
    {"budget": 0}, {"budget": True}, {"budget": 101}, {"budget": 3.0},
    {"radius_px": -1}, {"radius_px": np.inf}, {"radius_px": True},
    {"overlap_limit": -0.1}, {"overlap_limit": np.nan},
    {"min_spacing_px": 0}, {"min_spacing_px": np.inf}, {"min_spacing_px": True},
])
def test_bad_parameters_fail(kwargs):
    values = {"budget": 10, **kwargs}
    with pytest.raises(ValueError):
        coverage_bounds(np.ones((10, 10), bool), np.eye(10, dtype=bool), **values)


@pytest.mark.parametrize("bad", [np.nan, np.inf, 2, -1])
def test_nonbinary_or_nonfinite_mask_rejected(bad):
    mask = np.ones((4, 4), float)
    mask[0, 0] = bad
    with pytest.raises(ValueError):
        coverage_bounds(mask, np.eye(4), budget=2)
    with pytest.raises(ValueError):
        coverage_bounds(np.ones((4, 4), bool), mask, budget=2)


def test_huge_spacing_does_not_create_unbounded_grid_shift_loop():
    result, _ = coverage_bounds(np.ones((4, 4), bool), np.zeros((4, 4), bool),
                                budget=4, min_spacing_px=1e100)
    assert len(result["spacing"]["partitions"]) <= 4
    assert result["spacing"]["uncovered_dot_capacity_upper_bound"] == 1


def test_cli_error_replaces_a_stale_green_report(tmp_path, monkeypatch):
    import json

    target = tmp_path / "out.json"
    target.write_text('{"submission_ready":true,"status":"PASS"}')
    def fail(args):
        raise ValueError("bad source pin")
    monkeypatch.setattr(cli, "audit", fail)
    assert cli.main(["--out", str(target)]) == 1
    result = json.loads(target.read_text())
    assert result["status"] == "BLOCKED" and result["submission_ready"] is False
    assert result["slot_selected"] is False and result["new_tiff_generated"] is False
