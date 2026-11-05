#!/usr/bin/env python3
"""Narration through the Instinct chat in WhatsMac (Oz's standing method).
usage: instinct_vo.py lines.json outdir   (lines.json: [{"tag":"D1","text":"..."}], optional "style")"""
import json, os, sys, time, uuid, urllib.request, subprocess
ROOT = os.path.expanduser('~/Library/Application Support/WhatsMac')
TOKEN = open(os.path.join(ROOT, 'api-token')).read().strip()
ACC = '0dfb4608-0f4b-4532-8921-57ea0a55d287'
JID = '23949492670633@lid'
BASE = 'http://localhost:8796/api/accounts/' + ACC
DEF_STYLE = ('בקול של גבר, דרמטי וקולנועי כמו טריילר של סרט, בעברית, בקצב איטי ובטוח עם הפסקה דרמטית, '
             'קול עמוק וחם אבל לא זקן, עם עוצמה בסוף המשפט')

def call(method, path, body=None, raw=False):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return data if raw else json.loads(data)

lines = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
t0 = int(time.time())
seen = {m['id'] for m in call('GET', f'/messages?jid={JID}&limit=100')}
for ln in lines:
    style = ln.get('style', DEF_STYLE)
    text = (f"הקלט לי הודעה קולית (voice note) {style}. הקרא את המשפט הבא בדיוק כפי שהוא כתוב, "
            f"בלי שום תוספת לפני או אחרי, רק את המשפט. תיוג: {ln['tag']}. המשפט: {ln['text']}")
    call('POST', '/send', {'jid': JID, 'text': text, 'requestId': 'v3-' + uuid.uuid4().hex[:12]})
    print('sent', ln['tag'], flush=True)
    time.sleep(2.5)
# collect replies in order
want = len(lines); got = []
deadline = time.time() + 600
while len(got) < want and time.time() < deadline:
    time.sleep(5)
    msgs = call('GET', f'/messages?jid={JID}&limit=100')
    new = sorted([m for m in msgs if not m['mine'] and m['type'] == 'audioMessage' and m['id'] not in seen and m['media']], key=lambda m: m['ts'])
    got = new
    print('replies', len(got), '/', want, flush=True)
for ln, m in zip(lines, got):
    ogg = os.path.join(out, ln['tag'] + '.ogg')
    open(ogg, 'wb').write(call('GET', '/media/' + m['media'], raw=True))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', ogg, '-ar', '44100', '-ac', '1', os.path.join(out, ln['tag'] + '.wav')], check=True)
    print('saved', ln['tag'], flush=True)
print('done')
