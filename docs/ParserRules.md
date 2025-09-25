# `ParserRules`

Universal container for **parser rules** used in query filtering.

---

## Concept

* Defines **how the parser converts raw query parameters** into normalized records `(relationships, field, operations, value)`.
* Changing parser rules affects **interpretation**, but not the final normalized structure for the same input.
* Works in combination with a `SuffixSet`.
* Supports reactions on unknown components: `error` | `warn` | `ignore`.

---

## Input Format

```
relationship@field__suffix=value
```

* `relationship` (optional) - ORM relationship name.
* `@` - separates relationships from the field.
* `field` - required column name.
* `__` - separates field from suffix (default).
* `suffix` (optional) - operation from the `SuffixSet`.
* `value` - raw value from the query.

---

## Structure / Attributes

```python
class ParserRules:
    LOGGER: logger | None              # Logger if "warn" mode is onn
    SUFFIX_SET: SuffixSet              # set of valid suffixes (default DEFAULT_SUFFIXES)
    SUFFIX_DELIMITER: str              # separator between field and suffix, default="__"
    RELATIONSHIPS_DELIMITER: str       # separator for relationship chain, default="@"
    UNKNOWN_SUFFIX_REACTION: "error"|"warn"|"ignore"
    UNKNOWN_FIlTRATED_FIELD: "error"|"warn"|"ignore"
```
* `LOGGER` - instance of logger.
* `SUFFIX_SET` - source of operations.
* `SUFFIX_DELIMITER` and `RELATIONSHIPS_DELIMITER` can be changed without breaking the normalized output structure.
* `UNKNOWN_*` control behavior on unknown suffixes or fields.

---

## Normalized Output

The parser always returns a dictionary in the form:

```python
{
  "field_name": [
    {
      "relationships": ["rel1", "rel2"],  # empty list if none
      "operations": ["op1","op2"],        # list of valid suffixes (or ["exact"])
      "value": "raw string value"
    },
    ...
  ],
  ...
}
```

> Changing `SUFFIX_DELIMITER` or reactions affects which tokens are valid.
> If the input string is compatible with the rules, the normalized dictionary stays identical.


## Examples

### 1) Default Rules

Input:

```
profile@username__contains=foo&age__gt=30
```

```python
from ormparams.rules import ParserRules
from ormparams.parser import Parser

rules = ParserRules()  # defaults: RELATIONSHIPS_DELIMITER='@', SUFFIX_DELIMITER='__', UNKNOWN_*='error'
parsed = Parser(rules).parse_url("profile@username__contains=foo&age__gt=30")
```

Output:

```python
{
  "username": [{"relationships":["profile"], "operations":["contains"], "value":"foo"}],
  "age":      [{"relationships":[],        "operations":["gt"],       "value":"30"}]
}
```

---

### 2) Changed `SUFFIX_DELIMITER` (compatible input)

```python
rules2 = ParserRules(suffix_delimiter="--", unknown_suffix_reaction="warn")
parsed2 = Parser(rules2).parse_url("profile@username__contains=foo&age__gt=30")
```

Output (unchanged structure):

```python
{
  "username": [{"relationships":["profile"], "operations":["contains"], "value":"foo"}],
  "age":      [{"relationships":[],        "operations":["gt"],       "value":"30"}]
}
```

> Even with different parser settings, the normalized structure remains consistent if input uses compatible separators.

---

### 3) Custom `SuffixSet`

```python
from ormparams.suffixes import SuffixSet

custom = SuffixSet()
custom.register_suffix("like", lambda col, v, m: col.contains(v))
rules3 = ParserRules(suffix_set=custom)

parsed3 = Parser(rules3).parse_url("name__like=John")
```

Output:

```python
{
  "name": [{"relationships":[], "operations":["like"], "value":"John"}]
}
```

> Adding custom suffixes does not break the existing parsing contract.

---

## Error Handling

* `UNKNOWN_SUFFIX_REACTION="error"` -> raises `UnknownOperatorError` on first unknown suffix.
* `"warn"` -> logs warning and skips unknown suffixes.
* `"ignore"` -> silently skips unknown suffixes.
* `UNKNOWN_FIlTRATED_FIELD` applies similarly for unknown fields in combination with `OrmFilter`.

---

## Stability Guarantee

* Changing delimiters or suffix sets changes parsing rules.
* For the same valid input, the **normalized output dictionary** always stays predictable and identical.
* Useful when supporting alternative query formats without breaking ORM filter contracts.

---

## Quick Test Example

```python
from ormparams.rules import ParserRules
from ormparams.parser import Parser

q_def = "profile@username__contains=foo&age__gt=30"
q_alt = "profile.username--contains=foo&age--gt=30"

r_def = ParserRules()
r_alt = ParserRules(suffix_delimiter="--", relationships_delimiter=".", unknown_suffix_reaction="warn")

p_def = Parser(r_def)
p_alt = Parser(r_alt)

_ = p_def.parse_url(q_def) == p_alt.parse_url(q_alt)
print(_)
assert _ is True
```
