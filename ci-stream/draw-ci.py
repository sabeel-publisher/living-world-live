#!/usr/bin/env python3
# Frame-push renderer: state.json (produced by the overlay's own JS) -> current.png
# Replicates overlay.html layout/colors at 1080x1920. Arabic via PIL+raqm+Cairo.
import json, os, sys, time
from PIL import Image, ImageDraw, ImageFont

STATE = __file__.replace("draw-ci.py", "state.json")
OUT = __file__.replace("draw-ci.py", "current.png")
W, H = 1080, 1920
import os as _os
FB = _os.path.join(_os.path.dirname(__file__), "fonts", "Cairo900.ttf")
FR = _os.path.join(_os.path.dirname(__file__), "fonts", "Cairo700.ttf")

def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)

F_TITLE = font(FB, 46); F_GOAL = font(FB, 27); F_HOWTO = font(FR, 25)
F_PHASE = font(FB, 27); F_CHIP = font(FR, 19); F_CELL = font(FB, 19)
F_FERT = font(FR, 13); F_CONTRIB_L = font(FB, 21); F_TEXT = font(FR, 23)
F_BANNER = font(FB, 31); F_QUEUE = font(FR, 20)

def hexcol(h):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def ctext(d, cx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return w

def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def dashed_rect(d, box, color, width=2, dash=9, gap=6):
    x0, y0, x1, y1 = box
    x = x0
    while x < x1:
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=color, width=width)
        x += dash + gap
    y = y0
    while y < y1:
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=color, width=width)
        y += dash + gap

