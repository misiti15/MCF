/* Trivia web app. Two backends with one interface:
   - Remote: the FastAPI server (normal use).
   - Local:  everything in the browser, used by the standalone demo build (window.TRIVIA_CONTENT is set). */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
const store = {
  get(k, d) { try { const v = localStorage.getItem('trivia.' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem('trivia.' + k, JSON.stringify(v)); } catch {} },
};

const WIN = ['NAILED IT','BIG BRAIN','TAKE A BOW','FLAWLESS','CERTIFIED NERD','BULLSEYE','CHEF\'S KISS','HOME RUN','SWISH!','MIC DROP','TEXTBOOK','LEGEND','BOOM','GENIUS ALERT','STONE COLD'];
const LOSE = ['OOF.','WHIFF!','NOPE.','BRICK.','WOMP WOMP','YIKES','AIRBALL','FUMBLE!','STRIKE THREE','FLAG ON THE PLAY','NOT TODAY','BONK','OUCH','SWING AND A MISS','RED CARD'];
const WIN_SUB = ['Somebody call Jeopardy.','Your brain deserves a raise.','That was a deep cut and you knew it.','Frame that one.','Clean. Real clean.','The crowd goes wild.'];
const LOSE_SUB = ['Shake it off. The next one is yours.','Even the greats whiff sometimes.','Now you know. That counts for something.','The tidbit below is your revenge.','Walk it off, champ.','Tomorrow you get your rematch.'];
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
const pick = a => a[Math.floor(Math.random() * a.length)];

/* ---------------- shared helpers (local backend + matcher) ---------------- */
const STOP = new Set(['the','a','an','of','and','about','trivia','history','facts','fact','stuff','questions','i','like','love','my']);
const norm = t => t.toLowerCase().replace(/&/g,' and ').replace(/[^a-z0-9 ]+/g,' ').split(/\s+/).filter(w => w && !STOP.has(w)).join(' ');
function dice(a, b) {
  if (a.length < 2 || b.length < 2) return a === b ? 1 : 0;
  const grams = s => { const m = new Map(); for (let i = 0; i < s.length - 1; i++) { const g = s.slice(i, i + 2); m.set(g, (m.get(g) || 0) + 1); } return m; };
  const A = grams(a), B = grams(b); let hit = 0;
  for (const [g, n] of A) hit += Math.min(n, B.get(g) || 0);
  return 2 * hit / (a.length + b.length - 2);
}
function phraseScore(q, p) {
  q = norm(q); p = norm(p); if (!q || !p) return 0; if (q === p) return 1;
  const qt = new Set(q.split(' ')), pt = new Set(p.split(' '));
  const inter = [...qt].filter(x => pt.has(x)).length, uni = new Set([...qt, ...pt]).size;
  const contained = (` ${q} `.includes(` ${p} `) || ` ${p} `.includes(` ${q} `)) ? 0.9 : 0;
  return Math.max(inter / uni, contained, dice(q, p) * 0.95);
}

/* ---------------- Local backend ---------------- */
function makeLocal(C) {
  const NODE = {}, PARENT = {}, ROOTS = C.topics.topics.map(t => t.id);
  (function walk(list, parent) { for (const n of list) { NODE[n.id] = n; PARENT[n.id] = parent; if (n.kids) walk(n.kids, n.id); } })(C.topics.topics, null);
  const QS = Object.fromEntries(C.questions.questions.map(q => [q.id, q]));
  const lineage = id => { const a = []; while (id) { a.unshift(id); id = PARENT[id]; } return a; };
  const under = ids => { const out = new Set(), st = [...ids]; while (st.length) { const t = st.pop(); if (NODE[t] && !out.has(t)) { out.add(t); (NODE[t].kids || []).forEach(k => st.push(k.id)); } } return out; };
  const qFor = ids => { const s = under(ids); return Object.values(QS).filter(q => s.has(q.topic)); };
  const cfg = C.config;
  let S = store.get('local', null);
  const save = () => store.set('local', S);
  const today = () => new Date().toLocaleDateString('en-CA');
  const rng = seed => { let h = 1779033703 ^ seed.length; for (let i = 0; i < seed.length; i++) { h = Math.imul(h ^ seed.charCodeAt(i), 3432918353); h = h << 13 | h >>> 19; } return () => { h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13, 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; }; };
  const choice = (r, a) => a[Math.floor(r() * a.length)];
  const pub = (q, kind) => ({ id: q.id, kind, level: q.level, points: cfg.level_points[q.level], question: q.question, options: q.options, image: q.image ? C.images[q.image] : null, topic: lineage(q.topic).slice(-2).map(t => NODE[t].name) });
  const reveal = (q, a) => ({ choice: a.choice, correct: a.correct, answer: q.answer, answer_text: q.options[q.answer], explanation: q.explanation, tidbit: q.tidbit, source: q.source, points: a.points });
  const seen = () => { const m = {}; for (const [d, ids] of Object.entries(S.drops)) ids.forEach(i => m[i] = m[i] > d ? m[i] : d); for (const [d, ids] of Object.entries(S.bonus)) ids.forEach(i => m[i] = m[i] > d ? m[i] : d); return m; };
  const owner = q => { const line = lineage(q.topic); return S.user.topics.find(t => line.includes(t)) || q.topic; };
  function pickQs(levels, r, sortRamp) {
    const pool = qFor(S.user.topics), sn = seen();
    const unseen = pool.filter(q => !(q.id in sn)), reruns = pool.filter(q => q.id in sn).sort((a, b) => sn[a.id] < sn[b.id] ? -1 : 1);
    const chosen = [], used = {};
    for (const want of levels) {
      for (const bucket of [unseen, reruns]) {
        const left = bucket.filter(q => !chosen.includes(q)); if (!left.length) continue;
        const close = Math.min(...left.map(q => Math.abs(q.level - want)));
        let c = left.filter(q => Math.abs(q.level - want) === close);
        const few = Math.min(...c.map(q => used[owner(q)] || 0));
        c = c.filter(q => (used[owner(q)] || 0) === few);
        if (bucket === reruns) c = c.slice(0, 1);
        const q = choice(r, c); chosen.push(q); used[owner(q)] = (used[owner(q)] || 0) + 1; break;
      }
    }
    return sortRamp ? chosen.sort((a, b) => a.level - b.level) : chosen;
  }
  function drop(day) {
    if (!S.drops[day]) {
      const r = rng(S.user.id + day), n = S.user.drop_size, mix = S.user.mix;
      const levels = mix === 'deep' ? Array(n).fill(4) : mix === 'mix' ? Array.from({ length: n }, () => 1 + Math.floor(r() * 4)) : cfg.ramps[n];
      const qs = pickQs(levels, r, mix === 'ramp');
      if (!qs.length) throw Object.assign(new Error('No questions for your topics yet.'), { status: 404 });
      S.drops[day] = qs.map(q => q.id); save();
    }
    return S.drops[day];
  }
  const ans = (day, kind) => S.answers.filter(a => a.day === day && (!kind || a.kind === kind));
  const streakNow = () => { let s = 0; for (const a of [...S.answers].reverse()) { if (a.kind !== 'drop') continue; if (!a.correct) break; s++; } return s; };
  const mult = s => (cfg.streak_multipliers.find(([n]) => s >= n) || [0, 1])[1];
  const dayScore = day => { const ids = S.drops[day] || [], a = ans(day, 'drop'); let t = a.reduce((x, y) => x + y.points, 0); if (ids.length && a.length === ids.length && a.every(x => x.correct)) t += cfg.perfect_drop_bonus; return t; };
  function state() {
    const day = today(), ids = drop(day), done = Object.fromEntries(ans(day, 'drop').map(a => [a.qid, a]));
    return { day, questions: ids.map(i => ({ ...pub(QS[i], 'drop'), ...(done[i] ? { answered: reveal(QS[i], done[i]) } : {}) })), complete: ids.every(i => done[i]), score: dayScore(day), bonus_left: Math.max(0, cfg.bonus_per_day - (S.bonus[day] || []).length) };
  }
  const err = (m, s) => Promise.reject(Object.assign(new Error(m), { status: s }));
  const tree = () => { const node = id => { const n = NODE[id]; return { id, name: n.name, depth: lineage(id).length - 1, soon: !!n.soon, questions: qFor([id]).length, kids: (n.kids || []).map(k => node(k.id)) }; }; return ROOTS.map(node); };
  return {
    live: false,
    async config() { return cfg; },
    async topics() { return { tree: tree(), packs: C.topics.packs.map(p => ({ ...p, questions: qFor(p.topics).length })) }; },
    async search(text) {
      const out = [];
      for (const n of Object.values(NODE)) { const s = Math.max(...[n.name, ...(n.aliases || [])].map(p => phraseScore(text, p))); if (s >= 0.5) out.push({ s, d: lineage(n.id).length - 1, n }); }
      out.sort((a, b) => (Math.round(b.s * 100) - Math.round(a.s * 100)) || b.d - a.d);
      return out.slice(0, 3).map(({ s, d, n }) => ({ id: n.id, name: n.name, score: s, depth: d, path: lineage(n.id).map(t => NODE[t].name), questions: qFor([n.id]).length, soon: !!n.soon, confident: s >= 0.8 }));
    },
    async me() { return S && S.user; },
    async signup(body) { S = { user: { id: Math.random().toString(16).slice(2), ...body }, drops: {}, bonus: {}, answers: [], requests: [] }; save(); return S.user; },
    async saveSettings(p) { Object.assign(S.user, p); save(); return S.user; },
    async setTopics(t) { S.user.topics = t; save(); return { topics: t }; },
    async today() { return state(); },
    async answer(qid, c) {
      const day = today(), ids = drop(day), q = QS[qid];
      const kind = ids.includes(qid) ? 'drop' : (S.bonus[day] || []).includes(qid) ? 'bonus' : null;
      if (!kind) return err("That question isn't in today's drop.", 403);
      if (S.answers.some(a => a.qid === qid && a.day === day)) return err('Already answered.', 409);
      const correct = c === q.answer; let streak = streakNow(), points = 0;
      if (kind === 'drop') { streak = correct ? streak + 1 : 0; if (correct) points = Math.round(cfg.level_points[q.level] * mult(streak)); }
      S.answers.push({ qid, day, kind, level: q.level, choice: c, correct, points }); save();
      const st = state(), perfect = kind === 'drop' && st.complete && st.questions.every(x => x.answered.correct);
      return { ...reveal(q, { choice: c, correct, points }), kind, streak, multiplier: kind === 'drop' ? mult(streak) : null, drop_complete: st.complete, perfect_drop: perfect, day_score: st.score, bonus_left: st.bonus_left };
    },
    async oneMore() {
      const st = state(), day = st.day;
      if (!st.complete) return err("Finish today's drop first.", 409);
      const pending = (S.bonus[day] || []).find(i => !S.answers.some(a => a.qid === i && a.day === day));
      if (pending) return { ...pub(QS[pending], 'bonus'), bonus_left: st.bonus_left };
      if (st.bonus_left <= 0) return err(`That's all ${cfg.bonus_per_day} bonus questions for today. New drop tomorrow.`, 429);
      const r = rng(S.user.id + day + 'b' + st.bonus_left), q = pickQs([1 + Math.floor(r() * 4)], r, false)[0];
      if (!q) return err('No more questions for your topics right now.', 404);
      (S.bonus[day] = S.bonus[day] || []).push(q.id); save();
      return { ...pub(q, 'bonus'), bonus_left: st.bonus_left - 1 };
    },
    async stats() {
      const levels = {};
      for (const l of [1, 2, 3, 4]) { const a = S.answers.filter(x => x.level === l), c = a.filter(x => x.correct).length; levels[l] = { answered: a.length, correct: c, accuracy: a.length ? c / a.length : null }; }
      const days = [...new Set(S.answers.filter(a => a.kind === 'drop').map(a => a.day))];
      const fin = new Set(days.filter(d => ans(d, 'drop').length === (S.drops[d] || []).length));
      let streak = 0; const d = new Date(); if (!fin.has(d.toLocaleDateString('en-CA'))) d.setDate(d.getDate() - 1);
      while (fin.has(d.toLocaleDateString('en-CA'))) { streak++; d.setDate(d.getDate() - 1); }
      let best = 0, run = 0; for (const a of S.answers) if (a.kind === 'drop') { run = a.correct ? run + 1 : 0; best = Math.max(best, run); }
      return { levels, total_points: days.reduce((t, d) => t + dayScore(d), 0), today: dayScore(today()), day_streak: streak, answer_streak: streakNow(), best_answer_streak: best };
    },
    async request(text) {
      const m = await this.search(text);
      if (m.length && m[0].confident && !m[0].soon) return { queued: false, matches: m };
      if (S) { S.requests.unshift(text); save(); }
      return { queued: true, matches: m, status: 'Researching. It opens once enough questions pass two-source checks.' };
    },
    requests() { return (S && S.requests) || []; },
    async flag() { return { ok: true, message: 'Thanks. A person will re-check this one against its sources.' }; },
    reset() { S = null; save(); },
  };
}

/* ---------------- Remote backend ---------------- */
function makeRemote() {
  const fromLink = location.pathname.match(/^\/d\/([\w-]{16,})$/);
  let token = fromLink ? fromLink[1] : store.get('token', null);
  if (fromLink) { store.set('token', token); history.replaceState(null, '', '/'); }
  async function call(method, path, body) {
    const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json', ...(token ? { 'X-User-Token': token } : {}) }, body: body ? JSON.stringify(body) : undefined });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(typeof j.detail === 'string' ? j.detail : 'That didn\'t save. Check the fields and try again.'), { status: r.status });
    return j;
  }
  return {
    live: true,
    config: () => call('GET', '/api/config'),
    topics: () => call('GET', '/api/topics'),
    search: q => call('GET', '/api/topics/search?q=' + encodeURIComponent(q)).then(r => r.matches),
    me: () => token ? call('GET', '/api/me').catch(() => null) : Promise.resolve(null),
    signup: body => call('POST', '/api/users', body).then(r => { token = r.token; store.set('token', token); return r.user; }),
    saveSettings: p => call('PATCH', '/api/me', p),
    setTopics: t => call('PUT', '/api/me/topics', { topics: t }),
    today: () => call('GET', '/api/drop/today'),
    answer: (id, c) => call('POST', '/api/answer', { question_id: id, choice: c }),
    oneMore: () => call('POST', '/api/one-more'),
    stats: () => call('GET', '/api/stats'),
    request: text => call('POST', '/api/requests', { text }).then(r => { const l = store.get('requests', []); if (r.queued) { l.unshift(text); store.set('requests', l); } return r; }),
    requests: () => store.get('requests', []),
    flag: id => call('POST', '/api/flags', { question_id: id }),
    reset() { token = null; store.set('token', null); },
  };
}

