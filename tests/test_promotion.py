from copy import deepcopy

import pytest

from gems27.promotion import promotion_gate


def complete_card():
    return dict(lane="fixture only", raster_sha256="a" * 64, submission_name="fixture",
                note="Test only", hypothesis="h", mechanism="m", non_fault_mimic="dike",
                holdout=dict(raster_sha256="a" * 64, baseline_sha256="c" * 64, label="HOLDOUT-DTI", evaluator_version="fixture-v1", withheld_positives=10,
                             dti=0.2, ci95=[0.1, 0.3], paired_gain_ci95=[0.001, 0.01],
                             whole_segments=True, buffered=True, visible_only_features=True,
                             pixel_exact_visible_mask=True, pooled=True, alpha=0.2, beta=0.8,
                             kernel_m=300, kernel="triangular"),
                feature_canaries={"f": 0.7}, registry=dict(complete=True, manifest_sha256="b" * 64,
                surface=[dict(raster_sha256="d" * 64, spearman=0.4, within_3px_fraction=0.2)],
                dots=[dict(raster_sha256="d" * 64, spearman=0.3, within_3px_fraction=0.4)]),
                validator=dict(raster_sha256="a" * 64, no_nan_inside=True, range_0_1=True,
                               crs_match=True, shape_match=True, transform_match=True, single_band=True))


def test_missing_evidence_fails_closed():
    assert not promotion_gate({})["submission_ready"]


def test_complete_schema_does_not_select_slot():
    result = promotion_gate(complete_card())
    assert result["verdict"] == "promote"
    assert result["slot_selected"] is False


@pytest.mark.parametrize("stage", ["surface", "dots"])
@pytest.mark.parametrize("field,value", [("spearman", 0.90001), ("within_3px_fraction", 0.70001),
                                        ("spearman", float("nan")), ("spearman", None)])
def test_duplicate_or_unmeasured_fails(stage, field, value):
    card = complete_card()
    card["registry"][stage][0][field] = value
    assert not promotion_gate(card)["submission_ready"]


@pytest.mark.parametrize("auc", [0.91, float("nan"), float("inf"), -1, True])
def test_canaries(auc):
    card = complete_card()
    card["feature_canaries"]["f"] = auc
    assert not promotion_gate(card)["submission_ready"]


def test_missing_each_required_field_fails():
    card = complete_card()
    for field in card:
        changed = deepcopy(card)
        del changed[field]
        assert not promotion_gate(changed)["submission_ready"], field


def test_exact_protocol_boundaries():
    card = complete_card()
    card["feature_canaries"]["f"] = 0.90
    card["registry"]["surface"][0].update(spearman=0.90, within_3px_fraction=0.70)
    assert promotion_gate(card)["submission_ready"]
    card["holdout"]["paired_gain_ci95"] = [0, 0.01]
    assert not promotion_gate(card)["submission_ready"]
