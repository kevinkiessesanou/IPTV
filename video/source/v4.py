"""NTIC Solution – Développement web & mobile – version 16:9 originale, palette logo (bleu roi / orange / blanc)."""
import sys, os, math, json, random, subprocess
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out4")
_argv = sys.argv[:]; sys.argv = [sys.argv[0], OUTDIR]
import v2
sys.argv = _argv
from v2 import (font, tw, fade, smear, blur_sp, paste, T, txt, kin, CARD, PILL, LOGO, CURSOR, toggle,
                clamp, prog, ease, ease5, eio, pop, lerp)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1920, 1080, 30
v2.W, v2.H = W, H
BL = (6, 46, 186); BL2 = (40, 90, 230); OR = (253, 132, 1); WH = (255, 255, 255)
INKB = (8, 30, 120)          # texte sur blanc = bleu logo foncé
PALE = (236, 242, 255)
v2.BLUE = BL; v2.ORANGE = OR; v2.INK = INKB

A = dict(loop=3.83, site=5.12, pay3=7.18, trades=[8.97, 9.92, 10.63, 11.15, 11.73, 12.55, 13.24, 14.01],
         chaque=14.90, appli=17.30, kibaa=18.64, kibaa2=20.20, projet=23.81, sait=25.06, prix=26.12, delai=28.82,
         st1=30.92, st2=33.15, st3=35.48, st4=37.41, paiement=39.67, p50=40.42, p30=41.97, p20=43.18, reste=45.78,
         conf=47.79, case=49.17, votre=50.26, cta=51.10, cherche=52.55, trouve=54.28, end=57.0)

# ---------------------------------------------------------------- backgrounds
def _white():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .4) / H) ** 2)
    k = np.clip(r * 1.4, 0, 1)[..., None]
    base = np.array([255, 255, 255]) * (1 - k) + np.array(PALE) * k
    dots = (((xx % 48) - 24) ** 2 + ((yy % 48) - 24) ** 2 < 3.2)[..., None] * np.array([-22, -14, 0])
    return Image.fromarray(np.clip(base + dots * .6, 0, 255).astype(np.uint8)).convert("RGBA")
def _blue():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    k = np.clip(1 - r * 1.3, 0, 1)[..., None]
    base = np.array(BL) * (1 - k) + np.array(BL2) * k
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
def _orange():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    k = np.clip(1 - r * 1.3, 0, 1)[..., None]
    base = np.array([238, 112, 0]) * (1 - k) + np.array([255, 160, 50]) * k
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
BGS = {}
def bg(kind, t):
    if not BGS: BGS.update(white=_white(), blue=_blue(), orange=_orange())
    im = BGS[kind].copy()
    # logo motif: slow signal arcs in a corner
    signal(im, W - 120, H - 110, t, WH if kind != "white" else BL, .10 if kind == "white" else .14, 4)
    signal(im, 120, 110, t + 1, WH if kind != "white" else OR, .08 if kind == "white" else .12, 4, flip=True)
    return im

def signal(img, cx, cy, t, col, a=1.0, n=3, flip=False, base_r=60, gap=46, width=10):
    """the logo's 'signal' arcs, animated outward"""
    lay = Image.new("RGBA", (int(2 * (base_r + gap * n + 40)),) * 2, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    c = lay.width / 2
    for i in range(n):
        ph = (t * .6 + i / n) % 1
        r = base_r + ph * gap * n
        al = int(255 * a * math.sin(math.pi * ph))
        st = 200 if not flip else 290
        d.arc([c - r, c - r, c + r, c + r], st, st + 50, fill=col + (al,), width=width)
    paste(img, lay, cx, cy)

def wipe(img, t, t0, col, d=.45, direction=1):
    """coloured panel that sweeps across (transition accent)"""
    p = prog(t, t0, t0 + d)
    if p <= 0 or p >= 1: return
    x0 = lerp(-W, W, eio(p)) if direction > 0 else lerp(W, -W, eio(p))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(x0, 0), (x0 + W * .9, 0), (x0 + W * .75, H), (x0 - W * .15, H)], fill=col + (255,))
    img.alpha_composite(lay)

def reveal(img, s, size, x, y, t, t0, col, w="ExtraBold", anchor="c", per=.03):
    """letter-by-letter rise reveal"""
    f = font(size, w); total = f.getlength(s)
    x0 = x - total / 2 if anchor == "c" else x
    cx = x0
    for i, ch in enumerate(s):
        p = ease5(prog(t, t0 + i * per, t0 + i * per + .35))
        if p > 0 and ch != " ":
            txt(img, ch, size, cx, y + (1 - p) * size * .6, col, w, p, "l")
        cx += f.getlength(ch)

