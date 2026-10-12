import "./style.css";
import {
  freshRun,
  deliver,
  miss,
  reward,
  readSave,
  purchase,
  SKINS,
} from "./game.js";
const $ = (s) => document.querySelector(s);
let save;
try {
  save = readSave(localStorage.getItem("noriwake-save"));
} catch {
  save = readSave(null);
}
let state = freshRun(),
  mode = "idle",
  targets = [],
  shots = [],
  particles = [],
  spawn = 0,
  clock = 0,
  previous = 0,
  muted = true,
  audio;
$("#app").innerHTML =
  `<main class="shell"><header class="top"><div class="brand"><span class="mark">≈</span>noriwake<em>·</em></div><div class="topright"><span class="tag">Ночная кухня · прототип 0.1</span><button class="quiet" id="sound" aria-label="Включить звук">Звук: выкл.</button><button class="quiet" id="collection">Моя лодка ↗</button></div></header><div class="layout"><section class="intro"><div class="eyebrow">Маленькая лодка. Большое сердце.</div><h1>Ночная кухня.<br><span>Большое<br>сердце.</span></h1><p class="description">Твоя кухня — на воде. Твои соседи — на причалах. Один ночной рейс, чтобы сделать город немного теплее.</p><div class="chapter"><small>МАРШРУТ 01 / СТАРЫЙ ПОРТ</small><h3>Первые огни</h3><p>Тётушка Ко уже ждёт у причала.<br>Не дай её ужину остыть.</p></div><div class="stats"><div class="stat"><strong id="best">0</strong><span>личный рекорд</span></div><div class="stat"><strong id="coins">0</strong><span>чаевые ✦</span></div></div><button class="primary" id="play"><span>Отправиться в рейс</span><span>→</span></button><p class="hint">90 секунд · бесплатно · без кошелька</p><div class="steps"><b>01</b>Тапай по жителям с заказом</div><div class="steps"><b>02</b>Попадай подряд и собирай комбо</div><div class="steps"><b>03</b>Зарабатывай на новую лодку</div></section><section class="game-wrap" aria-label="Игровое поле: тапайте по животным с белым значком суши"><canvas id="game" aria-label="Ночной канал. Используйте мышь или касание для доставки еды."></canvas><div class="hud"><div class="glass"><small>ДОСТАВЛЕНО С ЛЮБОВЬЮ</small><strong id="score">0000</strong><div class="combo" id="combo">Хороший вечер для первого рейса</div></div><div class="hud-right"><div class="glass timer"><small>ДО ПРИЧАЛА</small><strong id="time">1:30</strong></div><button class="quiet glass hidden" id="pause" aria-label="Пауза">Ⅱ</button></div></div><div class="tip" id="tip"><div class="eyebrow">ДОБРО ПОЖАЛОВАТЬ В НОРИВЕЙК</div><h2>Ужин сам не приплывёт.</h2><p>Тапай по жителям с заказом.<br>Десять попаданий подряд зажгут горячую волну.</p></div><div class="scene-label"><i class="dot"></i>СТАРЫЙ ПОРТ<span> / НОЧНАЯ СМЕНА</span></div></section></div><footer class="bottom"><span>Сделано для коротких пауз и больших комбо.</span><button id="about">О прототипе и лицензиях ↗</button></footer></main><div id="overlay" class="modal-shade hidden"></div><div id="toast" class="toast hidden" role="status"></div>`;
const canvas = $("#game"),
  ctx = canvas.getContext("2d");
let W = 800,
  H = 700;
