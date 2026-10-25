import json

import pytest
from scripts.check_promotion import main


@pytest.mark.parametrize("text", ['{"x": NaN}', '{"x": Infinity}', '{"x": 1, "x": 2}', '{'])
def test_invalid_json_is_negative(tmp_path, capsys, text):
    path = tmp_path / "card.json"
    path.write_text(text)
    assert main([str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["submission_ready"] is False


def test_negative_card_exit_status(tmp_path, capsys):
    path = tmp_path / "card.json"
    path.write_text('{}')
    assert main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["slot_selected"] is False


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "absent")]) == 2
    assert json.loads(capsys.readouterr().out)["verdict"] == "negative"


def test_schema_pass_is_not_upload_authorization(tmp_path, capsys):
    from tests.test_promotion import complete_card

    path = tmp_path / "schema-only.json"
    path.write_text(json.dumps(complete_card()))
    assert main([str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["evidence_schema_passed"] is True
    assert result["submission_ready"] is False
    assert result["slot_selected"] is False
