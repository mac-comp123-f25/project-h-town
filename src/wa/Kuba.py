"""
Galaga-style mini-game
- Controls: Left/Right arrows or A/D to move.
- The cannon auto-fires red lasers upward.
- Golden shooting stars fall from the top and leave golden streaks behind.
- Background is black.
"""

import pygame
import random
import math
from collections import deque

# ----- Configuration -----
SCREEN_W, SCREEN_H = 800, 600
FPS = 60

CANNON_SPEED = 6
LASER_SPEED = 9
LASER_COOLDOWN_MS = 200  # auto-fire interval

STAR_SPAWN_INTERVAL_MS = 700
STAR_MIN_SPEED = 1.5
STAR_MAX_SPEED = 3.0
STAR_TRAIL_LENGTH = 12  # number of points in trail

STAR_SHOOT_CHANCE = 0.02  # chance per frame a star shoots a bullet
STAR_BULLET_SPEED = 4.0

# Colors
BLACK = (0, 0, 0)
RED = (255, 30, 30)
GOLD = (255, 200, 50)
WHITE = (255, 255, 255)
DARK_GOLD = (170, 120, 10)

# ----- Pygame init -----
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Galaga-style: Golden Shooting Stars")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# ----- Game objects -----
class Cannon:
    def __init__(self):
        self.width = 50
        self.height = 24
        self.x = SCREEN_W // 2
        self.y = SCREEN_H - 50
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.lives = 3
        self.score = 0

    def update(self, dx):
        self.x += dx
        # clamp
        self.x = max(self.width // 2 + 8, min(SCREEN_W - self.width // 2 - 8, self.x))
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        # simple cannon: rounded base + barrel
        base_rect = pygame.Rect(0, 0, self.width, self.height)
        base_rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surf, WHITE, base_rect, border_radius=8)
        # barrel
        barrel = pygame.Rect(0, 0, 6, 28)
        barrel.center = (int(self.x), int(self.y - 20))
        pygame.draw.rect(surf, WHITE, barrel, border_radius=4)
        # small highlight
        pygame.draw.rect(surf, (230, 230, 230), base_rect.inflate(-8, -8), border_radius=6)

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 4

    def update(self):
        self.y -= LASER_SPEED

    def offscreen(self):
        return self.y < -10

    def draw(self, surf):
        # core
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), self.radius)
        # glow
        pygame.draw.circle(surf, (255, 120, 120), (int(self.x), int(self.y)), self.radius + 2, 1)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

