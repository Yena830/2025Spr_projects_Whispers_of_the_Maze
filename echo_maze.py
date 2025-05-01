import random
import json
from collections import deque


class EchoMaze:
    """
    EchoMaze：
      - Generate a connected, acyclic maze (via DFS)
      - Random start and end points
      - Place monsters (off the solution path)
      - Optionally includes icy floors (slippery paths)
      - Provides echo-based probe system for blind navigation
      - Supports ASCII rendering & JSON saving
    """   
    # Direction vectors and their opposites
    DIRECTIONS = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'RIGHT': (1, 0),
        'LEFT': (-1, 0)
    }
    OPPOSITE = {'UP': 'DOWN', 'DOWN': 'UP', 'RIGHT': 'LEFT', 'LEFT': 'RIGHT'}

    def __init__(self, width=10, height=10, difficulty='easy',monster_count=None):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        # Initialize each cell with walls on all four sides
        self.cells = [{d: True for d in self.DIRECTIONS} for _ in range(width * height)]
        # Default floor is non-slippery
        self.floor_type = [['floor'] * width for _ in range(height)]
        # Randomly choose a start and end cell (not too close)
        self.start = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
        max_attempts = 100
        attempts = 0
        while attempts < max_attempts:
            self.end = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
            distance = abs(self.start[0] - self.end[0]) + abs(self.start[1] - self.end[1])
            if self.end != self.start and distance >= (self.width + self.height) // 2:
                break
            attempts += 1
        if attempts >= max_attempts:
            while True:
                self.end = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
                if self.end != self.start:
                    break
        # Carve maze via DFS
        self.dfs_carve(self.start, set())
        # Optionally add extra paths for higher difficulty
        if self.difficulty in ['medium', 'hard']:
            self.add_extra_paths(extra_count=5)
        # Solve the shortest path for later reference
        self.solution = self.solve(self.start, self.end)
        # Place monsters strategically
        self.place_monsters(monster_count)
        # Extract linear corridors and assign ice paths
        self.extract_graph()  
        self.assign_ice_by_ratio(ratio=0.3)  
        
               
    def send_echo(self, player_pos, direction):
        """
       Echo probe: returns echo from up to 3 tiles ahead unless blocked.
       Stops at wall, monster, or exit. Each echo has a delay (distance*2).
       """
        echoes = []
        x, y = player_pos
        dx, dy = self.DIRECTIONS[direction]
        for step in range(1, 4):
            prev_x, prev_y = x + dx * (step - 1), y + dy * (step - 1)
            if self.cells[self.idx(prev_x, prev_y)][direction]:
                echoes.append({"type": "wall", "delay": (step - 1) * 2})
                break
            nx, ny = x + dx * step, y + dy * step
            if not self.in_bounds(nx, ny):
                break
            if (nx, ny) in self.monsters:
                echoes.append({"type": "monster", "delay": (step - 1) * 2})
                break
            if (nx, ny) == self.end:
                echoes.append({"type": "exit", "delay": (step - 1) * 2})
                break
        return sorted(echoes, key=lambda e: e['delay'])

    def idx(self, x, y):
        """Convert (x, y) to 1D index in cells array."""
        return y * self.width + x

    def in_bounds(self, x, y):
        """Check whether (x, y) is inside maze bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def dfs_carve(self, pos, visited):
        """Recursively carve passages using DFS from a given cell."""
        x, y = pos
        visited.add(pos)
        dirs = list(self.DIRECTIONS.items())
        random.shuffle(dirs)
        for d, (dx, dy) in dirs:
            nx, ny = x + dx, y + dy
            if not self.in_bounds(nx, ny) or (nx, ny) in visited:
                continue
            self.cells[self.idx(x, y)][d] = False
            self.cells[self.idx(nx, ny)][self.OPPOSITE[d]] = False
            self.dfs_carve((nx, ny), visited)

    def solve(self, start, goal):
        """Solve the maze using BFS to find the shortest path."""
        queue = deque([start])
        prev = {start: None}
        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break
            for d, (dx, dy) in self.DIRECTIONS.items():
                if not self.cells[self.idx(x, y)][d]:
                    nxt = (x + dx, y + dy)
                    if nxt not in prev:
                        prev[nxt] = (x, y)
                        queue.append(nxt)
        path, node = [], goal
        while node:
            path.append(node)
            node = prev.get(node)
        return path[::-1]

    def add_extra_paths(self, extra_count=5):
        """Randomly open walls to create loops, increasing complexity."""
        added = 0
        attempts = 0
        max_attempts = extra_count * 10
        while added < extra_count and attempts < max_attempts:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            dir, (dx, dy) = random.choice(list(self.DIRECTIONS.items()))
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                if self.cells[self.idx(x, y)][dir]:
                    self.cells[self.idx(x, y)][dir] = False
                    self.cells[self.idx(nx, ny)][self.OPPOSITE[dir]] = False
                    added += 1
            attempts += 1

    def place_monsters(self, count=None):
        """
        Place monsters off the solution path.
        'easy'/'medium' place them only on non-path cells.
        'hard' could include path cells (currently commented).
        """
        all_cells = {(x, y) for x in range(self.width) for y in range(self.height)}
        solution_set = set(self.solution)
        non_solution_cells = list(all_cells - solution_set)
        max_monsters = int(len(non_solution_cells) * 0.1)
        monsters = set()

        if self.difficulty == 'easy':
            monsters.update(random.sample(non_solution_cells, max_monsters))

        elif self.difficulty == 'medium':
            monsters.update(random.sample(non_solution_cells, max_monsters))

        # elif self.difficulty == 'hard':
        #
        #     path_cells = list(solution_set - {self.start, self.end})
        #     extra_on_path = max(1, int(len(path_cells) * 0.1))
        #     monsters.update(random.sample(non_solution_cells, max_monsters))
        #     monsters.update(random.sample(path_cells, extra_on_path))

        self.monsters = monsters

    def extract_graph(self):
        """
        Extract nodes (degree != 2) and corridors (straight paths).
        Used to determine which areas may be converted into ice.
        """
        self.nodes = []
        for y in range(self.height):
            for x in range(self.width):
                if self.is_open(x, y):
                    deg = sum(
                        self.is_open(x+dx, y+dy)
                        for dx,dy in self.DIRECTIONS.values()
                    )
                    if deg != 2 or (x,y) in (self.start, self.end):
                        self.nodes.append((x, y))
        self.corridors = []
        for i, a in enumerate(self.nodes):
            for b in self.nodes[i+1:]:
                if (a[0] == b[0] or a[1] == b[1]) and self.clear_path(a, b):
                    cells = self.cells_between(a, b)
                    self.corridors.append({'nodes': (a, b), 'cells': cells})
                    
    def is_open(self, x, y):
        """Check if a cell is walkable (has any wall broken)."""
        if not self.in_bounds(x, y):
            return False
        idx = self.idx(x, y)
        return any(not self.cells[idx][d] for d in self.DIRECTIONS)

    def clear_path(self, a, b):
        """
        Return True if a and b are in a straight line and the path between them is unbranched.
        """
        x1, y1 = a; x2, y2 = b
        if x1 == x2:
            step = 1 if y2 > y1 else -1
            for y in range(y1, y2, step):
                dir_wall = 'DOWN' if step == 1 else 'UP'
                if self.cells[self.idx(x1, y)][dir_wall]:
                    return False
            for y in range(y1 + step, y2, step):
                idx = self.idx(x1, y)
                deg = sum(not self.cells[idx][d] for d in self.DIRECTIONS)
                if deg != 2:
                    return False
            return True
        if y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1, x2, step):
                dir_wall = 'RIGHT' if step == 1 else 'LEFT'
                if self.cells[self.idx(x, y1)][dir_wall]:
                    return False
            for x in range(x1 + step, x2, step):
                idx = self.idx(x, y1)
                deg = sum(not self.cells[idx][d] for d in self.DIRECTIONS)
                if deg != 2:
                    return False
            return True
        return False

    def cells_between(self, a, b):
        """Return all cells between a and b (exclusive)."""
        cells = []
        x1, y1 = a; x2, y2 = b
        if x1 == x2:
            step = 1 if y2 > y1 else -1
            for y in range(y1 + step, y2, step):
                cells.append((x1, y))
        elif y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                cells.append((x, y1))
        return cells
                    
                    
    def assign_ice_by_ratio(self, ratio=0.3):
        """
        Randomly convert ~30% of corridors into slippery ice sections.
        """
        candidates = self.corridors[:]  
        total = len(candidates)
        count = max(1, round(total * ratio))
        ice_corridors = random.sample(candidates, count)
        self.floor_type = [['floor'] * self.width for _ in range(self.height)]
        for corridor in ice_corridors:
            for x, y in corridor['cells']:
                self.floor_type[y][x] = 'ice'
        self.slide_dest = {n: {} for n in self.nodes}
        for node in self.nodes:
            for d, (dx, dy) in self.DIRECTIONS.items():
                self.slide_dest[node][d] = self.simulate_slide(node, dx, dy)

    def simulate_slide(self, node, dx, dy):
        """
        Simulate sliding from a node in a direction until normal floor or wall.
        """
        x, y = node
        dir_name = next((d for d,(vx,vy) in self.DIRECTIONS.items() if (vx,vy)==(dx,dy)), None)
        if dir_name is None or self.cells[self.idx(x, y)][dir_name]:
            return None
        nx, ny = x + dx, y + dy
        while True:
            if self.floor_type[ny][nx] == 'floor':
                return (nx, ny)
            if not self.in_bounds(nx + dx, ny + dy) or self.cells[self.idx(nx, ny)][dir_name]:
                return (nx, ny)
            nx += dx; ny += dy
          
          
    def is_reachable(self, start, end):
          """Use BFS on slide graph to determine reachability between nodes."""
          from collections import deque
          visited = {start}
          queue = deque([start])
          while queue:
              curr = queue.popleft()
              if curr == end:
                  return True
              for dest in self.slide_dest.get(curr, {}).values():
                  if dest not in visited:
                      visited.add(dest)
                      queue.append(dest)
          return False
  
    def dir_by_delta(self, dx, dy):
        """Return direction name for a (dx, dy) vector."""
        for name, (ddx, ddy) in self.DIRECTIONS.items():
            if (ddx, ddy) == (dx, dy):
                return name
        return None
           
        
    def save_to_json(self, filename):
        data = {
            "width": self.width,
            "height": self.height,
            "cells": self.cells,
            "start": self.start,
            "end": self.end,
            "monsters": self.monsters
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def print(self):
        """
        ASCII maze visualizer.
        S = start, E = exit, M = monster
        * = floor on solution path, ~ = ice off path, # = ice on path
        """
        path_set = set(self.solution)
        ice_cells = [(x, y)
                     for y in range(self.height)
                     for x in range(self.width)
                     if getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice']
        # print(f"Ice cells: {ice_cells}")
        
        print('+' + '---+' * self.width)
        for y in range(self.height):
            line = '|'
            for x in range(self.width):
                coord = (x, y)
                if coord == self.start:
                    cell = ' S '
                elif coord == self.end:
                    cell = ' E '
                elif coord in self.monsters:
                    cell = ' M '
                elif coord in path_set and getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice':
                    cell = ' # '
                elif coord in path_set:
                    cell = ' * '
                elif getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice':
                    cell = ' ~ '
                else:
                    cell = '   '
                if self.cells[self.idx(x, y)]['RIGHT']:
                    line += cell + '|'
                else:
                    line += cell + ' '
            print(line)
            bottom = '+'
            for x in range(self.width):
                if self.cells[self.idx(x, y)]['DOWN']:
                    bottom += '---+'
                else:
                    bottom += '   +'
            print(bottom)
        
if __name__ =="__main__":
    maze=EchoMaze(10,10,difficulty='easy')
    maze.print()
        
