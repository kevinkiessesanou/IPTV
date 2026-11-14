import math, sys, os, random, subprocess, json, wave
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
ORANGE = (255, 145, 25); BLUE = (40, 75, 235); INK = (14, 22, 62); WHITE = (255, 255, 255)
LOGO_PATH = "/home/user/IPTV/video/logo_ntic.jpg"
FD = "/usr/share/fonts/opentype/inter/"
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else "."

# ------------------------------------------------------------------ utils
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease5(x): x = clamp(x); return 1 - (1 - x) ** 5
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def pop(x):
    x = clamp(x); c = 1.6
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

@lru_cache(None)
def font(sz, w="Bold"):
    return ImageFont.truetype(FD + "InterDisplay-%s.otf" % w, int(sz))

def tw(s, sz, w="Bold"): return font(sz, w).getlength(s)

def fade(sp, a):
    if a >= 0.999: return sp
    sp = sp.copy(); sp.putalpha(sp.getchannel("A").point(lambda v: int(v * a))); return sp

def smear(sp, k):
    k = int(k)
    if k < 2: return sp
    a = np.asarray(sp).astype(np.float32)
    pad = np.zeros((a.shape[0], k, 4), np.float32)
    a = np.concatenate([pad, a, pad], 1)
    a[..., :3] *= a[..., 3:4] / 255.0
    c = np.cumsum(a, 1); c = np.concatenate([np.zeros_like(c[:, :1]), c], 1)
    o = (c[:, k:] - c[:, :-k]) / k
    o[..., :3] = o[..., :3] / np.maximum(o[..., 3:4], 1e-3) * 255.0
    return Image.fromarray(np.clip(o, 0, 255).astype(np.uint8))

def blur_sp(sp, r):
    p = int(r * 2.5) + 1
    big = Image.new("RGBA", (sp.width + 2 * p, sp.height + 2 * p), (0, 0, 0, 0)); big.paste(sp, (p, p))
    return big.filter(ImageFilter.GaussianBlur(r))

def paste(img, sp, x, y, a=1.0, scale=1.0, sm=0, blur=0, anchor="c", rot=0):
    if sp is None or a <= 0.004 or scale <= 0.01: return
    if abs(scale - 1) > 0.002:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.2: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if blur > 0.6: sp = blur_sp(sp, blur)
    if sm >= 2: sp = smear(sp, sm)
    sp = fade(sp, a)
    if anchor == "c": x -= sp.width / 2; y -= sp.height / 2
    elif anchor == "l": y -= sp.height / 2
    elif anchor == "r": x -= sp.width; y -= sp.height / 2
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sp.width, W - x), min(sp.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0: return
    if (sx0, sy0, sx1, sy1) != (0, 0, sp.width, sp.height): sp = sp.crop((sx0, sy0, sx1, sy1))
    img.alpha_composite(sp, (x + sx0, y + sy0))

# ------------------------------------------------------------------ sprites
@lru_cache(4096)
def T(s, size, col=WHITE, w="Bold", track=0):
    f = font(size, w); asc, desc = f.getmetrics(); pad = int(size * .12) + 2
    width = int(sum(f.getlength(c) + track for c in s)) if track else int(f.getlength(s))
    im = Image.new("RGBA", (width + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if track:
        x = pad
        for c in s: d.text((x, pad), c, font=f, fill=col); x += f.getlength(c) + track
    else:
        d.text((pad, pad), s, font=f, fill=col)
    return im

def txt(img, s, size, x, y, col=WHITE, w="Bold", a=1.0, anchor="c", sm=0, scale=1.0, blur=0, track=0):
    sp = T(s, int(size), col, w, track)
    pad = int(int(size) * .12) + 2
    if anchor == "l": x -= pad * scale
    if anchor == "r": x += pad * scale
    paste(img, sp, x, y, a, scale, sm, blur, anchor)

def kin(img, s, size, x, y, t, t0, col=WHITE, w="ExtraBold", anchor="c", dist=260, d=0.5, out=None):
    """kinetic text: slides in from the right with motion blur; optional slide out to the left"""
    p = prog(t, t0, t0 + d)
    if p <= 0: return
    e = ease5(p); sm = 140 * (1 - p) ** 2.2
    dx = (1 - e) * dist; a = clamp(p * 3)
    if out is not None and t > out:
        q = prog(t, out, out + .35); dx -= (q ** 2) * dist * 3; sm = max(sm, 160 * math.sin(math.pi * min(q, .5)))
        a *= 1 - q
    txt(img, s, size, x + dx, y, col, w, a, anchor, sm)

@lru_cache(512)
def CARD(w, h, r=30, style="dark", glow=None):
    S = 2; pad = 70
    W2, H2 = (w + 2 * pad) * S, (h + 2 * pad) * S
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    shc = (0, 0, 8, 170) if style != "light" else (40, 55, 140, 55)
    ImageDraw.Draw(sh).rounded_rectangle([pad * S, (pad + 22) * S, (pad + w) * S, (pad + h + 22) * S], r * S, fill=shc)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26 * S)))
    if glow:
        g = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle([pad * S, pad * S, (pad + w) * S, (pad + h) * S], r * S, outline=glow + (230,), width=8 * S)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16 * S)))
    fills = {"dark": (13, 15, 24, 248), "light": (255, 255, 255, 252), "navy": (10, 20, 62, 240),
             "blue": (38, 72, 230, 255), "glass": (255, 255, 255, 40), "ink": (16, 22, 52, 252)}
    body = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); d = ImageDraw.Draw(body)
    box = [pad * S, pad * S, (pad + w) * S, (pad + h) * S]
    d.rounded_rectangle(box, r * S, fill=fills[style])
    im.alpha_composite(body)
    # sheen
    sheen = Image.new("RGBA", (W2, H2), (255, 255, 255, 0))
    gr = np.zeros((H2, W2), np.uint8)
    top, bot = pad * S, (pad + h) * S
    strength = 26 if style in ("dark", "navy", "ink") else (45 if style == "blue" else 0)
    if strength:
        col = np.clip(np.linspace(strength, 0, int((bot - top) * .55)), 0, 255).astype(np.uint8)
        gr[top:top + len(col), :] = col[:, None]
        mask = np.asarray(body.getchannel("A")) > 0
        sheen.putalpha(Image.fromarray(gr * mask))
        im.alpha_composite(sheen)
    bd = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    bc = {"light": (215, 222, 245, 255), "blue": (130, 160, 255, 160)}.get(style, (255, 255, 255, 48))
    ImageDraw.Draw(bd).rounded_rectangle(box, r * S, outline=bc, width=2 * S)
    im.alpha_composite(bd)
    return im.resize((W2 // S, H2 // S), Image.LANCZOS)

@lru_cache(512)
def PILL(s, size=28, style="dark", dot=None, strike=False, w="SemiBold"):
    S = 2; f = font(size * S, w)
    num = None
    if " · " in s: num, rest = s.split(" · ", 1)
    tx_w = f.getlength(s); h = int(size * 2.05 * S); padx = int(size * .95 * S)
    dw = int(size * .8 * S) if dot else 0
    pw = int(tx_w + 2 * padx + dw); pad = 40 * S
    im = Image.new("RGBA", (pw + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    bgc, fg = {"dark": ((20, 22, 34, 245), WHITE), "light": ((255, 255, 255, 255), INK),
               "glass": ((14, 26, 80, 230), WHITE), "soft": ((228, 234, 255, 255), INK),
               "orange": (ORANGE + (255,), INK), "blue": ((40, 75, 235, 255), WHITE)}[style]
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 10 * S, pad + pw, pad + h + 10 * S], h / 2,
                                         fill=(0, 0, 20, 110) if style in ("dark", "glass") else (40, 60, 160, 50))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14 * S)))
    if style == "glass":
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + pw, pad + h], h / 2, outline=(110, 150, 255, 255), width=6 * S)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12 * S)))
    d = ImageDraw.Draw(im)
    oc = (255, 255, 255, 60) if style in ("dark", "glass") else (210, 218, 245, 255)
    d.rounded_rectangle([pad, pad, pad + pw, pad + h], h / 2, fill=bgc, outline=oc, width=2 * S)
    x = pad + padx
    if dot:
        r = size * .22 * S
        d.ellipse([x - r * .3, pad + h / 2 - r, x + r * 1.7, pad + h / 2 + r], fill=dot)
        x += dw
    if num:
        d.text((x, pad + h / 2), num + " · ", font=f, fill=ORANGE, anchor="lm")
        d.text((x + f.getlength(num + " · "), pad + h / 2), rest, font=f, fill=fg, anchor="lm")
    else:
        d.text((x, pad + h / 2), s, font=f, fill=fg, anchor="lm")
    if strike:
        d.line([x - 4 * S, pad + h / 2 + 2 * S, x + tx_w + 4 * S, pad + h / 2 + 2 * S], fill=fg, width=3 * S)
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)

