from echo_maze import EchoMaze


class GameEngine:
    def __init__(self, width=10, height=10):
        self.maze = EchoMaze(width, height)
        self.player_pos = self.maze.start
        self.running = True

    def start(self):
        print("\nFinal Maze State:")
        self.maze.print()

        print("Welcome to EchoMaze!")
        print("Commands: 'echo <direction>', 'move <direction>', 'exit'")
        print(f"You start at {self.player_pos}. Find the exit without hitting monsters!")

        while self.running:
            cmd = input("\nYour action > ").strip().upper().split()
            if not cmd:
                continue
            action = cmd[0]

            if action == 'ECHO' and len(cmd) == 2:
                direction = cmd[1]
                if direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                    echoes = self.maze.send_echo(self.player_pos, direction)
                    if not echoes:
                        print("Silence... Nothing detected within range.")
                    else:
                        for echo in echoes:
                            if echo['type'] == 'wall':
                                print(f"You hear a thud after {echo['delay']} seconds.")
                            elif echo['type'] == 'monster':
                                print(f"You hear growling after {echo['delay']} seconds.")
                            elif echo['type'] == 'exit':
                                print(f"You hear a breeze after {echo['delay']} seconds.")
                else:
                    print("Invalid direction. Use UP, DOWN, LEFT, RIGHT.")

            elif action == 'MOVE' and len(cmd) == 2:
                direction = cmd[1]
                if direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                    self.move_player(direction)
                else:
                    print("Invalid direction. Use UP, DOWN, LEFT, RIGHT.")

            elif action == 'EXIT':
                print("Goodbye!")
                self.running = False

            else:
                print("Unknown command.")

    def move_player(self, direction):
        x, y = self.player_pos
        dx, dy = self.maze.DIRECTIONS[direction]
        idx = self.maze._idx(x, y)

        if self.maze.cells[idx][direction]:
            print("There's a wall blocking your way!")
            return

        # Move
        new_pos = (x + dx, y + dy)
        if not self.maze._in_bounds(*new_pos):
            print("You can't move outside the maze!")
            return

        self.player_pos = new_pos

        # Slide
        if self.maze.floor_type[y + dy][x + dx] == 'ice':
            dest = self.maze.slide_dest.get(self.player_pos, {}).get(direction)
            if dest and dest != self.player_pos:
                print(f"You slide on ice to {dest}.")
                self.player_pos = dest
            else:
                print(f"You moved to {self.player_pos}.")
        else:
            print(f"You moved to {self.player_pos}.")

        # Check game status
        if self.player_pos in self.maze.monsters:
            print("You stepped on a monster! Game Over.")
            self.running = False
        elif self.player_pos == self.maze.end:
            print("You found the exit! Congratulations, you win!")
            self.running = False


if __name__ == "__main__":
    game = GameEngine(width=10, height=10)
    game.start()
