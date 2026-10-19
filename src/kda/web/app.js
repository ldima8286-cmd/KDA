"use strict";

const GAME = "dota2";
const state = {
  heroImg: new Map(),
  heroName: new Map(),
  lastPlayerId: null,
  meta: null,
  metaSort: { key: "pro_pick", dir: -1, board: "pro" },
};

/* ---------- tiny helpers ---------- */
const $ = (sel) => document.querySelector(sel);
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
const fmtInt = (n) => (n == null ? "—" : Number(n).toLocaleString("en-US"));
const fmtK = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "k" : fmtInt(n));
const fmtDur = (s) => {
  if (!s) return "—";
  const m = Math.floor(s / 60), sec = s % 60;
  return `${m}:${String(sec).padStart(2, "0")}`;
};
const fmtAgo = (ts) => {
  if (!ts) return "—";
  const d = Math.floor(Date.now() / 1000 - ts);
  if (d < 3600) return Math.max(1, Math.floor(d / 60)) + " мин";
  if (d < 86400) return Math.floor(d / 3600) + " ч";
  return Math.floor(d / 86400) + " дн";
};
const rankName = (tier) => {
  if (!tier) return "Без ранга";
  const names = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"];
  const star = tier % 10;
  return `${names[Math.floor(tier / 10) - 1] || "—"}${star ? " " + star : ""}`;
};

function setStatus(text, kind) {
  const s = $("#status");
  s.className = "status" + (kind ? " " + kind : "");
  $("#status-text").textContent = text;
}
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 2600);
}

