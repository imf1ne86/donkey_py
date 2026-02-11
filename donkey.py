"""
* Игра "donkey_py"
* *************************
* Программа является портом игры "Donkey" от IBM 1982 года,
* которая была написана на языке программирования MS-DOS
* QBasic, ver. 1.0 для корпорации IBM. Предположительно
* исходный код программы написал сам Билл Гейтс.
* Для работы текущей программы требуется Python 3. Предварительно
* требуется установить необходимые библиотеки:
* $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
* $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org pygame
* Программа является кроссплатформенной. Она должна работать
* под Microsoft Windows, Linux, macOS и т.д.
*
* @author Ефремов А. В., 11.02.2026
"""

import sys
import math
import random
import pygame

# Config (логическое маленькое полотно и масштаб окна)
SCREEN_W, SCREEN_H = 320, 200
SCALE = 3
W, H = SCREEN_W * SCALE, SCREEN_H * SCALE
FPS = 40

# Sprite pixel scale (увеличение спрайтов ~2.5x визуально)
PIX_SCALE = 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CGA_BG = (0, 0, 128)
CGA_BORDER = (192, 192, 192)
CGA_YELLOW = (255, 255, 0)
CGA_CYAN = (0, 255, 255)

SYS_FONT: str = "Courier"

# Tone generator for simple sounds (8-bit mono)
def make_tone(freq, duration_ms, volume=0.5, samplerate=44100):
    n = int(samplerate * (duration_ms / 1000.0))
    buf = bytearray(n)
    for i in range(n):
        t = i / samplerate
        sample = int(128 + 127 * volume * math.sin(2 * math.pi * freq * t))
        buf[i] = max(0, min(255, sample))
    return bytes(buf)

def make_sound(freq, duration_ms):
    arr = make_tone(freq, duration_ms)
    return pygame.mixer.Sound(buffer=arr)

# Base sprites (binary matrices)
CAR_SPR = [
    [0,1,1,1,0],
    [1,1,1,1,1],
    [1,1,1,1,1],
    [0,1,1,1,0],
    [0,1,1,1,0],
    [1,1,1,1,1],
    [1,0,1,0,1],
    [1,0,1,0,1],
    [0,0,1,0,0],
    [0,1,1,1,0],
    [0,1,0,1,0],
]

