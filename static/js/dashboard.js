/* ── State ───────────────────────────────────────────────────────── */
const state = {
  age: 34,
  yearsDiagnosed: 3,
  remoteness: 1,
};

/* ── Helpers ─────────────────────────────────────────────────────── */
function fmt(n) {
  return '$' + Math.round(n).toLocaleString('en-AU');
}

function fmtShort(n) {
  if (n >= 1000) return '$' + Math.round(n / 1000) + 'k';
  return '$' + Math.round(n);
}

/* ── API call ────────────────────────────────────────────────────── */
async function fetchPrediction() {
  const pill = document.getElementById('status-pill');
  pill.textContent = 'Calculating…';
  pill.classList.add('loading');

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        age: state.age,
        years_diagnosed: state.yearsDiagnosed,
        remoteness: state.remoteness,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      console.error('Prediction error:', err);
      pill.textContent = 'Error';
      return;
    }

    const data = await res.json();
    renderResults(data);

    pill.textContent = 'Updated';
    pill.classList.remove('loading');
    setTimeout(() => { pill.textContent = 'Ready'; }, 1200);

  } catch (e) {
    console.error('Network error:', e);
    pill.textContent = 'Error';
    pill.classList.remove('loading');
  }
}

/* ── Render results ──────────────────────────────────────────────── */
function renderResults(data) {
  // Budget range
  document.getElementById('low-out').textContent   = fmt(data.low);
  document.getElementById('high-out').textContent  = fmt(data.high);
  document.getElementById('point-out').textContent = fmt(data.point);

  // Metrics
  document.getElementById('width-out').textContent  = fmt(data.interval_width);
  document.getElementById('disp-out').textContent   = data.dispersion.toFixed(3);
  document.getElementById('conf-out').textContent   = data.confidence_pct;
  document.getElementById('remote-out').textContent = data.remoteness_label;

  // Confidence colour
  const confEl = document.getElementById('conf-out');
  confEl.className = 'metric-value ' + (
    data.confidence === 'High'     ? 'good' :
    data.confidence === 'Moderate' ? 'warn' : 'alert'
  );

  // Range bar
  const maxScale = Math.max(120000, data.high * 1.25);
  const pct = v => Math.min(100, (v / maxScale) * 100).toFixed(2);

  const fill   = document.getElementById('range-fill');
  const marker = document.getElementById('range-marker');
  const tip    = document.getElementById('range-tooltip');

  fill.style.left  = pct(data.low) + '%';
  fill.style.width = (pct(data.high) - pct(data.low)) + '%';
  marker.style.left = pct(data.point) + '%';
  tip.style.left    = pct(data.point) + '%';
  tip.textContent   = fmt(data.point);

  document.getElementById('axis-mid').textContent = fmtShort(maxScale / 2);
  document.getElementById('axis-max').textContent = fmtShort(maxScale);

  // Flag
  const flag = document.getElementById('flag-box');
  flag.className = 'flag-box ' + data.flag_level;
  flag.textContent = data.flag_text;

  // Variable contributions
  const contributions = data.contributions;
  const maxContrib = Math.max(...Object.values(contributions), 1);
  const list = document.getElementById('contrib-list');

  list.innerHTML = Object.entries(contributions).map(([name, val]) => `
    <div class="contrib-item">
      <span class="contrib-name">${name}</span>
      <div class="contrib-bar-wrap">
        <div class="contrib-bar" style="width: ${Math.round((val / maxContrib) * 100)}%"></div>
      </div>
      <span class="contrib-val">${fmt(val)}</span>
    </div>
  `).join('');
}

/* ── Slider: Age ─────────────────────────────────────────────────── */
const ageSlider = document.getElementById('age-slider');
const ageDisplay = document.getElementById('age-display');

ageSlider.addEventListener('input', function () {
  state.age = parseInt(this.value);
  ageDisplay.textContent = state.age + ' years';
  debouncedFetch();
});

/* ── Slider: Years diagnosed ─────────────────────────────────────── */
const diagSlider = document.getElementById('diag-slider');
const diagDisplay = document.getElementById('diag-display');

diagSlider.addEventListener('input', function () {
  state.yearsDiagnosed = parseInt(this.value);
  diagDisplay.textContent = state.yearsDiagnosed === 0
    ? 'Recently diagnosed'
    : state.yearsDiagnosed + (state.yearsDiagnosed === 1 ? ' year' : ' years');
  debouncedFetch();
});

/* ── Remoteness buttons ──────────────────────────────────────────── */
function setRemote(btn) {
  document.querySelectorAll('.rem-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.remoteness = parseInt(btn.dataset.val);
  document.getElementById('rem-display').textContent = btn.textContent.trim();
  fetchPrediction();
}

/* ── Debounce for sliders ────────────────────────────────────────── */
let debounceTimer = null;
function debouncedFetch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchPrediction, 180);
}

/* ── Init ────────────────────────────────────────────────────────── */
fetchPrediction();
