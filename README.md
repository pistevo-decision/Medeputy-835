# X12-Segment-Parser

A lightweight, memory-efficient Python library for streaming and parsing X12 EDI
files into structured, immutable segment objects.

Meant to allow segment by segment access to the X12 files with full control over
any custom validation logic.
Capable of handling all standard X12 files.

## Features

- **Streaming parser** - process files of any size in configurable chunks
  without loading the entire document into memory
- **Auto-detects delimiters** - reads element, component, repeats, and segment
  terminators directly from the ISA Header segment
- **Immutable data model** - `SegmentInfo` and `DataElement` objects are frozen
  after creation

## Installation

```bash
TBD
```

Requirements: Python 3.10+

## Quick Start

```python
from medeputy835 import X12Parser

parser = X12Parser()

from segment in parser.parse_file("path/to/file.edi"):
    print(segment.name)                     # e.g. "ISA", "GS"
    print(segment.get_element(1))           # first element (1-index)
```

## Core Classes

### `X12Parser`

The entry point for parsing X12 files.

```python
X12Parser(chunk_size: int=65536)
```

| Parameter    | Type  | Default | Description                                                       |
| ------------ | ----- | ------- | ----------------------------------------------------------------- |
| `chunk_size` | `int` | `65536` | Read buffer size (64 KB). Increase for faster I/O on larger files |

---

### Methods

`parse_file(filepath) -> Generator[SegmentInfo, None, None]`

Streams an X12 file and yields one `SegmentInfo` per segment. Never loads entire
file into memory

```python
parser = X12Parser()
for segment in parser.parse_file("834_enrollment.edi"):
    if segment.name == "NM1":
        print(segment.get_element(3))  # Last name

```

---

### `SegmentInfo`

An immutable representation of a single X12 Segment. This is constructed by the
`X12Parser`

```python
SegmentInfo(name: str, elements: Sequence[DataElement])
```

Elements are deep-copied during construction. The `name` and all elements are
immutable after creation

---

### Attributes

| Attribute | Type  | Description                                         |
| --------- | ----- | --------------------------------------------------- |
| `name`    | `str` | Segment identifier (e.g. `"NM1"`, `"CLM"`, `"ISA"`) |

---

### Methods

`get_element(idx: int) -> DataElement`

Returns the `DataElement` at the given 1-based index. Raises `IndexError` if out
of bounds.

`has_element_idx(idx: int, ignore_empty: bool=True) -> bool`

Returns `True` if the element exists at the given index. When
`ignore_empty=True (default), elements that are empty strings are treated as
absent.

`__len__() -> int`

Returns the total number of elements in the segment (including the name)

```python
print(len(segment)) # number of data elements (including the name)
```

---

### `DataElement`

An immutable representation of a single X12 data element. There are three
variants that are automatically determined during construction.

```python
DataElement(value: str | Sequence[str] | Sequence[DataElement])
```

### Types

| `DataType`        | Constructed from                                 | Example raw input                     |
| ----------------- | ------------------------------------------------ | ------------------------------------- |
| `STRING`          | A plain `str`                                    | `"PE"`                                |
| `COMPONENT`       | A `Sequence[str]`                                | `"11:B:1"` -> `['11', 'B', '1']`      |
| `MULTI_COMPONENT` | A `Sequence[DataElement]` (All `COMPONENT` type) | `"A:1^B:2"` -> two component elements |

---

### Methods

`get_value(index: int | None=None) -> str | DataElement`

Returns the elements value. For `STRING` types, call with no argument. For
`COMPONENT` and `MULTI_COMPONENT`, provide a 1-based index

```python
# STRING
plain = DataElement("PE")
plain.get_value()     # 'PE'

# COMPONENT
composite = DataElement(["11", "B", "1"])
composite.get_value(1)  # '11'
composite.get_value(2)  # 'B'
composite.get_value(3)  # '1'

# MULTI_COMPONENT (repeating element)
repeat = DataElement([
    DataElement(["A", "1"]),
    DataElement(["B", "2"]),
])
repeat.get_value(1)  # DataElement(['A', '1'])
repeat.get_value(2)  # DataElement(['B', '2'])
```

`get_repeats() -> Tuple[DataElement, ...]`

Returns all the repeat components for a `MULTI_COMPONENT` element. Raises
`TypeError` if called with a non-`MULTI_COMPONENT` element.

```python
repeats = element.get_repeats()
for repeat in repeats:
    print(repeat.get_value(1))
```

`has_component_idx(idx: int, ignore_empty: bool=True) -> bool`

Checks whether a component exists at the given 1-based index within a
`COMPONENT` element. Raises `TypeError` if called with a non-`COMPONENT`
element.

`is_empty() -> bool`

Returns `True` if the element is a `STRING` type with an empty value. Because
of the nature of X12 files only `STRING` elements can be empty

`__len__() -> int`

Returns the number jof components (for `COMPONENT`) or repeats (for
`MULTI_COMPONENT`). Raises `TypeError` for `STRING` types.

```python
print(len(composite_element)) # number of components
```

## Examples

**Iterating all segments in a file**

```python
from x12_segment_parser import X12Parser

parser = X12Parser()

for segment in parser.parse_file("claims.edi"):
    print(f"{segment.name} ({len(segment)} elements)")
```

**Extracting data from a specific Segment**

```python
for segment in parser.parse_file("835_remittance.edi"):
    if segment.name == "CLP":
        claim_id     = segment.get_element(1).get_value()
        claim_status = segment.get_element(2).get_value()
        billed_amt   = segment.get_element(3).get_value()
        print(f"Claim {claim_id}: status={claim_status}, billed=${billed_amt}")

```

**Working with composite elements**

```python
for segment in parser.parse_file("file.edi"):
    if segment.name == "CLM":
        # CLM05 is a composite: facility_code:claim_freq:..
        if segment.has_element_idx(5):
            clm05 = segment.get_element(5)
            facility_code = clm05.get_value(1)
            claim_freq    = clm05.get_value(3)

```

**Working with repeating elements**

```python
for segment in parser.parse_file("file.edi"):
    if segment.name == "REF":
        element = segment.get_element(2)
        if element.dataType.name == "MULTI_COMPONENT":
            for repeat in element.get_repeats():
                print(repeat.get_value(1))

```

**Tuning chunk size for large files**

```python
# Use a larger chunk size for faster throughput on very large files
parser = X12Parser(chunk_size=256 * 1024)  # 256 KB

for segment in parser.parse_file("very_large_file.edi"):
    ...
```

## Testing

This project uses [pytest](https://docs.pytest.org/en/stable/)

**Install test dependencies**

```bash
pip install pytest pytest-cov
```

**Run the test suite**

```bash
pytest
```

**Run with coverage report**

```bash
pytest --cov
```

# Building

For building the package (local testing) run the following command:

```bash
python -m build
```

## License

MIT