@lru_cache(64)
def ORB(r, hue="blue"):
    r = int(r); s = int(r * 3.2); c = s / 2
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    nx, ny = (x - c) / r, (y - c) / r; d = np.sqrt(nx ** 2 + ny ** 2)
    base = {"blue": np.array([70, 95, 245]), "orange": np.array([255, 140, 30]), "white": np.array([200, 205, 225]),
            "violet": np.array([150, 140, 255])}[hue]
    light = np.clip(1 - ((nx + .35) ** 2 + (ny + .42) ** 2) * .9, 0, 1)
    col = base * (.35 + .75 * light[..., None]) + 255 * (np.clip(light - .55, 0, 1) ** 1.5)[..., None] * 2.2
    rim = np.clip((d - .78) / .22, 0, 1) ** 2
    col = col + rim[..., None] * np.array([170, 190, 255]) * .55
    inside = np.clip((1 - d) * r, 0, 1)
    glow = np.exp(-((np.maximum(d - 1, 0)) * 2.4) ** 2) * (d > .98) * .55
    alpha = np.maximum(inside, glow)
    col = np.where((inside > 0)[..., None], col, base * 1.2)
    out = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

@lru_cache(None)
def LOGO(sz):
    L = Image.open(LOGO_PATH).convert("RGBA")
    m = Image.new("L", L.size, 0); ImageDraw.Draw(m).ellipse([10, 10, L.size[0] - 10, L.size[1] - 10], fill=255)
    L.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
    return L.resize((int(sz), int(sz)), Image.LANCZOS)

