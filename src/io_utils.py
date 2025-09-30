"""
io_utils.py
I/O helpers to write strategies to a file streamingly.
"""
from typing import Iterable, List, Tuple, TextIO


def write_strategies(strategies: Iterable[Tuple[List[str], float]], out_fp: TextIO) -> int:
    """
    Write strategies to the given file-like object.
    Returns the number of strategies written.
    """
    count = 0
    for parts, leaf in strategies:
        definition = " & ".join(parts) if parts else "TRUE"
        out_fp.write(f"{definition} : {leaf}\n")
        count += 1
    return count
