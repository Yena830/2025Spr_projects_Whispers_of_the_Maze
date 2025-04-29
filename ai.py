# ai.py

import time
from echo_maze import EchoMaze

class AISolver:
    """
    Tremaux-based AI for EchoMaze:
    - Marks directed edges with states 0=unvisited, 1=grey, 2=black
    - Each edge is explored at most twice (grey then black)
    - Uses a backtrack stack to return from dead ends
    - Tracks moves, echoes, and session time
    """
    def __init__(self, width=10, height=10):
        # Maze generation
        self.maze = EchoMaze(width, height)
        # Optional: self.maze.print()  # comment out for batch
        self.player_pos = self.maze.start
        self.edge_state = {}
        self.backtrack_stack = []
        self.echo_count = 0
        self.move_count = 0

    def mark_edge_state(self, pos, direction, state):
        self.edge_state[(pos, direction)] = state
        opp = self.maze.OPPOSITE[direction]
        dx, dy = self.maze.DIRECTIONS[direction]
        adj = (pos[0] + dx, pos[1] + dy)
        self.edge_state[(adj, opp)] = state

    def can_traverse(self, pos, direction):
        idx = self.maze._idx(*pos)
        if self.maze.cells[idx][direction]:
            return False
        echoes = self.maze.send_echo(pos, direction)
        self.echo_count += 1
        if echoes and echoes[0]['delay'] == 0 and echoes[0]['type'] in ('wall', 'monster'):
            return False
        return True

    def next_move(self):
        for state in (0, 1):
            for d in self.maze.DIRECTIONS:
                if self.edge_state.get((self.player_pos, d), 0) == state and self.can_traverse(self.player_pos, d):
                    return d
        return None

    def traverse_edge(self, direction):
        pos = self.player_pos
        curr = self.edge_state.get((pos, direction), 0)
        new_state = 1 if curr == 0 else 2 if curr == 1 else None
        if new_state is None:
            return False
        self.mark_edge_state(pos, direction, new_state)
        self.backtrack_stack.append(self.maze.OPPOSITE[direction])
        dx, dy = self.maze.DIRECTIONS[direction]
        self.player_pos = (pos[0] + dx, pos[1] + dy)
        self.move_count += 1
        if self.maze.floor_type[pos[1] + dy][pos[0] + dx] == 'ice':
            dest = self.maze.slide_dest.get(self.player_pos, {}).get(direction)
            if dest and dest != self.player_pos:
                self.player_pos = dest
                self.move_count += 1
        return True

    def backtrack(self):
        if not self.backtrack_stack:
            return False
        direction = self.backtrack_stack.pop()
        pos = self.player_pos
        dx, dy = self.maze.DIRECTIONS[direction]
        self.player_pos = (pos[0] + dx, pos[1] + dy)
        self.move_count += 1
        if self.maze.floor_type[pos[1] + dy][pos[0] + dx] == 'ice':
            dest = self.maze.slide_dest.get(self.player_pos, {}).get(direction)
            if dest and dest != self.player_pos:
                self.player_pos = dest
                self.move_count += 1
        return True

    def play(self):
        start = time.time()
        result = {'found_exit': False, 'hit_monster': False}
        while True:
            if self.player_pos == self.maze.end:
                result['found_exit'] = True
                break
            if self.player_pos in self.maze.monsters:
                result['hit_monster'] = True
                break
            d = self.next_move()
            if d:
                self.traverse_edge(d)
            else:
                if self.backtrack_stack:
                    self.backtrack()
                else:
                    break
        end = time.time()
        result['moves'] = self.move_count
        result['echoes'] = self.echo_count
        result['time'] = end - start
        return result


def run_batch(runs=100, width=10, height=10):
    successes = failures = 0
    total_moves = total_echoes = total_time = total_gen_time = 0.0

    for _ in range(runs):
        # Measure generation time
        gen_start = time.time()
        ai = AISolver(width, height)
        gen_time = time.time() - gen_start

        stats = ai.play()
        if stats['found_exit']:
            successes += 1
        else:
            failures += 1

        total_moves += stats['moves']
        total_echoes += stats['echoes']
        total_time += stats['time']
        total_gen_time += gen_time

    print(f"=== Batch ({runs} runs) Summary ===")
    print(f"Successes: {successes}, Failures: {failures}")
    print(f"Avg moves: {total_moves/runs:.2f}")
    print(f"Avg echoes: {total_echoes/runs:.2f}")
    print(f"Avg session time: {total_time/runs:.3f}s")
    print(f"Avg generation time: {total_gen_time/runs:.3f}s")

    return {
        'runs': runs,
        'successes': successes,
        'failures': failures,
        'avg_moves': total_moves / runs,
        'avg_echoes': total_echoes / runs,
        'avg_time': total_time / runs,
        'avg_gen_time': total_gen_time / runs
    }

if __name__ == '__main__':
    run_batch(1000, 10, 10)