const B = window.TRIVIA_CONTENT ? makeLocal(window.TRIVIA_CONTENT) : makeRemote();
let CFG, TREE, PACKS, USER, NODES = {};
let sound = store.get('sound', true);

/* ---------------- shell ---------------- */
const VIEWS = ['today', 'topics', 'scores', 'settings'];
function tabs(show) {
  $('#nav').hidden = !show;
  $('#nav').innerHTML = VIEWS.map(v => `<button role="tab" data-v="${v}" aria-selected="${v === view}">${{ today: 'Today', topics: 'My topics', scores: 'Scores', settings: 'Settings' }[v]}</button>`).join('');
  $('#nav').querySelectorAll('button').forEach(b => b.onclick = () => go(b.dataset.v));
}
let view = 'today';
function go(v) { view = v; tabs(true); ({ today: renderToday, topics: renderTopics, scores: renderScores, settings: renderSettings })[v](); window.scrollTo({ top: 0 }); }
const main = () => $('#main');
const levelName = l => (CFG.level_themes[(USER && USER.level_theme) || CFG.default_level_theme] || CFG.level_themes[CFG.default_level_theme])[l - 1];
const pips = l => `<span class="pips">${[1, 2, 3, 4].map(i => `<i class="${i <= l ? 'on' : ''}"></i>`).join('')}</span>`;
const depthName = d => ['Broad', 'Narrower', 'Niche', 'Deep cut', 'Deep cut'][Math.min(d, 4)];
function showError(e, where) { (where || main()).insertAdjacentHTML('afterbegin', `<div class="panel" role="alert"><b>${esc(e.message)}</b></div>`); }

