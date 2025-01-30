"""
Formatting class.

Provides several useful methods and classes for formatting text in WLW.
"""
import re
from enum import Enum

class FormatType(Enum):
    """
    Formatting types that should be used for all format related functions.

    Controls the formatting keys for all text, but can also be used as a reference in Chapters.
    """
    ITALIC = "<i>"
    BOLD = "<b>"
    SKIP = "<s>" # just for show, since we compile SKIP manually
    WAIT = "<w>" # just for show, since we compile WAIT manually

    @classmethod
    def compile_regex(cls) -> dict:
        """
        Dynamically compile regular expressions for all set format types.

        Note that WAIT/SKIP is a special type, and will be compiled regardless.

        Returns:
        dict: The compiled regular expressions.
        """
        regex_patterns = {fmt: re.compile(re.escape(fmt.value) + r'(.*?)' + re.escape("</" + fmt.value[1:])) for fmt in cls if fmt not in [cls.WAIT, cls.SKIP]}
        # WAIT is special, because it has no closing tag and contains a number.
        regex_patterns[cls.WAIT] = re.compile(r'<w=(\d+(\.\d+)?)>')
        regex_patterns[cls.SKIP] = re.compile(r'<s>')

        return regex_patterns

def format_line(text: str):
    """
    Creates a list of tuples containing text styles from a string that can allow for formatted printing.

    Args:
    text (str): The text to format.

    Returns:
    list[tuple[FormatType, str|float]]: The formatted text, split by formatting styles and their values.
    """
    regex = FormatType.compile_regex() # get all of the compiled regex patterns for each format

    out = []
    pos = 0

    while pos < len(text):
        # Find the next match for any format type
        next_match = None
        next_fmt = None
        for fmt, pattern in regex.items():
            match = pattern.search(text, pos)
            if match and (next_match is None or match.start() < next_match.start()):
                next_match = match
                next_fmt = fmt

        if next_match:
            # Add unformatted text before the match
            if next_match.start() > pos:
                out.append((None, text[pos:next_match.start()]))

            # Add the formatted text
            if next_fmt == FormatType.SKIP: # skipping
                out.append((next_fmt, None))
            elif next_fmt == FormatType.WAIT: # wait
                out.append((next_fmt, float(next_match.group(1))))
            else:
                out.append((next_fmt, next_match.group(1))) # any other

            # Update the current position
            pos = next_match.end()
        else:
            # Add the remaining unformatted text
            out.append((None, text[pos:]))
            break

    return out

def get_format_up_to(fmt: list[tuple[FormatType, str|float]], pos: int) -> list[tuple[FormatType, str|float]]:
    """
    Split a format list up to a certain position in the text.

    Args:
    fmt (list[tuple[FormatType, str|float]]): The formatted text to split.
    pos (int): The position to split the text at.
    
    Returns:
    list[tuple[FormatType, str|float]: A list of tuples containing text and its formatting type up to the requested character.
    """

    ipos = 0 # internal pos
    out = []
    for chunk in fmt:
        if chunk[0] in [FormatType.SKIP, FormatType.WAIT]:
            out.append(chunk)
            continue

        if ipos + len(chunk[1]) < pos:
            ipos += len(chunk[1])
            out.append(chunk)
        elif ipos + len(chunk[1]) >= pos:
            out.append((chunk[0], chunk[1][:pos-ipos]))
            break 

    return out

def get_format_max_length(fmt: list[tuple[FormatType, str|float]]) -> int:
    """
    Get the maximum length of a formatted list, excluding WAIT and SKIP values..

    Args:
    fmt (list[tuple[FormatType, str|float]]): The formatted text to get the length of.

    Returns:
    int: The maximum length of the format list, excluding WAIT and SKIP.
    """

    out = 0
    for chunk in fmt:
        if chunk[0] in [FormatType.SKIP, FormatType.WAIT]:
            continue

        out += len(chunk[1])
    
    return out
