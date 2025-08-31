"""Utility functions for formatting strings with file path details.

This module provides a `formatter` function that formats a string
using various attributes of a given file path.
"""

from pathlib import Path


def formatter(val: str, *, file_path: Path, executable: str = "None") -> str:
    """Format a string with details from a file path.

    Args:
        val (str): String to be formatted. It should contain placeholders
            that correspond to the available file path components and the executable.
        file_path (Path): Path to the file whose details will be used for formatting.
        executable (str, optional): Name of the executable. Defaults to "None".

    Returns:
        str: Formatted string with placeholders replaced by the corresponding values.

    Placeholders available for formatting:
        - {file}: The full file path as a string.
        - {fileWithoutExt}: The file path without the extension.
        - {fileName}: The name of the file (including the extension).
        - {fileStem}: The name of the file without the extension.
        - {fileExt}: The file extension (including the dot).
        - {fileParent}: The parent directory of the file as a string.
        - {fileParentName}: The name of the parent directory.
        - {executable}: The name of the executable (default is "None").

    """
    file = fileWithoutExt = fileName = fileStem = fileExt = fileParent = (
        fileParentName
    ) = "None"
    if file_path:
        file = str(file_path)
        fileWithoutExt = str(file_path.with_suffix(""))
        fileName = file_path.name
        fileStem = file_path.stem
        fileExt = file_path.suffix
        fileParent = str(file_path.parent)
        fileParentName = file_path.parent.name

    return val.format(
        file=file,
        fileWithoutExt=fileWithoutExt,
        fileName=fileName,
        fileStem=fileStem,
        fileExt=fileExt,
        fileParent=fileParent,
        fileParentName=fileParentName,
        executable=executable,
    )
