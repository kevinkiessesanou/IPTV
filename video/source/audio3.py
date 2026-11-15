import json, wave, os, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(HERE, "out3/timeline.json")))
A = tl["A"]; ST = tl["starts"]; T = ST[-1]
sr = 44100; N = int(T * sr) + sr
rng = np.random.default_rng(7)
music = np.zeros(N); sfx = np.zeros(N); voice = np.zeros(N)
def add(buf, t0, x, g=1.0):
    i = int(t0 * sr)
    if i < 0: x = x[-i:]; i = 0
    e = min(N, i + len(x)); buf[i:e] += x[:e - i] * g
def bandnoise(L, lo, hi):
    n = rng.standard_normal(L); F = np.fft.rfft(n); fr = np.fft.rfftfreq(L, 1 / sr)
    F[(fr < lo) | (fr > hi)] = 0; x = np.fft.irfft(F, L); return x / (np.abs(x).max() + 1e-9)
def tt(d): return np.arange(int(d * sr)) / sr
# ---------------- SFX library
def whoosh(d=.5, lo=500, hi=6000):
    t = tt(d); u = t / d; env = (np.sin(np.pi * u) ** 2) * (u < 1)
    x = bandnoise(len(t), lo, hi)
    # sweeping tone underneath
    f = 200 + 900 * u; tone = np.sin(2 * np.pi * np.cumsum(f) / sr) * .15
    return (x + tone) * env * .9
def swish_out(): return whoosh(.32, 1500, 9000)
def pop(f=900):
    t = tt(.09); fr = f * (1 + 1.5 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-t * 45)
def click():
    t = tt(.025); return bandnoise(len(t), 2000, 9000) * np.exp(-t * 300) * .8
def key():
    t = tt(.04); f = rng.uniform(2500, 4000)
    return (bandnoise(len(t), 1500, 7000) * .6 + np.sin(2 * np.pi * f * t) * .3) * np.exp(-t * 160) * rng.uniform(.6, 1)
def toggle():
    return np.concatenate([click(), np.zeros(int(.03 * sr)), pop(1400) * .7])
def ding(f=1320):
    t = tt(1.0); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.01 * t) + .2 * np.sin(2 * np.pi * f * 3.02 * t)) * np.exp(-t * 4) * .5
def impact():
    t = tt(1.6)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-t * 18)) / sr) * np.exp(-t * 2.6)
    return sub * 1.1 + bandnoise(len(t), 60, 3000) * np.exp(-t * 9) * .5
def riser(d=1.4):
    t = tt(d); u = t / d
    f = 200 * 2 ** (3 * u); tone = np.sin(2 * np.pi * np.cumsum(f) / sr) * .25
    return (bandnoise(len(t), 1000, 9000) * .6 + tone) * u ** 3
def blip(f=1800):
    t = tt(.07); return np.sin(2 * np.pi * f * t) * np.exp(-t * 50) * .5
def rise_tone(d):
    t = tt(d); u = t / d; f = 300 * 2 ** (2 * u)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * .18 * np.sin(np.pi * u) ** .5
def scratch():
    t = tt(.18); return bandnoise(len(t), 800, 5000) * np.exp(-t * 14) * .5
def servo(d=.6):
    t = tt(d); f = 140 + 60 * np.sin(t * 30)
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / sr)) * .08 + bandnoise(len(t), 300, 2000) * .15) * np.sin(np.pi * t / d)
def shimmer():
    t = tt(1.2); x = np.zeros(len(t))
    for f in (2093, 2637, 3136, 4186): x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * 3)
    return x * .12 * np.minimum(1, t * 30)

def typing(t0, n, rate):
    for i in range(n): add(sfx, t0 + i * rate + rng.uniform(-.006, .006), key(), .55)


def E(t, x, g=1.0): add(sfx, t, x, g)
def typing(t0, n, rate):
    for i in range(n): E(t0 + i * rate + rng.uniform(-.006, .006), key(), .55)
# 0 search
typing(.2, 18, .05)
for i in range(4): E(1.3 + i * .15, pop(700 + i * 120), .5)
E(2.35, riser(.3), .6); E(2.55, impact(), 1.3); E(2.55, bandnoise(int(.25 * sr), 200, 4000) * np.exp(-tt(.25) * 10), .8)
E(2.9, pop(500), .6)
# loop
E(A["loop"], whoosh(.4), 1.0); E(A["loop"] + .35, whoosh(.4, 900, 8000), .7)
E(A["site"], whoosh(.6, 200, 3000), .6)
for k in range(6): E(A["site"] + .2 + k * .22, pop(650 + k * 100), .35)
for i in range(3): E(A["pay3"] + i * .2, ding(1046 * (1.26 ** i)), .35); E(A["pay3"] + i * .2, pop(900 + i * 200), .7)
# trades
for i, t0 in enumerate(A["trades"]):
    E(t0 - .05, whoosh(.3, 1000, 8000), .7); E(t0 + .05, pop(700 + i * 90), .6); E(t0 + .45, click(), 1.0)
