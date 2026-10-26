from copy import deepcopy

import pytest

from gems27.promotion import promotion_gate


def complete_card():
    return dict(lane="fixture only", raster_sha256="a" * 64, submission_name="fixture",
                note="Test only", hypothesis="h", mechanism="m", non_fault_mimic="dike",
                holdout=dict(raster_sha256="a" * 64, baseline_sha256="c" * 64, label="HOLDOUT-DTI", evaluator_version="gems-segment-pooled-v1", withheld_positives=10,
                             dti=0.2, ci95=[0.1, 0.3], baseline_dti=0.195, paired_gain=0.005,
                             paired_gain_ci95=[0.001, 0.01],
                             whole_segments=True, buffered=True, visible_only_features=True,
                             pixel_exact_visible_mask=True, pooled=True, alpha=0.2, beta=0.8,
                             kernel_m=300, kernel="triangular"),
                feature_names=["f"], feature_canaries={"f": 0.7}, registry=dict(complete=True, manifest_sha256="b" * 64, members=["d" * 64],
                surface=[dict(raster_sha256="d" * 64, spearman=0.4, within_3px_fraction=0.2)],
                dots=[dict(raster_sha256="d" * 64, spearman=0.3, within_3px_fraction=0.4)]),
                validator=dict(raster_sha256="a" * 64, no_nan_inside=True, range_0_1=True,
                               crs_match=True, shape_match=True, transform_match=True, single_band=True))


def test_missing_evidence_fails_closed():
    assert not promotion_gate({})["promotion_eligible"]


def test_complete_schema_does_not_select_slot():
    result = promotion_gate(complete_card())
    assert result["verdict"] == "promote"
    assert result["slot_selected"] is False
    assert result["submission_ready"] is False


@pytest.mark.parametrize("stage", ["surface", "dots"])
@pytest.mark.parametrize("field,value", [("spearman", 0.90001), ("within_3px_fraction", 0.70001),
                                        ("spearman", float("nan")), ("spearman", None)])
def test_duplicate_or_unmeasured_fails(stage, field, value):
    card = complete_card()
    card["registry"][stage][0][field] = value
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("auc", [0.91, float("nan"), float("inf"), -1, True])
def test_canaries(auc):
    card = complete_card()
    card["feature_canaries"]["f"] = auc
    assert not promotion_gate(card)["promotion_eligible"]


def test_missing_each_required_field_fails():
    card = complete_card()
    for field in card:
        changed = deepcopy(card)
        del changed[field]
        assert not promotion_gate(changed)["promotion_eligible"], field


def test_exact_protocol_boundaries():
    card = complete_card()
    card["feature_canaries"]["f"] = 0.90
    card["registry"]["surface"][0].update(spearman=0.90, within_3px_fraction=0.70)
    assert promotion_gate(card)["promotion_eligible"]
    card["holdout"]["paired_gain_ci95"] = [0, 0.01]
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("value", [None, [], "invalid", 1, True])
def test_malformed_card_fails_closed(value):
    assert promotion_gate(value)["verdict"] == "negative"


@pytest.mark.parametrize("section", ["holdout", "registry", "validator"])
@pytest.mark.parametrize("value", [[], "invalid", 1, True])
def test_malformed_sections_fail_closed(section, value):
    card = complete_card()
    card[section] = value
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("stage", ["surface", "dots"])
@pytest.mark.parametrize("value", [[None], ["invalid"], [1]])
def test_malformed_comparison_fails_closed(stage, value):
    card = complete_card()
    card["registry"][stage] = value
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("stage", ["surface", "dots"])
def test_missing_extra_and_repeated_registry_comparisons(stage):
    for mode in ("missing", "extra", "repeated", "wrong"):
        card = complete_card()
        if mode == "missing":
            card["registry"]["members"].append("e" * 64)
        elif mode == "extra":
            comparison = dict(card["registry"][stage][0], raster_sha256="e" * 64)
            card["registry"][stage].append(comparison)
        elif mode == "repeated":
            card["registry"][stage] *= 2
        else:
            card["registry"][stage][0]["raster_sha256"] = "e" * 64
        assert not promotion_gate(card)["promotion_eligible"], mode


