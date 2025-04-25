# maze_simple.py

import random
from collections import deque

# 方向向量及其相对方向映射
DIRECTIONS = {
    'N': (0, -1),  # 北：y-1
    'S': (0, 1),   # 南：y+1
    'E': (1, 0),   # 东：x+1
    'W': (-1, 0)   # 西：x-1
}
OPPOSITE = {d: o for o, d in [('N','S'), ('S','N'), ('E','W'), ('W','E')]}

class Maze:
    """
    Maze 简易生成与求解类：
    - 使用 DFS 回溯算法生成骨架
    - 按概率增加环路 (loops)
    - 用 BFS 求最短路径
    - 提供打印接口，以 ASCII 展示迷宫与解
    """
    def __init__(self, width=8, height=8, complexity=0.75, seed=None):
        """
        初始化迷宫：
        width, height: 迷宫尺寸
        complexity: [0..1] 控制分支与死胡同比例
        seed: 随机数种子，方便调试复现
        """
        self.width = width
        self.height = height
        # cells 存储每个格子的四面墙状态，True=有墙，False=无墙
        self.cells = [{d: True for d in DIRECTIONS} for _ in range(width * height)]
        self._rng = random.Random(seed)

        # 1) 挖洞，生成骨架树形结构
        self._dfs_carve((0, 0), set(), complexity)
        # 2) 增加若干环路，提高迷惑度
        self._add_loops(density=complexity * 0.1)
        # 3) 求最短路径用于验证和打印
        self.solution = self._solve((0, 0), (width - 1, height - 1))

    def _idx(self, x, y):
        """计算一维索引: y * width + x"""
        return y * self.width + x

    def _in_bounds(self, x, y):
        """检查坐标是否在迷宫范围内"""
        return 0 <= x < self.width and 0 <= y < self.height

    def _dfs_carve(self, pos, visited, complexity):
        """
        使用随机深度优先回溯挖洞算法：
        - pos: 当前格子坐标 (x,y)
        - visited: 已访问格子集合
        - complexity: 决定是否沿某方向挖通的概率
        """
        x, y = pos
        visited.add(pos)
        # 打乱方向顺序，保证随机性
        dirs = list(DIRECTIONS.items())
        self._rng.shuffle(dirs)

        for d, (dx, dy) in dirs:
            nx, ny = x + dx, y + dy
            # 越界或已访问则跳过
            if not self._in_bounds(nx, ny) or (nx, ny) in visited:
                continue
            # 按 complexity 决定是否打通墙壁
            if self._rng.random() < complexity:
                # 移除当前格子与邻居格子之间的墙壁
                self.cells[self._idx(x, y)][d] = False
                self.cells[self._idx(nx, ny)][OPPOSITE[d]] = False
                # 递归深入下一格
                self._dfs_carve((nx, ny), visited, complexity)

    def _add_loops(self, density):
        """
        随机打通剩余墙壁的一部分，制造环路：
        - density: 打通比例 (0..1)
        """
        walls = []
        # 收集所有仍存在的墙
        for y in range(self.height):
            for x in range(self.width):
                for d, (dx, dy) in DIRECTIONS.items():
                    nx, ny = x + dx, y + dy
                    if self._in_bounds(nx, ny) and self.cells[self._idx(x, y)][d]:
                        walls.append(((x, y), (nx, ny), d))
        # 随机选择若干墙并移除，忽略是否会形成环
        count = int(len(walls) * density)
        for (x, y), (nx, ny), d in self._rng.sample(walls, count):
            self.cells[self._idx(x, y)][d] = False
            self.cells[self._idx(nx, ny)][OPPOSITE[d]] = False

    def _solve(self, start, goal):
        """
        使用 BFS 求解最短路径：
        - start: 起点 (x,y)
        - goal: 终点 (x,y)
        返回路径节点列表，从 start 到 goal。
        """
        queue = deque([start])
        prev = {start: None}

        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break  # 找到终点可提前退出
            for d, (dx, dy) in DIRECTIONS.items():
                if not self.cells[self._idx(x, y)][d]:  # 无墙才能通行
                    nxt = (x + dx, y + dy)
                    if nxt not in prev:
                        prev[nxt] = (x, y)
                        queue.append(nxt)

        # 回溯前驱节点，构造完整路径
        path, node = [], goal
        while node:
            path.append(node)
            node = prev.get(node)
        return path[::-1]  # 反转，起点在前

    def print(self):
        """
        以 ASCII 网格形式打印迷宫：
        - +---+ 标示墙
        - |   | 标示通路
        - S: 入口 (0,0)
        - E: 出口 (width-1,height-1)
        - *: 最短路径标记
        """
        path_set = set(self.solution)
        start = (0, 0)
        end = (self.width - 1, self.height - 1)

        # 顶部边界行
        print('+' + '---+' * self.width)
        for y in range(self.height):
            # 内容与纵墙行
            line = '|'
            for x in range(self.width):
                # 确定格子内部显示内容
                if (x, y) == start:
                    cell = ' S '
                elif (x, y) == end:
                    cell = ' E '
                elif (x, y) in path_set:
                    cell = ' * '
                else:
                    cell = '   '
                # 根据东墙决定是否绘制竖线
                if self.cells[self._idx(x, y)]['E']:
                    line += cell + '|'
                else:
                    line += cell + ' '
            print(line)

            # 底部墙行
            line = '+'
            for x in range(self.width):
                if self.cells[self._idx(x, y)]['S']:
                    line += '---+'
                else:
                    line += '   +'
            print(line)

        # 最后输出路径详情
        print(f"\nPath ({len(self.solution)-1} steps): {self.solution}")


if __name__ == "__main__":
    # 一行调用：生成 + 求解 + 打印
    maze = Maze(width=8, height=8, complexity=0.75, seed=None)
    maze.print()
