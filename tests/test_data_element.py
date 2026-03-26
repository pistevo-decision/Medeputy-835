import pytest
from x12_segment_parser.data_element import DataElement, DataType


def test_data_element_string():
    element = DataElement('val')
    assert element.dataType == DataType.STRING
    assert element.get_value() == 'val'
    assert not element.is_empty()

    element = DataElement('')
    assert element.is_empty()


def test_data_element_component():
    components = ['val0', 'val1']
    element = DataElement(components)
    assert element.dataType == DataType.COMPONENT
    assert element.get_value(1) == components[0]
    assert element.get_value(2) == components[1]

    components.pop()
    assert len(components) == 1
    assert element.get_value(1) == 'val0'
    assert element.get_value(2) == 'val1'

    with pytest.raises(ValueError) as exception_info:
        DataElement(['val', 0])  # type: ignore

    assert exception_info.type is ValueError
    exception_text_expected = (
        'If value is a list then they must all be of type string or all '
        'Component type DataElements.'
    )
    assert exception_text_expected in str(exception_info.value)

    with pytest.raises(ValueError) as exception_info:
        DataElement([])
    assert exception_info.type is ValueError
    assert 'Cannot have an empty sequence as a value' in str(
        exception_info.value
    )


def test_equality():
    element_str_1 = DataElement('val1')
    element_str_2 = DataElement('val1')
    element_str_3 = DataElement('val2')

    assert element_str_1 != 'val1'
    assert element_str_1 == element_str_2
    assert element_str_1 != element_str_3

    element_component_1 = DataElement(['val1', 'val2'])
    element_component_2 = DataElement(['val1', 'val2'])
    element_component_3 = DataElement(['val2', 'val1'])

    assert element_component_1 == element_component_2
    assert element_component_2 != element_component_3

    element_multi_1 = DataElement([element_component_1, element_component_3])
    element_multi_2 = DataElement([element_component_1, element_component_3])
    element_multi_3 = DataElement([element_component_2])

    assert element_multi_1 == element_multi_2
    assert element_multi_3 != element_multi_2

    assert DataElement('str') != DataElement(['str'])


def test_hash():
    element = DataElement('something')
    assert f"{element}" == "'something'"
    assert element.__hash__() == "'something'".__hash__()


def test_to_string():
    string_val = 'some_text'

    element = DataElement(string_val)
    assert f"{element}" == f"'{string_val}'"

    string_val_2 = 'some_other'
    element = DataElement([string_val, string_val_2])

    expected = f"{{\n  1:'{string_val}',\n  2:'{string_val_2}'\n}}"
    assert f"{element}" == expected

    element_2 = DataElement([string_val_2, string_val])
    element_3 = DataElement([element, element_2])

    expected = (
        f"[\n{{\n  1:'{string_val}',\n  2:'{string_val_2}'\n}},"
        f"\n{{\n  1:'{string_val_2}',\n  2:'{string_val}'\n}}\n]"
    )
    assert f"{element_3}" == expected


def test_data_element_multi_component():
    components_1 = ['val0', 'val1']
    components_2 = ['val2', 'val3']
    element_1 = DataElement(components_1)
    element_2 = DataElement(components_2)
    element_list = [element_1, element_2]
    element = DataElement(element_list)

    assert element.dataType == DataType.MULTI_COMPONENT
    assert element.get_value(1) == element_1
    assert element.get_value(2) == element_2

    element_list.pop()
    assert len(element_list) == 1
    assert element.get_value(1) == element_1
    assert element.get_value(2) == element_2

    repeat_list = element.get_repeats()
    assert len(repeat_list) == 2
    assert repeat_list[0] == element_1
    assert repeat_list[1] == element_2

    assert len(element) == 2

    with pytest.raises(ValueError) as exception:
        DataElement([element_1, DataElement('str')])

    assert exception.type is ValueError
    exception_text_expected = (
        'If value is a list then they must all be of type string or all '
        'Component type DataElements.'
    )
    assert exception_text_expected in str(exception.value)


def test_get_value_errors():
    element = DataElement('val')
    with pytest.raises(ValueError) as exception:
        element.get_value(1)

    assert exception.type is ValueError
    assert 'A string type DataElement does not have any index.' in str(
        exception.value
    )

    element = DataElement(['str1', 'str2'])
    with pytest.raises(IndexError) as exception:
        element.get_value(0)
    assert exception.type is IndexError
    expected_msg = (
        'Elements are 1-indexed. Index value of 0 is outside of bounds 1 and 2.'
    )
    assert expected_msg in str(exception.value)

    with pytest.raises(IndexError) as exception:
        element.get_value(3)
    assert exception.type is IndexError
    expected_msg = (
        'Elements are 1-indexed. Index value of 3 is outside of bounds 1 and 2.'
    )
    assert expected_msg in str(exception.value)


def test_repeats_methods():
    element = DataElement('val')
    with pytest.raises(NotImplementedError) as exception:
        element.get_repeats()
    assert exception.type is NotImplementedError
    assert 'There are no repeats for a non MULTI_COMPONENT DataElement.' in str(
        exception.value
    )

    with pytest.raises(NotImplementedError) as exception:
        len(element)
    assert exception.type is NotImplementedError
    assert 'DataElement of type STRING does not have a length.' in str(
        exception.value
    )

    components_1 = ['val0', 'val1']
    components_2 = ['val2', 'val3']
    element_1 = DataElement(components_1)
    element_2 = DataElement(components_2)

    element = DataElement([element_1, element_2])
    assert len(element) == 2
    repeat_list = element.get_repeats()
    assert repeat_list[0] == element_1
    assert repeat_list[1] == element_2


def test_has_component_methods():
    components = ['1', '2', '3', '']
    element = DataElement(components)

    assert not element.has_component_idx(0)
    assert element.has_component_idx(1)
    assert element.has_component_idx(2)
    assert element.has_component_idx(3)
    assert not element.has_component_idx(4)
    assert element.has_component_idx(4, ignore_empty=False)
    assert not element.has_component_idx(5)
    assert len(components) == 4

    with pytest.raises(NotImplementedError) as exception:
        DataElement('str').has_component_idx(0)
    assert exception.type == NotImplementedError
    assert (
        'There are no components for a non COMPONENT type DataElement.' in
        str(exception.value)
    )
