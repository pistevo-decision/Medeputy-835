from typing import List
from unittest.mock import patch, mock_open
from x12_segment_parser import X12Parser, SegmentInfo, DataElement, DataType
from x12_segment_parser._delimiters import Delimiters
import pytest


@pytest.fixture
def filepath() -> str:
    return '/some/path'


@pytest.fixture
def std_file_content() -> str:
    return (
        "ISA*00*          *00*          *30*341858379      *30*820836617      "
        "*250717*2350*^*00501*290360607*0*P*:~GS*HP*ECHOH*820836617*20250717*"
        "2350*1*X*005010X221A1~ST*835*000000001~BPR*I*5588.55*C*ACH*CCP*01*"
        "044115126*DA*01669508612C*1341858379**01*055002707*DA*1000216278415*"
        "20250722"
    )


@pytest.fixture
def parser() -> X12Parser:
    return X12Parser()


@pytest.fixture
def delimiters() -> Delimiters:
    return Delimiters(
        segment_term='~',
        element_sep='*',
        component_sep=':',
        repeat_sep='^'
    )


def test_create():
    parser = X12Parser(256)
    assert f"{parser}" == "X12Parser(256)"


def test_delimiters(parser: X12Parser, std_file_content: str, filepath: str):
    with patch('builtins.open', mock_open(read_data=std_file_content.encode())):
        delimiters = parser._determine_delimiters(filepath)  # type: ignore

    assert delimiters.component_sep == ':'
    assert delimiters.element_sep == '*'
    assert delimiters.repeat_sep == '^'
    assert delimiters.segment_term == '~'


def test_delimiters_short(parser: X12Parser, filepath: str):
    with pytest.raises(ValueError) as error:

        with patch('builtins.open', mock_open(read_data='abc'.encode())):
            parser._determine_delimiters(filepath)  # type: ignore

    assert error.type is ValueError
    assert 'File is too short to be a valid X12 Document.' in str(error.value)


def test_delimiters_invalid(
        parser: X12Parser,
        filepath: str,
        std_file_content: str
):
    file_content = f'ABC{std_file_content}'
    with pytest.raises(ValueError) as error:

        with patch('builtins.open', mock_open(read_data=file_content.encode())):
            parser._determine_delimiters(filepath)  # type: ignore

    assert error.type is ValueError
    assert 'X12 document must begin with ISA segment.' in str(error.value)


def test_parse_segment_simple(
        parser: X12Parser,
        delimiters: Delimiters
):
    raw_segment = "LQ*3"

    segment = parser._parse_segment(raw_segment, delimiters)  # type: ignore

    assert segment.name == 'LQ'
    assert segment.has_element_idx(1)
    assert segment.get_element(1) == DataElement('3')

    raw_segment = 'REF*6R *4'
    segment = parser._parse_segment(raw_segment, delimiters)  # type: ignore
    assert segment.name == 'REF'
    assert len(segment) == 3
    assert segment.get_element(1) == DataElement('6R')
    assert segment.get_element(2) == DataElement('4')

    raw_segment = 'CAS**thing*'
    segment = parser._parse_segment(raw_segment, delimiters)  # type: ignore
    assert segment.name == 'CAS'
    assert len(segment) == 4
    assert segment.get_element(1).is_empty()
    assert segment.get_element(2).get_value() == 'thing'
    assert segment.get_element(3).is_empty()


def test_parse_segment_components(
        parser: X12Parser,
        delimiters: Delimiters
):
    raw = "SVC*HC:T1019*246.21*0*0590*32**0"
    segment = parser._parse_segment(raw, delimiters)  # type: ignore

    assert segment.name == 'SVC'
    assert len(segment) == 8
    element = segment.get_element(1)
    assert element.dataType == DataType.COMPONENT
    assert len(element) == 2
    assert element.get_value(1) == 'HC'
    assert element.get_value(2) == 'T1019'
    assert segment.get_element(2).get_value() == '246.21'
    assert segment.get_element(3).get_value() == '0'
    assert segment.get_element(4).get_value() == '0590'
    assert segment.get_element(5).get_value() == '32'
    assert segment.get_element(6).is_empty()
    assert segment.get_element(7).get_value() == '0'

    raw = 'TV*:*else'
    segment = parser._parse_segment(raw, delimiters)  # type: ignore
    assert len(segment) == 3
    element = segment.get_element(1)
    assert element.dataType == DataType.COMPONENT
    assert len(element) == 2
    assert element.get_value(1) == ''
    assert element.get_value(2) == ''


def test_parse_segment_repeats(
        parser: X12Parser,
        delimiters: Delimiters
):
    raw = 'RAS*something^partial:value^^*else'
    segment = parser._parse_segment(raw, delimiters)  # type: ignore

    assert len(segment) == 3
    element = segment.get_element(1)
    assert element.dataType == DataType.MULTI_COMPONENT
    assert len(element) == 4
    repeats = element.get_repeats()
    assert len(repeats) == 4
    for repeat in repeats:
        assert repeat.dataType == DataType.COMPONENT
    assert repeats[0].get_value(1) == 'something'
    assert len(repeats[0]) == 1

    assert len(repeats[1]) == 2
    assert repeats[1].get_value(1) == 'partial'
    assert repeats[1].get_value(2) == 'value'

    assert len(repeats[2]) == 1
    assert repeats[2].get_value(1) == ''

    assert len(repeats[3]) == 1
    assert repeats[3].get_value(1) == ''

    assert segment.get_element(2).get_value() == 'else'


def test_full_parse(
        filepath: str,
        std_file_content: str
):
    parser = X12Parser(110)
    segments: List[SegmentInfo] = []
    with patch('builtins.open', mock_open(read_data=std_file_content.encode())):
        for segment in parser.parse_file(filepath):
            segments.append(segment)

    assert segments[0].name == 'ISA'
    assert len(segments[0]) == 17
