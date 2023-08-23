import argparse
import logging
import sys
import yaml
import glob
import os

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
    if Path(document_path).suffix not in filter_extensions :
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


def _validate_path(schema_path, document_paths, validate_file_extension, filter_extensions):
    results = [
        (path, _validate_single(schema_path, path, validate_file_extension, filter_extensions))
        for path in document_paths
    ]
    results = list(filter(lambda x: x[1] is not None, results))

    total_count = len(results)

    if any(not is_valid for (_, is_valid) in results):
        invalid_count = len([(path, is_valid) for (path, is_valid) in results if not is_valid])
        logging.error(f"{invalid_count} of {total_count} document(s) failed to validate:")
        [logging.error(f'❌\t{path}') for (path, is_valid) in results if not is_valid]
        sys.exit(1)
    else:
        logging.info(f"✅\t{total_count} of {total_count} documents are valid!")


def _filter_paths(include_paths, exclude_paths):
    expanded_included_paths = _expand_paths(include_paths)
    expanded_excluded_paths = _expand_paths(exclude_paths)

    matching_files = []

    # Filter out excluded paths from included paths
    for path in expanded_included_paths:
        if all(exclude_path not in path for exclude_path in expanded_excluded_paths):
            matching_files.append(path)

    return matching_files

def _expand_paths(paths):
    expanded_paths = []
    for path in paths:
        path_expanded = os.path.expanduser(path)
        path_absolute = os.path.abspath(path_expanded)
        expanded_paths.extend(glob.glob(path_absolute))

    return expanded_paths

def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("include_document_paths", help="A comma separated list of paths to the YAML document or directory of documents to be validated. "
                                              "Accepts globs.")

    parser.add_argument("exclude_document_paths", help="A comma separated exclude list of paths to the YAML document or directory of documents to be validated. "
                                              "Accepts globs.",
                        default="",
                        nargs='?')
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
    include_document_paths = args.include_document_paths
    exclude_document_paths = args.exclude_document_paths

    validate_file_extension = bool(strtobool(args.validate_file_extension.lower()))
    filter_extensions = args.filter_extensions.split(',')

    matching_files = _filter_paths(include_document_paths.split(','), exclude_document_paths.split(','))
    _validate_path(os.path.abspath(os.path.expanduser(schema_path)), matching_files, validate_file_extension, filter_extensions)


if __name__ == "__main__":
    main()