async function api(path) {
  const resp = await fetch(path, { headers: { Accept: "application/json" } });
  if (!resp.ok) {
    let detail = resp.statusText;
    try { detail = (await resp.json()).detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  return resp.json();
}

/* ---------- SVG line chart (hand-rolled, offline) ---------- */
function lineChart(points, { w = 640, h = 170, min = 0, max = 100 } = {}) {
  if (!points.length) return `<div class="muted" style="padding:24px 0">нет данных</div>`;
  const pad = { l: 34, r: 12, t: 14, b: 22 };
  const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
  const x = (i) => pad.l + (points.length === 1 ? iw / 2 : (i / (points.length - 1)) * iw);
  const y = (v) => pad.t + ih - ((v - min) / (max - min)) * ih;
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.winrate).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${pad.t + ih} L${x(0).toFixed(1)},${pad.t + ih} Z`;
  const grid = [0, 25, 50, 75, 100]
    .map((g) => {
      const yy = y(g);
      return `<line x1="${pad.l}" y1="${yy}" x2="${w - pad.r}" y2="${yy}" stroke="var(--line)" stroke-width="1"/>
              <text x="${pad.l - 8}" y="${yy + 3}" text-anchor="end" fill="var(--faint)" font-size="10" font-family="var(--mono)">${g}</text>`;
    })
    .join("");
  const dots = points
    .map((p, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(p.winrate).toFixed(1)}" r="2.6" fill="var(--gold)"/>`)
    .join("");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="xMidYMid meet">
    <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--gold)" stop-opacity=".22"/>
      <stop offset="100%" stop-color="var(--gold)" stop-opacity="0"/>
    </linearGradient></defs>
    ${grid}
    <path d="${area}" fill="url(#g)"/>
    <path d="${line}" fill="none" stroke="var(--gold)" stroke-width="1.8" stroke-linejoin="round"/>
    ${dots}
  </svg>`;
}

function heroCell(heroId, name) {
  const img = state.heroImg.get(heroId);
  const icon = img
    ? `<img class="hero-icon" src="${esc(img)}" loading="lazy" onerror="this.style.visibility='hidden'">`
    : `<div class="hero-icon"></div>`;
  return `<div class="hero-cell">${icon}<span class="name">${esc(name || state.heroName.get(heroId) || heroId)}</span></div>`;
}

/* ---------- views ---------- */
function renderHome() {
  const meta = state.meta;
  const contested = meta ? meta.pro_ranked.slice(0, 8) : [];
  const topPub = meta ? meta.pub_ranked.slice(0, 8) : [];
  const tiles = contested
    .map(
      (h) => `<div class="chip" data-hero="${h.hero_id}">${esc(h.name)} · ${h.pro_winrate}%</div>`
    )
    .join("");

  $("#view").innerHTML = `
    <p class="kicker">Обзор</p>
    <h1 class="title">Киберспорт-аналитика в одном месте</h1>
    <p class="subtitle">Введи Steam ID или ник игрока в поиске сверху — откроется Skill Lab. Ниже — текущая мета Dota 2.</p>

    <div class="panel">
      <div class="panel-head">
        <span class="panel-title">Самые контестуемые герои (Pro)</span>
        <span class="panel-note">${meta ? meta.count + " heroes" : "загрузка…"}</span>
      </div>
      <div class="chips">${tiles || '<span class="muted">нет данных</span>'}</div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="panel-title">Топ по пабам</span><span class="panel-note">pick rate</span></div>
      <table class="tbl">
        <thead><tr><th>Герой</th><th class="num">Pick share</th><th class="num">Побед</th></tr></thead>
        <tbody>
          ${topPub
            .map(
              (h) => `<tr>${`<td>${heroCell(h.hero_id, h.name)}</td>`}
                <td class="num">${h.pub_pick_share.toFixed(2)}%</td>
                <td class="num">${h.pub_winrate}%</td></tr>`
            )
            .join("") || '<tr><td colspan="3" class="muted">нет данных</td></tr>'}
        </tbody>
      </table>
    </div>`;
}

function statCard(label, value, sub, cls = "") {
  return `<div class="stat ${cls}">
    <div class="stat-label">${esc(label)}</div>
    <div class="stat-val">${value}</div>
    ${sub ? `<div class="stat-sub">${esc(sub)}</div>` : ""}
  </div>`;
}

function renderPlayer(profile) {
  const p = profile.player, s = profile.summary;
  const winClass = s.winrate >= 50 ? "win" : "loss";
  const avatar = p.avatar
    ? `<img class="player-avatar" src="${esc(p.avatar)}" onerror="this.style.visibility='hidden'">`
    : `<div class="player-avatar"></div>`;

  const heroesRows = profile.heroes
    .slice(0, 12)
    .map(
      (h) => `<tr>
        <td>${heroCell(h.hero_id, h.name)}</td>
        <td class="num">${h.matches}</td>
        <td class="num">${h.winrate}%</td>
        <td class="num">${h.avg_kda}</td>
      </tr>`
    )
    .join("");

  const recentRows = profile.recent
    .map(
      (m) => `<tr>
        <td>${heroCell(m.hero_id, h => h)}</td>
        <td>${h._}</td>
      </tr>`
    )
    .slice(0, 0)
    .join("");

  const recentHtml = profile.recent
    .map(
      (m) => `<tr>
        <td>${heroCell(m.hero_id, m.hero_name)}</td>
        <td><span class="badge ${m.win ? "win" : "loss"}">${m.win ? "Победа" : "Поражение"}</span></td>
        <td class="num">${h_ratio(m.kills, m.deaths, m.assists)}</td>
        <td class="num">${fmtK(m.gpm)} / ${fmtK(m.xpm)}</td>
        <td class="num">${fmtDur(m.duration)}</td>
        <td class="num faint">${fmtAgo(m.start_time)}</td>
      </tr>`
    )
    .join("");

  $("#view").innerHTML = `
    <p class="kicker">Skill Lab</p>
    <div class="player-head">
      ${avatar}
      <div class="player-id">
        <h1>${esc(p.name)}</h1>
        <div class="handle">account_id ${p.account_id}${p.country ? " · " + esc(p.country) : ""}</div>
      </div>
      <div class="rank-chip"><span class="star">◆</span> ${esc(rankName(p.rank_tier))}</div>
    </div>

    <div class="grid cols-4" style="margin-top:18px">
      ${statCard("Winrate", s.winrate + "<small>%</small>", `${s.wins}W · ${s.losses}L`, winClass)}
      ${statCard("Средний KDA", s.avg_kda, `${s.avg_kills} / ${s.avg_deaths} / ${s.avg_assists}`)}
      ${statCard("GPM", s.avg_gpm, `XPM ${s.avg_xpm}`, "accent")}
      ${statCard("Сыграно", s.matches, `${s.total_hours} ч в игре`)}
    </div>

    <div class="split" style="margin-top:18px">
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Динамика winrate</span><span class="panel-note">окно ${5} игр</span></div>
        ${lineChart(profile.trend || [])}
      </div>
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Лучшие герои</span><span class="panel-note">${profile.heroes.length}</span></div>
        <table class="tbl">
          <thead><tr><th>Герой</th><th class="num">Игр</th><th class="num">WR</th><th class="num">KDA</th></tr></thead>
          <tbody>${heroesRows || '<tr><td colspan="4" class="muted">нет данных</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="panel-title">Последние матчи</span><span class="panel-note">${profile.recent.length}</span></div>
      <table class="tbl">
        <thead><tr><th>Герой</th><th>Итог</th><th class="num">K / D / A</th><th class="num">GPM / XPM</th><th class="num">Длит.</th><th class="num">Когда</th></tr></thead>
        <tbody>${recentRows || '<tr><td colspan="6" class="muted">нет данных</td></tr>'}</tbody>
      </table>
    </div>`;
}

function renderMeta() {
  const meta = state.meta;
  if (!meta) { $("#view").innerHTML = `<div class="panel"><div class="muted">Загрузка…</div></div>`; return; }
  const board = state.metaSort.board === "pro" ? meta.pro_ranked : meta.pub_ranked;
  const { key, dir } = state.metaSort;
  const rows = [...board].sort((a, b) => (a[key] > b[key] ? dir : a[key] < b[key] ? -dir : 0));
  const arrow = (k) => (state.metaSort.key === k ? `<span class="arrow">${dir < 0 ? "↓" : "↑"}</span>` : "");
  const tbl = `
    <table class="tbl" id="meta-tbl">
      <thead><tr>
        <th>Герой</th>
        <th class="num sortable" data-k="pro_pick">Pro pick ${arrow("pro_pick")}</th>
        <th class="num sortable" data-k="pro_winrate">Pro WR ${arrow("pro_winrate")}</th>
        <th class="num sortable" data-k="pub_pick">Pub pick ${arrow("pub_pick")}</th>
        <th class="num sortable" data-k="pub_winrate">Pub WR ${arrow("pub_winrate")}</th>
        <th>Роли</th>
      </tr></thead>
      <tbody>
        ${rows
          .map(
            (h) => `<tr>
            <td>${heroCell(h.hero_id, h.name)}</td>
            <td class="num">${fmtInt(h.pro_pick)}</td>
            <td class="num">${h.pro_winrate}%</td>
            <td class="num">${fmtK(h.pub_pick)}</td>
            <td class="num">${h.pub_winrate}%</td>
            <td class="faint">${esc((h.roles || []).slice(0, 3).join(", "))}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>`;

  $("#view").innerHTML = `
    <p class="kicker">Meta Hub</p>
    <div class="panel">
      <div class="panel-head">
        <span class="panel-title">Мета героев</span>
        <div class="chips">
          <span class="chip" id="board-pro" ${state.metaSort.board === "pro" ? 'style="color:var(--gold);border-color:var(--gold-dim)"' : ""}>Pro</span>
          <span class="chip" id="board-pub" ${state.metaSort.board === "pub" ? 'style="color:var(--gold);border-color:var(--gold-dim)"' : ""}>Пабы</span>
        </div>
      </div>
      ${tbl}
    </div>`;

  document.querySelectorAll("#meta-tbl th.sortable").forEach((th) =>
    th.addEventListener("click", () => {
      const k = th.dataset.k;
      if (state.metaSort.key === k) state.metaSort.dir *= -1;
      else { state.metaSort.key = k; state.metaSort.dir = -1; }
      renderMeta();
    })
  );
  $("#board-pro").addEventListener("click", () => { state.metaSort.board = "pro"; renderMeta(); });
  $("#board-pub").addEventListener("click", () => { state.metaSort.board = "pub"; renderMeta(); });
}

/* ---------- navigation & data ---------- */
function setView(name) {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("is-active", b.dataset.view === name));
  if (name === "home") renderHome();
  else if (name === "player") {
    if (state.lastPlayerId) loadPlayer(state.lastPlayerId);
    else $("#view").innerHTML = `<div class="panel"><p class="kicker">Skill Lab</p><div class="muted">Найди игрока через поиск сверху.</div></div>`;
  } else if (name === "meta") renderMeta();
}

async function loadMeta(showStatus = false) {
  try {
    if (showStatus) setStatus("загрузка меты…", "is-busy");
    const meta = await api(`/api/meta?game=${GAME}`);
    state.meta = meta;
    meta.heroes.forEach((h) => {
      if (h.img) state.heroImg.set(h.hero_id, h.img);
      state.heroName.set(h.hero_id, h.name);
    });
    if (showStatus) setStatus("готов", "is-ok");
    return meta;
  } catch (e) {
    setStatus("ошибка меты", "is-error");
    throw e;
  }
}

async function loadPlayer(id) {
  state.lastPlayerId = id;
  setStatus("загрузка игрока…", "is-busy");
  $("#view").innerHTML = `<div class="view-loading"><div class="spinner"></div></div>`;
  try {
    const profile = await api(`/api/players/${id}?game=${GAME}&limit=30`);
    renderPlayer(profile);
    setStatus("готов", "is-ok");
  } catch (e) {
    $("#view").innerHTML = `<div class="panel"><p class="kicker">Skill Lab</p><div class="err">Не удалось загрузить игрока: ${esc(e.message)}</div></div>`;
    setStatus("ошибка", "is-error");
  }
}

async function onSearch(q) {
  q = q.trim();
  if (!q) return;
  setStatus("поиск…", "is-busy");
  try {
    if (/^\d+$/.test(q)) return loadPlayer(Number(q));
    const res = await api(`/api/search?game=${GAME}&q=${encodeURIComponent(q)}`);
    const hits = res.results || [];
    if (!hits.length) { toast("Игрок не найден"); setStatus("готов"); return; }
    loadPlayer(hits[0].account_id);
  } catch (e) {
    setStatus("ошибка поиска", "is-error");
    toast("Ошибка: " + e.message);
  }
}

/* ---------- boot ---------- */
async function boot() {
  $("#search-form").addEventListener("submit", (e) => { e.preventDefault(); onSearch($("#search-input").value); });
  document.querySelectorAll(".nav-item").forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));
  $("#refresh-global").addEventListener("click", async () => {
    try { state.meta = null; await loadMeta(true); toast("Мета обновлена"); setView("meta"); }
    catch (e) { toast("Не удалось обновить"); }
  });
  renderHome();
  setStatus("загрузка меты…", "is-busy");
  try { await loadMeta(); setStatus("готов", "is-ok"); renderHome(); }
  catch (e) { setStatus("мета недоступна", "is-error"); toast("Мета недоступна офлайн"); }
}

document.addEventListener("DOMContentLoaded", boot);
