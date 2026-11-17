from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess, math
S="src/"
order=["e2d3c827","7ad0d90b","f6f1fdfc","be13f5e7","139e945f","14f98eec","921edb63","68ff68ef","f418397e","4a0dc48c","088692e6","0577c531","9d30d0ce"]
shots=[Image.open(S+o+"-image.jpg").convert("RGB") for o in order]
RED=(226,0,26);YEL=(255,230,0)
F="/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
def font(s): return ImageFont.truetype(F,s)
def phone(img,w):
    sw=w; sh=int(sw*img.height/img.width); b=int(w*0.035); r=int(w*0.12)
    W,H=sw+2*b,sh+2*b
    ph=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ph)
    d.rounded_rectangle((0,0,W-1,H-1),r+b,fill=(18,18,20))
    d.rounded_rectangle((2,2,W-3,H-3),r+b,outline=(70,70,75),width=max(2,b//4))
    sc=img.resize((sw,sh),Image.LANCZOS); m=Image.new("L",(sw,sh),0)
    ImageDraw.Draw(m).rounded_rectangle((0,0,sw-1,sh-1),r,fill=255)
    ph.paste(sc,(b,b),m)
    cx=W//2; d.ellipse((cx-b*0.6,b+b*0.8,cx+b*0.6,b+b*2),fill=(10,10,10))
    return ph
def shadow(bg,ph,x,y):
    P=ph.width//6; s=Image.new("RGBA",(ph.width+2*P,ph.height+2*P),(0,0,0,0))
    a=Image.new("L",s.size,0); a.paste(ph.split()[3].point(lambda v:min(v,110)),(P,P)); s.putalpha(a)
    s=s.filter(ImageFilter.GaussianBlur(ph.width//14))
    bg.alpha_composite(s,(x-P+ph.width//25,y-P+ph.width//12)); bg.alpha_composite(ph,(x,y))
def background(W,H):
    bg=Image.new("RGBA",(W,H),RED); d=ImageDraw.Draw(bg)
    for i in range(H):
        t=i/H; d.line((0,i,W,i),fill=(int(226-60*t),0,int(26+6*t)))
    d.ellipse((-W*0.3,H*0.55,W*0.5,H*1.1),fill=(200,0,22)); d.ellipse((W*0.6,-H*0.1,W*1.3,H*0.3),fill=(240,20,40))
    return bg
def ctext(d,y,t,f,fill,W):
    w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=fill)
def pill(d,y,t,f,W):
    w=d.textlength(t,font=f); h=f.size*1.6; x=(W-w)/2
    d.rounded_rectangle((x-f.size,y,x+w+f.size,y+h),h/2,fill=YEL); d.text((x,y+f.size*0.25),t,font=f,fill=RED)
# ---- POSTER 2160x3840
W,H=2160,3840; bg=background(W,H); d=ImageDraw.Draw(bg)
ctext(d,170,"Speed Lessive",font(190),"white",W)
ctext(d,410,"Votre linge lavé, repassé et rendu impeccable.",font(72),(255,225,225),W)
pill(d,540,"NOUVEAU SITE WEB",font(70),W)
rows=[5,4,4]; pw=360; ph0=phone(shots[0],pw); gx=40; gy=70; y=780; k=0
for n in rows:
    tot=n*ph0.width+(n-1)*gx; x=(W-tot)//2
    for j in range(n):
        p=phone(shots[k],pw); shadow(bg,p,x,y+(30 if j%2 else 0)); x+=p.width+gx; k+=1
    y+=ph0.height+gy
d=ImageDraw.Draw(bg)
pill(d,H-330,"Demandez une lessiveuse en 1 minute",font(80),W)
ctext(d,H-170,"WhatsApp : 70 63 62 51",font(80),"white",W)
bg.convert("RGB").save("affiche_speed_lessive.png"); bg.convert("RGB").save("affiche_speed_lessive.jpg",quality=92)
# ---- VIDEO 1080x1920 15s
W,H,FPS=1080,1920,30; N=15*FPS
base=background(W,H); d=ImageDraw.Draw(base)
ctext(d,110,"Speed Lessive",font(110),"white",W)
ctext(d,250,"Découvrez le nouveau site",font(48),(255,225,225),W)
pill(d,H-250,"WhatsApp : 70 63 62 51",font(52),W)
phones=[phone(s,540) for s in shots]; PW,PH=phones[0].size; py=350
seg=N/13
def ease(t): return t*t*(3-2*t)
p=subprocess.Popen(["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-movflags","+faststart","video_speed_lessive_9x16.mp4"],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
for f in range(N):
    i=int(f//seg); t=(f-i*seg)/seg
    pos=i+ (ease((t-0.7)/0.3) if t>0.7 and i<12 else 0)
    fr=base.copy()
    for j in range(13):
        dx=(j-pos)*(PW+80)
        if abs(dx)>W: continue
        sc=1-0.12*min(1,abs(dx)/(PW+80)); pj=phones[j]
        if sc<0.999: pj=pj.resize((int(PW*sc),int(PH*sc)),Image.BILINEAR)
        x=int(W/2+dx-pj.width/2); y=int(py+(PH-pj.height)/2)
        shadow(fr,pj,x,y) if abs(dx)<10 else fr.alpha_composite(pj,(x,y)) if 0<=x and x+pj.width<=W else fr.paste(pj,(x,y),pj)
    if f<12: fr=Image.blend(Image.new("RGBA",(W,H),RED),fr,f/12)
    p.stdin.write(fr.convert("RGB").tobytes())
p.stdin.close(); p.wait()