@pytest.mark.parametrize("members", [None, [], ["bad"], [None], ["d" * 64, "d" * 64]])
def test_invalid_registry_inventory(members):
    card = complete_card()
    card["registry"]["members"] = members
    assert not promotion_gate(card)["promotion_eligible"]


def test_extreme_json_integer_is_negative_not_exception():
    card = complete_card()
    card["holdout"]["dti"] = 10 ** 1000
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("auc", [0.0, 0.01, 0.099999])
def test_inverted_leakage_does_not_evade_gate(auc):
    card = complete_card()
    card["feature_canaries"]["f"] = auc
    assert promotion_gate(card)["verdict"] == "negative"


def test_surface_does_not_require_impossible_preplacement_dot_overlap():
    card = complete_card()
    card["registry"]["surface"][0]["within_3px_fraction"] = None
    assert promotion_gate(card)["promotion_eligible"]
    card["registry"]["dots"][0]["within_3px_fraction"] = None
    assert not promotion_gate(card)["promotion_eligible"]


def test_negative_rank_duplicate_is_rejected_conservatively():
    card = complete_card()
    card["registry"]["surface"][0]["spearman"] = -0.90001
    assert not promotion_gate(card)["promotion_eligible"]


@pytest.mark.parametrize("field", ["lane", "submission_name", "hypothesis", "mechanism", "non_fault_mimic"])
@pytest.mark.parametrize("value", [True, {"not": "text"}, ["not text"], " "])
def test_required_text_cannot_be_replaced_by_truthy_containers(field, value):
    card = complete_card()
    card[field] = value
    assert not promotion_gate(card)["promotion_eligible"]


def test_schema_success_always_withholds_upload_authorization():
    # This checker has no raster/template path and cannot verify bytes or select a slot.
    card = complete_card()
    for status in (None, True, False, "approved"):
        card["submission_ready"] = status
        card["selector_approved"] = status
        result = promotion_gate(card)
        assert result["evidence_schema_passed"] is True
        assert result["submission_ready"] is False
        assert result["slot_selected"] is False


@pytest.mark.parametrize("card", [complete_card(), {}, []])
def test_concurrent_schema_api_names_are_consistent_without_granting_a_slot(card):
    result = promotion_gate(card)
    assert result['evidence_schema_passed'] is result['promotion_eligible']
    assert result['submission_ready'] is False
    assert result['slot_selected'] is False


@pytest.mark.parametrize("baseline,gain,ci", [
    (None, 0.005, [0.001, 0.01]),
    (0.25, 0.005, [0.001, 0.01]),  # a winning interval cannot rescue a worse point score
    (0.195, 0.004, [0.001, 0.01]),  # inconsistent paired difference
    (0.195, 0.005, [0.006, 0.01]),  # interval does not contain the reported gain
])
def test_paired_gain_is_bound_to_a_comparable_baseline(baseline, gain, ci):
    card = complete_card()
    card["holdout"].update(baseline_dti=baseline, paired_gain=gain, paired_gain_ci95=ci)
    assert not promotion_gate(card)["promotion_eligible"]


def test_canaries_must_cover_every_model_feature():
    card = complete_card()
    card["feature_names"].append("omitted_or_missingness_indicator")
    assert not promotion_gate(card)["promotion_eligible"]
    card["feature_canaries"]["omitted_or_missingness_indicator"] = 0.5
    assert promotion_gate(card)["promotion_eligible"]
    card["feature_canaries"]["not_a_feature"] = 0.5
    assert not promotion_gate(card)["promotion_eligible"]


def test_noncomparable_evaluator_cannot_promote():
    card = complete_card()
    card["holdout"]["evaluator_version"] = "gems27-sparse-quadrant-legacy"
    assert not promotion_gate(card)["promotion_eligible"]
