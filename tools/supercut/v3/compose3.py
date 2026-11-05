"""compose3.py — achi supercut v3
trump (UN WebTV, real audio) -> time tunnel (html) -> chaos (v2 events + time-travel fx) -> boom -> silence -> finale (html: VO via Instinct, app in motion, end card)
video: every segment is video-only, concatenated and encoded once; audio: numpy mix, one AAC encode.
usage: compose3.py   (reads v3/cfg.json)"""
import json, os, subprocess, sys, wave, concurrent.futures as cf
import numpy as np
FF = '/usr/local/bin/ffmpeg'
D = '/tmp/supercut'; V3 = D + '/v3'; B = V3 + '/b'; os.makedirs(B, exist_ok=True)
CFG = json.load(open(V3 + '/cfg.json'))
T = json.load(open(D + '/timeline.json')); FPS = 30; SR = 48000
GEIST = D + '/Geist-Variable.ttf'
def run(cmd, quiet=False):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print('FAIL', ' '.join(map(str, cmd))[:500]); print(r.stderr[-800:]); sys.exit(1)
    return r
def nfr(d): return max(1, round(d * FPS))
ENC = ['-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', str(FPS)]

# ------------------------------------------------------------------ timeline of the whole video
DT0 = CFG['tr_end'] - CFG['tr_start']; SLOW = 2.4; DT = DT0 + SLOW   # trump clip + slow-mo SI
TUN = 3.4; RW = 1.0
evs = T['events']; M = T['markers']
first = [e for e in evs if e['kind'] != 'card' or e.get('era') != 'intro'][0]   # first event after the open card
K = 0.78; F0 = first['t0']
sc = lambda t: F0 + (t - F0) * K
chaos_evs = [dict(e, t0=sc(e['t0']), dur=e['dur'] * K) for e in evs if e['t0'] >= F0 and e['t0'] < M['black'] - 1e-6]
M = {k: (sc(v) if isinstance(v, (int, float)) and v >= F0 else v) for k, v in M.items()}
for a in T['audio']: a['t'] = sc(a['t'])
CH0 = DT + RW + TUN; shift = CH0 - F0
CHL = M['black'] - first['t0']; CH1 = CH0 + CHL
BOOM = 1.4; FIN0 = CH1 + BOOM; FINL = 18.6; TOTAL = FIN0 + FINL
print('trump', DT, 'tunnel', TUN, 'chaos', round(CHL, 2), 'boom', BOOM, 'finale', FINL, 'TOTAL', round(TOTAL, 2))

# ------------------------------------------------------------------ video segments
def seg_trump():
    out = B + '/trump.mp4'; N = nfr(DT); si = CFG['si_rel']
    base = CFG['tr_start']              # offset of audio start inside un_seg.mp4
    s2 = CFG['slow_start']; sd = CFG['slow_dur']; k = SLOW / sd
    fc = (f"[0:v]split=2[a0][b0];[a0]trim=start={base}:end={base+DT0},setpts=PTS-STARTPTS[p1];"
          f"[b0]trim=start={s2}:end={s2+sd},setpts=(PTS-STARTPTS)*{k:.4f}[p2];"
          f"[p1][p2]concat=n=2:v=1:a=0,fps=30,scale=-2:1920,crop=1080:1920,eq=contrast=1.08:saturation=1.1,"
          f"scale=w='ceil(1080*(1+0.06*t/{DT})/2)*2':h=-2:eval=frame,crop=1080:1920,"
          f"drawbox=x=0:y=0:w=1080:h=420:color=black@0.45:t=fill,drawbox=x=0:y=1320:w=1080:h=600:color=black@0.55:t=fill,format=yuva420p[a];"
          f"[a][1:v]overlay=0:0[b];[b][2:v]overlay=0:0:enable='gte(t,{si})',"
          f"fade=t=out:st={DT-0.12:.2f}:d=0.12:color=white,format=yuv420p[v]")
    run([FF, '-v', 'error', '-y', '-i', V3 + '/trump/un_seg2.mp4', '-i', V3 + '/ov_cap.png', '-i', V3 + '/ov_si.png', '-filter_complex', fc, '-map', '[v]', '-frames:v', str(N)] + ENC + [out]); return out

