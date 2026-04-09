import pytest
from typing import List
from medeputy835 import SegmentInfo, DataElement


@pytest.fixture
def elements() -> List[DataElement]:
    return [
        DataElement('val'),
        DataElement('val2'),
        DataElement(''),
        DataElement(['', ''])
    ]


def test_setters():
    elements = [DataElement('val'), DataElement('val2')]
    segment = SegmentInfo('Name', elements)

    assert segment.name == 'Name'
    assert len(segment) == 3
    assert segment.get_element(1) == DataElement('val')
    assert segment.get_element(2) == DataElement('val2')

    elements.pop()
    assert len(segment) == 3
    assert segment.get_element(1) == DataElement('val')
    assert segment.get_element(2) == DataElement('val2')


def test_has_element(elements: List[DataElement]):
    segment = SegmentInfo('name', elements)
    assert not segment.has_element_idx(0)
    assert segment.has_element_idx(1)
    assert segment.has_element_idx(2)
    assert not segment.has_element_idx(3)
    assert segment.has_element_idx(3, ignore_empty=False)
    assert segment.has_element_idx(4)
    assert not segment.has_element_idx(5)


def test_get_element(elements: List[DataElement]):
    segment = SegmentInfo('name', elements)

    for idx, element in enumerate(elements):
        assert segment.get_element(idx + 1) == element

    with pytest.raises(IndexError) as error:
        segment.get_element(0)
    assert error.type is IndexError
    assert 'Index is out of range. Items are 1-indexed.' in str(error.value)


def test_to_string():
    segment = SegmentInfo('name', [DataElement('val'), DataElement('val2')])
    expected = f"name(\n1:{DataElement('val')},\n2:{DataElement('val2')}\n)"
    assert expected == f"{segment}"
