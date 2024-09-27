import collections.abc

from jsonschema_schema_validator import exceptions


TValidator = collections.abc.Callable[[dict[str, object]], None]


def valid_keywords(
    valid_keywords: list[str],
) -> collections.abc.Callable[[TValidator], TValidator]:
    def wrapper(fn: TValidator) -> TValidator:
        def inner(schema: dict[str, object]) -> None:
            if len(set(schema)) < len(list(schema)):
                raise exceptions.ValidationError('Duplicate keywords')

            if invalid_keywords := set(schema) - set(valid_keywords):
                raise exceptions.ValidationError(
                    f'Invalid keywords: {invalid_keywords}'
                )

            return fn(schema)

        return inner

    return wrapper


def _validate_object_additionalProperties(prop: object) -> None:
    if isinstance(prop, bool):
        return
    elif isinstance(prop, dict):
        return _validate_schema(prop)

    raise exceptions.ValidationError(
        'additionalProperties must be a bool or a schema'
    )


def _validate_object_properties(prop: object) -> None:
    if not isinstance(prop, dict):
        raise exceptions.ValidationError(
            'properties must be a mapping of property names to schemas'
        )

    # TODO(stephenfin): We should probably warn about suspicious looking
    # properties like 'properties' or any other keyword, but the infrastructure
    # isn't there for that yet

    for schema in prop.values():
        _validate_schema(schema)


def _validate_object_patternProperties(prop: object) -> None:
    if not isinstance(prop, dict):
        raise exceptions.ValidationError(
            'patternProperties must be a mapping of property name patterns '
            'to schemas'
        )

    for schema in prop.values():
        _validate_schema(schema)


def _validate_object_propertyNames(prop: object) -> None:
    if not isinstance(prop, dict) or prop.get('type', 'string') != 'string':
        raise exceptions.ValidationError(
            'propertyNames must be a schema with type string'
        )

    if 'type' not in prop:
        # "type": "string" is implied
        prop = {**prop, 'type': 'string'}
    _validate_string(prop)


def _validate_object_maxProperties(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            'maxProperties must be a non-negative integer'
        )


def _validate_object_minProperties(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            'minProperties must be a non-negative integer'
        )


def _validate_object_required(prop: object) -> None:
    if not isinstance(prop, list) or any(not isinstance(x, str) for x in prop):
        raise exceptions.ValidationError(
            'required must be a list of property names'
        )


@valid_keywords(
    [
        'additionalProperties',
        'properties',
        'patternProperties',
        'propertyNames',
        'maxProperties',
        'minProperties',
        'required',
        'type',
    ]
)
def _validate_object(schema: dict[str, object]) -> None:
    if schema.get('additionalProperties'):
        _validate_object_additionalProperties(schema['additionalProperties'])
    elif schema.get('properties'):
        _validate_object_properties(schema['properties'])
    elif schema.get('patternProperties'):
        _validate_object_patternProperties(schema['patternProperties'])
    elif schema.get('propertyNames'):
        _validate_object_propertyNames(schema['propertyNames'])
    elif schema.get('maxProperties'):
        _validate_object_maxProperties(schema['maxProperties'])
    elif schema.get('minProperties'):
        _validate_object_minProperties(schema['minProperties'])
    elif schema.get('required'):
        _validate_object_required(schema['required'])
    else:
        assert False, 'unreachable'


@valid_keywords(
    [
        'contains',
        'items',
        'minContains',
        'minItems',
        'maxContains',
        'maxItems',
        'prefixItems',
        'type',
        'uniqueItems',
    ]
)
def _validate_array(schema: dict[str, object]) -> None: ...


@valid_keywords(['format', 'minLength', 'maxLength', 'pattern', 'type'])
def _validate_string(schema: dict[str, object]) -> None: ...


@valid_keywords(
    [
        'exclusiveMaximum',
        'exclusiveMinimum',
        'maximum',
        'minimum',
        'multipleOf',
        'type',
    ]
)
def _validate_number(schema: dict[str, object]) -> None: ...


@valid_keywords(
    [
        'exclusiveMaximum',
        'exclusiveMinimum',
        'maximum',
        'minimum',
        'multipleOf',
        'type',
    ]
)
def _validate_integer(schema: dict[str, object]) -> None: ...


@valid_keywords(['type'])
def _validate_boolean(schema: dict[str, object]) -> None: ...


@valid_keywords(['type'])
def _validate_null(schema: dict[str, object]) -> None: ...


def _validate_schema(schema: object) -> None:
    if not isinstance(schema, dict):
        raise exceptions.ValidationError('Expected dict: got {type(schema)}')

    if 'type' not in schema:
        raise exceptions.ValidationError("Missing 'type' keyword")

    schema_type = schema['type']
    if schema_type == 'object':
        _validate_object(schema)
    elif schema_type == 'array':
        _validate_array(schema)
    elif schema_type == 'string':
        _validate_string(schema)
    elif schema_type == 'number':
        _validate_number(schema)
    elif schema_type == 'integer':
        _validate_integer(schema)
    elif schema_type == 'boolean':
        _validate_boolean(schema)
    elif schema_type == 'null':
        _validate_null(schema)
    else:
        raise exceptions.ValidationError(
            "Invalid 'type' keyword: {schema_type}"
        )


def validate(schema: object) -> None:
    _validate_schema(schema)
