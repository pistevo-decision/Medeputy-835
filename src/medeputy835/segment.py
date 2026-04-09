import copy
from dataclasses import dataclass
from typing import Tuple, Sequence
from medeputy835.data_element import DataElement


@dataclass(frozen=True)
class SegmentInfo:
    """
    Class for keeping track of segment info
    """
    name: str
    _elements: Tuple[DataElement]

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
        object.__setattr__(self, '_elements', tuple(
            copy.deepcopy(e) for e in elements
        ))

    def has_element_idx(
            self: SegmentInfo,
            idx: int,
            ignore_empty: bool = True
    ) -> bool:
        """
        Checks to see if there is an element at the given index.
        Note that indices are 1-indexed

        :param self: self
        :type self: SegmentInfo
        :param idx: Index of element (1-indexed)
        :type idx: int
        :param ignore_empty: If true then an empty DataElements are considered
        not present, defaults to True
        :type ignore_empty: bool, optional
        :return: True if there is a DataElement at that index
        :rtype: bool
        """
        valid_idx = 0 < idx <= len(self._elements)
        if ignore_empty:
            return valid_idx and not self._elements[idx - 1].is_empty()
        return valid_idx

    def get_element(self: SegmentInfo, idx: int) -> DataElement:
        """
        Returns the DataElement at the given index

        :param self: self
        :type self: SegmentInfo
        :param idx: Element index (1-indexed)
        :type idx: int
        :raises IndexError: If index is out of bounds (1-indexed)
        :return: DataElement at that location
        :rtype: DataElement
        """
        if not self.has_element_idx(idx, ignore_empty=False):
            raise IndexError('Index is out of range. Items are 1-indexed.')
        return self._elements[idx - 1]

    def __str__(self: SegmentInfo) -> str:
        """
        Generates String representation

        :param self: self
        :type self: SegmentInfo
        :return: String representation
        :rtype: str
        """
        string = f"{self.name}("
        for idx, element in enumerate(self._elements):
            string += f"\n{idx + 1}:{element}"
            if idx < len(self._elements) - 1:
                string += ','
        string += '\n)'
        return string

    def __len__(self: SegmentInfo) -> int:
        """
        Returns the number of elements in this segment instance

        :param self: self
        :type self: SegmentInfo
        :return: Number of elements in segment instance
        :rtype: int
        """
        return len(self._elements) + 1  # adding one b/c the name is an element
