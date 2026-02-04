from dataclasses import dataclass
from threading import Lock


@dataclass
class LoadingProgress:
    total: int = 0
    completed: int = 0
    message: str = ""
    
    def __post_init__(self):
        self._lock = Lock()

    def set_total(self, total: int):
        with self._lock:
            self.total = total

    def advance(self, step: int = 1, message: str = ""):
        with self._lock:
            self.completed += step
            if message:
                self.message = message

    def snapshot(self):
        with self._lock:
            return self.completed, self.total, self.message