def browser(w, h, t, spec, t0, url="votresite.com", accent=BL):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=WH + (255,), outline=(205, 215, 245), width=2)
    d.rounded_rectangle([0, 0, w - 1, 56], 22, fill=PALE + (255,)); d.rectangle([0, 34, w - 1, 56], fill=PALE + (255,))
    for i, c in enumerate([(250, 95, 85), (250, 190, 40), (60, 200, 90)]): d.ellipse([20 + i * 26, 20, 36 + i * 26, 36], fill=c)
    d.rounded_rectangle([110, 12, w - 30, 44], 16, fill=WH)
    d.text((130, 28), "🔒 " if False else url, font=font(18, "SemiBold"), fill=(90, 100, 150), anchor="lm")
    y = 76
    for i, b in enumerate(spec):
        a = ease(prog(t, t0 + i * .12, t0 + i * .12 + .35))
        if a <= 0: break
        k = b[0]; off = (1 - a) * 24; A_ = int(255 * a)
        if k == "hero":
            hh = int(h * .42)
            d.rounded_rectangle([20, y + off, w - 20, y + hh + off], 18, fill=accent + (A_,))
            paste(im, T(b[1], int(h * .085), WH, "ExtraBold"), 44, y + hh * .42 + off, a, anchor="l")
            paste(im, T(b[2], int(h * .04), (255, 220, 180) if accent == BL else WH, "SemiBold"), 46, y + hh * .7 + off, a, anchor="l")
            d.rounded_rectangle([w - 20 - hh * 1.1, y + 20 + off, w - 40, y + hh - 20 + off], 14, fill=(255, 255, 255, int(60 * a)))
            y += hh + 16
        elif k == "cards":
            n = b[1]; cw = (w - 40 - 16 * (n - 1)) / n; ch = h * .22
            for j in range(n):
                x = 20 + j * (cw + 16)
                d.rounded_rectangle([x, y + off, x + cw, y + ch + off], 14, fill=PALE + (A_,))
                d.rounded_rectangle([x + 14, y + 14 + off, x + cw * .45, y + 26 + off], 6, fill=(OR if j == 0 else BL) + (A_,))
                d.rounded_rectangle([x + 14, y + 38 + off, x + cw - 20, y + 46 + off], 4, fill=(190, 200, 235, A_))
            y += ch + 16
        elif k == "btns":
            for j, (s, c) in enumerate(b[1]):
                sp = PILL(s, int(h * .032), "orange" if c == "o" else "blue", w="ExtraBold")
                paste(im, sp, 24 + j * (sp.width - 60) + (sp.width - 80) / 2 + 30, y + 30, a, max(.01, pop(prog(t, t0 + i * .12, t0 + i * .12 + .4))))
            y += 70
    return im

def phone_frame(screen_img, a=1.0):
    sw, sh = screen_img.size; pad = 18
    im = Image.new("RGBA", (sw + 2 * pad + 80, sh + 2 * pad + 80), (0, 0, 0, 0))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([40, 60, 40 + sw + 2 * pad, 60 + sh + 2 * pad], 70, fill=(6, 30, 110, 90))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 40, 40 + sw + 2 * pad, 40 + sh + 2 * pad], 70, fill=BL)
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], 54, fill=255)
    sc = screen_img.copy(); sc.putalpha(m)
    im.alpha_composite(sc, (40 + pad, 40 + pad))
    d.rounded_rectangle([40 + pad + sw / 2 - 60, 40 + pad + 14, 40 + pad + sw / 2 + 60, 40 + pad + 44], 15, fill=(4, 20, 80))
    return im

