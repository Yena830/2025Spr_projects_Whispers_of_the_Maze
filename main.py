from echo_maze import EchoMaze


maze = EchoMaze(width=9, height=9)

# 打印迷宫结构
maze.print()

# 玩家从起点向右探测
echoes = maze.send_echo(maze.start, 'RIGHT')
print("Echo Feedback:", echoes)

# 保存地图到文件
# maze.save_to_json("saved_maps/map1.json")
