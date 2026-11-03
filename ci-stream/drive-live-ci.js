// Living World — LIVE operator driver.
// Runs the REAL overlay.html script in Node (minimal DOM stub) and keeps it alive.
// The operator types one command per line on stdin (or pipes them from a chat bridge):
//   place W 5 4 ليلى            -> window.__place('W',5,4,'ليلى')
//   placeAr Tp ب 3 عمر          -> window.__placeAr('Tp','ب',3,'عمر')
//   decompose 0 0               -> window.__decompose(0,0)
//   phase طور الربط             -> window.__setPhase('طور الربط')
//   banner نص الإعلان           -> window.__banner('نص الإعلان')
//   life 2                      -> window.__life(2)
//   worldname اسم العالم        -> window.__setWorldName('اسم العالم')
//   freeze                      -> window.__freeze()
//   state                       -> print current state.json version
// Every page render is captured to state.json; draw.py turns it into frames.
const fs = require("fs");
const readline = require("readline");
const html = fs.readFileSync(__dirname + "/../overlay.html", "utf8");
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const STATE_FILE = __dirname + "/state.json";
let version = 0;

function writeState() {
  version++;
  const cells = [];
  const re = /<div class="cell([^"]*)"(?: style="background:([^;]+);color:([^"]*)")?[^>]*>([^<]*)<\/div>/g;
  let m;
  const gridHtml = els.grid._innerHTML || "";
  while ((m = re.exec(gridHtml)) !== null) {
    cells.push({ cls: m[1].trim(), bg: m[2] || null, fg: m[3] || null, label: m[4] || "" });
  }
  const state = {
    version, cells,
    phase: els.phase._textContent || "",
    worldName: els.worldName._textContent || "",
    contrib: els.contrib._textContent || "",
    queue: els.queueLine._textContent || "",
    banner: { text: els.banner._textContent || "", shown: els.banner.classList._set.has("show") },
    life: [1, 2, 3, 4].map(i => els["life" + i].classList._set.has("on")),
    frozen: els.stage.classList._set.has("frozen")
  };
  fs.writeFileSync(STATE_FILE + ".tmp", JSON.stringify(state));
  fs.renameSync(STATE_FILE + ".tmp", STATE_FILE);
}

function makeEl() {
  const el = {
    _innerHTML: "", _textContent: "",
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); writeState(); },
      remove(c) { this._set.delete(c); writeState(); },
      toggle(c) { this._set.has(c) ? this._set.delete(c) : this._set.add(c); writeState(); }
    }
  };
  Object.defineProperty(el, "innerHTML", {
    get() { return this._innerHTML; }, set(v) { this._innerHTML = v; writeState(); }
  });
  Object.defineProperty(el, "textContent", {
    get() { return this._textContent; }, set(v) { this._textContent = v; writeState(); }
  });
  return el;
}

const els = {};
["grid", "contrib", "phase", "worldName", "banner", "queueLine", "stage",
 "life1", "life2", "life3", "life4"].forEach(id => els[id] = makeEl());
els.phase._textContent = "طور البذور";
els.contrib._textContent = "لسه محدش زرع حاجة… أول حجر مستني صاحبه.";

global.document = { getElementById: id => els[id] };
global.window = {};
global.console = console;
(0, eval)(code);
for (const k of Object.keys(global.window)) global[k] = global.window[k];
writeState();
console.log("READY — overlay state engine running. Commands on stdin.");

const rl = readline.createInterface({ input: process.stdin });
rl.on("line", line => {
  const parts = line.trim().split(/\s+/);
  if (!parts.length || !parts[0]) return;
  const cmd = parts[0];
  try {
    if (cmd === "place") {
      const by = parts.slice(4).join(" ") || "مجهول";
      console.log("place ->", window.__place(parts[1], +parts[2], +parts[3], by));
    } else if (cmd === "placeAr") {
      const by = parts.slice(4).join(" ") || "مجهول";
      console.log("placeAr ->", window.__placeAr(parts[1], parts[2], +parts[3], by));
    } else if (cmd === "decompose") {
      console.log("decompose ->", window.__decompose(+parts[1], +parts[2]));
    } else if (cmd === "phase") {
      window.__setPhase(parts.slice(1).join(" ")); console.log("phase ok");
    } else if (cmd === "banner") {
      window.__banner(parts.slice(1).join(" ")); console.log("banner ok");
    } else if (cmd === "life") {
      window.__life(+parts[1]); console.log("life ok");
    } else if (cmd === "worldname") {
      window.__setWorldName(parts.slice(1).join(" ")); console.log("worldname ok");
    } else if (cmd === "freeze") {
      window.__freeze(); console.log("frozen");
    } else if (cmd === "state") {
      console.log("state version", version);
    } else {
      console.log("unknown command:", cmd);
    }
  } catch (e) {
    console.log("command error:", e.message);
  }
});
