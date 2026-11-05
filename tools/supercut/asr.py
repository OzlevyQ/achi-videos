import subprocess, sys, json, os, glob, re
# usage: asr.py VIDEOID  -> /tmp/supercut/words/VIDEOID.json  (list of {w,s,e} in absolute seconds)
vid = sys.argv[1]
maxsec = sys.argv[2] if len(sys.argv)>2 else None
base = "/tmp/supercut"
os.makedirs(base+"/audio", exist_ok=True); os.makedirs(base+"/words", exist_ok=True)
key = None
for line in open(os.path.expanduser("~/loom/engines.env")):
    if line.startswith("GROQ_API_KEY="):
        key = line.split("=",1)[1].strip().strip('"').strip("'")
raw = f"{base}/audio/{vid}.m4a"
if not os.path.exists(raw):
    subprocess.run(["yt-dlp","-q","--no-progress","--no-warnings","-f","bestaudio[ext=m4a]/bestaudio","-o",raw,f"https://www.youtube.com/watch?v={vid}"],check=True)
seg_dir = f"{base}/audio/{vid}_seg"; os.makedirs(seg_dir, exist_ok=True)
if not glob.glob(seg_dir+"/*.mp3"):
    subprocess.run(["ffmpeg","-y","-loglevel","error"]+(["-t",maxsec] if maxsec else [])+["-i",raw,"-ac","1","-ar","16000","-b:a","32k","-f","segment","-segment_time","600","-reset_timestamps","1",seg_dir+"/s%03d.mp3"],check=True)
words = []
for i, f in enumerate(sorted(glob.glob(seg_dir+"/*.mp3"))):
    off = i*600.0
    for attempt in range(3):
        r = subprocess.run(["curl","-s","https://api.groq.com/openai/v1/audio/transcriptions","-H","Authorization: Bearer "+key,
            "-F","file=@"+f,"-F","model=whisper-large-v3-turbo","-F","response_format=verbose_json",
            "-F","timestamp_granularities[]=word","-F","language=en"],capture_output=True,text=True)
        try:
            j = json.loads(r.stdout); break
        except Exception:
            j = None
    if not j or "words" not in j:
        print(vid, f, "ERR", (r.stdout or "")[:200]); continue
    for w in j["words"]:
        words.append({"w":w["word"],"s":round(w["start"]+off,2),"e":round(w["end"]+off,2)})
json.dump(words, open(f"{base}/words/{vid}.json","w"))
print(vid, "words", len(words))
