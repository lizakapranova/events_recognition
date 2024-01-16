from dataclasses import dataclass
from typing import Callable

import pytest

from gmail import decode_text, remove_empty_lines


@dataclass
class TextFormatCase:
    name: str
    func: Callable[[str], str]
    text: str
    expected: str

    def __str__(self):
        return f"test_{self.name}({self.expected})"


FORMAT_CASES = [
    TextFormatCase(
        name='decode_text',
        func=decode_text,
        text='=?utf-8?Q?Hello, world!?=',
        expected='Hello, world!'
    ),
    TextFormatCase(
        name='decode_text',
        func=decode_text,
        text='=?utf-8?Q?=D0=9F=D1=80=D0=B8=D0=B2=D0=B5=D1=82, =D0=BC=D0=B8=D1=80!?=',
        expected='Привет, мир!'
    ),
    TextFormatCase(
        name='decode_text',
        func=decode_text,
        text='',
        expected=''
    ),
    TextFormatCase(
        name='remove_empty_lines',
        func=remove_empty_lines,
        text='',
        expected=''
    ),
]


@pytest.mark.parametrize("case", FORMAT_CASES, ids=str)
def test_text_formatting(case: TextFormatCase) -> None:
    assert case.func(case.text) == case.expected