@lru_cache(None)
def CURSOR():
    S = 3; im = Image.new("RGBA", (40 * S, 50 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(4, 2), (4, 36), (13, 28), (19, 42), (25, 39), (19, 26), (31, 26)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=WHITE, outline=(0, 0, 0), width=2 * S)
    return im.resize((40, 50), Image.LANCZOS)

def underline(img, x0, y, length, k, col=WHITE, width=6, dot=True):
    if k <= 0: return
    L = length * k
    lay = Image.new("RGBA", (int(length) + 40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([0, 20 - width / 2, L, 20 + width / 2], width / 2, fill=col + (255,))
    paste(img, lay, x0, y, anchor="l")
    if dot: paste(img, ORB(11, "white" if col == WHITE else "orange"), x0 + L, y)

def wave_bars(img, cx, cy, w, h, t, n=60, col=(255, 255, 255), a=1.0, amp=1.0, gap=None):
    lay = Image.new("RGBA", (int(w) + 10, int(h) + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    step = w / n; bw = max(2, step * .45)
    for i in range(n):
        u = i / (n - 1) - .5
        env = math.exp(-(u * 3.2) ** 2)
        v = abs(math.sin(i * .9 + t * 7) * .6 + math.sin(i * .37 - t * 4.3) * .4)
        hh = max(3, h * (.06 + .94 * env * v * amp))
        x = 5 + i * step
        d.rounded_rectangle([x, 5 + h / 2 - hh / 2, x + bw, 5 + h / 2 + hh / 2], bw / 2, fill=col + (int(255 * a),))
    paste(img, lay, cx, cy)

def toggle(img, x, y, on, a=1.0, oncol=BLUE):
    S = 2; w, h = 92, 50
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bg = tuple(int(lerp(c0, c1, on)) for c0, c1 in zip((215, 220, 235), oncol))
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], h * S / 2, fill=bg + (255,))
    kx = lerp(5, w - h + 5, on) * S
    d.ellipse([kx, 5 * S, kx + (h - 10) * S, (h - 5) * S], fill=WHITE)
    paste(img, im.resize((w, h), Image.LANCZOS), x, y, a)

# ------------------------------------------------------------------ icons
def ICON(kind, s, t=0.0, col=(240, 243, 255), acc=ORANGE):
    lay = Image.new("RGBA", (int(s * 1.6), int(s * 1.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = cy = s * .8; h = s / 2; lw = max(3, int(s / 20)); wc = col + (255,); bc = acc + (255,)
    if kind == "web":
        d.rounded_rectangle([cx - h, cy - h * .7, cx + h, cy + h * .7], 10, outline=wc, width=lw)
        d.line([cx - h, cy - h * .38, cx + h, cy - h * .38], fill=wc, width=lw)
        for i in range(3): d.ellipse([cx - h + 12 + i * 16, cy - h * .58, cx - h + 21 + i * 16, cy - h * .49], fill=bc)
        d.text((cx, cy + h * .17), "</>", font=font(int(s * .32)), fill=bc, anchor="mm")
    elif kind == "ai":
        d.rounded_rectangle([cx - h * .55, cy - h * .55, cx + h * .55, cy + h * .55], 12, outline=wc, width=lw)
        for i in range(3):
            o = (i - 1) * h * .3
            for seg in [(cx + o, cy - h * .55, cx + o, cy - h * .85), (cx + o, cy + h * .55, cx + o, cy + h * .85),
                        (cx - h * .55, cy + o, cx - h * .85, cy + o), (cx + h * .55, cy + o, cx + h * .85, cy + o)]:
                d.line(seg, fill=wc, width=lw)
        r = h * (.2 + .05 * math.sin(t * 5)); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bc)
    elif kind == "secu":
        d.polygon([(cx, cy - h), (cx + h * .8, cy - h * .6), (cx + h * .7, cy + h * .3), (cx, cy + h), (cx - h * .7, cy + h * .3), (cx - h * .8, cy - h * .6)], outline=wc, width=lw)
        d.line([(cx - h * .32, cy), (cx - h * .05, cy + h * .28), (cx + h * .38, cy - h * .3)], fill=bc, width=lw * 2)
    elif kind == "mkt":
        d.polygon([(cx - h * .7, cy - h * .25), (cx - h * .1, cy - h * .25), (cx + h * .6, cy - h * .75), (cx + h * .6, cy + h * .75), (cx - h * .1, cy + h * .25), (cx - h * .7, cy + h * .25)], outline=wc, width=lw)
        d.line([cx - h * .45, cy + h * .25, cx - h * .3, cy + h * .8], fill=wc, width=lw)
        for i in range(2): d.arc([cx + h * .3 - i * 10, cy - h * .5 - i * 10, cx + h * 1.0 + i * 10, cy + h * .5 + i * 10], -40, 40, fill=bc, width=lw)
    elif kind == "design":
        d.line([cx - h * .7, cy + h * .7, cx + h * .5, cy - h * .5], fill=wc, width=lw * 3)
        d.polygon([(cx - h * .85, cy + h * .85), (cx - h * .75, cy + h * .5), (cx - h * .5, cy + h * .75)], fill=bc)
        d.line([cx + h * .35, cy - h * .65, cx + h * .65, cy - h * .35], fill=bc, width=lw * 3)
    elif kind == "form":
        d.polygon([(cx - h, cy - h * .3), (cx, cy - h * .75), (cx + h, cy - h * .3), (cx, cy + h * .15)], outline=wc, width=lw)
        d.arc([cx - h * .6, cy - h * .3, cx + h * .6, cy + h * .7], 0, 180, fill=wc, width=lw)
        d.line([cx + h * .8, cy - h * .35, cx + h * .8, cy + h * .4], fill=bc, width=lw)
        d.ellipse([cx + h * .68, cy + h * .35, cx + h * .92, cy + h * .58], fill=bc)
    elif kind == "heart":
        d.ellipse([cx - h, cy - h * .7, cx, cy + h * .2], fill=bc); d.ellipse([cx, cy - h * .7, cx + h, cy + h * .2], fill=bc)
        d.polygon([(cx - h * .95, cy - h * .1), (cx + h * .95, cy - h * .1), (cx, cy + h * .9)], fill=bc)
    elif kind == "send":
        d.polygon([(cx - h * .7, cy - h * .6), (cx + h * .8, cy), (cx - h * .7, cy + h * .6), (cx - h * .4, cy)], fill=wc)
    elif kind == "check":
        d.line([(cx - h * .5, cy), (cx - h * .1, cy + h * .4), (cx + h * .55, cy - h * .4)], fill=wc, width=lw * 2)
    return lay

def icon_tile(img, kind, x, y, s, t, a=1.0, scale=1.0, style="blue"):
    paste(img, CARD(int(s), int(s), int(s * .26), style), x, y, a, scale)
    paste(img, ICON(kind, s * .5, t, acc=ORANGE if style != "orange" else INK), x, y, a, scale)

# ------------------------------------------------------------------ backgrounds
def _swirl(tint, seed):
    bw, bh = int(W * 1.18), int(H * 1.18)
    rnd = random.Random(seed)
    v = np.full((bh, bw), .02, np.float32)
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    for i in range(30):
        cx = rnd.uniform(-.15, 1.15) * bw; cy = rnd.uniform(-.15, 1.15) * bh; r = rnd.uniform(.28, .6) * bh
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        v = np.where(d < 1, .02 + .42 * d ** 6, v)
    img = Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))
    v = np.asarray(img).astype(np.float32) / 255
    vig = np.clip(1.25 - np.sqrt(((xx - bw / 2) / bw) ** 2 + ((yy - bh / 2) / bh) ** 2) * 1.5, .3, 1)
    rgb = v[..., None] * np.array(tint, np.float32)[None, None] * vig[..., None]
    return Image.fromarray(np.clip(rgb + np.array([4, 5, 12]), 0, 255).astype(np.uint8)).convert("RGBA")

def _blue():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    k = np.clip(1 - r * 1.25, 0, 1)[..., None] ** 1.2
    a, b = np.array([14, 26, 120]), np.array([48, 88, 245])
    return Image.fromarray((a + (b - a) * k).astype(np.uint8)).convert("RGBA")

def _light():
    bw, bh = int(W * 1.18), int(H * 1.18)
    im = Image.new("RGB", (bw, bh), (238, 240, 250)); d = ImageDraw.Draw(im)
    rnd = random.Random(11)
    for i in range(9):
        cx, cy, r = rnd.uniform(0, bw), rnd.uniform(0, bh), rnd.uniform(200, 420)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rnd.choice([(212, 220, 252), (248, 249, 255), (225, 228, 250)]))
    return im.filter(ImageFilter.GaussianBlur(120)).convert("RGBA")

def _navy():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    k = np.clip(1 - r * 1.6, 0, 1)[..., None]
    base = np.array([6, 12, 42]) + np.array([20, 38, 120]) * k
    grid = ((xx % 64 < 1.5) | (yy % 64 < 1.5))[..., None] * 14 * (0.4 + k)
    return Image.fromarray(np.clip(base + grid, 0, 255).astype(np.uint8)).convert("RGBA")

BG = {}
def init_bg():
    if BG: return
    BG["swirl"] = _swirl((205, 210, 228), 5)
    BG["bswirl"] = _swirl((80, 115, 255), 8)
    BG["blue"] = _blue(); BG["light"] = _light(); BG["navy"] = _navy()

def bg(kind, t):
    init_bg(); src = BG[kind]
    if src.width == W: im = src.copy()
    else:
        ox = (src.width - W) / 2 + math.sin(t * .35) * (src.width - W) * .45
        oy = (src.height - H) / 2 + math.cos(t * .28) * (src.height - H) * .4
        im = src.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))
    if kind == "blue":
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        rnd = random.Random(3)
        for i in range(9):
            y = rnd.uniform(.1, .9) * H; L = rnd.uniform(300, 900); sp = rnd.uniform(120, 420)
            x = (rnd.uniform(0, W + L) + t * sp) % (W + L) - L
            d.rounded_rectangle([x, y, x + L, y + rnd.choice([2, 3, 4])], 2, fill=(150, 180, 255, rnd.randint(35, 80)))
        im.alpha_composite(lay)
    return im

def corner(img, dark=True):
    paste(img, LOGO(66), W - 70, H - 64, .95)

# ------------------------------------------------------------------ devices
@lru_cache(8)
def PHONE_BODY(w, h):
    S = 2; pad = 60
    im = Image.new("RGBA", ((w + 2 * pad) * S, (h + 2 * pad) * S), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad * S, (pad + 30) * S, (pad + w) * S, (pad + h + 30) * S], 90 * S, fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30 * S)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad * S, pad * S, (pad + w) * S, (pad + h) * S], 90 * S, fill=(120, 124, 135))
    d.rounded_rectangle([(pad + 4) * S, (pad + 4) * S, (pad + w - 4) * S, (pad + h - 4) * S], 86 * S, fill=(30, 31, 36))
    d.rounded_rectangle([(pad + 16) * S, (pad + 16) * S, (pad + w - 16) * S, (pad + h - 16) * S], 74 * S, fill=(8, 8, 12))
    d.rounded_rectangle([(pad + w / 2 - 70) * S, (pad + 36) * S, (pad + w / 2 + 70) * S, (pad + 76) * S], 20 * S, fill=(0, 0, 0))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)

@lru_cache(8)
def LAPTOP_BODY(w, h):
    S = 2; pad = 60; bh = 34
    im = Image.new("RGBA", ((int(w * 1.2) + 2 * pad) * S, (h + bh + 2 * pad) * S), (0, 0, 0, 0))
    ox = (im.width / S - w) / 2
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([(ox - 40) * S, (pad + h) * S, (ox + w + 40) * S, (pad + h + bh + 25) * S], 20 * S, fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24 * S)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([ox * S, pad * S, (ox + w) * S, (pad + h) * S], 26 * S, fill=(26, 27, 32), outline=(90, 92, 100), width=3 * S)
    bx0, bx1 = ox - w * .09, ox + w * 1.09
    d.rounded_rectangle([bx0 * S, (pad + h - 4) * S, bx1 * S, (pad + h + 14) * S], 6 * S, fill=(150, 152, 160))
    d.rounded_rectangle([(bx0 + 12) * S, (pad + h + 10) * S, (bx1 - 12) * S, (pad + h + 24) * S], 8 * S, fill=(70, 72, 80))
    d.rounded_rectangle([(ox + w / 2 - 70) * S, (pad + h - 4) * S, (ox + w / 2 + 70) * S, (pad + h + 4) * S], 3 * S, fill=(100, 102, 110))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS), (int(ox + 16), int(pad + 16))

