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

    def get_repeats(self: DataElement) -> Tuple[DataElement, ...]:
        """
        Returns the list of repeats for this DataElement. 
        This occurs when a segment has a sub-component that is allowed to repeat

        :param self: self
        :type self: DataElement
        :raises TypeError: If called when the dataType is not 
        MULTI_COMPONENT
        :return: A tuple representing the repeated components
        :rtype: Tuple[DataElement, ...]
        """
        if self.dataType != DataType.MULTI_COMPONENT:
            raise TypeError(
                'There are no repeats for a non MULTI_COMPONENT DataElement.'
            )
        return self._value_data_tuple

    def has_component_idx(
            self: DataElement,
            idx: int,
            ignore_empty: bool = True
    ) -> bool:
        """
        Checks to see if the component at the given component index (1-indexed)
        is present and nonempty (optional)

        To retrieve the component value at the given index use 
        `getValue()` method

        :param self: self
        :type self: DataElement
        :param idx: component index (1-indexed)
        :type idx: int
        :param ignore_empty: if true then empty strings will return false, 
        defaults to True
        :type ignore_empty: bool, optional
        :raises TypeError: If called with MULTI COMPONENT or STRING 
        type DataElement
        :return: True if there is a component at the specified index
        :rtype: bool
        """
        if self.dataType != DataType.COMPONENT:
            raise TypeError(
                'There are no components for a non COMPONENT type DataElement.'
            )
        valid_idx = 0 < idx <= self._tuple_len
        if ignore_empty:
            return valid_idx and self._value_str_tuple[idx - 1] != ''
        return valid_idx

    def is_empty(self: DataElement) -> bool:
        """
        Checks of the data element is empty.
        Note that only DataElements of type STRING can be empty

        :param self: self
        :type self: DataElement
        :return: True if it is empty (string value is empty)
        :rtype: bool
        """
        return self.dataType == DataType.STRING and self._value_str == ''

    def __str__(self: DataElement) -> str:
        """
        Creates String representation

        :param self: self
        :type self: DataElement
        :return: String representation
        :rtype: str
        """
        if self.dataType == DataType.STRING:
            return f"'{self._value_str}'"
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

    def __hash__(self: DataElement) -> int:
        """
        Generates hash code. Based on has of string representation.
        Two equal objects will have the same string representation and thus
        the same hash code

        :return: hash code
        :rtype: int
        """
        return self.__str__().__hash__()

    def __len__(self: DataElement) -> int:
        """
        Returns the length of the internal components or repeats

        :param self: self
        :type self: DataElement
        :raises TypeError: if called with a STRING type DataElement
        :return: size of internal components / repeats
        :rtype: int
        """
        if self.dataType == DataType.STRING:
            raise TypeError(
                'DataElement of type STRING does not have a length.'
            )
        return self._tuple_len
