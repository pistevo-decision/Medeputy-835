from io import RawIOBase, BufferedIOBase
from pathlib import Path
from typing import Generator, List, Union
from medeputy835._delimiters import Delimiters
from medeputy835.segment import DataElement, SegmentInfo

Source = Union[str, Path, RawIOBase, BufferedIOBase]


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

    def _open_source(
            self: X12Parser,
            source: Source
    ):
        """
        Context manager that normalizes a filepath or stream into a readable
        binary stream. If a filepath is provided it is opened and owned by
        this context manager (closed on exit). If a stream is provided the
        caller retains ownership and it is not closed on exit.

        :param self: self
        :type self: X12Parser
        :param source: filepath or already-open binary stream
        :type source: Source
        :return: context manager yielding a binary stream
        """
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            if isinstance(source, (str, Path)):
                f = open(source, 'rb')
                try:
                    yield f
                finally:
                    f.close()
            else:
                yield source

        return _cm()

    def _determine_delimiters(
            self: X12Parser,
            source: Source
    ) -> Delimiters:
        """
        Reads the first segment of the x12 source and determines the delimiters
        that will be used. Returns an object representing the delimiters.

        :param self: self
        :type self: X12Parser
        :param source: filepath or already-open binary stream
        :type source: Source
        :raises ValueError: if the source is less than 106 bytes (too short)
        :raises ValueError: if the source does not start with the proper bytes
        :return: delimiters used in the file.
        :rtype: Delimiters
        """

        with self._open_source(source) as stream:
            header = stream.read(106)
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
            source: Source,
            delimiters: Delimiters
    ) -> Generator[str, None, None]:
        """
        Given a source and delimiters this will generate an iterable for
        each of the segments in the x12 file. Each segment will be a utf-8
        string.

        :param self: self
        :type self: X12Parser
        :param source: filepath or already-open binary stream
        :type source: Source
        :param delimiters: delimiters for the x12 file (determined by ISA seg)
        :type delimiters: Delimiters
        :yield: String representing the segment
        :rtype: Generator[str, None, None]
        """

        terminator_byte = delimiters.segment_term.encode()
        leftover = b''

        with self._open_source(source) as stream:
            while True:
                chunk = stream.read(self._chunk_size)
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

    def _parse_component(
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

    def _parse_segment(
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
                        self._parse_component(raw_sub_element, delimiters)
                    )
                elements.append(DataElement(sub_elements))

            elif delimiters.component_sep in raw_element and not is_isa_seg:
                elements.append(self._parse_component(raw_element, delimiters))
            else:
                elements.append(DataElement(raw_element.strip()))

        return SegmentInfo(name, elements)

    def parse(
            self: X12Parser,
            source: Source
    ) -> Generator[SegmentInfo, None, None]:
        """
        Given a filepath or an already-open binary stream, determines the
        x12 format and generates a series of SegmentInfo objects representing
        each segment.

        If a filepath is provided the file is opened and closed internally.
        If a stream is provided the caller retains ownership and is responsible
        for closing it.

        :param self: self
        :type self: X12Parser
        :param source: filepath or already-open binary stream
        :type source: Source
        :yield: SegmentInfo representation of X12 segment
        :rtype: Generator[SegmentInfo, None, None]
        """

        with self._open_source(source) as stream:
            delimiters = self._determine_delimiters(stream)
            stream.seek(0)
            is_isa_seg = True
            for raw_segment in self._iter_segments(stream, delimiters):
                segment = self._parse_segment(
                    raw_segment, delimiters, is_isa_seg)
                is_isa_seg = False
                yield segment
