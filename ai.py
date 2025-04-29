# ai_solver.py

import random
from collections import deque
from echo_maze import EchoMaze

class AISolver:
    def __init__(self, width=10, height=10):
        self.maze = EchoMaze(width, height)
        self.maze.print()
        self.player_pos = self.maze.start
        self.visited = set()
        self.backtrack_stack = deque()
        self.last_move = None
        print("Maze Initialized. Starting at", self.player_pos)

    def play(self):
        while True:
            if self.player_pos == self.maze.end:
                print("Found the exit! Escaped successfully!")
                break
            if self.player_pos in self.maze.monsters:
                print("Stepped on a monster... Game Over!")
                break

            move_dir = self.choose_move()
            if move_dir:
                print(f"Move {move_dir}")
                if not self.move_player(move_dir):
                    print("Bumped into a wall unexpectedly!")
            else:
                # Dead-end: backtrack
                if self.backtrack_stack:
                    prev_pos, came_from = self.backtrack_stack.pop()
                    self.player_pos = prev_pos
                    self.last_move = came_from
                    print(f"Dead-end! Backtracking to {prev_pos}")
                else:
                    print("Nowhere to backtrack! AI stuck!")
                    break

    def choose_move(self):
        echo_results = {}
        for d in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            echoes = self.maze.send_echo(self.player_pos, d)
            if echoes:
                echo_results[d] = echoes[0]  # 只看最近的反应
                print(f"Echo {d}: Detected {echoes[0]['type']} after {echoes[0]['delay']}s")
            else:
                echo_results[d] = {'type': 'silence', 'delay': 99}
                print(f"Echo {d}: Silence...")

        possible_dirs = []
        for d in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            if self.maze.cells[self.maze._idx(self.player_pos[0], self.player_pos[1])][d]:
                continue  # 有墙不能走
            if echo_results[d]['type'] == 'wall' and echo_results[d]['delay'] == 0:
                continue  # 0s撞墙
            dx, dy = self.maze.DIRECTIONS[d]
            next_pos = (self.player_pos[0] + dx, self.player_pos[1] + dy)
            if next_pos not in self.visited:
                possible_dirs.append(d)

        # 尽量不走回头路
        non_back_dirs = [d for d in possible_dirs if not (self.last_move and self.maze.OPPOSITE[d] == self.last_move)]

        if non_back_dirs:
            return random.choice(non_back_dirs)
        elif possible_dirs:
            return random.choice(possible_dirs)
        else:
            return None

    def move_player(self, direction):
        x, y = self.player_pos
        dx, dy = self.maze.DIRECTIONS[direction]
        idx = self.maze._idx(x, y)
        if self.maze.cells[idx][direction]:
            return False
        # Move one step
        new_pos = (x + dx, y + dy)
        if not self.maze._in_bounds(*new_pos):
            return False
        self.visited.add(new_pos)
        self.backtrack_stack.append((self.player_pos, self.maze.OPPOSITE[direction]))
        self.player_pos = new_pos

        # 滑冰逻辑
        if self.maze.floor_type[y + dy][x + dx] == 'ice':
            dest = self.maze.slide_dest.get(self.player_pos, {}).get(direction)
            if dest:
                print(f"Sliding on ice to {dest}")
                self.player_pos = dest
                self.visited.add(dest)
        self.last_move = direction
        return True

if __name__ == "__main__":
    ai = AISolver(10, 10)
    ai.play()
