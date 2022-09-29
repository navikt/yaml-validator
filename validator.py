import argparse
import logging
import sys
import yaml

try:
    from yaml import CFullLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from cerberus import Validator
from distutils.util import strtobool
from pathlib import Path

seen_fields = {}


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

    def _validate_value_must_be_unique(self, value_must_be_unique, field, value):
        """ Test that the value of the field has not been seen before.
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if not value_must_be_unique:
            return

        if field not in seen_fields:
            seen_fields[field] = {value: self.path_to_document}
            return

        if value in seen_fields[field]:
            seen_path = seen_fields[field][value]
            self._error(field, f"Duplicate value \"{value}\" found at \"{self.path_to_document}\"; conflicts with \"{seen_path}\".")
        else:
            seen_fields[field][value] = self.path_to_document


def _load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=Loader)
        except yaml.YAMLError as exception:
            raise exception


def _validate_single(schema_path, document_path, validate_file_extension, filter_extensions):
    if document_path.suffix not in filter_extensions :
        if validate_file_extension and not document_path.is_dir():
            logging.error(f"❌\t'{document_path}' does not have a file extension matching [.yml, .yaml].")
            return False
        return None

    validator = CustomValidator(path_to_document=document_path)
    schema = _load_yaml_document(schema_path)
    document = _load_yaml_document(document_path)
    valid = validator.validate(document, schema)

    if not valid:
        logging.error(f"❌\t'{document_path}'")
        logging.error(f"\n{yaml.dump(validator.errors, default_flow_style=False)}")
    return valid


def _validate_path(root, schema_path, document_paths, validate_file_extension, filter_extensions):
    results = [
        (path.relative_to('./'), _validate_single(schema_path, path.relative_to('./'), validate_file_extension, filter_extensions))
        for path in document_paths
    ]
    results = list(filter(lambda x: x[1] is not None, results))

    total_count = len(results)

    if any(not is_valid for (_, is_valid) in results):
        invalid_count = len([(path, is_valid) for (path, is_valid) in results if not is_valid])
        logging.error(f"{invalid_count} of {total_count} document(s) in '{root}' failed to validate:")
        [logging.error(f'❌\t{path}') for (path, is_valid) in results if not is_valid]
        sys.exit(1)
    else:
        logging.info(f"✅\t{total_count} of {total_count} documents in '{root}' are valid!")


def _process(schema_path, document_path, validate_file_extension, filter_extensions):
    logging.info(f"😘\tValidating '{document_path}' against schema '{schema_path}'...")

    root = Path(document_path).relative_to('./')
    paths = Path('.').glob(document_path)

    if Path(document_path).is_dir():
        if not document_path.endswith('/'):
            document_path = document_path + '/'
        paths = Path('.').glob(document_path + '**/*')

    _validate_path(root, schema_path, paths, validate_file_extension, filter_extensions)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document or directory of documents to be validated. "
                                              "Accepts globs. Defaults to recursive search if only a directory is "
                                              "provided.")
    parser.add_argument("validate_file_extension",
                        default="false",
                        nargs='?',
                        help="Validate that all the given documents have a file extension as specified by filter_extensions. Default: false")
    parser.add_argument("filter_extensions",
                        default=".yml,.yaml",
                        nargs='?',
                        help="Only the files with these extensions will be checked. Default: .yml,.yaml")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path
    validate_file_extension = bool(strtobool(args.validate_file_extension.lower()))
    filter_extensions = args.filter_extensions.split(',')

    _process(schema_path, document_path, validate_file_extension, filter_extensions)


if __name__ == "__main__":
    main()
