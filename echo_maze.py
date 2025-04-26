import random
import json
from collections import deque


class EchoMaze:
    DIRECTIONS = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'RIGHT': (1, 0),
        'LEFT': (-1, 0)
    }
    OPPOSITE = {'UP': 'DOWN', 'DOWN': 'UP', 'RIGHT': 'LEFT', 'LEFT': 'RIGHT'}

    def __init__(self, width=8, height=8, monster_count=5):
        self.width = width
        self.height = height
        self.cells = [{d: True for d in self.DIRECTIONS} for _ in range(width * height)]

        self.start = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
        max_attempts = 100
        attempts = 0

        while attempts < max_attempts:
            self.end = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
            distance = abs(self.start[0] - self.end[0]) + abs(self.start[1] - self.end[1])
            if self.end != self.start and distance >= (self.width + self.height) // 2:
                break
            attempts += 1

        # 如果超过最大次数还不满足，就退而求其次
        if attempts >= max_attempts:
            while True:
                self.end = random.choice([(x, y) for x in range(self.width) for y in range(self.height)])
                if self.end != self.start:
                    break

        self._dfs_carve(self.start, set())
        self.solution = self._solve(self.start, self.end)
        self.place_monsters(monster_count)

    def _idx(self, x, y):
        return y * self.width + x

    def _in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _dfs_carve(self, pos, visited):
        x, y = pos
        visited.add(pos)
        dirs = list(self.DIRECTIONS.items())
        random.shuffle(dirs)
        for d, (dx, dy) in dirs:
            nx, ny = x + dx, y + dy
            if not self._in_bounds(nx, ny) or (nx, ny) in visited:
                continue
            self.cells[self._idx(x, y)][d] = False
            self.cells[self._idx(nx, ny)][self.OPPOSITE[d]] = False
            self._dfs_carve((nx, ny), visited)

    def _solve(self, start, goal):
        queue = deque([start])
        prev = {start: None}
        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break
            for d, (dx, dy) in self.DIRECTIONS.items():
                if not self.cells[self._idx(x, y)][d]:
                    nxt = (x + dx, y + dy)
                    if nxt not in prev:
                        prev[nxt] = (x, y)
                        queue.append(nxt)
        path, node = [], goal
        while node:
            path.append(node)
            node = prev.get(node)
        return path[::-1]

    def place_monsters(self, count=None):
        all_cells = {(x, y) for x in range(self.width) for y in range(self.height)}
        candidate_cells = list(all_cells - set(self.solution))
        max_monsters = int(len(candidate_cells) * 0.5)
        self.monsters = random.sample(candidate_cells, max_monsters)

    def send_echo(self, player_pos, direction):
        echoes = []
        x, y = player_pos
        dx, dy = self.DIRECTIONS[direction]
        for step in range(1, 4):
            prev_x, prev_y = x + dx * (step - 1), y + dy * (step - 1)

            if self.cells[self._idx(prev_x, prev_y)][direction]:
                echoes.append({"type": "wall", "delay": (step - 1) * 2})
                break

            nx, ny = x + dx * step, y + dy * step
            if not self._in_bounds(nx, ny):
                break

            if (nx, ny) in self.monsters:
                echoes.append({"type": "monster", "delay": (step - 1) * 2})
                break
            if (nx, ny) == self.end:
                echoes.append({"type": "exit", "delay": (step - 1) * 2})
                break
        return sorted(echoes, key=lambda e: e['delay'])

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
        path_set = set(self.solution)
        print('+' + '---+' * self.width)
        for y in range(self.height):
            line = '|'
            for x in range(self.width):
                if (x, y) == self.start:
                    cell = ' S '
                elif (x, y) == self.end:
                    cell = ' E '
                elif (x, y) in self.monsters:
                    cell = ' M '
                elif (x, y) in path_set:
                    cell = ' * '
                else:
                    cell = '   '
                if self.cells[self._idx(x, y)]['RIGHT']:
                    line += cell + '|'
                else:
                    line += cell + ' '
            print(line)
            line = '+'
            for x in range(self.width):
                if self.cells[self._idx(x, y)]['DOWN']:
                    line += '---+'
                else:
                    line += '   +'
            print(line)
        print(f"\nPath ({len(self.solution) - 1} steps): {self.solution}")