new ResizeObserver(() => {
  const r = canvas.getBoundingClientRect();
  W = r.width;
  H = r.height;
  const d = Math.min(devicePixelRatio || 1, 2);
  canvas.width = W * d;
  canvas.height = H * d;
  ctx.setTransform(d, 0, 0, d, 0, 0);
}).observe(canvas);
function persist() {
  try {
    localStorage.setItem("noriwake-save", JSON.stringify(save));
  } catch {
    toast("Сохранение недоступно: прогресс останется до закрытия игры.");
  }
  updateStats();
}
function updateStats() {
  $("#best").textContent = save.best.toLocaleString("ru");
  $("#coins").textContent = save.coins;
}
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").classList.remove("hidden");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => $("#toast").classList.add("hidden"), 3500);
}
function sound(freq = 500) {
  if (muted) return;
  try {
    audio ??= new (window.AudioContext || window.webkitAudioContext)();
    audio.resume();
    const o = audio.createOscillator(),
      g = audio.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(freq, audio.currentTime);
    o.frequency.exponentialRampToValueAtTime(
      freq * 0.55,
      audio.currentTime + 0.16,
    );
    g.gain.setValueAtTime(0.08, audio.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.2);
    o.connect(g);
    g.connect(audio.destination);
    o.start();
    o.stop(audio.currentTime + 0.2);
  } catch {}
}
function hud() {
  $("#score").textContent = String(state.score).padStart(4, "0");
  const t = Math.ceil(state.remaining);
  $("#time").textContent =
    `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
  $("#combo").textContent =
    state.wave > 0
      ? `ГОРЯЧАЯ ВОЛНА · ×2 · ${Math.ceil(state.wave)}с`
      : state.combo
        ? `${state.combo} подряд · ещё ${10 - (state.combo % 10)} до волны`
        : "Тапай по жителям с заказом";
}
function addTarget(y = 0.15) {
  targets.push({
    x: targets.length % 2 ? 0.77 : 0.23,
    y,
    kind: Math.floor(Math.random() * 3),
    fed: false,
    phase: Math.random() * 6,
  });
}
function start() {
  state = freshRun();
  targets = [];
  shots = [];
  particles = [];
  spawn = 0;
  addTarget(0.25);
  addTarget(0.5);
  mode = "playing";
  $("#overlay").classList.add("hidden");
  $("#tip").classList.add("hidden");
  $("#pause").classList.remove("hidden");
  $("#play").innerHTML = "<span>Рейс в пути · пауза</span><span>Ⅱ</span>";
  hud();
  sound(650);
  canvas.scrollIntoView({ block: "center", behavior: "instant" });
}
function modal(html) {
  $("#overlay").innerHTML =
    `<section class="modal" role="dialog" aria-modal="true" aria-label="Noriwake">${html}</section>`;
  $("#overlay").classList.remove("hidden");
  $("#overlay").querySelector("button")?.focus();
}
function resume() {
  mode = "playing";
  $("#overlay").classList.add("hidden");
  $("#pause").focus();
}
function pause() {
  if (mode !== "playing") return;
  mode = "paused";
  modal(
    '<div class="eyebrow">КУХНЯ НА ПЕРЕРЫВЕ</div><h2>Можно выдохнуть.</h2><p>Заказы подождут. Вернись в рейс, когда будешь готов.</p><button class="primary" id="resume">Продолжить →</button><button class="quiet" id="exit">Закончить без награды</button>',
  );
  $("#resume").onclick = resume;
  $("#exit").onclick = () => {
    mode = "idle";
    $("#overlay").classList.add("hidden");
    $("#tip").classList.remove("hidden");
    $("#pause").classList.add("hidden");
    $("#play").innerHTML = "<span>Отправиться в рейс</span><span>→</span>";
    state = freshRun();
    hud();
  };
}
function finish() {
  mode = "ended";
  const coins = reward(state),
    record = state.score > save.best;
  save = {
    ...save,
    best: Math.max(save.best, state.score),
    coins: save.coins + coins,
    runs: save.runs + 1,
  };
  persist();
  $("#pause").classList.add("hidden");
  $("#play").innerHTML = "<span>Ещё один рейс</span><span>→</span>";
  modal(
    `<div class="eyebrow">${record ? "НОВЫЙ ЛИЧНЫЙ РЕКОРД" : "НОЧНАЯ СМЕНА ЗАВЕРШЕНА"}</div><h2>${state.hits ? "Город стал теплее." : "Завтра получится!"}</h2><div class="result-score">${state.score}</div><div class="result-row"><span>Доставки</span><strong>${state.hits}</strong></div><div class="result-row"><span>Лучшее комбо</span><strong>${state.bestCombo}</strong></div><div class="result-row"><span>Чаевые</span><strong>+${coins} ✦</strong></div><p>«Каждый ужин — маленькое доброе дело».<br>— Тётушка Ко</p><button class="primary" id="again">Ещё один рейс →</button><button class="quiet" id="share">Поделиться рекордом</button><button class="quiet" id="close">Вернуться в порт</button>`,
  );
  $("#again").onclick = start;
  $("#close").onclick = () => {
    $("#overlay").classList.add("hidden");
    $("#tip").classList.remove("hidden");
  };
  $("#share").onclick = async () => {
    const text = `Мой рейс в Noriwake: ${state.score} очков, ${state.hits} доставок, комбо ${state.bestCombo}!`;
    try {
      if (navigator.share) await navigator.share({ title: "Noriwake", text });
      else {
        await navigator.clipboard.writeText(text);
        toast("Результат скопирован.");
      }
    } catch (e) {
      if (e.name !== "AbortError")
        toast("Не удалось поделиться. Сделай скриншот результата.");
    }
  };
}
$("#play").onclick = () =>
  mode === "playing" ? pause() : mode === "paused" ? resume() : start();
$("#pause").onclick = pause;
$("#sound").onclick = () => {
  muted = !muted;
  $("#sound").textContent = `Звук: ${muted ? "выкл." : "вкл."}`;
  $("#sound").setAttribute(
    "aria-label",
    muted ? "Включить звук" : "Выключить звук",
  );
  sound();
};
document.addEventListener("visibilitychange", () => {
  if (document.hidden) pause();
});
window.addEventListener("blur", pause);
document.addEventListener("keydown", (e) => {
  if (e.code === "Escape") {
    if (mode === "playing") pause();
    else if (mode === "paused" && $("#resume")) resume();
    else if (mode !== "paused") $("#overlay").classList.add("hidden");
  }
  if (e.key === "Tab" && !$("#overlay").classList.contains("hidden")) {
    const b = [...$("#overlay").querySelectorAll("button:not(:disabled), a[href]")];
    if (e.shiftKey && document.activeElement === b[0]) {
      e.preventDefault();
      b.at(-1)?.focus();
    } else if (!e.shiftKey && document.activeElement === b.at(-1)) {
      e.preventDefault();
      b[0]?.focus();
    }
  }
});
function collection() {
  if (mode === "playing") pause();
  modal(
    `<div class="eyebrow">ТВОЯ ПЛАВУЧАЯ КУХНЯ</div><h2>Новый цвет ночи.</h2><p>Чаевые: ${save.coins} ✦. Только игровая косметика — никаких покупок за реальные деньги.</p>${SKINS.map((s) => `<div class="skin"><div class="swatch" style="background:${s.color}"></div><div class="skin-info">${s.name}<small>${save.owned.includes(s.id) ? "В коллекции" : s.cost + " чаевых"}</small></div><button class="quiet" data-skin="${s.id}" ${save.skin === s.id || (!save.owned.includes(s.id) && save.coins < s.cost) ? "disabled" : ""}>${save.skin === s.id ? "Выбрано" : save.owned.includes(s.id) ? "Надеть" : "Открыть"}</button></div>`).join("")}<p>Коллекция хранится на этом устройстве. Это не NFT; подключение кошелька появится на следующем этапе.</p><button class="primary" id="close">${mode === "paused" ? "Вернуться в рейс" : "В порт"} →</button>`,
  );
  document.querySelectorAll("[data-skin]").forEach(
    (b) =>
      (b.onclick = () => {
        save = purchase(save, b.dataset.skin);
        persist();
        collection();
      }),
  );
  $("#close").onclick = () =>
    mode === "paused" ? resume() : $("#overlay").classList.add("hidden");
}
$("#collection").onclick = collection;
$("#about").onclick = () => {
  if (mode === "playing") pause();
  modal(
    '<div class="eyebrow">ПРОТОТИП 0.1</div><h2>Сначала — игра.</h2><p>Оригинальный веб-прототип Noriwake с Android-оболочкой. Код, персонажи и графика Zooshi не включены. Все изображения здесь нарисованы программно.</p><p>Название рабочее: проверка товарного знака не завершена. NFT, кошелек и сетевой лидерборд пока не реализованы. Очки и чаевые не имеют денежной стоимости.</p><p><a href="./THIRD_PARTY_NOTICES.txt" target="_blank" rel="noopener">Лицензии npm-библиотек ↗</a><br><a href="./ANDROID_NOTICES.txt" target="_blank" rel="noopener">Предварительный Android-реестр ↗</a><br>Полный аудит Android-зависимостей перед релизом ещё предстоит.</p><button class="primary" id="close">Понятно →</button>',
  );
  $("#close").onclick = () =>
    mode === "paused" ? resume() : $("#overlay").classList.add("hidden");
};
canvas.addEventListener("pointerdown", (e) => {
  if (mode !== "playing") return;
  const r = canvas.getBoundingClientRect(),
    x = e.clientX - r.left,
    y = e.clientY - r.top;
  const t = targets.find(
    (t) =>
      !t.fed &&
      Math.hypot(x - t.x * W, y - t.y * H) <
        Math.max(32, Math.min(W, H) * 0.058),
  );
  shots.push({ x: W * 0.5, y: H * 0.84, tx: x, ty: y, life: 0 });
  if (t) {
    t.fed = true;
    state = deliver(state);
    sound(450 + Math.min(state.combo, 15) * 45);
    particles.push({
      x: t.x * W,
      y: t.y * H - 45,
      text:
        state.wave > 0
          ? "Горячо! ×2"
          : "Спасибо! +" + 100 * Math.min(5, 1 + Math.floor(state.combo / 5)),
      life: 1.2,
    });
  } else {
    state = miss(state);
    sound(140);
    particles.push({ x, y, text: "Мимо", life: 0.6 });
  }
  hud();
});
function rr(x, y, w, h, r, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.fill();
}
function ellipse(x, y, rx, ry, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  ctx.fill();
}
function line(x, y, x2, y2, color, width = 1) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}
function text(s, x, y, size, color) {
  ctx.font = `700 ${size}px system-ui`;
  ctx.textAlign = "center";
  ctx.fillStyle = color;
  ctx.fillText(s, x, y);
}
function animal(t) {
  const x = t.x * W,
    y = t.y * H,
    s = Math.max(0.7, Math.min(W / 700, 1.1));
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  ellipse(0, 32, 33, 9, "#071b2860");
  rr(-20, 5, 40, 31, 13, ["#e7a477", "#91bbb2", "#b5a6d5"][t.kind]);
  ellipse(-19, -21, 11, 13, "#9b7161");
  ellipse(19, -21, 11, 13, "#9b7161");
  ellipse(0, -9, 27, 25, ["#c59978", "#9c9a9a", "#d6b091"][t.kind]);
  if (t.kind === 1) {
    ellipse(-12, -10, 10, 7, "#405262");
    ellipse(12, -10, 10, 7, "#405262");
  }
  ellipse(-10, -11, 2.8, 3.5, "#192b31");
  ellipse(10, -11, 2.8, 3.5, "#192b31");
  ellipse(0, -1, 7, 4, "#554237");
  rr(-14, 12, 28, 19, 4, "#eff2df");
  line(0, 14, 0, 30, "#b7c9bf");
  if (t.fed) {
    text("♥", 0, -46, 23, "#a4ffd9");
  } else {
    const yy = -64 + Math.sin(clock * 3 + t.phase) * 3;
    rr(-22, yy - 14, 44, 29, 10, "#f6f0dc");
    sushi(0, yy, 1);
    ctx.fillStyle = "#f6f0dc";
    ctx.beginPath();
    ctx.moveTo(-5, yy + 14);
    ctx.lineTo(3, yy + 20);
    ctx.lineTo(8, yy + 14);
    ctx.fill();
  }
  ctx.restore();
}
function sushi(x, y, s) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  rr(-12, -5, 24, 13, 6, "#fff6de");
  rr(-14, -9, 28, 9, 4, "#ef946f");
  rr(-3, -10, 6, 19, 1, "#255a53");
  ctx.restore();
}
function draw() {
  ctx.clearRect(0, 0, W, H);
  const g = ctx.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, "#214959");
  g.addColorStop(0.6, "#173e4b");
  g.addColorStop(1, "#225657");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  // Deep canal, broken reflections and diagonal ripples.
  for (let i = 0; i < 40; i++) {
    const y = (i * 37 + clock * 16) % (H + 30),
      x = W * (0.29 + ((i * 73) % 100) / 240);
    line(x, y, x + 15 + (i % 4) * 11, y, "#8dd6c413", 1.5);
  }
  for (let side = 0; side < 2; side++) {
    ctx.save();
    if (side) {
      ctx.translate(W, 0);
      ctx.scale(-1, 1);
    }
    ctx.fillStyle = "#19313c";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(W * 0.2, 0);
    ctx.lineTo(W * 0.27, H);
    ctx.lineTo(0, H);
    ctx.fill();
    line(W * 0.2, 0, W * 0.27, H, "#627775", 3);
    for (let i = -1; i < 5; i++) {
      const y =
        ((i * 180 + clock * (mode === "playing" ? 8 : 2)) % (H + 200)) - 120;
      const b = W * 0.17;
      rr(-15, y, b, 115, 9, ["#334b55", "#3e4856", "#314d52"][(i + 4) % 3]);
      rr(8, y + 12, b - 22, 67, 4, "#142d39");
      for (let j = 0; j < 3; j++) {
        rr(
          17 + (j * (b - 33)) / 3,
          y + 24,
          Math.max(7, (b - 44) / 3),
          28,
          2,
          j === 1 ? "#a8bea16b" : "#e6b084a0",
        );
      }
      rr(0, y + 90, b + 9, 10, 2, "#5a6863");
      line(b + 5, y + 90, b + 21, y + 125, "#233b40", 4);
      rr(b - 25, y + 115, 46, 20, 3, "#c38b65");
      text(i % 2 ? "24" : "KO", b - 2, y + 130, 13, "#ffe4af");
      ellipse(b + 10, y + 157, 8, 12, "#ffd199");
      ellipse(b + 10, y + 172, 17, 35, "#ffce8110");
      line(0, y + 100, b + 12, y + 127, "#b3977250", 1);
    }
    ctx.restore();
  }
  // A string of lanterns over the channel.
  ctx.beginPath();
  ctx.moveTo(0, H * 0.17);
  ctx.quadraticCurveTo(W * 0.5, H * 0.37, W, H * 0.14);
  ctx.strokeStyle = "#142c36";
  ctx.lineWidth = 2;
  ctx.stroke();
  for (let i = 1; i < 8; i++) {
    const x = (W * i) / 8,
      u = i / 8,
      y = H * (0.17 * (1 - u) * (1 - u) + 0.74 * u * (1 - u) + 0.14 * u * u);
    line(x, y, x, y + 12, "#1c343b");
    ellipse(x, y + 20, 6, 9, i % 2 ? "#f2bb83" : "#a9dac0");
    ellipse(x, y + 20, 14, 19, "#ffc6810b");
  }
  for (const t of targets) {
    const x = t.x * W,
      y = t.y * H;
    rr(
      t.x < 0.5 ? 0 : x - 37,
      y + 25,
      t.x < 0.5 ? x + 37 : W - x + 37,
      20,
      3,
      "#7d7564",
    );
    for (let j = 0; j < 3; j++)
      line(
        t.x < 0.5 ? 0 : x - 37,
        y + 29 + j * 5,
        t.x < 0.5 ? x + 37 : W,
        y + 29 + j * 5,
        "#414f4c",
        1,
      );
    animal(t);
  }
  // Original vector kitchen boat.
  const bx = W * 0.5,
    by = H * 0.85 + Math.sin(clock * 2) * 3,
    bs = Math.min(W / 480, 1.1);
  ctx.save();
  ctx.translate(bx, by);
  ctx.scale(bs, bs);
  const color = SKINS.find((s) => s.id === save.skin).color;
  for (let i = 0; i < 3; i++)
    ellipse(0, 43 + i * 12, 34 + i * 8, 7, "#bce3ce13");
  ellipse(0, 8, 49, 67, "#092d3770");
  ctx.fillStyle = "#cba47a";
  ctx.beginPath();
  ctx.moveTo(-40, -43);
  ctx.lineTo(40, -43);
  ctx.lineTo(35, 37);
  ctx.quadraticCurveTo(0, 79, -35, 37);
  ctx.closePath();
  ctx.fill();
  rr(-31, -32, 62, 73, 12, "#314d50");
  rr(-28, -22, 56, 39, 5, "#f2dab0");
  sushi(-13, -5, 0.65);
  sushi(13, 5, 0.6);
  line(-33, -51, -33, 18, "#e4b98b", 4);
  line(33, -51, 33, 18, "#e4b98b", 4);
  rr(-43, -72, 86, 36, 7, color);
  for (let i = 0; i < 5; i++)
    rr(-40 + i * 17, -52, 14, 16, 3, i % 2 ? "#f7e7bf" : color);
  text("NORI", 0, -57, 12, "#25423e");
  ellipse(0, 31, 12, 11, "#d5a886");
  rr(-10, 18, 20, 9, 4, "#f7ebcd");
  ellipse(-48, -26, 7, 10, "#ffd198");
  if (state.wave > 0) {
    ctx.shadowColor = "#acffd9";
    ctx.shadowBlur = 22;
    line(-37, 38, 0, 61, color, 4);
    line(0, 61, 37, 38, color, 4);
  }
  ctx.restore();
  for (const s of shots) {
    const p = Math.min(s.life / 0.35, 1),
      x = s.x + (s.tx - s.x) * p,
      y = s.y + (s.ty - s.y) * p - Math.sin(p * Math.PI) * 65;
    sushi(x, y, 0.8);
  }
  for (const p of particles) {
    ctx.globalAlpha = Math.min(1, p.life * 2);
    text(p.text, p.x, p.y - (1.2 - p.life) * 30, 14, "#c3ffdb");
    ctx.globalAlpha = 1;
  }
}
function frame(ms) {
  const dt = Math.min((ms - previous) / 1000 || 0, 0.05);
  previous = ms;
  if (mode !== "paused") {
    clock += dt;
    if (mode === "playing") {
      state.remaining = Math.max(0, state.remaining - dt);
      state.wave = Math.max(0, state.wave - dt);
      spawn += dt;
      const speed = 0.033 + state.score / 400000;
      if (spawn > 2.5) {
        addTarget();
        spawn = 0;
      }
      for (const t of targets) {
        t.y += dt * speed;
        if (t.y > 0.93 && !t.fed) {
          t.fed = true;
          state = miss(state);
        }
      }
      targets = targets.filter((t) => t.y < 1.06);
      if (state.remaining <= 0) finish();
      hud();
    }
    for (const s of shots) s.life += dt;
    shots = shots.filter((s) => s.life < 0.35);
    for (const p of particles) p.life -= dt;
    particles = particles.filter((p) => p.life > 0);
  }
  draw();
  requestAnimationFrame(frame);
}
addTarget(0.36);
addTarget(0.63);
updateStats();
requestAnimationFrame(frame);