YR = {'2016': (0.55, 14), '2017': (0.55, 14), '2022': (0.7, 10), '2023': (0.85, 6), '2024': (0.95, 3), '2025': (1.05, 0), '2026': (1.08, 0)}
def render_fx(ev):
    i = ev['id']; src = f'{D}/b2/ev{i}.mp4'; out = f'{B}/fx{i}.mp4'; N = nfr(ev['dur']); era = str(ev.get('era', ''))
    sat, gr = YR.get(era, YR.get(str(ev.get('year', '')), (1.05, 0)))
    slow = 0.05 if ev['kind'] == 'card' and era != 'flash' else 0.0
    punch = 0.22 if era != 'flash' else 0.12
    jit = ",crop=1080:1920:x='54+14*sin(n*2.3)':y='96+16*cos(n*1.9)'" if era == 'flash' else ',crop=1080:1920'
    pre = f"scale=w='ceil(1080*(1.0{'+0.09' if era=='flash' else ''}+{punch}*pow(max(0,1-t/0.30),2)+{slow}*n/{N})/2)*2':h=-2:eval=frame{jit}"
    gradef = f"eq=saturation={sat}" + (f",noise=alls={gr}:allf=t" if gr else '')
    fc = (f"[0:v]{pre},rgbashift=rh=-16:bh=16:enable='lt(t,0.26)',{gradef},format=yuv420p[a];"
          f"[a]fade=t=in:st=0:d=0.07:color=white,format=yuv420p[v]")
    run([FF, '-v', 'error', '-y', '-i', src, '-filter_complex', fc, '-map', '[v]', '-frames:v', str(N)] + ENC + [out])
    return out

def seg_rewind():
    out = B + '/rewind.mp4'; N = nfr(RW)
    fc = ("[0:v]reverse,setpts=PTS/9,fps=30,scale=-2:1920,crop=1080:1920,eq=contrast=1.15:saturation=0.7,"
          "rgbashift=rh=-18:bh=18,noise=alls=40:allf=t,"
          "geq=lum='lum(X,Y)*(0.82+0.18*sin(Y*1.6))':cb='cb(X,Y)':cr='cr(X,Y)',"
          "crop=1080:1920:x='30*sin(n*1.7)*(1+sin(n*0.31))':y=0,"
          "drawbox=x=0:y='mod(t*4000,1900)':w=1080:h=70:color=white@0.35:t=fill,format=yuva420p[a];"
          "[a][1:v]overlay=0:0:enable='lt(mod(t,0.3),0.2)',format=yuv420p[v]")
    run([FF, '-v', 'error', '-y', '-ss', '2.0', '-i', V3 + '/trump/un_seg2.mp4', '-i', V3 + '/ov_rew.png', '-filter_complex', fc, '-map', '[v]', '-frames:v', str(N)] + ENC + [out]); return out

def seg_boom():
    out = B + '/boom.mp4'; N = nfr(BOOM)
    fc = f"color=c=white:s=1080x1920:r=30:d={BOOM},fade=t=out:st=0.05:d=0.45:color=black,format=yuv420p[v]"
    run([FF, '-v', 'error', '-y', '-f', 'lavfi', '-i', f"color=c=white:s=1080x1920:r=30:d={BOOM}", '-vf', "fade=t=out:st=0.05:d=0.45:color=black,format=yuv420p", '-frames:v', str(N)] + ENC + [out]); return out

