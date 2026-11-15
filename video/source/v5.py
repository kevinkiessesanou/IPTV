"""NTIC – Web & mobile – moteur multi-formats (9:16, 4:5 natifs + 16:9) et montages courts.
usage: python v5.py OUTDIR FORMAT TIMELINE      FORMAT in {916,45,169}  TIMELINE in {full,prix,metiers}"""
import sys, os, math, json, subprocess
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT, FMT, TL = sys.argv[1], sys.argv[2], sys.argv[3]; PREVIEW = len(sys.argv) > 4
sys.argv = [sys.argv[0], OUT]
import v4, v2
from v4 import (BL, BL2, OR, WH, INKB, PALE, A, browser, phone_frame, chat_screen, reveal, QR)
from v2 import (font, tw, T, txt, paste, CARD, PILL, LOGO, CURSOR, clamp, prog, ease, ease5, eio, pop, lerp, blur_sp)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 30
SW, SH = 1080, 960                     # portrait stage
FW, FH = {"916": (1080, 1920), "45": (1080, 1350), "169": (1920, 1080)}[FMT]
STAGE_Y = {"916": 250, "45": 40}.get(FMT, 0)

TIMELINES = {
    "full": [(0.0, 58.6)],
    "prix": [(0.0, 3.40), (26.12, 28.62), (39.67, 47.55), (51.10, 52.20), (55.10, 58.6)],
    "metiers": [(0.0, 3.40), (8.96, 18.35), (23.81, 25.80), (51.10, 52.20), (55.10, 58.6)],
}
SEGS = TIMELINES[TL]

# ---------------------------------------------------------------- portrait backgrounds
_BG = {}
def fullbg(kind):
    key = (kind, FW, FH)
    if key not in _BG:
        yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
        r = np.sqrt(((xx - FW * .5) / FW) ** 2 + ((yy - FH * .42) / FH) ** 2)
        if kind == "white":
            k = np.clip(r * 1.4, 0, 1)[..., None]
            base = np.array([255, 255, 255]) * (1 - k) + np.array(PALE) * k
            dots = (((xx % 48) - 24) ** 2 + ((yy % 48) - 24) ** 2 < 3.2)[..., None] * np.array([-22, -14, 0]) * .6
            base = base + dots
        else:
            k = np.clip(1 - r * 1.3, 0, 1)[..., None]
            a, b = (np.array(BL), np.array(BL2)) if kind == "blue" else (np.array([238, 112, 0]), np.array([255, 160, 50]))
            base = a * (1 - k) + b * k
        _BG[key] = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    return _BG[key].copy()

def sig(img, cx, cy, t, col, a, n=3, flip=False, base_r=40, gap=36, width=8):
    v2.W, v2.H = img.width, img.height
    v4.signal(img, cx, cy, t, col, a, n, flip, base_r, gap, width)

def stage():
    v2.W, v2.H = SW, SH
    return Image.new("RGBA", (SW, SH), (0, 0, 0, 0))

