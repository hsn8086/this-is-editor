"""Builder script for packaging Python applications.

This script uses Nuitka to build Python applications into standalone executables.
It supports options for build mode, debug symbols, and platform-specific configurations.
"""

import argparse
import platform
import subprocess
from collections.abc import Sequence

from loguru import logger


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line build options."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mode",
        choices=["onefile", "dir"],
        default="onefile",
        help="Build mode: onefile or dir (default: onefile)",
    )
    arg_parser.add_argument(
        "--debug",
        action="store_true",
        help="Build with debug symbols (default: False)",
    )
    return arg_parser.parse_args(argv)


def build_command(args: argparse.Namespace, system: str | None = None) -> list[str]:
    """Build the Nuitka command for the requested platform and mode."""
    command = [
        "uv",
        "run",
        "nuitka",
        "--standalone",
        "--include-data-dir=web=web",
        "--include-module=fastapi",
        "--include-module=uvicorn",
        "--assume-yes-for-downloads",
    ]
    if (system or platform.system()) == "Windows" and not args.debug:
        command.append("--windows-disable-console")
    if args.mode == "onefile":
        command.append("--onefile")
    if args.debug:
        command.extend(["--lto=no", "--debugger"])
    command.extend(
        [
            "--enable-plugin=pywebview",
            "--output-dir=.dist",
            "main.py",
        ],
    )
    return command


def main(argv: Sequence[str] | None = None) -> int:
    """Run Nuitka and propagate its exit status to the caller."""
    command = build_command(parse_args(argv))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        logger.error("Build process failed with return code {}", error.returncode)
        logger.error("Command: {}", error.cmd)
        logger.error("Please check the build configuration and try again.")
        return error.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
