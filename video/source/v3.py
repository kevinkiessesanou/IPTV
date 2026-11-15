"""NTIC Solution – vidéo Développement web & mobile, native 9:16, calée sur la voix ElevenLabs."""
import sys, os, math, json, random, subprocess
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out3")
_argv = sys.argv[:]; sys.argv = [sys.argv[0], OUTDIR]
import v2
sys.argv = _argv
from v2 import *  # helpers
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
v2.W, v2.H = W, H
FPS = 30
RED = (240, 60, 70); GREEN = (40, 190, 110)

# ---------------- voice anchors (seconds, ElevenLabs file)
A = dict(
    s0=0.0, concur=1.92, loop=3.83, site=5.12, pay3=7.18,
    trades=[8.97, 9.92, 10.63, 11.15, 11.73, 12.55, 13.24, 14.01],
    chaque=14.90, appli=17.30, kibaa=18.64, kibaa2=20.20, projet=23.81, sait=25.06,
    prix=26.12, delai=28.82, st1=30.92, st2=33.15, st3=35.48, st4=37.41,
    paiement=39.67, p50=40.42, p30=41.97, p20=43.18, reste=45.78,
    conf=47.79, case=49.17, votre=50.26, cta=51.10, cherche=52.55, trouve=54.28, end=56.8)

def bgv(kind, t):
    return bg(kind, t)

def headline(img, s, size, y, t, t0, col=WHITE, out=None, anchor="c", x=None):
    kin(img, s, size, W / 2 if x is None else x, y, t, t0, col, out=out, anchor=anchor, dist=200)