# ---------------------------------------------------------------- portrait scenes: return (bgkind, stage)
def p_search(t):
    s = stage()
    txt(s, "Vos clients vous", 84, SW / 2, 40, INKB, "ExtraBold", 1, scale=lerp(1.12, 1, ease5(prog(t, 0, .35))))
    txt(s, "cherchent en ligne.", 84, SW / 2, 135, OR, "ExtraBold", 1, scale=lerp(1.12, 1, ease5(prog(t, 0, .35))))
    k = ease5(prog(t, 0, .6))
    paste(s, CARD(980, 110, 55, "light"), SW / 2, 290, max(k, .4))
    q = "restaurant Banfora"; n = int(len(q) * prog(t, .15, 1.0))
    txt(s, q[:n] + ("|" if int(t * 3) % 2 == 0 else ""), 44, SW / 2 - 440, 290, INKB, "SemiBold", 1, "l")
    gray = ease(prog(t, 2.5, 2.8))
    for i in range(4):
        a = ease5(prog(t, 1.1 + i * .12, 1.4 + i * .12))
        if a <= 0: continue
        x = 290 + (i % 2) * 500; y = 520 + (i // 2) * 240
        paste(s, CARD(470, 210, 26, "light"), x, y + (1 - a) * 50, a * (1 - .5 * gray))
        blk = Image.new("RGBA", (430, 100), (0, 0, 0, 0)); ImageDraw.Draw(blk).rounded_rectangle([0, 0, 429, 99], 16, fill=(BL if (i + i // 2) % 2 else OR) + (255,))
        paste(s, blk, x, y - 35 + (1 - a) * 50, a * (1 - .6 * gray))
        ImageDraw.Draw(s).rounded_rectangle([x - 200, y + 40, x + 60, y + 54], 7, fill=(170, 180, 215, int(255 * a * (1 - .5 * gray))))
        ImageDraw.Draw(s).rounded_rectangle([x - 200, y + 68, x - 20, y + 78], 5, fill=(205, 212, 240, int(255 * a * (1 - .5 * gray))))
    p = prog(t, 2.55, 2.8)
    if p > 0:
        sh = (1 - prog(t, 2.8, 3.2)) * 16; dx = math.sin(t * 90) * sh
        paste(s, CARD(900, 330, 50, "light", glow=OR), SW / 2 + dx, 640, ease(p), lerp(1.4, 1, ease5(p)))
        txt(s, "Et vous ?", 90, SW / 2 + dx, 580, INKB, "ExtraBold", ease(p), scale=lerp(1.4, 1, ease5(p)))
        txt(s, "Introuvable.", 110, SW / 2 + dx, 690, OR, "ExtraBold", ease(p), scale=lerp(1.4, 1, ease5(p)))
    return "white", s

def p_loop(t):
    s = stage(); t0 = A["loop"]
    reveal(s, "Restez", 120, SW / 2, 90, t, t0, WH)
    reveal(s, "jusqu'à la fin.", 100, SW / 2, 210, t, t0 + .2, WH)
    a = ease(prog(t, A["site"], A["site"] + .4)); b = ease(prog(t, A["pay3"], A["pay3"] + .4))
    txt(s, "Votre site…", 52, SW / 2, 330, (255, 205, 150), "Bold", a, sm=(1 - a) * 60)
    txt(s, "…payé en 3 fois.", 60, SW / 2, 400, WH, "ExtraBold", b, sm=(1 - b) * 60)
    cx, cy = SW / 2, 760
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(3):
        r = 120 + (2 - i) * 80
        d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=(255, 255, 255, 50), width=30)
        p = ease5(prog(t, A["pay3"] + i * .25, A["pay3"] + i * .25 + .5))
        if p > 0: d.arc([cx - r, cy - r, cx + r, cy + r], 200, 200 + 140 * p, fill=(OR if i == 2 else WH) + (255,), width=30)
    s.alpha_composite(lay)
    paste(s, LOGO(150), cx, cy, ease(prog(t, t0 + .2, t0 + .6)), pop(prog(t, t0 + .2, t0 + .7)))
    for i in range(3):
        p = pop(prog(t, A["pay3"] + i * .25, A["pay3"] + i * .25 + .4))
        if p > 0: paste(s, PILL(str(i + 1), 28, "orange" if i == 2 else "light", w="ExtraBold"), cx - 120 - (2 - i) * 80, cy + 50, clamp(p), p)
    return "blue", s

def p_trades(t):
    s = stage(); ts = A["trades"]
    pos = 0.0
    for i, x in enumerate(ts):
        if t >= x - .05: pos = i - 1 + ease5(prog(t, x - .05, x + .3))
    pos = max(0, pos); cur = int(round(pos))
    txt(s, "UN SITE POUR CHAQUE ACTIVITÉ", 30, SW / 2, 20, OR, "ExtraBold", 1, track=5)
    for i, (nm, h1, h2, ac, dom) in enumerate(v4.TRADES):
        rel = i - pos
        if abs(rel) > 1.6: continue
        x = SW / 2 + rel * 900; sc = 1 - min(1, abs(rel)) * .2; a = clamp(1.5 - abs(rel) * .8)
        bimg = browser(900, 560, t, [("hero", h1, h2), ("cards", 3), ("btns", [("Découvrir", "o"), ("Contact", "b")])], ts[i] + .1, dom or nm.lower() + ".bf", ac)
        paste(s, bimg, x, 420, a, sc)
        txt(s, nm, 104, x, 790, INKB, "ExtraBold", a, scale=sc)
        if dom and abs(rel) < .3:
            paste(s, PILL("Réalisé par NTIC  ✓", 26, "orange", w="ExtraBold"), SW / 2, 120, ease(prog(t, ts[i] + .3, ts[i] + .5)), pop(prog(t, ts[i] + .3, ts[i] + .6)))
    for i in range(8):
        on = i == cur
        dot = Image.new("RGBA", (44, 18), (0, 0, 0, 0)); ImageDraw.Draw(dot).rounded_rectangle([0, 0, 42 if on else 16, 16], 8, fill=(OR if on else (190, 200, 235)) + (255,))
        paste(s, dot, SW / 2 - 170 + i * 44, 910, 1, anchor="l")
    return "white", s

def p_split(t):
    s = stage()
    e = ease5(prog(t, A["chaque"], A["chaque"] + .5))
    sp = eio(prog(t, A["appli"] - .1, A["appli"] + .45))
    reveal(s, "Son site.", 100, SW / 2, 80, t, A["chaque"] + .3, INKB)
    bimg = browser(900, 540, t, [("hero", "Votre activité", "en ligne, 24 h / 24"), ("cards", 3), ("btns", [("Nous contacter", "o")])], A["chaque"] + .2, "votresite.com")
    paste(s, bimg, SW / 2 - sp * 200, lerp(500, 380, sp) + (1 - e) * 120, e, lerp(1, .62, sp))
    if sp > 0:
        top = lerp(SH + 40, 520, sp)
        panel = Image.new("RGBA", (SW + 200, SH), (0, 0, 0, 0)); ImageDraw.Draw(panel).rounded_rectangle([0, 0, SW + 199, SH], 60, fill=BL + (255,))
        paste(s, panel, SW / 2, top + SH / 2, 1)
        txt(s, "Son appli.", 96, 60, top + 120, WH, "ExtraBold", sp, "l")
        txt(s, "Android  ·  Web", 40, 64, top + 220, (255, 205, 150), "Bold", sp, "l")
        scr = Image.new("RGBA", (330, 680), WH + (255,)); d = ImageDraw.Draw(scr)
        d.rectangle([0, 0, 330, 250], fill=OR); d.text((30, 170), "Mon appli", font=font(40, "ExtraBold"), fill=WH)
        for j in range(3):
            a2 = ease(prog(t, A["appli"] + .3 + j * .15, A["appli"] + .6 + j * .15))
            d.rounded_rectangle([24, 280 + j * 110, 306, 370 + j * 110], 20, fill=PALE + (int(255 * a2),))
            d.ellipse([44, 305 + j * 110, 84, 345 + j * 110], fill=(BL if j % 2 else OR) + (int(255 * a2),))
        paste(s, phone_frame(scr), 790, top + 300, sp, .55, rot=-6)
    return "white", s

def p_kibaa(t):
    s = stage(); k0 = A["kibaa"]
    reveal(s, "Kibaa", 140, 60, 100, t, k0, WH, anchor="l")
    txt(s, "Notre propre", 44, 64, 220, (255, 205, 150), "Bold", ease(prog(t, k0 + .5, k0 + .9)), "l")
    txt(s, "application", 44, 64, 275, WH, "Bold", ease(prog(t, k0 + .6, k0 + 1.0)), "l")
    txt(s, "de messagerie.", 44, 64, 330, WH, "Bold", ease(prog(t, k0 + .7, k0 + 1.1)), "l")
    e = ease5(prog(t, k0 + .1, k0 + .7))
    paste(s, phone_frame(chat_screen(400, 820, t, k0 + .6)), 780, 480 + (1 - e) * 500, e, .9, rot=lerp(-12, -5, e))
    g = ease(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.0))
    if g > 0:
        paste(s, PILL("▶  Google Play", 32, "light", w="ExtraBold"), 240, 560, g, pop(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.1)))
        txt(s, "kibaa.online", 34, 64, 660, WH, "SemiBold", g, "l")
    sig(s, 120, 860, t, OR, .6, 3, flip=True)
    return "blue", s

def p_sait(t):
    s = stage()
    reveal(s, "Votre projet ?", 110, SW / 2, 150, t, A["projet"], INKB)
    a = ease5(prog(t, A["sait"], A["sait"] + .35))
    if a > 0:
        paste(s, T("On sait", 150, OR, "ExtraBold"), SW / 2, 470, a, lerp(1.35, 1, a))
        paste(s, T("le faire.", 150, OR, "ExtraBold"), SW / 2, 630, a, lerp(1.35, 1, a))
        for i in range(3):
            p = prog(t, A["sait"] + .2 + i * .12, A["sait"] + .8 + i * .12)
            if 0 < p < 1:
                lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); r = 200 + p * 500
                ImageDraw.Draw(lay).ellipse([SW / 2 - r, 550 - r * .7, SW / 2 + r, 550 + r * .7], outline=BL + (int(160 * (1 - p)),), width=6)
                s.alpha_composite(lay)
    return "white", s

