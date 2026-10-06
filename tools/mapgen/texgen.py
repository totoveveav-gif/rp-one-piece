"""Generateurs de textures procedurales (tuilables) - style colore One Piece."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
             "/usr/share/fonts/truetype/wqy", "/usr/share/fonts/truetype/freefont"]


def font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Bruits tuilables
# ---------------------------------------------------------------------------

def fbm(n, seed, beta=2.0, lo=1.0, hi=None, aniso=(1.0, 1.0), m=None):
    """Bruit fractal periodique (filtrage spectral), normalise 0..1."""
    m = m or n
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((m, n))
    F = np.fft.fft2(w)
    ky = np.fft.fftfreq(m) * m * aniso[1]
    kx = np.fft.fftfreq(n) * n * aniso[0]
    K = np.sqrt(ky[:, None] ** 2 + kx[None, :] ** 2)
    K[0, 0] = 1.0
    filt = 1.0 / K ** (beta / 2)
    filt[K < lo] = 0
    if hi:
        filt[K > hi] = 0
    r = np.real(np.fft.ifft2(F * filt))
    r -= r.min()
    r /= max(r.max(), 1e-9)
    return r


def col(c):
    return np.array(c, float) / (255.0 if max(c) > 1.5 else 1.0)


def mix(a, b, t):
    t = np.asarray(t)[..., None]
    return a * (1 - t) + b * t


def to_img(a):
    a = np.clip(a, 0, 1)
    return (a * 255 + 0.5).astype(np.uint8)


def tone(base, n, amt):
    return np.clip(base * (1 + (n[..., None] - 0.5) * amt), 0, 1)


# ---------------------------------------------------------------------------
# Terrains
# ---------------------------------------------------------------------------

def t_grass(seed=1, c1=(78, 158, 52), c2=(122, 190, 64)):
    n = 512
    a = fbm(n, seed, 2.2, lo=2)
    b = fbm(n, seed + 1, 1.2, lo=40)
    img = mix(col(c1), col(c2), a)
    img = tone(img, b, 0.35)
    rng = np.random.default_rng(seed)
    # petites fleurs
    for _ in range(60):
        x, y = rng.integers(0, n, 2)
        c = [(250, 240, 120), (255, 255, 255), (255, 170, 200)][rng.integers(0, 3)]
        img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = col(c)
    return img


def t_sand(seed=2, c1=(236, 216, 160), c2=(222, 196, 136)):
    n = 512
    a = fbm(n, seed, 2.0, lo=2)
    g = fbm(n, seed + 5, 0.5, lo=100)
    img = mix(col(c1), col(c2), a)
    return tone(img, g, 0.18)


def t_seafloor(seed=3):
    n = 512
    a = fbm(n, seed, 2.0, lo=2)
    yy, xx = np.mgrid[0:n, 0:n]
    rip = 0.5 + 0.5 * np.sin((xx + yy * 0.3) / n * 2 * np.pi * 12 + a * 8)
    img = mix(col((214, 198, 150)), col((186, 170, 124)), a * 0.6 + rip * 0.4)
    return tone(img, fbm(n, seed + 2, 0.6, lo=90), 0.15)


def t_desert(seed=4):
    n = 512
    a = fbm(n, seed, 2.3, lo=2)
    yy, xx = np.mgrid[0:n, 0:n]
    rip = 0.5 + 0.5 * np.sin((yy + a * 60) / n * 2 * np.pi * 9)
    img = mix(col((238, 196, 122)), col((216, 160, 92)), a * 0.7 + rip * 0.3)
    return tone(img, fbm(n, seed + 3, 0.5, lo=100), 0.15)


def t_snow(seed=5):
    n = 512
    a = fbm(n, seed, 2.4, lo=2)
    img = mix(col((246, 250, 255)), col((206, 222, 244)), a ** 1.5)
    return tone(img, fbm(n, seed + 1, 0.5, lo=120), 0.06)


def t_rock(seed=6, c1=(150, 138, 122), c2=(104, 96, 88)):
    n = 512
    a = fbm(n, seed, 2.0, lo=2)
    r = np.abs(fbm(n, seed + 1, 2.2, lo=3) - 0.5) * 2
    cracks = np.clip(1 - r * 9, 0, 1)
    strata = 0.5 + 0.5 * np.sin(np.mgrid[0:n, 0:n][0] / n * 2 * np.pi * 10 + a * 6)
    img = mix(col(c1), col(c2), a * 0.7 + strata * 0.3)
    img = img * (1 - cracks[..., None] * 0.45)
    return tone(img, fbm(n, seed + 2, 0.6, lo=80), 0.2)


def t_dirt(seed=7):
    n = 512
    a = fbm(n, seed, 2.0, lo=2)
    img = mix(col((150, 112, 72)), col((122, 88, 56)), a)
    return tone(img, fbm(n, seed + 1, 0.5, lo=90), 0.25)


# ---------------------------------------------------------------------------
# Bois
# ---------------------------------------------------------------------------

def t_planks(seed=10, c=(170, 118, 70), rows=8, gap=(60, 38, 22), vary=0.18, vertical=False):
    n = 512
    rng = np.random.default_rng(seed)
    grain = fbm(n, seed, 2.0, lo=1, aniso=(0.08, 1.0))
    fine = fbm(n, seed + 1, 1.0, lo=30, aniso=(0.1, 1.0))
    img = np.zeros((n, n, 3))
    rh = n // rows
    base = col(c)
    for r in range(rows):
        y0 = r * rh
        cuts = sorted(rng.integers(0, n, 2))
        for seg in range(3):
            x0 = [0, cuts[0], cuts[1]][seg]
            x1 = [cuts[0], cuts[1], n][seg]
            k = 1 + rng.uniform(-vary, vary)
            img[y0:y0 + rh, x0:x1] = np.clip(base * k, 0, 1)
        img[y0:y0 + 3, :] = col(gap)
        for x in cuts:
            img[y0:y0 + rh, x:x + 3] = col(gap)
    img = img * (0.82 + 0.28 * grain[..., None]) * (0.92 + 0.12 * fine[..., None])
    img = np.clip(img, 0, 1)
    if vertical:
        img = np.transpose(img, (1, 0, 2))
    return img


def t_bark(seed=11, c1=(150, 116, 80), c2=(112, 84, 56), rings=16):
    n = 512
    a = fbm(n, seed, 2.0, lo=1, aniso=(0.15, 1.0))
    yy = np.mgrid[0:n, 0:n][0]
    ring = (np.sin(yy / n * 2 * np.pi * rings) > 0.6).astype(float)
    img = mix(col(c1), col(c2), a * 0.7 + ring * 0.3)
    return tone(img, fbm(n, seed + 1, 0.8, lo=50), 0.2)


def t_mangrove_bark(seed=12):
    n = 512
    a = fbm(n, seed, 2.0, lo=1, aniso=(1.0, 0.08))
    b = fbm(n, seed + 3, 1.0, lo=20, aniso=(1.0, 0.15))
    img = mix(col((196, 160, 112)), col((150, 116, 78)), a * 0.75 + b * 0.25)
    return img


def t_leaves(seed=13, c1=(64, 150, 52), c2=(28, 98, 40), hl=(140, 205, 90)):
    n = 512
    a = fbm(n, seed, 2.0, lo=3)
    b = fbm(n, seed + 1, 1.0, lo=24)
    blobs = np.clip((b - 0.45) * 4, 0, 1)
    img = mix(col(c2), col(c1), a)
    img = mix(img, col(hl), blobs * 0.55)
    return img


def t_palm_leaves(seed=14):
    n = 512
    yy, xx = np.mgrid[0:n, 0:n]
    stripes = 0.5 + 0.5 * np.sin(xx / n * 2 * np.pi * 24 + fbm(n, seed, 2.0, lo=2) * 4)
    img = mix(col((40, 120, 40)), col((110, 186, 70)), stripes)
    vein = np.exp(-((xx % 128 - 64) ** 2) / 30.0)
    img = mix(img, col((170, 210, 110)), vein * 0.6)
    return img


def t_sakura(seed=15):
    n = 512
    a = fbm(n, seed, 2.0, lo=3)
    b = fbm(n, seed + 1, 1.0, lo=30)
    img = mix(col((228, 132, 170)), col((252, 196, 216)), a)
    img = mix(img, col((255, 240, 246)), np.clip((b - 0.55) * 4, 0, 1))
    return img


def t_pine_snow(seed=16):
    n = 512
    a = fbm(n, seed, 2.0, lo=3)
    b = fbm(n, seed + 1, 1.8, lo=6)
    img = mix(col((24, 70, 44)), col((44, 104, 60)), a)
    return mix(img, col((240, 246, 255)), np.clip((b - 0.5) * 3.5, 0, 1))


# ---------------------------------------------------------------------------
# Maconnerie
# ---------------------------------------------------------------------------

def t_plaster(seed=20, c=(240, 236, 226), amt=0.08):
    n = 512
    a = fbm(n, seed, 2.2, lo=2)
    b = fbm(n, seed + 1, 0.6, lo=100)
    img = tone(np.ones((n, n, 3)) * col(c), a, amt)
    return tone(img, b, amt * 0.6)


def t_bricks(seed=21, c=(200, 196, 186), mortar=(150, 144, 134), rows=8, per=4, vary=0.1,
             bevel=True):
    n = 512
    rng = np.random.default_rng(seed)
    img = np.zeros((n, n, 3))
    rh = n // rows
    bw = n // per
    noise = fbm(n, seed, 2.0, lo=2)
    yy, xx = np.mgrid[0:n, 0:n]
    for r in range(rows):
        off = (bw // 2) * (r % 2)
        for b in range(per + 1):
            x0 = b * bw - off
            k = 1 + rng.uniform(-vary, vary)
            tint = col(c) * k
            xs = np.arange(x0, x0 + bw) % n
            img[r * rh:(r + 1) * rh][:, xs] = tint
            for xm in (x0 % n,):
                img[r * rh:(r + 1) * rh, xm:xm + 5] = col(mortar)
        img[r * rh:r * rh + 5, :] = col(mortar)
    img = img * (0.86 + 0.24 * noise[..., None])
    if bevel:
        ly = (yy % rh) / rh
        img = img * (1.05 - 0.15 * ly[..., None])
    return np.clip(img, 0, 1)


def t_cobble(seed=22, c1=(178, 170, 156), c2=(140, 132, 120), cells=70, n=512):
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, n, (cells, 2))
    tints = rng.uniform(0, 1, cells)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    idx = np.zeros((n, n), np.int32)
    for i, (px, py) in enumerate(pts):
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                d = np.hypot(xx - px - ox, yy - py - oy)
                closer = d < f1
                f2 = np.where(closer, f1, np.minimum(f2, d))
                idx = np.where(closer, i, idx)
                f1 = np.where(closer, d, f1)
    edge = np.clip((f2 - f1) / 7.0, 0, 1)
    img = mix(col(c1), col(c2), tints[idx])
    img = img * (0.55 + 0.45 * edge[..., None])
    img = img * (0.92 + 0.16 * fbm(n, seed, 2.0, lo=2)[..., None])
    return np.clip(img, 0, 1)


def t_roof(seed=23, c=(196, 70, 52), rows=16, per=8, scallop=True):
    n = 512
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n]
    rh = n // rows
    tw = n // per
    img = np.zeros((n, n, 3))
    base = col(c)
    for r in range(rows):
        off = (tw // 2) * (r % 2)
        for t in range(per + 1):
            x0 = t * tw - off
            k = 1 + rng.uniform(-0.12, 0.12)
            xs = np.arange(x0, x0 + tw) % n
            img[r * rh:(r + 1) * rh][:, xs] = base * k
    ly = (yy % rh) / rh
    lx = ((xx + (tw // 2) * ((yy // rh) % 2)) % tw) / tw
    shade = 0.65 + 0.45 * ly
    if scallop:
        curve = 0.18 * (1 - np.sin(lx * np.pi))
        shade = np.where(ly > 1 - curve, 0.55, shade)
    edge = np.minimum(lx, 1 - lx) < 0.03
    shade = np.where(edge, shade * 0.7, shade)
    img = img * shade[..., None]
    img = img * (0.9 + 0.2 * fbm(n, seed, 2.0, lo=2)[..., None])
    return np.clip(img, 0, 1)


def t_marble(seed=24, c1=(246, 246, 242), c2=(196, 200, 210)):
    n = 512
    a = fbm(n, seed, 2.2, lo=1)
    yy, xx = np.mgrid[0:n, 0:n]
    v = np.abs(np.sin((xx + yy) / n * 2 * np.pi * 2 + a * 9))
    veins = np.clip(1 - v * 6, 0, 1)
    img = mix(col(c1), col(c2), veins * 0.8 + a * 0.15)
    return img


def t_flat(c, seed=25, amt=0.06):
    n = 512
    return tone(np.ones((n, n, 3)) * col(c), fbm(n, seed, 2.0, lo=2), amt)


def t_gold(seed=26):
    n = 512
    a = fbm(n, seed, 2.0, lo=1)
    yy = np.mgrid[0:n, 0:n][0]
    s = 0.5 + 0.5 * np.sin(yy / n * 2 * np.pi * 3)
    return mix(col((200, 150, 40)), col((255, 222, 110)), a * 0.5 + s * 0.5)


def t_metal(seed=27, c=(84, 88, 96), plates=4):
    n = 512
    img = np.ones((n, n, 3)) * col(c)
    img = tone(img, fbm(n, seed, 2.0, lo=2), 0.25)
    yy, xx = np.mgrid[0:n, 0:n]
    p = n // plates
    lx, ly = xx % p, yy % p
    edge = (lx < 4) | (ly < 4)
    img[edge] *= 0.55
    hl = (lx >= 4) & (lx < 8) | (ly >= 4) & (ly < 8)
    img[hl] = np.clip(img[hl] * 1.25, 0, 1)
    for cx in (14, p - 14):
        for cy in (14, p - 14):
            d = np.hypot(lx - cx, ly - cy)
            img[d < 5] = img[d < 5] * 1.4
    return np.clip(img, 0, 1)


def t_bars(seed=28):
    n = 512
    rgba = np.zeros((n, n, 4))
    rgba[..., :3] = col((70, 72, 78))
    yy, xx = np.mgrid[0:n, 0:n]
    lx = xx % 64
    bar = (lx > 24) & (lx < 40)
    shade = 0.6 + 0.6 * np.sin((lx - 24) / 16 * np.pi)
    rgba[..., :3] *= np.clip(shade, 0.3, 1.2)[..., None]
    band = (yy % 256 > 230)
    alpha = (bar | band).astype(float)
    rgba[band, :3] = col((60, 62, 66))
    rgba[..., 3] = alpha
    return np.clip(rgba, 0, 1)


def t_fabric_stripes(c1, c2, seed=29, stripes=8):
    n = 512
    xx = np.mgrid[0:n, 0:n][1]
    s = ((xx // (n // stripes)) % 2).astype(float)
    img = mix(col(c1), col(c2), s)
    weave = 0.95 + 0.05 * np.sin(np.mgrid[0:n, 0:n][0] * 1.7) * np.sin(xx * 1.7)
    return img * weave[..., None]


def t_waterfall(seed=30):
    n = 512
    a = fbm(n, seed, 1.6, lo=2, aniso=(1.0, 0.06))
    b = fbm(n, seed + 1, 1.0, lo=20, aniso=(1.0, 0.1))
    img = mix(col((120, 190, 220)), col((245, 252, 255)), np.clip(a * 0.7 + b * 0.5, 0, 1))
    return img


def t_portal(seed=31):
    n = 512
    yy, xx = np.mgrid[0:n, 0:n] - n / 2
    r = np.hypot(xx, yy) / (n / 2)
    th = np.arctan2(yy, xx)
    sw = 0.5 + 0.5 * np.sin(th * 5 + r * 14)
    glow = np.clip(1 - r, 0, 1)
    c = mix(col((10, 60, 120)), col((120, 240, 255)), sw * glow)
    c = c * np.clip(glow * 1.6, 0, 1)[..., None]
    c = mix(c, col((255, 255, 255)), np.clip(1 - r * 5, 0, 1))
    return np.clip(c, 0, 1)


def t_jp_wall(seed=32, fh=160):
    n = 512
    img = t_plaster(seed, (244, 238, 222), 0.05)
    wood = col((66, 40, 28))
    img[:, :26] = wood
    img[:, -26:] = wood
    img[:24, :] = wood
    img[-30:, :] = wood
    img[230:248, :] = wood
    # fenetre shoji
    x0, x1, y0, y1 = 150, 362, 70, 210
    img[y0:y1, x0:x1] = col((250, 244, 220))
    for x in range(x0, x1 + 1, 53):
        img[y0:y1, x:x + 6] = wood
    for y in range(y0, y1 + 1, 35):
        img[y:y + 6, x0:x1 + 6] = wood
    return np.clip(img * (0.94 + 0.08 * fbm(n, seed, 2.0, lo=2)[..., None]), 0, 1)


def t_windows(wall, seed=40, frame=(250, 250, 246), shutter=None, glass=(80, 140, 200),
              arch=False, slit=False, plain_base=False):
    """Facade : une fenetre par tuile (128 unites x 1 etage)."""
    n = 512
    img = t_plaster(seed, wall, 0.07)
    # bandeau d'etage
    img[-22:, :] = np.clip(col(wall) * 0.82, 0, 1)
    img[-26:-22, :] = np.clip(col(wall) * 1.08, 0, 1)
    if slit:
        x0, x1, y0, y1 = 236, 276, 110, 340
    else:
        x0, x1, y0, y1 = 160, 352, 102, 358
    yy, xx = np.mgrid[0:n, 0:n]
    win = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    if arch:
        cx, r = (x0 + x1) / 2, (x1 - x0) / 2
        top = y0 + r
        win &= ~((yy < top) & (np.hypot(xx - cx, yy - top) > r))
    fr = np.zeros_like(win)
    for d in range(14):
        fr |= np.roll(win, d, 0) | np.roll(win, -d, 0) | np.roll(win, d, 1) | np.roll(win, -d, 1)
    fr &= ~win
    img[fr] = col(frame)
    g = (yy - y0) / max(1, (y1 - y0))
    gl = mix(col(glass) * 1.25, col(glass) * 0.6, np.clip(g, 0, 1))
    streak = np.abs(((xx - yy * 0.6) % 160) - 40) < 12
    gl = np.where(streak[..., None], np.clip(gl * 1.35, 0, 1), gl)
    img[win] = gl[win]
    if not slit:
        mx = (x0 + x1) // 2
        img[y0:y1, mx - 5:mx + 5][win[y0:y1, mx - 5:mx + 5]] = col(frame)
        my = y0 + (y1 - y0) // 3
        img[my - 5:my + 5, x0:x1][win[my - 5:my + 5, x0:x1]] = col(frame)
        # appui
        img[y1 + 10:y1 + 26, x0 - 22:x1 + 22] = np.clip(col(frame) * 0.9, 0, 1)
    if shutter is not None:
        sh = col(shutter)
        for sx0 in (x0 - 14 - 80, x1 + 14):
            img[y0:y1, sx0:sx0 + 80] = sh
            for y in range(y0, y1, 18):
                img[y:y + 4, sx0:sx0 + 80] = sh * 0.7
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------------------
# Textures "ajustees" (panneaux, drapeaux, voiles, portes)
# ---------------------------------------------------------------------------

def pil_to_arr(im):
    a = np.asarray(im.convert("RGBA"), float) / 255.0
    return a


def wood_board(w, h, seed=50, c=(150, 98, 54)):
    base = t_planks(seed, c, rows=4)
    im = Image.fromarray(to_img(base)).resize((w, h))
    return im


def sign(text, w=1024, h=256, seed=51, color=(255, 236, 170), board=(140, 90, 48),
         font_name="DejaVuSerif-Bold.ttf", sub=None, border=(70, 40, 20)):
    im = wood_board(w, h, seed, board)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=border, width=max(4, h // 24))
    m = max(6, h // 18)
    d.rectangle([m, m, w - m - 1, h - m - 1], outline=(220, 180, 110), width=max(2, h // 80))
    size = int(h * (0.52 if sub else 0.62))
    f = font(font_name, size)
    while d.textlength(text, font=f) > w * 0.9 and size > 10:
        size -= 4
        f = font(font_name, size)
    tw = d.textlength(text, font=f)
    ty = h * (0.10 if sub else 0.16)
    d.text(((w - tw) / 2 + 4, ty + 4), text, font=f, fill=(40, 22, 10))
    d.text(((w - tw) / 2, ty), text, font=f, fill=color)
    if sub:
        fs = font("DejaVuSans-Bold.ttf", int(h * 0.2))
        sw = d.textlength(sub, font=fs)
        d.text(((w - sw) / 2, h * 0.70), sub, font=fs, fill=(250, 250, 240))
    return im


def flag_strawhat(w=512, h=512):
    im = Image.new("RGB", (w, h), (18, 18, 20))
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, int(h * 0.52)
    # os croises
    for sgn in (-1, 1):
        d.line([(cx - 170, cy + 150 * sgn * -1 + 40), (cx + 170, cy - 150 * sgn * -1 + 40)],
               fill=(245, 245, 240), width=34)
        for ex, ey in ((cx - 170, cy + 150 * sgn * -1 + 40), (cx + 170, cy - 150 * sgn * -1 + 40)):
            d.ellipse([ex - 26, ey - 26, ex + 26, ey + 26], fill=(245, 245, 240))
    # crane
    d.ellipse([cx - 110, cy - 130, cx + 110, cy + 80], fill=(245, 245, 240))
    d.rectangle([cx - 60, cy + 40, cx + 60, cy + 110], fill=(245, 245, 240))
    d.ellipse([cx - 70, cy - 50, cx - 18, cy + 10], fill=(18, 18, 20))
    d.ellipse([cx + 18, cy - 50, cx + 70, cy + 10], fill=(18, 18, 20))
    d.polygon([(cx, cy + 15), (cx - 14, cy + 40), (cx + 14, cy + 40)], fill=(18, 18, 20))
    for x in range(cx - 48, cx + 49, 24):
        d.line([(x, cy + 62), (x, cy + 110)], fill=(18, 18, 20), width=5)
    # chapeau de paille
    d.ellipse([cx - 175, cy - 150, cx + 175, cy - 85], fill=(236, 196, 70))
    d.chord([cx - 112, cy - 230, cx + 112, cy - 40], 180, 360, fill=(236, 196, 70))
    d.rectangle([cx - 112, cy - 150, cx + 112, cy - 120], fill=(200, 30, 36))
    return im


def flag_marine(w=512, h=512, bg=(250, 250, 250), fg=(30, 90, 190)):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, int(h * 0.38)
    # mouette stylisee
    d.arc([cx - 170, cy - 60, cx + 10, cy + 110], 200, 330, fill=fg, width=26)
    d.arc([cx - 10, cy - 60, cx + 170, cy + 110], 210, 340, fill=fg, width=26)
    d.ellipse([cx - 22, cy - 6, cx + 22, cy + 40], fill=fg)
    f = font("DejaVuSans-Bold.ttf", 92)
    t = "MARINE"
    tw = d.textlength(t, font=f)
    d.text(((w - tw) / 2, h * 0.62), t, font=f, fill=fg)
    return im


def kanji(text, w=1024, h=512, bg=(250, 250, 248), fg=(20, 20, 24), border=None):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    size = int(h * 0.78)
    f = font("wqy-zenhei.ttc", size)
    while d.textlength(text, font=f) > w * 0.9:
        size -= 8
        f = font("wqy-zenhei.ttc", size)
    tw = d.textlength(text, font=f)
    d.text(((w - tw) / 2, (h - size) / 2 - size * 0.04), text, font=f, fill=fg)
    if border:
        d.rectangle([0, 0, w - 1, h - 1], outline=border, width=24)
    return im


def sail(w=512, h=512, emblem=None, c=(246, 240, 224)):
    base = t_plaster(55, c, 0.05)
    im = Image.fromarray(to_img(base)).resize((w, h))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 64):
        d.line([(x, 0), (x, h)], fill=(220, 210, 190), width=3)
    if emblem == "marine":
        em = flag_marine(380, 380, bg=c)
        em = em.convert("RGBA")
        im.paste(em, ((w - 380) // 2, (h - 380) // 2))
    elif emblem == "strawhat":
        em = flag_strawhat(512, 512).resize((340, 340))
        im.paste(em, ((w - 340) // 2, (h - 340) // 2))
    elif emblem == "stripes":
        for x in range(0, w, 128):
            d.rectangle([x, 0, x + 64, h], fill=(214, 60, 60))
    return im


def door(w=256, h=512, c=(120, 72, 40), double=False):
    base = t_planks(60, c, rows=8, vertical=True)
    im = Image.fromarray(to_img(base)).resize((w, h))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(60, 34, 18), width=12)
    panels = [(0.15, 0.08, 0.85, 0.45), (0.15, 0.52, 0.85, 0.92)]
    if double:
        panels = [(0.08, 0.08, 0.44, 0.92), (0.56, 0.08, 0.92, 0.92)]
        d.line([(w // 2, 0), (w // 2, h)], fill=(60, 34, 18), width=8)
    for x0, y0, x1, y1 in panels:
        d.rectangle([x0 * w, y0 * h, x1 * w, y1 * h], outline=(80, 48, 26), width=8)
    hx = w * (0.48 if double else 0.82)
    d.ellipse([hx - 12, h * 0.5 - 12, hx + 12, h * 0.5 + 12], fill=(220, 180, 70))
    if double:
        d.ellipse([w * 0.52 - 12, h * 0.5 - 12, w * 0.52 + 12, h * 0.5 + 12], fill=(220, 180, 70))
    return im


def clock_face(w=512, h=512):
    im = Image.new("RGB", (w, h), (236, 210, 160))
    d = ImageDraw.Draw(im)
    cx, cy, r = w / 2, h / 2, w * 0.44
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=(170, 120, 50))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 246, 232))
    f = font("DejaVuSerif-Bold.ttf", 40)
    for i in range(12):
        a = math.radians(i * 30 - 60)
        t = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"][i]
        x, y = cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8
        tw = d.textlength(t, font=f)
        d.text((x - tw / 2, y - 24), t, font=f, fill=(40, 30, 20))
    d.line([(cx, cy), (cx + r * 0.5 * math.cos(math.radians(-60)), cy + r * 0.5 * math.sin(math.radians(-60)))],
           fill=(30, 20, 10), width=14)
    d.line([(cx, cy), (cx + r * 0.75 * math.cos(math.radians(-90)), cy + r * 0.75 * math.sin(math.radians(-90)))],
           fill=(30, 20, 10), width=9)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(30, 20, 10))
    return im


def grove(num, w=512, h=512):
    base = t_mangrove_bark(70 + num)
    im = Image.fromarray(to_img(base)).resize((w, h))
    d = ImageDraw.Draw(im)
    f = font("DejaVuSans-Bold.ttf", 260)
    t = str(num)
    tw = d.textlength(t, font=f)
    d.text(((w - tw) / 2 + 6, 96), t, font=f, fill=(90, 60, 40))
    d.text(((w - tw) / 2, 90), t, font=f, fill=(250, 250, 245))
    f2 = font("DejaVuSans-Bold.ttf", 54)
    t2 = "GROVE"
    tw2 = d.textlength(t2, font=f2)
    d.text(((w - tw2) / 2, 30), t2, font=f2, fill=(250, 250, 245))
    return im


def water_normal(n=512, seed=90):
    h = fbm(n, seed, 3.0, lo=2) * 0.6 + fbm(n, seed + 1, 2.0, lo=10) * 0.4
    gy, gx = np.gradient(h * 18.0)
    nx, ny, nz = -gx, -gy, np.ones_like(h)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    rgb = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
    return rgb


def world_map(markers, routes, w=1024, h=1024, extent=16384):
    """Carte du monde facon parchemin (pour le panneau de Sabaody et les joueurs)."""
    base = mix(col((236, 214, 168)), col((206, 176, 122)), fbm(w, 99, 2.0, lo=2))
    yy, xx = np.mgrid[0:h, 0:w]
    vign = np.clip(np.hypot(xx - w / 2, yy - h / 2) / (w * 0.75), 0, 1)
    base = base * (1 - 0.35 * vign[..., None] ** 2)
    im = Image.fromarray(to_img(base))
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (w / 2 + x / extent * w * 0.47, h / 2 - y / extent * h * 0.47)

    for (a, b) in routes:
        d.line([P(*a), P(*b)], fill=(150, 60, 40), width=3)
    f = font("DejaVuSerif-Bold.ttf", 30)
    for m in markers:
        if m["kind"] != "ile":
            continue
        poly = [P(x, y) for x, y in m["poly"]]
        d.polygon(poly, fill=(150, 170, 90), outline=(90, 70, 40))
        x, y = P(*m["pos"][:2])
        tw = d.textlength(m["name"], font=f)
        d.text((x - tw / 2 + 2, y - 15 + 2), m["name"], font=f, fill=(250, 240, 210))
        d.text((x - tw / 2, y - 15), m["name"], font=f, fill=(70, 34, 18))
    # rose des vents
    cx, cy = w - 110, h - 110
    for a, L in ((0, 80), (90, 80), (180, 80), (270, 80), (45, 45), (135, 45), (225, 45), (315, 45)):
        r = math.radians(a)
        d.polygon([(cx, cy), (cx + math.cos(r + 0.2) * 18, cy - math.sin(r + 0.2) * 18),
                   (cx + math.cos(r) * L, cy - math.sin(r) * L),
                   (cx + math.cos(r - 0.2) * 18, cy - math.sin(r - 0.2) * 18)], fill=(110, 50, 30))
    d.text((cx - 9, cy - 118), "N", font=font("DejaVuSerif-Bold.ttf", 28), fill=(110, 50, 30))
    ft = font("DejaVuSerif-Bold.ttf", 44)
    t = "GRAND LINE"
    d.text(((w - d.textlength(t, font=ft)) / 2, 18), t, font=ft, fill=(110, 50, 30))
    d.rectangle([4, 4, w - 5, h - 5], outline=(110, 70, 40), width=8)
    return im


def t_stairs(seed=80, c=(200, 196, 186), steps=8):
    n = 512
    base = t_bricks(seed, c, tuple(int(v * 0.75) for v in c), 8, 2, 0.05, False)
    yy = np.mgrid[0:n, 0:n][0]
    ly = (yy % (n // steps)) / (n // steps)
    shade = np.where(ly < 0.62, 1.05, 0.68)
    shade = np.where(ly < 0.05, 1.25, shade)
    return np.clip(base * shade[..., None], 0, 1)