# ---------------- generic phone screen builder
def screen(w, h, t, spec, t0=0.0, dark=False):
    bgc = (12, 13, 20) if dark else (246, 247, 252)
    fg = WHITE if dark else INK
    im = Image.new("RGBA", (w, h), bgc + (255,)); d = ImageDraw.Draw(im)
    d.text((44, 26), "9:41", font=font(24, "SemiBold"), fill=fg)
    y = 90
    for i, blk in enumerate(spec):
        a = ease(prog(t, t0 + i * .12, t0 + i * .12 + .3))
        if a <= 0: break
        k = blk[0]; off = (1 - a) * 30
        if k == "hero":
            _, col, title, sub = blk
            hh = 250
            d.rounded_rectangle([20, y + off, w - 20, y + hh + off], 28, fill=col + (int(255 * a),))
            paste(im, ORB(46, "white"), w - 90, y + 80 + off, a * .9)
            paste(im, T(title, 44, WHITE, "ExtraBold"), 44 - 6, y + 150 + off, a, anchor="l")
            paste(im, T(sub, 22, (255, 230, 200), "SemiBold"), 44 - 4, y + 200 + off, a, anchor="l")
            y += hh + 20
        elif k == "row":
            _, label, val, ic = blk
            paste(im, CARD(w - 40, 84, 22, "dark" if dark else "light"), w / 2, y + 42 + off, a)
            d.ellipse([44, y + 22 + off, 84, y + 62 + off], fill=ic + (int(255 * a),))
            paste(im, T(label, 24, fg, "Bold"), 100 - 4, y + 42 + off, a, anchor="l")
            if val: paste(im, T(val, 24, ORANGE, "ExtraBold"), w - 44, y + 42 + off, a, anchor="r")
            y += 96
        elif k == "grid":
            _, n, cols = blk
            cw = (w - 40 - 16) / 2
            for j in range(n):
                cx = 20 + (j % 2) * (cw + 16); cy = y + (j // 2) * (cw * .9 + 16) + off
                d.rounded_rectangle([cx, cy, cx + cw, cy + cw * .9], 22, fill=cols[j % len(cols)] + (int(255 * a),))
                d.rounded_rectangle([cx + 16, cy + cw * .9 - 40, cx + cw * .6, cy + cw * .9 - 26], 6, fill=(255, 255, 255, int(200 * a)))
            y += math.ceil(n / 2) * (cw * .9 + 16)
        elif k == "btn":
            _, txt_, col = blk
            sc = pop(prog(t, t0 + i * .12, t0 + i * .12 + .4))
            paste(im, PILL(txt_, 28, "orange" if col == "o" else "blue", w="ExtraBold"), w / 2, y + 40, a, max(sc, .01))
            y += 100
        elif k == "chart":
            for j, v in enumerate([.4, .6, .5, .8, .7, 1.0]):
                g = ease(prog(t, t0 + i * .12 + j * .06, t0 + i * .12 + j * .06 + .5))
                x0 = 40 + j * (w - 80) / 6
                d.rounded_rectangle([x0, y + 220 - 200 * v * g, x0 + (w - 80) / 6 - 14, y + 220], 8, fill=(BLUE if j < 5 else ORANGE) + (255,))
            y += 240
        elif k == "live":
            d.rounded_rectangle([20, y + off, w - 20, y + 260 + off], 24, fill=(20, 22, 34, int(255 * a)))
            d.polygon([(w / 2 - 26, y + 100 + off), (w / 2 + 34, y + 130 + off), (w / 2 - 26, y + 160 + off)], fill=(255, 255, 255, int(230 * a)))
            if int(t * 2) % 2 == 0: d.ellipse([44, y + 30 + off, 62, y + 48 + off], fill=RED + (255,))
            d.text((72, y + 26 + off), "EN DIRECT", font=font(22, "ExtraBold"), fill=(255, 255, 255, int(255 * a)))
            y += 280
        elif k == "cal":
            days = ["L", "M", "M", "J", "V", "S", "D"]
            for j in range(14):
                cx = 30 + (j % 7) * (w - 60) / 7; cy = y + (j // 7) * 70 + off
                sel = j == 9 and t > t0 + i * .12 + .6
                d.rounded_rectangle([cx, cy, cx + (w - 60) / 7 - 10, cy + 58], 14, fill=(ORANGE if sel else ((40, 44, 60) if dark else (226, 230, 245))) + (int(255 * a),))
                d.text((cx + 26, cy + 29), str(10 + j), font=font(22, "Bold"), fill=(WHITE if sel or dark else INK), anchor="mm")
            y += 160
        elif k == "score":
            _, a1, b1, s1 = blk
            paste(im, CARD(w - 40, 120, 24, "dark" if dark else "light"), w / 2, y + 60 + off, a)
            paste(im, T(a1, 26, fg, "Bold"), 50, y + 60 + off, a, anchor="l")
            paste(im, T(b1, 26, fg, "Bold"), w - 50, y + 60 + off, a, anchor="r")
            paste(im, T(s1, 40, ORANGE, "ExtraBold"), w / 2, y + 60 + off, a)
            y += 136
        elif k == "chat":
            _, side, s = blk
            bw = min(w - 120, tw(s, 24, "SemiBold") + 50)
            x0 = w - 24 - bw if side == "r" else 24
            col = BLUE if side == "r" else ((36, 40, 56) if dark else (226, 230, 245))
            d.rounded_rectangle([x0, y + off, x0 + bw, y + 64 + off], 30, fill=col + (int(255 * a),))
            d.text((x0 + 25, y + 32 + off), s, font=font(24, "SemiBold"), fill=(WHITE if side == "r" or dark else INK) + (int(255 * a),), anchor="lm")
            y += 80
        elif k == "voice":
            d.rounded_rectangle([24, y + off, w - 140, y + 70 + off], 35, fill=(36, 40, 56, int(255 * a)))
            d.ellipse([40, y + 15 + off, 80, y + 55 + off], fill=ORANGE + (int(255 * a),))
            for j in range(26):
                hh = 8 + 24 * abs(math.sin(j * .8 + t * 6))
                x = 100 + j * 12
                d.rounded_rectangle([x, y + 35 - hh / 2 + off, x + 6, y + 35 + hh / 2 + off], 3, fill=(255, 255, 255, int(220 * a)))
            y += 86
        elif k == "file":
            d.rounded_rectangle([w - 300, y + off, w - 24, y + 90 + off], 22, fill=BLUE + (int(255 * a),))
            d.rounded_rectangle([w - 284, y + 16 + off, w - 230, y + 74 + off], 10, fill=(255, 255, 255, int(230 * a)))
            d.text((w - 216, y + 45 + off), "Devis.pdf", font=font(24, "Bold"), fill=(255, 255, 255, int(255 * a)), anchor="lm")
            y += 106
        elif k == "title":
            _, s = blk
            paste(im, T(s, 34, fg, "ExtraBold"), 40, y + 24 + off, a, anchor="l"); y += 64
    return im

def realized(img, x, y, domain, t, t0):
    a = ease(prog(t, t0, t0 + .25))
    if a > 0: paste(img, PILL("Réalisé ✓  " + domain, 26, "light", dot=GREEN), x, y, a, pop(prog(t, t0, t0 + .35)))

# ---------------- scenes (t = absolute voice time)
def sc_search(t):
    img = bgv("swirl", t)
    k = ease5(prog(t, 0, .7))
    def scr(w, h, tt):
        im = Image.new("RGBA", (w, h), (246, 247, 252, 255)); d = ImageDraw.Draw(im)
        d.text((44, 26), "9:41", font=font(24, "SemiBold"), fill=INK)
        paste(im, CARD(w - 40, 84, 42, "light"), w / 2, 140)
        q = "restaurant Banfora"; n = int(len(q) * prog(tt, .2, 1.1))
        d.text((70, 140), q[:n] + ("|" if int(tt * 3) % 2 == 0 else ""), font=font(28, "SemiBold"), fill=INK, anchor="lm")
        for i, (nm, st) in enumerate([("Maquis Le Baobab", "★ 4,6"), ("Restaurant Le Palmier", "★ 4,4"), ("Chez Awa", "★ 4,5"), ("Grill Express", "★ 4,2")]):
            a = ease(prog(tt, 1.3 + i * .15, 1.6 + i * .15))
            if a <= 0: continue
            y = 240 + i * 130
            paste(im, CARD(w - 40, 112, 24, "light"), w / 2 + (1 - a) * 40, y + 56, a)
            d.rounded_rectangle([40, y + 18, 116, y + 94], 18, fill=[ORANGE, BLUE, (40, 160, 120), (150, 90, 200)][i] + (int(255 * a),))
            d.text((136, y + 42), nm, font=font(26, "Bold"), fill=INK + (int(255 * a),), anchor="lm")
            d.text((136, y + 76), st + "  ·  Site web", font=font(20, "SemiBold"), fill=(110, 115, 140, int(255 * a)), anchor="lm")
        return im
    phone(img, W / 2, 900 + (1 - k) * 300, t, 1.05 + .08 * ease(prog(t, 2.2, 3.8)), k, 0, content=scr)
    # INVISIBLE slam
    s = prog(t, 2.55, 2.75)
    if s > 0:
        shake = (1 - prog(t, 2.75, 3.1)) * 14
        dx = math.sin(t * 90) * shake
        g = blur_sp(T("INVISIBLE", 150, RED, "ExtraBold"), 20)
        paste(img, g, W / 2 + dx, 960, ease(s) * .8, lerp(1.6, 1, ease5(s)))
        paste(img, T("INVISIBLE", 150, WHITE, "ExtraBold"), W / 2 + dx, 960, ease(s), lerp(1.6, 1, ease5(s)))
        paste(img, PILL("Votre entreprise : 0 résultat", 30, "dark", dot=RED), W / 2, 1100, ease(prog(t, 2.9, 3.2)))
    return img

def sc_loop(t):
    T0 = A["loop"]; img = bgv("blue", t)
    headline(img, "Restez", 150, 520, t, T0)
    headline(img, "jusqu'à la fin", 110, 660, t, T0 + .35)
    a = ease5(prog(t, A["site"], A["site"] + .5))
    if a > 0:
        laptop(img, W / 2, 1000 + (1 - a) * 200, t, .78, a, "blue", A["site"] + .2)
    b = prog(t, A["pay3"], A["pay3"] + .4)
    if b > 0:
        for i in range(3):
            e = pop(prog(t, A["pay3"] + i * .2, A["pay3"] + i * .2 + .35))
            paste(img, ORB(56, "orange"), W / 2 - 180 + i * 180, 1220, clamp(e), max(e, .01))
            txt(img, ["1", "2", "3"][i], 44, W / 2 - 180 + i * 180, 1214, INK, "ExtraBold", clamp(e))
        paste(img, PILL("Payer en 3 fois  ·  réponse à la fin", 30, "glass", w="Bold"), W / 2, 380, ease(b), pop(b))
    return img

TRADES = [
    ("Restaurant", "🍽", [("hero", (230, 120, 30), "Menu du jour", "Scannez · Commandez"), ("row", "Riz gras", "1 500 F", ORANGE), ("row", "Poulet braisé", "3 000 F", (200, 80, 40)), ("btn", "Commander", "o")], "menusqr.online", False),
    ("Boutique", "🛍", [("title", "Nouveautés"), ("grid", 4, [(40, 75, 235), (255, 145, 25), (30, 30, 50), (120, 90, 220)]), ("btn", "Ajouter au panier", "o")], "maisondesbonneschoses.shop", False),
    ("École", "🎓", [("hero", (40, 75, 235), "Inscriptions", "Année 2026 – 2027"), ("row", "Maths", "16/20", BLUE), ("row", "Français", "14/20", ORANGE), ("btn", "S'inscrire", "b")], "managerschool.online", False),
    ("Média", "📺", [("live",), ("row", "Journal de 20h", "", RED), ("row", "Sport · Culture", "", BLUE)], "evitv.com", True),
    ("Entreprise", "📊", [("title", "Ventes du mois"), ("chart",), ("row", "Stock", "1 248", GREEN), ("row", "Factures", "86", BLUE)], "gestionplus.store", False),
    ("Événement", "🏆", [("hero", (20, 120, 80), "Le tournoi", "Calendrier · Résultats"), ("score", "Équipe A", "Équipe B", "2 – 1"), ("btn", "Voir le classement", "o")], "coupeduronier.com", False),
    ("Institution", "🏛", [("hero", (14, 22, 62), "Bienvenue", "Actualités · Services"), ("row", "Nos missions", "", BLUE), ("row", "Événements", "", ORANGE), ("btn", "Nous contacter", "b")], None, False),
    ("Clinique", "🩺", [("title", "Prendre rendez-vous"), ("cal",), ("row", "Consultation", "10:30", GREEN), ("btn", "Confirmer", "o")], None, False),
]

def sc_trades(t):
    ts = A["trades"]
    i = max(0, min(7, sum(1 for x in ts if t >= x) - 1))
    t0 = ts[i]; name, _, spec, dom, dark = TRADES[i]
    light = i % 2 == 0
    img = bgv("light" if light else "bswirl", t)
    col = INK if light else WHITE
    # counter
    txt(img, "%d / 8" % (i + 1), 34, W / 2, 330, BLUE if light else ORANGE, "Bold", 1)
    # trade name kinetic
    kin(img, name, 130, W / 2, 450, t, t0 - .05, col, d=.3)
    # phone
    e = ease5(prog(t, t0 - .05, t0 + .3))
    phone(img, W / 2 + (1 - e) * 500, 1080, t, .8, 1, (1 - e) * -8, content=lambda w, h, tt: screen(w, h, tt, spec, t0, dark))
    # click ripple
    cp = prog(t, t0 + .45, t0 + .75)
    if 0 < cp < 1:
        lay = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); r = 20 + 70 * cp
        ImageDraw.Draw(lay).ellipse([100 - r, 100 - r, 100 + r, 100 + r], outline=ORANGE + (int(255 * (1 - cp)),), width=5)
        paste(img, lay, W / 2 + 60, 1330)
    paste(img, CURSOR(), W / 2 + 80 - (1 - ease(prog(t, t0 + .2, t0 + .45))) * 150, 1350, ease(prog(t, t0 + .2, t0 + .3)))
    if dom: realized(img, W / 2, 1520 if False else 600, dom, t, t0 + .25)
    return img

def sc_appli(t):
    img = bgv("light", t)
    headline(img, "Son site.", 130, 420, t, A["chaque"] + .3, INK)
    e = ease5(prog(t, A["chaque"], A["chaque"] + .6))
    laptop(img, W / 2 - (ease5(prog(t, A["appli"], A["appli"] + .5))) * 120, 950, t, .82, e, "blue", A["chaque"] + .3)
    b = ease5(prog(t, A["appli"], A["appli"] + .45))
    if b > 0:
        headline(img, "Son appli.", 130, 560, t, A["appli"], BLUE)
        phone(img, W / 2 + 330 + (1 - b) * 400, 1080, t, .55, b, (1 - b) * 10, "blue", A["appli"] + .2)
    return img

def sc_kibaa(t):
    img = bgv("navy", t)
    wave_bars(img, W / 2, 1000, W * 1.1, 300, t, 60, (110, 140, 255), .2, .8)
    k0 = A["kibaa"]
    kin(img, "Kibaa", 150, W / 2, 400, t, k0, WHITE)
    txt(img, "Notre application de messagerie", 34, W / 2, 520, (190, 200, 240), "SemiBold", ease(prog(t, k0 + .4, k0 + .8)))
    spec = [("title", "Discussions"), ("chat", "l", "Salut ! Le projet avance ?"), ("chat", "r", "Oui, maquette prête 👍"),
            ("voice",), ("file",), ("chat", "l", "Parfait, on valide !"), ("chat", "r", "Envoyé ✓✓")]
    e = ease5(prog(t, k0 + .1, k0 + .7))
    phone(img, W / 2, 1110 + (1 - e) * 300, t, .78, e, 0, content=lambda w, h, tt: screen(w, h, tt, spec, k0 + .5, True))
    g = ease(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.0))
    if g > 0:
        sp = PILL("▶  Disponible sur Google Play", 32, "light", w="ExtraBold")
        paste(img, sp, W / 2, 640, g, pop(prog(t, A["kibaa2"] + 1.6, A["kibaa2"] + 2.1)))
        paste(img, PILL("kibaa.online", 26, "glass"), W / 2, 1560, g)
    return img