def p_prix(t):
    s = stage(); p0 = A["prix"]
    txt(s, "SITE VITRINE", 52, SW / 2, 60, WH, "ExtraBold", ease(prog(t, p0, p0 + .3)), track=8)
    txt(s, "à partir de", 50, SW / 2, 140, WH, "SemiBold", ease(prog(t, p0 + .2, p0 + .5)))
    v = int(round(50000 * ease5(prog(t, p0 + .5, p0 + 1.7)) / 500) * 500)
    sv = "{:,}".format(v).replace(",", " ")
    a = ease(prog(t, p0 + .5, p0 + .7)); sc = 1 + .1 * math.sin(math.pi * prog(t, p0 + 1.7, p0 + 2.0))
    paste(s, T(sv, 230, BL, "ExtraBold"), SW / 2, 330, a, sc)
    paste(s, T("FCFA", 70, BL, "ExtraBold"), SW / 2, 480, a)
    d0 = A["delai"]; b = ease5(prog(t, d0, d0 + .45))
    if b > 0:
        txt(s, "LIVRAISON", 34, SW / 2, 620, WH, "ExtraBold", b, track=6)
        bar = Image.new("RGBA", (900, 30), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
        bd.rounded_rectangle([0, 6, 899, 24], 9, fill=(255, 255, 255, 110))
        bd.rounded_rectangle([0, 6, max(18, 899 * ease(prog(t, d0 + .3, d0 + 1.5))), 24], 9, fill=BL + (255,))
        paste(s, bar, SW / 2, 700, b)
        paste(s, LOGO(64), SW / 2 - 450 + 900 * ease(prog(t, d0 + .3, d0 + 1.5)), 700, b)
        txt(s, "1 semaine", 48, SW / 2 - 450, 780, WH, "ExtraBold", b, "l")
        txt(s, "1 mois", 48, SW / 2 + 450, 780, WH, "ExtraBold", ease(prog(t, d0 + 1.2, d0 + 1.5)), "r")
    return "orange", s

def p_method(t):
    s = stage()
    txt(s, "NOTRE MÉTHODE", 36, SW / 2, 20, OR, "ExtraBold", ease(prog(t, A["st1"] - .2, A["st1"] + .2)), track=8)
    ys = [160 + i * 210 for i in range(4)]; x = 130
    keys = [A[k] for _, _, k in v4.STEPS]
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line([x, ys[0], x, ys[3]], fill=(210, 220, 245), width=10)
    py = ys[0]
    for i in range(3):
        p = ease5(prog(t, keys[i + 1] - .5, keys[i + 1]))
        if p > 0: py = ys[i] + (ys[i + 1] - ys[i]) * p
    if t >= keys[0]: d.line([x, ys[0], x, py], fill=BL, width=10)
    s.alpha_composite(lay)
    for i, (h1, sub, key) in enumerate(v4.STEPS):
        t0 = A[key]; on = t >= t0; p = pop(prog(t, t0, t0 + .45))
        node = Image.new("RGBA", (140, 140), (0, 0, 0, 0)); nd = ImageDraw.Draw(node)
        nd.ellipse([8, 8, 132, 132], fill=(BL if on else WH) + (255,), outline=(OR if on else (205, 215, 245)) + (255,), width=8)
        nd.text((70, 70), str(i + 1), font=font(56, "ExtraBold"), fill=WH if on else (190, 200, 235), anchor="mm")
        paste(s, node, x, ys[i], 1, 1 + .15 * (p if 0 < p < 1 else 0))
        a = ease5(prog(t, t0, t0 + .4))
        active = on and (i == 3 or t < keys[i + 1])
        if active: paste(s, CARD(800, 170, 34, "light", glow=OR), 640, ys[i], a)
        txt(s, h1, 52, 250 + (1 - a) * 40, ys[i] - 26, INKB, "ExtraBold", max(.25, a), "l")
        txt(s, sub.replace("\n", " "), 32, 252 + (1 - a) * 40, ys[i] + 34, (90, 110, 170), "SemiBold", a, "l")
    return "white", s

def p_pay(t):
    s = stage()
    reveal(s, "Et le paiement ?", 96, SW / 2, 70, t, A["paiement"], WH)
    cx, cy, R = SW / 2, 440, 210
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, 50), width=56)
    segs = [(.5, "p50", WH, "50 %", "au lancement"), (.3, "p30", (255, 200, 140), "30 %", "à la livraison"), (.2, "p20", OR, "20 %", "après 30 jours")]
    st = -90
    for frac, key, col, lab, sub in segs:
        p = ease5(prog(t, A[key], A[key] + .6))
        if p > 0: d.arc([cx - R, cy - R, cx + R, cy + R], st, st + 360 * frac * p - 1.5, fill=col + (255,), width=56)
        st += 360 * frac
    s.alpha_composite(lay)
    paste(s, LOGO(200), cx, cy, ease(prog(t, A["paiement"] + .2, A["paiement"] + .6)))
    for i, (frac, key, col, lab, sub) in enumerate(segs):
        a = ease5(prog(t, A[key] + .1, A[key] + .45)); x = 190 + i * 350
        if a <= 0: continue
        txt(s, lab, 76, x, 730 + (1 - a) * 30, col, "ExtraBold", a)
        txt(s, sub, 28, x, 800 + (1 - a) * 30, WH, "SemiBold", a)
    r = ease(prog(t, A["reste"], A["reste"] + .4))
    if r > 0: paste(s, PILL("Le reste quand ça marche  ✓", 32, "orange", w="ExtraBold"), SW / 2, 900, r, pop(prog(t, A["reste"], A["reste"] + .5)))
    return "blue", s

