// Sidebar
const sidebar = document.getElementById('sidebar');
const toggle = document.getElementById('sidebarToggle');
const composerWrap = document.getElementById('composerWrap');
toggle.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
  composerWrap.classList.toggle('full', sidebar.classList.contains('collapsed'));
});
document.getElementById('newTaskBtn').addEventListener('click', () => {
  document.getElementById('chat').innerHTML = '';
  document.getElementById('hero').classList.remove('hidden');
  document.getElementById('promptInput').value = '';
  composerWrap.classList.remove('docked');
});

// Cursor-following mesh
const bgSpot = document.getElementById('bgSpot');
window.addEventListener('mousemove', e => {
  bgSpot.style.setProperty('--mx', e.clientX + 'px');
  bgSpot.style.setProperty('--my', e.clientY + 'px');
});

// Halo around the hero logo
function positionHalo() {
  const logo = document.querySelector('.hero-logo');
  const halo = document.getElementById('bgHalo');
  if (!logo || !halo) return;
  const r = logo.getBoundingClientRect();
  halo.style.setProperty('--lx', (r.left + r.width / 2) + 'px');
  halo.style.setProperty('--ly', (r.top + r.height / 2) + 'px');
}
window.addEventListener('load', positionHalo);
window.addEventListener('resize', positionHalo);
toggle.addEventListener('click', () => setTimeout(positionHalo, 300));
document.getElementById('newTaskBtn').addEventListener('click', () => setTimeout(positionHalo, 50));

// Models
async function loadModels() {
  const res = await fetch('/api/models');
  const data = await res.json();
  const sel = document.getElementById('modelSelect');
  sel.innerHTML = data.models.map(m => `<option value="${m}">${m}</option>`).join('');
  sel.value = data.default;
}
loadModels();

// Files
async function refreshFiles() {
  const res = await fetch('/api/files');
  const data = await res.json();
  document.getElementById('inputList').innerHTML = data.inputs.map(f => `<li title="${f}">${f}</li>`).join('') || '<li>—</li>';
  document.getElementById('outputList').innerHTML = data.outputs.map(f => `<li title="${f}">${f}</li>`).join('') || '<li>—</li>';
}
refreshFiles();

// Toasts
function toast(msg, isError = false) {
  const el = document.createElement('div');
  el.className = 'toast' + (isError ? ' error' : '');
  el.textContent = msg;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// Upload with chips
const chips = document.getElementById('chips');
const uploaded = [];
const attachBtn = document.getElementById('attachBtn');
const fileInput = document.getElementById('fileInput');
attachBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => [...e.target.files].forEach(uploadFile));

async function uploadFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/api/upload', { method: 'POST', body: fd });
  const data = await res.json();
  uploaded.push(data.saved);
  renderChips();
  toast(`Uploaded ${file.name}`);
  refreshFiles();
}
function renderChips() {
  chips.innerHTML = uploaded.map((f, i) =>
    `<span class="chip">${f.split('/').pop()}<button data-i="${i}">×</button></span>`).join('');
  chips.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    uploaded.splice(+b.dataset.i, 1); renderChips();
  }));
}

// Chat helpers
const chat = document.getElementById('chat');
function userMsg(text) {
  const el = document.createElement('div');
  el.className = 'msg user';
  el.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  chat.appendChild(el);
}
function agentTurn() {
  const el = document.createElement('div');
  el.className = 'msg agent';
  el.innerHTML = `<div class="agent-head"><span class="agent-avatar"><svg viewBox="0 0 32 32" width="22" height="22"><rect x="1" y="1" width="30" height="30" rx="6" fill="#2e8b62"/><path d="M8 23h16M8 16h16M8 9h16" stroke="#14181c" stroke-width="2.4" stroke-linecap="round"/></svg></span><span class="agent-name">SHEETPT</span></div><div class="events"></div>`;
  chat.appendChild(el);
  return el.querySelector('.events');
}
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function addEventCard(container, title, body, cls = '') {
  const card = document.createElement('div');
  card.className = 'event-card ' + cls;
  card.innerHTML = `<h4>${escapeHtml(title)}</h4>` + (body ? `<pre><code>${escapeHtml(body)}</code></pre>` : '');
  container.appendChild(card);
  card.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// Run
const runBtn = document.getElementById('runBtn');
const promptInput = document.getElementById('promptInput');
promptInput.addEventListener('input', () => {
  promptInput.style.height = 'auto';
  promptInput.style.height = promptInput.scrollHeight + 'px';
});
promptInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runBtn.click(); }
});

runBtn.addEventListener('click', async () => {
  const prompt = promptInput.value.trim();
  if (!prompt) { toast('Type a task first.', true); return; }

  document.getElementById('hero').classList.add('hidden');
  composerWrap.classList.add('docked');
  userMsg(prompt);
  const events = agentTurn();
  promptInput.value = ''; promptInput.style.height = 'auto';
  runBtn.disabled = true;

  const history = document.getElementById('historyList');
  if (history.querySelector('.muted')) history.innerHTML = '';
  history.insertAdjacentHTML('afterbegin', `<li>${escapeHtml(prompt.slice(0, 40))}</li>`);

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        model: document.getElementById('modelSelect').value,
        max_retries: 3,
      }),
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop();
      for (const part of parts) {
        const line = part.replace(/^data: /, '');
        if (line.trim()) handleEvent(JSON.parse(line), events);
      }
    }
  } catch (err) {
    toast('Request failed: ' + err.message, true);
  } finally {
    runBtn.disabled = false;
    refreshFiles();
  }
});

let pendingCard = null;

function handleEvent(ev, container) {
  switch (ev.type) {
    case 'attempt_start':
      pendingCard = addPendingCard(container, `Attempt ${ev.attempt} / ${ev.max_retries} — generating code…`);
      break;
    case 'code_generated':
      if (pendingCard) { pendingCard.remove(); pendingCard = null; }
      addEventCard(container, 'Code generated', ev.code);
      break;
    case 'execution_failed':
      if (pendingCard) { pendingCard.remove(); pendingCard = null; }
      addEventCard(container, `Execution error — retrying with context`, ev.output, 'warn');
      break;
    case 'execution_success':
      if (pendingCard) { pendingCard.remove(); pendingCard = null; }
      addEventCard(container, `Completed on attempt ${ev.attempt}`, ev.output, 'success');
      toast('Task completed');
      break;
    case 'generation_error':
      if (pendingCard) { pendingCard.remove(); pendingCard = null; }
      addEventCard(container, 'Code generation error', ev.error, 'error');
      break;
    case 'mcp_error':
      if (pendingCard) { pendingCard.remove(); pendingCard = null; }
      addEventCard(container, 'MCP communication error', ev.error, 'error');
      break;
    case 'all_retries_exhausted':
      addEventCard(container, `Failed after ${ev.max_retries} attempts`, '', 'error');
      break;
  }
}

function addPendingCard(container, title) {
  const card = document.createElement('div');
  card.className = 'event-card pending';
  card.innerHTML = `<h4>${escapeHtml(title)}</h4><div class="shimmer"></div>`;
  container.appendChild(card);
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  return card;
}
