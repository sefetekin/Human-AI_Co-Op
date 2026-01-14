# 🎮 Adaptive Survival Game (Pygame)

An infinite survival game built with **Pygame**, designed around a **clear and explainable adaptive difficulty system**.

The player’s goal is simple: **survive as long as possible**.  
The game dynamically adjusts enemy behaviour to remain fair, responsive, and stable as the player improves.

## 🧠 Core Principles

- Infinite survival (no win condition)
- Adaptive difficulty based on player behaviour
- Conservative, bounded adjustments
- Clear separation between logic, rendering, UI, and persistence
- Live debug HUD for tuning and validation

## 📁 Project Structure

```text
.
├── main.py          # Game loop, input handling, system wiring
├── config.py        # Tunable parameters (GameConfig)
├── game_manager.py  # Core logic + adaptive difficulty
├── character.py     # Player logic (movement, shields)
├── enemy.py         # Enemy movement
├── render_world.py  # World/entity rendering
├── hud.py           # HUD, game over screen, debug panel
├── scoreboard.py    # Persistent leaderboard (JSON)
├── scores.json      # Local scores (gitignored)
├── models/          # External assets/models (gitignored)
└── README.md
```



## 🎯 Game Flow

1. Player starts in `PLAYING`
2. Enemies spawn continuously
3. Player survives and kills enemies with shields
4. On death, the game enters `AWAITING_NAME`
5. Player enters their name and score is saved
6. Game enters `GAME_OVER`
7. Player can restart


## ⚙️ Adaptive Difficulty Overview

Difficulty is controlled along two independent axes:

- **Enemy density** (how many enemies exist)
- **Enemy pressure** (how fast enemies approach)

All difficulty decisions are made **once per second**, never per frame.

> Frame ticks measure.  
> Second ticks decide.

## 📊 Metrics Used

### Average Enemy Distance

Computed once per second:
avg_distance = mean(distance(enemy_i, player))

Measures overall enemy pressure rather than player skill.

### Enemy Count Delta

Measured at each spawn event:
enemy_count_delta = current_enemy_count - last_spawn_enemy_count


Indicates whether the player is clearing enemies or being overwhelmed.

### Kill Count

Tracked for scoreboard context only.  
Not used for difficulty decisions.


## 🧠 Difficulty Axis 1 — Enemy Density (Spawning)

Controlled by:
- `spawn_count`
- `spawn_interval`

### Target Behaviour

Over `spawn_interval` seconds, the ideal enemy change is:
ideal_delta = -spawn_interval / 2


Enemies should decrease slowly, but not disappear.

### Adjustment Rules

- If enemies decrease too quickly:
  - increase `spawn_count`
  - or decrease `spawn_interval`
- If enemies increase too quickly:
  - decrease `spawn_count`
  - or increase `spawn_interval`

### Bounds
spawn_count ∈ [3, 10]
spawn_interval ∈ [3s, 15s]

Values slowly return to defaults when pressure stabilises.

## 🧠 Difficulty Axis 2 — Enemy Pressure (Speed)

Controlled by:
- `enemy_min_speed`
- `enemy_max_speed`

### Rate-of-Change Rule

Let:
ΔD = avg_distance_now - avg_distance_previous

- If `ΔD > shield_radius` → game got easier fast → increase speed
- If `ΔD < -shield_radius` → game got harder fast → decrease speed

### Absolute Distance Rule

- If `avg_distance > enemy_max_spawn_dist` → increase speed
- If `avg_distance < enemy_min_spawn_dist` → decrease speed

Rate-of-change logic always takes priority.

### Speed Bounds
enemy_speed ∈ [30, 300]


## 🧪 Debug HUD

The debug panel displays live values for:

- Spawn count
- Spawn interval
- Shield count
- Average enemy distance
- Enemy count delta (color-coded)
- Enemy min and max speed

Enemy count delta colors:
- Green → enemies increasing (player struggling)
- Red → enemies decreasing (player dominating)


## 🏆 Scoreboard

Each run records:
- Player name
- Survival time (ranking metric)
- Kill count (context)

The leaderboard is local, persistent, and sorted strictly by survival time.
