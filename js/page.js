/* Where the sun sets into the sea: the named beaches of Britain and Ireland on a plain MapLibre base map (OpenFreeMap
 * Positron), coloured by the days of the year when the Sun sets into (or rises out of) the open sea, with a date slider,
 * the line of sunset and sunrise from the chosen beach, and a rose of the year's bearings.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const ML = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const ALPH = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  const SEQ = ['#BDB8AE', '#F1DCA0', '#E6C27A', '#EDB457', '#E89A3C', '#D9782C', '#B95424'];   // none to all year
  const SEA = '#E8962E', LAND = '#8C8577';
  let map = null, D = null, S = null, sel = null, mode = qs.get('mode') || 'set', doy = +(qs.get('day') || 172);
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  const dayTxt = d => { let m = 0; while (d > ML[m]) { d -= ML[m]; m++; } return `${d} ${MONTHS[m]}`; };
  const R = Math.PI / 180;
  function decl(d) { const g = 2 * Math.PI / 365 * (d - 1); return (0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g)) / R; }
  function riseSet(lat, d) { const c = (Math.sin(decl(d) * R) - Math.sin(lat * R) * Math.sin(S.h0 * R)) / (Math.cos(lat * R) * Math.cos(S.h0 * R)); if (Math.abs(c) > 1) return [NaN, NaN]; const a = Math.acos(c) / R; return [a, 360 - a]; }
  function dest(lon, lat, az, m) { const p1 = lat * R, l1 = lon * R, a = az * R, dr = m / 6371000; const p2 = Math.asin(Math.sin(p1) * Math.cos(dr) + Math.cos(p1) * Math.sin(dr) * Math.cos(a)); const l2 = l1 + Math.atan2(Math.sin(a) * Math.sin(dr) * Math.cos(p1), Math.cos(dr) - Math.sin(p1) * Math.sin(p2)); return [l2 / R, p2 / R]; }
  const distOf = (str, d) => { const p = str.substr(2 * (d - 1), 2); return p === '..' ? null : 50 * (ALPH.indexOf(p[0]) * 62 + ALPH.indexOf(p[1])); };
  const isOpen = (str, d) => str[2 * (d - 1)] === '.';
  const cnt = str => { let n = 0; for (let k = 0; k < str.length; k += 2) if (str[k] === '.') n++; return n; };
  const km = m => m < 1000 ? `${Math.round(m / 10) * 10} m` : (m < 20000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m / 1000)} km`);
  function blockerTxt(b, ev, d) { const ch = b[ev + 'n'][d - 1]; if (ch === '.') return ''; const nm = b[ev + 'N'][ALPH.indexOf(ch)]; return nm === 'coast' ? 'the coast' : (nm === 'mainland' ? 'the far shore' : (nm ? nm : 'an island or rock')); }

  function colorExpr() {
    if (mode === 'date') return ['case', ['==', ['get', 'od'], 1], SEA, LAND];
    const k = mode === 'rise' ? 'r' : 's';
    return ['step', ['get', k], SEQ[0], 1, SEQ[1], 60, SEQ[2], 120, SEQ[3], 180, SEQ[4], 240, SEQ[5], 330, SEQ[6]];
  }
  function refresh() {
    const ev = mode === 'rise' ? 'rise' : 'set';
    D.feats.forEach(f => { const b = D.b[f.properties.i]; const evd = document.getElementById('evRise').getAttribute('aria-pressed') === 'true' ? 'r' : 's'; f.properties.od = isOpen(b[evd + 's'], doy) ? 1 : 0; });
    map.getSource('b').setData({ type: 'FeatureCollection', features: D.feats });
    map.setPaintProperty('pts', 'circle-color', colorExpr());
    document.getElementById('dTxt').textContent = dayTxt(doy);
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
    document.getElementById('keySeq').hidden = mode === 'date'; document.getElementById('keyDate').hidden = mode !== 'date';
    document.getElementById('keyTitle').textContent = mode === 'rise' ? 'Days the Sun rises out of the sea' : (mode === 'set' ? 'Days the Sun sets into the sea' : `On ${dayTxt(doy)}`);
    if (sel !== null) { drawLines(); rose(); }
  }
  function drawLines() {
    const b = D.b[sel], fs = [];
    const [ar, as] = riseSet(b.olat, doy);
    [['rise', ar], ['set', as]].forEach(([ev, az]) => { if (!isFinite(az)) return; const dm = distOf(b[ev[0] + 's'], doy); const L = dm ? Math.min(dm, 150000) : 40000;
      const pts = []; for (let k = 0; k <= 30; k++) pts.push(dest(b.olon, b.olat, az, L * k / 30));
      fs.push({ type: 'Feature', properties: { ev, open: dm ? 0 : 1 }, geometry: { type: 'LineString', coordinates: pts } });
      if (dm) fs.push({ type: 'Feature', properties: { ev, open: 0, end: 1, t: `${ev === 'set' ? 'Sunset' : 'Sunrise'} behind ${blockerTxt(b, ev[0], doy)}` }, geometry: { type: 'Point', coordinates: pts[30] } }); });
    fs.push({ type: 'Feature', properties: { obs: 1 }, geometry: { type: 'Point', coordinates: [b.olon, b.olat] } });
    map.getSource('ray').setData({ type: 'FeatureCollection', features: fs });
  }
  function rose() {
    const b = D.b[sel], W = 280, c = W / 2;
    const tick = (az, r0, r1, col, w) => { const s = Math.sin(az * R), k = -Math.cos(az * R); return `<line x1="${(c + r0 * s).toFixed(1)}" y1="${(c + r0 * k).toFixed(1)}" x2="${(c + r1 * s).toFixed(1)}" y2="${(c + r1 * k).toFixed(1)}" stroke="${col}" stroke-width="${w}"/>`; };
    let g = `<circle cx="${c}" cy="${c}" r="118" fill="#FBF5E4" stroke="#9C8656"/><circle cx="${c}" cy="${c}" r="70" fill="none" stroke="#E2D3AE"/>`;
    for (let a = 0; a < 360; a += 30) g += tick(a, 116, 120, '#9C8656', 1);
    [['N', 0], ['E', 90], ['S', 180], ['W', 270]].forEach(([t, a]) => { g += `<text x="${(c + 130 * Math.sin(a * R)).toFixed(0)}" y="${(c - 130 * Math.cos(a * R) + 4).toFixed(0)}" text-anchor="middle" class="ax">${t}</text>`; });
    for (let d = 1; d <= 365; d++) {
      const [ar, as] = riseSet(b.olat, d), h1 = d < 172 || d > 355;    // winter to summer: outer ring; summer to winter: inner ring
      const [r0, r1] = h1 ? [92, 112] : [74, 90];
      if (isFinite(as)) g += tick(as, r0, r1, isOpen(b.ss, d) ? SEA : LAND, 1.3);
      if (isFinite(ar)) g += tick(ar, r0, r1, isOpen(b.rs, d) ? '#3D7EA6' : LAND, 1.3);
    }
    const [ar, as] = riseSet(b.olat, doy);
    if (isFinite(as)) g += tick(as, 6, 118, '#A3261B', 1.6);
    if (isFinite(ar)) g += tick(ar, 6, 118, '#A3261B', 1.6);
    g += `<circle cx="${c}" cy="${c}" r="4" fill="#2B2119"/>`;
    g += `<text x="${c}" y="${c - 24}" text-anchor="middle" class="lg">outer ring: Dec to Jun</text><text x="${c}" y="${c - 12}" text-anchor="middle" class="lg">inner ring: Jun to Dec</text>`;
    const ns = cnt(b.ss), nr = cnt(b.rs);
    const bl = (ev) => { const cnt = {}; for (let d = 0; d < 365; d++) { const ch = b[ev + 'n'][d]; if (ch !== '.') { const nm = b[ev + 'N'][ALPH.indexOf(ch)] || 'an island or rock'; cnt[nm] = (cnt[nm] || 0) + 1; } }
      return Object.entries(cnt).filter(([k]) => k !== 'mainland' && k !== 'coast').sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${esc(k)} (${v} days)`).join(', '); };
    const bs = bl('s'), br = bl('r');
    const dset = distOf(b.ss, doy), drise = distOf(b.rs, doy);
    document.getElementById('hzBody').innerHTML = `<h3>${esc(b.n)}</h3>
      <p class="nt">${esc([b.town ? 'near ' + b.town : '', b.county, b.nat].filter(Boolean).join(', '))}${b.surf ? ' · ' + esc(b.surf.replace(/;/g, ', ')) : ''}</p>
      <div class="hzg"><svg viewBox="0 0 ${W} ${W}" role="img" aria-label="Rose of sunrise and sunset bearings through the year">${g}</svg>
      <div><p><b>${ns}</b> days a year the Sun sets into the sea${bs ? `; islands in the way: ${bs}` : ''}.</p>
      <p><b>${nr}</b> days it rises out of the sea${br ? `; islands in the way: ${br}` : ''}.</p>
      <p>On <b>${dayTxt(doy)}</b>: sunset ${dset ? `behind ${esc(blockerTxt(b, 's', doy))}, ${km(dset)} away` : '<b>into the open sea</b>'}; sunrise ${drise ? `behind ${esc(blockerTxt(b, 'r', doy))}, ${km(drise)} away` : '<b>out of the open sea</b>'}.</p>
      <p class="nt">Ticks: the bearing of sunset and sunrise on each day, <span style="color:${SEA}">gold</span> or <span style="color:#3D7EA6">blue</span> over open sea, grey behind land; red: the chosen day. From a point at the water's edge, eye 3 m above the sea.</p>
      <p class="nt"><a href="https://www.openstreetmap.org/${esc(b.osm[0])}" target="_blank" rel="noopener">OpenStreetMap</a></p></div></div>`;
    document.getElementById('hz').hidden = false;
  }
  function choose(i, fly) {
    sel = i; const b = D.b[i];
    if (fly) map.flyTo({ center: [b.olon, b.olat], zoom: small ? 8.6 : 9.4, duration: 1300 });
    drawLines(); rose();
  }
  function setup() {
    D.feats = D.b.map((b, i) => ({ type: 'Feature', properties: { i, s: cnt(b.ss), r: cnt(b.rs), od: 0, n: b.n }, geometry: { type: 'Point', coordinates: [b.olon, b.olat] } }));
    const before = (map.getStyle().layers.find(l => l.type === 'symbol') || {}).id;
    map.addSource('area', { type: 'geojson', data: 'data/area.geojson' });
    map.addLayer({ id: 'area', type: 'line', source: 'area', maxzoom: 7.5, paint: { 'line-color': '#A3261B', 'line-width': 1.2, 'line-dasharray': [3, 2], 'line-opacity': 0.7 } }, before);
    map.addSource('ray', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'ray', type: 'line', source: 'ray', filter: ['all', ['==', ['geometry-type'], 'LineString'], ['==', ['get', 'open'], 1]], layout: { 'line-cap': 'round' }, paint: { 'line-color': ['match', ['get', 'ev'], 'set', SEA, '#3D7EA6'], 'line-width': 3.2 } });
    map.addLayer({ id: 'ray-b', type: 'line', source: 'ray', filter: ['all', ['==', ['geometry-type'], 'LineString'], ['==', ['get', 'open'], 0]], paint: { 'line-color': '#6E604E', 'line-width': 2.6, 'line-dasharray': [2, 1.5] } });
    map.addLayer({ id: 'ray-end', type: 'symbol', source: 'ray', filter: ['==', ['get', 'end'], 1], layout: { 'text-field': ['get', 't'], 'text-size': 12, 'text-font': ['Noto Sans Italic'], 'text-anchor': 'top', 'text-offset': [0, 0.6] }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.6 } });
    map.addSource('b', { type: 'geojson', data: { type: 'FeatureCollection', features: D.feats }, attribution: 'Beaches and coast: <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> (ODbL); terrain: AWS Terrain Tiles' });
    map.addLayer({ id: 'pts-halo', type: 'circle', source: 'b', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 4.4, 8, 6.4, 13, 10.4], 'circle-color': '#fff', 'circle-opacity': 0.92 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'b', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 8, 5, 13, 9], 'circle-color': colorExpr(), 'circle-stroke-color': '#2B2119', 'circle-stroke-width': 0.7 } });
    map.addLayer({ id: 'obs', type: 'circle', source: 'ray', filter: ['==', ['get', 'obs'], 1], paint: { 'circle-radius': 6, 'circle-color': '#A3261B', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'b', minzoom: 9, layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Italic'], 'text-offset': [0, 0.9], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#4A3B2B', 'text-halo-color': '#fff', 'text-halo-width': 1.4 } });
    map.on('click', 'pts', e => choose(e.features[0].properties.i, false));
    map.on('mouseenter', 'pts', () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', 'pts', () => map.getCanvas().style.cursor = '');
    document.getElementById('hzX').addEventListener('click', () => { document.getElementById('hz').hidden = true; sel = null; map.getSource('ray').setData({ type: 'FeatureCollection', features: [] }); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyB').addEventListener('change', e => vis(['pts', 'pts-halo'], e.target.checked));
    document.getElementById('lyR').addEventListener('change', e => vis(['ray', 'ray-b', 'ray-end', 'obs'], e.target.checked));
    document.getElementById('lyL').addEventListener('change', e => vis(['lbl'], e.target.checked));
    document.getElementById('lyA').addEventListener('change', e => vis(['area'], e.target.checked));
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    ['evSet', 'evRise'].forEach(id => document.getElementById(id).addEventListener('click', () => { document.getElementById('evSet').setAttribute('aria-pressed', id === 'evSet'); document.getElementById('evRise').setAttribute('aria-pressed', id === 'evRise'); refresh(); }));
    const s = document.getElementById('day'); s.value = doy;
    s.addEventListener('input', () => { doy = +s.value; refresh(); });
    document.querySelectorAll('[data-day]').forEach(b => b.addEventListener('click', () => { doy = +b.dataset.day; s.value = doy; refresh(); }));
    let timer = null; const play = document.getElementById('play');
    play.addEventListener('click', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = '▶'; return; } play.textContent = '❚❚';
      timer = setInterval(() => { doy = doy % 365 + 3; s.value = doy; refresh(); }, 500); });
    refresh();
    if (qs.get('beach')) { const i = D.b.findIndex(b => norm(b.n) === norm(qs.get('beach'))); if (i >= 0) choose(i, true); }
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.b.map((b, i) => ({ n: b.n, nn: norm(b.n), i, s: [b.town, b.county].filter(Boolean).join(', ') }));
    D.b.forEach((b, i) => { if (b.town && !idx.some(x => x.town && x.nn === norm(b.town))) idx.push({ n: b.town, nn: norm(b.town), i, s: 'town · nearest beach ' + b.n, town: 1 }); });
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 3 && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; fold(true); choose(it.i, true); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const i = D.b.findIndex(b => b.id === +a.dataset.go); if (i < 0) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); if (a.dataset.d) { doy = +a.dataset.d; document.getElementById('day').value = doy; refresh(); } choose(i, true); }));
  }
  Promise.all([fetch('data/beaches.json').then(r => r.json()), fetch('data/site.json').then(r => r.json())]).then(([d, s]) => {
    D = d; S = s;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-10.8, 49.8], [1.9, 60.9]], fitBoundsOptions: { padding: small ? 10 : { top: 40, bottom: 90, left: 330, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 16 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.tl,.hz,.keys,.mfs-btn,.maplibregl-ctrl')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
