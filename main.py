import argparse
import platform

import webview

import pysrc.web
from pysrc.web import start_server, window

args_parser = argparse.ArgumentParser()
args_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
args = args_parser.parse_args()

server, thread, server_recver, thread_recver = start_server()
if platform.system() == "Windows":
    webview.start(window, gui="qt", debug=args.debug)
else:
    webview.start(window, debug=args.debug)

pysrc.web.should_exit = True
server.should_exit = True
server_recver.should_exit = True

print("Shutting down server...")
thread.join()
thread_recver.join()
print("Server stopped.")
