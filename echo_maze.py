import random
import json
from collections import deque


class EchoMaze:
    """
    EchoMaze：
      - 生成连通无环的迷宫
      - 随机选取入口/出口
      - 放置怪物（不在最短路径上）
      - 可选冰面滑道
      - 发声探测（回声模拟）
      - ASCII 打印 & JSON 存档
    """    
    DIRECTIONS = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'RIGHT': (1, 0),
        'LEFT': (-1, 0)
    }
    OPPOSITE = {'UP': 'DOWN', 'DOWN': 'UP', 'RIGHT': 'LEFT', 'LEFT': 'RIGHT'}

    def __init__(self, width=10, height=10, monster_count=None, difficulty=0.5):
        self.width = width
        self.height = height
        #每个cell初始化四面墙
        self.cells = [{d: True for d in self.DIRECTIONS} for _ in range(width * height)]
        # 地面类型 floor vs ice，默认全 floor
        self.floor_type = [['floor'] * width for _ in range(height)]
        #选出入口
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
        # 生成迷宫、求解最短路、放怪物
        self._dfs_carve(self.start, set())
        self.solution = self._solve(self.start, self.end)
        self.place_monsters(monster_count)
        #构建滑道图 & 铺冰面
        self._extract_graph()  
        self._assign_ice_by_ratio(ratio=0.3)  
        
               
    def send_echo(self, player_pos, direction):
        """
        发声探测：最远 3 格，遇到墙/怪物/出口即停，
        返回列表[{"type":..., "delay":...}]，按 delay 排序。
        """
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
        max_monsters = int(len(candidate_cells) * 0.2)
        self.monsters = random.sample(candidate_cells, max_monsters)


    
    
    ####根据连通格提取节点与走廊列表#########################
    def _extract_graph(self):
        """
        提取节点 (度 !=2 的通路) 及相邻节点间的走廊 (直线、无分叉)
        """
        self.nodes = []
        for y in range(self.height):
            for x in range(self.width):
                if self._is_open(x, y):
                    deg = sum(
                        self._is_open(x+dx, y+dy)
                        for dx,dy in self.DIRECTIONS.values()
                    )
                    if deg != 2 or (x,y) in (self.start, self.end):
                        self.nodes.append((x, y))
        self.corridors = []
        for i, a in enumerate(self.nodes):
            for b in self.nodes[i+1:]:
                if (a[0] == b[0] or a[1] == b[1]) and self._clear_path(a, b):
                    cells = self._cells_between(a, b)
                    self.corridors.append({'nodes': (a, b), 'cells': cells})
                    
    def _is_open(self, x, y):
        """
        检查坐标 (x,y) 是否在迷宫内且为通路格 (至少有一个开墙方向)。
        """
        if not self._in_bounds(x, y):
            return False
        idx = self._idx(x, y)
        # 如果任意方向的墙被打通，则表示该格可通行
        return any(not self.cells[idx][d] for d in self.DIRECTIONS)

    def _clear_path(self, a, b):
        """
        判断节点 a, b 之间是否存在直线路径且中间无分叉。
        -- a, b 必在同一行或同一列。
        -- 所有相邻格之间的墙都被打通，且中间格度数都为 2（直线走廊）。
        """
        x1, y1 = a; x2, y2 = b
        # 垂直走廊
        if x1 == x2:
            step = 1 if y2 > y1 else -1
            # 检查墙连接
            for y in range(y1, y2, step):
                dir_wall = 'DOWN' if step == 1 else 'UP'
                if self.cells[self._idx(x1, y)][dir_wall]:
                    return False
            # 中间格度数检查
            for y in range(y1 + step, y2, step):
                idx = self._idx(x1, y)
                deg = sum(not self.cells[idx][d] for d in self.DIRECTIONS)
                if deg != 2:
                    return False
            return True
        # 水平走廊
        if y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1, x2, step):
                dir_wall = 'RIGHT' if step == 1 else 'LEFT'
                if self.cells[self._idx(x, y1)][dir_wall]:
                    return False
            for x in range(x1 + step, x2, step):
                idx = self._idx(x, y1)
                deg = sum(not self.cells[idx][d] for d in self.DIRECTIONS)
                if deg != 2:
                    return False
            return True
        return False

    def _cells_between(self, a, b):
        """
        返回 a, b 之间（不含端点）的所有格坐标列表。
        """
        cells = []
        x1, y1 = a; x2, y2 = b
        # 同列
        if x1 == x2:
            step = 1 if y2 > y1 else -1
            for y in range(y1 + step, y2, step):
                cells.append((x1, y))
        # 同行
        elif y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                cells.append((x, y1))
        return cells
                    
                    
                    
    
    ####按 30%比率选择走廊设为冰道，标注 floor_type 并生成 slide_dest    
    def _assign_ice_by_ratio(self, ratio=0.3):
        """
        按走廊抽样：随机将约 ratio 比例的走廊全段设为冰面
        （整条连续），而不是仅随机挑格子。
        """
        # 1) 确保已经提取了 self.corridors
        #    每个 corridor = {'nodes':(a,b), 'cells':[(x1,y1),(x2,y2),...]}
        candidates = self.corridors[:]  
        total = len(candidates)
        # 2) 计算要抽多少条走廊
        count = max(1, round(total * ratio))
        # 3) 随机选出若干整条走廊
        ice_corridors = random.sample(candidates, count)
    
        # 4) 重置全地图为普通
        self.floor_type = [['floor'] * self.width for _ in range(self.height)]
        # 5) 标记选中走廊上所有格子为 'ice'
        for corridor in ice_corridors:
            for x, y in corridor['cells']:
                self.floor_type[y][x] = 'ice'
    
        # 6) 重新计算滑动终点 slide_dest（若你需要滑动逻辑）
        self.slide_dest = {n: {} for n in self.nodes}
        for node in self.nodes:
            for d, (dx, dy) in self.DIRECTIONS.items():
                self.slide_dest[node][d] = self._simulate_slide(node, dx, dy)

    def _simulate_slide(self, node, dx, dy):
      """
      从节点 node 出发，按 (dx, dy) 方向滑行，
      直到遇到普通地板或墙前一格，返回最终坐标。
      如果初始方向被墙阻挡，返回 None。
      """
      x, y = node
      # 找到方向名称
      dir_name = next((d for d,(vx,vy) in self.DIRECTIONS.items() if (vx,vy)==(dx,dy)), None)
      if dir_name is None or self.cells[self._idx(x, y)][dir_name]:
          return None
      nx, ny = x + dx, y + dy
      while True:
          if self.floor_type[ny][nx] == 'floor':
              return (nx, ny)
          # 下一格若出界或被墙，则停在当前格
          if not self._in_bounds(nx + dx, ny + dy) or self.cells[self._idx(nx, ny)][dir_name]:
              return (nx, ny)
          nx += dx; ny += dy
          
          
    def _is_reachable(self, start, end):
          """
          在 slide_dest 图上做 BFS，检查 start 到 end 是否可达。
          """
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
  
    def _dir_by_delta(self, dx, dy):
        """根据(dx,dy) 查找方向名"""
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
        打印迷宫状态：
        S = start, E = exit, M = monster
        * = 路径上的普通地板
        ~ = 非路径上的冰面
        # = 路径上的冰面
        其他格子留空
        """
        path_set = set(self.solution)
        ice_cells = [(x, y)
                     for y in range(self.height)
                     for x in range(self.width)
                     if getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice']
        print(f"Ice cells: {ice_cells}")
        
        

        # 顶部边界
        print('+' + '---+' * self.width)
        for y in range(self.height):
            line = '|'
            for x in range(self.width):
                coord = (x, y)
                # 最高优先级：起点/终点/怪物
                if coord == self.start:
                    cell = ' S '
                elif coord == self.end:
                    cell = ' E '
                elif coord in self.monsters:
                    cell = ' M '
                # 其次按“路径上的冰” → “路径上的普通地板”
                elif coord in path_set and getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice':
                    cell = ' # '
                elif coord in path_set:
                    cell = ' * '
                # 再次按“非路径但冰面”
                elif getattr(self, 'floor_type', None) and self.floor_type[y][x] == 'ice':
                    cell = ' ~ '
                # 其余什么都不显示
                else:
                    cell = '   '
                # 右侧墙
                if self.cells[self._idx(x, y)]['RIGHT']:
                    line += cell + '|'
                else:
                    line += cell + ' '
            print(line)

            # 底部边界
            bottom = '+'
            for x in range(self.width):
                if self.cells[self._idx(x, y)]['DOWN']:
                    bottom += '---+'
                else:
                    bottom += '   +'
            print(bottom)

        

        
