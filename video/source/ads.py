import subprocess, os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "out/master169.mp4")
OUT = sys.argv[1]
FD = "/usr/share/fonts/opentype/inter/"
ORANGE = (255, 145, 25); WHITE = (255, 255, 255)
def font(s, w="ExtraBold"): return ImageFont.truetype(FD + "InterDisplay-%s.otf" % w, s)

# caption chunks (source timeline, seconds) aligned on the ElevenLabs voice pauses
CAP = [
    (0.00, 1.06, "Vous venez de vous arrêter ?"), (1.41, 2.03, "Bonne idée."),
    (2.31, 4.36, "Parce que votre entreprise mérite d'être {vue.}"),
    (4.77, 5.43, "Pas par hasard."), (5.63, 7.11, "Avec une vraie {stratégie.}"),
    (7.62, 9.17, "Aujourd'hui, tout se joue en ligne."),
    (9.57, 10.16, "Et vous êtes…"), (10.63, 11.28, "au {bon endroit.}"),
    (11.79, 12.62, "Tout le digital."), (12.88, 13.65, "Une seule {équipe.}"),
    (13.98, 15.31, "Voici nos {6 services.}"),
    (15.73, 17.15, "{Développement web et mobile}"), (17.42, 18.17, "sites vitrines,"),
    (18.30, 19.09, "boutiques en ligne,"), (19.23, 20.71, "applications web et Android."),
    (21.14, 22.36, "{Intelligence artificielle}"), (22.69, 24.42, "des chatbots qui répondent à vos clients,"),
    (24.68, 26.18, "et l'automatisation de vos contenus."),
    (26.60, 27.55, "{Cybersécurité}"), (27.89, 28.32, "audits,"), (28.47, 29.85, "sécurisation de vos serveurs,"),
    (30.09, 31.49, "et supervision de votre réseau."),
    (31.90, 32.92, "{Marketing digital}"), (33.27, 34.33, "community management,"), (34.47, 35.22, "référencement,"),
    (35.33, 36.64, "et publicités sponsorisées."),
    (37.06, 38.00, "{Création graphique}"), (38.29, 39.31, "identité visuelle,"), (39.46, 39.95, "affiches,"),
    (40.10, 41.46, "flyers, et interfaces."),
    (41.85, 43.20, "{Formations en informatique}"), (43.44, 45.10, "bureautique et programmation web,"),
    (45.20, 46.67, "avec l'intelligence artificielle."),
    (47.16, 48.53, "Ils nous font déjà confiance :"), (48.84, 49.27, "CAVOR,"), (49.50, 50.19, "Menu QR,"),
    (50.46, 50.81, "KIBAA,"), (51.03, 51.87, "Faso24.info,"), (52.02, 52.44, "et MyVivo."),
    (52.85, 53.82, "Si c'est digital…"), (54.24, 55.09, "c'est {NTIC.}"),
    (55.48, 56.38, "Parlons de votre {projet.}"), (56.72, 57.74, "Écrivez-nous sur {WhatsApp,}"),
    (57.84, 58.42, "ou appelez-nous."), (58.74, 59.69, "Nous sommes à {Banfora.}"),
    (60.13, 61.01, "{NTIC Solution.}"), (61.44, 62.78, "L'univers du digital."),
]

def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)

def make_ass(path, segs, W, H, marginv, size):
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: %d" % W, "PlayResY: %d" % H, "WrapStyle: 0", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Cap,Inter Display ExtraBold,%d,&H00FFFFFF,&H00FFFFFF,&H00401A0A,&H90000000,0,0,0,0,100,100,0,0,1,7,3,2,70,70,%d,1" % (size, marginv),
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    out_t = 0.0
    for a, b in segs:
        for s0, s1, tx in CAP:
            if s1 <= a or s0 >= b: continue
            st = out_t + max(s0, a) - a; en = out_t + min(s1 + .25, b) - a
            tx = tx.replace("{", "{\\c&H1991FF&}").replace("}", "{\\c&HFFFFFF&}") if "{" in tx else tx
            # fix: ASS override braces – rebuild properly
            raw = [c for c in tx]
            lines.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,{\\fad(60,60)\\t(0,120,\\fscx104\\fscy104)\\t(120,220,\\fscx100\\fscy100)}%s" % (ass_time(st), ass_time(en), fixbraces(tx)))
        out_t += b - a
    open(path, "w").write("\n".join(lines) + "\n")