def chat_screen(w, h, t, t0):
    im = Image.new("RGBA", (w, h), WH + (255,)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 150], fill=BL)
    paste(im, LOGO(64), 70, 105)
    d.text((115, 92), "Kibaa", font=font(30, "ExtraBold"), fill=WH, anchor="lm")
    d.text((115, 124), "en ligne", font=font(18, "SemiBold"), fill=(255, 200, 140), anchor="lm")
    msgs = [("l", "Salut ! Le projet avance ?"), ("r", "Oui, maquette prête 👍" if False else "Oui, la maquette est prête"), ("v",), ("r", "Devis.pdf"), ("l", "Parfait, on valide !")]
    y = 190
    for i, m in enumerate(msgs):
        a = ease5(prog(t, t0 + i * .45, t0 + i * .45 + .3))
        if a <= 0: break
        A_ = int(255 * a)
        if m[0] == "v":
            x0 = w - 300; d.rounded_rectangle([x0, y, w - 24, y + 66], 33, fill=OR + (A_,))
            for j in range(18):
                hh = 8 + 22 * abs(math.sin(j * .8 + t * 6)); x = x0 + 26 + j * 13
                d.rounded_rectangle([x, y + 33 - hh / 2, x + 6, y + 33 + hh / 2], 3, fill=(255, 255, 255, A_))
        else:
            s = m[1]; bw = tw(s, 22, "SemiBold") + 46
            x0 = w - 24 - bw if m[0] == "r" else 24
            d.rounded_rectangle([x0 + (1 - a) * (40 if m[0] == "r" else -40), y, x0 + bw, y + 60], 30, fill=(BL if m[0] == "r" else PALE) + (A_,))
            d.text((x0 + 23, y + 30), s, font=font(22, "SemiBold"), fill=(WH if m[0] == "r" else INKB) + (A_,), anchor="lm")
        y += 84
    return im

# ---------------------------------------------------------------- scenes (t = absolute time)
def sc_search(t):
    img = bg("white", t)
    k = ease5(prog(t, 0, .6))
    # big search bar
    paste(img, CARD(1100, 120, 60, "light"), W / 2, 300 + (1 - k) * -80, k)
    q = "restaurant Banfora"; n = int(len(q) * prog(t, .15, 1.0))
    txt(img, q[:n] + ("|" if int(t * 3) % 2 == 0 else ""), 48, W / 2 - 480, 300, INKB, "SemiBold", k, "l")
    lay = Image.new("RGBA", (60, 60), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.ellipse([8, 8, 40, 40], outline=BL, width=6); dd.line([36, 36, 54, 54], fill=BL, width=7)
    paste(img, lay, W / 2 + 480, 300, k)
    names = ["Maquis Le Baobab", "Restaurant Le Palmier", "Chez Awa", "Grill Express"]
    for i, nm in enumerate(names):
        a = ease5(prog(t, 1.1 + i * .12, 1.4 + i * .12))
        if a <= 0: continue
        x = 330 + i * 420; y = 620
        gray = ease(prog(t, 2.5, 2.8))
        paste(img, CARD(380, 300, 28, "light"), x, y + (1 - a) * 60, a * (1 - .5 * gray))
        dd2 = Image.new("RGBA", (340, 150), (0, 0, 0, 0)); ImageDraw.Draw(dd2).rounded_rectangle([0, 0, 339, 149], 18, fill=(BL if i % 2 else OR) + (255,))
        paste(img, dd2, x, y - 50 + (1 - a) * 60, a * (1 - .6 * gray))
        txt(img, nm, 28, x - 165, y + 60 + (1 - a) * 60, INKB, "Bold", a * (1 - .5 * gray), "l")
        txt(img, "★ 4,%d  ·  Site web" % (6 - i % 3), 22, x - 165, y + 100 + (1 - a) * 60, (110, 125, 180), "SemiBold", a * (1 - .5 * gray), "l")
    # the punch
    s = prog(t, 2.55, 2.8)
    if s > 0:
        sh = (1 - prog(t, 2.8, 3.2)) * 16; dx = math.sin(t * 90) * sh
        paste(img, CARD(1240, 230, 115, "light", glow=OR), W / 2 + dx, 640, ease(s), lerp(1.4, 1, ease5(s)))
        txt(img, "Et vous ? Introuvable.", 96, W / 2 + dx, 636, OR, "ExtraBold", ease(s), scale=lerp(1.4, 1, ease5(s)))
    return img

def sc_loop(t):
    img = bg("blue", t)
    t0 = A["loop"]
    reveal(img, "Restez jusqu'à la fin.", 96, 160, 330, t, t0, WH, anchor="l")
    a = ease(prog(t, A["site"], A["site"] + .4))
    txt(img, "Votre site…", 60, 160, 470, (255, 205, 150), "Bold", a, "l", sm=(1 - a) * 60)
    b = ease(prog(t, A["pay3"], A["pay3"] + .4))
    txt(img, "…payé en 3 fois.", 60, 160, 560, WH, "ExtraBold", b, "l", sm=(1 - b) * 60)
    # three big arcs (logo signal) filling one by one
    cx, cy = 1420, 560
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(3):
        r = 150 + (2 - i) * 90
        d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=(255, 255, 255, 50), width=34)
        p = ease5(prog(t, A["pay3"] + i * .25, A["pay3"] + i * .25 + .5))
        if p > 0: d.arc([cx - r, cy - r, cx + r, cy + r], 200, 200 + 140 * p, fill=(OR if i == 2 else WH) + (255,), width=34)
    img.alpha_composite(lay)
    paste(img, LOGO(170), cx, cy, ease(prog(t, t0 + .2, t0 + .6)), pop(prog(t, t0 + .2, t0 + .7)))
    for i in range(3):
        p = pop(prog(t, A["pay3"] + i * .25, A["pay3"] + i * .25 + .4))
        if p > 0: paste(img, PILL("%d" % (i + 1), 30, "orange" if i == 2 else "light", w="ExtraBold"), cx - 150 - (2 - i) * 90 + 6, cy + 60, clamp(p), p)
    return img

