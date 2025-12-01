"""
Galaga-style shooting game with five-point stars and 3-line golden trails.

Controls:
  - Move left/right: Arrow keys or A/D
  - Quit: Esc or window close

Features:
  - Cannon auto-fires red lasers upward.
  - Falling 5-point stars (large), with 3 thin golden streaks trailing behind (starting above the star).
  - Limited number of stars/lasers/particles to guarantee performance.
  - Scoreboard and lives. Lose a life when a star hits the bottom.
  - Explosion particle effect when a star is shot.
"""

import pygame
import random
import math
from collections import deque

# ---------- Config ----------
SCREEN_W, SCREEN_H = 900, 640
FPS = 60

CANNON_SPEED = 7
LASER_SPEED = 10
LASER_COOLDOWN_MS = 180

STAR_SPAWN_INTERVAL_MS = 900
STAR_MIN_SPEED = 1.6
STAR_MAX_SPEED = 3.0
STAR_TRAIL_LEN = 6  # small, to avoid heavy drawing
MAX_STARS = 6  # cap number of falling objects for guaranteed performance

MAX_LASERS = 12
MAX_PARTICLES = 120

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 40, 40)
GOLD = (255, 205, 60)
GOLD_DARK = (200, 140, 20)
HINT_COLOR = (180, 180, 180)

# ---------- Pygame init ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Shooting Stars — Galaga-style")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 72)

# ---------- Helpers ----------
def star_points(cx, cy, outer_r, inner_r_ratio=0.5, rotation=0.0):
    """Return points for a 5-point star polygon centered at (cx,cy)."""
    pts = []
    points = 5
    angle = rotation
    step = math.pi / points
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else outer_r * inner_r_ratio
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        pts.append((x, y))
        angle += step
    return pts

# ---------- Game objects ----------
class Cannon:
    def __init__(self):
        self.w = 68
        self.h = 22
        self.x = SCREEN_W // 2
        self.y = SCREEN_H - 48
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self.lives = 3
        self.score = 0

    def update(self, dx):
        self.x += dx
        self.x = max(self.w//2 + 8, min(SCREEN_W - self.w//2 - 8, self.x))
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        # simple white cannon with barrel
        base = pygame.Rect(0, 0, self.w, self.h)
        base.center = (int(self.x), int(self.y))
        pygame.draw.rect(surf, WHITE, base, border_radius=10)
        barrel = pygame.Rect(0,0,10,28)
        barrel.center = (int(self.x), int(self.y - 20))
        pygame.draw.rect(surf, WHITE, barrel, border_radius=5)
        # inner highlight
        pygame.draw.rect(surf, (230,230,230), base.inflate(-12, -8), border_radius=8)

class Laser:
    __slots__ = ('x','y','r')
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.r = 4

    def update(self):
        self.y -= LASER_SPEED

    def offscreen(self):
        return self.y < -20

    def draw(self, surf):
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (255,140,140), (int(self.x), int(self.y)), self.r+1, 1)

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)

