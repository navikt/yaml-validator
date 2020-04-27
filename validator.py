import argparse
import logging
import pathlib
import sys
import yaml

try:
    from yaml import CFullLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from cerberus import Validator


# Custom rules for vault-iac validations
class CustomValidator(Validator):
    def __init__(self, *args, **kwargs):
        self.path_to_document = kwargs.get('path_to_document')
        super(CustomValidator, self).__init__(*args, **kwargs)

    def _validate_app_must_exist(self, app_must_exist, field, value):
        """ Test that the application defined for the team exists in the apps directory
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        cluster = self.document_path[-1]
        file_path = pathlib.Path(self.path_to_document).parent.parent.joinpath(f"apps/{cluster}/{value}.yml")
        if app_must_exist and not file_path.exists():
            self._error(field, f"\"{value}\" does not exist at \"{file_path}\"")

    def _validate_app_name_must_match_filename(self, app_name_must_match_filename, field, value):
        """ Test that the application name matches the given filename.
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        filename = pathlib.Path(self.path_to_document).stem
        matches = filename == value
        if app_name_must_match_filename and not matches:
            self._error(field, f"\"{value}\" does not match the filename \"{filename}\" at \"{self.path_to_document}\"")


def __load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=Loader)
        except yaml.YAMLError as exception:
            raise exception


def evaluate_yaml_schema(schema_path, document_path):
    validator = CustomValidator(path_to_document=document_path)
    schema = __load_yaml_document(schema_path)
    document = __load_yaml_document(document_path)
    valid = validator.validate(document, schema)
    if not valid:
        logging.error(f"❌\t'{document_path}'")
        logging.error(f"\n{yaml.dump(validator.errors, default_flow_style=False)}")
    return valid


def validate_yaml_for_dir(schema_path, document_dir_path):
    results = [
        (document_path.relative_to('./'), evaluate_yaml_schema(schema_path, document_path.relative_to('./')))
        for file_ext in ('*.yml', '*.yaml')
        for document_path in pathlib.Path(document_dir_path).glob('**/' + file_ext)
    ]
    valid_count = len([(path, is_valid) for (path, is_valid) in results if is_valid])
    invalid_count = len([(path, is_valid) for (path, is_valid) in results if not is_valid])
    total_count = len(results)

    if any(not is_valid for (_, is_valid) in results):
        logging.error(f"{invalid_count} of {total_count} document(s) in '{document_dir_path}' failed to validate:")
        [logging.error(f'❌\t{path}') for (path, is_valid) in results if not is_valid]
        sys.exit(1)
    else:
        logging.info(f"✅\t{valid_count+invalid_count} of {total_count} documents in '{document_dir_path}' are valid!")


def validate_single_yaml(schema_path, document_path):
    if not evaluate_yaml_schema(schema_path, document_path):
        sys.exit(1)
    else:
        logging.info(f"✅\tDocument '{document_path}' is valid!")


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document or directory of documents to be validated")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path

    logging.info(f"😘\tValidating '{document_path}' against schema '{schema_path}'...")

    if pathlib.Path(document_path).is_dir():
        validate_yaml_for_dir(schema_path, document_path)
    else:
        validate_single_yaml(schema_path, document_path)


if __name__ == "__main__":
    main()
