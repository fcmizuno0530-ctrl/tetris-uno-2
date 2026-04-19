import pygame
import sys
import random
import serial
import time
import math

ser = serial.Serial("COM5", 9600)
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.mixer.init()
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

WIDTH, HEIGHT = 300, 600
BLOCK = 30
COLS = WIDTH // BLOCK
ROWS = HEIGHT // BLOCK

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

SHAPES = [
    ([[1,1,1,1]], (0,255,255)),
    ([[1,1],[1,1]], (255,255,0)),
    ([[0,1,0],[1,1,1]], (128,0,128)),
    ([[1,0,0],[1,1,1]], (255,165,0)),
    ([[0,0,1],[1,1,1]], (0,0,255)),
    ([[1,1,0],[0,1,1]], (0,255,0)),
    ([[0,1,1],[1,1,0]], (255,0,0))
]

def make_beep(freq=440, duration=0.1, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        val = int(32767 * volume * math.sin(2 * math.pi * freq * t))
        buf += val.to_bytes(2, byteorder='little', signed=True)
    return pygame.mixer.Sound(buffer=buf)

rotate_sound = make_beep(800, 0.05)
clear_sound  = make_beep(400, 0.15)
lock_sound   = make_beep(200, 0.05)

score = 0
level = 1
drop_speed = 30

def new_piece():
    shape, color = random.choice(SHAPES)
    x = COLS//2 - len(shape[0])//2
    y = 0
    return shape, color, x, y

shape, color, x, y = new_piece()

def rotate(s):
    return [list(row) for row in zip(*s[::-1])]

def can_move(s, nx, ny):
    for r in range(len(s)):
        for c in range(len(s[r])):
            if s[r][c]:
                gx, gy = nx+c, ny+r
                if gx < 0 or gx >= COLS or gy >= ROWS:
                    return False
                if gy >= 0 and grid[gy][gx]:
                    return False
    return True

def fix_piece():
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                grid[y+r][x+c] = color

def clear_lines():
    global grid, score
    new = []
    cleared = 0
    for row in grid:
        if all(row):
            cleared += 1
        else:
            new.append(row)
    for _ in range(cleared):
        new.insert(0, [0]*COLS)
    grid = new
    if cleared == 1:
        score += 100
    elif cleared == 2:
        score += 300
    elif cleared == 3:
        score += 500
    elif cleared >= 4:
        score += 800
    if cleared > 0:
        clear_sound.play()

def game_over():
    return any(grid[0])

def get_ghost_y(shape, x, y):
    ghost_y = y
    while can_move(shape, x, ghost_y + 1):
        ghost_y += 1
    return ghost_y

last_input_time = 0
INPUT_DELAY = 0.12

frame = 0
font = pygame.font.SysFont(None, 30)

while True:
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    now = time.time()
    if ser.in_waiting and now - last_input_time > INPUT_DELAY:
        data = ser.readline().decode(errors='ignore').strip()

        if data == "L":
            if can_move(shape, x-1, y):
                x -= 1
                last_input_time = now

        elif data == "R":
            if can_move(shape, x+1, y):
                x += 1
                last_input_time = now

        elif data == "D":
            if can_move(shape, x, y+1):
                y += 1
                last_input_time = now

        elif data == "T":
            new_s = rotate(shape)
            if can_move(new_s, x, y):
                shape = new_s
                rotate_sound.play()
                last_input_time = now

    level = score // 1000 + 1
    drop_speed = max(5, 30 - (level - 1)*2)

    frame += 1
    if frame % drop_speed == 0:
        if can_move(shape, x, y+1):
            y += 1
        else:
            fix_piece()
            lock_sound.play()
            clear_lines()

            if game_over():
                pygame.quit()
                sys.exit()

            shape, color, x, y = new_piece()

    screen.fill((0,0,0))

    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c]:
                pygame.draw.rect(screen, grid[r][c],
                                 (c*BLOCK, r*BLOCK, BLOCK, BLOCK))
                pygame.draw.rect(screen, (50,50,50),
                                 (c*BLOCK, r*BLOCK, BLOCK, BLOCK), 1)

    ghost_y = get_ghost_y(shape, x, y)
    ghost_color = tuple(c//3 for c in color)

    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                pygame.draw.rect(
                    screen,
                    ghost_color,
                    ((x+c)*BLOCK, (ghost_y+r)*BLOCK, BLOCK, BLOCK)
                )

    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                pygame.draw.rect(
                    screen,
                    color,
                    ((x+c)*BLOCK, (y+r)*BLOCK, BLOCK, BLOCK)
                )
                pygame.draw.rect(
                    screen,
                    (50,50,50),
                    ((x+c)*BLOCK, (y+r)*BLOCK, BLOCK, BLOCK),
                    1
                )

    score_text = font.render(f"Score: {score}", True, (255,255,255))
    level_text = font.render(f"Level: {level}", True, (255,255,255))

    screen.blit(score_text, (5, 5))
    screen.blit(level_text, (5, 30))

    pygame.display.update()