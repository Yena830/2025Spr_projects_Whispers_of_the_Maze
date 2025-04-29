import pygame
from echo_maze import EchoMaze

pygame.init()
pygame.font.init()
title_font=pygame.font.SysFont(None,50)
font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 30)


pygame.mixer.music.load('sounds/creepy_bg.mp3')
pygame.mixer.music.play(-1)
slide_sound = pygame.mixer.Sound('sounds/slide.mp3')
thud_sound = pygame.mixer.Sound('sounds/thud.mp3')
growl_sound = pygame.mixer.Sound('sounds/growl.mp3')
breeze_sound = pygame.mixer.Sound('sounds/breeze.mp3')
win_sound = pygame.mixer.Sound('sounds/win.mp3')
lose_sound = pygame.mixer.Sound('sounds/girl_lose.mp3')

CELL_SIZE = 60
VIEW_SIZE = 7  # 视野范围 7x7
SCREEN = pygame.display.set_mode((VIEW_SIZE * CELL_SIZE, VIEW_SIZE * CELL_SIZE + 50))
pygame.display.set_caption("EchoMaze - Follow View")


player_sprites = {
    'UP': pygame.image.load('icon/player_up.png'),
    'DOWN': pygame.image.load('icon/player_down.png'),
    'LEFT': pygame.image.load('icon/left.png'),
    'RIGHT': pygame.image.load('icon/right.png')
}
current_sprite = player_sprites['DOWN']


monster_img = pygame.image.load('icon/monster.png')
monster_img = pygame.transform.scale(monster_img, (CELL_SIZE, CELL_SIZE))
wall_img = pygame.image.load('icon/wall.png')
wall_img = pygame.transform.scale(wall_img, (CELL_SIZE, CELL_SIZE))


# player_img = pygame.image.load('icon/icon.png')
# player_img = pygame.transform.scale(player_img, (CELL_SIZE, CELL_SIZE))

BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
CYAN = (0, 100, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

def draw_button(text, y_pos):
    button_font = pygame.font.SysFont(None, 40)
    button_text = button_font.render(text, True, BLACK)
    button_rect = button_text.get_rect(center=(VIEW_SIZE * CELL_SIZE // 2, y_pos))
    pygame.draw.rect(SCREEN, GRAY, button_rect.inflate(20, 10))
    SCREEN.blit(button_text, button_rect)
    return button_rect

def show_start_screen():
    SCREEN.fill(BLACK)
    title = title_font.render("Whispers of the Maze", True, RED)
    SCREEN.blit(title, title.get_rect(center=(VIEW_SIZE * CELL_SIZE // 2, 150)))


    subtitle = font.render("Can you escape? Find the exit!", True, WHITE)
    SCREEN.blit(subtitle, subtitle.get_rect(center=(VIEW_SIZE * CELL_SIZE // 2, 200)))


    start_btn = draw_button("Start Game", 400)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    waiting = False
            elif event.type == pygame.KEYDOWN:
                waiting = False

def show_end_screen(message, color):
    SCREEN.fill(BLACK)
    text = title_font.render(message, True, color)
    SCREEN.blit(text, text.get_rect(center=(VIEW_SIZE * CELL_SIZE // 2, 200)))
    restart_btn = draw_button("Restart", 300)
    quit_btn = draw_button("Quit", 350)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if restart_btn.collidepoint(event.pos):
                    waiting = False
                elif quit_btn.collidepoint(event.pos):
                    pygame.quit()
                    exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def run_game():
    maze = EchoMaze(10, 10)
    # maze.print()
    player_pos = list(maze.start)
    echo_feedback = []
    echo_timer = 0
    status_message = "Find the exit and escape this place!"
    clock = pygame.time.Clock()
    global current_sprite
    current_sprite = player_sprites['DOWN']

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                move_dir = None
                if event.key == pygame.K_UP:
                    move_dir = 'UP'
                elif event.key == pygame.K_DOWN:
                    move_dir = 'DOWN'
                elif event.key == pygame.K_LEFT:
                    move_dir = 'LEFT'
                elif event.key == pygame.K_RIGHT:
                    move_dir = 'RIGHT'

                if move_dir:
                    current_sprite = player_sprites[move_dir]
                    dx, dy = maze.DIRECTIONS[move_dir]
                    idx = maze._idx(player_pos[0], player_pos[1])
                    if not maze.cells[idx][move_dir]:
                        player_pos[0] += dx
                        player_pos[1] += dy
                        status_message = f"You moved {move_dir}."
                        if maze.floor_type[player_pos[1]][player_pos[0]] == 'ice':
                            slide_sound.play()
                            dest = maze.slide_dest.get(tuple(player_pos), {}).get(move_dir)
                            if dest:
                                player_pos = list(dest)
                                status_message = f"Oops! You slipped across the ice!"

                        if tuple(player_pos) == maze.end:
                            win_sound.play()
                            show_end_screen("YOU WIN!", GREEN)
                            return
                        if tuple(player_pos) in maze.monsters:
                            lose_sound.play()
                            show_end_screen("GAME OVER!", RED)
                            return

                echo_dir = None
                if event.key == pygame.K_w:
                    echo_dir = 'UP'
                elif event.key == pygame.K_s:
                    echo_dir = 'DOWN'
                elif event.key == pygame.K_a:
                    echo_dir = 'LEFT'
                elif event.key == pygame.K_d:
                    echo_dir = 'RIGHT'

                if echo_dir:
                    echoes = maze.send_echo(tuple(player_pos), echo_dir)
                    if not echoes:
                        status_message = "Silence... Nothing detected."
                    else:
                        first_echo = echoes[0]
                        sound_desc = {
                            'wall': 'a thud',
                            'monster': 'a growl',
                            'exit': 'a breeze'
                        }
                        heard = sound_desc.get(first_echo['type'], 'something')
                        status_message = f"You hear {heard} after {first_echo['delay']}s."
                    echo_feedback = [(echo_dir, e['type'], (e['delay']//2)+1) for e in echoes]
                    echo_timer = pygame.time.get_ticks()
                    for e in echoes:
                        if e['type'] == 'wall':
                            thud_sound.play()
                        elif e['type'] == 'monster':
                            growl_sound.play()
                        elif e['type'] == 'exit':
                            breeze_sound.play()

        SCREEN.fill(BLACK)

        px, py = player_pos
        offset_x = px - VIEW_SIZE // 2
        offset_y = py - VIEW_SIZE // 2

        for vy in range(VIEW_SIZE):
            for vx in range(VIEW_SIZE):
                mx = offset_x + vx
                my = offset_y + vy
                if not maze._in_bounds(mx, my):
                    continue

        if echo_feedback and pygame.time.get_ticks() - echo_timer < 500:
            for direction, obj_type, steps in echo_feedback:
                dx, dy = maze.DIRECTIONS[direction]
                ex, ey = px + dx * steps, py + dy * steps
                vx = ex - offset_x
                vy = ey - offset_y
                if 0 <= vx < VIEW_SIZE and 0 <= vy < VIEW_SIZE:
                    rect = pygame.Rect(vx * CELL_SIZE, vy * CELL_SIZE + 50, CELL_SIZE, CELL_SIZE)
                    if obj_type == 'wall':
                        SCREEN.blit(wall_img,rect)
                    elif obj_type == 'monster':
                        SCREEN.blit(monster_img, rect)
                    elif obj_type == 'exit':
                        pygame.draw.rect(SCREEN, GREEN, rect)

        center_rect = pygame.Rect((VIEW_SIZE//2) * CELL_SIZE, (VIEW_SIZE//2) * CELL_SIZE + 50, CELL_SIZE, CELL_SIZE)
        # pygame.draw.circle(SCREEN, YELLOW, center_rect.center, CELL_SIZE // 3)
        SCREEN.blit(pygame.transform.scale(current_sprite, (CELL_SIZE, CELL_SIZE)), center_rect)

        status_text = small_font.render(status_message, True, WHITE)
        SCREEN.blit(status_text, (10, 10))

        pygame.display.flip()

def main():
    show_start_screen()
    while True:
        run_game()

if __name__ == "__main__":
    main()
