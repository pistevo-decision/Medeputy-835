from typing import Generator, List
from x12_segment_parser._delimiters import Delimiters
from x12_segment_parser.segment import DataElement, SegmentInfo


class X12Parser:
    """
    Class that will parse an X12 file and yield information about each segment.
    """

    _chunk_size: int

    def __init__(self: X12Parser, chunk_size: int = 65536):
        """
        Initialization

        :param self: self
        :type self: X12Parser
        :param chunk_size: streaming chunk size in bytes, defaults to 65536
        :type chunk_size: int, optional
        """

        self._chunk_size = chunk_size

    def __repr__(self: X12Parser) -> str:
        """
        Generates string representation of parser

        :param self: self
        :type self: X12Parser
        :return: string representation
        :rtype: str
        """

        return f"X12Parser({self._chunk_size})"

    def _determine_delimiters(self: X12Parser, filepath: str) -> Delimiters:
        """
        Reads the first segment of the x12 file and determines the delimiters
        that will be used for the file. Returns an object representing the 
        delimiters used in the file

        :param self: self
        :type self: X12Parser
        :param filepath: path for x12 file to be parsed
        :type filepath: str
        :raises ValueError: if the file is less than 106 bytes (too short)
        :raises ValueError: if the file does not start with the proper bytes
        :return: delimiters used in the file.
        :rtype: Delimiters
        """

        with open(filepath, 'rb') as file:
            header = file.read(106)
            if len(header) < 106:
                raise ValueError(
                    'File is too short to be a valid X12 Document.')
            if not header.startswith(b'ISA'):
                raise ValueError("X12 document must begin with ISA segment.")

            element_sep = chr(header[3])
            component_sep = chr(header[104])
            segment_term = chr(header[105])
            repeat_sep = chr(header[82])
            return Delimiters(
                element_sep, component_sep, repeat_sep, segment_term
            )

    def _iter_segments(
            self: X12Parser,
            filepath: str,
            delimiters: Delimiters
    ) -> Generator[str, None, None]:
        """
        Given filepath and delimiters this will generate an iterable for
        each of the segments in the x12 835 file. Each segment will be a utf-8
        string

        :param self: self
        :type self: X12Parser
        :param filepath: path for x12 file that is being parsed
        :type filepath: str
        :param delimiters: delimiters for the x12 file (determined by ISA seg)
        :type delimiters: Delimiters
        :yield: String representing the segment
        :rtype: Generator[str, None, None]
        """

        terminator = delimiters.segment_term
        terminator_byte = terminator.encode()

        leftover = b''

        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(self._chunk_size)
                if not chunk:
                    break

                chunk = leftover + chunk
                segments = chunk.split(terminator_byte)

                leftover = segments.pop()

                for raw_segment in segments:
                    raw_segment = raw_segment.strip()
                    if raw_segment:
                        yield raw_segment.decode('utf-8')
        if leftover.strip():
            yield leftover.strip().decode('utf-8')

    def parse_component(
            self: X12Parser,
            raw: str,
            delimiters: Delimiters
    ) -> DataElement:
        """
        Parses a component (sub element) from a raw string

        :param self: self
        :type self: X12Parser
        :param raw: raw string representing the entire element
        :type raw: str
        :param delimiters: delimiters for the file
        :type delimiters: Delimiters
        :return: DataElement of type Component with all necessary values
        :rtype: DataElement
        """

        raw_components = raw.split(delimiters.component_sep)
        components: List[str] = [v.strip() for v in raw_components]
        return DataElement(components)

    def parse_segment(
            self: X12Parser,
            raw_segment: str,
            delimiters: Delimiters,
            is_isa_seg: bool = False
    ) -> SegmentInfo:
        """
        Given a raw string representing an entire component it will return
        a Segment info object.

        :param self: self
        :type self: X12Parser
        :param raw_segment: raw string for the entire segment
        :type raw_segment: str
        :param delimiters: Delimiters for this x12 file
        :type delimiters: Delimiters
        :param is_isa_seg: ISA segments are special and must be handled as such 
        (they must not have sub components), defaults to False
        :type is_isa_seg: bool, optional
        :return: Segment info object
        :rtype: SegmentInfo
        """
        raw_elements = raw_segment.split(delimiters.element_sep)
        name = raw_elements.pop(0).strip()
        elements: List[DataElement] = []

        for raw_element in raw_elements:
            if delimiters.repeat_sep in raw_element and not is_isa_seg:
                raw_sub_elements = raw_element.split(delimiters.repeat_sep)
                sub_elements: List[DataElement] = []
                for raw_sub_element in raw_sub_elements:
                    sub_elements.append(
                        self.parse_component(raw_sub_element, delimiters)
                    )
                elements.append(DataElement(sub_elements))

            elif delimiters.component_sep in raw_element and not is_isa_seg:
                elements.append(self.parse_component(raw_element, delimiters))
            else:
                elements.append(DataElement(raw_element.strip()))

        return SegmentInfo(name, elements)

    def parse_file(
            self: X12Parser,
            filepath: str
    ) -> Generator[SegmentInfo, None, None]:
        """
        Given a file path this function will determine its format and 
        Generate a series of SegmentInfo objects that represent each segment
        in the file

        :param self: self
        :type self: X12Parser
        :param filepath: filepath for x12 file
        :type filepath: str
        :yield: SegmentInfo representation of X12 segment
        :rtype: Generator[SegmentInfo, None, None]
        """
        delimiters = self._determine_delimiters(filepath)
        is_isa_seg = True

        for raw_segment in self._iter_segments(filepath, delimiters):
            yield self.parse_segment(raw_segment, delimiters, is_isa_seg)
            is_isa_seg = False