def ui_screen(w, h, t, theme="blue", t0=0.0):
    """Builds an animated website/app UI on a screen."""
    bgc = (38, 72, 232) if theme == "blue" else (10, 11, 16)
    im = Image.new("RGBA", (w, h), bgc + (255,))
    d = ImageDraw.Draw(im)
    s = w / 900
    def ap(k): return ease(prog(t, t0 + k * .22, t0 + k * .22 + .4))
    a = ap(0)
    if a > 0:
        d.ellipse([30 * s, 28 * s, 48 * s, 46 * s], fill=ORANGE + (int(255 * a),))
        for i, L in enumerate([70, 50, 60]):
            x = w - 300 * s + i * 95 * s
            d.rounded_rectangle([x, 33 * s, x + L * s, 41 * s], 4, fill=(255, 255, 255, int(170 * a)))
    a = ap(1)
    if a > 0:
        paste(im, T("NTIC Solution", int(64 * s), WHITE, "ExtraBold"), 50 * s - 6 + (1 - a) * 40, 150 * s, a, anchor="l")
    a = ap(2)
    for i in range(2):
        L = [380, 300][i] * s * a
        d.rounded_rectangle([56 * s, (215 + i * 26) * s, 56 * s + L, (229 + i * 26) * s], 7, fill=(255, 255, 255, 120))
    a = ap(3)
    if a > 0:
        bw = 210 * s * pop(prog(t, t0 + .66, t0 + 1.1))
        d.rounded_rectangle([56 * s, 300 * s, 56 * s + bw, 360 * s], 30 * s, fill=(255, 255, 255, int(255 * a)))
        d.rounded_rectangle([290 * s, 300 * s, 290 * s + 150 * s * a, 360 * s], 30 * s, outline=(255, 255, 255, int(200 * a)), width=max(2, int(3 * s)))
    a = ap(4)
    if a > 0:
        paste(im, ORB(int(70 * s * pop(prog(t, t0 + .88, t0 + 1.4))), "white"), w - 230 * s, 200 * s + math.sin(t * 2) * 8 * s, a)
        paste(im, CARD(int(120 * s), int(120 * s), int(28 * s), "glass"), w - 120 * s, 330 * s + math.cos(t * 2) * 8 * s, a)
    a = ap(5)
    if a > 0:
        for i in range(3):
            x = 56 * s + i * 270 * s
            d.rounded_rectangle([x, 420 * s, x + 245 * s, 420 * s + (h / s - 450) * s * a], 22 * s, fill=(255, 255, 255, 40))
    return im

def phone(img, x, y, t, scale=1.0, a=1.0, rot=0, theme="blue", t0=0.0, content=None):
    pw, ph = 470, 960
    body = PHONE_BODY(pw, ph).copy()
    sw, sh = pw - 40, ph - 40
    scr = content(sw, sh, t) if content else ui_phone(sw, sh, t, theme, t0)
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], 72, fill=255)
    scr.putalpha(m)
    body.alpha_composite(scr, (60 + 20, 60 + 20))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([60 + pw / 2 - 70, 60 + 36, 60 + pw / 2 + 70, 60 + 76], 20, fill=(0, 0, 0))
    paste(img, body, x, y, a, scale, rot=rot)

def ui_phone(w, h, t, theme="blue", t0=0.0):
    bgc = (38, 72, 232) if theme == "blue" else (12, 12, 18)
    im = Image.new("RGBA", (w, h), bgc + (255,)); d = ImageDraw.Draw(im)
    d.text((50, 30), "9:41", font=font(26, "SemiBold"), fill=WHITE)
    def ap(k): return ease(prog(t, t0 + k * .2, t0 + k * .2 + .4))
    a = ap(0); paste(im, LOGO(110), w / 2, 210, a, pop(prog(t, t0, t0 + .5)))
    a = ap(1); paste(im, T("NTIC Solution", 46, WHITE, "ExtraBold"), w / 2 + (1 - a) * 30, 320, a)
    a = ap(2)
    if a > 0:
        paste(im, T("L'Univers du Digital", 26, ORANGE, "SemiBold"), w / 2, 370, a)
    for i in range(3):
        a = ap(3 + i)
        if a > 0:
            y = 450 + i * 120
            paste(im, CARD(w - 80, 96, 26, "glass"), w / 2 + (1 - a) * 60, y, a)
            paste(im, ORB(20, ["orange", "white", "violet"][i]), 80 + (1 - a) * 60, y, a)
            d.rounded_rectangle([120, y - 12, 120 + (200 - i * 30) * a, y - 2], 5, fill=(255, 255, 255, int(200 * a)))
            d.rounded_rectangle([120, y + 8, 120 + 130 * a, y + 16], 4, fill=(255, 255, 255, int(110 * a)))
    a = ap(6)
    if a > 0: d.rounded_rectangle([w / 2 - 100, h - 120, w / 2 + 100, h - 60], 30, fill=(255, 255, 255, int(255 * a)))
    return im

def laptop(img, x, y, t, scale=1.0, a=1.0, theme="blue", t0=0.0, content=None):
    lw, lh = 1000, 620
    body, (sx, sy) = LAPTOP_BODY(lw, lh)
    body = body.copy()
    scr = content(lw - 32, lh - 32, t) if content else ui_screen(lw - 32, lh - 32, t, theme, t0)
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], 14, fill=255)
    scr.putalpha(m)
    body.alpha_composite(scr, (sx, sy))
    paste(img, body, x, y, a, scale)

# ------------------------------------------------------------------ scenes
# each scene: (fn, duration, bg, transition_in)

def sc_phone(t, D):
    img = bg("swirl", t)
    k = ease5(prog(t, 0, 1.6))
    sc = lerp(1.25, .95, k); rot = lerp(16, -4, k)
    push = eio(prog(t, D - .7, D))
    sc *= 1 + push ** 2 * 2.2
    phone(img, W / 2 + lerp(520, 0, k) - push * 80, H / 2 + lerp(380, 70, k) + push * 120, t, sc, min(1, k * 2.5), rot * (1 - push), "dark", .5)
    return img

def sc_type(t, D):
    img = bg("swirl", t)
    k = ease5(prog(t, 0, .6))
    cw, ch = 1040, 330
    paste(img, CARD(cw, ch, 36, "dark"), W / 2, H / 2 - 70 + (1 - k) * 80, k, lerp(.9, 1, k))
    lines = ["Votre entreprise", "mérite d'être vue."]
    full = "\n".join(lines); n = int(len(full) * prog(t, .45, .45 + len(full) * .045))
    shown = full[:n].split("\n")
    x0 = W / 2 - cw / 2 + 70
    for i, l in enumerate(shown):
        txt(img, l, 82, x0, H / 2 - 150 + i * 100, WHITE, "ExtraBold", k, "l")
    if n < len(full) or int(t * 2.5) % 2 == 0:
        li = len(shown) - 1
        cx = x0 + tw(shown[li], 82, "ExtraBold") + 12
        paste(img, Image.new("RGBA", (7, 84), ORANGE + (255,)), cx, H / 2 - 150 + li * 100, k)
    # underline on "vue."
    if n >= len(full):
        lx = x0 + tw("mérite d'être ", 82, "ExtraBold")
        underline(img, lx, H / 2 - 50 + 52, tw("vue.", 82, "ExtraBold"), ease(prog(t, 2.3, 2.8)), ORANGE, 7, False)
    # pills: struck then active
    pills = [("Hasard", 2.3, 3.0), ("Improvisation", 2.5, 3.3), ("Stratégie", 2.7, None)]
    ws = [PILL(p, 28, "dark", dot=WHITE).width - 80 for p, _, _ in pills]
    x = W / 2 - (sum(ws) + 24 * 2) / 2
    for i, (p, ta, tstrike) in enumerate(pills):
        a = ease(prog(t, ta, ta + .35))
        strike = tstrike is not None and t > tstrike
        active = tstrike is None and t > 3.5
        style = "light" if active else "dark"
        sp = PILL(p, 28, style, dot=ORANGE if active else (150, 150, 165), strike=strike)
        sc = pop(prog(t, 3.5, 3.85)) if active else 1
        paste(img, sp, x + ws[i] / 2, H / 2 + 175 + (1 - a) * 30, a * (0.45 if strike else 1), sc)
        x += ws[i] + 24
    return img

