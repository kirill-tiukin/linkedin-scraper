/* ── state ─────────────────────────────────────────────────────────────── */
let currentJobId = null;
let rowCount = 0;
const rowIndex = {};       // profile_url → <tr> element
let savedResults = [];     // full result objects (persisted to localStorage)

const STORAGE_KEY = 'li_scrape_session';

/* ── elements ──────────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);
const runBtn       = $('run-btn');
const stopBtn      = $('stop-btn');
const newSearchBtn = $('new-search-btn');
const statusBar    = $('status-bar');
const statusText   = $('status-text');
const downloadBtn  = $('download-btn');
const emptyState   = $('empty-state');
const tableWrap    = $('table-wrap');
const tbody        = $('results-body');
const errorLog     = $('error-log');
const resultsCount = $('results-count');
const companyTrack = $('company-track');

function hasFinalScout() {
  return !!$('finalscout-key').value.trim();
}

/* ── persistence ────────────────────────────────────────────────────────── */
function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ jobId: currentJobId, results: savedResults }));
  } catch (_) {}
}

function clearPersisted() {
  try { localStorage.removeItem(STORAGE_KEY); } catch (_) {}
  savedResults = [];
}

function restoreFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const { jobId, results } = JSON.parse(raw);
    if (!results || !results.length) return;
    currentJobId = jobId;
    results.forEach(r => appendRow(r));
    downloadBtn.classList.remove('hidden');
    newSearchBtn.classList.remove('hidden');
  } catch (_) {}
}

/* ── LinkedIn session ──────────────────────────────────────────────────── */
async function checkSession() {
  try {
    const r = await fetch('/api/session-status');
    const { connected } = await r.json();
    setSessionStatus(connected);
  } catch (_) {
    setSessionStatus(false);
  }
}

function setSessionStatus(connected) {
  const dot   = $('auth-dot');
  const label = $('auth-label');
  const btn   = $('connect-btn');
  if (connected) {
    dot.className     = 'auth-dot ok';
    label.textContent = 'Session active';
    btn.textContent   = 'Reconnect';
  } else {
    dot.className     = 'auth-dot bad';
    label.textContent = 'Not connected';
    btn.textContent   = 'Connect';
  }
}

function connectLinkedIn() {
  const statusEl = $('connect-status');
  const btn      = $('connect-btn');
  statusEl.classList.remove('hidden');
  statusEl.textContent = 'Opening browser…';
  btn.disabled = true;

  const es = new EventSource('/api/connect-linkedin');

  es.addEventListener('status', e => {
    statusEl.textContent = JSON.parse(e.data).msg;
  });

  es.addEventListener('done', e => {
    statusEl.textContent = '✓ ' + JSON.parse(e.data).msg;
    es.close();
    btn.disabled = false;
    checkSession();
    setTimeout(() => statusEl.classList.add('hidden'), 6000);
  });

  es.addEventListener('error', e => {
    const d = JSON.parse(e.data);
    statusEl.textContent = '✗ ' + (d.msg || 'Failed');
    es.close();
    btn.disabled = false;
  });

  es.onerror = () => {
    es.close();
    btn.disabled = false;
    statusEl.textContent = 'Connection lost — please try again';
  };
}

checkSession();

/* ── run ────────────────────────────────────────────────────────────────── */
runBtn.addEventListener('click', startJob);