TRADES = [
    ("Restaurant", "Menu du jour", "Commandez en un clic", OR, "menusqr.online"),
    ("Boutique", "Nouvelle collection", "Livraison rapide", BL, "maisondesbonneschoses.shop"),
    ("École", "Inscriptions ouvertes", "Notes · Emploi du temps", BL, "managerschool.online"),
    ("Média", "En direct", "Infos · Sport · Culture", OR, "evitv.com"),
    ("Entreprise", "Gestion simplifiée", "Stock · Ventes · Factures", BL, "gestionplus.store"),
    ("Événement", "Le tournoi", "Calendrier · Résultats", OR, "coupeduronier.com"),
    ("Institution", "Bienvenue", "Actualités · Services", BL, None),
    ("Clinique", "Rendez-vous en ligne", "Choisissez votre créneau", OR, None),
]
def sc_trades(t):
    img = bg("white", t)
    ts = A["trades"]
    pos = 0.0
    for i, x in enumerate(ts): pos = i + ease5(prog(t, x - .05, x + .3)) - 1 if t >= x - .05 else pos
    pos = max(0, pos)
    cur = int(round(pos))
    txt(img, "UN SITE POUR CHAQUE ACTIVITÉ", 30, W / 2, 120, OR, "ExtraBold", 1, track=6)
    for i, (nm, h1, h2, ac, dom) in enumerate(TRADES):
        rel = i - pos
        if abs(rel) > 2.2: continue
        x = W / 2 + rel * 640; sc = 1 - min(1, abs(rel)) * .28
        a = clamp(1.6 - abs(rel) * .7)
        bimg = browser(760, 470, t, [("hero", h1, h2), ("cards", 3), ("btns", [("Découvrir", "o"), ("Contact", "b")])], ts[i] + .1, (dom or nm.lower() + ".bf"), ac)
        paste(img, bimg, x, 560, a, sc * .95)
        txt(img, nm, 78, x, 900, INKB if abs(rel) < .5 else (150, 165, 210), "ExtraBold", a, scale=sc)
        if dom and abs(rel) < .3:
            paste(img, PILL("Réalisé par NTIC  ✓", 24, "orange", w="ExtraBold"), x + 250, 300, ease(prog(t, ts[i] + .3, ts[i] + .5)), pop(prog(t, ts[i] + .3, ts[i] + .6)))
    # progress dots
    for i in range(8):
        on = i == cur
        lay = Image.new("RGBA", (40, 20), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle([0, 0, 38 if on else 14, 14], 7, fill=(OR if on else (190, 200, 235)) + (255,))
        paste(img, lay, W / 2 - 150 + i * 40, 1000, 1, anchor="l")
    return img

def sc_split(t):
    img = bg("white", t)
    sp = eio(prog(t, A["appli"] - .1, A["appli"] + .45))
    split = lerp(W, W * .5, sp)
    # left: site
    e = ease5(prog(t, A["chaque"], A["chaque"] + .5))
    bimg = browser(820, 520, t, [("hero", "Votre activité", "en ligne, 24 h / 24"), ("cards", 3), ("btns", [("Nous contacter", "o")])], A["chaque"] + .2, "votresite.com")
    paste(img, bimg, lerp(W / 2, split / 2, sp), 600 + (1 - e) * 120, e, lerp(1.0, .78, sp))
    reveal(img, "Son site.", 92, lerp(W / 2, split / 2, sp), 180, t, A["chaque"] + .3, INKB)
    if sp > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lay.paste(BGS["blue"].crop((int(split), 0, W, H)), (int(split), 0))
        img.alpha_composite(lay)
        ph_scr = Image.new("RGBA", (330, 680), WH + (255,)); d = ImageDraw.Draw(ph_scr)
        d.rectangle([0, 0, 330, 250], fill=OR); d.text((30, 170), "Mon appli", font=font(40, "ExtraBold"), fill=WH)
        for j in range(3):
            a2 = ease(prog(t, A["appli"] + .3 + j * .15, A["appli"] + .6 + j * .15))
            d.rounded_rectangle([24, 280 + j * 110, 306, 370 + j * 110], 20, fill=(PALE[0], PALE[1], PALE[2], int(255 * a2)))
            d.ellipse([44, 305 + j * 110, 84, 345 + j * 110], fill=(BL if j % 2 else OR) + (int(255 * a2),))
            d.rounded_rectangle([100, 312 + j * 110, 260, 324 + j * 110], 6, fill=(INKB[0], INKB[1], INKB[2], int(200 * a2)))
        ph = phone_frame(ph_scr)
        ph2 = Image.new("RGBA", ph.size, (0, 0, 0, 0)); ph2.alpha_composite(ph)
        ImageDraw.Draw(ph2).rounded_rectangle([40, 40, ph.width - 41, ph.height - 41], 70, outline=WH, width=6)
        paste(img, ph2, split + (W - split) / 2, 620 + (1 - sp) * 300, sp, .8)
        reveal(img, "Son appli.", 92, split + (W - split) / 2, 180, t, A["appli"] + .1, WH)
    return img

def sc_kibaa(t):
    img = bg("blue", t)
    k0 = A["kibaa"]
    reveal(img, "Kibaa", 150, 180, 330, t, k0, WH, anchor="l")
    txt(img, "Notre propre application", 46, 185, 470, (255, 205, 150), "Bold", ease(prog(t, k0 + .5, k0 + .9)), "l")
    txt(img, "de messagerie.", 46, 185, 530, WH, "Bold", ease(prog(t, k0 + .7, k0 + 1.1)), "l")
    g = ease(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.0))
    if g > 0:
        paste(img, PILL("▶  Disponible sur Google Play", 34, "light", w="ExtraBold"), 470, 680, g, pop(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.1)))
        txt(img, "kibaa.online", 36, 185, 790, WH, "SemiBold", g, "l")
    e = ease5(prog(t, k0 + .1, k0 + .7))
    ph = phone_frame(chat_screen(400, 820, t, k0 + .6))
    paste(img, ph, 1360, 560 + (1 - e) * 500, e, .95, rot=lerp(-12, -4, e))
    signal(img, 1700, 250, t, WH, .5, 3, base_r=40, gap=36)
    signal(img, 1020, 860, t + .5, OR, .6, 3, flip=True, base_r=40, gap=36)
    return img

