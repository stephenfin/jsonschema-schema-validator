import pytest

from jsonschema_schema_validator import exceptions
from jsonschema_schema_validator import validator


def test_integer():
    schema = {'type': 'integer'}
    validator.validate(schema)


def test_integer__valid_properties():
    schema = {'type': 'integer', 'minimum': 0, 'maximum': 1}
    validator.validate(schema)


def test_integer__invalid_properties():
    schema = {'type': 'integer', 'minimumm': 0}
    with pytest.raises(exceptions.ValidationError) as exc:
        validator.validate(schema)
    assert 'Invalid keywords: ' in str(exc)
