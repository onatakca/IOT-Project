# river.py
import pygame, math, random, os
from .settings import BLACK

class River:
    """Curved river sized to a viewport; loads textures via image_dir."""
    def __init__(self, vw, vh, image_dir):
        self.vw, self.vh = vw, vh
        self.segments = []
        self.segment_h = 5
        self.scroll_off = 0.0
        self.total_scroll = 0.0
        self.center_x = vw // 2
        self.phase = 0.0
        self.width = int(vw * 0.44)

        # textures (BASE_DIR-aware)
        water_png = pygame.image.load(os.path.join(image_dir, "water.png")).convert_alpha()
        grass_png = pygame.image.load(os.path.join(image_dir, "grass.png")).convert_alpha()
        self.water = pygame.transform.scale(water_png, (128,128))
        self.grass = pygame.transform.scale(grass_png, (192,192))
        self.ww=self.wh=128; self.gw=self.gh=192

        for _ in range(vh // self.segment_h + 20):
            self._add_seg()

    def _add_seg(self):
        if not self.segments:
            off = 0
        else:
            self.phase += 0.02
            off = math.sin(self.phase) * (self.vw*0.11) + random.uniform(-5,5)
            off = max(min(off, 120), -120)
        self.segments.append(off)

    def update(self, speed):
        self.scroll_off += speed
        self.total_scroll += speed
        while self.scroll_off >= self.segment_h:
            self.scroll_off -= self.segment_h
            if self.segments: self.segments.pop(0)
            self._add_seg()
        while self.scroll_off < 0:
            self.scroll_off += self.segment_h
            self.phase -= 0.02
            off = math.sin(self.phase) * (self.vw*0.11) + random.uniform(-5,5)
            off = max(min(off, 120), -120)
            self.segments.insert(0, off)
            if len(self.segments) > 240: self.segments.pop()

    def bounds_at(self, y):
        idx = int((y + self.scroll_off) // self.segment_h)
        off = self.segments[idx] if 0 <= idx < len(self.segments) else 0
        c = self.center_x + off
        return int(c - self.width//2), int(c + self.width//2)

    def draw(self, screen):
        water_off = int((pygame.time.get_ticks()//10 - self.total_scroll*0.6) % self.wh)
        for ty in range(-self.wh, self.vh+self.wh, self.wh):
            for tx in range(0, self.vw, self.ww):
                screen.blit(self.water, (tx, ty+water_off))

        BROWN = (101, 67, 33)
        for i in range(len(self.segments)-1):
            y1 = i*self.segment_h - self.scroll_off
            y2 = (i+1)*self.segment_h - self.scroll_off
            if y2 < -50 or y1 > self.vh+50: continue
            c1 = self.center_x + self.segments[i]
            c2 = self.center_x + self.segments[i+1]
            l1, l2 = c1 - self.width//2, c2 - self.width//2
            r1, r2 = c1 + self.width//2, c2 + self.width//2

            if l1 > 0:
                rect = pygame.Rect(0, int(y1), int(l1), max(1,int(y2-y1)))
                screen.set_clip(rect)
                grass_off = int(-self.total_scroll) % self.gh
                for gy in range(-self.gh, self.vh+self.gh, self.gh):
                    for gx in range(0, int(l1)+self.gw, self.gw):
                        screen.blit(self.grass, (gx, gy+grass_off))
                screen.set_clip(None)
                pygame.draw.line(screen, BROWN, (l1, y1), (l2, y2), 2)

            if r1 < self.vw:
                rect = pygame.Rect(int(r1), int(y1), self.vw-int(r1), max(1,int(y2-y1)))
                screen.set_clip(rect)
                grass_off = int(-self.total_scroll) % self.gh
                for gy in range(-self.gh, self.vh+self.gh, self.gh):
                    for gx in range(int(r1)-self.gw, self.vw+self.gw, self.gw):
                        screen.blit(self.grass, (gx, gy+grass_off))
                screen.set_clip(None)
                pygame.draw.line(screen, BROWN, (r1, y1), (r2, y2), 2)

    def hits_bank(self, rect):
        y = rect.centery
        left, right = self.bounds_at(y)
        return rect.left < left or rect.right > right
