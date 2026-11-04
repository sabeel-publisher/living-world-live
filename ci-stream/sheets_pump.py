#!/usr/bin/env python3
# Poll a public Google Sheet (CSV export) for operator commands.
# Column A of each NEW row may carry: "<CMD_TOKEN> <operator command>".
# Rows present at startup are skipped (history never replays).
# Usage: sheets_pump.py <sheet_id> <token> <outfile>
import csv, io, sys, time, urllib.request

sheet_id, token, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

def fetch_rows():
    req = urllib.request.Request(URL, headers={"User-Agent": "lw-sheets-pump/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", "replace")
    return [r for r in csv.reader(io.StringIO(text)) if r and r[0].strip()]

seen = None
while True:
    try:
        rows = fetch_rows()
        if seen is None:
            seen = len(rows)
            print(f"pump ready — skipping {seen} historical rows", flush=True)
        elif len(rows) > seen:
            for row in rows[seen:]:
                msg = row[0].strip()
                if msg.startswith(token + " "):
                    cmd = msg[len(token) + 1:].strip()
                    with open(outfile, "a", encoding="utf-8") as f:
                        f.write(cmd + "\n")
                    print("cmd ->", cmd, flush=True)
            seen = len(rows)
    except Exception as e:
        print("pump fetch error:", e, flush=True)
    time.sleep(8)
