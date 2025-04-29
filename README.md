# Whispers of the Maze (EchoMaze)

## 1. Project Overview
Whispers of the Maze is a puzzle-adventure game that challenges players to rely on sound rather than sight. Players emit echoes in four cardinal directions to detect nearby walls, lurking monsters, or the distant exit, creating an immersive audio-based navigation experience. Random monsters increase tension by punishing reckless moves, and ice-slide corridors introduce dynamic elements by propelling players across several cells when stepped upon.

## 2. Game Rules & Mechanics
- **Maze Generation**: Each session starts with a randomly generated perfect maze (connected, no loops).
- **Blind Navigation**: Players cannot see the map—only their current cell.
- **Echo Detection**: Use keys to emit an echo up to 3 cells away.
  - **Wall**: thud sound
  - **Monster**: growl
  - **Exit**: breeze
- **Movement**: Arrow keys to move one cell; blocked by walls.
- **Monsters**: Stepping on a monster ends the game.
- **Exit**: Reaching the exit cell wins the game.
- **Ice Corridors**: stepping onto ice slides you to the corridor’s end (or until a wall).

## 3. Implementation & Architecture
- **Language & Libraries**: Python 3.7+, Pygame for GUI.
- **Module Overview**:
  - `echo_maze.py`: Maze generation (DFS carve), shortest-path solving (BFS), slide logic, echo function.
  - `word_play.py`: Command-line interface (`echo`/`move` commands).
  - `game_engine.py`: Pygame GUI, rendering, input handling, audio feedback.
  - `ai.py`: Heuristic AI player that uses echo delays to guide search.
  - `Blind_AI.py`: Blind DFS AI player using `WordPlayInterface` (echo + visited pruning).
  - `requirements.txt`: Dependency list.
- **Assets**:
  - `icon/` and `sounds/` directories for sprites and audio files.

## 4. Algorithm Analysis & Performance
- **Maze Generation (DFS-based)**
  - Visits each cell at most once → O(N), where N = width × height.
- **Path Solving (BFS)**
  - Finds unique shortest path from start to exit → O(N + E) ≃ O(N).
- **AI Exploration**
  - **Blind DFS**: worst-case O(4^d), pruned by visited set and echo collisions.
  - **Heuristic Solver**: uses echo delay ordering to prioritize directions, reducing branching.
- **Echo Logic**
  - Checks up to 3 cells, constant work per step → O(1) per echo.

## 5. Performance Testing
- **Batch Runs**: Execute `Blind_AI.run_batch()` for multiple trials.
- **Metrics Recorded**:
  - Echo calls vs. movement steps.
  - Dead-end entries (backtracking count).
  - Success rate (exit found vs. monster hit).
  - Time-to-solve distribution.
- **Example Results** (100 runs, 10×10 maze):
  - Success rate: 85%
  - Avg. moves: 120
  - Avg. echoes: 95
  - Avg. time: 0.25s

## 6. Quick Start & Interaction

### 6.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 6.2 GUI Version (Human Play)
1. Launch:
   ```bash
   python start_game.py
   ```
2. Controls:
   - **Arrow Keys**: Move your character one cell in the pressed direction.
   - **W/A/S/D Keys**: Emit an echo pulse in the corresponding direction:
     - **W = UP**, **S = DOWN**, **A = LEFT**, **D = RIGHT**.
3. Feedback:
   - Visual: Nearby walls, monsters, or exit briefly highlighted in view window.
   - Audio: Thud (wall), growl (monster), breeze (exit).
4. Win/Lose:
   - Reach the exit cell to win (victory screen).
   - Step on a monster to lose (game over screen).

### 6.4 AI Examples
```bash
python ai.py       # Heuristic AI auto-solve
python Blind_AI.py # Blind DFS AI auto-solve
```

---
*Refer to module docstrings for advanced configuration and parameters.*