def sc_laptop(t, D):
    img = bg("bswirl", t)
    k = ease5(prog(t, 0, .9))
    laptop(img, W / 2 + 40, H / 2 + 60 + (1 - k) * 200, t, lerp(1.25, 1.0, k), k, "blue", .5)
    # chip "digital"
    a = pop(prog(t, 1.3, 1.75))
    if a > 0:
        paste(img, PILL("digital", 54, "ink", w="ExtraBold") if False else PILL("digital", 54, "dark", w="ExtraBold"), 520, 215, clamp(a), a)
    # side orb card
    a = ease(prog(t, 2.0, 2.6))
    if a > 0:
        paste(img, CARD(260, 260, 40, "blue"), 1500 + (1 - a) * 120, 470 + math.sin(t * 1.8) * 10, a)
        paste(img, ORB(70, "white"), 1500 + (1 - a) * 120, 450 + math.sin(t * 1.8) * 10, a)
    a = ease(prog(t, 2.4, 2.9))
    if a > 0:
        paste(img, PILL("100 % sur mesure", 34, "dark", dot=ORANGE), 420, 880, a, pop(prog(t, 2.4, 2.9)))
    return img

def sc_kin1(t, D):
    img = bg("blue", t)
    kin(img, "Et vous êtes", 150, W / 2, H / 2 - 30, t, .1, out=1.7)
    underline(img, W / 2 - 300, H / 2 + 90, 600, ease(prog(t, .4, 1.4)) * (1 - prog(t, 1.7, 1.9)), WHITE, 5)
    kin(img, "au bon endroit.", 150, W / 2, H / 2 - 30, t, 1.85)
    if t > 2.2:
        L = tw("au bon endroit.", 150, "ExtraBold")
        underline(img, W / 2 - L / 2, H / 2 + 90, L, ease(prog(t, 2.3, 3.0)), WHITE, 5)
    return img

def sc_light_head(t, D):
    img = bg("light", t)
    kin(img, "Tout le digital,", 140, W / 2, H / 2 - 95, t, .1, INK)
    s1, s2 = "une seule ", "équipe."
    L = tw(s1 + s2, 140, "ExtraBold"); x0 = W / 2 - L / 2
    kin(img, s1, 140, x0, H / 2 + 70, t, .5, INK, anchor="l")
    kin(img, s2, 140, x0 + tw(s1, 140, "ExtraBold"), H / 2 + 70, t, .62, BLUE, anchor="l")
    underline(img, x0 + tw(s1, 140, "ExtraBold"), H / 2 + 165, tw(s2, 140, "ExtraBold") - 30, ease(prog(t, 1.2, 1.9)), ORANGE, 8)
    return img

def sc_section(t, D):
    img = bg("navy", t)
    wave_bars(img, W / 2, H / 2, W * 1.05, 260, t, 110, (120, 150, 255), .35, .9)
    a = pop(prog(t, .2, .7)); b = ease(prog(t, .2, .5))
    paste(img, PILL("6 · Services", 64, "glass", w="ExtraBold"), W / 2, H / 2, b, max(a, .01), blur=(1 - b) * 10)
    for i, (x, y, kind) in enumerate([(240, 200, "o"), (1680, 200, "c"), (260, 860, "w"), (1660, 870, "o2")]):
        e = ease(prog(t, .5 + i * .12, 1 + i * .12)); fy = math.sin(t * 1.5 + i) * 10
        if kind == "o": paste(img, ORB(46, "violet"), x, y + fy, e)
        elif kind == "o2": paste(img, ORB(30, "orange"), x, y + fy, e)
        elif kind == "c": paste(img, CARD(110, 110, 28, "blue"), x, y + fy, e)
        else:
            paste(img, CARD(190, 110, 24, "ink"), x, y + fy, e)
            wave_bars(img, x, y + fy, 140, 50, t, 16, WHITE, e, .8)
    return img

def svc_title(img, t, label, dark, y=120):
    a = pop(prog(t, .15, .6)); b = ease(prog(t, .15, .4))
    paste(img, PILL(label, 46, "glass" if dark else "light", w="ExtraBold"), W / 2, y, b, max(a, .01))

def tags(img, t, items, y, t0, dark=True, x=None):
    ws = [PILL(p, 28, "dark" if dark else "light", dot=ORANGE).width - 80 for p in items]
    x = (W / 2 - (sum(ws) + 22 * (len(ws) - 1)) / 2) if x is None else x
    for i, p in enumerate(items):
        a = ease(prog(t, t0 + i * .18, t0 + i * .18 + .35))
        paste(img, PILL(p, 28, "dark" if dark else "light", dot=ORANGE), x + ws[i] / 2, y + (1 - a) * 30, a, pop(prog(t, t0 + i * .18, t0 + i * .18 + .4)))
        x += ws[i] + 22

def sc_web(t, D):
    img = bg("light", t)
    svc_title(img, t, "01 · Développement web et mobile", False)
    k = ease5(prog(t, .2, 1.1))
    laptop(img, W / 2 - 120 - (1 - k) * 300, H / 2 + 40, t, .92, k, "blue", .6)
    k2 = ease5(prog(t, 1.6, 2.4))
    if k2 > 0:
        phone(img, W / 2 + 520 + (1 - k2) * 400, H / 2 + 90, t, .52, k2, lerp(10, 0, k2), "blue", 1.9)
    a = pop(prog(t, 2.6, 3.0))
    if a > 0: paste(img, PILL("Responsive", 30, "light", dot=BLUE), W / 2 + 560, 260, clamp(a), a)
    tags(img, t, ["Sites vitrines", "Boutiques en ligne", "Applications web & Android"], 960, 2.7, dark=False)
    return img

def chat_screen(w, h, t):
    im = Image.new("RGBA", (w, h), (10, 14, 34, 255)); d = ImageDraw.Draw(im)
    return im

