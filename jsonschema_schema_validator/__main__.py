import argparse
import json
import pathlib
import sys

from jsonschema_schema_validator.validator import validate


def main() -> None:
    parser = argparse.ArgumentParser('Validate the provided schema')
    parser.add_argument(
        'schema',
        type=pathlib.Path,
        help='Path to schema',
    )
    parsed_args = parser.parse_args()

    path: pathlib.Path = parsed_args.path
    if not path.exists():
        print('ERROR: {path} does not exist', file=sys.stderr)

    with path.open() as fh:
        schema = json.load(fh)

    validate(schema)


if __name__ == '__main__':
    main()