def fixbraces(tx):
    return tx

def colorize(tx):
    # {word} -> orange
    out = ""; i = 0
    while i < len(tx):
        if tx[i] == "{":
            j = tx.index("}", i); out += "{\\c&H1991FF&}" + tx[i + 1:j] + "{\\c&HFFFFFF&}"; i = j + 1
        else: out += tx[i]; i += 1
    return out

def make_ass2(path, segs, W, H, marginv, size):
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: %d" % W, "PlayResY: %d" % H, "WrapStyle: 0", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Cap,Inter Display ExtraBold,%d,&H00FFFFFF,&H00FFFFFF,&H00401A0A,&H90000000,0,0,0,0,100,100,0,0,1,7,3,2,70,70,%d,1" % (size, marginv),
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    out_t = 0.0
    for a, b in segs:
        for s0, s1, tx in CAP:
            if s1 <= a or s0 >= b: continue
            st = out_t + max(s0, a) - a; en = out_t + min(s1 + .25, b) - a
            lines.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,{\\fad(60,60)\\fscx92\\fscy92\\t(0,140,\\fscx100\\fscy100)}%s" % (ass_time(st), ass_time(en), colorize(tx)))
        out_t += b - a
    open(path, "w").write("\n".join(lines) + "\n")

def overlay_png(path, W, H, hook, vid_box, cta_y):
    """Static branded frame: hook headline on top, brand + CTA bar under the captions."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # hook headline
    y = vid_box[1] - 40
    lines = hook
    fs = 76 if W / H < .7 else 62
    hh = len(lines) * (fs + 14)
    y0 = y - hh
    for i, l in enumerate(lines):
        parts = l.split("|")
        wsum = sum(font(fs).getlength(p) for p in parts)
        x = (W - wsum) / 2
        for k, p in enumerate(parts):
            d.text((x, y0 + i * (fs + 14)), p, font=font(fs), fill=ORANGE if k % 2 else WHITE)
            x += font(fs).getlength(p)
    # brand / CTA bar
    logo = Image.open("/home/user/IPTV/video/logo_ntic.jpg").convert("RGBA").resize((96, 96), Image.LANCZOS)
    m = Image.new("L", (96, 96), 0); ImageDraw.Draw(m).ellipse([3, 3, 93, 93], fill=255); logo.putalpha(m)
    bar_w = W - 120; bx = 60
    S = 2
    bar = Image.new("RGBA", (bar_w * S, 140 * S), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle([0, 0, bar_w * S - 1, 140 * S - 1], 70 * S, fill=(10, 18, 60, 235), outline=(110, 150, 255, 160), width=3 * S)
    bar = bar.resize((bar_w, 140), Image.LANCZOS)
    im.alpha_composite(bar, (bx, cta_y))
    im.alpha_composite(logo, (bx + 22, cta_y + 22))
    d.text((bx + 136, cta_y + 30), "NTIC Solution", font=font(40), fill=WHITE)
    d.text((bx + 136, cta_y + 78), "WhatsApp +226 69 69 69 24", font=font(30, "SemiBold"), fill=ORANGE)
    # button
    bw = 210 if W > 1000 else 190
    b = Image.new("RGBA", (bw * S, 76 * S), (0, 0, 0, 0)); ImageDraw.Draw(b).rounded_rectangle([0, 0, bw * S - 1, 76 * S - 1], 38 * S, fill=ORANGE + (255,))
    b = b.resize((bw, 76), Image.LANCZOS); im.alpha_composite(b, (bx + bar_w - bw - 32, cta_y + 32))
    d.text((bx + bar_w - bw / 2 - 32, cta_y + 70), "Nous écrire", font=font(28), fill=(14, 22, 62), anchor="mm")
    im.save(path)

def navy_bg(path, W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .42) / H) ** 2)
    k = np.clip(1 - r * 1.5, 0, 1)[..., None]
    base = np.array([6, 12, 42]) + np.array([22, 42, 130]) * k
    grid = ((xx % 54 < 1.5) | (yy % 54 < 1.5))[..., None] * 12 * (0.4 + k)
    Image.fromarray(np.clip(base + grid, 0, 255).astype(np.uint8)).save(path)

def build(name, segs, W, H, hook, vid_w, vid_cy, cap_marginv, cap_size, cta_y):
    vid_h = int(vid_w * 9 / 16) // 2 * 2
    vx = 0; vy = int(vid_cy - vid_h / 2)
    crop_w = W
    ovl = os.path.join(OUT, name + "_ovl.png"); ass = os.path.join(OUT, name + ".ass")
    overlay_png(ovl, W, H, hook, (0, vy, W, vy + vid_h), cta_y)
    bgp = os.path.join(OUT, name + "_bg.png"); navy_bg(bgp, W, H)
    make_ass2(ass, segs, W, H, cap_marginv, cap_size)
    # trim + concat source segments
    parts = []; fc = ""
    for i, (a, b) in enumerate(segs):
        fc += "[0:v]trim=%f:%f,setpts=PTS-STARTPTS[v%d];[0:a]atrim=%f:%f,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st=%f:d=0.06[a%d];" % (a, b, i, a, b, max(0, b - a - .06), i)
        parts.append("[v%d][a%d]" % (i, i))
    fc += "".join(parts) + "concat=n=%d:v=1:a=1[v][a];" % len(segs)
    fc += ("[v]split[va][vb];"
           "[va]nullsink;[2:v]copy[bg];"
           "[vb]scale=%d:-2,crop=%d:%d[fg];"
           "[bg][fg]overlay=(W-w)/2:%d:shortest=1[c1];"
           "[c1][1:v]overlay=0:0[c2];"
           "[c2]ass=%s:fontsdir=%s[out]") % (vid_w, W, vid_h, vy, ass, FD)
    dst = os.path.join(OUT, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", ovl, "-loop", "1", "-i", bgp, "-filter_complex", fc, "-map", "[out]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "slow", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
                    "-r", "30", "-shortest", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst], check=True)
    return dst

FULL = [(0, 65.5)]
HOOK15 = [(0, 7.62), (52.85, 65.5)]
SERV = [(11.79, 52.85), (60.13, 65.5)]

if __name__ == "__main__":
    # 9:16 Reels / Stories  (keep key text between y=250 and y=1340: Reels UI covers the bottom)
    V = dict(W=1080, H=1920, vid_w=1200, vid_cy=830, cap_marginv=640, cap_size=64, cta_y=1385)
    print(build("NTIC_Reels_9x16_complete_65s", FULL, hook=["Votre entreprise", "mérite d'être |vue|."], **V))
    print(build("NTIC_Reels_9x16_accroche_20s", HOOK15, hook=["Vous venez de", "vous |arrêter| ?"], **V))
    print(build("NTIC_Reels_9x16_services_46s", SERV, hook=["Tout le |digital|,", "une seule équipe."], **V))
    # 4:5 Feed
    F = dict(W=1080, H=1350, vid_w=1200, vid_cy=600, cap_marginv=330, cap_size=54, cta_y=1150)
    print(build("NTIC_Feed_4x5_complete_65s", FULL, hook=["Tout le |digital|, une seule équipe."], **F))
