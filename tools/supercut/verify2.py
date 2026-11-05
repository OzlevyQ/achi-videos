import json,re,subprocess,os,time,difflib
env=dict(l.strip().split('=',1) for l in open(os.path.expanduser('~/loom/engines.env')) if '=' in l and not l.startswith('#'))
K=env['GROQ_API_KEY'].strip().strip('"').strip("'")
D='/tmp/supercut'; B=D+'/b2v'; os.makedirs(B,exist_ok=True)
T=json.load(open(D+'/timeline.json')); FF='/usr/local/bin/ffmpeg'
norm=lambda w:re.sub(r'[^a-z0-9]','',w.lower())
sil=B+'/sil.wav'
if not os.path.exists(sil): subprocess.run([FF,'-v','error','-y','-f','lavfi','-t','0.5','-i','anullsrc=r=16000:cl=mono',sil],check=True)
def tx(o):
    for tr in range(4):
        r=subprocess.run(['curl','-s','https://api.groq.com/openai/v1/audio/transcriptions','-H',f'Authorization: Bearer {K}','-F',f'file=@{o}','-F','model=whisper-large-v3-turbo','-F','language=en','-F','temperature=0'],capture_output=True,text=True).stdout
        try: t=json.loads(r).get('text','')
        except Exception: t=''
        if t.strip(): return t
        time.sleep(8)
    return ''
res=[]; bad=json.load(open(D+'/bad2.json')) if os.path.exists(D+'/bad2.json') else []
for i,a in enumerate(T['audio']):
    w=f'{B}/a{i}.wav'
    subprocess.run([FF,'-v','error','-y','-ss',str(a['ss']),'-t',str(a['dur']),'-i',a['src'],'-vn','-ar','16000','-ac','1',w],check=True)
    open(f'{B}/a{i}.txt','w').write(''.join(f"file '{x}'\n" for x in [sil,w,sil,w,sil,w,sil]))
    o=f'{B}/a{i}.mp3'; subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i',f'{B}/a{i}.txt','-b:a','48k',o],check=True)
    t=tx(o); time.sleep(1.2)
    exp=[norm(x) for x in a['word'].split()]; exp=[e for e in exp if e]
    if a['word']=='Computer use': exp=['computer']
    if a['word']=='for you': exp=['for','you']
    toks=[norm(x) for x in t.split()]
    def match(e):
        if e=='chatgpt' and any(x.startswith('cha') and len(x)>=4 or 'gpt' in x or 'gbt' in x for x in toks): return True
        return any(difflib.SequenceMatcher(None,e,x).ratio()>=0.75 or (len(e)>2 and x and (e in x or x in e)) for x in toks) or e in norm(t)
    ok=any(match(e) for e in exp) if a['role']!='sentence' or len(exp)==1 else all(match(e) for e in exp)
    res.append(dict(i=i,t=a['t'],word=a['word'],ok=ok,heard=t.strip()[:70],key=a['key'],ws=a['ws'],role=a['role']))
    print(('OK  ' if ok else 'MISS'),round(a['t'],2),a['word'],'|',t.strip()[:70],flush=True)
    if not ok and a['role']!='sentence' and [a['key'],round(a['ws'],2)] not in bad: bad.append([a['key'],round(a['ws'],2)])
json.dump(res,open(D+'/verify2.json','w'),ensure_ascii=False); json.dump(bad,open(D+'/bad2.json','w'))
print('OK',sum(r['ok'] for r in res),'of',len(res))
