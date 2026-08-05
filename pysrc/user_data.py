"""Set up user-specific directories for application data."""

import os
from dataclasses import dataclass
from pathlib import Path

import appdirs

from .runtime import DEV_USER_DATA_DIR_ENV


@dataclass(frozen=True)
class UserDirectories:
    """Resolved locations for TIE's user-managed files."""

    data: Path
    config: Path
    log: Path


def resolve_user_directories(dev_root: str | Path | None = None) -> UserDirectories:
    """Resolve platform defaults or isolated development directories."""
    if dev_root:
        root = Path(dev_root).expanduser().resolve()
        return UserDirectories(
            data=root / "data",
            config=root / "config",
            log=root / "log",
        )

    return UserDirectories(
        data=Path(appdirs.user_data_dir("this_is_editor", "hsn8086")),
        config=Path(appdirs.user_config_dir("this_is_editor", "hsn8086")),
        log=Path(appdirs.user_log_dir("this_is_editor", "hsn8086")),
    )


def ensure_user_directories(directories: UserDirectories) -> None:
    """Create all resolved user directories."""
    for directory in (directories.config, directories.data, directories.log):
        directory.mkdir(parents=True, exist_ok=True)


user_directories = resolve_user_directories(os.environ.get(DEV_USER_DATA_DIR_ENV))
user_data_dir = user_directories.data
user_config_dir = user_directories.config
user_log_dir = user_directories.log
ensure_user_directories(user_directories)