def sc_ai(t, D):
    img = bg("navy", t)
    wave_bars(img, W / 2, H / 2 + 40, W * 1.05, 200, t, 110, (110, 140, 255), .18, .8)
    svc_title(img, t, "02 · Intelligence artificielle", True)
    k = ease5(prog(t, .3, 1.0))
    cw, ch = 980, 600; cx, cy = W / 2, H / 2 + 70
    paste(img, CARD(cw, ch, 40, "ink", glow=(70, 110, 255)), cx, cy + (1 - k) * 80, k)
    if k > .1:
        top = cy - ch / 2 + (1 - k) * 80
        paste(img, ORB(26, "orange"), cx - cw / 2 + 70, top + 60, k)
        txt(img, "Assistant NTIC", 32, cx - cw / 2 + 110, top + 60, WHITE, "Bold", k, "l")
        txt(img, "● en ligne", 22, cx - cw / 2 + 110, top + 96, (120, 220, 150), "SemiBold", k, "l")
        # user bubble
        a = ease(prog(t, 1.0, 1.4))
        if a > 0:
            s = "Vous faites aussi des applis Android ?"
            bw = tw(s, 30, "SemiBold") + 60
            paste(img, PILL(s, 30, "blue"), cx + cw / 2 - 40 - bw / 2, top + 210 + (1 - a) * 30, a)
        # typing dots
        if 1.6 < t < 2.4:
            for i in range(3):
                yy = top + 330 - abs(math.sin(t * 8 + i)) * 8
                paste(img, ORB(8, "white"), cx - cw / 2 + 90 + i * 30, yy, 1)
        if t >= 2.4:
            s = "Oui ! Et on automatise aussi vos contenus."
            n = int(len(s) * prog(t, 2.4, 3.6))
            bw = tw(s, 30, "SemiBold") + 60
            paste(img, CARD(int(bw), 74, 37, "dark"), cx - cw / 2 + 40 + bw / 2, top + 330, 1)
            txt(img, s[:n], 30, cx - cw / 2 + 70, top + 330, WHITE, "SemiBold", 1, "l")
        a = ease(prog(t, 3.4, 3.8))
        if a > 0:
            paste(img, CARD(cw - 80, 80, 40, "dark"), cx, top + ch - 80, a)
            txt(img, "Écrivez votre message…", 28, cx - cw / 2 + 80, top + ch - 80, (140, 145, 170), "SemiBold", a, "l")
            paste(img, ORB(26, "blue"), cx + cw / 2 - 90, top + ch - 80, a)
    paste(img, ICON("ai", 120, t), 250, 560 + math.sin(t * 1.5) * 12, ease(prog(t, .8, 1.3)))
    paste(img, ORB(40, "violet"), 1700, 420 + math.cos(t * 1.4) * 12, ease(prog(t, 1, 1.5)))
    tags(img, t, ["Chatbots", "Automatisation", "Création de contenus"], 1010, 3.0)
    return img

def sc_secu(t, D):
    img = bg("blue", t)
    svc_title(img, t, "03 · Cybersécurité", True)
    cx, cy = 640, H / 2 + 40
    # corner brackets closing in
    k = ease5(prog(t, .2, 1.0)); s = lerp(380, 250, k)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = cx + sx * s, cy + sy * s
            d.line([x0, y0, x0 - sx * 50, y0], fill=(255, 255, 255, int(230 * k)), width=5)
            d.line([x0, y0, x0, y0 - sy * 50], fill=(255, 255, 255, int(230 * k)), width=5)
    # rotating HUD rings
    for i, (r, span, sp) in enumerate([(200, 250, 40), (165, 120, -70), (230, 60, 25)]):
        a0 = t * sp + i * 70
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + span * ease(prog(t, .4 + i * .1, 1.2)), fill=(255, 255, 255, 200), width=4 if i != 2 else 2)
    for j in range(36):
        ang = math.radians(j * 10 + t * 15); r1, r2 = 245, 255 if j % 3 else 268
        d.line([cx + math.cos(ang) * r1, cy + math.sin(ang) * r1, cx + math.cos(ang) * r2, cy + math.sin(ang) * r2], fill=(255, 255, 255, int(120 * k)), width=2)
    img.alpha_composite(lay)
    # scan line
    sy = cy - 140 + ((t * .8) % 1) * 280
    paste(img, Image.new("RGBA", (300, 3), (255, 200, 120, int(200 * k))), cx, sy, k)
    icon_tile(img, "secu", cx, cy, 190, t, ease(prog(t, .5, 1)), pop(prog(t, .5, 1)), "ink")
    a = ease(prog(t, 1, 1.4))
    if a > 0 and int(t * 2) % 2 == 0: paste(img, PILL("SCAN", 24, "dark", dot=(255, 70, 70)), cx, cy - 330, a)
    # checklist card
    k2 = ease5(prog(t, 1.0, 1.7))
    px, py = 1330, H / 2 + 40
    paste(img, CARD(620, 400, 36, "light"), px + (1 - k2) * 200, py, k2)
    items = ["Audit de sécurité", "Sécurisation serveurs", "Supervision réseau"]
    for i, it in enumerate(items):
        y = py - 120 + i * 120; x0 = px - 260 + (1 - k2) * 200
        paste(img, PILL(str(i + 1), 22, "soft"), x0 + 10, y, k2)
        txt(img, it, 34, x0 + 50, y, INK, "Bold", k2, "l")
        on = ease(prog(t, 2.0 + i * .45, 2.25 + i * .45))
        toggle(img, px + 230 + (1 - k2) * 200, y, on, k2, ORANGE)
    return img

def sc_mkt(t, D):
    img = bg("light", t)
    svc_title(img, t, "04 · Marketing digital", False)
    # social post card
    k = ease5(prog(t, .3, 1.0))
    cx, cy = 620, H / 2 + 60
    paste(img, CARD(520, 640, 36, "light"), cx - (1 - k) * 200, cy, k)
    if k > .05:
        ox = cx - (1 - k) * 200
        paste(img, LOGO(64), ox - 190, cy - 255, k)
        txt(img, "NTIC Solution", 30, ox - 145, cy - 265, INK, "Bold", k, "l")
        txt(img, "Sponsorisé", 22, ox - 145, cy - 232, (120, 125, 150), "SemiBold", k, "l")
        paste(img, CARD(460, 330, 22, "blue"), ox, cy - 20, k)
        paste(img, ORB(60, "white"), ox + 110, cy - 50 + math.sin(t * 2) * 8, k)
        txt(img, "Boostez", 54, ox - 200, cy - 70, WHITE, "ExtraBold", k, "l")
        txt(img, "votre marque", 40, ox - 200, cy - 15, (255, 210, 160), "Bold", k, "l")
        hp = pop(prog(t, 1.6, 2.0))
        paste(img, ICON("heart", 50, t, acc=(240, 60, 90)), ox - 200, cy + 210, k, max(hp, .01) if t > 1.6 else .8)
        likes = int(1250 * ease(prog(t, 1.6, 3.6)))
        txt(img, "{:,}".format(likes).replace(",", " ") + " j'aime", 30, ox - 160, cy + 210, INK, "Bold", k, "l")
    # chart
    k2 = ease5(prog(t, 1.0, 1.6))
    gx, gy = 1340, H / 2 + 20
    paste(img, CARD(640, 420, 36, "light"), gx + (1 - k2) * 200, gy, k2)
    if k2 > .05:
        ox = gx + (1 - k2) * 200
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        p = ease(prog(t, 1.6, 3.4)); pts = []
        for i in range(int(60 * p) + 1):
            u = i / 60
            pts.append((ox - 260 + u * 520, gy + 120 - (u ** 1.8) * 230 - math.sin(u * 9) * 18))
        if len(pts) > 1:
            d.line(pts, fill=BLUE + (255,), width=7, joint="curve")
        img.alpha_composite(lay)
        if len(pts) > 1: paste(img, ORB(12, "orange"), pts[-1][0], pts[-1][1], 1)
        txt(img, "+%d" % int(250 * p), 74, ox - 260, gy - 130, INK, "ExtraBold", k2, "l")
        txt(img, "%", 36, ox - 260 + tw("+%d" % int(250 * p), 74, "ExtraBold") + 4, gy - 118, INK, "Bold", k2, "l")
        txt(img, "de visibilité", 28, ox + 60, gy - 125, (110, 115, 140), "SemiBold", k2, "l")
    tags(img, t, ["Community management", "Référencement", "Publicités sponsorisées"], 980, 2.6, dark=False, x=None)
    return img

