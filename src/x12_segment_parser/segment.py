from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Sequence
import copy


class DataType(Enum):
    STRING = 0
    COMPONENT = 1
    MULTI_COMPONENT = 2


@dataclass(frozen=True)
class DataElement:
    """
    Class that is meant to keep track of information within a segment.

    """
    dataType: DataType
    _value_str: str
    _value_str_tuple: Tuple[str, ...]
    _value_data_tuple: Tuple[DataElement, ...]
    _tuple_len: int

    def __init__(
        self: DataElement,
        dataType: DataType,
        value: str | Sequence[str] | Sequence[DataElement]
    ):
        """
        Initializer

        :param self: self
        :type self: DataElement
        :param dataType: Determines type of DataElement
        :type dataType: DataType
        :param value: The value for the datatype
        :type value: str | Sequence[str] | Sequence[DataElement]
        :raises ValueError: If a Component type DataElement has a list of
        DataElements as values
        :raises ValueError: If the value list is not all of type str or
        all of type DataElement
        """
        object.__setattr__(self, 'dataType', dataType)

        if isinstance(value, str):
            object.__setattr__(self, '_value_str', value)
            object.__setattr__(self, '_value_str_tuple', tuple())
            object.__setattr__(self, '_value_data_tuple', tuple())
            object.__setattr__(self, '_tuple_len', 0)

        else:
            object.__setattr__(self, '_tuple_len', len(value))
            if all(isinstance(e, str) for e in value):
                object.__setattr__(
                    self, '_value_str_tuple',
                    tuple(e for e in value)
                )
                object.__setattr__(self, '_value_str', '')
                object.__setattr__(self, '_value_data_tuple', tuple())
            elif all(isinstance(e, DataElement) for e in value):
                if dataType == DataType.COMPONENT:
                    raise ValueError(
                        'DataElements of type Component are not allowed to have'
                        ' a value consisting of a list of other DataElements'
                    )
                object.__setattr__(
                    self, '_value_data_tuple',
                    tuple(copy.deepcopy(e) for e in value)
                )
                object.__setattr__(self, '_value_str_tuple', tuple())
                object.__setattr__(self, '_value_str', '')
            else:
                raise ValueError(
                    'If value is a list they must all be of type string or all'
                    ' of type DataElement.'
                )

    def get_value(
        self: DataElement,
        index: None | int = None
    ) -> str | DataElement:
        """
        Will return the value of the data element.
        If an index is specified it will return the element value of that index

        :param self: self
        :type self: DataElement
        :param index: index of element to extract, defaults to None
        :type index: None | int, optional
        :raises ValueError: If asking for an index with String type DataElement
        :raises IndexError: If index is out of bound (1-indexed)
        :return: Element value 
        :rtype: str | DataElement
        """
        if self.dataType == DataType.STRING:
            if index:
                raise ValueError(
                    'A string type DataElement does not have any index'
                )
            return self._value_str
        else:
            if not index or index < 1 or index > self._tuple_len:
                raise IndexError(
                    f'Elements are 1-indexed. Index value of {index} is outside'
                    f' of bounds 1 and ${self._tuple_len}.'
                )
            if self.dataType == DataType.COMPONENT:
                return self._value_str_tuple[index]

            return self._value_data_tuple[index]

    def __repr__(self: DataElement) -> str:
        """
        Creates String representation

        :param self: self
        :type self: DataElement
        :return: String representation
        :rtype: str
        """
        if self.dataType == DataType.STRING:
            return self._value_str
        if self.dataType == DataType.COMPONENT:
            if self._tuple_len == 0:
                return "{}"
            repr = "{"
            for index, ele in enumerate(self._value_str_tuple):
                repr = repr + f"\n  {index + 1}:'{ele}'"
                if index != self._tuple_len - 1:
                    repr += ','
            repr = repr + "\n}"
            return repr

        if self._tuple_len == 0:
            return "[]"
        repr = '['
        for index, ele in enumerate(self._value_data_tuple):
            repr += f"\n{ele}"
            if index != self._tuple_len - 1:
                repr += ','
        repr = repr + "\n]"
        return repr


@dataclass(frozen=True)
class SegmentInfo:
    """
    Class for keeping track of segment info
    """
    name: str
    elements: Tuple[DataElement]

    def __init__(self: SegmentInfo, name: str, elements: Sequence[DataElement]):
        """
        Initializer

        :param self: self
        :type self: SegmentInfo
        :param name: name of segment
        :type name: str
        :param elements: data elements
        :type elements: Sequence[DataElement]
        """
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'elements', tuple(
            copy.deepcopy(e) for e in elements
        ))
