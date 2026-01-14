import json
from pathlib import Path


class Scoreboard:
    def __init__(self, path="data/scores.json", max_entries=10):
        self.path = Path(path)
        self.max_entries = max_entries
        self.entries = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.entries = json.loads(self.path.read_text())
            except Exception:
                self.entries = []
        else:
            self.entries = []

    def _save(self):
        self.path.write_text(json.dumps(self.entries, indent=2))

    def add_score(self, name: str, time_seconds: float, kills: int):
        name = name.strip() or "Anonymous"
        self.entries.append({
            "name": name,
            "time": time_seconds,
            "kills": kills,
        })
        self.entries.sort(key=lambda e: e["time"], reverse=True)
        self.entries = self.entries[: self.max_entries]
        self._save()

    def get_scores(self):
        return list(self.entries)
