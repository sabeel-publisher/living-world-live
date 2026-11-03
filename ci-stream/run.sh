#!/usr/bin/env bash
# Living World — CI stream runner (GitHub Actions).
# Needs env: RST_KEY (Restream ingest key), NTFY_TOPIC, CMD_TOKEN.
set -u
cd "$(dirname "$0")"

mkdir -p fonts
curl -sL -o fonts/Cairo900.ttf "https://fonts.gstatic.com/s/cairo/v31/SLXgc1nY6HkvangtZmpQdkhzfH5lkSs2SgRjCAGMQ1z0hEk5W1Q.ttf"
curl -sL -o fonts/Cairo700.ttf "https://fonts.gstatic.com/s/cairo/v31/SLXgc1nY6HkvangtZmpQdkhzfH5lkSs2SgRjCAGMQ1z0hAc5W1Q.ttf"
python3 -c "from PIL import ImageFont; ImageFont.truetype('fonts/Cairo900.ttf', 40, layout_engine=ImageFont.Layout.RAQM); print('font+raqm OK')"

curl -s -d "STATUS runner-start $(date -u +%H:%M:%S)" "https://ntfy.sh/$NTFY_TOPIC" > /dev/null
( while true; do sleep 300; curl -s -d "STATUS alive $(date -u +%H:%M:%S)" "https://ntfy.sh/$NTFY_TOPIC" > /dev/null; done ) &

: > cmds.log
python3 ntfy_pump.py "$NTFY_TOPIC" "$CMD_TOKEN" cmds.log > pump.log 2>&1 &
tail -n 0 -F cmds.log | node drive-live-ci.js > drive.log 2>&1 &
sleep 3
echo "engine state:"; tail -n 2 drive.log || true

python3 draw-ci.py --stream 2> draw.log | ffmpeg -hide_banner -loglevel warning \
  -f image2pipe -framerate 30 -i - \
  -c:v libx264 -pix_fmt yuv420p -r 30 -preset veryfast -maxrate 4500k -bufsize 9000k -g 60 \
  -f flv "rtmp://live.restream.io/live/$RST_KEY"
echo "ffmpeg exited — stream ended"