E(A["chaque"], whoosh(.6, 200, 4000), .7)
for k in range(6): E(A["chaque"] + .3 + k * .22, pop(650 + k * 100), .35)
E(A["appli"], whoosh(.45), .8); E(A["appli"] + .2, pop(1200), .6)
# kibaa
E(A["kibaa"], impact(), .6); E(A["kibaa"], whoosh(.4), .8)
for k in range(7): E(A["kibaa"] + .5 + k * .12, blip(1500 + k * 120), .45)
E(A["kibaa2"] + 1.6, ding(1568), .6); E(A["kibaa2"] + 1.6, pop(1100), .8)
# sait
E(A["projet"], whoosh(.4), .9); E(A["sait"], impact(), 1.1); E(A["sait"] + .3, rise_tone(.5), .6)
# prix
E(A["prix"], whoosh(.4), .7)
for k in range(24): E(A["prix"] + .6 + k * .05 * (1 + k / 24), click(), .5)
E(A["prix"] + 1.8, impact(), 1.0); E(A["prix"] + 1.8, shimmer(), .8)
E(A["delai"], whoosh(.4), .6); E(A["delai"] + .4, rise_tone(1.2), .6); E(A["delai"] + 1.6, pop(1300), .7)
# method
for k in ("st1", "st2", "st3", "st4"):
    E(A[k] - .1, whoosh(.3, 1500, 8000), .6); E(A[k], pop(900), .7); E(A[k] + .3, toggle(), .9)
# pay
E(A["paiement"], whoosh(.4), .9)
for i, k in enumerate(("p50", "p30", "p20")): E(A[k], rise_tone(.5), .6); E(A[k] + .2, pop(800 + i * 250), .9)
for k in range(12): E(A["p20"] + 1.0 + k * .1, click(), .4)
E(A["reste"], ding(1760), .8); E(A["reste"], pop(1200), .8)
# wall
for i in range(11): E(A["conf"] + i * .07, pop(600 + i * 60), .4)
E(A["case"], riser(.6), .5); E(A["votre"], impact(), .9); E(A["votre"], shimmer(), .7)
# cta
E(A["cta"], whoosh(.4), .8); typing(A["cta"] + .1, 27, .026)
E(A["cta"] + .85, click(), 1.0); E(A["cta"] + 1.0, whoosh(.35, 2000, 9000), .8); E(A["cta"] + 1.0, ding(2093), .5)
E(A["cherche"], whoosh(.5, 200, 3000), .8); E(A["trouve"] - .3, riser(.3), .6); E(A["trouve"], impact(), 1.2); E(A["trouve"], ding(1568), .6)
E(A["trouve"] + .8, shimmer(), 1.0)
for s0 in ST[1:-1]: E(s0 - .18, whoosh(.45, 600, 7000), .45)
# voice
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.environ["ELVOICE"], "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
add(voice, 0.0, x / (np.abs(x).max() + 1e-9) * .95)
# ---------------- music (energetic, 118 bpm)
bpm = 118; beat = 60 / bpm; bar = 4 * beat
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
chords = [(57, 60, 64, 67), (53, 57, 60, 64), (48, 55, 60, 64), (55, 59, 62, 67)]
tg = np.arange(N) / sr
for ci in range(int(T / bar) + 2):
    ch = chords[(ci // 2) % 4]; s0 = ci * bar
    i0, i1 = int(s0 * sr), min(N, int((s0 + bar) * sr))
    if i0 >= N: break
    t = tg[i0:i1] - s0
    env = np.minimum(1, t / .3) * np.minimum(1, (bar - t) / .2)
    for m in ch:
        for det in (-.15, .15):
            for h in range(1, 5): music[i0:i1] += env * np.sin(2 * np.pi * mtof(m) * h * (1 + det / 100) * t) / h ** 1.7 * .03
    # 16th arpeggio pluck
    for k in range(16):
        st = k * beat / 4; m = ch[[0, 1, 2, 3, 2, 1, 3, 2][k % 8]] + 12
        a = int((s0 + st) * sr); L = int(.18 * sr)
        if a + L >= N: continue
        pt = np.arange(L) / sr
        music[a:a + L] += np.sin(2 * np.pi * mtof(m) * pt) * np.exp(-pt * 22) * .06
    # bass on 8ths
    for k in range(8):
        a = int((s0 + k * beat / 2) * sr); L = int(beat / 2 * sr)
        if a + L >= N: continue
        pt = np.arange(L) / sr; f = mtof(ch[0] - 24)
        music[a:a + L] += (np.sin(2 * np.pi * f * pt) + .35 * np.sin(4 * np.pi * f * pt)) * np.exp(-pt * 6) * .22
# drums from scene 1 to outro, kick + clap + hats
d0, d1 = A["loop"], A["trouve"] + .2
k = 0
while d0 + k * beat < d1:
    s = d0 + k * beat
    t = tt(.35); kick = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t * 32)) / sr) * np.exp(-t * 8) * .8
    add(music, s, kick)
    if k % 2 == 1: add(music, s, bandnoise(int(.15 * sr), 800, 6000) * np.exp(-tt(.15) * 22) * .25)
    for h in (.5, .25, .75):
        add(music, s + h * beat, bandnoise(int(.04 * sr), 6000, 15000) * np.exp(-tt(.04) * 90) * (.12 if h == .5 else .05))
    k += 1


env = np.abs(voice); win = int(.12 * sr); env = np.convolve(env, np.ones(win) / win, "same")
duck = 1 - .6 * np.clip(env / (env.max() * .25 + 1e-9), 0, 1)
mix = music * .45 * duck + sfx * .5 + voice
mix = mix[:int(T * sr)]
fo = int(1.0 * sr); mix[-fo:] *= np.linspace(1, 0, fo)
mix = np.tanh(mix * 1.15); mix = mix / np.abs(mix).max() * .93
st = np.stack([mix, mix], 1)
with wave.open(os.path.join(HERE, "out3/mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", T)