class Star:
    def __init__(self):
        self.x = random.uniform(30, SCREEN_W - 30)
        self.y = -20
        # give slight horizontal velocity to make them 'shooting'
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(STAR_MIN_SPEED, STAR_MAX_SPEED)
        self.radius = random.randint(10, 16)
        # trail as deque of previous positions
        self.trail = deque(maxlen=STAR_TRAIL_LENGTH)
        # rotation angle for twinkle
        self.angle = random.random() * math.pi * 2
        self.angle_speed = random.uniform(-0.04, 0.04)
        self.alive = True

    def update(self):
        self.trail.appendleft((self.x, self.y))
        self.x += self.vx
        self.y += self.vy
        self.angle += self.angle_speed
        # bounce horizontally on edges
        if self.x < 10:
            self.x = 10
            self.vx *= -1
        elif self.x > SCREEN_W - 10:
            self.x = SCREEN_W - 10
            self.vx *= -1

    def offscreen(self):
        return self.y > SCREEN_H + 50

    def draw(self, surf):
        # draw trail (golden streaks)
        if len(self.trail) >= 2:
            points = list(self.trail)
            # thickness decreases along trail
            for i in range(len(points)-1):
                a = points[i]
                b = points[i+1]
                t = i / (len(points)-1)
                thickness = int((1.0 - t) * (self.radius * 0.9)) + 1
                alpha = int(220 * (1.0 - t))
                # create a surface for alpha blending
                seg_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                pygame.draw.line(seg_surf, (GOLD[0], GOLD[1], GOLD[2], alpha), a, b, thickness)
                surf.blit(seg_surf, (0,0))
        # star body - simple radial circle + twinkle spikes
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.radius)
        # small inner circle for depth
        pygame.draw.circle(surf, DARK_GOLD, (int(self.x), int(self.y)), max(2, self.radius//3))
        # twinkle spike
        spike_len = self.radius + 6
        sx = int(self.x + math.cos(self.angle) * spike_len)
        sy = int(self.y + math.sin(self.angle) * spike_len)
        pygame.draw.line(surf, (255, 230, 120), (int(self.x), int(self.y)), (sx, sy), 2)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

class StarBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5

    def update(self):
        self.y += STAR_BULLET_SPEED

    def offscreen(self):
        return self.y > SCREEN_H + 20

    def draw(self, surf):
        # golden small bullet
        pygame.draw.circle(surf, (255, 210, 80), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (200, 150, 20), (int(self.x), int(self.y)), self.radius-2, 1)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

# explosion particles for hit effect
class Particle:
    def __init__(self, x, y, color, life=40):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = life
        self.color = color
        self.age = 0
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12  # gravity
        self.age += 1

    def alive(self):
        return self.age < self.life

    def draw(self, surf):
        alpha = max(0, 255 - int(255 * (self.age / self.life)))
        part_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(part_surf, (self.color[0], self.color[1], self.color[2], alpha), (self.size, self.size), self.size)
        surf.blit(part_surf, (int(self.x - self.size), int(self.y - self.size)))

# ----- Game state -----
def main():
    running = True
    cannon = Cannon()
    lasers = []
    stars = []
    star_bullets = []
    particles = []

    last_laser_time = 0
    last_star_spawn = 0

    move_left = move_right = False

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    move_left = True
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    move_right = True
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    move_left = False
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    move_right = False

        # Update cannon movement
        dx = 0
        if move_left: dx -= CANNON_SPEED
        if move_right: dx += CANNON_SPEED
        cannon.update(dx)

        # Auto-fire lasers
        if now - last_laser_time >= LASER_COOLDOWN_MS:
            # create a laser from the tip of the barrel
            lasers.append(Laser(cannon.x, cannon.y - 32))
            last_laser_time = now

        # Spawn stars
        if now - last_star_spawn >= STAR_SPAWN_INTERVAL_MS:
            stars.append(Star())
            last_star_spawn = now

        # Update lasers
        for l in lasers:
            l.update()
        lasers = [l for l in lasers if not l.offscreen()]

        # Update stars
        for s in stars:
            s.update()
            # sometimes shooting stars fire a small bullet downward
            if random.random() < STAR_SHOOT_CHANCE:
                star_bullets.append(StarBullet(s.x, s.y + s.radius + 6))

        # Update star bullets
        for sb in star_bullets:
            sb.update()
        star_bullets = [b for b in star_bullets if not b.offscreen()]

        # Update particles
        for p in particles:
            p.update()
        particles = [p for p in particles if p.alive()]

        # Collisions: lasers vs stars
        for l in lasers[:]:
            lr = l.rect()
            hit_any = False
            for s in stars[:]:
                if lr.colliderect(s.rect()):
                    hit_any = True
                    try:
                        stars.remove(s)
                    except ValueError:
                        pass
                    try:
                        lasers.remove(l)
                    except ValueError:
                        pass
                    # spawn explosion particles
                    for _ in range(14):
                        particles.append(Particle(s.x + random.uniform(-6,6), s.y + random.uniform(-6,6), GOLD, life=30 + random.randint(0,20)))
                    cannon.score += 10
                    break
            if hit_any:
                continue

        # Collisions: star bullets vs cannon
        for b in star_bullets[:]:
            if b.rect().colliderect(cannon.rect):
                star_bullets.remove(b)
                cannon.lives -= 1
                # explosion
                for _ in range(12):
                    particles.append(Particle(cannon.x + random.uniform(-8,8), cannon.y + random.uniform(-8,8), (255,120,60), life=25))
                if cannon.lives <= 0:
                    running = False

        # Remove offscreen stars
        stars = [s for s in stars if not s.offscreen()]

        # draw
        screen.fill(BLACK)

        # starfield: subtle tiny stars in background
        for i in range(30):
            # static background sparkle (cheap)
            bx = (i * 31) % SCREEN_W
            by = (i * 47) % SCREEN_H
            pygame.draw.circle(screen, (20,20,20), (bx, by), 1)

        # draw stars (with trails)
        for s in stars:
            s.draw(screen)
        # draw star bullets
        for b in star_bullets:
            b.draw(screen)
        # draw lasers
        for l in lasers:
            l.draw(screen)
        # draw cannon
        cannon.draw(screen)
        # draw particles on top
        for p in particles:
            p.draw(screen)

        # UI
        score_surf = font.render(f"Score: {cannon.score}", True, WHITE)
        lives_surf = font.render(f"Lives: {cannon.lives}", True, WHITE)
        screen.blit(score_surf, (12, 12))
        screen.blit(lives_surf, (12, 36))

        # hint
        hint = font.render("Move: ← → or A/D. Auto-fire lasers. Avoid golden bullets!", True, (180,180,180))
        screen.blit(hint, (SCREEN_W - hint.get_width() - 12, 12))

        pygame.display.flip()

    # game over screen
    game_over(screen, cannon.score)

def game_over(surface, score):
    surface.fill(BLACK)
    big = pygame.font.SysFont(None, 72)
    t1 = big.render("GAME OVER", True, (255, 80, 80))
    t2 = font.render(f"Final Score: {score}", True, WHITE)
    t3 = font.render("Press ESC or close window to quit.", True, (200,200,200))
    surface.blit(t1, ((SCREEN_W - t1.get_width())//2, SCREEN_H//2 - 90))
    surface.blit(t2, ((SCREEN_W - t2.get_width())//2, SCREEN_H//2 - 20))
    surface.blit(t3, ((SCREEN_W - t3.get_width())//2, SCREEN_H//2 + 30))
    pygame.display.flip()

    # wait until user closes or ESC
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
    pygame.quit()
