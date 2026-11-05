"""compose.py — renders timeline.json into the supercut.
video: one video-only segment per event (exact frame counts) -> concat (copy)
audio: numpy mix of snippets with pre/post handles (overlapping), bed, VO; hard silence in the black window
"""
import json, os, subprocess, sys, wave, random, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw, ImageFont
FF='/usr/local/bin/ffmpeg'
D='/tmp/supercut'; B=D+'/b2'; os.makedirs(B,exist_ok=True)
T=json.load(open(D+'/timeline.json'))
W,H,FPS=T['W'],T['H'],T['fps']
AMBER=(255,185,56); INK=(14,14,15); WHITE=(255,255,255); MUTED=(170,170,170)
GEIST=D+'/Geist-Variable.ttf'; SERIF='/Users/ozlevy/Projects/humanbrowser/app/assets/fonts/InstrumentSerif-Regular.ttf'; HEB='/System/Library/Fonts/ArialHB.ttc'
SHOTS=os.path.expanduser('~/Projects/achi-marketing/screens/')
def gf(size,bold=False):
    f=ImageFont.truetype(GEIST,size)
    if bold:
        try: f.set_variation_by_name('Bold')
        except Exception: pass
    return f
def tw(d,t,f): b=d.textbbox((0,0),t,font=f); return b[2]-b[0]
def ct(d,t,y,f,fill,stroke=0,cx=W//2):
    d.text((cx-tw(d,t,f)//2,y),t,font=f,fill=fill,stroke_width=stroke,stroke_fill=(0,0,0))
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print('FAIL',' '.join(map(str,cmd))[:400]); print(r.stderr[-600:]); sys.exit(1)
def nfr(dur): return max(1,round(dur*FPS))
ENC=['-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r',str(FPS)]
def grad_overlay():
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for y in range(0,520): d.line([(0,y),(W,y)],fill=(0,0,0,int(150*(1-y/520))))
    for y in range(1350,H): d.line([(0,y),(W,y)],fill=(0,0,0,int(190*((y-1350)/(H-1350)))))
    return im
def clip_overlay(ev,i):
    im=grad_overlay(); d=ImageDraw.Draw(im); p=ev['panels'][0]
    ct(d,p['year'],150,gf(84,True),WHITE+(235,)); ct(d,p['label'],255,gf(38),WHITE+(185,))
    if ev.get('sentence'):
        ws=ev['sentence']; f=gf(56,True); sp=18; wd=[tw(d,w,f) for w in ws]; tot=sum(wd)+sp*(len(ws)-1); x=(W-tot)//2
        for j,w in enumerate(ws):
            d.text((x,1560),w,font=f,fill=(AMBER if j==ev['cur'] else WHITE)+(255,)); x+=wd[j]+sp
    else: ct(d,p['word'],1540,gf(96,True),AMBER+(255,))
    q=f'{B}/ov{i}.png'; im.save(q); return q
def stack_overlay(ev,i):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); n=len(ev['panels']); ph=H//n
    for j,p in enumerate(ev['panels']):
        y0=j*ph
        d.text((36,y0+30),p['year']+'  '+p['label'],font=gf(42,True),fill=WHITE+(245,),stroke_width=5,stroke_fill=(0,0,0))
        ct(d,p['word'],y0+ph-150,gf(90,True),AMBER+(255,),stroke=6)
        if j: d.line([(0,y0),(W,y0)],fill=(14,14,15,255),width=6)
    q=f'{B}/ov{i}.png'; im.save(q); return q
def card_img(ev):
    im=Image.new('RGB',(W,H),INK); d=ImageDraw.Draw(im); c=ev['card']
    if c=='open':
        ct(d,'A supercut of public statements,',860,gf(52),WHITE); ct(d,'2016–2026',940,gf(52,True),AMBER)
    elif c=='alphago':
        ct(d,'2016',690,gf(84,True),WHITE); ct(d,'AlphaGo beats Lee Sedol',830,ImageFont.truetype(SERIF,92),WHITE); ct(d,'4–1 · Google DeepMind · March 2016',990,gf(36),MUTED)
    elif c=='attention':
        ct(d,'2017',700,gf(84,True),WHITE); ct(d,'“Attention Is All You Need”',840,ImageFont.truetype(SERIF,92),WHITE); ct(d,'research paper · arXiv · June 2017',990,gf(36),MUTED)
    elif c=='chatgpt':
        ct(d,'2022',700,gf(84,True),WHITE); ct(d,'ChatGPT',840,ImageFont.truetype(SERIF,110),WHITE); ct(d,'OpenAI announcement · Nov 30, 2022',1010,gf(36),MUTED)
    elif c=='atlas_retire':
        ct(d,'2026',680,gf(84,True),WHITE); ct(d,'OpenAI retires ChatGPT Atlas',820,ImageFont.truetype(SERIF,80),WHITE); ct(d,'announced Jul 9, 2026 · OpenAI help center',980,gf(34),MUTED)
    elif c=='name': ct(d,ev['text'],880,gf(120,True),WHITE)
    return im
def end_img():
    im=Image.new('RGB',(W,H),INK); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(SERIF,300); t='achi'; x=(W-tw(d,t,f)-90)//2
    d.text((x,700),t,font=f,fill=WHITE); r=34; cx=x+tw(d,t,f)+14+r; cy=700+300-62
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=AMBER,width=12)
    ct(d,'Not only a browser. A colleague.',1080,gf(46),WHITE); ct(d,'Waitlist open: achilabs.app',1170,gf(46,True),AMBER)
    ct(d,'Clips show public moments in AI history.',1600,gf(38),(190,190,190)); ct(d,'achi is not affiliated with these companies.',1655,gf(38),(190,190,190))
    return im
vw=json.load(open(D+'/vo_words.json')); VO_OFF=0.3
def vo_sub(phrase,key,screen):
    sc=Image.open(SHOTS+screen).convert('RGB'); h=int(sc.height*W/sc.width); sc=sc.resize((W,h),Image.LANCZOS)
    im=Image.new('RGB',(W,H),INK); im.paste(sc.crop((0,60,W,60+H)),(0,0)); ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    for y in range(1350,H): od.line([(0,y),(W,y)],fill=(0,0,0,int(210*((y-1350)/(H-1350)))))
    im=Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB'); dr=ImageDraw.Draw(im); f=ImageFont.truetype(HEB,68,index=1)
    sp=26; ws=[tw(dr,w[::-1],f) for w in phrase]; tot=sum(ws)+sp*(len(phrase)-1); x=(W+tot)//2
    for i,wd in enumerate(phrase):
        x-=ws[i]; dr.text((x,1560),wd[::-1],font=f,fill=AMBER if wd.strip('.') in key else WHITE); x-=sp
    return im
def render_event(ev):
    i=ev['id']; out=f'{B}/ev{i}.mp4'; N=nfr(ev['dur']); k=ev['kind']
    if k=='clip':
        p=ev['panels'][0]; q=clip_overlay(ev,i)
        fc="[0:v]scale=-2:1920,crop=1080:1920,fps=30,format=yuv420p[v0];[v0][1:v]overlay=0:0,format=yuv420p[v]"
        run([FF,'-v','error','-y','-ss',f"{p['vs']:.3f}",'-i',p['src'],'-loop','1','-i',q,'-filter_complex',fc,'-map','[v]','-frames:v',str(N)]+ENC+[out])
    elif k=='stack':
        ps=ev['panels']; n=len(ps); ph=H//n; q=stack_overlay(ev,i); cmd=[FF,'-v','error','-y']
        for p in ps: cmd+=['-ss',f"{p['vs']:.3f}",'-i',p['src']]
        cmd+=['-loop','1','-i',q]
        fc=';'.join(f'[{j}:v]scale=-2:{ph},crop=1080:{ph},fps=30,setsar=1[p{j}]' for j in range(n))+';'+''.join(f'[p{j}]' for j in range(n))+f'vstack=inputs={n}[v0];[v0][{n}:v]overlay=0:0,format=yuv420p[v]'
        run(cmd+['-filter_complex',fc,'-map','[v]','-frames:v',str(N)]+ENC+[out])
    elif k in('card','end','black'):
        im={'card':lambda:card_img(ev),'end':end_img,'black':lambda:Image.new('RGB',(W,H),(0,0,0))}[k](); q=f'{B}/ci{i}.png'; im.save(q)
        run([FF,'-v','error','-y','-loop','1','-i',q,'-frames:v',str(N)]+['-vf','fps=30,format=yuv420p']+ENC+[out])
    elif k=='vo':
        words=[(w,s+VO_OFF,e+VO_OFF) for w,s,e in vw]; p1_end=words[4][2]+0.35
        cuts=sorted(set([0,round(2.2*FPS)/FPS,round(p1_end*FPS)/FPS,round(4.2*FPS)/FPS,ev['dur']])); scr=[(0,'home.png'),(2.2,'chat.png'),(4.2,'tabs.png')]
        P1=[w for w,_,_ in vw[:5]]; P2=[w for w,_,_ in vw[5:]]; subs=[(0,P1,['סוכן']),(p1_end,P2,['בנינו'])]
        lst=[]
        for j in range(len(cuts)-1):
            a,b=cuts[j],cuts[j+1]; tm=(a+b)/2; s=[x for x in scr if x[0]<=tm][-1][1]; sb=[x for x in subs if x[0]<=tm][-1]
            q=f'{B}/vo{j}.png'; vo_sub(sb[1],sb[2],s).save(q); lst.append((q,b-a))
        txt=''.join(f"file '{q}'\nduration {d:.4f}\n" for q,d in lst)+f"file '{lst[-1][0]}'\n"; open(f'{B}/vo.txt','w').write(txt)
        run([FF,'-v','error','-y','-f','concat','-safe','0','-i',f'{B}/vo.txt','-vf','fps=30,format=yuv420p','-frames:v',str(N)]+ENC+[out])
    return out
def main():
    evs=T['events']
    with cf.ThreadPoolExecutor(4) as ex: outs=list(ex.map(render_event,evs))
    open(B+'/list.txt','w').write(''.join(f"file '{o}'\n" for o in outs))
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',B+'/list.txt','-c','copy',B+'/video.mp4'])
    nfrm=sum(nfr(e['dur']) for e in evs); print('frames',nfrm,'sec',nfrm/FPS)
    audio_mix(nfrm/FPS)
    run([FF,'-v','error','-y','-i',B+'/video.mp4','-i',B+'/mix.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',D+'/achi-supercut-v2.mp4'])
    print('rendered',D+'/achi-supercut-v2.mp4')
SR=48000
def snippet(src,ss,dur):
    r=subprocess.run([FF,'-v','error','-ss',f'{ss:.3f}','-t',f'{dur:.3f}','-i',src,'-vn','-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True)
    return np.frombuffer(r.stdout,dtype=np.float32).astype(np.float64)
def norm_rms(x,target=0.11,lo=0.4,hi=8.0):
    r=np.sqrt(np.mean(x**2)+1e-12); return x*min(hi,max(lo,target/r))
def audio_mix(total):
    N=int(total*SR); L=np.zeros(N); R=np.zeros(N); M=T['markers']
    def put(x,t,pan,gain):
        i=int(round(t*SR)); 
        if i<0: x=x[-i:]; i=0
        n=min(len(x),N-i)
        if n<=0: return
        a=(pan+1)*np.pi/4; L[i:i+n]+=x[:n]*np.cos(a)*gain*1.414; R[i:i+n]+=x[:n]*np.sin(a)*gain*1.414
    def fade(x,fi=0.025,fo=0.08):
        a=int(fi*SR); b=int(fo*SR); x=x.copy()
        if len(x)>a+b: x[:a]*=np.linspace(0,1,a); x[-b:]*=np.linspace(1,0,b)
        return x
    # bed
    def thump(t,amp,f0=55,dec=0.22):
        i=int(t*SR); Ln=int(0.4*SR)
        if i+Ln>=N: return
        x=np.arange(Ln)/SR; y=amp*np.sin(2*np.pi*f0*x)*np.exp(-x/dec); put(y,t,0,1.0)
    t=0.0
    while t<M['fast_start']: thump(t,0.22); t+=1.0
    r=2.0
    while t<M['seq_start']: thump(t,0.2,60,0.12); t+=1.0/r; r=min(6.0,r+0.12)
    while t<M['names_start']: thump(t,0.1,60,0.1); t+=1/6
    nS,nE=int(M['names_start']*SR),int(M['black']*SR); Ln=nE-nS; env=(np.arange(Ln)/Ln)**2
    rng=np.random.default_rng(3); nz=np.diff(rng.standard_normal(Ln),prepend=0); x=np.arange(Ln)/SR
    put(0.14*env*nz+0.26*env*np.sin(2*np.pi*(40+20*env)*x),M['names_start'],0,1.0)
    # speech snippets (handles => overlap)
    for a in T['audio']:
        x=snippet(a['src'],a['ss'],a['dur'])
        if len(x)<100: print('empty',a['word']); continue
        put(fade(norm_rms(x)),a['t'],a['pan'],a['gain']*0.8)
    # VO
    vo=snippet(D+'/vo_will.mp3',0,10); put(norm_rms(vo,0.13),M['vo']+VO_OFF,0,1.0)
    # hard silence in black window
    b0,b1=int(M['black']*SR),int(M['vo']*SR); f=int(0.015*SR)
    for ch in (L,R): ch[b0-f:b0]*=np.linspace(1,0,f); ch[b0:b1]=0
    pk=max(np.abs(L).max(),np.abs(R).max()); sc=0.9/pk if pk>0.9 else 1.0
    st=np.stack([np.tanh(L*sc*1.1)/np.tanh(1.1),np.tanh(R*sc*1.1)/np.tanh(1.1)],axis=1); st=(np.clip(st,-1,1)*32767).astype('<i2')
    w=wave.open(B+'/mix.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
    print('audio peak',round(pk,2),'scale',round(sc,2))
if __name__=='__main__': main()
