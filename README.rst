===========================
jsonschema-schema-validator
===========================

A strict validator for JSON Schema schemas. Only `Draft 2020-12`__ is currently supported.

.. __: https://json-schema.org/draft/2020-12

.. warning::

    This is very much work-in-progress and pretty dumb. For example, it does
    not resolve references or handle composition (``allOf`` etc.).

Usage
-----

From the CLI:

.. code-block:: shell

    python -m jsonschema-schema-validator <path-to-schema>

From Python:

.. code-block:: python-repl

    >>> from jsonschema_schema_validator import validate
    >>> schema = {'type': 'boolean'}
    >>> validate(schema)
