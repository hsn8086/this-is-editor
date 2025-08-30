import threading

from loguru import logger
from watchfiles import watch


class Watcher:
    def __init__(self, callback: callable) -> None:
        self.callback = callback
        self.task = None
        self.stop_event = None

    def _watch_loop(self, path: str) -> None:
        logger.debug(f"Starting to watch: {path}")

        def _inner() -> None:
            for changes in watch(path, stop_event=self.stop_event):
                logger.debug(f"Detected changes: {changes}")
                for change, file_path in changes:
                    self.callback(file_path)

        self.stop_event = threading.Event()
        self.task = threading.Thread(target=_inner, daemon=True)
        self.task.start()

    def stop(self) -> None:
        if self.stop_event and self.task:
            self.stop_event.set()
            self.task.join()
            self.stop_event = None
            self.task = None

    def create_observer(self, path: str) -> None:
        self.stop()
        self._watch_loop(path)