def sc_sait(t):
    img = bg("white", t)
    reveal(img, "Votre projet ?", 120, W / 2, 380, t, A["projet"], INKB)
    s = A["sait"]
    a = ease5(prog(t, s, s + .35))
    if a > 0:
        paste(img, T("On sait le faire.", 150, OR, "ExtraBold"), W / 2, 620, a, lerp(1.35, 1, a))
        for i in range(3):
            p = prog(t, s + .2 + i * .12, s + .8 + i * .12)
            if 0 < p < 1:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); r = 200 + p * 700
                ImageDraw.Draw(lay).ellipse([W / 2 - r, 620 - r * .5, W / 2 + r, 620 + r * .5], outline=BL + (int(160 * (1 - p)),), width=6)
                img.alpha_composite(lay)
    return img

def sc_prix(t):
    img = bg("orange", t)
    p0 = A["prix"]
    txt(img, "SITE VITRINE  ·  À PARTIR DE", 40, W / 2, 230, WH, "ExtraBold", ease(prog(t, p0, p0 + .3)), track=6)
    v = int(round(50000 * ease5(prog(t, p0 + .5, p0 + 1.7)) / 500) * 500)
    sv = "{:,}".format(v).replace(",", " ") + " F"
    a = ease(prog(t, p0 + .5, p0 + .7)); sc = 1 + .1 * math.sin(math.pi * prog(t, p0 + 1.7, p0 + 2.0))
    paste(img, T(sv, 230, BL, "ExtraBold"), W / 2, 450, a, sc)
    d0 = A["delai"]; b = ease5(prog(t, d0, d0 + .45))
    if b > 0:
        lay = Image.new("RGBA", (1300, 30), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([0, 6, 1299, 24], 9, fill=(255, 255, 255, 110))
        dd.rounded_rectangle([0, 6, max(18, 1299 * ease(prog(t, d0 + .3, d0 + 1.5))), 24], 9, fill=BL + (255,))
        paste(img, lay, W / 2, 790, b)
        txt(img, "LIVRAISON", 30, W / 2, 720, WH, "ExtraBold", b, track=6)
        txt(img, "1 semaine", 50, W / 2 - 650, 870, WH, "ExtraBold", b, "l")
        txt(img, "1 mois", 50, W / 2 + 650, 870, WH, "ExtraBold", ease(prog(t, d0 + 1.2, d0 + 1.5)), "r")
        mx = W / 2 - 650 + 1300 * ease(prog(t, d0 + .3, d0 + 1.5))
        paste(img, LOGO(70), mx, 790, b)
    return img

STEPS = [("Entretien", "On comprend\nvotre activité", "st1"), ("Cahier des charges", "Validé\nensemble", "st2"),
         ("Maquette", "Vous voyez\navant de commencer", "st3"), ("Développement", "Toute l'équipe\nmobilisée", "st4")]
def sc_method(t):
    img = bg("white", t)
    txt(img, "NOTRE MÉTHODE", 34, W / 2, 150, OR, "ExtraBold", ease(prog(t, A["st1"], A["st1"] + .3)), track=8)
    xs = [300 + i * 440 for i in range(4)]; y = 470
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line([xs[0], y, xs[3], y], fill=(210, 220, 245), width=10)
    keys = [A[s[2]] for s in STEPS]
    prog_x = xs[0]
    for i in range(3):
        p = ease5(prog(t, keys[i + 1] - .5, keys[i + 1]))
        if p > 0: prog_x = xs[i] + (xs[i + 1] - xs[i]) * p
    if t >= keys[0]: d.line([xs[0], y, prog_x, y], fill=BL, width=10)
    img.alpha_composite(lay)
    for i, (h1, sub, key) in enumerate(STEPS):
        t0 = A[key]; on = t >= t0
        p = pop(prog(t, t0, t0 + .45))
        c = OR if on else (205, 215, 245)
        node = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); nd = ImageDraw.Draw(node)
        nd.ellipse([10, 10, 150, 150], fill=(BL if on else WH) + (255,), outline=c + (255,), width=8)
        nd.text((80, 80), str(i + 1), font=font(64, "ExtraBold"), fill=WH if on else (190, 200, 235), anchor="mm")
        paste(img, node, xs[i], y, 1, 1 + .15 * (p if 0 < p < 1 else 0))
        a = ease5(prog(t, t0, t0 + .4))
        txt(img, h1, 40, xs[i], y + 150 + (1 - a) * 30, INKB, "ExtraBold", max(.25, a))
        for j, line in enumerate(sub.split("\n")):
            txt(img, line, 30, xs[i], y + 210 + j * 42 + (1 - a) * 30, (90, 110, 170), "SemiBold", a)
        if on: signal(img, xs[i] + 70, y - 70, t, OR, .7 * a, 2, base_r=20, gap=24, width=6)
    return img

