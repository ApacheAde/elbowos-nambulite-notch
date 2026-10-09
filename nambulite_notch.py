#!/usr/bin/env python3
"""Nambulite Notch — amber neon pinball for ElbowOS. Python 3 + pygame.

Flip the copper paddles, keep the ember ball off the drain, and punch the
notch gate at the top of the table. Left/Right or A/D flip. Space launches.
"""
import math
import os
import random
import subprocess
import sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if "--play" not in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get(
    "ELBOWOS_MP4", "/workspace/artifacts/NAMBULITE_NOTCH_ElbowOS.mp4"
)
TITLE, HANDLE = "NAMBULITE NOTCH", "x.com/ElbowOS"
INK = (12, 8, 10)
AMBER = (255, 146, 42)
COPPER = (214, 118, 58)
TEAL = (42, 232, 196)
MAG = (255, 72, 168)
CREAM = (255, 236, 214)
VIOLET = (168, 92, 255)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if "--play" in sys.argv else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((W, H))
        self.font = pygame.font.SysFont("dejavusans", 68, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.tiny = pygame.font.SysFont("dejavusans", 30, bold=True)
        rng = random.Random(9)
        self.stars = [
            (rng.randint(40, 1040), rng.randint(160, 1800), rng.randint(1, 3))
            for _ in range(90)
        ]
        self.reset()

    def reset(self):
        self.tick = 0
        self.score = 0
        self.combo = 0
        self.balls = 3
        self.left = 0.0
        self.right = 0.0
        self.notch = 0
        self.flash = []
        self.pops = []
        self.trail = []
        self.bumpers = [
            (400, 640, 72, MAG),
            (680, 760, 60, TEAL),
            (460, 940, 54, VIOLET),
            (700, 1080, 66, AMBER),
            (360, 1180, 48, TEAL),
        ]
        self.launch(hard=True)

    def launch(self, hard=False):
        self.bx, self.by = 900.0, 1460.0
        self.vx = random.uniform(-3.5, -0.6)
        self.vy = -34.0 if hard else -28.0

    def flipper(self, side, power):
        if side < 0:
            pivot = (300.0, 1610.0)
            ang = math.radians(32 - 54 * power)
        else:
            pivot = (780.0, 1610.0)
            ang = math.radians(148 + 54 * power)
        tip = (pivot[0] + math.cos(ang) * 220, pivot[1] + math.sin(ang) * 220)
        return pivot, tip

    def step(self, keys=None, auto=False):
        self.tick += 1
        want_l = want_r = False
        if auto:
            pred = self.bx + self.vx * 6
            if self.by > 1180 and self.vy > -2:
                want_l = pred < 560
                want_r = pred > 520
            if self.tick % 90 == 0 and self.by < 700:
                want_l = want_r = True
        elif keys:
            want_l = keys[pygame.K_LEFT] or keys[pygame.K_a]
            want_r = keys[pygame.K_RIGHT] or keys[pygame.K_d]
            if keys[pygame.K_SPACE] and self.by > 1500:
                self.vy = -32
        self.left = max(0.0, min(1.0, self.left + (0.35 if want_l else -0.28)))
        self.right = max(0.0, min(1.0, self.right + (0.35 if want_r else -0.28)))
        self.vy += 0.46
        self.vx *= 0.999
        self.bx += self.vx
        self.by += self.vy
        if self.bx < 168:
            self.bx, self.vx = 168, abs(self.vx) * 0.92
        if self.bx > 912 and not (self.by > 1380 and self.bx > 840):
            self.bx, self.vx = 912, -abs(self.vx) * 0.92
        if self.by < 300:
            self.by, self.vy = 300, abs(self.vy) * 0.8
            self.notch = min(100, self.notch + 18)
            self.score += 40
            self.flash.append([540, 320, 40, 14, AMBER])
        for cx, cy, rad, col in self.bumpers:
            dx, dy = self.bx - cx, self.by - cy
            dist = math.hypot(dx, dy) or 1
            if dist < rad + 22:
                nx, ny = dx / dist, dy / dist
                self.bx, self.by = cx + nx * (rad + 24), cy + ny * (rad + 24)
                dot = self.vx * nx + self.vy * ny
                self.vx = (self.vx - 2 * dot * nx) * 1.04 + nx * 7
                self.vy = (self.vy - 2 * dot * ny) * 1.04 + ny * 7
                self.combo = min(9, self.combo + 1)
                gain = 30 + self.combo * 6
                self.score += gain
                self.notch = min(100, self.notch + 8)
                self.flash.append([cx, cy, rad, 12, col])
                self.pops.append([cx - 18, cy - rad, 18, f"+{gain}"])
        for side, power in ((-1, self.left), (1, self.right)):
            pivot, tip = self.flipper(side, power)
            if self._kick(pivot, tip, power):
                self.flash.append([self.bx, self.by, 26, 8, COPPER])
        if self.by > 1748:
            self.balls -= 1
            self.combo = 0
            self.notch = max(0, self.notch - 20)
            if self.balls < 0:
                self.balls = 3
            self.launch(hard=True)
        speed = math.hypot(self.vx, self.vy)
        if speed > 38:
            self.vx *= 38 / speed
            self.vy *= 38 / speed
        self.trail.append((self.bx, self.by))
        if len(self.trail) > 16:
            self.trail.pop(0)
        self.flash = [f for f in self.flash if f[3] > 1]
        for f in self.flash:
            f[3] -= 1
        self.pops = [p for p in self.pops if p[2] > 1]
        for p in self.pops:
            p[1] -= 1.4
            p[2] -= 1
        if self.notch >= 100 and self.by < 420:
            self.score += 120
            self.notch = 20
            self.pops.append([460, 360, 22, "NOTCH"])

    def _kick(self, a, b, power):
        ax, ay = a
        bx, by = b
        abx, aby = bx - ax, by - ay
        lab = abx * abx + aby * aby or 1
        t = max(0.0, min(1.0, ((self.bx - ax) * abx + (self.by - ay) * aby) / lab))
        px, py = ax + abx * t, ay + aby * t
        if math.hypot(self.bx - px, self.by - py) > 36:
            return False
        ang = math.atan2(aby, abx)
        nx, ny = -math.sin(ang), -abs(math.cos(ang))
        boost = 12 + power * 16
        self.vx += nx * 4 + (1 if bx > ax else -1) * 3
        self.vy = -abs(self.vy) * 0.35 - boost
        self.bx, self.by = px, py - 26
        self.score += 3
        return True

    def draw(self):
        s = self.canvas
        s.fill(INK)
        for i in range(16):
            pygame.draw.rect(s, (28 + i, 10, 14 + i // 2), (0, i * 120, W, 120))
        for x, y, r in self.stars:
            pygame.draw.circle(s, (90, 48, 36), (x, y), r)
        pygame.draw.rect(s, (32, 14, 16), (130, 250, 820, 1500), border_radius=48)
        pygame.draw.rect(s, AMBER, (130, 250, 820, 1500), 8, border_radius=48)
        gate = 220 + int((100 - self.notch) * 1.6)
        pygame.draw.rect(s, TEAL, (430, 268, gate, 18), border_radius=6)
        pygame.draw.rect(s, MAG, (430 + gate, 268, 220 - min(gate, 220), 18))
        pulse = 1 + 0.05 * math.sin(self.tick * 0.25)
        for cx, cy, rad, col in self.bumpers:
            pygame.draw.circle(s, col, (int(cx), int(cy)), int(rad * pulse), 7)
            pygame.draw.circle(s, CREAM, (int(cx), int(cy)), int(rad * 0.32))
        for x, y, rad, life, col in self.flash:
            pygame.draw.circle(s, col, (int(x), int(y)), int(rad + (12 - life) * 5), 3)
        pygame.draw.line(s, COPPER, (168, 1380), (300, 1660), 10)
        pygame.draw.line(s, COPPER, (912, 1380), (780, 1660), 10)
        for side, power in ((-1, self.left), (1, self.right)):
            pivot, tip = self.flipper(side, power)
            pygame.draw.line(s, AMBER, pivot, tip, 24)
            pygame.draw.circle(s, CREAM, (int(pivot[0]), int(pivot[1])), 16)
        for i, (x, y) in enumerate(self.trail):
            pygame.draw.circle(s, (255, 110, 40), (int(x), int(y)), 5 + i // 3)
        pygame.draw.circle(s, AMBER, (int(self.bx), int(self.by)), 22)
        pygame.draw.circle(s, CREAM, (int(self.bx) - 6, int(self.by) - 7), 7)
        for x, y, _life, text in self.pops:
            img = self.tiny.render(text, True, TEAL)
            s.blit(img, (x, y))
        title = self.font.render(TITLE, True, AMBER)
        s.blit(title, title.get_rect(center=(W // 2, 96)))
        score = self.mid.render(f"SCORE  {self.score}", True, CREAM)
        s.blit(score, score.get_rect(center=(W // 2, 176)))
        balls = self.tiny.render(f"BALLS {max(self.balls, 0)}   NOTCH {self.notch}", True, TEAL)
        s.blit(balls, balls.get_rect(center=(W // 2, 1688)))
        handle = self.mid.render(HANDLE, True, MAG)
        s.blit(handle, handle.get_rect(center=(W // 2, H - 70)))
        return s

    def play(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            self.step(pygame.key.get_pressed(), auto=False)
            self.screen.blit(self.draw(), (0, 0))
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(FPS * SECS):
                self.step(auto=True)
                raw = pygame.image.tobytes(self.draw(), "RGB")
                proc.stdin.write(raw)
            proc.stdin.close()
        except BrokenPipeError:
            err = proc.stderr.read().decode("utf-8", "ignore")
            raise SystemExit(f"ffmpeg pipe broke:\n{err[-1500:]}")
        err = proc.stderr.read().decode("utf-8", "ignore")
        if proc.wait() != 0:
            raise SystemExit(f"ffmpeg failed:\n{err[-1500:]}")
        print("wrote", OUT)


def main():
    game = Game()
    if "--play" in sys.argv:
        game.play()
    else:
        game.record()


if __name__ == "__main__":
    main()
