from dataclasses import dataclass

@dataclass(frozen=True)
class Delimiters:
    element_sep: str
    component_sep: str
    repeat_sep: str
    segment_term: str
