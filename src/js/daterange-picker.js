/**
 * DateRangePicker — Reusable date range selector with presets
 * Inspired by Stitch design mockups. Dark theme, consistent across all dashboards.
 *
 * Usage:
 *   const picker = new DateRangePicker({
 *     containerId: 'date-picker',   // where to mount
 *     dateMin: '2023-07-01',        // earliest date in data
 *     dateMax: '2026-03-08',        // latest date in data
 *     onChange: (start, end) => {}   // callback when range changes
 *   });
 */
class DateRangePicker {
  constructor(opts) {
    this.containerId = opts.containerId;
    this.dateMin = opts.dateMin;
    this.dateMax = opts.dateMax;
    this.onChange = opts.onChange || function(){};
    this.start = opts.initialStart || opts.dateMin;
    this.end = opts.initialEnd || opts.dateMax;
    this.open = false;

    // Calendar state
    const endD = new Date(this.end + 'T00:00:00');
    this.calYear = endD.getFullYear();
    this.calMonth = endD.getMonth();

    this._injectStyles();
    this._render();
    this._bindOutsideClick();
  }

  /* ── Presets ─────────────────────────────────── */
  _getPresets() {
    const max = new Date(this.dateMax + 'T00:00:00');
    const min = new Date(this.dateMin + 'T00:00:00');
    const fmt = d => d.toISOString().substring(0, 10);

    const sub = (months) => {
      const d = new Date(max);
      d.setMonth(d.getMonth() - months);
      if (d < min) return fmt(min);
      return fmt(d);
    };

    // YTD: Jan 1 of max's year
    const ytdStart = new Date(max.getFullYear(), 0, 1);

    return [
      { label: 'Último mes',       start: sub(1),                    end: fmt(max) },
      { label: 'Últimos 3 meses',  start: sub(3),                    end: fmt(max) },
      { label: 'Últimos 6 meses',  start: sub(6),                    end: fmt(max) },
      { label: 'Último año',       start: sub(12),                   end: fmt(max) },
      { label: 'YTD',              start: fmt(ytdStart < min ? min : ytdStart), end: fmt(max) },
      { label: 'Todo el período',  start: fmt(min),                  end: fmt(max) },
    ];
  }

  /* ── Format display ──────────────────────────── */
  _fmtDisplay(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    return months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
  }

  _fmtShort(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    return months[d.getMonth()] + ' ' + d.getFullYear();
  }

  /* ── Calendar helpers ────────────────────────── */
  _daysInMonth(y, m) { return new Date(y, m + 1, 0).getDate(); }
  _firstDow(y, m) { return new Date(y, m, 1).getDay(); } // 0=Sun

  _buildCalendar() {
    const y = this.calYear, m = this.calMonth;
    const days = this._daysInMonth(y, m);
    const first = this._firstDow(y, m);
    const months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

    const startD = new Date(this.start + 'T00:00:00');
    const endD = new Date(this.end + 'T00:00:00');
    const minD = new Date(this.dateMin + 'T00:00:00');
    const maxD = new Date(this.dateMax + 'T00:00:00');

    let html = '<div class="drp-cal-header">';
    html += '<button class="drp-cal-nav" data-dir="-1">‹</button>';
    html += '<span class="drp-cal-title">' + months[m] + ' ' + y + '</span>';
    html += '<button class="drp-cal-nav" data-dir="1">›</button>';
    html += '</div>';
    html += '<div class="drp-cal-grid">';
    html += ['Do','Lu','Ma','Mi','Ju','Vi','Sá'].map(d => '<span class="drp-cal-dow">' + d + '</span>').join('');

    // Empty cells before first day
    for (let i = 0; i < first; i++) html += '<span class="drp-cal-empty"></span>';

    for (let d = 1; d <= days; d++) {
      const dt = new Date(y, m, d);
      const iso = dt.toISOString().substring(0, 10);
      const inRange = dt >= startD && dt <= endD;
      const isStart = iso === this.start;
      const isEnd = iso === this.end;
      const disabled = dt < minD || dt > maxD;
      let cls = 'drp-cal-day';
      if (inRange) cls += ' drp-in-range';
      if (isStart) cls += ' drp-range-start';
      if (isEnd) cls += ' drp-range-end';
      if (disabled) cls += ' drp-disabled';
      html += '<span class="' + cls + '" data-date="' + iso + '">' + d + '</span>';
    }
    html += '</div>';
    return html;
  }

  /* ── Active preset detection ─────────────────── */
  _activePreset() {
    const presets = this._getPresets();
    for (let i = 0; i < presets.length; i++) {
      if (presets[i].start === this.start && presets[i].end === this.end) return i;
    }
    return -1;
  }

