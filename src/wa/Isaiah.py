import pygame
import random

pygame.init()

# -------------------------------
# SETTINGS (tuned for speed)
# -------------------------------
W, H = 800, 600
FPS = 60

STAR_MAX = 12
LASER_MAX = 20

STAR_SPEED_MIN = 2
STAR_SPEED_MAX = 4

LASER_SPEED = 8
CANNON_SPEED = 6

# colors
BLACK = (0, 0, 0)
RED   = (255, 40, 40)
GOLD  = (255, 220, 60)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Galaga FAST — No Lag")

font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()

# -------------------------------
# GAME OBJECTS
# -------------------------------

class Cannon:
    def __init__(self):
        self.x = W // 2
        self.y = H - 40
        self.w = 50
        self.h = 20
        self.score = 0
        self.lives = 3

    @property
    def rect(self):
        return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

    def move(self, dx):
        self.x = max(25, min(W - 25, self.x + dx))

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, WHITE, (self.x - 3, self.y - 35, 6, 25))

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def rect(self):
        return pygame.Rect(self.x - 2, self.y - 12, 4, 12)

    def update(self):
        self.y -= LASER_SPEED

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)

    def offscreen(self):
        return self.y < -20

class Star:
    def __init__(self):
        self.x = random.randint(20, W - 20)
        self.y = -20
        self.speed = random.uniform(STAR_SPEED_MIN, STAR_SPEED_MAX)
        self.r = 12

    @property
    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)

    def update(self):
        self.y += self.speed

    def draw(self):
        # star body
        pygame.draw.circle(screen, GOLD, (int(self.x), int(self.y)), self.r)
        # simple streak (fast)
        pygame.draw.line(screen, GOLD, (self.x, self.y), (self.x, self.y - 20), 3)

    def offscreen(self):
        return self.y > H + 30

# -------------------------------
# GAME LOOP
# -------------------------------
def main():
    running = True
    cannon = Cannon()
    lasers = []
    stars = []

    last_laser = 0
    last_spawn = 0

    move_left = move_right = False

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        # -------------------------
        # INPUT
        # -------------------------
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a): move_left = True
                if e.key in (pygame.K_RIGHT, pygame.K_d): move_right = True
            if e.type == pygame.KEYUP:
                if e.key in (pygame.K_LEFT, pygame.K_a): move_left = False
                if e.key in (pygame.K_RIGHT, pygame.K_d): move_right = False

        # move cannon
        dx = (-CANNON_SPEED if move_left else 0) + (CANNON_SPEED if move_right else 0)
        cannon.move(dx)

        # -------------------------
        # AUTOFIRE (laser cap)
        # -------------------------
        if now - last_laser > 180 and len(lasers) < LASER_MAX:
            lasers.append(Laser(cannon.x, cannon.y - 30))
            last_laser = now

        # -------------------------
        # SPAWN STARS (star cap)
        # -------------------------
        if now - last_spawn > 550 and len(stars) < STAR_MAX:
            stars.append(Star())
            last_spawn = now

        # -------------------------
        # UPDATE LASERS
        # -------------------------
        for l in lasers:
            l.update()
        lasers = [l for l in lasers if not l.offscreen()]

        # -------------------------
        # UPDATE STARS
        # -------------------------
        for s in stars:
            s.update()

        # -------------------------
        # COLLISIONS: lasers → stars
        # -------------------------
        for l in lasers[:]:
            for s in stars[:]:
                if l.rect.colliderect(s.rect):
                    try:
                        lasers.remove(l)
                        stars.remove(s)
                    except ValueError:
                        pass
                    cannon.score += 10
                    break

        # -------------------------
        # CHECK BOTTOM (lose life)
        # -------------------------
        for s in stars[:]:
            if s.offscreen():     # ship touches bottom
                stars.remove(s)
                cannon.lives -= 1
                if cannon.lives <= 0:
                    running = False

        # -------------------------
        # DRAW EVERYTHING
        # -------------------------
        screen.fill(BLACK)

        # draw stars
        for s in stars:
            s.draw()

        # draw lasers
        for l in lasers:
            l.draw()

        # draw cannon
        cannon.draw()

        # HUD
        score_text = font.render(f"Score: {cannon.score}", True, WHITE)
        lives_text = font.render(f"Lives: {cannon.lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 40))

        pygame.display.flip()

    # -------------------------
    # GAME OVER SCREEN
    # -------------------------
    screen.fill(BLACK)
    over = font.render("GAME OVER", True, RED)
    final = font.render(f"Final Score: {cannon.score}", True, WHITE)
    screen.blit(over, (W//2 - over.get_width()//2, H//2 - 40))
    screen.blit(final, (W//2 - final.get_width()//2, H//2))
    pygame.display.flip()

    pygame.time.wait(2000)


if __name__ == "__main__":
    main()
    pygame.quit()

