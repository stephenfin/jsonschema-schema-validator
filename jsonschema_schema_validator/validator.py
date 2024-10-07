import collections.abc
import re
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
        "'additionalProperties' must be a boolean or a schema"
    )


def _validate_object_properties(prop: object) -> None:
    if not isinstance(prop, dict):
        raise exceptions.ValidationError(
            "'properties' must be a mapping of property names to schemas"
        )

    # TODO(stephenfin): We should probably warn about suspicious looking
    # properties like 'properties' or any other keyword, but the infrastructure
    # isn't there for that yet

    for schema in prop.values():
        _validate_schema(schema)


def _validate_object_patternProperties(prop: object) -> None:
    if not isinstance(prop, dict):
        raise exceptions.ValidationError(
            "'patternProperties' must be a mapping of property name patterns "
            'to schemas'
        )

    for pattern in prop:
        if not isinstance(pattern, str):
            raise exceptions.ValidationError(
                "'patternProperties' must be a mapping of property name "
                'patterns to schemas'
            )

        try:
            re.compile(pattern)
        except re.error:
            raise exceptions.ValidationError(
                "'patternProperties' must be a mapping of property name "
                'patterns to schemas'
            )

    for schema in prop.values():
        _validate_schema(schema)


def _validate_object_propertyNames(prop: object) -> None:
    if not isinstance(prop, dict) or prop.get('type', 'string') != 'string':
        raise exceptions.ValidationError(
            "'propertyNames' must be a schema with type string"
        )

    if 'type' not in prop:
        # "type": "string" is implied
        prop = {**prop, 'type': 'string'}

    _validate_string(prop)


def _validate_object_maxProperties(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'maxProperties' must be a non-negative integer"
        )


def _validate_object_minProperties(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'minProperties' must be a non-negative integer"
        )


