import json,re
D='/tmp/supercut'
T=json.load(open(D+'/timeline.json'))
YT={'outcGtbnMuQ':'GPT-4 Developer Livestream','Fs0t6SdODd8':'Introducing Gemini 2.0','CSE77wAdDLg':'Introducing Operator & Agents','8UWKxJbjriY':'Introducing ChatGPT Atlas','Wq45rvPGNHs':'Introducing ChatGPT Work','Fls_onRviPM':'OpenAI DevDay 2026 Keynote','U9mJuUkhUzk':'OpenAI DevDay 2023 Opening Keynote','duHhImuaZGU':'Sundar Pichai Opening Remarks, I/O 2026','hF8swzNR1-o':'Apple WWDC 2026 Siri AI','F1_0Lkp16Rc':'Introducing Grok Bot','xr4VUV-7rN0':'Mistral and Microsoft strategic partnership','ODaHJzOyVCQ':'Claude Computer use','YeldJ4UezDQ':'Introducing Comet','_fuimO6ErKI':'Google Welcome to the Gemini era','jV1vkHv4zq8':"Google's newest and most capable AI | Gemini"}
def vid(p): return re.search(r'/([^/]+)\.mp4',p).group(1)
def tc(x): return f'{x:05.2f}'.replace('.',':') if False else f'{x:.2f}'
CARD={'open':'כרטיס פתיחה: A supercut of public statements, 2016–2026','alphago':'כרטיס טקסט: 2016 · AlphaGo beats Lee Sedol 4–1 · Google DeepMind · March 2016','attention':'כרטיס טקסט: 2017 · "Attention Is All You Need" · arXiv, June 2017','chatgpt':'כרטיס טקסט: 2022 · ChatGPT · OpenAI announcement, Nov 30, 2022','atlas_retire':'כרטיס טקסט: 2026 · OpenAI retires ChatGPT Atlas · announced Jul 9, 2026 (OpenAI help center)'}
A={}
for a in T['audio']: A.setdefault(a['ev'],[]).append(a)
rows=[]; tot_over=0
for ev in T['events']:
    t0,t1=ev['t0'],ev['t0']+ev['dur']; k=ev['kind']; au=A.get(ev['id'],[])
    if k=='clip':
        p=ev['panels'][0]; what=f'**{p["word"]}**' + (f' (רצף: {" ".join(ev["sentence"])})' if ev.get('sentence') else '')
        src=f'{p["label"]} · `{vid(p["src"])}` @ {p["vs"]}s'
    elif k=='stack':
        what='מסך מפוצל: '+' + '.join(f'**{p["word"]}**' for p in ev['panels']); src='<br>'.join(f'{p["label"]} · `{vid(p["src"])}` @ {p["vs"]}s' for p in ev['panels'])
    elif k=='card':
        what=CARD.get(ev['card'],f'הבזק שם: **{ev.get("text","")}**'); src='—'
    elif k=='black': what='שחור + שקט מוחלט'; src='—'
    elif k=='vo': what='קריינות עברית על מסכי achi: "כולם הבטיחו סוכן שיעשה בשבילך. אז בנינו אותו."'; src='ElevenLabs TTS (טיוטה) + צילומי מסך אמיתיים של achi'
    else: what='כרטיס סיום: achi. · Not only a browser. A colleague. · Waitlist open: achilabs.app · שורת אי-שיוך'; src='—'
    aud=''
    for a in au:
        tail=a['t']+a['dur']-t1; over=max(0,tail); tot_over+=over
        aud+=f'כניסה {a["t"]:.2f} → זנב {a["t"]+a["dur"]:.2f} (חפיפה לקליפ הבא {over:.2f}s)<br>'
    rows.append(f'| {ev["id"]+1} | {t0:.2f}–{t1:.2f} | {ev["dur"]:.2f} | {ev.get("era","")} | {what} | {src} | {aud or "—"} |')
