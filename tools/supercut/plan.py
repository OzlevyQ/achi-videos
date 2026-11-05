import json, sys
sys.path.insert(0,'/tmp/supercut')
from cands import load, n, SRCV
D='/tmp/supercut'; F=D+'/full1080/'
FPS=30
def sn(x): return round(x*FPS)/FPS
META={ # key: (label, year, yt id)
 'gpt4':('OpenAI · GPT-4 launch','2023'),'gem23':('Google · Gemini 1.0','2023'),'devday23':('OpenAI · DevDay 2023','2023'),
 'gemera24':('Google · Gemini era','2024'),'claude24':('Anthropic · Computer use','2024'),'gem2':('Google · Gemini 2.0','2024'),
 'op':('OpenAI · Operator launch','2025'),'comet25':('Perplexity · Comet','2025'),'atlas':('OpenAI · ChatGPT Atlas launch','2025'),
 'io26':('Google · I/O 2026','2026'),'wwdc26':('Apple · WWDC 2026','2026'),'work26':('OpenAI · ChatGPT Work','2026'),
 'devday26':('OpenAI · DevDay 2026','2026'),'grok26':('xAI · Grok Bot','2026'),'mistral26':('Mistral · Microsoft','2026')}
def path(k): return F+SRCV[k]+'.mp4'
PRE,POST=0.16,0.34
BAD=set()
try: BAD=set(map(tuple,json.load(open(D+'/bad2.json'))))
except Exception: pass
_used={}
def pick(k,tok,nth=None,mn=0.18,mx=0.7):
    w=load(k); hits=[(x['s'],x['e']) for x in w if n(x['w'])==tok and mn<=x['e']-x['s']<=mx and (k,round(x['s'],2)) not in BAD]
    if not hits: print('NO HIT',k,tok); return None
    j=_used.get((k,tok),0) if nth is None else nth
    _used[(k,tok)]=j+1
    return hits[min(j,len(hits)-1)]
def pickfix(k,s,e): return (s,e)
events=[]; audio=[]; t=0.0
def add_ev(kind,dur,**kw):
    global t
    ev=dict(id=len(events),kind=kind,t0=sn(t),dur=sn(dur),**kw); events.append(ev); t=ev['t0']+ev['dur']; return ev
def add_audio(ev,k,s,e,word,onset=None,gain=1.0,pan=0.0,role='word'):
    on=ev['t0'] if onset is None else onset
    ss=max(0.0,s-PRE); dur=(e-ss)+POST
    audio.append(dict(ev=ev['id'],src=path(k),key=k,ss=round(ss,3),dur=round(dur,3),t=round(on-(s-ss),3),gain=gain,pan=pan,word=word,role=role,ws=round(s,3),we=round(e,3)))
def disp(tok): return {'perplexity':'Perplexity','intelligence':'Intelligence','claude':'Claude','computer':'Computer use','ai':'AI','chatgpt':'ChatGPT','gpt-4':'GPT-4','gemini':'Gemini','codex':'Codex','siri':'Siri','openai':'OpenAI'}.get(tok,tok)
def clip(k,tok,dur,nth=None,era=''):
    h=pick(k,tok,nth)
    if not h: return
    ev=add_ev('clip',dur,era=era,year=META[k][1],panels=[dict(src=path(k),key=k,vs=round(h[0],3),word=disp(tok),label=META[k][0],year=META[k][1])])
    add_audio(ev,k,h[0],h[1],disp(tok))
def stack(items,dur,era=''):
    pans=[];hs=[]
    for k,tok in items:
        h=pick(k,tok)
        if h: pans.append(dict(src=path(k),key=k,vs=round(h[0],3),word=disp(tok),label=META[k][0],year=META[k][1])); hs.append((k,tok,h))
    if len(pans)<2: return
    ev=add_ev('stack',dur,era=era,year=pans[0]['year'],panels=pans)
    for i,(k,tok,h) in enumerate(hs): add_audio(ev,k,h[0],h[1],disp(tok),onset=ev['t0']+0.05*i,gain=0.8,pan=(-0.4 if i%2==0 else 0.4))
