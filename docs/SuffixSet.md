# `SuffixSet`

Universal container for **suffix rules** used in query filtering.


## Concept

* A **suffix** defines how a field is compared to a value.
* Format:

  ```
  field__suffix=value
  ```
* Each suffix maps to a SQLAlchemy expression.
* Custom suffixes can be registered or overridden.

Example:

```
age__gt=18        -> column > 18
name__contains=foo -> column.contains("foo")
```


## Structure

* `suffixes: Dict[str, SuffixContent]` – all rules.

### `SuffixContent` (TypedDict)

```python
{
    "id": str,                      # suffix name
    "func": Callable,               # builds SQLAlchemy expression
    "serializer": Optional[Callable]# preprocesses value
}
```

### `SuffixFunc`

```python
def func(column, value, model) -> Any
```
The comparison function can interact with fields from the model.
This is not recommended!!!
If you need complex filtering logic, implement it directly in code.
Using `model` args is at your own risk.

### `SuffixValueSerializer`

```python
def serializer(value) -> Any
```

Runs before `func`.  

---

## Methods

### `register_suffix(suffix, func, serializer=None) -> Self`

Add or override suffix.

Example:

```python
s.register_suffix(
    "isnull",
    lambda col, v, m: col.is_(None) if v else col.is_not(None),
    serializer=lambda v: v.lower() in ("true", "1"),
)
```

### `__getitem__(suffix: str)`

Dict-like access.

### `get(suffix, default=None)`

Safe access.

### `__iter__`, `__len__`

Iteration and size.

---

## Default Suffixes (`DefaultSuffixSet`)

| Suffix       | Expression              |
| ------------ | ----------------------- |
| `exact`      | `col == value`          |
| `gt`         | `col > value`           |
| `ge`         | `col >= value`          |
| `lt`         | `col < value`           |
| `le`         | `col <= value`          |
| `contains`   | `col.contains(value)`   |
| `startswith` | `col.startswith(value)` |
| `endswith`   | `col.endswith(value)`   |
| `in`         | `col.in_(iterable)`     |

---

## Usage

```python
suffixes = DefaultSuffixSet()

rule = suffixes["contains"]
expr = rule["func"](User.name, "john", User)
# -> User.name.contains("john")
```