class Star:
    __slots__ = ('x','y','vx','vy','outer_r','rotation','trail','rotation_speed')
    def __init__(self):
        self.reset()

    def reset(self):
        # spawn near top, random x
        margin = 40
        self.x = random.uniform(margin, SCREEN_W - margin)
        self.y = -random.uniform(20, 90)
        # give small horizontal for variety
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(STAR_MIN_SPEED, STAR_MAX_SPEED)
        self.outer_r = random.randint(22, 36)  # bigger stars
        self.rotation = random.uniform(0, math.pi*2)
        self.rotation_speed = random.uniform(-0.03, 0.03)
        # trail deque stores previous centers (small length)
        self.trail = deque(maxlen=STAR_TRAIL_LEN)
        # pre-seed trail a bit above so streaks start above the star
        start_above = max(0, int(self.outer_r * 0.8))
        for i in range(self.trail.maxlen):
            self.trail.appendleft((self.x, self.y - start_above - i * self.vy * 0.6))

    def update(self):
        self.trail.appendleft((self.x, self.y - self.outer_r * 0.6))  # store point slightly above
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rotation_speed
        # bounce horizontally to keep on-screen
        if self.x < 20:
            self.x = 20
            self.vx *= -1
        elif self.x > SCREEN_W - 20:
            self.x = SCREEN_W - 20
            self.vx *= -1

    def offscreen_bottom(self):
        return self.y - self.outer_r > SCREEN_H + 10

    def draw(self, surf):
        # draw 3 thin trail lines (offsets) starting a bit above the star
        if len(self.trail) >= 2:
            # offsets (x offset) to get 3 parallel streaks
            offsets = (-10, 0, 10)
            widths = (2, 2, 1)  # thin lines
            for off_idx, off in enumerate(offsets):
                pts = []
                # start from a little ahead of the current center so streaks "start above" the star
                for (px, py) in self.trail:
                    pts.append((px + off, py))
                # draw as anti-aliased polyline if available; fallback to lines
                if len(pts) >= 2:
                    pygame.draw.aalines(surf, GOLD, False, pts)
                    # draw a thin darker center line for contrast on middle streak
                    if off_idx == 1:
                        pygame.draw.lines(surf, GOLD_DARK, False, pts, widths[off_idx])
        # draw star polygon
        pts = star_points(self.x, self.y, self.outer_r, inner_r_ratio=0.45, rotation=self.rotation)
        pygame.draw.polygon(surf, GOLD, pts)
        # inner darker polygon for depth
        inner_pts = star_points(self.x, self.y, int(self.outer_r * 0.45), inner_r_ratio=0.6, rotation=self.rotation + 0.1)
        pygame.draw.polygon(surf, GOLD_DARK, inner_pts)

    def rect(self):
        r = int(self.outer_r)
        return pygame.Rect(self.x - r, self.y - r, r*2, r*2)

class Particle:
    __slots__ = ('x','y','vx','vy','age','life','size','color')
    def __init__(self, x, y, color, life=30):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3.5, 3.5)
        self.vy = random.uniform(-3.5, 3.5)
        self.age = 0
        self.life = life
        self.size = random.randint(2, 5)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # slight gravity so particles fall
        self.vy += 0.12
        self.vx *= 0.99
        self.age += 1

    def alive(self):
        return self.age < self.life

    def draw(self, surf):
        # fade out by scaling alpha via size reduction (no alpha surface creation)
        prog = 1.0 - (self.age / self.life)
        r = max(1, int(self.size * prog))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)

