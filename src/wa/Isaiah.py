import pygame
import random
import math

pygame.init()

# ---------------------------------------
# SETTINGS (all tuned for performance)
# ---------------------------------------
W, H = 800, 600
FPS = 60

STAR_COUNT = 5          # very low = no lag
STAR_SPEED = 3
STAR_SIZE = 32          # bigger stars
TRAIL_LENGTH = 6        # short = fast performance

LASER_SPEED = 10
LASER_COOLDOWN = 180    # ms

# Colors
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GOLD = (255, 215, 80)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Shooting Stars (Fast Mode)")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 32)


# ---------------------------------------
# DRAW A STAR SHAPE
# ---------------------------------------
def draw_star(surf, x, y, size, color):
    pts = []
    spikes = 5
    outer = size
    inner = size * 0.45

    angle = math.pi / 2
    step = math.pi / spikes

    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        px = x + math.cos(angle) * r
        py = y - math.sin(angle) * r
        pts.append((px, py))
        angle += step

    pygame.draw.polygon(surf, color, pts)


# ---------------------------------------
# GAME OBJECTS
# ---------------------------------------
class Cannon:
    def __init__(self):
        self.x = W // 2
        self.y = H - 60
        self.speed = 10
        self.lives = 3
        self.score = 0

    def update(self, left, right):
        if left:
            self.x -= self.speed
        if right:
            self.x += self.speed
        self.x = max(20, min(W - 20, self.x))

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x - 25, self.y, 50, 20))
        pygame.draw.rect(screen, WHITE, (self.x - 4, self.y - 20, 8, 20))


class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self):
        self.y -= LASER_SPEED

    def offscreen(self):
        return self.y < -10

    def rect(self):
        return pygame.Rect(self.x - 3, self.y - 6, 6, 12)

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x - 2, self.y - 10, 4, 10))


class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(50, W - 50)
        self.y = random.randint(-600, -50)
        self.speed = STAR_SPEED
        self.trail = [(self.x, self.y)] * TRAIL_LENGTH

    def update(self):
        self.trail.append((self.x, self.y))
        self.trail.pop(0)
        self.y += self.speed

    def rect(self):
        return pygame.Rect(self.x - STAR_SIZE, self.y - STAR_SIZE, STAR_SIZE * 2, STAR_SIZE * 2)

    def offscreen(self):
        return self.y > H + 50

    def draw(self):
        # Trail (golden fading lines)
        for i, (tx, ty) in enumerate(self.trail):
            fade = int(255 * (i / TRAIL_LENGTH))
            pygame.draw.circle(screen, (255, 215, 80, fade), (int(tx), int(ty)), 6)

        # Star shape
        draw_star(screen, self.x, self.y, STAR_SIZE, GOLD)


# ---------------------------------------
# MAIN GAME LOOP
# ---------------------------------------
def main():
    cannon = Cannon()
    lasers = []
    stars = [Star() for _ in range(STAR_COUNT)]

    last_laser = 0
    running = True

    left = right = False

    while running:
        dt = clock.tick(FPS)
        time_now = pygame.time.get_ticks()

        # ---------------- INPUT ----------------
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    left = True
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    right = True
                if e.key == pygame.K_ESCAPE:
                    running = False
            elif e.type == pygame.KEYUP:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    left = False
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    right = False

        # ---------------- UPDATE ----------------
        cannon.update(left, right)

        # Auto-fire
        if time_now - last_laser > LASER_COOLDOWN:
            lasers.append(Laser(cannon.x, cannon.y - 20))
            last_laser = time_now

        for l in lasers:
            l.update()
        lasers = [l for l in lasers if not l.offscreen()]

        for s in stars:
            s.update()

        # COLLISION: laser hits star
        for l in lasers[:]:
            for s in stars:
                if l.rect().colliderect(s.rect()):
                    lasers.remove(l)
                    s.reset()
                    cannon.score += 10
                    break

        # LOSE LIFE: star reaches bottom
        for s in stars:
            if s.offscreen():
                cannon.lives -= 1
                s.reset()

        if cannon.lives <= 0:
            running = False

        # ---------------- DRAW ----------------
        screen.fill(BLACK)

        # stars
        for s in stars:
            s.draw()

        # lasers
        for l in lasers:
            l.draw()

        # cannon
        cannon.draw()

        # UI
        screen.blit(font.render(f"Score: {cannon.score}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Lives: {cannon.lives}", True, WHITE), (10, 40))

        pygame.display.flip()

    pygame.quit()


main()