def sc_pay(t):
    img = bg("blue", t)
    reveal(img, "Et le paiement ?", 100, 150, 220, t, A["paiement"], WH, anchor="l")
    cx, cy, R = 1400, 560, 290
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, 50), width=70)
    start = -90
    segs = [(.5, "p50", WH, "50 %", "au lancement"), (.3, "p30", (255, 200, 140), "30 %", "à la livraison"), (.2, "p20", OR, "20 %", "après 30 jours d'utilisation")]
    for frac, key, col, lab, sub in segs:
        p = ease5(prog(t, A[key], A[key] + .6))
        if p > 0: d.arc([cx - R, cy - R, cx + R, cy + R], start, start + 360 * frac * p - 1.5, fill=col + (255,), width=70)
        start += 360 * frac
    img.alpha_composite(lay)
    paste(img, LOGO(260), cx, cy, ease(prog(t, A["paiement"] + .2, A["paiement"] + .6)))
    for i, (frac, key, col, lab, sub) in enumerate(segs):
        a = ease5(prog(t, A[key] + .1, A[key] + .45)); y = 430 + i * 150
        if a <= 0: continue
        txt(img, lab, 86, 150 + (1 - a) * -60, y, col, "ExtraBold", a, "l")
        txt(img, sub, 38, 420 + (1 - a) * -60, y + 6, WH, "SemiBold", a, "l")
    r = ease(prog(t, A["reste"], A["reste"] + .4))
    if r > 0: paste(img, PILL("Vous payez le reste quand ça marche  ✓", 34, "orange", w="ExtraBold"), 560, 930, r, pop(prog(t, A["reste"], A["reste"] + .5)))
    return img

