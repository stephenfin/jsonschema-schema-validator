from jsonschema_schema_validator import validator


def test_boolean():
    schema = {'type': 'boolean'}
    validator.validate(schema)
