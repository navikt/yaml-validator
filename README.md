# YAML Validator
Basic Python script and accompanying GitHub action for validating a given YAML document against a given schema using [Cerberus](http://docs.python-cerberus.org/en/stable/).

## Usage
```shell script
usage: validator.py [-h] schema_path document_path

YAML validator

positional arguments:
  schema_path    Path to the YAML schema to validate against
  document_path  Path to the YAML document to be validated

optional arguments:
  -h, --help     show this help message and exit
```

## Github Action

### Required parameters

- `schema_path` - Path to the YAML schema to validate against
- `document_path` - Path to the YAML document to be validated

### Workflow example
```yaml
name: Validate YAML
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v1
    - uses: navikt/yaml-validator@v1
      with:
        schema_path: schema.yaml
        document_path: document.yaml
```
