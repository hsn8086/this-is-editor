"""Builder script for packaging Python applications.

This script uses Nuitka to build Python applications into standalone executables.
It supports options for build mode, debug symbols, and platform-specific configurations.
"""

import argparse
import platform
import shlex
import subprocess

from loguru import logger

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
args = arg_parser.parse_args()
base = [
    "uv",
    "run",
    "nuitka",
    "--standalone",
    "--include-data-dir=web=web",
    "--include-module=fastapi",
    "--include-module=uvicorn",
    "--assume-yes-for-downloads",
]
if platform.system() == "Windows" and not args.debug:
    base.append("--windows-disable-console")
if args.mode == "onefile":
    base.append("--onefile")
if args.debug:
    base.append("--lto=no")
    base.append("--debugger")
# qt
if platform.system() == "Windows":
    base.append("--enable-plugin=pyqt6")
    base.append("--enable-plugin=pywebview")
base.extend(
    [
        "--output-dir=.dist",
        "main.py",
    ],
)

try:
    subprocess.run(shlex.join(base), shell=True, check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Build process failed with return code {e.returncode}")
    logger.error(f"Command: {e.cmd}")
    logger.error(f"Output: {e.output}")
    logger.error("Please check the build configuration and try again.")
