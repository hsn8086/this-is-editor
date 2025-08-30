from pathlib import Path


def format(val: str, *, file_path: Path, executable: str = "None") -> str:
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
