import json,re,sys,os
D='/tmp/supercut'
n=lambda w:re.sub(r'[^a-z0-9\-]','',w.lower())
SRCV={'gpt4':'outcGtbnMuQ','gem2':'Fs0t6SdODd8','op':'CSE77wAdDLg','atlas':'8UWKxJbjriY','work26':'Wq45rvPGNHs','devday26':'Fls_onRviPM','devday23':'U9mJuUkhUzk','io26':'duHhImuaZGU','wwdc26':'hF8swzNR1-o','grok26':'F1_0Lkp16Rc','mistral26':'xr4VUV-7rN0','claude24':'ODaHJzOyVCQ','comet25':'YeldJ4UezDQ','gemera24':'_fuimO6ErKI','gem23':'jV1vkHv4zq8'}
def load(k): return json.load(open(f'{D}/words/{SRCV[k]}.json'))
def cands(k,tok,mn=0.18,mx=0.8):
    w=load(k); out=[]
    for i,x in enumerate(w):
        if n(x['w'])!=tok or not (mn<=x['e']-x['s']<=mx): continue
        gb=x['s']-w[i-1]['e'] if i>0 else 0; ga=(w[i+1]['s']-x['e']) if i+1<len(w) else 0
        ctx=' '.join(y['w'] for y in w[max(0,i-3):i+4])
        out.append((round(gb+ga,2),x['s'],x['e'],ctx))
    out.sort(key=lambda r:-r[0]); return out
if __name__=='__main__':
    toks=sys.argv[1].split(','); keys=sys.argv[2].split(',') if len(sys.argv)>2 else list(SRCV)
    for t in toks:
        print('##',t)
        for k in keys:
            try: c=cands(k,t)
            except Exception: continue
            for r in c[:2]: print(f'  {k:10s} {r[1]:8.2f}-{r[2]:.2f} gap{r[0]:.2f} | {r[3][:60]}')
