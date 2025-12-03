import pygame, random, math

pygame.init()

# ---------------- SETTINGS ----------------
W, H = 800, 600
FPS = 60

STAR_COUNT   = 5
STAR_SPEED   = 3
STAR_SIZE    = 32

LASER_SPEED  = 10

BLACK = (40, 30, 100)
RED   = (255, 255, 255)
GOLD  = (255, 215, 80)
WHITE = (255, 60, 60)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Shooting Stars (Fast Mode)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)


# ---------------- STAR DRAWING ----------------
def draw_star(surf, x, y, size, color):
    pts = []
    spikes = 5
    outer = size
    inner = size * 0.45
    angle = math.pi / 2
    step = math.pi / spikes

    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        pts.append((x + math.cos(angle) * r, y - math.sin(angle) * r))
        angle += step

    pygame.draw.polygon(surf, color, pts)


# ---------------- EXPLOSION ----------------
class Explosion:
    def __init__(self, x, y):
        self.particles = [
            [x, y,
             math.cos(a := random.uniform(0, 2*math.pi)) * (s := random.uniform(2, 6)),
             math.sin(a) * s,
             random.randint(10, 20)]
            for _ in range(15)
        ]

    def update(self):
        alive = False
        for p in self.particles:
            if p[4] > 0:
                p[0] += p[2]
                p[1] += p[3]
                p[4] -= 1
                alive = True
        return alive

    def draw(self, surf):
        for x, y, _, _, life in self.particles:
            if life > 0:
                pygame.draw.circle(surf, GOLD, (int(x), int(y)), max(1, life // 3))


# ---------------- CANNON ----------------
class Cannon:
    def __init__(self):
        self.x, self.y = W // 2, H - 60
        self.speed = 10
        self.lives = 3
        self.score = 0

    @property
    def pos(self):
        return self.x, self.y

    def update(self, keys):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed

        self.x = max(20, min(W - 20, self.x))

    def draw(self, surf):
        x, y = self.x, self.y
        pygame.draw.rect(surf, WHITE, (x - 25, y, 50, 20))
        pygame.draw.rect(surf, WHITE, (x - 4,  y - 20, 8, 20))


# ---------------- LASER ----------------
class Laser:
    def __init__(self, x, y):
        self.x, self.y = x, y

    @property
    def rect(self):
        return pygame.Rect(self.x - 3, self.y - 6, 6, 12)

    def update(self):
        self.y -= LASER_SPEED

    def offscreen(self):
        return self.y < -10

    def draw(self, surf):
        pygame.draw.rect(surf, RED, (self.x - 2, self.y - 10, 4, 10))


# ---------------- STAR ----------------
class Star:
    def __init__(self):
        self.reset()

    @property
    def rect(self):
        return pygame.Rect(self.x - STAR_SIZE, self.y - STAR_SIZE, STAR_SIZE * 2, STAR_SIZE * 2)

    def reset(self):
        self.x = random.randint(50, W - 50)
        self.y = random.randint(-600, -50)
        self.speed = STAR_SPEED

    def update(self):
        self.y += self.speed

    def offscreen(self):
        return self.y > H + 50

    def draw(self, surf):
        draw_star(surf, self.x, self.y, STAR_SIZE, GOLD)


# ---------------- GAME LOOP ----------------
def main():
    # ------ DIFFICULTY INPUT ------
    print("\nChoose difficulty:")
    print("1 = Easy   (fast lasers)")
    print("2 = Medium (normal)")
    print("3 = Hard   (slow lasers)\n")

    choice = input("Enter 1, 2, or 3: ").strip()

    if choice == "1":
        LASER_COOLDOWN = 200
    elif choice == "3":
        LASER_COOLDOWN = 600
    else:
        LASER_COOLDOWN = 400  # default medium

    # ------ SETUP ------
    cannon = Cannon()
    lasers = []
    stars = [Star() for _ in range(STAR_COUNT)]
    explosions = []
    last_laser = 0

    running = True

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        # events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        cannon.update(keys)

        # shooting
        if now - last_laser > LASER_COOLDOWN:
            x, y = cannon.pos
            lasers.append(Laser(x, y - 20))
            last_laser = now

        for l in lasers:
            l.update()
        lasers = [l for l in lasers if not l.offscreen()]

        for s in stars:
            s.update()

        for ex in explosions[:]:
            if not ex.update():
                explosions.remove(ex)

        # collisions
        for l in lasers[:]:
            for s in stars:
                if l.rect.colliderect(s.rect):
                    lasers.remove(l)
                    explosions.append(Explosion(s.x, s.y))
                    s.reset()
                    cannon.score += 10
                    break

        # lives lost
        for s in stars:
            if s.offscreen():
                cannon.lives -= 1
                s.reset()

        if cannon.lives <= 0:
            running = False

        # drawing
        screen.fill(BLACK)

        for s in stars:
            s.draw(screen)
        for l in lasers:
            l.draw(screen)
        for ex in explosions:
            ex.draw(screen)
        cannon.draw(screen)

        screen.blit(font.render(f"Score: {cannon.score}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Lives: {cannon.lives}", True, WHITE), (10, 40))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
