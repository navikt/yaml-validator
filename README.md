# YAML Validator
Basic Python script and accompanying GitHub action for validating a given YAML document against a given schema using [Cerberus](http://docs.python-cerberus.org/en/stable/).

## Usage
```text
usage: validator.py [-h] schema_path document_path

YAML validator

positional arguments:
  schema_path    Path to the YAML schema to validate against
  document_path  Path to the YAML document or directory of documents to be validated

optional arguments:
  -h, --help     show this help message and exit
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
- `document_path` - Path to the YAML document or directory of documents to be validated

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
