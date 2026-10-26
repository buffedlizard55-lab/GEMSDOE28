"""Evidence readers must reject ambiguity before any experiment or promotion."""
import pytest

from gems27.evidence_json import loads


@pytest.mark.parametrize("text", [
    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}',
    '{"x":-1e999}', '{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
])
def test_reject_ambiguous_evidence(text):
    with pytest.raises(ValueError):
        loads(text)


def test_preserve_valid_json_types():
    assert loads('{"x":0.2,"y":[true,null,42]}') == {"x": 0.2, "y": [True, None, 42]}
