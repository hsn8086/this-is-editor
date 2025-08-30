import argparse
import platform
import shlex
import subprocess

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--mode",
    choices=["onefile", "dir"],
    default="onefile",
    help="Build mode: onefile or dir (default: onefile)",
)
arg_parser.add_argument(
    "--debug", action="store_true", help="Build with debug symbols (default: False)"
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
    base.append("--enable-plugin=qt-plugins")
base.extend(
    [
        "--output-dir=.dist",
        "main.py",
    ]
)

subprocess.run(shlex.join(base), shell=True)
