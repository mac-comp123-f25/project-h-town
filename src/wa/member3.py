import pygame, random, math

pygame.init()

# ---------------- SETTINGS ----------------
W, H = 800, 600
FPS = 60

STAR_COUNT   = 5
STAR_SPEED   = 3
STAR_SIZE    = 32
LASER_SPEED  = 10
LASER_COOLDOWN = 180  # ms

BLACK = (40, 30, 100)
RED   = (40, 240, 255)
GOLD  = (255, 215, 80)
WHITE = (255, 60, 60)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Shooting Stars (Fast Mode)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)


def draw_star(surf, x, y, size, color):
    pts, spikes = [], 5
    outer, inner = size, size * 0.45
    angle, step = math.pi / 2, math.pi / spikes
    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        pts.append((x + math.cos(angle) * r, y - math.sin(angle) * r))
        angle += step
    pygame.draw.polygon(surf, color, pts)


# ------------ SIMPLE DISPLAY LOOP ------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw ONE star just to show something on screen
    draw_star(screen, W//2, H//2, STAR_SIZE, GOLD)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

