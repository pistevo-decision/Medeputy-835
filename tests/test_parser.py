from unittest.mock import patch, mock_open
from x12_segment_parser import X12Parser
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
