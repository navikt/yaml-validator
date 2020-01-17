import argparse
import logging
import pathlib
import pprint
import sys
import yaml

from cerberus import Validator

# TODO
class CustomValidator(Validator):
    def _validate_app_must_exist(self, app_must_exist, field, value):
        """ Test that the application defined for the team exists in the apps directory
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        pass

    def _validate_app_name_must_match_filename(self, app_name_must_match_filename, field, value):
        """ Test that the application name matches the given filename.
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        matches = True
        if app_name_must_match_filename and not matches:
            self._error(field, "must match the given filename")


def __load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exception:
            raise exception


def evaluate_yaml_schema(schema_path, document_path):
    validator = CustomValidator()
    schema = __load_yaml_document(schema_path)
    document = __load_yaml_document(document_path)
    valid = validator.validate(document, schema)
    if not valid:
        logging.error(f"Failed to validate document '{document_path}' against schema `{schema_path}`")
        pp = pprint.PrettyPrinter(width=200)
        logging.error(pp.pformat(validator.errors))
        print('')
    return valid


def validate_yaml_for_dir(schema_path, document_dir_path):
    results = [(document_path.relative_to('./'), evaluate_yaml_schema(schema_path, document_path.relative_to('./')))
               for document_path in pathlib.Path(document_dir_path).glob('**/*.yml')]
    if any(not is_valid for (_, is_valid) in results):
        logging.error(f"Found validation failures for the following document(s) in '{document_dir_path}':")
        for (path, is_valid) in results:
            if not is_valid:
                logging.error(f'{path}')
        sys.exit(1)
    else:
        logging.info(f"All documents in '{document_dir_path}' are valid!")


def validate_single_yaml(schema_path, document_path):
    if not evaluate_yaml_schema(schema_path, document_path):
        sys.exit(1)
    else:
        logging.info(f"Document '{document_path}' is valid!")


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document or directory of documents to be validated")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path

    if pathlib.Path(document_path).is_dir():
        validate_yaml_for_dir(schema_path, document_path)
    else:
        validate_single_yaml(schema_path, document_path)


if __name__ == "__main__":
    main()
