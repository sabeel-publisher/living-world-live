#!/usr/bin/env python3
# Subscribe to an ntfy topic; append authorized operator commands to cmds.log.
# A message counts only if it starts with the CMD_TOKEN. Usage:
#   ntfy_pump.py <topic> <token> <outfile>
import json, sys, time, urllib.request

topic, token, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
last_id = None

def emit(text):
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print("cmd ->", text, flush=True)

while True:
    try:
        url = f"https://ntfy.sh/{topic}/json"
        if last_id:
            url += f"?since={last_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "lw-pump/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            for raw in resp:
                try:
                    ev = json.loads(raw.decode("utf-8", "replace"))
                except Exception:
                    continue
                if ev.get("id"):
                    last_id = ev["id"]
                if ev.get("event") != "message":
                    continue
                msg = (ev.get("message") or "").strip()
                if msg.startswith(token + " "):
                    emit(msg[len(token) + 1:].strip())
    except Exception as e:
        print("pump reconnect after:", e, flush=True)
        time.sleep(3)