def video():
    with cf.ThreadPoolExecutor(4) as ex:
        fx = list(ex.map(render_fx, chaos_evs))
    parts = [seg_trump(), seg_rewind(), V3 + '/tunnel.mp4'] + fx + [seg_boom(), V3 + '/finale.mp4']
    open(B + '/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', B + '/list.txt', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', '30', B + '/video.mp4'])
    n = sum(nfr(DT) for _ in [0]) + nfr(RW) + nfr(TUN) + sum(nfr(e['dur']) for e in chaos_evs) + nfr(BOOM) + nfr(FINL)
    print('video frames', n, 'sec', n / FPS)
    return n / FPS

# ------------------------------------------------------------------ audio
rng = np.random.default_rng(7)
def snippet(src, ss, dur):
    r = subprocess.run([FF, '-v', 'error', '-ss', f'{ss:.3f}', '-t', f'{dur:.3f}', '-i', src, '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
def norm_rms(x, target=0.11, lo=0.4, hi=8.0):
    r = np.sqrt(np.mean(x ** 2) + 1e-12); return x * min(hi, max(lo, target / r))
def fade(x, fi=0.025, fo=0.08):
    a = int(fi * SR); b = int(fo * SR); x = x.copy()
    if len(x) > a + b: x[:a] *= np.linspace(0, 1, a); x[-b:] *= np.linspace(1, 0, b)
    return x
def lp_sweep(x, f0, f1):
    n = len(x); f = np.linspace(f0, f1, n); a = 1 - np.exp(-2 * np.pi * f / SR); y = np.empty(n); s = 0.0
    for i in range(n): s += a[i] * (x[i] - s); y[i] = s
    return y
def noise(d): return rng.standard_normal(int(d * SR))
def whoosh(d, f0=300, f1=5000, shape=2.0):
    n = noise(d); y = lp_sweep(n, f0, f1); k = np.arange(len(y)) / len(y); env = np.sin(np.pi * np.clip(k, 0, 1)) ** shape
    return y * env * 3.0
def riser(d, amp=1.0):
    n = noise(d); y = lp_sweep(n, 200, 7000); k = np.arange(len(y)) / len(y); t = k * d
    chirp = np.sin(2 * np.pi * (150 * t + 0.5 * (1400 / d) * t ** 2))
    return (0.8 * y * 3.0 * k ** 2 + 0.25 * chirp * k ** 2.5) * amp
def thud(amp=0.4, f0=60, dec=0.18, d=0.5):
    t = np.arange(int(d * SR)) / SR; return amp * np.sin(2 * np.pi * f0 * np.exp(-t * 3) * t + 2 * np.pi * f0 * t * 0.0) * np.exp(-t / dec) + amp * 0.6 * np.sin(2 * np.pi * f0 * t) * np.exp(-t / dec)
def click(amp=0.35):
    t = np.arange(int(0.06 * SR)) / SR; n = noise(0.06); hp = n - lp_sweep(n, 2500, 2500)
    return amp * (hp * np.exp(-t / 0.006) * 1.5 + 0.7 * np.sin(2 * np.pi * 1700 * t) * np.exp(-t / 0.012))
def tick(amp=0.12):
    t = np.arange(int(0.025 * SR)) / SR; return amp * np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.004)
def chime(f, amp=0.2, d=0.9):
    t = np.arange(int(d * SR)) / SR; return amp * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t / 0.35) * np.minimum(1, t / 0.004)
def boom_snd(amp=0.9):
    d = 1.4; t = np.arange(int(d * SR)) / SR; sub = np.sin(2 * np.pi * (28 + 40 * np.exp(-t * 5)) * t) * np.exp(-t / 0.5)
    n = noise(d); br = lp_sweep(n, 6000, 400) * np.exp(-t / 0.12) * 1.5
    return amp * (sub * 1.2 + br * 0.7)
def pad(d, amp=0.05):
    t = np.arange(int(d * SR)) / SR; y = 0
    for f, a in [(110, 1), (164.81, .7), (220, .6), (277.18, .4), (329.63, .3)]:
        y = y + a * np.sin(2 * np.pi * f * t + np.sin(t * 0.7 + f)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.13 * t + f))
    return amp * y * np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.2)

