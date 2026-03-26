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
        :raises ValueError: If the value is an empty sequence
        :raises ValueError: If a Component type DataElement has a list of
        DataElements as values
        :raises ValueError: If the value list is not all of type str or
        all of type DataElement
        """

        if isinstance(value, str):
            object.__setattr__(self, '_value_str', value)
            object.__setattr__(self, '_value_str_tuple', tuple())
            object.__setattr__(self, '_value_data_tuple', tuple())
            object.__setattr__(self, '_tuple_len', 0)
            object.__setattr__(self, 'dataType', DataType.STRING)

        else:
            num_values = len(value)
            if num_values == 0:
                raise ValueError('Cannot have an empty sequence as a value')
            object.__setattr__(self, '_tuple_len', num_values)
            if all(isinstance(e, str) for e in value):
                object.__setattr__(
                    self, '_value_str_tuple',
                    tuple(e for e in value)
                )
                object.__setattr__(self, '_value_str', '')
                object.__setattr__(self, '_value_data_tuple', tuple())
                object.__setattr__(self, 'dataType', DataType.COMPONENT)
            elif all(isinstance(e, DataElement) and e.dataType == DataType.COMPONENT for e in value):
                object.__setattr__(
                    self, '_value_data_tuple',
                    tuple(copy.deepcopy(e) for e in value)
                )
                object.__setattr__(self, '_value_str_tuple', tuple())
                object.__setattr__(self, '_value_str', '')
                object.__setattr__(self, 'dataType', DataType.MULTI_COMPONENT)
            else:
                raise ValueError(
                    'If value is a list then they must all be of type string or '
                    'all Component type DataElements.'
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
                    'A string type DataElement does not have any index.'
                )
            return self._value_str
        else:
            if not index or index < 1 or index > self._tuple_len:
                raise IndexError(
                    f'Elements are 1-indexed. Index value of {index} is outside'
                    f' of bounds 1 and {self._tuple_len}.'
                )
            if self.dataType == DataType.COMPONENT:
                return self._value_str_tuple[index - 1]

            return self._value_data_tuple[index - 1]

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
            repr = "{"
            for index, ele in enumerate(self._value_str_tuple):
                repr = repr + f"\n  {index + 1}:'{ele}'"
                if index != self._tuple_len - 1:
                    repr += ','
            repr = repr + "\n}"
            return repr

        repr = '['
        for index, ele in enumerate(self._value_data_tuple):
            repr += f"\n{ele}"
            if index != self._tuple_len - 1:
                repr += ','
        repr = repr + "\n]"
        return repr

    def __eq__(self: DataElement, other: object) -> bool:
        """
        Equality. Checks if the DataTypes are the same. Then checks
        to see if the appropriate value is the same

        :param self: self
        :type self: DataElement
        :param other: other object to check
        :type other: object
        :return: true if they are equal false otherwise
        :rtype: bool
        """
        if not isinstance(other, DataElement):
            return False
        if self.dataType != other.dataType:
            return False
        if self.dataType == DataType.STRING:
            return self._value_str == other._value_str
        if self.dataType == DataType.COMPONENT:
            return self._value_str_tuple == other._value_str_tuple
        return self._value_data_tuple == other._value_data_tuple

    def __hash__(self) -> int:
        """
        Generates hash code. Based on has of string representation.
        Two equal objects will have the same string representation and thus
        the same hash code

        :return: hash code
        :rtype: int
        """
        return self.__repr__().__hash__()


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