# ---------- Main ----------
def main():
    running = True
    cannon = Cannon()

    lasers = []  # list of Laser
    stars = []   # list of Star
    particles = []  # list of Particle

    last_laser_time = 0
    last_star_spawn = 0

    move_left = move_right = False

    # Pre-create small pool of star objects to reuse (object pooling)
    star_pool = [Star() for _ in range(MAX_STARS)]
    # We'll use at most MAX_STARS active at a time; star_pool holds fresh stars

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        # --- Events ---
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    move_left = True
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    move_right = True
                elif ev.key == pygame.K_ESCAPE:
                    running = False
            elif ev.type == pygame.KEYUP:
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    move_left = False
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    move_right = False

        # --- Update cannon ---
        dx = 0
        if move_left: dx -= CANNON_SPEED
        if move_right: dx += CANNON_SPEED
        cannon.update(dx)

        # --- Auto-fire lasers (capped) ---
        if now - last_laser_time >= LASER_COOLDOWN_MS and len(lasers) < MAX_LASERS:
            lasers.append(Laser(cannon.x, cannon.y - 30))
            last_laser_time = now

        # --- Spawn stars (but keep count capped) ---
        if now - last_star_spawn >= STAR_SPAWN_INTERVAL_MS:
            if len(stars) < MAX_STARS:
                # take a pooled star, reset it and add to active
                s = star_pool[len(stars)]
                s.reset()
                stars.append(s)
            last_star_spawn = now

        # --- Update lasers ---
        for l in lasers:
            l.update()
        # remove offscreen lasers efficiently
        if lasers:
            lasers = [l for l in lasers if not l.offscreen()]

        # --- Update stars ---
        for s in stars:
            s.update()

        # --- Update particles ---
        for p in particles:
            p.update()
        # keep only alive particles up to MAX_PARTICLES
        if particles:
            particles = [p for p in particles if p.alive()][:MAX_PARTICLES]

        # --- Collisions: lasers vs stars ---
        # Use simple bounding rect collision; iterate over copy to allow removals
        lasers_copy = lasers[:]
        stars_copy = stars[:]
        for l in lasers_copy:
            lr = l.rect()
            hit = False
            for s in stars_copy:
                if lr.colliderect(s.rect()):
                    # hit: remove laser and star, spawn particles, increment score
                    try:
                        lasers.remove(l)
                    except ValueError:
                        pass
                    try:
                        stars.remove(s)
                    except ValueError:
                        pass
                    # particle explosion (golden)
                    for _ in range(18):
                        if len(particles) < MAX_PARTICLES:
                            particles.append(Particle(s.x + random.uniform(-10,10),
                                                      s.y + random.uniform(-10,10),
                                                      GOLD_DARK if random.random() < 0.4 else GOLD,
                                                      life=random.randint(22, 44)))
                    cannon.score += 10
                    hit = True
                    break
            if hit:
                continue

        # --- Stars reach bottom: lose life ---
        # If a star crosses bottom edge, remove it and decrement lives
        for s in stars[:]:
            if s.offscreen_bottom():
                try:
                    stars.remove(s)
                except ValueError:
                    pass
                cannon.lives -= 1
                # small impact particles at cannon top as feedback
                for _ in range(8):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(random.uniform(cannon.x - 12, cannon.x + 12),
                                                  cannon.y - 8,
                                                  (255, 110, 60),
                                                  life=20))
                # lose condition
                if cannon.lives <= 0:
                    running = False

        # --- Draw everything (minimal heavy ops) ---
        screen.fill(BLACK)

        # subtle background starfield (cheap static dots)
        for i in range(28):
            bx = (i * 53) % SCREEN_W
            by = (i * 89) % SCREEN_H
            pygame.draw.circle(screen, (18,18,18), (bx,by), 1)

        # draw stars (trail then star)
        for s in stars:
            s.draw(screen)

        # draw lasers
        for l in lasers:
            l.draw(screen)

        # draw cannon
        cannon.draw(screen)

        # draw particles on top
        for p in particles:
            p.draw(screen)

        # UI: Score and Lives
        score_surf = font.render(f"Score: {cannon.score}", True, WHITE)
        lives_surf = font.render(f"Lives: {cannon.lives}", True, WHITE)
        screen.blit(score_surf, (12, 12))
        screen.blit(lives_surf, (12, 38))

        # hint text
        hint = font.render("Move: ← → or A/D. Auto-fire. Avoid letting stars hit bottom.", True, HINT_COLOR)
        screen.blit(hint, (SCREEN_W - hint.get_width() - 12, 12))

        pygame.display.flip()

    # Game over screen
    game_over_screen(screen, cannon.score)

    pygame.quit()

def game_over_screen(surf, score):
    surf.fill(BLACK)
    t1 = big_font.render("GAME OVER", True, (255, 80, 80))
    t2 = font.render(f"Final Score: {score}", True, WHITE)
    t3 = font.render("Press ESC or close window to quit.", True, (200,200,200))
    surf.blit(t1, ((SCREEN_W - t1.get_width())//2, SCREEN_H//2 - 90))
    surf.blit(t2, ((SCREEN_W - t2.get_width())//2, SCREEN_H//2 - 10))
    surf.blit(t3, ((SCREEN_W - t3.get_width())//2, SCREEN_H//2 + 36))
    pygame.display.flip()

    waiting = True
    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                waiting = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                waiting = False
        clock.tick(30)

if __name__ == "__main__":
    main()