def _validate_object_required(prop: object) -> None:
    if not isinstance(prop, list) or any(not isinstance(x, str) for x in prop):
        raise exceptions.ValidationError(
            "'required' must be a list of property names"
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
    for keyword in schema:
        if keyword == 'additionalProperties':
            _validate_object_additionalProperties(
                schema['additionalProperties']
            )
        elif keyword == 'properties':
            _validate_object_properties(schema['properties'])
        elif keyword == 'patternProperties':
            _validate_object_patternProperties(schema['patternProperties'])
        elif keyword == 'propertyNames':
            _validate_object_propertyNames(schema['propertyNames'])
        elif keyword == 'maxProperties':
            _validate_object_maxProperties(schema['maxProperties'])
        elif keyword == 'minProperties':
            _validate_object_minProperties(schema['minProperties'])
        elif keyword == 'required':
            _validate_object_required(schema['required'])
        elif keyword == 'type':
            if schema['type'] != 'object':
                # programmer error
                raise RuntimeError("'type' must be 'object'")
        else:
            assert False, 'unreachable'


def _validate_array_contains(prop: object) -> None:
    return _validate_schema(prop)


def _validate_array_items(prop: object) -> None:
    return _validate_schema(prop)


def _validate_array_maxContains(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'maxContains' must be a non-negative integer"
        )


def _validate_array_maxItems(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'maxItems' must be a non-negative integer"
        )


def _validate_array_minContains(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'minContains' must be a non-negative integer"
        )


def _validate_array_minItems(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'minItems' must be a non-negative integer"
        )


def _validate_array_prefixItems(prop: object) -> None:
    if not isinstance(prop, list):
        raise exceptions.ValidationError(
            "'prefixItems' must be a list of schemas"
        )

    for schema in prop:
        _validate_schema(schema)


def _validate_array_uniqueItems(prop: object) -> None:
    if not isinstance(prop, bool):
        raise exceptions.ValidationError("'uniqueItems' must be a boolean")


@valid_keywords(
    [
        'contains',
        'items',
        'maxContains',
        'maxItems',
        'minContains',
        'minItems',
        'prefixItems',
        'type',
        'uniqueItems',
    ]
)
def _validate_array(schema: dict[str, object]) -> None:
    for keyword in schema:
        if keyword == 'contains':
            _validate_array_contains(schema['contains'])
        elif keyword == 'items':
            _validate_array_items(schema['items'])
        elif keyword == 'maxContains':
            _validate_array_maxContains(schema['maxContains'])
        elif keyword == 'maxItems':
            _validate_array_maxItems(schema['maxItems'])
        elif keyword == 'minContains':
            _validate_array_minContains(schema['minContains'])
        elif keyword == 'minItems':
            _validate_array_minItems(schema['minItems'])
        elif keyword == 'prefixItems':
            _validate_array_prefixItems(schema['prefixItems'])
        elif keyword == 'type':
            if schema['type'] != 'array':
                # programmer error
                raise RuntimeError("'type' must be 'array'")
        elif keyword == 'uniqueItems':
            _validate_array_uniqueItems(schema['uniqueItems'])
        else:
            assert False, 'unreachable'


def _validate_string_format(prop: object) -> None:
    # TODO(stephenfin): Take a context argument that allows us to indicate the
    # supported format values
    if not isinstance(prop, str):
        raise exceptions.ValidationError("'format' must be a string")


def _validate_string_maxLength(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'maxLength' must be a non-negative integer"
        )


def _validate_string_minLength(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'minLength' must be a non-negative integer"
        )


def _validate_string_pattern(prop: object) -> None:
    if not isinstance(prop, str):
        raise exceptions.ValidationError("'pattern' must be a string")

    try:
        re.compile(prop)
    except re.error:
        raise exceptions.ValidationError("'pattern' must be a valid regex")


@valid_keywords(['format', 'minLength', 'maxLength', 'pattern', 'type'])
def _validate_string(schema: dict[str, object]) -> None:
    for keyword in schema:
        if keyword == 'format':
            _validate_string_format(schema['format'])
        elif keyword == 'maxLength':
            _validate_string_maxLength(schema['maxLength'])
        elif keyword == 'minLength':
            _validate_string_minLength(schema['minLength'])
        elif keyword == 'pattern':
            _validate_string_pattern(schema['pattern'])
        elif keyword == 'type':
            if schema['type'] != 'string':
                # programmer error
                raise RuntimeError("'type' must be 'string'")


def _validate_number_exclusiveMaximum(prop: object) -> None:
    if not isinstance(prop, int):
        raise exceptions.ValidationError(
            "'exclusiveMaximum' must be an integer"
        )


def _validate_number_exclusiveMinimum(prop: object) -> None:
    if not isinstance(prop, int):
        raise exceptions.ValidationError(
            "'exclusiveMinimum' must be an integer"
        )


def _validate_number_maximum(prop: object) -> None:
    if not isinstance(prop, int):
        raise exceptions.ValidationError("'maximum' must be an integer")


def _validate_number_minimum(prop: object) -> None:
    if not isinstance(prop, int):
        raise exceptions.ValidationError("'minimum' must be an integer")


def _validate_number_multipleOf(prop: object) -> None:
    if not isinstance(prop, int) or prop < 1:
        raise exceptions.ValidationError(
            "'multipleOf' must be a positive integer"
        )


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
def _validate_number(schema: dict[str, object]) -> None:
    for keyword in schema:
        if keyword == 'exclusiveMaximum':
            _validate_number_exclusiveMaximum(schema['exclusiveMaximum'])
        elif keyword == 'exclusiveMinimum':
            _validate_number_exclusiveMinimum(schema['exclusiveMinimum'])
        elif keyword == 'maximum':
            _validate_number_maximum(schema['maximum'])
        elif keyword == 'minimum':
            _validate_number_minimum(schema['minimum'])
        elif keyword == 'multipleOf':
            _validate_number_multipleOf(schema['multipleOf'])
        elif keyword == 'type':
            if schema['type'] != 'number':
                # programmer error
                raise RuntimeError("'type' must be 'number'")


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
def _validate_integer(schema: dict[str, object]) -> None:
    for keyword in schema:
        if keyword == 'exclusiveMaximum':
            _validate_number_exclusiveMaximum(schema['exclusiveMaximum'])
        elif keyword == 'exclusiveMinimum':
            _validate_number_exclusiveMinimum(schema['exclusiveMinimum'])
        elif keyword == 'maximum':
            _validate_number_maximum(schema['maximum'])
        elif keyword == 'minimum':
            _validate_number_minimum(schema['minimum'])
        elif keyword == 'multipleOf':
            _validate_number_multipleOf(schema['multipleOf'])
        elif keyword == 'type':
            if schema['type'] != 'integer':
                # programmer error
                raise RuntimeError("'type' must be 'integer'")


@valid_keywords(['type'])
def _validate_boolean(schema: dict[str, object]) -> None:
    if schema['type'] != 'boolean':
        # programmer error
        raise RuntimeError("'type' must be 'boolean'")


@valid_keywords(['type'])
def _validate_null(schema: dict[str, object]) -> None:
    if schema['type'] != 'null':
        # programmer error
        raise RuntimeError("'type' must be 'null'")


def _validate_schema(schema: object) -> None:
    if not isinstance(schema, dict):
        raise exceptions.ValidationError('schemas must dicts')

    schema_type = schema.get('type')
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
            "'type' must be one of: object, array, string, number, integer, "
            'boolean, null'
        )


def validate(schema: object) -> None:
    _validate_schema(schema)