def sc_sait(t):
    img = bgv("blue", t)
    headline(img, "Votre projet ?", 120, 800, t, A["projet"])
    s = "On sait le faire."
    a = ease(prog(t, A["sait"], A["sait"] + .3))
    if a > 0:
        paste(img, blur_sp(T(s, 120, (140, 170, 255), "ExtraBold"), 16), W / 2, 980, a * .8)
        paste(img, T(s, 120, WHITE, "ExtraBold"), W / 2, 980, a, lerp(1.3, 1, ease5(prog(t, A["sait"], A["sait"] + .4))))
        L = tw(s, 120, "ExtraBold")
        underline(img, W / 2 - L / 2, 1070, L, ease(prog(t, A["sait"] + .3, A["sait"] + .8)), ORANGE, 8)
    return img

def sc_prix(t):
    img = bgv("bswirl", t)
    p0 = A["prix"]
    txt(img, "SITE VITRINE", 40, W / 2, 470, ORANGE, "ExtraBold", ease(prog(t, p0, p0 + .3)), track=8)
    txt(img, "à partir de", 54, W / 2, 560, WHITE, "SemiBold", ease(prog(t, p0 + .2, p0 + .5)))
    v = int(round(50000 * ease5(prog(t, p0 + .6, p0 + 1.8)) / 500) * 500)
    sv = "{:,}".format(v).replace(",", " ")
    a = ease(prog(t, p0 + .6, p0 + .8))
    sc = 1 + .12 * math.sin(math.pi * prog(t, p0 + 1.8, p0 + 2.1))
    paste(img, blur_sp(T(sv + " F", 170, (255, 160, 60), "ExtraBold"), 22), W / 2, 740, a * .6, sc)
    paste(img, T(sv + " F", 170, WHITE, "ExtraBold"), W / 2, 740, a, sc)
    # delivery timeline
    d0 = A["delai"]; b = ease5(prog(t, d0, d0 + .5))
    if b > 0:
        paste(img, CARD(880, 300, 40, "navy", glow=(80, 120, 255)), W / 2, 1100, b)
        txt(img, "Livraison", 34, W / 2 - 380, 1010, (180, 190, 240), "SemiBold", b, "l")
        lay = Image.new("RGBA", (760, 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([0, 14, 759, 26], 6, fill=(255, 255, 255, 50))
        dd.rounded_rectangle([0, 14, max(12, 759 * ease(prog(t, d0 + .4, d0 + 1.6))), 26], 6, fill=ORANGE + (255,))
        paste(img, lay, W / 2, 1100, b)
        txt(img, "1 semaine", 38, W / 2 - 380, 1180, WHITE, "ExtraBold", b, "l")
        txt(img, "1 mois", 38, W / 2 + 380, 1180, WHITE, "ExtraBold", ease(prog(t, d0 + 1.2, d0 + 1.5)), "r")
    return img

STEPS = [("Entretien", "On comprend votre activité", "st1"), ("Cahier des charges", "Validé ensemble", "st2"),
         ("Maquette", "Vous voyez avant de commencer", "st3"), ("Développement", "Toute l'équipe mobilisée", "st4")]

def sc_method(t):
    img = bgv("light", t)
    txt(img, "NOTRE MÉTHODE", 36, W / 2, 360, BLUE, "ExtraBold", ease(prog(t, A["st1"], A["st1"] + .3)), track=8)
    for i, (tt_, sub, key) in enumerate(STEPS):
        t0 = A[key]; a = ease5(prog(t, t0 - .1, t0 + .35))
        y = 520 + i * 200
        if a <= 0:
            paste(img, CARD(900, 160, 36, "light"), W / 2, y, .35); continue
        active = t >= t0 and (i == 3 or t < A[STEPS[i + 1][2]])
        paste(img, CARD(900, 160, 36, "ink" if active else "light", glow=(80, 120, 255) if active else None), W / 2 + (1 - a) * 80, y, a, 1 + .03 * pop(prog(t, t0, t0 + .4)) - .03 if active else 1)
        c = WHITE if active else INK
        paste(img, ORB(34, "orange" if active else "blue"), W / 2 - 370, y, a)
        txt(img, str(i + 1), 34, W / 2 - 370, y - 4, WHITE, "ExtraBold", a)
        txt(img, tt_, 44, W / 2 - 310, y - 24, c, "ExtraBold", a, "l")
        txt(img, sub, 28, W / 2 - 310, y + 30, (190, 200, 240) if active else (100, 105, 140), "SemiBold", a, "l")
        toggle(img, W / 2 + 360, y, ease(prog(t, t0 + .3, t0 + .55)), a, ORANGE)
    return img

def sc_pay(t):
    img = bgv("navy", t)
    headline(img, "Et le paiement ?", 110, 420, t, A["paiement"])
    segs = [(.5, "50 %", "au lancement", A["p50"], BLUE), (.3, "30 %", "à la livraison", A["p30"], (90, 120, 255)), (.2, "20 %", "après 30 jours", A["p20"], ORANGE)]
    x = 90; total = 900
    for frac, lab, sub, t0, col in segs:
        wseg = total * frac
        g = ease5(prog(t, t0, t0 + .5))
        if g > 0:
            lay = Image.new("RGBA", (int(wseg) + 4, 150), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle([0, 0, max(10, (wseg - 8) * g), 149], 26, fill=col + (255,))
            paste(img, lay, x, 760, 1, anchor="l")
            txt(img, lab, 56, x + wseg / 2 - 4, 760, WHITE, "ExtraBold", ease(prog(t, t0 + .2, t0 + .45)), scale=max(.01, pop(prog(t, t0 + .2, t0 + .5))))
            txt(img, sub, 26, x + wseg / 2 - 4, 870, (200, 210, 245), "SemiBold", ease(prog(t, t0 + .3, t0 + .6)))
        x += wseg
    # calendar 30 days
    c = ease(prog(t, A["p20"] + .8, A["p20"] + 1.2))
    if c > 0:
        paste(img, CARD(560, 220, 36, "ink"), W / 2, 1100, c)
        txt(img, "30 jours d'utilisation", 34, W / 2, 1040, WHITE, "Bold", c)
        lay = Image.new("RGBA", (480, 60), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        n = int(30 * ease(prog(t, A["p20"] + 1.0, A["p20"] + 2.2)))
        for j in range(30):
            dd.rounded_rectangle([j * 16, 10, j * 16 + 11, 50], 4, fill=(ORANGE if j < n else (60, 70, 120)) + (255,))
        paste(img, lay, W / 2, 1130, c)
    r = ease(prog(t, A["reste"], A["reste"] + .4))
    if r > 0:
        paste(img, PILL("Vous payez le reste quand ça marche ✓", 32, "light", w="ExtraBold", dot=GREEN), W / 2, 1300, r, pop(prog(t, A["reste"], A["reste"] + .5)))
    return img

PROJ = [("NTIC Solution", "nticsolution.org"), ("MyVivo", "myvivo.online"), ("Menus QR", "menusqr.online"), ("EVI TV", "evitv.com"),
        ("CCGT TV Media", "ccgttvmedia.com"), ("Gestion+", "gestionplus.store"), ("Coupe du Ronier", "coupeduronier.com"),
        ("Tannounyan", "tannounyan.online"), ("MBC", "maisondesbonneschoses.shop"), ("Manager School", "managerschool.online"),
        ("Kibaa", "kibaa.online")]

def sc_wall(t):
    img = bgv("bswirl", t)
    t0 = A["conf"]
    txt(img, "ILS NOUS ONT FAIT CONFIANCE", 34, W / 2, 330, ORANGE, "ExtraBold", ease(prog(t, t0, t0 + .3)), track=5)
    for i, (nm, dom) in enumerate(PROJ + [("Votre projet ici ?", "")]):
        col, row = i % 2, i // 2
        x = W / 2 - 250 + col * 500; y = 470 + row * 150
        a = ease5(prog(t, t0 + i * .07, t0 + i * .07 + .3))
        last = i == len(PROJ)
        if last:
            a = ease5(prog(t, A["case"], A["case"] + .3))
            if a <= 0: continue
            glow = .5 + .5 * math.sin(t * 8)
            paste(img, CARD(470, 128, 30, "blue", glow=ORANGE), x, y, a, 1 + .05 * pop(prog(t, A["votre"], A["votre"] + .4)) * (1 if t > A["votre"] else 0))
            sq = Image.new("RGBA", (470, 128), (0, 0, 0, 0)); ImageDraw.Draw(sq).rounded_rectangle([0, 0, 469, 127], 30, fill=ORANGE + (255,))
            paste(img, sq, x, y, a)
            txt(img, nm, 36, x, y, INK, "ExtraBold", a)
            continue
        if a <= 0: continue
        paste(img, CARD(470, 128, 30, "ink"), x, y + (1 - a) * 30, a)
        txt(img, nm.upper(), 30, x - 205, y - 20 + (1 - a) * 30, WHITE, "ExtraBold", a, "l")
        txt(img, dom, 22, x - 205, y + 22 + (1 - a) * 30, (170, 185, 240), "SemiBold", a, "l")
    return img

def sc_cta(t):
    t0 = A["cta"]
    phase2 = t >= A["cherche"]
    img = bgv("light" if not phase2 else "swirl", t)
    if not phase2:
        txt(img, "Écrivez-nous", 110, W / 2, 520, INK, "ExtraBold", ease(prog(t, t0, t0 + .3)), sm=(1 - ease(prog(t, t0, t0 + .3))) * 80)
        paste(img, CARD(900, 120, 60, "light"), W / 2, 820, ease(prog(t, t0, t0 + .3)))
        m = "Bonjour, je veux mon site !"; n = int(len(m) * prog(t, t0 + .1, t0 + .8))
        txt(img, m[:n], 40, W / 2 - 400, 820, INK, "SemiBold", 1, "l")
        cl = prog(t, t0 + .85, t0 + 1.0)
        paste(img, ORB(44, "blue"), W / 2 + 370, 820, 1, 1 - .15 * math.sin(math.pi * cl))
        paste(img, ICON("send", 40, t), W / 2 + 372, 820, 1)
        if t > t0 + 1.0: paste(img, PILL("Envoyé ✓✓", 28, "orange"), W / 2 + 300, 940, 1, pop(prog(t, t0 + 1.0, t0 + 1.3)))
        return img
    # phase 2: search again, now found
    def scr(w, h, tt):
        im = Image.new("RGBA", (w, h), (246, 247, 252, 255)); d = ImageDraw.Draw(im)
        d.text((44, 26), "9:41", font=font(24, "SemiBold"), fill=INK)
        paste(im, CARD(w - 40, 84, 42, "light"), w / 2, 140)
        d.text((70, 140), "restaurant Banfora", font=font(28, "SemiBold"), fill=INK, anchor="lm")
        a = ease5(prog(tt, A["trouve"] - .3, A["trouve"] + .2))
        paste(im, CARD(w - 40, 150, 26, "blue", glow=ORANGE), w / 2, 280 + (1 - a) * -60, a, 1 + .04 * pop(prog(tt, A["trouve"], A["trouve"] + .4)))
        paste(im, LOGO(90), 90, 280 + (1 - a) * -60, a)
        paste(im, T("Votre entreprise", 32, WHITE, "ExtraBold"), 150, 258 + (1 - a) * -60, a, anchor="l")
        paste(im, T("Site officiel · Commander · WhatsApp", 20, (255, 220, 180), "SemiBold"), 150, 300 + (1 - a) * -60, a, anchor="l")
        for i, nm in enumerate(["Maquis Le Baobab", "Restaurant Le Palmier"]):
            y = 400 + i * 130
            paste(im, CARD(w - 40, 112, 24, "light"), w / 2, y + 56, .7)
            d.text((136, y + 56), nm, font=font(26, "Bold"), fill=(120, 125, 150), anchor="lm")
            d.rounded_rectangle([40, y + 18, 116, y + 94], 18, fill=(200, 205, 220))
        return im
    phone(img, W / 2, 1000, t, 1.0, 1, 0, content=scr)
    a = ease(prog(t, A["trouve"], A["trouve"] + .3))
    if a > 0:
        paste(img, T("TROUVÉ ✓", 130, WHITE, "ExtraBold"), W / 2, 520, a, lerp(1.4, 1, ease5(prog(t, A["trouve"], A["trouve"] + .4))))
    # end card
    e = ease(prog(t, A["trouve"] + .8, A["trouve"] + 1.2))
    if e > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (6, 12, 42, int(235 * e))))
        paste(img, LOGO(230), W / 2, 700, e, pop(prog(t, A["trouve"] + .8, A["trouve"] + 1.3)))
        txt(img, "NTIC SOLUTION", 66, W / 2, 900, WHITE, "ExtraBold", e, track=8)
        txt(img, "Développement web & mobile", 36, W / 2, 975, ORANGE, "Bold", e)
        paste(img, PILL("WhatsApp  +226 69 69 69 24", 40, "orange", w="ExtraBold"), W / 2, 1120, e, pop(prog(t, A["trouve"] + 1.1, A["trouve"] + 1.5)))
    return img

SC = [(0.0, sc_search, "cut"), (A["loop"], sc_loop, "whip"), (A["trades"][0] - .02, sc_trades, "whip"), (A["chaque"], sc_appli, "whip"),
      (A["kibaa"], sc_kibaa, "blur"), (A["projet"], sc_sait, "whip"), (A["prix"], sc_prix, "whip"), (A["st1"], sc_method, "blur"),
      (A["paiement"], sc_pay, "whip"), (A["conf"], sc_wall, "whip"), (A["cta"], sc_cta, "blur")]
FR = [round(s * FPS) for s, _, _ in SC] + [round(A["end"] * FPS)]

_DUST = [(random.Random(i).uniform(0, W), random.Random(i + 99).uniform(0, H), random.Random(i + 7).uniform(1.5, 4.5), random.Random(i + 3).uniform(10, 40)) for i in range(45)]
def dust(img, t, light):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = (90, 120, 255) if light else (200, 215, 255)
    for i, (x, y, r, v) in enumerate(_DUST):
        yy = (y - t * v) % H; xx = x + math.sin(t * .6 + i) * 20
        a = int(100 * (.5 + .5 * math.sin(t * 2 + i)))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=col + (a,))
    img.alpha_composite(lay)

_GR = None
def grain(img, t):
    global _GR
    if _GR is None:
        r = np.random.default_rng(3); _GR = [r.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    g = np.repeat(np.repeat(_GR[int(t * FPS) % 6], 2, 0), 2, 1)[..., None] * 4.0
    return Image.fromarray(np.clip(np.asarray(img).astype(np.float32) + g, 0, 255).astype(np.uint8))

LIGHTFN = {sc_appli, sc_method}
def frame(si, f):
    s0, fn, _ = SC[si]; t = f / FPS
    img = fn(t)
    dust(img, t, fn in LIGHTFN)
    rel = t - FR[si] / FPS; D = (FR[si + 1] - FR[si]) / FPS
    z = 1 + .03 * (rel / D) + .06 * (1 - ease5(prog(rel, 0, .4)))
    cw, ch = W / z, H / z
    img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).convert("RGB")
    return grain(img, t)

def lowsmear(im, amt):
    s = im.resize((W // 3, H // 3), Image.BILINEAR).convert("RGBA")
    s = smear(s, max(2, int(amt / 3)))
    return s.resize((W, H), Image.BILINEAR, box=(s.width / 2 - W / 6, 0, s.width / 2 + W / 6, s.height)).convert("RGB")

TRN = 10
def render(si):
    out = os.path.join(OUTDIR, "seg%02d.mp4" % si)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", out], stdin=subprocess.PIPE)
    tr = SC[si][2]
    prev = frame(si - 1, FR[si] - 1) if si > 0 and tr != "cut" else None
    for f in range(FR[si], FR[si + 1]):
        im = frame(si, f); k = f - FR[si]
        if prev is not None and k < TRN:
            p_ = k / TRN; e = eio(p_); s = math.sin(math.pi * p_)
            if tr == "whip":
                c = Image.new("RGB", (W, H)); c.paste(prev, (int(-e * W), 0)); c.paste(im, (int(W - e * W), 0))
                im = Image.blend(c, lowsmear(c, 220 * s), min(1, s * 1.4))
            else:
                b = Image.blend(prev, im, e)
                sm = b.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
                im = Image.blend(b, sm, s)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        ims = []
        for si in range(len(SC)):
            for fr in (.45, .9):
                f = int(FR[si] + (FR[si + 1] - FR[si]) * fr); ims.append(frame(si, f).resize((216, 384)))
        sh = Image.new("RGB", (216 * 11, 384 * 2))
        for i, im in enumerate(ims): sh.paste(im, ((i // 2) * 216, (i % 2) * 384))
        sh.save(os.path.join(OUTDIR, "preview.png")); sys.exit()
    v2.init_bg()
    with Pool(4) as pool:
        for o in pool.imap_unordered(render, range(len(SC))): print("done", o, flush=True)
    with open(os.path.join(OUTDIR, "list.txt"), "w") as fh:
        for si in range(len(SC)): fh.write("file 'seg%02d.mp4'\n" % si)
    json.dump({"A": A, "starts": [f / FPS for f in FR]}, open(os.path.join(OUTDIR, "timeline.json"), "w"))
