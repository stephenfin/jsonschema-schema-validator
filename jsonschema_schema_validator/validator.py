import collections.abc
from typing import Union

from jsonschema_schema_validator import exceptions


TValidator = collections.abc.Callable[[dict[str, object]], None]

GENERIC_KEYWORDS = [
    'const',
    'default',
    'deprecated',
    'description',
    'enum',
    'examples',
    'readOnly',
    'title',
    'writeOnly',
]


def valid_keywords(
    valid_keywords: list[str],
) -> collections.abc.Callable[[TValidator], TValidator]:
    def wrapper(fn: TValidator) -> TValidator:
        def inner(schema: dict[str, object]) -> None:
            if len(set(schema)) < len(list(schema)):
                raise exceptions.ValidationError('Duplicate keywords')

            if invalid_keywords := set(schema) - (
                set(valid_keywords) | set(GENERIC_KEYWORDS)
            ):
                raise exceptions.ValidationError(
                    f'Invalid keywords: {invalid_keywords}'
                )

            _validate_generic_keywords(schema)

            return fn(schema)

        return inner

    return wrapper


def _validate_generic_keywords(schema: dict[str, object]) -> None:
    for keyword in schema:
        if keyword in ('description', 'title'):
            if not isinstance(schema[keyword], str):
                raise exceptions.ValidationError(
                    f"'{keyword}' must be a string"
                )
        elif keyword in ('deprecated', 'readOnly', 'writeOnly'):
            if not isinstance(schema[keyword], bool):
                raise exceptions.ValidationError(
                    f"'{keyword}' must be a boolean"
                )
        elif keyword in ('enum', 'examples'):
            if not isinstance(schema[keyword], list):
                raise exceptions.ValidationError(f"'{keyword}' must be a list")

    if type_ := schema.get('type'):
        if not isinstance(type_, str):
            raise exceptions.ValidationError(
                "'type' must be one of: object, array, string, number, "
                'integer, boolean, null'
            )

        types: dict[str, Union[type, tuple[type, ...]]] = {
            'array': list,
            'boolean': bool,
            'integer': (int, float),
            'number': (int, float),
            'object': dict,
            'string': str,
        }
        if type_ not in list(types) + ['null']:
            raise exceptions.ValidationError(
                "'type' must be one of: object, array, string, number, "
                'integer, boolean, null'
            )

        if const := schema.get('const'):
            # TODO: There's nothing to say this check should exist, so we're
            # technically out of spec. Perhaps this should be a warning
            # instead?
            if not isinstance(const, types[type_]):
                raise exceptions.ValidationError(
                    "mismatch between 'type' and type of 'const'"
                )

        if default := schema.get('default'):
            # TODO: This should really be a warning, not an error, since "[t]he
            # value of default should validate against the schema in which it
            # resides, but that isn't required".
            if not isinstance(default, types[type_]):
                raise exceptions.ValidationError(
                    "mismatch between 'type' and type of 'default'"
                )

        if enum := schema.get('enum'):
            # we already did this, but mypy can't figure that out
            if not isinstance(enum, list):
                raise exceptions.ValidationError("'enum' must be a list")

            # TODO: As above, this is not strictly necessary
            if not all(
                (isinstance(x, types[type_]) if type_ in types else x is None)
                for x in enum
            ):
                raise exceptions.ValidationError(
                    "mismatch between 'type' and types of 'enum'"
                )

        if examples := schema.get('examples'):
            # we already did this, but mypy can't figure that out
            if not isinstance(examples, list):
                raise exceptions.ValidationError("'examples' must be a list")

            # TODO: As above, this is not strictly necessary
            if not all(
                (isinstance(x, types[type_]) if type_ in types else x is None)
                for x in examples
            ):
                raise exceptions.ValidationError(
                    "mismatch between 'type' and types of 'examples'"
                )


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
