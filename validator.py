import argparse
import logging
import sys
import yaml

try:
    from yaml import CFullLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from cerberus import Validator
from pathlib import Path


class CustomValidator(Validator):
    def __init__(self, *args, **kwargs):
        self.path_to_document = kwargs.get('path_to_document')
        super(CustomValidator, self).__init__(*args, **kwargs)

    def _validate_value_must_match_filename(self, value_must_match_filename, field, value):
        """ Test that the value of the field matches the given filename.
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        filename = Path(self.path_to_document).stem
        matches = filename == value
        if value_must_match_filename and not matches:
            self._error(field, f"\"{value}\" does not match the filename \"{filename}\" at \"{self.path_to_document}\"")


def _load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=Loader)
        except yaml.YAMLError as exception:
            raise exception


def _validate_single(schema_path, document_path):
    validator = CustomValidator(path_to_document=document_path)
    schema = _load_yaml_document(schema_path)
    document = _load_yaml_document(document_path)
    valid = validator.validate(document, schema)

    if not valid:
        logging.error(f"❌\t'{document_path}'")
        logging.error(f"\n{yaml.dump(validator.errors, default_flow_style=False)}")
    return valid


def _validate_path(root, schema_path, document_paths):
    results = [
        (path.relative_to('./'), _validate_single(schema_path, path.relative_to('./')))
        for path in document_paths if path.suffix in [".yml", ".yaml"]
    ]
    total_count = len(results)

    if any(not is_valid for (_, is_valid) in results):
        invalid_count = len([(path, is_valid) for (path, is_valid) in results if not is_valid])
        logging.error(f"{invalid_count} of {total_count} document(s) in '{root}' failed to validate:")
        [logging.error(f'❌\t{path}') for (path, is_valid) in results if not is_valid]
        sys.exit(1)
    else:
        logging.info(f"✅\t{total_count} of {total_count} documents in '{root}' are valid!")


def _process(schema_path, document_path):
    logging.info(f"😘\tValidating '{document_path}' against schema '{schema_path}'...")

    root = Path(document_path).relative_to('./')
    paths = Path('.').glob(document_path)

    if Path(document_path).is_dir():
        if not document_path.endswith('/'):
            document_path = document_path + '/'
        paths = Path('.').glob(document_path + '**/*')

    _validate_path(root, schema_path, paths)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document or directory of documents to be validated. "
                                              "Accepts globs. Defaults to recursive search if only a directory is "
                                              "provided.")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path

    _process(schema_path, document_path)


if __name__ == "__main__":
    main()
