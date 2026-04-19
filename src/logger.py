import json
from pathlib import Path

class DifficultyLogger:
    def __init__(self, filepath="difficulty_log.json"):
        self.filepath = Path(filepath)
        self.data = []

        # Load existing data safely
        if self.filepath.exists():
            try:
                with open(self.filepath, "w") as f:
                    json.dump([], f)  # Clear file on new session
            except:
                self.data = []  # file empty or corrupted

    def log(self, entry: dict):
        self.data.append(entry)

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)
            
    def reset(self):
        self.data = []
        with open(self.filepath, "w") as f:
            json.dump([], f)
            
    def create_graph(self):
        import matplotlib.pyplot as plt
        with open("difficulty_log.json", "r") as f:
            data = json.load(f)

        times = [d["time"] for d in data]
        llm = [d["llm_score"] for d in data]
        system = [d["system_score"] for d in data]
        final = [d["final_difficulty"] for d in data]

        plt.figure()

        plt.plot(times, llm, label="LLM Score")
        plt.plot(times, system, label="System Score")
        plt.plot(times, final, label="Final Difficulty", linewidth=3)

        plt.xlabel("Time")
        plt.ylabel("Difficulty")
        plt.title("Difficulty Over Time")

        plt.legend()
        plt.grid()

        plt.show()

