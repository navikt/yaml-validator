# YAML Validator
Basic Python script and accompanying GitHub action for validating a given YAML document against a given schema using [Cerberus](http://docs.python-cerberus.org/en/stable/).

## Usage
```text
usage: validator.py [-h] schema_path document_path [validate_file_extension] [filter_extensions]

YAML validator

positional arguments:
  schema_path              Path to the YAML schema to validate against
  include_document_paths   A comma separated list of paths to the YAML document or directory of documents to be validated. Accepts globs. 
  exclude_document_paths   A comma separated exclude list of paths to the YAML document or directory of documents to be validated. Accepts globs. 
  validate_file_extension  Validate that all the given documents have a file extension as specified by filter_extensions. Default: false
  filter_extensions        Only the files with these extensions will be checked. Default: .yml,.yaml

optional arguments:
  -h, --help            show this help message and exit
```

### Examples

#### Valid schema
```yaml
Users:
  required: true
  type: list
  schema:
    type: dict
    schema:
      name:
        required: true
        type: string
      age:
        required: true
        type: integer
```

#### Valid document that validates against schema

```yaml
Users:
  - name: "Joe"
    age: 21
  - name: "Jane"
    age: 24
```

## Github Action

### Required parameters

- `schema_path` - Path to the YAML schema to validate against
- `include_document_paths` - A comma separated list of paths to the YAML document or directory of documents to be validated. Accepts globs.

### Optional parameters

- `validate_file_extension` - Validate that all the given documents have a valid YAML file extension. Defaults to `no`.

### Workflow example
```yaml
name: Validate YAML
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: navikt/yaml-validator@v4
      with:
        schema_path: schema.yaml
        include_document_paths: document.yaml,dir/*
        exclude_document_paths: dir/not_these_files*
        validate_file_extension: 'no' # optional, defaults shown, enum of ['yes', 'no']
        filter_extensions: '.yml,.yaml' # optional, defaults shown
```