def draw(state):
    img = Image.new("RGB", (W, H), hexcol("#0f1a2e"))
    d = ImageDraw.Draw(img)
    # subtle vertical gradient
    for y in range(H):
        t = y / H
        c = tuple(int(15 + (13 - 15) * t + 0) for _ in range(1))
        base = (int(15 + (13 - 15) * t), int(26 + (31 - 26) * t), int(46 + (45 - 46) * t))
        d.line([(0, y), (W, y)], fill=base)
    cx = W // 2
    ctext(d, cx, 55, "عالم يُولد مرة واحدة", F_TITLE, (248, 250, 252))
    if state.get("worldName"):
        ctext(d, cx, 122, state["worldName"], F_GOAL, (251, 191, 36))
    ctext(d, cx, 128, "بنبني مكان يصلح للحياة", F_GOAL, (167, 243, 208))
    # howto box
    d.rounded_rectangle([43, 175, W - 43, 268], radius=12, fill=(27, 42, 68), outline=(53, 80, 122), width=1)
    ctext(d, cx, 208, "اكتب حاجة ومكانها: ازرع شجرة في ب٣ — وهتظهر باسمك", F_HOWTO, (241, 245, 249))
    # phase pill
    ph = state.get("phase") or "طور البذور"
    pw = d.textlength(ph, font=F_PHASE) + 90
    d.rounded_rectangle([cx - pw / 2, 292, cx + pw / 2, 348], radius=28, fill=hexcol("#7c3aed"))
    ctext(d, cx, 306, ph, F_PHASE, (255, 255, 255))
    # life chips
    chips = ["مية لكل مكان", "ضل على الطرق", "نور عند التقاطعات", "مركز بيجمع الكل"]
    widths = [d.textlength(c, font=F_CHIP) + 44 for c in chips]
    total = sum(widths) + 6 * 3
    x = cx - total / 2
    for i, c in enumerate(chips):
        on = state.get("life", [False] * 4)[i]
        box = [x, 372, x + widths[i], 412]
        if on:
            d.rounded_rectangle(box, radius=20, fill=hexcol("#065f46"), outline=hexcol("#34d399"), width=1)
            ctext(d, x + widths[i] / 2, 382, c, F_CHIP, (236, 253, 245))
        else:
            d.rounded_rectangle(box, radius=20, outline=(100, 116, 139), width=1)
            ctext(d, x + widths[i] / 2, 382, c, F_CHIP, (148, 163, 184))
        x += widths[i] + 6
    # grid
    cell, gap, gx, gy = 79, 4, 44, 445
    cells = state.get("cells", [])
    for idx in range(120):
        r, c = divmod(idx, 12)
        x0, y0 = gx + c * (cell + gap), gy + r * (cell + gap)
        x1, y1 = x0 + cell, y0 + cell
        cellst = cells[idx] if idx < len(cells) else {"cls": "", "bg": None, "fg": None, "label": ""}
        if cellst.get("bg"):
            d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=hexcol(cellst["bg"]))
            lab = cellst.get("label", "")
            fnt = F_CELL
            while d.textlength(lab, font=fnt) > cell - 6 and fnt.size > 10:
                fnt = font(FB, fnt.size - 1)
            ctext(d, (x0 + x1) / 2, y0 + cell / 2 - fnt.size / 2 - 2, lab, fnt, hexcol(cellst["fg"] or "#ffffff"))
            if "seed" in (cellst.get("cls") or ""):
                dashed_rect(d, [x0 + 1, y0 + 1, x1 - 1, y1 - 1], (245, 158, 11))
        elif "fertile" in (cellst.get("cls") or ""):
            d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=hexcol("#fef3c7"))
            ctext(d, (x0 + x1) / 2, y0 + cell / 2 - 8, "تربة خصبة", F_FERT, hexcol("#92400e"))
        else:
            d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=(26, 42, 68))
    # banner (event) — above grid like the page
    b = state.get("banner") or {}
    if b.get("shown") and b.get("text"):
        lines = wrap(d, b["text"], F_BANNER, 880)
        bh = len(lines) * 48 + 44
        by0 = 660
        d.rounded_rectangle([54, by0, W - 54, by0 + bh], radius=14, fill=(5, 46, 22), outline=hexcol("#34d399"), width=2)
        for i, ln in enumerate(lines):
            ctext(d, cx, by0 + 24 + i * 48, ln, F_BANNER, (236, 253, 245))
    # queue + contributors
    if state.get("queue"):
        ctext(d, cx, 1560, state["queue"], F_QUEUE, (165, 180, 252))
    d.text((W - 43 - d.textlength("صُنّاع العالم لحد دلوقتي:", font=F_CONTRIB_L), 1620),
           "صُنّاع العالم لحد دلوقتي:", font=F_CONTRIB_L, fill=(251, 191, 36))
    d.rounded_rectangle([43, 1665, W - 43, 1800], radius=10, fill=(23, 36, 58), outline=(53, 80, 122), width=1)
    contrib = state.get("contrib") or ""
    lines = wrap(d, contrib, F_TEXT, 940)[:3]
    for i, ln in enumerate(lines):
        ctext(d, cx, 1690 + i * 38, ln, F_TEXT, (226, 232, 240))
    img.save(OUT + ".tmp.png")
    os.replace(OUT + ".tmp.png", OUT)

def draw_to_bytes(state):
    import io
    draw(state)  # writes OUT png
    with open(OUT, "rb") as f:
        return f.read()

def main():
    if "--stream" in sys.argv:
        # Live mode: emit PNG frames at 30fps to stdout (image2pipe -> ffmpeg).
        # Redraw only when the page state version changes; repeat last frame otherwise.
        out = sys.stdout.buffer
        last, payload = -1, None
        frame_dt = 1.0 / 30.0
        nxt = time.time()
        err_logged = False
        while True:
            try:
                with open(STATE) as f:
                    state = json.load(f)
                if state.get("version", 0) != last:
                    payload = draw_to_bytes(state)
                    last = state["version"]
            except FileNotFoundError:
                pass
            except Exception as e:
                if not err_logged:
                    print("draw err:", e, file=sys.stderr, flush=True)
                    err_logged = True
            if payload:
                try:
                    out.write(payload); out.flush()
                except BrokenPipeError:
                    break
            nxt += frame_dt
            time.sleep(max(0, nxt - time.time()))
        return
    last = -1
    deadline = time.time() + 45
    while time.time() < deadline:
        try:
            with open(STATE) as f:
                state = json.load(f)
            if state.get("version", 0) != last:
                draw(state)
                last = state["version"]
                print("drew version", last, flush=True)
        except FileNotFoundError:
            pass
        except Exception as e:
            print("draw err:", e, flush=True)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
