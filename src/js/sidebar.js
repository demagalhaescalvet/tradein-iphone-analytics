/**
 * Sidebar Navigation — Replaces horizontal nav bar
 * Inspired by Stitch design mockups. Collapsible, icon-based, dark theme.
 *
 * Usage: Add <script src="js/sidebar.js"></script> before </body>
 *        Then call: initSidebar('dashboard') where arg = active page key
 *
 * Pages: overview, dashboard, explorer, sankey, migration, insights, curves, benchmark, elasticity
 */

const SIDEBAR_PAGES = [
  { key:'overview',    href:'index.html',      icon:'home',      label:'Overview' },
  { key:'dashboard',   href:'dashboard.html',  icon:'grid',      label:'Dashboard General' },
  { key:'explorer',    href:'explorer.html',   icon:'trending',  label:'Trends Explorer' },
  { key:'sankey',      href:'sankey.html',     icon:'shuffle',   label:'Migration Sankey' },
  { key:'migration',   href:'migration.html',  icon:'matrix',    label:'Matriz Migración' },
  { key:'insights',    href:'insights.html',   icon:'bulb',      label:'Insights Avanzados' },
  { key:'curves',      href:'curves.html',     icon:'chart',     label:'Curvas de Valor' },
  { key:'benchmark',   href:'benchmark.html',  icon:'bar',       label:'Benchmarks' },
  { key:'elasticity',  href:'elasticity.html', icon:'activity',  label:'Elasticidad' },
];

const SIDEBAR_ICONS = {
  home: '<path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
  trending: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
  shuffle: '<polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/>',
  matrix: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/>',
  bulb: '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 00-4 12.7V17h8v-2.3A7 7 0 0012 2z"/>',
  chart: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><path d="M2 2s3 2 5-1 5 1 5 1 3-2 5 1 5-1 5-1"/>',
  bar: '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
  activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  collapse: '<polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/>',
  expand: '<polyline points="13 7 18 12 13 17"/><polyline points="6 7 11 12 6 17"/>',
};

