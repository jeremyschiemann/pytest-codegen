"""Custom types."""
from pathlib import Path
from typing import TypedDict, List, Any


class ArgumentInfo(TypedDict):
    """Info about an argument of a python function."""
    name: str
    type: str
    default: Any


class FunctionInfo(TypedDict):
    """Info about a python function."""
    name: str
    arguments: List[ArgumentInfo]
    return_type: str
    docstring: str
    is_private: bool


class FileInfo(TypedDict):
    """Info about a .py file."""
    name: str
    path: Path
    module: str
    package: str
    test_name: str
    test_path: Path
    functions: List[FunctionInfo]
