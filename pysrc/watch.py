"""Module for watching directories for file changes.

This module provides the Watcher class, which monitors a directory for file changes
and triggers a callback function when changes are detected.
"""

import threading

from loguru import logger
from watchfiles import watch


class Watcher:
    """Watches a directory for file changes and triggers a callback.

    Args:
        callback (callable): Function to call when a file changes.

    """

    def __init__(self, callback: callable) -> None:
        """Initialize the Watcher.

        Args:
            callback (callable): Function to call when a file changes.

        """
        self.callback = callback
        self.task = None
        self.stop_event = None

    def _watch_loop(self, path: str) -> None:
        """Start watching the given path for changes.

        Args:
            path (str): Directory path to watch.

        """
        logger.debug(f"Starting to watch: {path}")

        def _inner() -> None:
            for changes in watch(path, stop_event=self.stop_event):
                logger.debug(f"Detected changes: {changes}")
                for _, file_path in changes:
                    self.callback(file_path)

        self.stop_event = threading.Event()
        self.task = threading.Thread(target=_inner, daemon=True)
        self.task.start()

    def stop(self) -> None:
        """Stop the watcher thread if running.

        Returns:
            None

        """
        if self.stop_event and self.task:
            self.stop_event.set()
            self.task.join()
            self.stop_event = None
            self.task = None

    def create_observer(self, path: str) -> None:
        """Create a new observer for the given path, stopping any previous observer.

        Args:
            path (str): Directory path to observe.

        Returns:
            None

        """
        self.stop()
        self._watch_loop(path)