/* ---------------- onboarding ---------------- */
let OB = null;
function startOnboarding() {
  OB = { step: 1, mode: 'type', topics: [], swipeIdx: 0, settings: { drop_size: 3, mix: 'ramp', channel: 'push', send_days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], send_time: '12:15', level_theme: CFG.default_level_theme } };
  tabs(false); renderOnboarding();
}
function renderOnboarding() {
  const steps = `<div class="steps" aria-label="Step ${OB.step} of 3">${[1, 2, 3].map(i => `<i class="${i <= OB.step ? 'on' : ''}"></i>`).join('')}</div>`;
  if (OB.step === 1) {
    main().innerHTML = `<div class="stack">${steps}
      <div class="panel"><h2>What are you into?</h2>
        <p>Pick three or so. The more specific, the better the questions get.</p>
        <div class="row" role="tablist">${[['type', 'Type it'], ['packs', 'Starter packs'], ['swipe', 'Quick pick']].map(([k, n]) => `<button class="chip" aria-pressed="${OB.mode === k}" data-m="${k}">${n}</button>`).join('')}</div>
        <div id="obBody"></div>
      </div>
      <div class="panel"><div class="label">Your picks</div><div class="row" id="obPicks"></div>
        <div class="actions"><button class="btn brand" id="obNext" ${OB.topics.length ? '' : 'disabled'}>Next</button><span class="note">${OB.topics.length ? '' : 'Add at least one topic to continue.'}</span></div></div></div>`;
    main().querySelectorAll('[data-m]').forEach(b => b.onclick = () => { OB.mode = b.dataset.m; renderOnboarding(); });
    renderPicks();
    ({ type: obType, packs: obPacks, swipe: obSwipe })[OB.mode]();
    $('#obNext').onclick = () => { OB.step = 2; renderOnboarding(); };
  } else if (OB.step === 2) {
    const deeper = OB.topics.filter(t => NODES[t] && NODES[t].kids.some(k => !k.soon));
    main().innerHTML = `<div class="stack">${steps}<div class="panel"><h2>Want to go deeper?</h2>
      <p>Optional. Narrower picks get you more specific questions. You keep the broad topic either way.</p>
      ${deeper.length ? deeper.map(t => `<div class="stack" style="gap:8px"><div class="label">${esc(NODES[t].name)}</div><div class="row">${NODES[t].kids.filter(k => !k.soon).map(k => `<button class="chip" data-add="${k.id}" aria-pressed="${OB.topics.includes(k.id)}">${esc(k.name)}</button>`).join('')}</div></div>`).join('') : '<p class="note">Your picks are already as specific as the library goes. Nice.</p>'}
      <div class="actions"><button class="btn ghost" id="obBack">Back</button><button class="btn brand" id="obNext">Next</button></div></div></div>`;
    main().querySelectorAll('[data-add]').forEach(b => b.onclick = () => { toggleOB(b.dataset.add); renderOnboarding(); });
    $('#obBack').onclick = () => { OB.step = 1; renderOnboarding(); };
    $('#obNext').onclick = () => { OB.step = 3; renderOnboarding(); };
  } else {
    main().innerHTML = `<div class="stack">${steps}<div class="panel"><h2>Your daily drop</h2>
      <p>A few questions a day, sent when you want them. You can always play more with "Give me one more".</p>
      <div id="obSettings"></div>
      <div class="actions"><button class="btn ghost" id="obBack">Back</button><button class="btn brand" id="obGo">Start my first drop</button></div></div></div>`;
    settingsForm($('#obSettings'), OB.settings, p => Object.assign(OB.settings, p), true);
    $('#obBack').onclick = () => { OB.step = 2; renderOnboarding(); };
    $('#obGo').onclick = async () => {
      try {
        USER = await B.signup({ topics: OB.topics, ...OB.settings, tz: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York' });
        OB = null; go('today');
      } catch (e) { showError(e); }
    };
  }
}
function renderPicks() {
  $('#obPicks').innerHTML = OB.topics.length ? OB.topics.map(t => `<span class="chip">${esc(NODES[t].name)}<button class="x" aria-label="Remove ${esc(NODES[t].name)}" data-rm="${t}">×</button></span>`).join('') : '<span class="note">Nothing yet.</span>';
  $('#obPicks').querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { toggleOB(b.dataset.rm); renderOnboarding(); });
}
function toggleOB(id) { OB.topics = OB.topics.includes(id) ? OB.topics.filter(t => t !== id) : [...OB.topics, id]; }
function obType() {
  $('#obBody').innerHTML = `<div class="search"><input id="obQ" placeholder="Try: Cincinnati Reds, Lamborghini, Marshall football" aria-label="Type an interest" autocomplete="off" maxlength="80"></div><div class="matches" id="obM"></div>
    <div class="label">Or tap a starting point</div><div class="row">${TREE.map(n => `<button class="chip" data-add="${n.id}" ${n.soon ? 'disabled title="Coming soon"' : ''} aria-pressed="${OB.topics.includes(n.id)}">${esc(n.name)}${n.soon ? ' · soon' : ''}</button>`).join('')}</div>`;
  $('#obBody').querySelectorAll('[data-add]').forEach(b => b.onclick = () => { toggleOB(b.dataset.add); renderOnboarding(); });
  const input = $('#obQ'); input.value = OB.q || ''; input.focus();
  let t; input.oninput = () => { clearTimeout(t); OB.q = input.value; t = setTimeout(() => searchInto($('#obM'), input.value, id => { toggleOB(id); OB.q = ''; renderOnboarding(); }), 150); };
  if (OB.q) input.oninput();
}
async function searchInto(el, text, onAdd) {
  if (text.trim().length < 2) { el.innerHTML = ''; return; }
  const m = await B.search(text);
  const picked = id => (OB ? OB.topics : USER.topics).includes(id);
  el.innerHTML = m.map((x, i) => `<div class="match"><div class="nm">${i === 0 && x.confident ? '' : '<span class="note">Did you mean </span>'}${esc(x.name)}<small>${esc(x.path.join(' › '))} · ${x.soon ? 'coming soon' : plural(x.questions, 'question')}</small></div>
      <span class="depth" data-d="${x.depth}">${depthName(x.depth)}</span>
      <button class="sm ${picked(x.id) ? 'on' : ''}" data-id="${x.id}" ${x.soon ? 'disabled' : ''}>${picked(x.id) ? '✓ Added' : '+ Add'}</button></div>`).join('')
    + `<div class="match"><div class="nm">${m.length && m[0].confident ? 'Not quite it?' : 'No exact match yet.'}<small>Ask for "${esc(text.trim())}" and we'll research it. It opens once enough questions pass source checks.</small></div><button class="sm" id="reqBtn">Request it</button></div>`;
  el.querySelectorAll('[data-id]').forEach(b => b.onclick = () => onAdd(b.dataset.id));
  $('#reqBtn').onclick = async () => { const r = await B.request(text.trim()); $('#reqBtn').outerHTML = `<span class="status">${r.queued ? 'REQUESTED' : 'ALREADY HERE'}</span>`; };
}
function obPacks() {
  $('#obBody').innerHTML = `<div class="packs">${PACKS.map(p => { const on = p.topics.every(t => OB.topics.includes(t)); return `<button class="pack" data-p="${p.id}" aria-pressed="${on}"><b>${esc(p.name)}</b><span>${esc(p.blurb)}</span><span class="mono">${plural(p.questions, 'question')}</span></button>`; }).join('')}</div>`;
  $('#obBody').querySelectorAll('[data-p]').forEach(b => b.onclick = () => {
    const p = PACKS.find(x => x.id === b.dataset.p), on = p.topics.every(t => OB.topics.includes(t));
    OB.topics = on ? OB.topics.filter(t => !p.topics.includes(t)) : [...new Set([...OB.topics, ...p.topics])]; renderOnboarding();
  });
}
function swipeDeck() { const out = []; const walk = (ns) => ns.forEach(n => { if (!n.soon && n.questions && n.depth >= 1 && n.depth <= 3) out.push(n); walk(n.kids); }); walk(TREE); return out; }
function obSwipe() {
  const deck = swipeDeck(), n = deck[OB.swipeIdx];
  if (!n) { $('#obBody').innerHTML = `<div class="swipe"><div class="ask">That's the whole deck.</div><button class="sm" id="again">Start over</button></div>`; $('#again').onclick = () => { OB.swipeIdx = 0; renderOnboarding(); }; return; }
  const path = []; let p = n; while (p) { path.unshift(p.name); p = Object.values(NODES).find(x => x.kids.includes(p)); }
  $('#obBody').innerHTML = `<div class="swipe"><span class="note">${OB.swipeIdx + 1} of ${deck.length}</span><div class="ask">Into ${esc(n.name)}?</div><span class="note">${esc(path.join(' › '))}</span>
    <div class="actions"><button class="btn ghost" id="nah">Nah</button><button class="btn brand" id="yes">Yes!</button></div></div>`;
  $('#nah').onclick = () => { OB.swipeIdx++; renderOnboarding(); };
  $('#yes').onclick = () => { if (!OB.topics.includes(n.id)) OB.topics.push(n.id); OB.swipeIdx++; renderOnboarding(); };
}

/* ---------------- today ---------------- */
let T = null; // {state, idx, bonus, revealed}
async function renderToday() {
  try { T = { state: await B.today(), bonus: null, last: null }; } catch (e) { main().innerHTML = ''; return showError(e); }
  drawToday();
}
function drawToday() {
  const st = T.state, qs = st.questions;
  const cur = T.bonus || T.last || qs.find(q => !q.answered);
  const prog = `<div class="progress" aria-label="Progress">${qs.map(q => `<i class="${q.answered ? (q.answered.correct ? 'ok' : 'no') : (cur && cur.id === q.id ? 'now' : '')}"></i>`).join('')}<span>${T.bonus ? 'Bonus round' : `${qs.filter(q => q.answered).length} of ${qs.length}`}</span></div>`;
  if (!cur) { main().innerHTML = `<div class="stack">${prog}${summary()}</div>`; wireSummary(); return; }
  main().innerHTML = `<div class="stack">${prog}${card(cur)}<div class="statline note" id="statline"></div></div>`;
  wireCard(cur);
}
function card(q) {
  return `<article class="card lvl" data-l="${q.level}" id="card">
    <div class="card-top"><span class="badge">${pips(q.level)} ${esc(levelName(q.level))}</span>${q.kind === 'bonus' ? '<span class="bonus-tag">BONUS · just for fun</span>' : ''}<span class="topic">${esc(q.topic.join(' · '))}</span><span class="pts mono">${q.kind === 'bonus' ? 'no points' : q.points + ' pts'}</span></div>
    <h2 class="q">${esc(q.question)}</h2>
    ${q.image ? `<div class="pic"><img src="${q.image.startsWith('data:') ? q.image : '/' + esc(q.image)}" alt=""></div>` : ''}
    <div class="opts">${q.options.map((o, i) => `<button class="opt" data-i="${i}"><span class="k">${'ABCD'[i]}</span><span>${esc(o)}</span></button>`).join('')}</div>
    <div id="rev"></div></article>`;
}
function wireCard(q) {
  const opts = [...document.querySelectorAll('.opt')];
  if (q.answered) return showReveal(q, q.answered, false);
  opts.forEach(b => b.onclick = async () => {
    opts.forEach(x => x.disabled = true);
    try { const r = await B.answer(q.id, +b.dataset.i); q.answered = r; T.last = q; T.state.score = r.day_score; T.state.bonus_left = r.bonus_left; showReveal(q, r, true); }
    catch (e) { opts.forEach(x => x.disabled = false); showError(e, $('#rev')); }
  });
}
function showReveal(q, r, fresh) {
  document.querySelectorAll('.opt').forEach((b, j) => { b.disabled = true; b.classList.add(j === r.answer ? 'right' : j === r.choice ? 'wrong' : 'dim'); });
  const sub = r.correct ? pick(WIN_SUB) : pick(LOSE_SUB);
  const extra = r.kind === 'bonus' ? 'Bonus: counts toward your accuracy, not your score' : r.correct ? `+${r.points}${r.streak >= 3 ? ` · 🔥 ${r.streak} in a row · ${r.multiplier}× points` : ''}` : (r.points === 0 && r.streak === 0 ? 'Streak reset' : '');
  $('#rev').innerHTML = `<div class="reveal">
    <div class="verdict ${r.correct ? 'good' : 'bad'}">${r.correct ? 'Correct!' : 'Not this time.'} <small>${esc(extra || '')}</small></div>
    <p class="muted">${esc(sub)}</p>
    <p class="answer-line">Answer: <b>${esc(r.answer_text)}</b></p>
    <p>${esc(r.explanation)}</p>
    <div class="tidbit"><span class="label">Bonus tidbit</span>${esc(r.tidbit)}</div>
    <div class="source"><span>Source: <a href="${esc(r.source.url)}" target="_blank" rel="noopener">${esc(r.source.title)} ↗</a></span><button class="linkbtn" id="flagBtn">Challenge this fact</button></div>
    <p class="note" id="flagMsg" hidden></p></div>
    <div class="actions" style="margin-top:6px"><button class="btn" id="nextBtn">${nextLabel()}</button></div>`;
  $('#flagBtn').onclick = async () => { const m = await B.flag(q.id); $('#flagMsg').textContent = m.message; $('#flagMsg').hidden = false; $('#flagBtn').disabled = true; };
  $('#nextBtn').onclick = () => { T.last = null; T.bonus = null; drawToday(); };
  $('#nextBtn').focus({ preventScroll: true });
  if (fresh) { r.correct ? celebrate(q.level) : commiserate(); }
}
function nextLabel() { const left = T.state.questions.filter(q => !q.answered).length; return T.bonus ? 'Done' : left ? `Next question (${left} left) →` : 'See my score →'; }
function summary() {
  const st = T.state, right = st.questions.filter(q => q.answered && q.answered.correct).length, n = st.questions.length;
  const perfect = right === n;
  const when = USER.send_days && USER.send_days.length ? `Drops arrive ${USER.send_days.length === 7 ? 'every day' : USER.send_days.join(', ')} at ${fmtTime(USER.send_time)}` : 'No days scheduled. Set some in Settings';
  return `<div class="panel summary"><div class="label">Today's drop</div>
    <div class="big mono">${right} / ${n}</div>
    <p><b class="mono">${st.score.toLocaleString()} points</b>${perfect ? ` · Perfect drop, +${CFG.perfect_drop_bonus} bonus` : ''}</p>
    <p class="muted">${perfect ? 'Every single one. Go tell somebody.' : right ? 'Solid. The tidbits are yours to keep.' : 'Rough one. Tomorrow is a rematch.'}</p>
    <div class="actions">${st.bonus_left > 0 ? `<button class="onemore" id="oneMore">Give me one more <span class="note">(${st.bonus_left} left today)</span></button>` : '<span class="note">That\'s all the bonus questions for today.</span>'}
    <button class="btn ghost" id="toScores">See my scores</button></div>
    <p class="note">${esc(when)}. Bonus questions count toward your accuracy, never your score or streak.</p></div>`;
}
function wireSummary() {
  const om = $('#oneMore'); if (om) om.onclick = async () => { try { T.bonus = await B.oneMore(); T.state.bonus_left = T.bonus.bonus_left; drawToday(); } catch (e) { showError(e); } };
  $('#toScores').onclick = () => go('scores');
}
const fmtTime = t => { const [h, m] = (t || '12:15').split(':'); return `${((+h + 11) % 12) + 1}:${m} ${+h < 12 ? 'AM' : 'PM'}`; };

/* ---------------- topics ---------------- */
let path = [];
async function renderTopics() {
  const reqs = B.requests();
  main().innerHTML = `<div class="stack">
    <div class="panel"><h2>Your topics</h2><div class="row" id="mine"></div></div>
    <div class="panel"><h2>Add a topic</h2><div class="search"><input id="tq" placeholder="Type anything, however niche" aria-label="Search topics" autocomplete="off" maxlength="80"></div><div class="matches" id="tm"></div></div>
    <div class="panel"><div class="label">Starter packs</div><div class="packs" id="tpacks"></div></div>
    <div class="panel"><div class="label">Browse</div><div class="crumbs" id="crumbs"></div><div class="nodes" id="nodes"></div></div>
    ${reqs.length ? `<div class="panel"><div class="label">Requested</div>${reqs.map(r => `<div class="match"><div class="nm">${esc(r)}<small>Researching. Opens once enough questions pass two-source checks.</small></div><span class="status">RESEARCHING</span></div>`).join('')}</div>` : ''}
  </div>`;
  drawMine(); drawBrowse();
  $('#tpacks').innerHTML = PACKS.map(p => `<button class="pack" data-p="${p.id}" aria-pressed="${p.topics.every(t => USER.topics.includes(t))}"><b>${esc(p.name)}</b><span>${esc(p.blurb)}</span></button>`).join('');
  $('#tpacks').querySelectorAll('[data-p]').forEach(b => b.onclick = async () => { const p = PACKS.find(x => x.id === b.dataset.p); await saveTopics([...new Set([...USER.topics, ...p.topics])]); renderTopics(); });
  const q = $('#tq'); let t;
  q.oninput = () => { clearTimeout(t); t = setTimeout(() => searchInto($('#tm'), q.value, async id => { await toggleTopic(id); q.value = ''; $('#tm').innerHTML = ''; }), 150); };
}
async function saveTopics(list) { if (!list.length) return; const r = await B.setTopics(list); USER.topics = r.topics; }
async function toggleTopic(id) { await saveTopics(USER.topics.includes(id) ? USER.topics.filter(t => t !== id) : [...USER.topics, id]); drawMine(); drawBrowse(); }
function drawMine() {
  $('#mine').innerHTML = USER.topics.map(t => `<span class="chip">${esc(NODES[t].name)} <span class="depth" data-d="${NODES[t].depth}">${depthName(NODES[t].depth)}</span>${USER.topics.length > 1 ? `<button class="x" data-rm="${t}" aria-label="Remove ${esc(NODES[t].name)}">×</button>` : ''}</span>`).join('');
  $('#mine').querySelectorAll('[data-rm]').forEach(b => b.onclick = () => toggleTopic(b.dataset.rm));
}
function drawBrowse() {
  const here = path.length ? NODES[path[path.length - 1]].kids : TREE;
  $('#crumbs').innerHTML = `<button data-p="-1">All topics</button>` + path.map((id, i) => `<span>›</span><button data-p="${i}">${esc(NODES[id].name)}</button>`).join('');
  $('#crumbs').querySelectorAll('button').forEach(b => b.onclick = () => { path = path.slice(0, +b.dataset.p + 1); drawBrowse(); });
  $('#nodes').innerHTML = here.map(n => { const on = USER.topics.includes(n.id); return `<div class="node"><div class="nm" style="${n.soon ? 'color:var(--muted)' : ''}">${esc(n.name)}<small>${n.soon ? 'Coming soon' : plural(n.questions, 'question')}</small></div>
    <span class="depth" data-d="${n.depth}">${depthName(n.depth)}</span>
    <button class="sm ${on ? 'on' : ''}" data-add="${n.id}" ${n.soon ? 'disabled' : ''}>${on ? '✓ Added' : '+ Add'}</button>
    ${n.kids.length ? `<button class="sm" data-go="${n.id}">Go deeper ›</button>` : ''}</div>`; }).join('');
  $('#nodes').querySelectorAll('[data-add]').forEach(b => b.onclick = () => toggleTopic(b.dataset.add));
  $('#nodes').querySelectorAll('[data-go]').forEach(b => b.onclick = () => { path.push(b.dataset.go); drawBrowse(); });
}

/* ---------------- scores ---------------- */
const rank = p => p >= 15000 ? 'Hall of Famer' : p >= 6000 ? 'All-Star' : p >= 2000 ? 'Starter' : 'Rookie';
async function renderScores() {
  const s = await B.stats();
  const answered = Object.values(s.levels).reduce((a, v) => a + v.answered, 0);
  main().innerHTML = `<div class="stack">
    <div class="overall"><div><span>Points</span><b class="mono">${s.total_points.toLocaleString()}</b></div><div><span>Rank</span><b>${rank(s.total_points)}</b></div><div><span>Day streak</span><b class="mono">${s.day_streak}</b></div><div><span>Best run</span><b class="mono">${s.best_answer_streak}</b></div></div>
    <div class="tiles">${[1, 2, 3, 4].map(l => { const v = s.levels[l], pct = v.answered ? Math.round(v.correct / v.answered * 100) : 0;
      return `<div class="tile lvl" data-l="${l}"><h3>${esc(levelName(l))}</h3><div class="big mono">${v.correct}<span class="sub"> / ${v.answered} right</span></div><div class="bar"><i style="width:${pct}%"></i></div><div class="sub">${v.answered ? pct + '% accuracy' : 'No answers yet at this level'} · ${CFG.level_points[l]} pts each</div></div>`; }).join('')}</div>
    <p class="note">${answered} answers so far, bonus questions included. Today: ${s.today.toLocaleString()} points.</p></div>`;
}

/* ---------------- settings ---------------- */
function settingsForm(el, s, onChange, onboarding) {
  const draw = () => {
    const theme = s.level_theme || CFG.default_level_theme;
    el.innerHTML = `<div class="stack">
      <div class="field"><div class="label">Questions per drop</div><div class="row">${CFG.drop_sizes.map(n => `<button class="chip" data-n="${n}" aria-pressed="${s.drop_size === n}">${n}</button>`).join('')}</div><span class="note">${{ 3: 'About a minute. Recommended.', 4: 'About two minutes, one of each level.', 5: 'A coffee break.' }[s.drop_size]}</span></div>
      <div class="field"><div class="label">Send it by</div><div class="row">${[['push', 'App notification'], ['sms', 'Text message'], ['email', 'Email']].map(([k, n]) => `<button class="chip" data-c="${k}" aria-pressed="${s.channel === k}">${n}</button>`).join('')}</div></div>
      ${s.channel === 'sms' ? `<div class="field"><label class="label" for="sPhone">Mobile number</label><input id="sPhone" type="tel" placeholder="+1 304 555 1234" value="${esc(s.phone || '')}"><label class="note"><input type="checkbox" id="sOpt" ${s.sms_opt_in ? 'checked' : ''}> Text me my trivia drops. Up to 7 texts a week. Msg &amp; data rates may apply. Reply STOP to cancel.</label></div>` : ''}
      ${s.channel === 'email' ? `<div class="field"><label class="label" for="sEmail">Email</label><input id="sEmail" type="email" value="${esc(s.email || '')}"></div>` : ''}
      <div class="field"><div class="label">Days</div><div class="row">${DAYS.map(d => `<button class="chip" data-d="${d}" aria-pressed="${s.send_days.includes(d)}">${d}</button>`).join('')}</div></div>
      <div class="field"><label class="label" for="sTime">Time</label><input type="time" id="sTime" value="${esc(s.send_time)}"></div>
      <div class="field"><label class="label" for="sMix">Difficulty mix</label><select id="sMix"><option value="ramp">Ramp up: easy first, hardest last</option><option value="mix">Random</option><option value="deep">Hardest only</option></select></div>
      <div class="field"><div class="label">Level names</div><div class="themes">${Object.entries(CFG.level_themes).map(([k, names]) => `<button class="theme" data-t="${k}" aria-pressed="${theme === k}">${names.map((n, i) => `<span class="badge lvl" data-l="${i + 1}">${esc(n)}</span>`).join('')}</button>`).join('')}</div></div>
      ${!onboarding ? `<div class="field"><div class="label">Sound</div><div class="row"><button class="chip" id="sSound" aria-pressed="${sound}">${sound ? 'On' : 'Off'}</button></div></div>` : ''}
      <div class="phone"><span class="note">${s.channel === 'sms' ? 'Text preview' : s.channel === 'email' ? 'Email preview' : 'Notification preview'}</span><div class="bubble">${esc(CFG.brand)}: ${s.drop_size} new questions on ${esc(previewTopics())}. ${s.channel === 'push' ? 'Tap to play.' : 'yourapp.com/d/8F2K'}${s.channel === 'sms' ? ' Reply STOP to opt out.' : ''}</div></div>
      ${!B.live ? '<p class="note">Demo: nothing is sent from this page.</p>' : ''}</div>`;
    $('#sMix').value = s.mix;
    const set = p => { Object.assign(s, p); onChange(p); draw(); };
    el.querySelectorAll('[data-n]').forEach(b => b.onclick = () => set({ drop_size: +b.dataset.n }));
    el.querySelectorAll('[data-c]').forEach(b => b.onclick = () => set({ channel: b.dataset.c }));
    el.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { const d = b.dataset.d; set({ send_days: s.send_days.includes(d) ? s.send_days.filter(x => x !== d) : DAYS.filter(x => s.send_days.includes(x) || x === d) }); });
    el.querySelectorAll('[data-t]').forEach(b => b.onclick = () => set({ level_theme: b.dataset.t }));
    $('#sTime').onchange = e => set({ send_time: e.target.value });
    $('#sMix').onchange = e => set({ mix: e.target.value });
    const ph = $('#sPhone'); if (ph) ph.onchange = e => { const v = e.target.value.replace(/[^\d+]/g, ''); set({ phone: v.startsWith('+') ? v : '+1' + v }); };
    const op = $('#sOpt'); if (op) op.onchange = e => set({ sms_opt_in: e.target.checked });
    const em = $('#sEmail'); if (em) em.onchange = e => set({ email: e.target.value.trim() });
    const so = $('#sSound'); if (so) so.onclick = () => { sound = !sound; store.set('sound', sound); draw(); };
  };
  draw();
}
const previewTopics = () => ((OB ? OB.topics : USER.topics) || []).slice(0, 2).map(t => NODES[t] && NODES[t].name).filter(Boolean).join(' + ') || 'your topics';
function renderSettings() {
  main().innerHTML = `<div class="panel"><h2>Settings</h2><div id="sf"></div><p class="note" id="saved" aria-live="polite"></p>
    <div class="actions"><button class="linkbtn" id="startOver">Start over with new topics</button></div></div>`;
  const s = { ...USER };
  settingsForm($('#sf'), s, async p => { try { USER = { ...USER, ...(await B.saveSettings(p)) }; $('#saved').textContent = 'Saved'; } catch (e) { $('#saved').textContent = e.message; } }, false);
  $('#startOver').onclick = () => { B.reset(); USER = null; startOnboarding(); };
}