  /* ── Render ──────────────────────────────────── */
  _render() {
    const el = document.getElementById(this.containerId);
    if (!el) return;

    const activeIdx = this._activePreset();
    const presets = this._getPresets();

    let html = '<div class="drp-wrapper">';

    // Trigger button
    html += '<button class="drp-trigger" id="' + this.containerId + '-trigger">';
    html += '<svg class="drp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>';
    html += '<span class="drp-label">' + this._fmtShort(this.start) + ' — ' + this._fmtShort(this.end) + '</span>';
    html += '<svg class="drp-chevron' + (this.open ? ' drp-chevron-up' : '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>';
    html += '</button>';

    // Popover
    if (this.open) {
      html += '<div class="drp-popover">';

      // Left: Presets
      html += '<div class="drp-presets">';
      html += '<div class="drp-presets-title">Presets</div>';
      presets.forEach((p, i) => {
        html += '<button class="drp-preset' + (i === activeIdx ? ' drp-preset-active' : '') + '" data-pidx="' + i + '">' + p.label + '</button>';
      });
      html += '</div>';

      // Right: Calendar + inputs
      html += '<div class="drp-calendar-panel">';

      // Date inputs row
      html += '<div class="drp-inputs-row">';
      html += '<div class="drp-input-group"><label>Desde</label><input type="date" class="drp-date-input" id="' + this.containerId + '-ds" value="' + this.start + '" min="' + this.dateMin + '" max="' + this.dateMax + '"></div>';
      html += '<span class="drp-input-sep">→</span>';
      html += '<div class="drp-input-group"><label>Hasta</label><input type="date" class="drp-date-input" id="' + this.containerId + '-de" value="' + this.end + '" min="' + this.dateMin + '" max="' + this.dateMax + '"></div>';
      html += '</div>';

      // Calendar
      html += this._buildCalendar();

      // Apply button
      html += '<div class="drp-actions">';
      html += '<button class="drp-btn-apply">Aplicar</button>';
      html += '</div>';

      html += '</div>'; // calendar-panel
      html += '</div>'; // popover
    }

    html += '</div>'; // wrapper
    el.innerHTML = html;
    this._bindEvents();
  }

  /* ── Events ──────────────────────────────────── */
  _bindEvents() {
    const self = this;
    const el = document.getElementById(this.containerId);
    if (!el) return;

    // Toggle popover
    const trigger = el.querySelector('.drp-trigger');
    if (trigger) trigger.addEventListener('click', function(e) {
      e.stopPropagation();
      self.open = !self.open;
      self._render();
    });

    // Presets
    el.querySelectorAll('.drp-preset').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const idx = parseInt(this.getAttribute('data-pidx'));
        const p = self._getPresets()[idx];
        self.start = p.start;
        self.end = p.end;
        const endD = new Date(self.end + 'T00:00:00');
        self.calYear = endD.getFullYear();
        self.calMonth = endD.getMonth();
        self._render();
        // Auto-apply on preset click
        self.open = false;
        self._render();
        self.onChange(self.start, self.end);
      });
    });

    // Calendar navigation
    el.querySelectorAll('.drp-cal-nav').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const dir = parseInt(this.getAttribute('data-dir'));
        self.calMonth += dir;
        if (self.calMonth > 11) { self.calMonth = 0; self.calYear++; }
        if (self.calMonth < 0) { self.calMonth = 11; self.calYear--; }
        self._render();
      });
    });

    // Calendar day clicks
    el.querySelectorAll('.drp-cal-day:not(.drp-disabled)').forEach(function(day) {
      day.addEventListener('click', function(e) {
        e.stopPropagation();
        const date = this.getAttribute('data-date');
        // Smart selection: if no start or date < start, set start; else set end
        if (!self._selectingEnd || date < self.start) {
          self.start = date;
          self.end = date;
          self._selectingEnd = true;
        } else {
          self.end = date;
          self._selectingEnd = false;
        }
        self._render();
      });
    });

    // Date inputs
    const dsInput = document.getElementById(self.containerId + '-ds');
    const deInput = document.getElementById(self.containerId + '-de');
    if (dsInput) dsInput.addEventListener('change', function(e) {
      e.stopPropagation();
      if (this.value >= self.dateMin && this.value <= self.dateMax) {
        self.start = this.value;
        if (self.start > self.end) self.end = self.start;
        self._render();
      }
    });
    if (deInput) deInput.addEventListener('change', function(e) {
      e.stopPropagation();
      if (this.value >= self.dateMin && this.value <= self.dateMax) {
        self.end = this.value;
        if (self.end < self.start) self.start = self.end;
        self._render();
      }
    });

    // Apply button
    const applyBtn = el.querySelector('.drp-btn-apply');
    if (applyBtn) applyBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      self.open = false;
      self._render();
      self.onChange(self.start, self.end);
    });
  }

  _bindOutsideClick() {
    const self = this;
    document.addEventListener('click', function(e) {
      if (self.open) {
        const el = document.getElementById(self.containerId);
        if (el && !el.contains(e.target)) {
          self.open = false;
          self._render();
        }
      }
    });
  }

  /* ── Public API ──────────────────────────────── */
  setRange(start, end) {
    this.start = start;
    this.end = end;
    this._render();
  }

  getRange() {
    return { start: this.start, end: this.end };
  }

  setDateBounds(min, max) {
    this.dateMin = min;
    this.dateMax = max;
    this._render();
  }

  /* ── Inject styles (once) ────────────────────── */
  _injectStyles() {
    if (document.getElementById('drp-styles')) return;
    const style = document.createElement('style');
    style.id = 'drp-styles';
    style.textContent = `
/* ── DateRangePicker ─────────────────────── */
.drp-wrapper { position: relative; display: inline-block; }

.drp-trigger {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 16px; border-radius: 10px;
  background: linear-gradient(135deg, #1e293b 0%, #253349 100%);
  border: 1px solid #334155; color: #e2e8f0;
  font-family: inherit; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.drp-trigger:hover { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
.drp-icon { width: 16px; height: 16px; color: #60a5fa; flex-shrink: 0; }
.drp-chevron { width: 14px; height: 14px; color: #64748b; transition: transform 0.2s; flex-shrink: 0; }
.drp-chevron-up { transform: rotate(180deg); }
.drp-label { color: #f1f5f9; }

.drp-popover {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 1000;
  display: flex; background: #141b2b;
  border: 1px solid #334155; border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(59,130,246,0.08);
  overflow: hidden; animation: drpFadeIn 0.15s ease-out;
}
@keyframes drpFadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }

/* Presets panel */
.drp-presets {
  width: 170px; padding: 16px 12px;
  border-right: 1px solid #1e293b; display: flex; flex-direction: column; gap: 4px;
}
.drp-presets-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #475569; padding: 0 8px 8px; margin-bottom: 4px;
  border-bottom: 1px solid #1e293b;
}
.drp-preset {
  padding: 8px 12px; border: none; border-radius: 8px;
  background: transparent; color: #94a3b8; font-size: 13px;
  font-family: inherit; cursor: pointer; text-align: left;
  transition: all 0.15s;
}
.drp-preset:hover { background: #1e293b; color: #e2e8f0; }
.drp-preset-active { background: rgba(59,130,246,0.15); color: #60a5fa; font-weight: 600; }

/* Calendar panel */
.drp-calendar-panel { padding: 16px 20px; min-width: 290px; }

.drp-inputs-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}
.drp-input-group { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.drp-input-group label {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
  color: #64748b; font-weight: 600;
}
.drp-date-input {
  padding: 7px 10px; border: 1px solid #334155; border-radius: 8px;
  background: #0f172a; color: #e2e8f0; font-family: inherit; font-size: 12px;
  width: 100%;
}
.drp-date-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }
.drp-input-sep { color: #475569; font-size: 16px; padding-top: 18px; }

/* Calendar */
.drp-cal-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.drp-cal-title { font-size: 14px; font-weight: 600; color: #f1f5f9; }
.drp-cal-nav {
  width: 28px; height: 28px; border: none; border-radius: 6px;
  background: transparent; color: #94a3b8; font-size: 18px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.drp-cal-nav:hover { background: #1e293b; color: #e2e8f0; }

.drp-cal-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px;
}
.drp-cal-dow {
  font-size: 10px; color: #475569; text-align: center;
  padding: 4px 0; font-weight: 600; text-transform: uppercase;
}
.drp-cal-empty { padding: 6px; }
.drp-cal-day {
  padding: 6px 2px; text-align: center; font-size: 12px; color: #94a3b8;
  border-radius: 6px; cursor: pointer; transition: all 0.1s;
}
.drp-cal-day:hover { background: #1e293b; color: #e2e8f0; }
.drp-in-range { background: rgba(59,130,246,0.12); color: #93c5fd; }
.drp-range-start { background: #3b82f6 !important; color: #fff !important; border-radius: 6px 2px 2px 6px; font-weight: 600; }
.drp-range-end { background: #3b82f6 !important; color: #fff !important; border-radius: 2px 6px 6px 2px; font-weight: 600; }
.drp-range-start.drp-range-end { border-radius: 6px; }
.drp-disabled { color: #334155 !important; cursor: default; pointer-events: none; }

.drp-actions {
  display: flex; justify-content: flex-end; margin-top: 14px;
  padding-top: 12px; border-top: 1px solid #1e293b;
}
.drp-btn-apply {
  padding: 8px 24px; border: none; border-radius: 8px;
  background: #3b82f6; color: #fff; font-family: inherit;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.drp-btn-apply:hover { background: #2563eb; }

/* Responsive */
@media (max-width: 600px) {
  .drp-popover { flex-direction: column; right: -20px; }
  .drp-presets { width: auto; border-right: none; border-bottom: 1px solid #1e293b; flex-direction: row; flex-wrap: wrap; }
  .drp-presets-title { display: none; }
  .drp-calendar-panel { min-width: 260px; }
}
`;
    document.head.appendChild(style);
  }
}
