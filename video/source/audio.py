import json, wave, numpy as np
tl=json.load(open('out/timeline.json')); T=tl['total']; starts=tl['starts']; tr=tl['trans']
sr=44100; N=int(T*sr)+sr; t=np.arange(N)/sr; rng=np.random.default_rng(1)
mix=np.zeros(N)
def mtof(m): return 440*2**((m-69)/12)
bpm=112; beat=60/bpm
# chords Am F C G (2 bars each)
chords=[(57,60,64,67),(53,57,60,64),(48,55,60,64),(55,59,62,67)]
bar=4*beat
pad=np.zeros(N); bass=np.zeros(N)
for ci in range(int(T/(2*bar))+2):
    ch=chords[ci%4]; s0=ci*2*bar; s1=s0+2*bar
    i0,i1=int(s0*sr),min(N,int(s1*sr))
    if i0>=N: break
    tt=t[i0:i1]-s0
    env=np.minimum(1,tt/0.4)*np.minimum(1,(2*bar-tt)/0.3)
    for m in ch:
        f=mtof(m)
        for det in (-0.12,0.12):
            for h in range(1,6):
                pad[i0:i1]+=env*np.sin(2*np.pi*f*h*(1+det/100)*tt)/h**1.6*0.05
    f=mtof(ch[0]-24)
    ph=(tt%(beat/2))
    benv=np.exp(-ph*5)*env
    bass[i0:i1]+=benv*(np.sin(2*np.pi*f*tt)+0.3*np.sin(2*np.pi*2*f*tt))*0.28
# start drums after intro (scene 2) ; kick with sidechain
kick=np.zeros(N); hat=np.zeros(N); side=np.ones(N)
dstart=starts[2]; dend=starts[-1]
k=0
while True:
    s=dstart+k*beat
    if s>=dend: break
    i=int(s*sr); L=int(0.35*sr); tt=np.arange(L)/sr
    f=45+90*np.exp(-tt*30); ph=2*np.pi*np.cumsum(f)/sr
    seg=np.sin(ph)*np.exp(-tt*9)*0.9
    e=min(N,i+L); kick[i:e]+=seg[:e-i]
    sc=1-0.6*np.exp(-tt*10); side[i:e]=np.minimum(side[i:e],sc[:e-i])
    hs=s+beat/2; hi=int(hs*sr); HL=int(0.06*sr)
    if hi+HL<N:
        n=rng.standard_normal(HL); n=np.diff(np.concatenate([[0],n]))
        hat[hi:hi+HL]+=n*np.exp(-np.arange(HL)/sr*60)*0.12
    k+=1
mix+=pad*side+bass*side+kick+hat
# whooshes at cuts
def bandnoise(L,lo,hi):
    n=rng.standard_normal(L); F=np.fft.rfft(n); fr=np.fft.rfftfreq(L,1/sr)
    F[(fr<lo)|(fr>hi)]=0; return np.fft.irfft(F,L)
for i,s in enumerate(starts[1:],1):
    L=int(0.7*sr); c=int((s-0.35)*sr)
    if c<0: continue
    tt=np.arange(L)/L
    env=np.sin(np.pi*tt)**3
    w=bandnoise(L,600 if tr[i]=='whip' else 300,7000 if tr[i]=='whip' else 3000)
    w=w/np.abs(w).max()*env*(0.35 if tr[i]=='whip' else 0.22)
    e=min(N,c+L); mix[c:e]+=w[:e-c]
# pops (UI clicks) a few per scene
for s,D in zip(starts,[starts[i+1]-starts[i] for i in range(len(starts)-1)]+[T-starts[-1]]):
    for off in (0.6,1.4,2.8):
        if off<D-0.4:
            i=int((s+off)*sr); L=int(0.05*sr); tt=np.arange(L)/sr
            mix[i:i+L]+=np.sin(2*np.pi*1800*tt*np.exp(-tt*25))*np.exp(-tt*90)*0.18
# impact + riser for outro
o=starts[-1]; L=int(2*sr); tt=np.arange(L)/sr; i=int(o*sr)
boom=(np.sin(2*np.pi*48*tt)*np.exp(-tt*2.5)*0.9+bandnoise(L,40,400)/8*np.exp(-tt*4))
e=min(N,i+L); mix[i:e]+=boom[:e-i]
L=int(1.5*sr); r=bandnoise(L,1000,8000); r=r/np.abs(r).max()*np.linspace(0,1,L)**3*0.3
i=int((o-1.5)*sr); mix[i:i+L]+=r
# master
mix=mix[:int(T*sr)]
fi=int(1.0*sr); mix[:fi]*=np.linspace(0,1,fi); fo=int(2.5*sr); mix[-fo:]*=np.linspace(1,0,fo)
mix=np.tanh(mix*1.1); mix=mix/np.abs(mix).max()*0.89
st=np.stack([mix,mix],1)
with wave.open('out/music.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st*32767).astype(np.int16).tobytes())
print(T)
