import json, wave, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(HERE, "out/timeline.json")))
T = tl["total"]; ST = tl["starts"]; TR = tl["trans"]
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

# ---------------- per-scene events (times relative to scene start; must mirror v2.py animations)
def ev(si, t, x, g=1.0): add(sfx, ST[si] + t, x, g)
# 0 phone
ev(0, 0, whoosh(1.2, 200, 3000), .8)
for k in range(7): ev(0, .5 + k * .2, pop(700 + k * 90), .45)
# 1 typing card
ev(1, 0, whoosh(.4), .5)
typing(ST[1] + .45, len("Votre entreprise\nmérite d'être vue."), .045)
ev(1, 2.3, whoosh(.3, 2000, 8000), .4)
for i, tp in enumerate((2.3, 2.5, 2.7)): ev(1, tp, pop(800 + i * 150), .6)
ev(1, 3.0, scratch()); ev(1, 3.3, scratch()); ev(1, 3.5, ding(1568), .7)
# 2 laptop
ev(2, 0, whoosh(.8, 200, 4000), .8)
for k in range(6): ev(2, .5 + k * .22, pop(600 + k * 110), .45)
ev(2, 1.3, pop(500), .9); ev(2, 2.0, whoosh(.5), .5); ev(2, 2.4, pop(1000), .7)
# 3 kinetic
ev(3, .05, whoosh(.45), 1.0); ev(3, 1.7, swish_out(), .8); ev(3, 1.8, whoosh(.45), 1.0)
ev(3, .4, rise_tone(1.0), .6); ev(3, 2.3, rise_tone(.7), .6)
# 4 light head
ev(4, .05, whoosh(.4), .9); ev(4, .45, whoosh(.4, 800, 7000), .7); ev(4, 1.2, rise_tone(.7), .6); ev(4, 1.9, blip(2200), .6)
# 5 section
ev(5, .15, impact(), .9); ev(5, .2, shimmer(), .8)
# services
def svc_common(si):
    ev(si, 0, whoosh(.35, 300, 4000), .3); ev(si, .15, pop(1100), .8); ev(si, .15, impact(), .45)
def tags_ev(si, t0, n=3):
    for i in range(n): ev(si, t0 + i * .18, pop(900 + i * 120), .55)
svc_common(6)
ev(6, .2, whoosh(.8, 200, 3000), .6)
for k in range(6): ev(6, .6 + k * .22, pop(650 + k * 100), .4)
ev(6, 1.6, whoosh(.6), .6); ev(6, 2.6, pop(1300), .7); tags_ev(6, 2.7)
svc_common(7)
ev(7, .3, whoosh(.5), .5); ev(7, 1.0, pop(1200), .8)
for k in range(4): ev(7, 1.6 + k * .2, blip(1500 + k * 100), .4)
typing(ST[7] + 2.4, 40, .03); ev(7, 3.4, pop(700), .5); tags_ev(7, 3.0)
svc_common(8)
ev(8, .2, servo(.8), .9)
for k in range(8): ev(8, 1.0 + k * .5, blip(2400), .35)
for i in range(3): ev(8, .5, pop(600), .5); ev(8, 2.0 + i * .45, toggle(), .9)
ev(8, 1.0, whoosh(.6), .5)
svc_common(9)
ev(9, .3, whoosh(.5), .5); ev(9, 1.0, whoosh(.5), .5); ev(9, 1.6, pop(1500), .9)
for k in range(20): ev(9, 1.6 + k * .1, click(), .35)
ev(9, 1.6, rise_tone(1.8), .7); tags_ev(9, 2.6)
svc_common(10)
ev(10, .3, whoosh(.45), .8)
for i in range(4): ev(10, 1.0 + i * .12, pop(800 + i * 200), .6)
ev(10, 2.2, swish_out(), .5); ev(10, 2.6, whoosh(.5), .6); ev(10, 2.9, whoosh(.5), .6); tags_ev(10, 3.2)
svc_common(11)
ev(11, .3, whoosh(.5), .5)
for i, s in enumerate(["Bureautique", "Programmation web", "avec l'intelligence artificielle"]):
    typing(ST[11] + 1.0 + i * .8, len(s), .03)
ev(11, 1.0, rise_tone(2.8), .6); ev(11, 3.8, ding(1760), .7)
# 12 stack
for i in range(5): ev(12, .3 + i * .75, whoosh(.3, 1500, 8000), .6); ev(12, .3 + i * .75, pop(700 + i * 140), .7)
# 13 kin2
ev(13, .05, whoosh(.45), 1.0); ev(13, .85, impact(), 1.0); ev(13, 1.6, rise_tone(.8), .6)
# 14 contact
ev(14, .05, whoosh(.45), .8); ev(14, .5, whoosh(.4), .4)
typing(ST[14] + 1.0, len("Bonjour, j'ai un projet digital !"), .043)
ev(14, 2.6, click(), 1.0); ev(14, 2.8, whoosh(.35, 2000, 9000), .8); ev(14, 2.8, ding(2093), .5)
for i in range(4): ev(14, 2.2 + i * .3, toggle(), .8)
# 15 outro
add(sfx, ST[15] - 1.4, riser(1.4), .8)
ev(15, .2, impact(), 1.2); ev(15, 1.4, shimmer(), 1.0); ev(15, 2.5, pop(1200), .6)
# whooshes on every transition
for i in range(1, len(ST)):
    if TR[i] == "whip": add(sfx, ST[i] - .18, whoosh(.45, 600, 7000), .55)
    elif TR[i] == "blur": add(sfx, ST[i] - .25, whoosh(.6, 200, 2500), .35)

# ---------------- voice
dur = json.load(open(os.path.join(HERE, "vo/dur.json")))
for i in range(len(dur)):
    w = wave.open(os.path.join(HERE, "vo/l%02d.wav" % i)); fr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    x = np.interp(np.arange(int(len(x) * sr / fr)) * fr / sr, np.arange(len(x)), x)
    add(voice, ST[i] + .3, x / (np.abs(x).max() + 1e-9) * .95)
# voice presence: gentle high-shelf-ish via adding a bit of derivative
voice = voice + np.concatenate([[0], np.diff(voice)]) * 1.2

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
d0, d1 = ST[1], ST[15] + .2
k = 0
while d0 + k * beat < d1:
    s = d0 + k * beat
    t = tt(.35); kick = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t * 32)) / sr) * np.exp(-t * 8) * .8
    add(music, s, kick)
    if k % 2 == 1: add(music, s, bandnoise(int(.15 * sr), 800, 6000) * np.exp(-tt(.15) * 22) * .25)
    for h in (.5, .25, .75):
        add(music, s + h * beat, bandnoise(int(.04 * sr), 6000, 15000) * np.exp(-tt(.04) * 90) * (.12 if h == .5 else .05))
    k += 1

# ---------------- mix with ducking under voice
env = np.abs(voice); win = int(.12 * sr)
env = np.convolve(env, np.ones(win) / win, "same")
duck = 1 - .6 * np.clip(env / (env.max() * .25 + 1e-9), 0, 1)
mix = music * .55 * duck + sfx * .55 + voice * 1.0
mix = mix[:int(T * sr)]
fi = int(.5 * sr); mix[:fi] *= np.linspace(0, 1, fi)
fo = int(1.2 * sr); mix[-fo:] *= np.linspace(1, 0, fo)
mix = np.tanh(mix * 1.15); mix = mix / np.abs(mix).max() * .93
st = np.stack([mix, mix], 1)
with wave.open(os.path.join(HERE, "out/mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", T)
