#!/usr/bin/env python3
"""News in one image: Wednesday 18 November 2026.

Draws a 1024x1024 newspaper-style infographic of the day's world news
with pure-Python stdlib only (no PIL, no fonts on disk: a built-in 5x7
bitmap font), and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Deterministic: the same bytes on every run. No network.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette (newsprint) ---
PAPER = (247, 243, 234)
INK = (22, 28, 38)
NAVY = (16, 34, 60)
NAVY2 = (28, 52, 86)
GOLD = (198, 158, 40)
RED = (172, 32, 32)
TEAL = (14, 110, 110)
BLUE = (30, 90, 160)
GREEN = (34, 110, 60)
ORANGE = (196, 96, 20)
PURPLE = (96, 60, 140)
BROWN = (122, 74, 30)
WHITE = (255, 255, 255)
GREY = (110, 110, 104)
LIGHT = (232, 226, 212)
CARD = (255, 255, 255)

# --- 5x7 bitmap font ('#' = ink). Uppercase + digits + punctuation only;
# all text is upper-cased before drawing. ---
FONT = {
    'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    'D': ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    'G': (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'I': (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    'J': ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    'N': ("#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"),
    'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    'X': ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    '0': (" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "),
    '1': ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    '2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    '3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    '4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    '5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    '6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    '7': ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    '8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    '9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    ' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    '.': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ',': ("     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "),
    ':': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ';': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    '-': ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     ", "     ", "     "),
    '(': ("   ##", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   ##"),
    ')': ("##   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", "##   "),
    '/': ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    '%': ("##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"),
    '&': (" ##  ", "#  # ", "#  # ", " #   ", "# # #", "#  # ", " ## #"),
    '+': ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    '!': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    '?': (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    '$': ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    '"': (" # # ", " # # ", "     ", "     ", "     ", "     ", "     "),
    '=': ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
    '*': ("     ", " # # ", " ### ", "#####", " ### ", " # # ", "     "),
    '_': ("     ", "     ", "     ", "     ", "     ", "     ", "#####"),
    '#': (" # # ", " # # ", "#####", " # # ", "#####", " # # ", " # # "),
}

# --- canvas ---------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, c, t=2):
        for ox in range(-(t // 2), t // 2 + 1):
            for oy in range(-(t // 2), t // 2 + 1):
                self.line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, c)

    def circle(self, cx, cy, r, c, filled=True):
        if filled:
            for yy in range(-r, r + 1):
                dx = int((r * r - yy * yy) ** 0.5)
                for xx in range(-dx, dx + 1):
                    self.set(cx + xx, cy + yy, c)
        else:
            x, y, d = 0, r, 3 - 2 * r
            while x <= y:
                for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                               (x, -y), (y, -x), (-x, -y), (-y, -x)):
                    self.set(cx + sx, cy + sy, c)
                if d < 0:
                    d += 4 * x + 6
                else:
                    d += 4 * (x - y) + 10
                    y -= 1
                x += 1

    def poly(self, pts, c):
        # filled polygon, scanline fill
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)


# --- text -----------------------------------------------------------------
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, s, x, y, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == '#':
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, c)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, s, cx, y, scale, c):
    draw_text(cv, s, cx - text_w(s, scale) // 2, y, scale, c)


def wrap(s, max_w, scale):
    """Word-wrap upper-cased text to lines fitting max_w pixels."""
    words, lines, cur = s.upper().split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- PNG writer (stdlib only) ---------------------------------------------
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# --- pictograms (drawn white on the story's accent tile, 54x54) ------------
def drone_at(cv, x, y, s):
    c = WHITE
    cv.fill_rect(x + 22 * s, y + 24 * s, 10 * s, 8 * s, c)
    for ex, ey in ((8, 10), (46, 10), (8, 46), (46, 46)):
        cv.line(x + 27 * s, y + 28 * s, x + ex * s, y + ey * s, c)
        cv.hline(x + ex * s - 5 * s, y + ey * s, 11 * s, c)
    cv.circle(x + 47 * s, y + 6 * s, 8 * s, c, filled=False)
    cv.circle(x + 47 * s, y + 6 * s, 13 * s, c, filled=False)


def icon_drone(cv, x, y):
    drone_at(cv, x, y, 1)


def icon_bridge(cv, x, y):
    c = WHITE
    cv.circle(x + 27, y + 38, 16, c, filled=False)
    cv.hline(x + 6, y + 38, 42, c, 3)
    cv.line(x + 12, y + 38, x + 12, y + 48, c)
    cv.line(x + 42, y + 38, x + 42, y + 48, c)
    cv.hline(x + 4, y + 50, 46, c)


def icon_plane(cv, x, y):
    c = WHITE
    cv.poly([(x + 6, y + 24), (x + 40, y + 24), (x + 50, y + 28),
             (x + 40, y + 32), (x + 6, y + 32)], c)
    cv.poly([(x + 22, y + 24), (x + 32, y + 8), (x + 38, y + 8),
             (x + 30, y + 24)], c)
    cv.poly([(x + 10, y + 24), (x + 16, y + 10), (x + 20, y + 24)], c)


def icon_globe(cv, x, y):
    c = WHITE
    cv.circle(x + 27, y + 27, 20, c, filled=False)
    cv.circle(x + 27, y + 27, 10, c, filled=False)
    cv.line(x + 27, y + 7, x + 27, y + 47, c)
    cv.line(x + 7, y + 27, x + 47, y + 27, c)


def icon_chip(cv, x, y):
    c = WHITE
    cv.rect(x + 14, y + 14, 26, 26, c, 3)
    cv.fill_rect(x + 22, y + 22, 10, 10, c)
    for i in range(3):
        px = x + 18 + i * 9
        cv.line(px, y + 6, px, y + 14, c)
        cv.line(px, y + 40, px, y + 48, c)
        cv.line(x + 6, y + 18 + i * 9, x + 14, y + 18 + i * 9, c)
        cv.line(x + 40, y + 18 + i * 9, x + 48, y + 18 + i * 9, c)


def icon_scales(cv, x, y):
    c = WHITE
    cv.line(x + 27, y + 10, x + 27, y + 44, c)
    cv.line(x + 12, y + 12, x + 42, y + 12, c)
    for px in (12, 42):
        cv.line(x + px, y + 12, x + px - 6, y + 26, c)
        cv.line(x + px, y + 12, x + px + 6, y + 26, c)
        cv.circle(x + px, y + 29, 5, c, filled=False)
    cv.hline(x + 19, y + 44, 16, c, 2)


def icon_cyclone(cv, x, y):
    c = WHITE
    for r in (6, 12, 18):
        cv.circle(x + 27, y + 27, r, c, filled=False)
    cv.circle(x + 27, y + 27, 3, c, filled=True)


def icon_cricket(cv, x, y):
    c = WHITE
    cv.thick_line(x + 36, y + 6, x + 22, y + 38, c, 5)
    cv.thick_line(x + 38, y + 4, x + 36, y + 10, c, 3)
    cv.circle(x + 14, y + 42, 6, c, filled=True)
    cv.line(x + 10, y + 40, x + 18, y + 44, INK)


def icon_building(cv, x, y):
    c = WHITE
    cv.poly([(x + 8, y + 20), (x + 27, y + 8), (x + 46, y + 20)], c)
    cv.fill_rect(x + 10, y + 22, 34, 4, c)
    for px in (14, 24, 34):
        cv.fill_rect(x + px, y + 26, 5, 16, c)
    cv.fill_rect(x + 8, y + 42, 38, 4, c)


ICONS = {
    'drone': icon_drone, 'bridge': icon_bridge, 'plane': icon_plane,
    'globe': icon_globe, 'chip': icon_chip, 'scales': icon_scales,
    'cyclone': icon_cyclone, 'cricket': icon_cricket,
    'building': icon_building,
}

# --- the day's news (verified from wire reports, 18 Nov 2026) -------------
# (accent, kicker, headline, body, icon)
STORIES = [
    (RED, "UKRAINE", "KYIV HITS CRIMEA BRIDGE AGAIN",
     "Ukraine strikes the bridge to Crimea for a second straight day, "
     "as Russia pounds bridges in Kyiv.", 'bridge'),
    (BLUE, "MANILA", "TRUMP LANDS IN MANILA",
     "The US president arrives in the Philippines for Quad talks, "
     "ahead of a visit to China.", 'plane'),
    (TEAL, "APEC - TRADE", "XI MEETS CARNEY IN SHENZHEN",
     "Canada and China extend trade deals as Xi meets Carney, with "
     "APEC leaders' week opening in Shenzhen.", 'globe'),
    (GREEN, "TECH", "NVIDIA SALES JUMP 103%",
     "Revenue jumps 103% year on year, but ousted chief Jensen Huang "
     "will not return as CEO.", 'chip'),
    (PURPLE, "BRITAIN", "UK SANCTIONS SETTLERS",
     "Britain sanctions Israeli settlement firms in a push to protect "
     "the two-state solution.", 'scales'),
    (ORANGE, "WEATHER", "CYCLONE AKVAN STRENGTHENS",
     "The storm over the Bay of Bengal is set to turn severe, "
     "with India on alert.", 'cyclone'),
    (BROWN, "SPORT", "DHONI CALLS TIME ON IPL",
     "MS Dhoni retires as a player and becomes Chennai Super Kings "
     "mentor.", 'cricket'),
    (NAVY2, "ISRAEL", "KNESSET ELECTS NEW SPEAKER",
     "Matan Kahana, an ally of Gadi Eisenkot, is elected speaker "
     "in a blow to Netanyahu.", 'building'),
]

LEAD_BODY = ("Bahrain sounds the all-clear after a new threat alert, and "
             "Kuwait's air defences fight off drone attacks, as the US and "
             "Iran trade strikes over Qeshm and Bahrain.")
LEAD_STRIP = ("US STRUCK A MISSILE SITE ON QESHM AFTER IRAN HIT A US RADAR "
              "IN BAHRAIN")
BRIEF = ("ALSO TODAY: US LOSES MEASLES-FREE STATUS - INDIA RE-ELECTED TO THE "
         "ITU COUNCIL - POPE LEO HIT BY A ROSARY THROWN FROM A CROWD IN PERU")


def draw_card(cv, x, y, w, h, accent, kicker, headline, body, icon):
    cv.fill_rect(x, y, w, h, CARD)
    cv.rect(x, y, w, h, NAVY, 1)
    cv.fill_rect(x, y, w, 5, accent)
    cv.fill_rect(x + 12, y + 14, 54, 54, accent)
    ICONS[icon](cv, x + 12, y + 14)
    draw_text(cv, kicker, x + 78, y + 16, 2, accent)
    lines = wrap(headline, w - 78 - 12, 3)
    ly = y + 36
    for ln in lines[:2]:
        draw_text(cv, ln, x + 78, ly, 3, INK)
        ly += 22
    blines = wrap(body, w - 24, 2)
    by = y + 88
    for ln in blines[:3]:
        draw_text(cv, ln, x + 12, by, 2, INK)
        by += 17


def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.fill_rect(0, 0, W, 120, NAVY)
    cv.hline(0, 120, W, GOLD, 4)
    draw_text_centered(cv, "THE WORLD IN ONE DAY", W // 2, 16, 5, WHITE)
    draw_text_centered(cv, "WEDNESDAY - 18 NOVEMBER 2026", W // 2, 72, 3, GOLD)
    # lead story
    lx, ly, lw, lh = 16, 132, 992, 200
    cv.fill_rect(lx, ly, lw, lh, CARD)
    cv.rect(lx, ly, lw, lh, NAVY, 1)
    cv.fill_rect(lx, ly, 8, lh, RED)
    draw_text(cv, "GULF - LEAD STORY", lx + 28, ly + 16, 2, RED)
    draw_text(cv, "IRAN-US DRONE WAR WIDENS", lx + 28, ly + 42, 4, INK)
    blines = wrap(LEAD_BODY, 800, 2)
    by = ly + 92
    for ln in blines[:3]:
        draw_text(cv, ln, lx + 28, by, 2, INK)
        by += 17
    cv.fill_rect(lx + 830, ly + 28, 134, 110, NAVY)
    drone_at(cv, lx + 838, ly + 42, 2)
    cv.hline(lx + 28, ly + 158, lw - 56, LIGHT, 2)
    draw_text(cv, LEAD_STRIP, lx + 28, ly + 170, 2, GREY)
    # grid of 7 stories
    gx, gy = 16, 344
    cw, ch, gap = 491, 148, 10
    for i, (accent, kicker, headline, body, icon) in enumerate(STORIES):
        cx = gx + (i % 2) * (cw + gap)
        cy = gy + (i // 2) * (ch + gap)
        draw_card(cv, cx, cy, cw, ch, accent, kicker, headline, body, icon)
    # footer: also today
    flines = wrap(BRIEF, W - 32, 2)
    fy = 976
    for ln in flines[:2]:
        draw_text(cv, ln, 16, fy, 2, INK)
        fy += 17
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path}: {cv.w}x{cv.h}, {size} bytes")


if __name__ == "__main__":
    main()