/* ---------------- effects ---------------- */
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const cv = $('#fx'), cx = cv.getContext('2d'); let parts = [], raf = 0;
const size = () => { cv.width = innerWidth * devicePixelRatio; cv.height = innerHeight * devicePixelRatio; }; size(); addEventListener('resize', size);
function burst(colors, n, mode) {
  const w = cv.width, h = cv.height, d = devicePixelRatio;
  for (let k = 0; k < n; k++) {
    if (mode === 'win') { const L = k % 2 === 0; parts.push({ x: L ? 0 : w, y: h * .75, vx: (L ? 1 : -1) * (6 + Math.random() * 12) * d, vy: -(10 + Math.random() * 14) * d, g: .35 * d, r: (4 + Math.random() * 6) * d, c: colors[k % colors.length], rot: Math.random() * 6, vr: (Math.random() - .5) * .4, life: 140 }); }
    else parts.push({ x: Math.random() * w, y: -20 * d, vx: (Math.random() - .5) * d, vy: (1 + Math.random() * 2) * d, g: .06 * d, r: (3 + Math.random() * 4) * d, c: colors[k % colors.length], rot: 0, vr: 0, life: 150 });
  }
  if (!raf) tick();
}
function tick() {
  cx.clearRect(0, 0, cv.width, cv.height);
  parts = parts.filter(p => p.life-- > 0 && p.y < cv.height + 40);
  for (const p of parts) { p.vy += p.g; p.x += p.vx; p.y += p.vy; p.vx *= .99; p.rot += p.vr; cx.save(); cx.globalAlpha = Math.min(1, p.life / 40); cx.translate(p.x, p.y); cx.rotate(p.rot); cx.fillStyle = p.c; cx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); cx.restore(); }
  raf = parts.length ? requestAnimationFrame(tick) : 0;
}
function replay(el, cls) { el.className = el.className.split(' ').filter(c => !cls.split(' ').includes(c)).join(' '); void el.offsetWidth; cls.split(' ').forEach(c => el.classList.add(c)); }
function shout(text, cls, color) {
  const sh = $('#shout'); sh.textContent = text; sh.style.setProperty('--c', color || '');
  sh.style.fontSize = `clamp(26px, ${Math.min(9, 110 / text.length).toFixed(1)}vw, 80px)`;
  sh.className = 'shout'; void sh.offsetWidth; sh.classList.add(cls);
}
function celebrate(l) {
  const card = $('#card'), c = getComputedStyle(card).getPropertyValue('--c').trim();
  ['#show', '#flash'].forEach(s => $(s).style.setProperty('--c', c));
  shout(pick(WIN), 'win', c); replay($('#flash'), 'flash go');
  card.classList.add('glow'); setTimeout(() => card.classList.remove('glow'), 1400);
  if (!reduce) { replay($('#show'), 'show win'); burst([c, '#ffffff', '#19c2d6', c, '#ffd23f'], l * 40 + 60, 'win'); }
  beep(true, l);
}
function commiserate() {
  const card = $('#card');
  shout(pick(LOSE), 'lose'); replay($('#vignette'), 'vignette go');
  card.classList.add('gray'); setTimeout(() => card.classList.remove('gray'), 1200);
  if (!reduce) { replay($('.app'), 'shake'); burst(['#6b6680', '#4a4558', '#8a8599'], 70, 'lose'); }
  beep(false);
}
let ac = null;
function beep(win, l) {
  if (!sound) return;
  try {
    ac = ac || new (window.AudioContext || window.webkitAudioContext)(); const t = ac.currentTime;
    const note = (f, s, d, type, vol, f2) => { const o = ac.createOscillator(), g = ac.createGain(); o.type = type; o.frequency.setValueAtTime(f, t + s); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + s + d); g.gain.setValueAtTime(0, t + s); g.gain.linearRampToValueAtTime(vol, t + s + .01); g.gain.exponentialRampToValueAtTime(.0001, t + s + d); o.connect(g).connect(ac.destination); o.start(t + s); o.stop(t + s + d + .05); };
    if (win) { const seq = [523, 659, 784, 1047, 1319, 1568].slice(0, 3 + l); seq.forEach((f, i) => note(f, i * .08, .35, 'triangle', .18)); note(seq[seq.length - 1] * 2, seq.length * .08, .6, 'sine', .08); }
    else { note(220, 0, .45, 'sawtooth', .12, 90); note(70, .05, .4, 'square', .1, 40); }
  } catch {}
}

/* ---------------- boot ---------------- */
async function boot() {
  try {
    CFG = await B.config();
    const t = await B.topics(); TREE = t.tree; PACKS = t.packs;
    const index = ns => ns.forEach(n => { NODES[n.id] = n; index(n.kids); }); index(TREE);
    $('#brandName').textContent = CFG.brand; document.title = CFG.brand;
    USER = await B.me();
    if (USER && USER.topics && USER.topics.length) go('today'); else startOnboarding();
  } catch (e) { main().innerHTML = ''; showError(e); }
}
boot();
})();
