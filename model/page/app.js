(function () {
  const PARTY = { D: '#2E6BD6', R: '#D4403A', I: '#8A63C9' };
  const MINUS = '−';
  const fPct = d3.format('.0%'), fInt = d3.format(','), f1 = d3.format('.1f'), f2 = d3.format('.2f');
  const fS1 = d3.format('+.1f'), fS2 = d3.format('+.2f'), fSI = d3.format('+d');
  const fDate = d3.utcFormat('%b %-d, %Y'), fDay = d3.utcFormat('%b %-d');
  const fix = (s) => s.replace('-', MINUS);
  const blank = (v) => v === null || v === undefined || v === '' || (typeof v === 'number' && Number.isNaN(v));

  function fmt(v, f) {
    if (blank(v)) return '';
    switch (f) {
      case 'pct': return fPct(+v);
      case 'int': return fInt(+v);
      case 'dec1': return f1(+v);
      case 'dec2': return f2(+v);
      case 'sdec1': return +v === 0 ? '0.0' : fix(fS1(+v));
      case 'sdec2': return +v === 0 ? '0.00' : fix(fS2(+v));
      case 'sint': return +v === 0 ? '0' : fix(fSI(+v));
      case 'date': return fDate(new Date(String(v).slice(0, 10) + 'T00:00:00Z'));
      default: return String(v);
    }
  }
  const lead = (m, pos, neg) => (Math.abs(m) < 0.05 ? 'Even' : (m > 0 ? pos : neg) + '+' + f1(Math.abs(m)));

  function parseWhere(w) {
    const o = {};
    (w || '').split('&').forEach((p) => { if (!p) return; const i = p.indexOf('='); o[decodeURIComponent(p.slice(0, i))] = decodeURIComponent(p.slice(i + 1)); });
    return o;
  }
  function pickRow(rows, el) {
    if (el.dataset.where) { const w = parseWhere(el.dataset.where); return rows.find((r) => Object.keys(w).every((k) => String(r[k]) === w[k])); }
    if (el.dataset.row) return rows[+el.dataset.row];
    return rows[0];
  }
  function failNote(el) {
    const div = document.createElement('div'); div.className = 'mt-fail'; div.textContent = 'Failed to load'; el.replaceChildren(div);
  }
  function tipFor(el) {
    const tip = document.createElement('div'); tip.className = 'mt-tip'; tip.hidden = true; el.appendChild(tip);
    return {
      show(lines, x, y) {
        tip.replaceChildren(...lines.map((l, i) => { const d = document.createElement('div'); if (i === 0) d.className = 't'; if (l.color) { const s = document.createElement('span'); s.className = 'mt-sw'; s.style.background = l.color; d.appendChild(s); } d.appendChild(document.createTextNode(l.text || l)); return d; }));
        tip.hidden = false;
        const W = el.clientWidth, tw = tip.offsetWidth, th = tip.offsetHeight;
        let left = x + 12; if (left + tw > W) left = Math.max(0, x - tw - 12);
        let top = y - th - 8; if (top < 0) top = y + 12;
        tip.style.left = left + 'px'; tip.style.top = top + 'px';
      },
      hide() { tip.hidden = true; },
    };
  }
  function svgFor(el, H) {
    const W = Math.max(280, el.clientWidth || 600);
    const svg = d3.create('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).attr('preserveAspectRatio', 'xMinYMin meet');
    el.replaceChildren(svg.node());
    return { svg, W, H };
  }
  function measure(svg, texts, size) {
    const t = svg.append('text').attr('font-size', size).attr('visibility', 'hidden');
    let w = 0; texts.forEach((s) => { t.text(s); w = Math.max(w, t.node().getComputedTextLength()); }); t.remove(); return w;
  }
  function styleAxis(g) {
    g.attr('font-size', null).attr('font-family', null);
    g.selectAll('text').attr('fill', 'var(--color-fg-muted)').style('font-size', 'var(--cds-font-size-caption)');
    g.selectAll('.domain').attr('stroke', 'var(--cds-chart-axis)');
    g.selectAll('.tick line').attr('stroke', 'var(--cds-chart-grid)');
  }
  const pointer = (event, el) => { const r = el.getBoundingClientRect(); return [event.clientX - r.left, event.clientY - r.top]; };

  // ---------- generic value
  dash.draw('v', (el) => {
    const d = dash.data(el.dataset.source);
    if (d.status !== 'ok') { el.textContent = '—'; return; }
    const row = pickRow(d.data, el);
    const s = row ? fmt(row[el.dataset.field], el.dataset.fmt) : '';
    el.textContent = s === '' ? '—' : s;
  });

  // ---------- tables (search + sort)
  dash.draw('tbl', (tbody) => {
    const table = tbody.closest('table');
    const d = dash.data(table.dataset.source);
    if (d.status !== 'ok') { tbody.replaceChildren(); return; }
    const ths = Array.from(table.querySelectorAll('thead th'));
    const cols = ths.map((th) => ({ field: th.dataset.field, fmt: th.dataset.fmt || '', right: th.classList.contains('r') }));
    let rows = d.data.slice();
    const card = table.closest('.mt-card');
    const box = card ? card.querySelector('.mt-search') : null;
    const q = box ? box.value.trim().toLowerCase() : '';
    if (q) rows = rows.filter((r) => cols.some((c) => String(r[c.field] ?? '').toLowerCase().includes(q)));
    const sorted = ths.find((th) => ['ascending', 'descending'].includes(th.getAttribute('aria-sort')));
    if (sorted) {
      const f = sorted.dataset.field, dir = sorted.getAttribute('aria-sort') === 'ascending' ? 1 : -1;
      rows.sort((a, b) => {
        const x = a[f], y = b[f];
        if (blank(x) && blank(y)) return 0; if (blank(x)) return 1; if (blank(y)) return -1;
        return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * dir;
      });
    }
    const key = table.dataset.rowKey;
    tbody.replaceChildren(...rows.map((r) => {
      const tr = document.createElement('tr');
      cols.forEach((c) => {
        const td = document.createElement('td');
        if (c.right) td.className = 'r';
        td.textContent = c.field === key ? String(r[c.field]) : fmt(r[c.field], c.fmt);
        tr.appendChild(td);
      });
      return tr;
    }));
  });

  // ---------- seat distribution
  dash.draw('dist', (el) => {
    const d = dash.data('seat_dist');
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const ch = el.dataset.chamber;
    const rows = d.data.filter((r) => r.chamber === ch).map((r) => ({ seats: +r.seats, prob: +r.prob, thr: +r.threshold }));
    if (!rows.length) { el.replaceChildren(); return; }
    const thr = rows[0].thr;
    const lo = d3.min(rows, (r) => r.seats), hi = d3.max(rows, (r) => r.seats);
    const all = d3.range(lo, hi + 1).map((s) => rows.find((r) => r.seats === s) || { seats: s, prob: 0 });
    const { svg, W, H } = svgFor(el, 208);
    const ymax = d3.max(all, (r) => r.prob);
    const yTicks = d3.scaleLinear([0, ymax], [0, 1]).ticks(4);
    const ml = measure(svg, yTicks.map((t) => d3.format('.0%')(t)), 12) + 10;
    const m = { t: 10, r: 8, b: 26, l: ml };
    const x = d3.scaleBand(all.map((r) => r.seats), [m.l, W - m.r]).paddingInner(all.length > 40 ? 0.15 : 0.2);
    const y = d3.scaleLinear([0, ymax], [H - m.b, m.t]).nice();
    const gy = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat(d3.format('.0%')).tickSize(-(W - m.l - m.r)));
    styleAxis(gy); gy.select('.domain').remove();
    const step = Math.max(1, Math.ceil(measure(svg, [String(hi)], 12) * 2.2 / x.step()));
    const nice = [1, 2, 5, 10, 20].find((s) => s >= step) || step;
    const gx = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).tickValues(all.map((r) => r.seats).filter((s) => s % nice === 0)).tickSize(3));
    styleAxis(gx);
    const color = (s) => (s >= thr ? PARTY.D : (ch === 'governors' && s === thr - 1 ? 'var(--cds-chart-muted)' : PARTY.R));
    const bars = svg.append('g').selectAll('rect').data(all).join('rect')
      .attr('x', (r) => x(r.seats)).attr('width', x.bandwidth())
      .attr('y', (r) => y(r.prob)).attr('height', (r) => Math.max(0, y(0) - y(r.prob)))
      .attr('rx', Math.min(2, x.bandwidth() / 2)).attr('fill', (r) => color(r.seats));
    if (x(thr) !== undefined) {
      const xl = x(thr) - (x.step() - x.bandwidth()) / 2;
      svg.append('line').attr('x1', xl).attr('x2', xl).attr('y1', m.t).attr('y2', H - m.b)
        .attr('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
    }
    const tip = tipFor(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('pointermove', (event) => {
        const [px, py] = pointer(event, el);
        const i = Math.max(0, Math.min(all.length - 1, Math.floor((px - m.l) / x.step())));
        const r = all[i];
        bars.attr('opacity', (b) => (b.seats === r.seats ? 1 : 0.55));
        const word = ch === 'governors' ? ' Democratic governors' : ' Democratic seats';
        tip.show([{ text: fInt(r.seats) + word }, { text: d3.format('.1%')(r.prob) + ' of simulations' }], px, py);
      })
      .on('pointerleave', () => { bars.attr('opacity', 1); tip.hide(); });
  });

  // ---------- polling-miss scenarios
  dash.draw('scen', (el) => {
    const s = dash.data('scenarios'), cb = dash.data('cycle_bias');
    if (s.status === 'error') { failNote(el); return; }
    if (s.status !== 'ok') { el.replaceChildren(); return; }
    const rows = s.data.map((r) => ({ x: +r.shift, sen: +r.senate_dem_control, house: +r.house_dem_control, ss: +r.senate_dem_seats, hs: +r.house_dem_seats }));
    const { svg, W, H } = svgFor(el, 300);
    const m = { t: 12, r: 12, b: 70, l: measure(svg, ['100%'], 12) + 10 };
    const x = d3.scaleLinear(d3.extent(rows, (r) => r.x), [m.l, W - m.r]);
    const y = d3.scaleLinear([0, 1], [H - m.b, m.t]);
    const gy = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('.0%')).tickSize(-(W - m.l - m.r)));
    styleAxis(gy); gy.select('.domain').remove();
    const gx = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.min(13, Math.floor((W - m.l - m.r) / 36))).tickFormat((v) => (v === 0 ? '0' : fix(fSI(v)))).tickSize(3));
    styleAxis(gx);
    svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0.5)).attr('y2', y(0.5)).attr('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
    svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', m.t).attr('y2', H - m.b).attr('stroke', 'var(--cds-chart-axis)');
    const series = [{ k: 'sen', c: dash.colors[0] }, { k: 'house', c: dash.colors[1] }];
    series.forEach((sr) => svg.append('path').datum(rows).attr('fill', 'none').attr('stroke', sr.c).attr('stroke-width', 2)
      .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round').attr('d', d3.line().x((r) => x(r.x)).y((r) => y(r[sr.k]))));
    if (cb.status === 'ok') {
      const [x0, x1] = x.domain();
      const marks = cb.data.filter((r) => !blank(r.state_poll_bias)).map((r) => ({ year: String(r.cycle), v: -r.state_poll_bias }))
        .map((r) => ({ ...r, cx: x(Math.max(x0, Math.min(x1, r.v))), out: r.v < x0 || r.v > x1 })).sort((a, b) => a.cx - b.cx);
      const yb = H - m.b + 30;
      let lastEnd = [-Infinity, -Infinity];
      marks.forEach((mk) => {
        const label = mk.out ? (mk.v > 0 ? mk.year + ' →' : '← ' + mk.year) : mk.year;
        const w = measure(svg, [label], 12);
        let row = 0; if (mk.cx - w / 2 < lastEnd[0] + 4) row = 1; if (row === 1 && mk.cx - w / 2 < lastEnd[1] + 4) row = 0;
        lastEnd[row] = mk.cx + w / 2;
        svg.append('path').attr('d', d3.symbol(d3.symbolTriangle, 36)()).attr('transform', `translate(${mk.cx},${H - m.b + 14})`).attr('fill', 'var(--color-fg-muted)');
        const tx = Math.max(m.l + w / 2, Math.min(W - m.r - w / 2, mk.cx));
        svg.append('text').attr('x', tx).attr('y', yb + row * 16).attr('text-anchor', 'middle').attr('fill', 'var(--color-fg-muted)').style('font-size', 'var(--cds-font-size-caption)').text(label);
      });
    }
    const dots = series.map((sr) => svg.append('circle').attr('r', 4.5).attr('fill', sr.c).attr('stroke', 'var(--color-panel)').attr('stroke-width', 2).attr('opacity', 0));
    const rule = svg.append('line').attr('y1', m.t).attr('y2', H - m.b).attr('stroke', 'var(--cds-chart-axis)').attr('opacity', 0);
    const tip = tipFor(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('pointermove', (event) => {
        const [px, py] = pointer(event, el);
        const xv = Math.round(x.invert(px)); const r = rows.reduce((a, b) => (Math.abs(b.x - xv) < Math.abs(a.x - xv) ? b : a));
        rule.attr('x1', x(r.x)).attr('x2', x(r.x)).attr('opacity', 1);
        dots[0].attr('cx', x(r.x)).attr('cy', y(r.sen)).attr('opacity', 1); dots[1].attr('cx', x(r.x)).attr('cy', y(r.house)).attr('opacity', 1);
        const head = r.x === 0 ? 'Polls exactly right' : (r.x > 0 ? 'Democrats beat polls by ' + f1(r.x) : 'Republicans beat polls by ' + f1(-r.x));
        tip.show([{ text: head }, { color: series[0].c, text: 'Senate control ' + fPct(r.sen) + ', ' + f1(r.ss) + ' D seats' }, { color: series[1].c, text: 'House control ' + fPct(r.house) + ', ' + f1(r.hs) + ' D seats' }], px, py);
      })
      .on('pointerleave', () => { rule.attr('opacity', 0); dots.forEach((d) => d.attr('opacity', 0)); tip.hide(); });
  });

  // ---------- race margins with 80% range
  dash.draw('dots', (el) => {
    const d = dash.data(el.dataset.source);
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const rows = d.data.filter((r) => !String(r.model_rating).startsWith('Safe') || r.favored !== r.holder).sort((a, b) => b.margin - a.margin);
    if (!rows.length) { el.replaceChildren(); return; }
    const rowH = 26, H = rows.length * rowH + 34;
    const { svg, W } = svgFor(el, H);
    const left = measure(svg, rows.map((r) => r.race), 12) + 12;
    const rightLabels = rows.map((r) => { const p = r.p_win >= 0.5 ? r.p_win : 1 - r.p_win; return (r.p_win >= 0.5 ? r.chal : 'R') + ' ' + fPct(p); });
    const right = measure(svg, rightLabels, 12) + 12;
    const lim = Math.min(30, Math.max(8, d3.max(rows, (r) => Math.max(Math.abs(r.margin_lo), Math.abs(r.margin_hi)))));
    const x = d3.scaleLinear([-lim, lim], [left, W - right]).nice();
    const top = 22;
    const gx = svg.append('g').attr('transform', `translate(0,${top - 6})`).call(d3.axisTop(x).ticks(Math.max(3, Math.floor((W - left - right) / 60))).tickFormat((v) => (v === 0 ? '0' : (v > 0 ? '+' : MINUS) + Math.abs(v))).tickSize(-(rows.length * rowH)));
    styleAxis(gx); gx.select('.domain').remove();
    svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', top - 6).attr('y2', top + rows.length * rowH).attr('stroke', 'var(--cds-chart-reference)');
    const tip = tipFor(el);
    const g = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', (r, i) => `translate(0,${top + i * rowH + rowH / 2})`);
    const col = (r) => PARTY[r.favored] || PARTY.R;
    g.append('text').attr('x', left - 10).attr('dy', '0.35em').attr('text-anchor', 'end').attr('fill', 'var(--color-fg)').style('font-size', 'var(--cds-font-size-caption)').text((r) => r.race);
    g.append('line').attr('x1', (r) => x(Math.max(-lim, r.margin_lo))).attr('x2', (r) => x(Math.min(lim, r.margin_hi))).attr('stroke', col).attr('stroke-width', 2).attr('stroke-linecap', 'round').attr('opacity', 0.45);
    g.append('circle').attr('cx', (r) => x(Math.max(-lim, Math.min(lim, r.margin)))).attr('r', 5).attr('fill', col).attr('stroke', 'var(--color-panel)').attr('stroke-width', 2);
    g.append('text').attr('x', W - right + 10).attr('dy', '0.35em').attr('fill', 'var(--color-fg-muted)').style('font-size', 'var(--cds-font-size-caption)').text((r, i) => rightLabels[i]);
    g.append('rect').attr('x', 0).attr('y', -rowH / 2).attr('width', W).attr('height', rowH).attr('fill', 'transparent')
      .on('pointermove', (event, r) => {
        const [px, py] = pointer(event, el);
        const p = r.p_win >= 0.5 ? r.p_win : 1 - r.p_win;
        const who = r.p_win >= 0.5 ? r.dem : r.rep;
        tip.show([{ text: r.race }, { text: r.dem + ' vs ' + r.rep }, { color: col(r), text: 'Model margin ' + lead(r.margin, r.chal, 'R') + ' (80%: ' + lead(r.margin_lo, r.chal, 'R') + ' to ' + lead(r.margin_hi, r.chal, 'R') + ')' },
          { text: 'Win chance: ' + who + ' ' + fPct(p) }, { text: blank(r.poll_avg) ? 'No polls' : 'Poll average ' + lead(r.poll_avg, r.chal, 'R') + ' across ' + fInt(r.polls) + ' polls' }], px, py);
      })
      .on('pointerleave', () => tip.hide());
  });

  // ---------- House win-probability ladder
  dash.draw('ladder', (el) => {
    const d = dash.data('house_races');
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const rows = d.data.slice().sort((a, b) => b.p_win - a.p_win);
    const { svg, W, H } = svgFor(el, 220);
    const m = { t: 10, r: 8, b: 10, l: measure(svg, ['100%'], 12) + 10 };
    const x = d3.scaleBand(rows.map((r) => r.district), [m.l, W - m.r]).paddingInner(0.2);
    const y = d3.scaleLinear([0, 1], [H - m.b, m.t]);
    const gy = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).tickValues([0, 0.25, 0.5, 0.75, 1]).tickFormat(d3.format('.0%')).tickSize(-(W - m.l - m.r)));
    styleAxis(gy); gy.select('.domain').remove();
    const col = (r) => (r.p_win >= 0.5 ? PARTY.D : PARTY[r.neg] || PARTY.R);
    const bars = svg.append('g').selectAll('rect').data(rows).join('rect').attr('x', (r) => x(r.district)).attr('width', x.bandwidth())
      .attr('y', (r) => y(Math.max(0.5, r.p_win))).attr('height', (r) => Math.abs(y(r.p_win) - y(0.5)))
      .attr('rx', Math.min(2, x.bandwidth() / 2)).attr('fill', col);
    svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0.5)).attr('y2', y(0.5)).attr('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
    const tip = tipFor(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('pointermove', (event) => {
        const [px, py] = pointer(event, el);
        const i = Math.max(0, Math.min(rows.length - 1, Math.floor((px - m.l) / x.step()))); const r = rows[i];
        bars.attr('opacity', (b) => (b.district === r.district ? 1 : 0.5));
        tip.show([{ text: r.district + ' · ' + r.pvi + ' · held by ' + r.holder }, { text: 'Cook ' + r.cook + ', Sabato ' + r.sabato + ', IE ' + r.ie },
          { color: col(r), text: 'Model margin ' + lead(r.margin, 'D', r.neg) + ', D win chance ' + fPct(r.p_win) }], px, py);
      })
      .on('pointerleave', () => { bars.attr('opacity', 1); tip.hide(); });
  });

  // ---------- generic ballot polls
  dash.draw('gbchart', (el) => {
    const d = dash.data('polls'), p = dash.data('params');
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok' || p.status !== 'ok') { el.replaceChildren(); return; }
    const rows = d.data.filter((r) => r.contest === 'Generic ballot').map((r) => ({ ...r, date: new Date(r.end + 'T00:00:00Z') }));
    const avgRow = p.data.find((r) => r.key === 'gb');
    if (!rows.length) { el.replaceChildren(); return; }
    const { svg, W, H } = svgFor(el, 220);
    const yv = rows.map((r) => r.adj_margin).concat(avgRow ? [avgRow.value] : []);
    const y = d3.scaleLinear([Math.min(0, d3.min(yv) - 1), d3.max(yv) + 1], [H - 26, 10]).nice();
    const m = { t: 10, r: 10, b: 26, l: measure(svg, y.ticks(4).map((t) => (t > 0 ? '+' : '') + t), 12) + 10 };
    const x = d3.scaleUtc(d3.extent(rows, (r) => r.date), [m.l + 6, W - m.r - 6]);
    const gy = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat((v) => (v > 0 ? 'D+' + v : v === 0 ? '0' : 'R+' + Math.abs(v))).tickSize(-(W - m.l - m.r)));
    styleAxis(gy); gy.select('.domain').remove();
    const gx = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.max(2, Math.floor((W - m.l) / 90))).tickFormat(fDay).tickSize(3));
    styleAxis(gx);
    if (avgRow) svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(avgRow.value)).attr('y2', y(avgRow.value)).attr('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
    const r = d3.scaleSqrt([0, d3.max(rows, (q) => q.weight)], [2.5, 7]);
    const dots = svg.append('g').selectAll('circle').data(rows).join('circle').attr('cx', (q) => x(q.date)).attr('cy', (q) => y(q.adj_margin)).attr('r', (q) => r(q.weight))
      .attr('fill', PARTY.D).attr('fill-opacity', 0.75).attr('stroke', 'var(--color-panel)').attr('stroke-width', 1.5);
    const tip = tipFor(el);
    const pts = rows.map((q) => [x(q.date), y(q.adj_margin)]);
    const del = d3.Delaunay.from(pts);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('pointermove', (event) => {
        const [px, py] = pointer(event, el);
        const i = del.find(px, py); const q = rows[i];
        dots.attr('fill-opacity', (o) => (o === q ? 1 : 0.35));
        tip.show([{ text: q.pollster + ', ' + fDay(q.date) }, { text: 'Raw ' + lead(q.margin_2p, 'D', 'R') + ', adjusted ' + lead(q.adj_margin, 'D', 'R') }, { text: q.pop + (blank(q.n) ? '' : ', n = ' + fInt(q.n)) + ', weight ' + f2(q.weight) }], px, py);
      })
      .on('pointerleave', () => { dots.attr('fill-opacity', 0.75); tip.hide(); });
  });

  // ---------- sources list
  dash.draw('srcs', (ul) => {
    const d = dash.data('sources');
    if (d.status !== 'ok') { ul.replaceChildren(); return; }
    ul.replaceChildren(...d.data.map((r) => {
      const li = document.createElement('li'); const a = document.createElement('a');
      if (/^https:\/\//.test(String(r.url))) { a.href = r.url; a.target = '_blank'; a.rel = 'noopener noreferrer'; }
      a.textContent = r.title; li.append(a, document.createTextNode(': ' + r.used_for)); return li;
    }));
  });

  // ---------- controls: tabs, sorting, search, legend colors
  const TABS = ['overview', 'senate', 'governors', 'house', 'polls', 'method'];
  let current = TABS.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'overview';
  function show() {
    document.querySelectorAll('[data-page]').forEach((s) => { s.hidden = s.dataset.page !== current; });
    document.querySelectorAll('.mt-tab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === current)));
  }
  document.querySelectorAll('.mt-tab').forEach((b) => b.addEventListener('click', () => { current = b.dataset.tab; show(); dash.setLink(current); }));
  document.querySelectorAll('.mt-table th .mt-sort').forEach((btn) => btn.addEventListener('click', () => {
    const th = btn.closest('th'); const was = th.getAttribute('aria-sort');
    th.closest('tr').querySelectorAll('th').forEach((o) => { if (o.hasAttribute('aria-sort')) o.setAttribute('aria-sort', 'none'); });
    th.setAttribute('aria-sort', was === 'descending' ? 'ascending' : 'descending');
    dash.draw('tbl');
  }));
  document.querySelectorAll('.mt-search').forEach((inp) => inp.addEventListener('input', () => dash.draw('tbl')));
  document.querySelectorAll('.mt-c0').forEach((s) => { s.style.background = dash.colors[0]; });
  document.querySelectorAll('.mt-c1').forEach((s) => { s.style.background = dash.colors[1]; });
  dash.onData(show);
  show();
})();