def sc_design(t, D):
    img = bg("light", t)
    svc_title(img, t, "05 · Création graphique", False)
    # phase 1: big word with swatches
    sh = eio(prog(t, 2.2, 2.9))
    x = W / 2 - sh * 420
    kin(img, "Identité visuelle.", 110, x, H / 2 - 20, t, .3, INK)
    cols = [(10, 18, 60), BLUE, ORANGE, (225, 230, 250)]
    for i, c in enumerate(cols):
        a = pop(prog(t, 1.0 + i * .12, 1.4 + i * .12))
        sw = CARD(70, 70, 16, "light")
        sq = Image.new("RGBA", (70, 70), (0, 0, 0, 0)); ImageDraw.Draw(sq).rounded_rectangle([0, 0, 69, 69], 16, fill=c + (255,))
        paste(img, sq, x - 150 + i * 100, H / 2 + 110, clamp(a), max(a, .01))
    # phase 2: poster + flyer
    for j, (dx, dy, rot, st) in enumerate([(560, 40, -6, 2.6), (300, 80, 5, 2.9)]):
        a = ease5(prog(t, st, st + .6))
        if a <= 0: continue
        pw, ph = 330, 460
        card = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], 24, fill=(BLUE if j == 0 else (14, 20, 56)) + (255,))
        card.alpha_composite(ORB(70, "orange" if j == 0 else "violet").resize((180, 180)), (pw - 200, 30))
        d.text((28, 250), "PROMO" if j == 0 else "EVENT", font=font(54, "ExtraBold"), fill=WHITE)
        d.rounded_rectangle([28, 320, 230, 334], 7, fill=(255, 255, 255, 170))
        d.rounded_rectangle([28, 350, 180, 362], 6, fill=(255, 255, 255, 110))
        d.rounded_rectangle([28, 395, 160, 435], 20, fill=ORANGE + (255,))
        paste(img, CARD(pw, ph, 24, "light"), W / 2 + dx + (1 - a) * 300, H / 2 + dy, a * .6, rot=rot + (1 - a) * 12)
        paste(img, card, W / 2 + dx + (1 - a) * 300, H / 2 + dy, a, rot=rot + (1 - a) * 12)
    # pen cursor draws
    a = ease(prog(t, 3.2, 3.5))
    if a > 0:
        u = prog(t, 3.3, 4.2)
        paste(img, ICON("design", 80, t, col=INK), W / 2 + 820 - u * 120, H / 2 - 180 + math.sin(u * 6) * 30, a)
    tags(img, t, ["Identité visuelle", "Affiches & flyers", "Interfaces"], 980, 3.2, dark=False)
    return img

def sc_form(t, D):
    img = bg("bswirl", t)
    svc_title(img, t, "06 · Formations en informatique", True)
    k = ease5(prog(t, .3, 1.0))
    cw, ch = 860, 460; cx, cy = W / 2 + 180, H / 2 + 60
    paste(img, CARD(cw, ch, 36, "navy", glow=(80, 120, 255)), cx, cy + (1 - k) * 60, k)
    top = cy - ch / 2 + (1 - k) * 60; x0 = cx - cw / 2 + 60
    txt(img, "Programme", 30, x0, top + 60, (170, 180, 230), "SemiBold", k, "l")
    items = ["Bureautique", "Programmation web", "avec l'intelligence artificielle"]
    for i, s in enumerate(items):
        t0 = 1.0 + i * .8
        n = int(len(s) * prog(t, t0, t0 + len(s) * .03))
        if n <= 0: continue
        y = top + 140 + i * 80
        paste(img, ORB(10, "orange"), x0 + 10, y, 1)
        txt(img, s[:n], 46, x0 + 40, y, WHITE, "Bold", 1, "l")
    p = ease(prog(t, 1.0, 3.8))
    lay = Image.new("RGBA", (cw - 120, 14), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, cw - 121, 13], 7, fill=(255, 255, 255, 40))
    d.rounded_rectangle([0, 0, max(14, (cw - 121) * p), 13], 7, fill=ORANGE + (255,))
    paste(img, lay, x0, top + ch - 60, k, anchor="l")
    txt(img, "%d %%" % int(100 * p), 34, cx + cw / 2 - 60, top + ch - 105, WHITE, "ExtraBold", k, "r")
    icon_tile(img, "form", 420, H / 2 + 60 + math.sin(t * 1.5) * 12, 220, t, ease(prog(t, .5, 1.1)), pop(prog(t, .5, 1.1)), "blue")
    return img

PROJECTS = [("CAVOR", "web", BLUE), ("Menu QR", "mkt", (14, 20, 56)), ("KIBAA", "ai", ORANGE), ("Faso24.info", "web", (14, 20, 56)), ("MyVivo", "design", BLUE)]

def sc_stack(t, D):
    img = bg("light", t)
    txt(img, "NOS RÉALISATIONS", 28, 1000, 230, BLUE, "Bold", ease(prog(t, .1, .5)), "l", track=4)
    step = .75
    cur = min(len(PROJECTS) - 1, int(max(0, t - .3) / step))
    for i, (name, kind, col) in enumerate(PROJECTS):
        t0 = .3 + i * step
        a = ease5(prog(t, t0, t0 + .35))
        if a <= 0: continue
        y = 330 + i * 92
        txt(img, name, 76, 1030 + (1 - a) * 60, y, INK, "ExtraBold", a, "l", sm=(1 - a) * 80)
        if i == cur:
            paste(img, Image.new("RGBA", (8, 80), BLUE + (255,)), 1005, y, a)
    # visual on left changes with current project
    name, kind, col = PROJECTS[cur]
    t0 = .3 + cur * step; a = pop(prog(t, t0, t0 + .45))
    sq = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); ImageDraw.Draw(sq).rounded_rectangle([0, 0, 419, 419], 60, fill=col + (255,))
    paste(img, CARD(420, 420, 60, "light"), 600, H / 2 + 30, .7, max(a, .01))
    paste(img, sq, 600, H / 2 + 30, 1, max(a, .01))
    paste(img, ICON(kind, 190, t, col=WHITE, acc=WHITE if col == ORANGE else ORANGE), 600, H / 2 + 30, 1, max(a, .01))
    paste(img, CURSOR(), 760 + math.sin(t * 2) * 20, H / 2 + 200, ease(prog(t, .8, 1.2)))
    return img

def sc_kin2(t, D):
    img = bg("bswirl", t)
    zoom = lerp(1.15, 1.0, ease5(prog(t, 0, .9)))
    kin(img, "Si c'est digital,", 150, W / 2, H / 2 - 90, t, .1)
    s = "c'est NTIC."
    txt_a = ease(prog(t, .9, 1.4))
    if txt_a > 0:
        sp = T(s, 150, WHITE, "ExtraBold")
        g = blur_sp(T(s, 150, (120, 150, 255), "ExtraBold"), 18)
        paste(img, g, W / 2, H / 2 + 80, txt_a * .9, zoom)
        paste(img, sp, W / 2, H / 2 + 80, txt_a, lerp(1.3, 1, ease5(prog(t, .9, 1.5))), blur=(1 - txt_a) * 12)
        L = tw(s, 150, "ExtraBold")
        underline(img, W / 2 - L / 2 + 10, H / 2 + 175, L - 20, ease(prog(t, 1.6, 2.4)), ORANGE, 7)
    return img