function initSidebar(activeKey) {
  // Inject styles
  if (!document.getElementById('sb-styles')) {
    const style = document.createElement('style');
    style.id = 'sb-styles';
    style.textContent = `
/* ── Sidebar ─────────────────────────────────── */
.sb { position:fixed; top:0; left:0; height:100vh; width:220px; background:#0c111b; border-right:1px solid #1e293b; z-index:900; display:flex; flex-direction:column; transition:width 0.25s cubic-bezier(.4,0,.2,1); overflow:hidden; }
.sb.sb-collapsed { width:56px; }
.sb-logo { padding:16px 14px; display:flex; align-items:center; gap:10px; border-bottom:1px solid #1e293b; min-height:56px; cursor:default; }
.sb-logo-icon { width:28px; height:28px; background:linear-gradient(135deg,#3b82f6,#8b5cf6); border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.sb-logo-icon svg { width:16px; height:16px; stroke:#fff; fill:none; stroke-width:2; }
.sb-logo-text { font-size:13px; font-weight:700; color:#f1f5f9; white-space:nowrap; overflow:hidden; line-height:1.2; }
.sb-logo-text span { display:block; font-size:10px; font-weight:500; color:#64748b; letter-spacing:.5px; text-transform:uppercase; }
.sb.sb-collapsed .sb-logo-text { opacity:0; width:0; }

.sb-nav { flex:1; overflow-y:auto; padding:8px 8px; display:flex; flex-direction:column; gap:2px; }
.sb-link { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:8px; text-decoration:none; color:#64748b; font-size:13px; font-weight:500; transition:all .15s; white-space:nowrap; overflow:hidden; position:relative; }
.sb-link:hover { color:#cbd5e1; background:#1e293b; }
.sb-link.sb-active { color:#f1f5f9; background:rgba(59,130,246,0.12); }
.sb-link.sb-active::before { content:''; position:absolute; left:0; top:6px; bottom:6px; width:3px; border-radius:0 3px 3px 0; background:#3b82f6; }
.sb-link svg { width:18px; height:18px; flex-shrink:0; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.sb-link.sb-active svg { stroke:#60a5fa; }
.sb-link-label { overflow:hidden; text-overflow:ellipsis; }
.sb.sb-collapsed .sb-link-label { opacity:0; width:0; }
.sb.sb-collapsed .sb-link { justify-content:center; padding:9px 0; }
.sb.sb-collapsed .sb-link.sb-active::before { left:0; }

.sb-toggle { padding:8px; border-top:1px solid #1e293b; display:flex; justify-content:center; }
.sb-toggle-btn { background:none; border:none; color:#475569; cursor:pointer; padding:6px; border-radius:6px; transition:all .15s; display:flex; align-items:center; justify-content:center; }
.sb-toggle-btn:hover { color:#94a3b8; background:#1e293b; }
.sb-toggle-btn svg { width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }

/* Tooltip on collapsed */
.sb.sb-collapsed .sb-link { position:relative; }
.sb.sb-collapsed .sb-link::after { content:attr(data-tip); position:absolute; left:calc(100% + 8px); top:50%; transform:translateY(-50%); background:#1e293b; color:#e2e8f0; padding:5px 10px; border-radius:6px; font-size:12px; white-space:nowrap; pointer-events:none; opacity:0; transition:opacity .15s; border:1px solid #334155; z-index:1000; }
.sb.sb-collapsed .sb-link:hover::after { opacity:1; }

/* Main content offset */
body.sb-body { margin-left:220px !important; transition:margin-left 0.25s cubic-bezier(.4,0,.2,1); }
body.sb-body.sb-body-collapsed { margin-left:56px !important; }

/* Remove old nav */
body.sb-body > nav:first-of-type,
body.sb-body > nav[style*="background:#0c111b"] { display:none !important; }

/* Responsive */
@media (max-width:768px) {
  .sb { width:56px; }
  .sb .sb-logo-text, .sb .sb-link-label { opacity:0; width:0; }
  .sb .sb-link { justify-content:center; padding:9px 0; }
  body.sb-body { margin-left:56px !important; }
  .sb-toggle { display:none; }
}
`;
    document.head.appendChild(style);
  }

  // Remove existing nav
  const oldNav = document.querySelector('nav');
  if (oldNav) oldNav.remove();

  // Build sidebar HTML
  let html = '<div class="sb-logo">';
  html += '<div class="sb-logo-icon"><svg viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="3"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></div>';
  html += '<div class="sb-logo-text">iPhone Trade-In<span>Analytics</span></div>';
  html += '</div>';
  html += '<div class="sb-nav">';

  SIDEBAR_PAGES.forEach(p => {
    const active = p.key === activeKey ? ' sb-active' : '';
    const iconSvg = SIDEBAR_ICONS[p.icon] || '';
    html += '<a href="' + p.href + '" class="sb-link' + active + '" data-tip="' + p.label + '">';
    html += '<svg viewBox="0 0 24 24">' + iconSvg + '</svg>';
    html += '<span class="sb-link-label">' + p.label + '</span>';
    html += '</a>';
  });

  html += '</div>';
  html += '<div class="sb-toggle">';
  html += '<button class="sb-toggle-btn" id="sb-toggle-btn" title="Colapsar menú">';
  html += '<svg viewBox="0 0 24 24">' + SIDEBAR_ICONS.collapse + '</svg>';
  html += '</button>';
  html += '</div>';

  // Insert sidebar
  const sidebar = document.createElement('div');
  sidebar.className = 'sb';
  sidebar.id = 'mainSidebar';
  sidebar.innerHTML = html;
  document.body.prepend(sidebar);
  document.body.classList.add('sb-body');

  // Toggle collapse
  const toggleBtn = document.getElementById('sb-toggle-btn');
  const sb = document.getElementById('mainSidebar');
  const savedState = localStorage.getItem('sb-collapsed');
  if (savedState === 'true') {
    sb.classList.add('sb-collapsed');
    document.body.classList.add('sb-body-collapsed');
    toggleBtn.innerHTML = '<svg viewBox="0 0 24 24">' + SIDEBAR_ICONS.expand + '</svg>';
  }

  toggleBtn.addEventListener('click', function() {
    const collapsed = sb.classList.toggle('sb-collapsed');
    document.body.classList.toggle('sb-body-collapsed', collapsed);
    toggleBtn.innerHTML = '<svg viewBox="0 0 24 24">' + SIDEBAR_ICONS[collapsed ? 'expand' : 'collapse'] + '</svg>';
    try { localStorage.setItem('sb-collapsed', collapsed); } catch(e) {}
  });
}
