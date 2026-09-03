import importlib.util
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "delegation" / "scripts" / "validate_contract.py"
SPEC = importlib.util.spec_from_file_location("contract_validation", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_empty_contract_lists_required_fields():
    assert any(message.startswith("missing fields") for message in MODULE.errors({}))


def test_example_contract_is_valid():
    import json

    example = PATH.parents[1] / "contracts" / "example.json"
    assert MODULE.errors(json.loads(example.read_text())) == []
