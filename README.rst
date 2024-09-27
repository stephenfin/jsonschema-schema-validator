===========================
jsonschema-schema-validator
===========================

A strict validator for JSON Schema schema.

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
