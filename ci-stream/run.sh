#!/usr/bin/env bash
# Living World — CI stream runner v2 (GitHub Actions).
# Command channel: a public Google Sheet polled by sheets_pump.py.
# Needs env: RST_KEY (Restream ingest key), CMD_TOKEN.
set -u
cd "$(dirname "$0")"
SHEET_ID="1RHAh4SNlyvMmQuVaFHXQoWusNcY7xaDqZbBsUc6aPyk"

mkdir -p fonts
curl -sL -o fonts/Cairo900.ttf "https://fonts.gstatic.com/s/cairo/v31/SLXgc1nY6HkvangtZmpQdkhzfH5lkSs2SgRjCAGMQ1z0hEk5W1Q.ttf"
curl -sL -o fonts/Cairo700.ttf "https://fonts.gstatic.com/s/cairo/v31/SLXgc1nY6HkvangtZmpQdkhzfH5lkSs2SgRjCAGMQ1z0hAc5W1Q.ttf"
python3 -c "from PIL import ImageFont; ImageFont.truetype('fonts/Cairo900.ttf', 40, layout_engine=ImageFont.Layout.RAQM); print('font+raqm OK')"

: > cmds.log
python3 sheets_pump.py "$SHEET_ID" "$CMD_TOKEN" cmds.log > pump.log 2>&1 &
tail -n 0 -F cmds.log | node drive-live-ci.js > drive.log 2>&1 &
sleep 3
echo "engine state:"; tail -n 2 drive.log || true
echo "pump state:"; tail -n 2 pump.log || true

# ffmpeg with retry: a freshly-killed previous session can make Restream
# reject the first attempts ("End of file") while it releases the event.
attempt=1
while [ $attempt -le 12 ]; do
  echo "ffmpeg attempt $attempt $(date -u +%H:%M:%S)"
  python3 draw-ci.py --stream 2> draw.log | ffmpeg -hide_banner -loglevel warning \
    -f image2pipe -framerate 30 -i - \
    -c:v libx264 -pix_fmt yuv420p -r 30 -preset veryfast -maxrate 4500k -bufsize 9000k -g 60 \
    -f flv "rtmp://live.restream.io/live/$RST_KEY"
  echo "ffmpeg exited (attempt $attempt) — retrying in 20s"
  attempt=$((attempt + 1))
  sleep 20
done
echo "all ffmpeg attempts exhausted — stream ended"