def sc_contact(t, D):
    img = bg("light", t)
    kin(img, "Parlons de votre projet", 96, 140, 170, t, .1, INK, anchor="l")
    # message field like the reference
    k = ease5(prog(t, .5, 1.1))
    fx, fy = 560, 400
    txt(img, "Message", 26, 160, 315, (100, 105, 140), "SemiBold", k, "l")
    paste(img, CARD(820, 110, 55, "light"), fx, fy + (1 - k) * 40, k)
    msg = "Bonjour, j'ai un projet digital !"
    n = int(len(msg) * prog(t, 1.0, 2.4))
    txt(img, msg[:n], 34, 210, fy + (1 - k) * 40, INK, "SemiBold", k, "l")
    click = prog(t, 2.6, 2.8)
    bsc = 1 - .15 * math.sin(math.pi * click)
    paste(img, ORB(34, "blue"), fx + 340, fy, k, bsc)
    paste(img, ICON("send", 34, t), fx + 342, fy, k, bsc)
    cu = ease(prog(t, 1.8, 2.6))
    paste(img, CURSOR(), lerp(1100, fx + 352, cu), lerp(700, fy + 22, cu), ease(prog(t, 1.6, 1.9)) * (1 - prog(t, 3.2, 3.5)))
    sent = ease(prog(t, 2.8, 3.2))
    if sent > 0:
        paste(img, PILL("Envoyé", 26, "orange", dot=WHITE), 200 + 60, 510, sent, pop(prog(t, 2.8, 3.2)))
    # contact list card
    k2 = ease5(prog(t, 1.2, 1.9))
    cx, cy = 1440, H / 2 + 60
    paste(img, CARD(720, 560, 40, "light"), cx + (1 - k2) * 200, cy, k2)
    rows = [("WhatsApp", "+226 69 69 69 24"), ("Téléphone", "+226 05 58 58 68"), ("E-mail", "nticsolution.bf@gmail.com"), ("Site", "nticsolution.org")]
    for i, (lab, val) in enumerate(rows):
        a = ease(prog(t, 1.8 + i * .3, 2.2 + i * .3))
        y = cy - 190 + i * 115; x0 = cx - 300 + (1 - k2) * 200
        paste(img, PILL(str(i + 1), 22, "soft"), x0 + 12, y, a)
        txt(img, lab, 22, x0 + 60, y - 22, (110, 115, 145), "SemiBold", a, "l")
        txt(img, val, 31, x0 + 60 + (1 - a) * 30, y + 14, INK, "Bold", a, "l")
        on = ease(prog(t, 2.2 + i * .3, 2.45 + i * .3))
        toggle(img, cx + 270 + (1 - k2) * 200, y, on, a, ORANGE)
    a = ease(prog(t, 3.2, 3.7))
    txt(img, "Secteur 15, Quartier Tatana · Banfora, Burkina Faso", 30, 160, 960, (60, 70, 120), "SemiBold", a, "l")
    paste(img, ORB(10, "orange"), 140, 960, a)
    return img

def sc_outro(t, D):
    img = bg("navy", t)
    cx, cy = W / 2, H / 2 - 90
    # pulse rings
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(4):
        ph = ((t - .3) * .55 + i * .25) % 1
        if t < .3 + i * .45: continue
        r = 130 + ph * 330
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(110, 150, 255, int(150 * (1 - ph))), width=3)
    img.alpha_composite(lay)
    k = pop(prog(t, .2, .9))
    paste(img, blur_sp(ORB(120, "blue"), 30), cx, cy, ease(prog(t, .2, .9)) * .8, 1.6)
    paste(img, LOGO(240), cx, cy, ease(prog(t, .2, .6)), max(k, .01))
    a = ease5(prog(t, .9, 1.6))
    txt(img, "NTIC SOLUTION", 70, cx, cy + 210 + (1 - a) * 30, WHITE, "ExtraBold", a, track=10, blur=(1 - a) * 8)
    L = 200 * ease(prog(t, 1.4, 2.1))
    paste(img, Image.new("RGBA", (max(1, int(L)), 6), ORANGE + (255,)), cx, cy + 270, a)
    b = ease(prog(t, 1.9, 2.5))
    txt(img, "L'Univers du Digital", 40, cx, cy + 320, ORANGE, "SemiBoldItalic" if os.path.exists(FD + "InterDisplay-SemiBoldItalic.otf") else "SemiBold", b)
    c = ease(prog(t, 2.5, 3.0))
    paste(img, PILL("nticsolution.org", 30, "glass"), cx, cy + 420, c, pop(prog(t, 2.5, 3.0)))
    f = prog(t, D - .7, D)
    if f > 0: img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * f))))
    return img

SCENES = [
    (sc_phone, 3.6, "cut"),
    (sc_type, 4.6, "blur"),
    (sc_laptop, 4.0, "whip"),
    (sc_kin1, 3.6, "whip"),
    (sc_light_head, 3.4, "blur"),
    (sc_section, 2.6, "whip"),
    (sc_web, 5.0, "whip"),
    (sc_ai, 5.0, "whip"),
    (sc_secu, 5.0, "whip"),
    (sc_mkt, 5.0, "whip"),
    (sc_design, 5.0, "whip"),
    (sc_form, 4.8, "whip"),
    (sc_stack, 4.6, "blur"),
    (sc_kin2, 3.6, "whip"),
    (sc_contact, 6.0, "blur"),
    (sc_outro, 5.4, "blur"),
]
NOCORNER = {sc_outro}

def frame(si, t):
    fn, D, _ = SCENES[si]
    img = fn(t, D)
    if fn not in NOCORNER: corner(img)
    z = 1 + .035 * (t / D)
    if z > 1.001:
        cw, ch = W / z, H / z
        img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    return img.convert("RGB")

def lowsmear(im, amt):
    s = im.resize((W // 3, H // 3), Image.BILINEAR).convert("RGBA")
    s = smear(s, max(2, int(amt / 3)))
    return s.resize((W, H), Image.BILINEAR, box=(s.width / 2 - W / 6, 0, s.width / 2 + W / 6, s.height)).convert("RGB")

TR = .36
def render_scene(si):
    fn, D, tr = SCENES[si]
    n = int(round(D * FPS))
    out = os.path.join(OUTDIR, "seg%02d.mp4" % si)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out], stdin=subprocess.PIPE)
    prev = None
    if si > 0 and tr != "cut":
        pD = SCENES[si - 1][1]; prev = frame(si - 1, pD - 1 / FPS)
    for f in range(n):
        t = f / FPS
        im = frame(si, t)
        if prev is not None and t < TR:
            p_ = t / TR; e = eio(p_)
            if tr == "whip":
                c = Image.new("RGB", (W, H))
                c.paste(prev, (int(-e * W), 0)); c.paste(im, (int(W - e * W), 0))
                k = math.sin(math.pi * p_)
                im = Image.blend(c, lowsmear(c, 260 * k), min(1, k * 1.4))
            else:
                b = Image.blend(prev, im, e)
                k = math.sin(math.pi * p_)
                sm = b.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
                im = Image.blend(b, sm, k)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    return out

def timeline():
    ts, acc = [], 0.0
    for fn, D, tr in SCENES: ts.append(acc); acc += round(D * FPS) / FPS
    return ts, acc

if __name__ == "__main__":
    only = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else list(range(len(SCENES)))
    init_bg()
    with Pool(4) as pool:
        for o in pool.imap_unordered(render_scene, only): print("done", o, flush=True)
    ts, total = timeline()
    json.dump({"starts": ts, "total": total, "trans": [s[2] for s in SCENES]}, open(os.path.join(OUTDIR, "timeline.json"), "w"))
