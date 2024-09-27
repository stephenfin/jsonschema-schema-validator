import pytest

from jsonschema_schema_validator import exceptions
from jsonschema_schema_validator import validator


def test_additionalProperties_boolean():
    schema = {'type': 'object', 'additionalProperties': True}
    validator.validate(schema)


def test_additionalProperties_schema():
    schema = {
        'type': 'object',
        'additionalProperties': {'type': 'string'},
    }
    validator.validate(schema)


def test_additionalProperties_invalid():
    schema = {
        'type': 'object',
        'additionalProperties': 123,
    }
    with pytest.raises(exceptions.ValidationError) as exc:
        validator.validate(schema)
    assert 'additionalProperties must be a bool or a schema' in str(exc)


def test_required():
    schema = {
        'type': 'object',
        'required': ['foo'],
    }
    validator.validate(schema)


def test_required__invalid():
    schema = {
        'type': 'object',
        'required': 'foo',
    }
    with pytest.raises(exceptions.ValidationError) as exc:
        validator.validate(schema)
    assert 'required must be a list of property names' in str(exc)