DONKEY_SPR = [
    [0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,1,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [1,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0],
]


# Drawing helpers on logical surface
def draw_block_pixel(surf, x, y, color):
    # draw PIX_SCALE x PIX_SCALE block at logical coords (x,y)
    # ensure we don't write outside surface
    sx0 = int(x)
    sy0 = int(y)
    for dy in range(PIX_SCALE):
        py = sy0 + dy
        if py < 0 or py >= SCREEN_H: continue
        for dx in range(PIX_SCALE):
            px = sx0 + dx
            if px < 0 or px >= SCREEN_W: continue
            surf.set_at((px, py), color)

def draw_sprite_from_matrix(surf, x, y, matrix, color):
    # x,y are logical coordinates for top-left of sprite (already in logical space)
    for j, row in enumerate(matrix):
        for i, v in enumerate(row):
            if v:
                bx = x + i * PIX_SCALE
                by = y + j * PIX_SCALE
                draw_block_pixel(surf, bx, by, color)

class Car:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.base_w = len(CAR_SPR[0])
        self.base_h = len(CAR_SPR)
        self.w = self.base_w * PIX_SCALE
        self.h = self.base_h * PIX_SCALE
        self.target_x = self.x
        self.move_speed = 8.0
    def update(self):
        if abs(self.x - self.target_x) > 0.5:
            dir = 1 if self.target_x > self.x else -1
            self.x += dir * self.move_speed
            if (dir > 0 and self.x > self.target_x) or (dir < 0 and self.x < self.target_x):
                self.x = self.target_x
    def set_lane_center(self, cx):
        # cx is logical center coordinate of lane
        self.target_x = float(cx - self.w // 2)
    def draw(self, surf):
        draw_sprite_from_matrix(surf, int(round(self.x)), int(round(self.y)), CAR_SPR, CGA_YELLOW)

class Donkey:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.base_w = len(DONKEY_SPR[0])
        self.base_h = len(DONKEY_SPR)
        self.w = self.base_w * PIX_SCALE
        self.h = self.base_h * PIX_SCALE
    def draw(self, surf):
        draw_sprite_from_matrix(surf, int(round(self.x)), int(round(self.y)), DONKEY_SPR, CGA_CYAN)

def rects_collide(ax, ay, aw, ah, bx, by, bw, bh):
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)

def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -8, 1)
    pygame.mixer.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Donkey (scaled sprites)")
    clock = pygame.time.Clock()

    # sounds
    beep = make_sound(880, 60)
    crash = make_sound(220, 220)

    # lane centers (logical coords). These are centers inside road area.
    lane_center_left = 100
    lane_center_right = 180
    lanes = [lane_center_left, lane_center_right]

    # Starting positions for car (account for new sprite size)
    car_x = lanes[0] - (len(CAR_SPR[0]) * PIX_SCALE) // 2
    car_y = SCREEN_H - (PIX_SCALE * len(CAR_SPR)) - 10
    player = Car(car_x, car_y)
    player.set_lane_center(lanes[0])

    obstacles = []
    spawn_timer = 0
    score = 0
    explosion = None

    # Background on logical surface
    bg = pygame.Surface((SCREEN_W, SCREEN_H))
    bg.fill(CGA_BG)
    pygame.draw.rect(bg, CGA_BORDER, (6, 6, 91, SCREEN_H - 12))
    pygame.draw.rect(bg, CGA_BORDER, (183, 6, 119, SCREEN_H - 12))
    for y in range(4, SCREEN_H, 20):
        pygame.draw.line(bg, CGA_BORDER, (140, y), (140, y + 10), 1)
    pygame.draw.line(bg, CGA_BORDER, (100, 0), (100, SCREEN_H), 1)
    pygame.draw.line(bg, CGA_BORDER, (180, 0), (180, SCREEN_H), 1)

    small_font = pygame.font.SysFont(SYS_FONT, 10)

    while True:
        dt = clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if ev.key in (pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT):
                    cur_idx = 0 if abs(player.target_x + player.w//2 - lanes[0]) < abs(player.target_x + player.w//2 - lanes[1]) else 1
                    if ev.key == pygame.K_LEFT:
                        new_idx = 0
                    elif ev.key == pygame.K_RIGHT:
                        new_idx = 1
                    else:
                        new_idx = 1 - cur_idx
                    if new_idx != cur_idx:
                        player.set_lane_center(lanes[new_idx])
                        beep.play()

        player.update()

        spawn_timer -= dt
        if spawn_timer <= 0:
            lane = random.choice([0,1])
            ox = lanes[lane] - (len(DONKEY_SPR[0]) * PIX_SCALE) // 2 + random.randint(-3*PIX_SCALE, 3*PIX_SCALE)
            oy = - (len(DONKEY_SPR) * PIX_SCALE) - 5
            obstacles.append(Donkey(ox, oy))
            spawn_timer = 600 + random.randint(-200, 400)

        for ob in obstacles:
            ob.y += 2

        hit = None
        for ob in obstacles:
            if rects_collide(player.x, player.y, player.w, player.h, ob.x, ob.y, ob.w, ob.h):
                hit = ob
                break
        if hit and explosion is None:
            crash.play()
            explosion = {'t':0, 'max':12, 'cx': player.x + player.w//2, 'cy': player.y + player.h//2}
            if hit in obstacles: obstacles.remove(hit)

        if explosion:
            explosion['t'] += 1
            if explosion['t'] > explosion['max']:
                explosion = None
                score += 1
                obstacles.clear()
                player.x = lanes[0] - player.w//2
                player.set_lane_center(lanes[0])

        obstacles = [o for o in obstacles if o.y < SCREEN_H + 50]

        # Render on logical surface
        frame = bg.copy()
        title = small_font.render("Donkey", True, WHITE)
        instr = small_font.render("Arrows or Space: switch lanes  Esc: quit", True, WHITE)
        frame.blit(title, (5,6))
        frame.blit(instr, (5,24))

        player.draw(frame)
        for ob in obstacles:
            ob.draw(frame)

        if explosion:
            t = explosion['t']
            r = int(t * (PIX_SCALE))  # explosion scaled with PIX_SCALE
            cx = int(explosion['cx']); cy = int(explosion['cy'])
            pygame.draw.circle(frame, CGA_YELLOW, (cx, cy), r, 1)

        # Scale to window and blit
        scaled = pygame.transform.scale(frame, (W, H))
        screen.blit(scaled, (0,0))

        hud_font = pygame.font.SysFont(SYS_FONT, 14)
        score_surf = hud_font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_surf, (6, 6))

        pygame.display.flip()

if __name__ == "__main__":
    main()
