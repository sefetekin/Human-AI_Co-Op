import json
from pathlib import Path


class Scoreboard:
    def __init__(self, path="data/scores.json", max_entries=10):
        self.path = Path(path)
        self.max_entries = max_entries
        self.entries = []
        self._load()

    # -------------------------------------------------

    def _load(self):
        if self.path.exists():
            try:
                self.entries = json.loads(self.path.read_text())
            except Exception:
                self.entries = []
        else:
            self.entries = []

    def _save(self):
        # keep only most recent max_entries
        self.entries = self.entries[-self.max_entries :]
        self.path.write_text(json.dumps(self.entries, indent=2))

    # -------------------------------------------------
    # ADD SCORE (UPDATED SCHEMA)
    # -------------------------------------------------

    def add_score(
        self,
        name,
        age_group,
        mood,
        likes,
        time_survived,
        kills,
    ):
        entry = {
            "name": name or "Anonymous",
            "age_group": age_group,
            "mood": mood,
            "likes": likes,
            "time": time_survived,
            "kills": kills,
        }

        self.entries.append(entry)
        self._save()
        return entry

    # -------------------------------------------------

    def get_scores(self):
        return list(self.entries)

    # -------------------------------------------------
    # QUERY / SORT
    # -------------------------------------------------

    def get_entries(
        self,
        sort_by="time",
        descending=True,
        search="",
        age_group=None,
        mood=None,
    ):
        entries = self.entries

        if search:
            entries = [
                e for e in entries
                if search.lower() in e.get("name", "").lower()
            ]

        if age_group:
            entries = [
                e for e in entries
                if e.get("age_group") == age_group
            ]

        if mood:
            entries = [
                e for e in entries
                if e.get("mood") == mood
            ]

        entries = sorted(
            entries,
            key=lambda e: e.get(sort_by, 0),
            reverse=descending,
        )
        return entries

    # -------------------------------------------------
    # PREVIEW (UNCHANGED LOGIC, SAFER)
    # -------------------------------------------------

    def get_preview_for_entry(self, entry, window=2):
        entries = self.get_entries(sort_by="time", descending=True)

        if entry not in entries:
            return [], -1

        idx = entries.index(entry)
        start = max(0, idx - window)
        end = min(len(entries), idx + window + 1)

        return entries[start:end], idx
