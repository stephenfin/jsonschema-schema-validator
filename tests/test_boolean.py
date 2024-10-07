import pytest

from jsonschema_schema_validator import validator


def test_basics():
    schema = {'type': 'boolean'}
    validator._validate_boolean(schema)


def test_invalid_type():
    schema = {'type': 'integer'}
    with pytest.raises(RuntimeError) as exc:
        validator._validate_boolean(schema)
    assert "'type' must be 'boolean'" in str(exc)
