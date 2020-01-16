from cerberus import Validator
from cerberus.errors import BasicErrorHandler
import argparse
import pprint
import sys
import yaml


class CustomErrorHandler(BasicErrorHandler):
    def _format_message(self, field, error):
        document_error_path = '->'.join([str(x) for x in error.document_path])
        return f"'{error.value}' does not satisfy constraint '{error.constraint}' at '{document_error_path}'"


def __load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exception:
            raise exception


def evaluate_yaml_schema(schema_path, document_path):
    validator = Validator(error_handler=CustomErrorHandler())
    schema = __load_yaml_document(schema_path)
    document = __load_yaml_document(document_path)
    valid = validator.validate(document, schema)
    if not valid:
        pp = pprint.PrettyPrinter(width=200)
        pp.pprint(validator.errors)
    return valid


def main():
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document to be validated")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path
    if not evaluate_yaml_schema(schema_path, document_path):
        print(f"found validation failures for entries in document '{document_path}'")
        sys.exit(1)
    else:
        print(f"document '{document_path}' is valid")


if __name__ == "__main__":
    main()