def card(name,dur,era='',**kw): return add_ev('card',dur,era=era,card=name,**kw)
M={}
# ---- intro + early eras (facts-only text cards)
card('open',1.6,era='intro'); M['intro_end']=t
card('alphago',1.2,era='2016'); card('attention',1.0,era='2017'); card('chatgpt',1.0,era='2022')
M['early_end']=t
# ---- 2023
for k,tok,d in [('gpt4','gpt-4',1.0),('gem23','gemini',0.9),('devday23','chatgpt',0.9),('gpt4','openai',0.8),('devday23','gpt-4',0.8)]: clip(k,tok,d,era='2023')
# ---- 2024
for k,tok,d in [('gemera24','gemini',0.8),('claude24','computer',0.75),('gem2','ai',0.7),('claude24','claude',0.7),('gem2','gemini',0.65)]: clip(k,tok,d,era='2024')
# ---- 2025
for k,tok,d in [('op','agent',0.65),('op','ai',0.6),('atlas','browser',0.55),('op','agents',0.5),('atlas','agent',0.5)]: clip(k,tok,d,era='2025')
card('atlas_retire',0.9,era='2026')
M['fast_start']=t
# ---- 2026 (faster) + first stacks
for k,tok,d in [('io26','gemini',0.5),('wwdc26','siri',0.45),('work26','work',0.45),('devday26','codex',0.45),('grok26','agent',0.4),('mistral26','ai',0.4),('io26','ai',0.4),('work26','chatgpt',0.4)]: clip(k,tok,d,era='2026')
stack([('io26','ai'),('devday26','ai')],0.5,era='collage')
stack([('work26','work'),('grok26','work')],0.5,era='collage')
stack([('devday23','ai'),('atlas','ai'),('gem23','ai')],0.5,era='collage')
stack([('devday26','agents'),('op','agents')],0.45,era='collage')
stack([('gem2','gemini'),('gem23','gemini'),('io26','gemini')],0.45,era='collage')
M['seq_start']=t
# ---- the sentence (each word from a different statement)
SEQ=[('AI','atlas',18.22,18.46),('agents','devday26',156.70,157.32),('will','work26',360.08,360.36),('do','wwdc26',120.22,120.40),('everything','grok26',90.68,91.06),('for you','op',14.88,15.14)]
sw=[s[0] for s in SEQ]
for i,(wd,k,s,e) in enumerate(SEQ):
    ev=add_ev('clip',0.85,era='sentence',year=META[k][1],panels=[dict(src=path(k),key=k,vs=s,word=wd,label=META[k][0],year=META[k][1])],sentence=sw[:i+1],cur=i)
    add_audio(ev,k,s,e,wd,role='sentence')
M['names_start']=t
# ---- flash: company names + overlapping audio collage
names=['OpenAI','Google','Apple','Nvidia','Anthropic','Meta','Microsoft','Perplexity','Mistral','xAI','DeepSeek','Amazon','Grok','Gemini']
pool=[('op','agents'),('atlas','ai'),('wwdc26','intelligence'),('devday26','agents'),('gem2','agents'),('work26','chatgpt'),('claude24','claude'),('op','ai'),('grok26','ai'),('wwdc26','siri'),('devday23','ai'),('atlas','agent'),('io26','gemini'),('gem23','gemini')]
for i,nm in enumerate(names):
    ev=add_ev('card',0.28,era='flash',card='name',text=nm)
    k,tok=pool[i%len(pool)]; h=pick(k,tok)
    if h: add_audio(ev,k,h[0],h[1],disp(tok),gain=0.7+0.3*i/len(names),pan=(-0.5 if i%2 else 0.5),role='flash')
M['black']=t
add_ev('black',1.0,era='silence'); M['vo']=t
add_ev('vo',6.0,era='vo'); M['end']=t
add_ev('end',3.0,era='end')
TOTAL=round(t,3)
json.dump(dict(fps=FPS,W=1080,H=1920,events=events,audio=audio,markers={k:round(v,3) for k,v in M.items()},total=TOTAL,pre=PRE,post=POST),open(D+'/timeline.json','w'),indent=1)
print('events',len(events),'audio',len(audio),'total',TOTAL,M)
