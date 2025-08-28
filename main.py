import argparse
import platform

import webview
from loguru import logger

import pysrc.web
from pysrc.user_data import user_log_dir
from pysrc.web import start_server, window

args_parser = argparse.ArgumentParser()
args_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
args = args_parser.parse_args()

logger.add(
    user_log_dir / "this_is_editor.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG" if args.debug else "INFO",
)

server, thread, server_recver, thread_recver = start_server()
if platform.system() == "Windows":
    webview.start(window, gui="qt", debug=args.debug)
else:
    webview.start(window, debug=args.debug)

pysrc.web.should_exit = True
server.should_exit = True
server_recver.should_exit = True

logger.info("Shutting down server...")
thread.join()
thread_recver.join()
logger.info("Server shut down successfully.")
