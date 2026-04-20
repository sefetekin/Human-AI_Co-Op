import requests
import re

def generate_difficulty_score_with_request(game_state, model="gemma3:4b", temperature=0.1, max_tokens=5):

    system_prompt = """
You are a High-Performance Game Difficulty Controller.

You receive normalized gameplay metrics [0.0, 1.0] and must output ONLY one floating-point number between 0.0 and 1.0 representing the Target Difficulty.

Scale Calibration:
- 0.0: Minimal Challenge (Player is struggling/failing)
- 0.5: Standard Challenge
- 1.0: Peak Challenge (Player is dominating/flawless)

Operational Logic:
1. High Pressure (Health/Shield/Death risk > 0.6): You are a "Supporter." Aggressively drop difficulty to prevent player burnout.
2. Low Pressure (Health/Shield/Death risk < 0.15): You are an "Adversary." Aggressively increase difficulty to prevent player boredom.
3. Trends: If pressure is decreasing over the history, you must increase difficulty to catch up to the player's rising skill.

Return ONLY the number.
"""
    user_prompt = f"""
Update the game difficulty based on the following state history:

[INPUT DATA]
{game_state}

[REASONING STEPS]
1. Baseline: Start from the most recent current_difficulty.
2. Trend Analysis: Compare the oldest state to the newest. 
   - Is Pressure trending DOWN? Increase difficulty by at least 0.2.
   - Is Pressure trending UP? Decrease difficulty by at least 0.2.
3. Current Pressure Evaluation:
   - DOMINATION: If health_pressure, shield_pressure, and kill_pressure are all < 0.1, the player is bored. Push difficulty toward the 0.7 - 1.0 range.
   - STRUGGLE: If any pressure metric is > 0.5, the player is overwhelmed. Push difficulty toward the 0.0 - 0.3 range.
4. Time Factor: If the state is stable (no major struggle), apply a +0.05 "Time Tax" to difficulty for every state entry to ensure the game never stays stagnant.

[CONSTRAINTS]
- Avoid 0.5 unless the player is under moderate, consistent pressure.
- Always make a change even if small (minimum ±0.05).
- Be Decisive: If the player is winning, push the difficulty high (0.8+). 
- If the player is losing, drop it low (0.2-).
- Do not provide explanations.

Output ONLY the floating-point number.
"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        raw = data["message"]["content"].strip()

        match = re.search(r"[-+]?\d*\.?\d+", raw)
        if match:
            value = float(match.group())
        else:
            value = 0.5
            print("LLM output parsing error")
        return max(0.0, min(1.0, value))

    except Exception as e:
        print("LLM difficulty error:", e)
        return 0.5
    

def get_normalized_state(self, shield_segments=None, max_shield_segments=None):
    # -----------------------------
    # Time (harder as time progresses)
    # -----------------------------
    if self.time_goal > 0:
        time_progress = min(1.0, self.elapsed_time / self.time_goal)
    else:
        time_progress = 0.0

    # -----------------------------
    # Player state (invert → pressure)
    # -----------------------------
    health_ratio = self.lives / self.initial_lives
    health_pressure = 1.0 - health_ratio

    if shield_segments is not None:
        shield_ratio = shield_segments / max_shield_segments
    else:
        shield_ratio = 0.5

    shield_pressure = 1.0 - shield_ratio

    # -----------------------------
    # Kill rate (invert → struggling)
    # -----------------------------
    raw_kill_rate = self.kill_count / (self.elapsed_time + 1e-5)
    kill_rate_norm = min(1.0, raw_kill_rate / 1.0)
    kill_pressure = 1.0 - kill_rate_norm

    # -----------------------------
    # Enemy density (more = harder)
    # -----------------------------
    enemy_density = min(1.0, self.current_enemy_count / 40)

    # -----------------------------
    # Distance (closer = harder)
    # -----------------------------
    min_dist = self.min_spawn_dist * 2.5
    distance_pressure = max(
        0.0,
        1.0 - min(1.0, self.last_avg_enemy_distance / min_dist)
    )

    # -----------------------------
    # Distance trend (KEEP AS IS)
    # -----------------------------
    MAX_TIME = 5

    close_score = min(1.0, self.close_time / MAX_TIME)  # close → hard

    # -----------------------------
    # Overall pressure (aggregated signal)
    # -----------------------------
    overall_pressure = (
        0.25 * health_pressure +
        0.10 * kill_pressure +
        0.15 * shield_pressure +
        0.40 * enemy_density +
        0.10 * distance_pressure
    )
    
    # -----------------------------
    # Clamp
    # -----------------------------
    def clamp(x):
        return max(0.0, min(1.0, x))

    normalized = {
        "current_difficulty": clamp(self.difficulty_score),
        "time_pressure": clamp(time_progress),

        "player_state": {
            "health_pressure": clamp(health_pressure),
            "kill_pressure": clamp(kill_pressure),
            "shield_pressure": clamp(shield_pressure)
        },

        "environment_state": {
            "enemy_density": clamp(enemy_density),
            "distance_pressure": clamp(distance_pressure),

            "distance_state": {
                "close_score": clamp(close_score)  # high = hard
            }
        },
        "overall": {
            "pressure": clamp(overall_pressure)
        }
    }

    return normalized