M=T['markers']
out=f"""# achi — "AI timeline supercut" v2: תוכנית הרכבה עם זמנים

**אורך כולל: {T['total']:.2f} שניות** (9:16, 1080x1920, 30fps) · {len(T['events'])} אירועי תמונה · {len(T['audio'])} חיתוכי אודיו · סך חפיפות זנב-אודיו: {tot_over:.1f}s

## עקרון הקולאז׳ (מה השתנה מ-v1)
- **אודיו עם ידיות:** כל חיתוך מתחיל {T['pre']}s לפני המילה ונגמר {T['post']}s אחריה, עם fade קצר. המילה נופלת בדיוק על החיתוך, והזנב נמשך מעל הקליפ הבא (חפיפה במקום חיתוך חד).
- **שכבות אמיתיות:** באזור ההצפה יש אירועי מסך מפוצל (2–3 קליפים אחד מעל השני, כל אחד עם האודיו שלו) והבזקי שמות עם 4–5 קולות שמתערבבים.
- **קצב מואץ:** 2023 ≈0.9s לקליפ → 2025 ≈0.55s → 2026 ≈0.4s → מסך מפוצל 0.45–0.5s → הבזקים 0.28s.
- **מסך מלא ללא מסגרת**, שנה ושם האירוע בראש הפריים (לא שם דובר: לא ניתן לאמת דובר בכל קליפ).

## מקטעים
| מקטע | התחלה | סיום | אורך |
|---|---|---|---|
| פתיחה + 2016/2017/2022 (כרטיסי טקסט) | 0.00 | {M['early_end']:.2f} | {M['early_end']:.2f} |
| 2023–2025 (קליפים) + כרטיס 2026 | {M['early_end']:.2f} | {M['fast_start']:.2f} | {M['fast_start']-M['early_end']:.2f} |
| 2026 + מסכים מפוצלים (האצה) | {M['fast_start']:.2f} | {M['seq_start']:.2f} | {M['seq_start']-M['fast_start']:.2f} |
| המשפט "AI agents will do everything for you" | {M['seq_start']:.2f} | {M['names_start']:.2f} | {M['names_start']-M['seq_start']:.2f} |
| הבזקי שמות חברות + ערבוב קולות + ריסר | {M['names_start']:.2f} | {M['black']:.2f} | {M['black']-M['names_start']:.2f} |
| שחור ושקט מוחלט | {M['black']:.2f} | {M['vo']:.2f} | {M['vo']-M['black']:.2f} |
| קריינות + achi | {M['vo']:.2f} | {M['end']:.2f} | {M['end']-M['vo']:.2f} |
| כרטיס סיום + אי-שיוך | {M['end']:.2f} | {T['total']:.2f} | {T['total']-M['end']:.2f} |

## טבלת זמנים מלאה
| # | זמן (שנ') | אורך | עידן | תוכן | מקור (YouTube ID @ שנייה) | אודיו |
|---|---|---|---|---|---|---|
"""+'\n'.join(rows)+f"""

## מקורות וידאו (כולם ערוצים רשמיים)
"""+'\n'.join(f'- `{k}` — {v}' for k,v in YT.items())+"""

## כללים שנשמרו
- רק מילים שנאמרו בפועל בקליפ רשמי; כרטיסי טקסט רק לעובדות מאומתות (AlphaGo 2016, arXiv 2017, ChatGPT 30.11.2022, הודעת הסגירה של Atlas 9.7.2026).
- פוסט אורגני בלבד, ללא קידום ממומן עד ייעוץ משפטי.
- שורת חובה בסוף ובתיאור: "Clips show public moments in AI history. achi is not affiliated with these companies."
- הקריינות הנוכחית היא TTS (טיוטה) וצילום המסך של achi הוא צילומי מסך סטטיים: להחליף בקול של Oz ובהקלטת מסך אמיתית.
"""
open(D+'/ig-supercut-timeline-v2.md','w').write(out); print(len(out),'chars; total',T['total'])