async function startJob() {
  const positions = $('search-position').value.trim();
  const companies = $('search-company').value.trim();

  if (!positions) { shake($('search-position')); return; }

  const body = {
    positions,
    companies,
    location_filter: $('search-location').value.trim(),
    n: parseInt($('search-n').value) || 50,
    finalscout_key: $('finalscout-key').value.trim(),
  };

  resetResults();

  // Seed company status pills
  const companyList = companies.split('\n').map(s => s.trim()).filter(Boolean);
  if (companyList.length) {
    companyTrack.innerHTML = '';
    companyList.forEach(c => {
      const pill = document.createElement('div');
      pill.className = 'company-pill queued';
      pill.dataset.company = c;
      pill.textContent = c;
      companyTrack.appendChild(pill);
    });
    companyTrack.classList.remove('hidden');
  }

  setRunning(true);

  let res;
  try {
    res = await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (e) {
    setRunning(false);
    showError(`Network error: ${e.message}`);
    return;
  }

  const json = await res.json();
  if (!res.ok) {
    setRunning(false);
    showError(json.error || 'Unknown error');
    return;
  }

  currentJobId = json.job_id;
  stopBtn.classList.remove('hidden');
  listenStream(currentJobId);
}

/* ── SSE stream ─────────────────────────────────────────────────────────── */
function listenStream(jobId) {
  const es = new EventSource(`/api/stream/${jobId}`);

  es.addEventListener('status', e => {
    statusText.textContent = JSON.parse(e.data).msg;
  });

  es.addEventListener('company_status', e => {
    const { company, status } = JSON.parse(e.data);
    const pill = companyTrack.querySelector(`[data-company="${CSS.escape(company)}"]`);
    if (pill) pill.className = `company-pill ${status}`;
  });

  es.addEventListener('result', e => {
    const r = JSON.parse(e.data);
    savedResults.push(r);
    persist();
    appendRow(r);
  });

  es.addEventListener('email_update', e => {
    const { profile_url, email } = JSON.parse(e.data);

    // Update in-memory store and persist
    const saved = savedResults.find(r => r.profile_url === profile_url);
    if (saved) { saved.email = email; persist(); }

    // Update DOM
    const tr = rowIndex[profile_url];
    if (tr) {
      const cell = tr.querySelector('.cell-email');
      if (cell) {
        cell.innerHTML = email
          ? `<a href="mailto:${esc(email)}" class="email-link">${esc(email)}</a>`
          : '<span class="muted">—</span>';
      }
    }
  });

  es.addEventListener('error_row', e => {
    const d = JSON.parse(e.data);
    appendErrorRow(d.slug || '', d.msg);
  });

  es.addEventListener('fatal', e => {
    showError(`Error: ${JSON.parse(e.data).msg}`);
    es.close();
    setRunning(false);
  });

  es.addEventListener('done', e => {
    const d = JSON.parse(e.data);
    es.close();
    setRunning(false);
    stopBtn.classList.add('hidden');
    statusText.textContent = `Done — ${d.count} contact${d.count !== 1 ? 's' : ''} found`;
    setTimeout(() => statusBar.classList.add('hidden'), 10_000);
    if (d.count > 0) {
      downloadBtn.classList.remove('hidden');
      newSearchBtn.classList.remove('hidden');
    }
    persist();
    updateCount();
  });

  es.onerror = () => { es.close(); setRunning(false); stopBtn.classList.add('hidden'); };
}

/* ── table helpers ──────────────────────────────────────────────────────── */
function appendRow(r) {
  rowCount++;
  emptyState.classList.add('hidden');
  tableWrap.classList.remove('hidden');

  const srcLabel = r.source === 'DDG' ? 'DDG' : 'LI';
  const srcClass = r.source === 'DDG' ? 'src-ddg' : 'src-li';
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td class="cell-num">${rowCount}</td>
    <td class="cell-name">
      <a href="${esc(r.profile_url)}" target="_blank" rel="noopener">${esc(r.name)}</a>
    </td>
    <td class="cell-headline">${esc(r.headline || '—')}</td>
    <td class="cell-company">${esc(r.current_company || '—')}</td>
    <td class="cell-location">${esc(r.location || '—')}</td>
    <td class="cell-email">
      ${r.email
        ? `<a href="mailto:${esc(r.email)}" class="email-link">${esc(r.email)}</a>`
        : '<span class="muted">—</span>'}
    </td>
    <td class="cell-src"><span class="src-badge ${srcClass}">${srcLabel}</span></td>
    <td class="cell-link">
      <a href="${esc(r.profile_url)}" target="_blank" rel="noopener" class="link-arrow">↗</a>
    </td>
  `;
  tbody.appendChild(tr);
  rowIndex[r.profile_url] = tr;
  updateCount();
  downloadBtn.classList.remove('hidden');
}

function updateCount() {
  resultsCount.textContent =
    rowCount === 0
      ? 'No profiles found yet'
      : `${rowCount} contact${rowCount !== 1 ? 's' : ''} found`;
}

function appendErrorRow(slug, msg) {
  errorLog.classList.remove('hidden');
  const p = document.createElement('p');
  p.textContent = slug ? `${slug}: ${msg}` : msg;
  errorLog.appendChild(p);
}

/* ── new search ─────────────────────────────────────────────────────────── */
newSearchBtn.addEventListener('click', () => {
  clearPersisted();
  resetResults();
  newSearchBtn.classList.add('hidden');
});

/* ── stop ───────────────────────────────────────────────────────────────── */
stopBtn.addEventListener('click', async () => {
  if (currentJobId) {
    await fetch(`/api/stop/${currentJobId}`, { method: 'POST' });
    stopBtn.classList.add('hidden');
    statusText.textContent = 'Stopping…';
  }
});

/* ── download ───────────────────────────────────────────────────────────── */
downloadBtn.addEventListener('click', () => {
  if (currentJobId) {
    window.open(`/api/download/${currentJobId}`, '_blank');
  } else if (savedResults.length) {
    // Fallback: client-side CSV from localStorage (server job may be gone after refresh)
    const fields = ['name', 'headline', 'location', 'current_company', 'profile_url', 'email', 'source'];
    const rows = [fields.join(',')];
    savedResults.forEach(r => {
      rows.push(fields.map(f => `"${String(r[f] ?? '').replace(/"/g, '""')}"`).join(','));
    });
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'linkedin-contacts.csv';
    a.click();
  }
});

/* ── ui helpers ─────────────────────────────────────────────────────────── */
function setRunning(on) {
  runBtn.disabled = on;
  statusBar.classList.toggle('hidden', !on);
}

function resetResults() {
  tbody.innerHTML = '';
  rowCount = 0;
  Object.keys(rowIndex).forEach(k => delete rowIndex[k]);
  errorLog.innerHTML = '';
  errorLog.classList.add('hidden');
  tableWrap.classList.add('hidden');
  emptyState.classList.remove('hidden');
  downloadBtn.classList.add('hidden');
  newSearchBtn.classList.add('hidden');
  companyTrack.classList.add('hidden');
  companyTrack.innerHTML = '';
  currentJobId = null;
  updateCount();
}

function showError(msg) {
  errorLog.classList.remove('hidden');
  const p = document.createElement('p');
  p.textContent = msg;
  errorLog.appendChild(p);
}

function shake(el) {
  el.style.animation = 'none';
  el.offsetHeight;
  el.style.animation = 'shake .35s ease';
  el.addEventListener('animationend', () => (el.style.animation = ''), { once: true });
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const style = document.createElement('style');
style.textContent = `
@keyframes shake {
  0%,100%{transform:translateX(0)}
  20%{transform:translateX(-5px)}
  60%{transform:translateX(5px)}
  80%{transform:translateX(-3px)}
}`;
document.head.appendChild(style);

/* ── restore on load ────────────────────────────────────────────────────── */
restoreFromStorage();
