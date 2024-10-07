import pytest

from jsonschema_schema_validator import exceptions
from jsonschema_schema_validator import validator


@pytest.mark.parametrize(
    'schema',
    [
        {'additionalProperties': True},
        {'additionalProperties': {'type': 'string'}},
        {'patternProperties': {r'^S_': {'type': 'string'}}},
        {'propertyNames': {'type': 'string', 'enum': ['a', 'b']}},
        {'propertyNames': {'enum': ['a', 'b']}},
        {'maxProperties': 999},
        {'minProperties': 1},
        {'required': ['foo']},
    ],
)
def test_valid(schema):
    schema = {'type': 'object', **schema}
    validator._validate_object(schema)


@pytest.mark.parametrize(
    'schema',
    [
        {'additionalProperties': 123},
        {'patternProperties': 'a string'},
        {'patternProperties': {'\\z': {'type': 'string'}}},
        {'patternProperties': {r'^S_': 'a string'}},
        {'propertyNames': {'type': 'boolean'}},
        {'maxProperties': '999'},
        {'maxProperties': -1},
        {'minProperties': '1'},
        {'minProperties': -1},
        {'required': 'foo'},
    ],
)
def test_invalid(schema):
    schema = {'type': 'object', **schema}
    with pytest.raises(exceptions.ValidationError):
        validator._validate_object(schema)


def test_invalid_type():
    schema = {
        'type': 'string',
    }
    with pytest.raises(RuntimeError) as exc:
        validator._validate_object(schema)
    assert "'type' must be 'object'" in str(exc)