def p_wall(t):
    s = stage(); t0 = A["conf"]
    txt(s, "ILS NOUS ONT FAIT CONFIANCE", 34, SW / 2, 20, BL, "ExtraBold", ease(prog(t, t0 - .1, t0 + .3)), track=4)
    for i, nm in enumerate(v4.PROJ + ["Votre projet ici ?"]):
        c, r = i % 3, i // 3
        x = 190 + c * 350; y = 170 + r * 200
        last = i == len(v4.PROJ); stt = A["case"] if last else t0 + i * .06
        p = ease5(prog(t, stt, stt + .35))
        if p <= 0: continue
        w_, h_ = 330, 170
        tile = Image.new("RGBA", (w_, h_), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
        col = OR if last else (BL if (c + r) % 2 == 0 else WH)
        td.rounded_rectangle([0, 0, w_ - 1, h_ - 1], 26, fill=col + (255,), outline=(205, 215, 245) if col == WH else None, width=3)
        lines = ["Votre projet", "ici ?"] if last else [nm]
        for j, l in enumerate(lines):
            fs = 38 if len(l) < 12 else 30
            td.text((w_ / 2, h_ / 2 + (j - (len(lines) - 1) / 2) * 44), l, font=font(fs, "ExtraBold"), fill=WH if col != WH else BL, anchor="mm")
        tile = tile.resize((max(2, int(w_ * max(.02, p))), h_), Image.BILINEAR)
        sc = 1 + (.08 * math.sin(t * 6) if last and t > A["votre"] else 0)
        paste(s, tile, x, y, 1, sc)
    return "white", s

def p_cta(t):
    s = stage(); t0 = A["cta"]
    if t < A["cherche"]:
        reveal(s, "Écrivez-nous", 110, SW / 2, 80, t, t0, BL, per=.02)
        reveal(s, "sur WhatsApp", 110, SW / 2, 210, t, t0 + .15, OR, per=.02)
        paste(s, CARD(980, 130, 65, "light"), SW / 2, 520)
        m = "Bonjour, je veux mon site !"; n = int(len(m) * prog(t, t0 + .1, t0 + .8))
        txt(s, m[:n], 44, SW / 2 - 440, 520, INKB, "SemiBold", 1, "l")
        cl = prog(t, t0 + .85, t0 + 1.0)
        btn = Image.new("RGBA", (100, 100), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
        bd.ellipse([0, 0, 99, 99], fill=OR); bd.polygon([(34, 28), (76, 50), (34, 72), (42, 50)], fill=WH)
        paste(s, btn, SW / 2 + 410, 520, 1, 1 - .15 * math.sin(math.pi * cl))
        paste(s, CURSOR(), lerp(SW - 40, SW / 2 + 425, ease(prog(t, t0 + .5, t0 + .85))), 560, 1)
        if t > t0 + 1.0: paste(s, PILL("Envoyé  ✓✓", 30, "blue", w="ExtraBold"), SW / 2 + 300, 660, 1, pop(prog(t, t0 + 1.0, t0 + 1.3)))
        return "white", s
    if t < A["trouve"] + .8:
        paste(s, CARD(980, 110, 55, "light"), SW / 2, 120)
        txt(s, "restaurant Banfora", 44, SW / 2 - 440, 120, INKB, "SemiBold", 1, "l")
        a = ease5(prog(t, A["trouve"] - .3, A["trouve"] + .2))
        paste(s, CARD(980, 230, 34, "blue", glow=OR), SW / 2, 360, a, 1 + .04 * pop(prog(t, A["trouve"], A["trouve"] + .4)))
        paste(s, LOGO(130), 150, 360, a)
        txt(s, "Votre entreprise", 58, 240, 330, WH, "ExtraBold", a, "l")
        txt(s, "Site officiel · WhatsApp", 30, 240, 400, (255, 210, 160), "SemiBold", a, "l")
        for i in range(2):
            paste(s, CARD(980, 120, 30, "light"), SW / 2, 580 + i * 140, .6)
        b = ease(prog(t, A["trouve"], A["trouve"] + .3))
        if b > 0: paste(s, PILL("Trouvé  ✓", 44, "orange", w="ExtraBold"), SW / 2 + 300, 220, b, pop(prog(t, A["trouve"], A["trouve"] + .4)))
        return "white", s
    e = ease(prog(t, A["trouve"] + .8, A["trouve"] + 1.2))
    sig(s, SW / 2, 230, t, BL, .5, 4, base_r=120, gap=46, width=12)
    sig(s, SW / 2, 230, t + .5, OR, .5, 4, flip=True, base_r=120, gap=46, width=12)
    v2.W, v2.H = SW, SH
    paste(s, LOGO(230), SW / 2, 230, e, pop(prog(t, A["trouve"] + .8, A["trouve"] + 1.3)))
    txt(s, "NTIC SOLUTION", 76, SW / 2, 440, BL, "ExtraBold", e, track=8)
    txt(s, "Agence digitale  ·  L'Univers du Digital", 36, SW / 2, 515, OR, "Bold", e)
    txt(s, "Secteur 15, Quartier Tatana", 32, SW / 2, 575, INKB, "SemiBold", e)
    txt(s, "Banfora, Burkina Faso", 32, SW / 2, 620, INKB, "SemiBold", e)
    paste(s, PILL("WhatsApp  +226 69 69 69 24", 46, "orange", w="ExtraBold"), SW / 2, 750, e, pop(prog(t, A["trouve"] + 1.1, A["trouve"] + 1.5)))
    txt(s, "Écrivez « SITE » pour démarrer", 38, SW / 2, 860, BL, "ExtraBold", ease(prog(t, A["trouve"] + 1.5, A["trouve"] + 1.9)))
    return "white", s

PSC = [(0.0, p_search), (A["loop"], p_loop), (A["trades"][0] - .02, p_trades), (A["chaque"], p_split), (A["kibaa"], p_kibaa),
       (A["projet"], p_sait), (A["prix"], p_prix), (A["st1"], p_method), (A["paiement"], p_pay), (A["conf"], p_wall), (A["cta"], p_cta)]
STARTS = [s for s, _ in PSC]
def scene_of(src):
    i = 0
    for k, s0 in enumerate(STARTS):
        if src >= s0 - 1e-6: i = k
    return i

# brand strip (9:16 only, lower zone) and 4:5 strip
def strip(img, kind):
    if FMT == "169": return
    y = 1480 if FMT == "916" else 1075
    col = BL if kind != "blue" else WH
    paste(img, LOGO(84), 120, y, 1)
    txt(img, "NTIC Solution", 40, 180, y - 20, col, "ExtraBold", 1, "l")
    txt(img, "Agence digitale · Banfora", 28, 182, y + 24, OR if kind != "orange" else WH, "Bold", 1, "l")
    paste(img, PILL("Écrivez « SITE »", 30, "orange" if kind != "orange" else "blue", w="ExtraBold"), FW - 210, y, 1)

def render_src(src, rel_scene_t):
    """full frame for a given source time"""
    if FMT == "169":
        si = v4.SC.index(next(sc for sc in reversed(v4.SC) if src >= sc[0] - 1e-6))
        v2.W, v2.H = 1920, 1080
        img = v4.SC[si][1](src)
        if v4.SC[si][1] is not v4.sc_cta or src < A["trouve"] + .8: paste(img, LOGO(60), 1860, 1024, .95)
        z = 1 + .05 * (1 - ease5(prog(rel_scene_t, 0, .4))) + .02 * min(1, rel_scene_t / 6)
        cw, ch = 1920 / z, 1080 / z
        return img.resize((1920, 1080), Image.BILINEAR, box=((1920 - cw) / 2, (1080 - ch) / 2, (1920 + cw) / 2, (1080 + ch) / 2)).convert("RGB")
    si = scene_of(src)
    kind, st = PSC[si][1](src)
    img = fullbg(kind)
    sig(img, FW - 110, 140 if FMT == "916" else 110, src, WH if kind != "white" else BL, .25, 3)
    sig(img, 110, FH - 160, src + 1, WH if kind != "white" else OR, .2, 3, flip=True)
    z = 1 + .05 * (1 - ease5(prog(rel_scene_t, 0, .4))) + .02 * min(1, rel_scene_t / 6)
    st = st.resize((int(SW * z), int(SH * z)), Image.BILINEAR)
    img.alpha_composite(st, (int((FW - st.width) / 2), int(STAGE_Y + (SH - st.height) / 2)))
    strip(img, kind)
    return img.convert("RGB")

# ---------------------------------------------------------------- output timeline
FRAMES = []          # (src_t, cut_flag)
for a, b in SEGS:
    n = int(round((b - a) * FPS))
    for k in range(n):
        FRAMES.append(a + k / FPS)
TOTAL = len(FRAMES)
def scene_key(src):
    if FMT == "169": return max(i for i, sc in enumerate(v4.SC) if src >= sc[0] - 1e-6)
    return scene_of(src)
CUTS = [0]
for k in range(1, TOTAL):
    if scene_key(FRAMES[k]) != scene_key(FRAMES[k - 1]) or abs(FRAMES[k] - FRAMES[k - 1] - 1 / FPS) > 1e-3: CUTS.append(k)
def rel_t(k):
    c = max(c for c in CUTS if c <= k); return (k - c) / FPS, c

TRN = 11
def out_frame(k):
    r, c = rel_t(k)
    im = render_src(FRAMES[k], r)
    if c > 0 and k - c < TRN:
        prev = render_src(FRAMES[c - 1], rel_t(c - 1)[0])
        p_ = (k - c) / TRN; col = BL if (c // 7) % 2 == 0 else OR
        x0 = lerp(-FW * .25, FW * 1.05, eio(p_))
        m = Image.new("L", (FW, FH), 0); ImageDraw.Draw(m).polygon([(x0 + FH * .2, 0), (FW * 2, 0), (FW * 2, FH), (x0 - FH * .1, FH)], fill=255)
        base = Image.composite(prev, im, m)
        band = Image.new("L", (FW, FH), 0); ImageDraw.Draw(band).polygon([(x0 - 80, 0), (x0 + FH * .2, 0), (x0 - FH * .1, FH), (x0 - FH * .1 - 280, FH)], fill=255)
        im = Image.composite(Image.new("RGB", (FW, FH), col), base, band)
    return im

def render_chunk(ci):
    n = 4; lo = TOTAL * ci // n; hi = TOTAL * (ci + 1) // n
    out = os.path.join(OUT, "chunk%d.mp4" % ci)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (FW, FH), "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out], stdin=subprocess.PIPE)
    for k in range(lo, hi): p.stdin.write(out_frame(k).tobytes())
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if PREVIEW:
        pts = [int(TOTAL * f) for f in np.linspace(.02, .98, 14)]
        ims = [out_frame(k).resize((FW // 5, FH // 5)) for k in pts]
        sh = Image.new("RGB", ((FW // 5) * 7, (FH // 5) * 2), WH)
        for i, im in enumerate(ims): sh.paste(im, ((i % 7) * (FW // 5), (i // 7) * (FH // 5)))
        sh.save(os.path.join(OUT, "preview.png")); sys.exit()
    with Pool(4) as pool: list(pool.imap_unordered(render_chunk, range(4)))
    with open(os.path.join(OUT, "list.txt"), "w") as fh:
        for ci in range(4): fh.write("file 'chunk%d.mp4'\n" % ci)
    json.dump({"segs": SEGS, "total": TOTAL / FPS}, open(os.path.join(OUT, "tl.json"), "w"))