def S(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o

def audio(total):
    N = int(total * SR); L = np.zeros(N); R = np.zeros(N); SL = np.zeros(N); SR_ = np.zeros(N)
    def put(x, t, pan=0.0, gain=1.0, sp=False):
        dl, dr = (SL, SR_) if sp else (L, R)
        i = int(round(t * SR))
        if i < 0: x = x[-i:]; i = 0
        n = min(len(x), N - i)
        if n <= 0: return
        a = (pan + 1) * np.pi / 4; dl[i:i + n] += x[:n] * np.cos(a) * gain * 1.414; dr[i:i + n] += x[:n] * np.sin(a) * gain * 1.414
    # ---- 1. trump (real speech, from t=0)
    tr = snippet(V3 + '/trump/un_seg2.mp4', CFG['tr_start'], DT0); tr = norm_rms(tr, 0.24, 0.3, 8.0); tr = fade(tr, 0.01, 0.05)
    put(tr, 0.0, 0.0, 1.0, sp=True)
    sd = CFG['slow_dur']; tp = sd / SLOW
    r = subprocess.run([FF, '-v', 'error', '-ss', f"{CFG['slow_start']:.3f}", '-t', f'{sd:.3f}', '-i', V3 + '/trump/un_seg2.mp4', '-vn', '-ac', '1', '-ar', str(SR), '-af', f'atempo=0.5,atempo={tp/0.5:.4f}', '-f', 'f32le', '-'], capture_output=True)
    sl = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64); sl = fade(norm_rms(sl, 0.26, 0.3, 8.0), 0.02, 0.15)
    put(sl, DT0, 0.0, 1.0, sp=True); put(thud(0.5, 45, 0.3, 0.8), DT0 - 0.02, 0, 0.5)
    # ---- 2. tunnel
    t_ = np.arange(int(RW*SR))/SR; ph = np.cumsum(2*np.pi*(2400*np.exp(-t_*1.5)+200)/SR)
    put(0.12*np.sin(ph)*np.minimum(1,t_*20)*np.minimum(1,(RW-t_)*10) + 0.25*lp_sweep(noise(RW),6000,1500)*0.4, DT, 0, 1.0)
    T0 = DT + RW
    put(whoosh(0.5, 400, 7000), T0 - 0.1, 0, 0.15)
    put(riser(TUN + 0.1, 1.0), T0, 0, 0.3)
    cand = [a for a in T['audio'] if a['dur'] > 0.5]; rng2 = np.random.default_rng(11); picks = rng2.choice(len(cand), size=min(26, len(cand)), replace=False)
    for j, pi in enumerate(picks):
        a = cand[pi]; d = min(a['dur'], float(rng2.uniform(0.45, 0.85))); x = snippet(a['src'], a['ss'] + 0.05, d)
        if len(x) < 100: continue
        if j % 3 == 2: x = x[::-1].copy()
        tt = T0 + float(rng2.uniform(0.0, TUN - d)) ** 1.0
        put(fade(norm_rms(x, 0.13, 0.4, 8.0), 0.01, 0.05), tt, float(rng2.uniform(-0.8, 0.8)), 0.9, sp=True)
    k = 2025
    for kk in range(2025, 2015, -1):
        u = ((2026 - kk) / 10) ** (1 / 1.35); tt = T0 + u * TUN
        put(S(tick(0.18), thud(0.25, 70 + (2025 - kk) * 6, 0.08, 0.2)), tt, 0, 0.35)
    put(thud(0.8, 45, 0.3, 0.8), T0 + TUN - 0.02, 0, 0.4)
    # ---- 3. chaos : bed + speech + fx
    def bump(t, amp, f0=55, dec=0.22): put(thud(amp, f0, dec, 0.4), t, 0, 1.0)
    t = 0.0
    fs, ss, ns, bk = M['fast_start'] + shift, M['seq_start'] + shift, M['names_start'] + shift, M['black'] + shift
    t = CH0
    pass
    r = 2.0
    pass
    pass
    Ln = int((bk - ns) * SR); env = (np.arange(Ln) / Ln) ** 2; nz = np.diff(rng.standard_normal(Ln), prepend=0); xx = np.arange(Ln) / SR
    put(0.14 * env * nz + 0.26 * env * np.sin(2 * np.pi * (40 + 20 * env) * xx), ns, 0, 0.25)
    for a in T['audio']:
        if a['ev'] not in {e['id'] for e in chaos_evs}: continue
        x = snippet(a['src'], a['ss'], a['dur'])
        if len(x) < 100: continue
        put(fade(norm_rms(x, 0.20, 0.4, 10.0)), a['t'] + shift, a['pan'] * 0.5, 1.0, sp=True)
    prev = None
    for e in chaos_evs:
        te = e['t0'] + shift; era = str(e.get('era', ''))
        pass
        if era.isdigit() and era != prev: put(S(tick(0.25), thud(0.45, 50, 0.2, 0.45)), te, 0, 0.4)
        if era.isdigit(): prev = era
    # ---- 4. boom + silence
    put(boom_snd(0.95), CH1, 0, 0.7)
    # ---- 5. finale
    F = FIN0; V = lambda n: V3 + f'/vo/{n}.wav'
    def vo(n, t, g=1.0):
        x = np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', V(n), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, dtype=np.float32).astype(np.float64)
        put(fade(norm_rms(x, 0.24, 0.5, 8.0), 0.01, 0.06), F + t, 0, g, sp=True)
    vo('D1', 0.0); vo('D2', 2.3); vo('D3', 4.1); vo('D4', 14.35)
    for tt, a in [(0.2, .5), (0.6, .5), (1.32, .9), (2.48, .5), (2.92, .7)]: put(S(thud(a, 55, 0.16, 0.4), 0.5 * tick(0.2)), F + tt, 0, 1.0)
    put(whoosh(0.35, 300, 4500), F + 3.45, 0, 0.5)
    for tt in [4.36, 4.56, 4.84]: put(chime(440 * (1.5 if tt > 4.8 else 1), 0.12, 0.5), F + tt, 0, 1.0)
    put(riser(0.9, 0.7), F + 4.0, 0, 0.55); put(whoosh(0.7, 200, 6000), F + 4.85, 0, 0.7); put(thud(0.6, 50, 0.3, 0.7), F + 4.95, 0, 1.0)
    put(pad(FINL - 4.9, 0.05), F + 4.9, 0, 1.0)
    n_ch = 32
    for i in range(n_ch): put(tick(0.10 + 0.04 * (i % 3)), F + 6.0 + i * 1.3 / n_ch, 0.1, 1.0)
    put(click(0.4), F + 7.5, 0, 1.0); put(whoosh(0.5, 300, 4000), F + 7.6, 0, 0.45); put(whoosh(0.5, 300, 4000), F + 8.5, 0, 0.4)
    for tt in [8.85, 9.35, 11.15, 11.45]: put(chime(1320, 0.08, 0.4), F + tt, 0.2, 1.0)
    for tt in [9.5, 10.1, 10.45, 10.8, 11.2]: put(click(0.45), F + tt, 0.1, 1.0)
    put(chime(659.25, 0.2, 1.0), F + 11.3, 0, 1.0); put(chime(880, 0.2, 1.2), F + 11.42, 0, 1.0)
    put(whoosh(0.9, 300, 6000), F + 12.55, 0, 0.55); put(thud(0.5, 55, 0.25, 0.6), F + 13.0, 0, 1.0)
    put(whoosh(0.6, 400, 7000), F + 14.05, 0, 0.6); put(chime(523.25, 0.2, 1.6) + chime(659.25, 0.15, 1.6) + chime(783.99, 0.12, 1.6), F + 14.55, 0, 1.0)
    env = np.abs(SL) + np.abs(SR_); k = int(0.12 * SR); cs = np.cumsum(np.insert(env, 0, 0)); env = (cs[k:] - cs[:-k]) / k; env = np.concatenate([env, np.zeros(N - len(env))])[:N]
    env = np.convolve(env, np.ones(int(0.15 * SR)) / int(0.15 * SR), mode='same')
    duck = 1 - 0.85 * np.clip(env / 0.06, 0, 1)
    L = L * duck + SL; R = R * duck + SR_
    # ---- hard silence between boom and finale
    b0 = int((CH1 + 0.45) * SR); b1 = int(FIN0 * SR); f = int(0.02 * SR)
    for ch in (L, R): ch[b0 - f:b0] *= np.linspace(1, 0, f); ch[b0:b1] = 0
    pk = max(np.abs(L).max(), np.abs(R).max()); sc = 0.9 / pk if pk > 0.9 else 1.0
    st = np.stack([np.tanh(L * sc * 1.1) / np.tanh(1.1), np.tanh(R * sc * 1.1) / np.tanh(1.1)], axis=1); st = (np.clip(st, -1, 1) * 32767).astype('<i2')
    w = wave.open(B + '/mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
    print('audio peak', round(float(pk), 2), 'scale', round(float(sc), 2))

def main():
    vs = video() if not os.environ.get('SKIPV') else (sum(nfr(DT) for _ in [0]) + nfr(RW) + nfr(TUN) + sum(nfr(e['dur']) for e in chaos_evs) + nfr(BOOM) + nfr(FINL)) / FPS
    audio(vs)
    out = D + '/achi-supercut-v3.mp4'
    run([FF, '-v', 'error', '-y', '-i', B + '/video.mp4', '-i', B + '/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out])
    json.dump(dict(DT=DT, TUN=TUN, CH0=CH0, CH1=CH1, BOOM=BOOM, FIN0=FIN0, TOTAL=TOTAL, shift=shift), open(V3 + '/marks.json', 'w'))
    print('rendered', out)
if __name__ == '__main__': main()