PROJ = ["NTIC Solution", "MyVivo", "Menus QR", "EVI TV", "CCGT TV Media", "Gestion+", "Coupe du Ronier", "Tannounyan", "MBC", "Manager School", "Kibaa"]
def sc_wall(t):
    img = bg("white", t)
    t0 = A["conf"]
    txt(img, "ILS NOUS ONT FAIT CONFIANCE", 40, W / 2, 130, BL, "ExtraBold", ease(prog(t, t0, t0 + .3)), track=6)
    for i, nm in enumerate(PROJ + ["Votre projet ici ?"]):
        c, r = i % 4, i // 4
        x = 330 + c * 420; y = 330 + r * 230
        last = i == len(PROJ)
        st = A["case"] if last else t0 + i * .06
        p = ease5(prog(t, st, st + .35))
        if p <= 0: continue
        flip = max(.02, p)  # scale-x flip-in
        w_, h_ = 380, 180
        tile = Image.new("RGBA", (w_, h_), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
        col = OR if last else (BL if (c + r) % 2 == 0 else WH)
        td.rounded_rectangle([0, 0, w_ - 1, h_ - 1], 28, fill=col + (255,), outline=(205, 215, 245) if col == WH else None, width=3)
        fs = 40 if len(nm) < 12 else 32
        td.text((w_ / 2, h_ / 2), nm, font=font(fs, "ExtraBold"), fill=WH if col != WH else BL, anchor="mm")
        tile = tile.resize((max(2, int(w_ * flip)), h_), Image.BILINEAR)
        sc = 1 + (.08 * math.sin(t * 6) if last and t > A["votre"] else 0)
        paste(img, CARD(int(w_ * flip), h_, 28, "light"), x, y + 8, .5 * p)
        paste(img, tile, x, y, 1, sc)
    return img

def sc_cta(t):
    t0 = A["cta"]
    if t < A["cherche"]:
        img = bg("white", t)
        reveal(img, "Écrivez-nous sur WhatsApp", 90, W / 2, 260, t, t0, BL, per=.015)
        paste(img, CARD(1200, 130, 65, "light"), W / 2, 560)
        m = "Bonjour, je veux mon site !"; n = int(len(m) * prog(t, t0 + .1, t0 + .8))
        txt(img, m[:n], 48, W / 2 - 540, 560, INKB, "SemiBold", 1, "l")
        cl = prog(t, t0 + .85, t0 + 1.0)
        btn = Image.new("RGBA", (100, 100), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
        bd.ellipse([0, 0, 99, 99], fill=OR); bd.polygon([(34, 28), (76, 50), (34, 72), (42, 50)], fill=WH)
        paste(img, btn, W / 2 + 520, 560, 1, 1 - .15 * math.sin(math.pi * cl))
        paste(img, CURSOR(), lerp(W / 2 + 800, W / 2 + 535, ease(prog(t, t0 + .5, t0 + .85))), 600, 1)
        if t > t0 + 1.0: paste(img, PILL("Envoyé  ✓✓", 30, "blue", w="ExtraBold"), W / 2 + 430, 700, 1, pop(prog(t, t0 + 1.0, t0 + 1.3)))
        return img
    img = bg("white", t)
    if t < A["trouve"] + .8:
        paste(img, CARD(1100, 110, 55, "light"), W / 2, 230)
        txt(img, "restaurant Banfora", 44, W / 2 - 480, 230, INKB, "SemiBold", 1, "l")
        a = ease5(prog(t, A["trouve"] - .3, A["trouve"] + .2))
        paste(img, CARD(1100, 220, 34, "blue", glow=OR), W / 2, 470, a, 1 + .04 * pop(prog(t, A["trouve"], A["trouve"] + .4)))
        paste(img, LOGO(140), W / 2 - 420, 470, a)
        txt(img, "Votre entreprise", 60, W / 2 - 320, 440, WH, "ExtraBold", a, "l")
        txt(img, "Site officiel  ·  Commander  ·  WhatsApp", 30, W / 2 - 320, 510, (255, 210, 160), "SemiBold", a, "l")
        for i, nm in enumerate(["Maquis Le Baobab", "Restaurant Le Palmier"]):
            paste(img, CARD(1100, 120, 30, "light"), W / 2, 680 + i * 140, .6)
            txt(img, nm, 34, W / 2 - 480, 680 + i * 140, (150, 165, 210), "Bold", .8, "l")
        b = ease(prog(t, A["trouve"], A["trouve"] + .3))
        if b > 0: paste(img, PILL("Trouvé  ✓", 40, "orange", w="ExtraBold"), W / 2 + 430, 360, b, pop(prog(t, A["trouve"], A["trouve"] + .4)))
        return img
    # end card – white, logo + arcs
    e = ease(prog(t, A["trouve"] + .8, A["trouve"] + 1.2))
    signal(img, W / 2, 420, t, BL, .5, 4, base_r=150, gap=60, width=14)
    signal(img, W / 2, 420, t + .5, OR, .5, 4, flip=True, base_r=150, gap=60, width=14)
    paste(img, LOGO(260), W / 2, 420, e, pop(prog(t, A["trouve"] + .8, A["trouve"] + 1.3)))
    txt(img, "NTIC SOLUTION", 76, W / 2, 640, BL, "ExtraBold", e, track=10)
    txt(img, "Développement web & mobile", 40, W / 2, 720, OR, "Bold", e)
    paste(img, PILL("WhatsApp  +226 69 69 69 24", 46, "orange", w="ExtraBold"), W / 2, 860, e, pop(prog(t, A["trouve"] + 1.1, A["trouve"] + 1.5)))
    return img

SC = [(0.0, sc_search, "cut"), (A["loop"], sc_loop, "wipeB"), (A["trades"][0] - .02, sc_trades, "wipeO"), (A["chaque"], sc_split, "wipeB"),
      (A["kibaa"], sc_kibaa, "wipeO"), (A["projet"], sc_sait, "wipeB"), (A["prix"], sc_prix, "wipeB"), (A["st1"], sc_method, "wipeO"),
      (A["paiement"], sc_pay, "wipeO"), (A["conf"], sc_wall, "wipeB"), (A["cta"], sc_cta, "wipeO")]
FR = [round(s * FPS) for s, _, _ in SC] + [round(A["end"] * FPS)]

def frame(si, f):
    t = f / FPS
    img = SC[si][1](t)
    if SC[si][1] is not sc_cta or t < A["trouve"] + .8: paste(img, LOGO(60), W - 60, H - 56, .95)
    rel = t - FR[si] / FPS; D = (FR[si + 1] - FR[si]) / FPS
    z = 1 + .025 * (rel / D) + .05 * (1 - ease5(prog(rel, 0, .4)))
    cw, ch = W / z, H / z
    return img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).convert("RGB")

TRN = 12
def render(si):
    out = os.path.join(OUTDIR, "seg%02d.mp4" % si)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out], stdin=subprocess.PIPE)
    tr = SC[si][2]
    prev = frame(si - 1, FR[si] - 1) if si > 0 and tr != "cut" else None
    for f in range(FR[si], FR[si + 1]):
        im = frame(si, f); k = f - FR[si]
        if prev is not None and k < TRN:
            # diagonal colour panel sweeps over, revealing the new scene behind it
            p_ = k / TRN; col = BL if tr == "wipeB" else OR
            x0 = lerp(-W * .2, W * 1.0, eio(p_))
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon([(x0 + 200, 0), (W * 2, 0), (W * 2, H), (x0 - 100, H)], fill=255)
            base = Image.composite(prev, im, m)
            band = Image.new("L", (W, H), 0); ImageDraw.Draw(band).polygon([(x0 - 80, 0), (x0 + 200, 0), (x0 - 100, H), (x0 - 380, H)], fill=255)
            im = Image.composite(Image.new("RGB", (W, H), col), base, band)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        ims = []
        for si in range(len(SC)):
            for fr in (.5, .92):
                f = int(FR[si] + (FR[si + 1] - FR[si]) * fr); ims.append(frame(si, f).resize((384, 216)))
        sh = Image.new("RGB", (384 * 4, 216 * 6), WH)
        for i, im in enumerate(ims): sh.paste(im, ((i % 4) * 384, (i // 4) * 216))
        sh.save(os.path.join(OUTDIR, "preview.png")); sys.exit()
    with Pool(4) as pool:
        for o in pool.imap_unordered(render, range(len(SC))): print("done", o, flush=True)
    with open(os.path.join(OUTDIR, "list.txt"), "w") as fh:
        for si in range(len(SC)): fh.write("file 'seg%02d.mp4'\n" % si)
    json.dump({"A": A, "starts": [f / FPS for f in FR]}, open(os.path.join(OUTDIR, "timeline.json"), "w"))
