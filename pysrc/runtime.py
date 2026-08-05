"""Runtime overrides that must be applied before loading application state."""

import os
from pathlib import Path

DEV_USER_DATA_DIR_ENV = "TIE_DEV_USER_DATA_DIR"


def configure_dev_user_data_dir(path: Path | None) -> None:
    """Set the development user-data root for subsequently imported modules."""
    if path is not None:
        os.environ[DEV_USER_DATA_DIR_ENV] = str(path)
