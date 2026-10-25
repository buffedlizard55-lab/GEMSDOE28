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
