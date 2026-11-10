(function () {
  const PARTY = { D: '#2E6BD6', R: '#D4403A', I: '#8A63C9' };
  const MUTED = 'var(--cds-chart-muted, #9AA0A6)';
  const MINUS = '−';
  const fPct = d3.format('.0%'), fInt = d3.format(','), f1 = d3.format('.1f'), f2 = d3.format('.2f');
  const fS1 = d3.format('+.1f'), fS2 = d3.format('+.2f'), fSI = d3.format('+d');
  const fDate = d3.utcFormat('%b %-d, %Y');
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
  const lead = (m, pos, neg) => (blank(m) ? '' : Math.abs(m) < 0.05 ? 'Even' : (m > 0 ? pos : neg) + '+' + f1(Math.abs(m)));

  function parseWhere(w) {
    const o = {};
    (w || '').split('&').forEach((p) => { if (!p) return; const i = p.indexOf('='); o[decodeURIComponent(p.slice(0, i))] = decodeURIComponent(p.slice(i + 1)); });
    return o;
  }
  const matches = (r, w) => Object.keys(w).every((k) => String(r[k]) === w[k]);
  function pickRow(rows, el) {
    if (el.dataset.where) { const w = parseWhere(el.dataset.where); return rows.find((r) => matches(r, w)); }
    if (el.dataset.row) return rows[+el.dataset.row];
    return rows[0];
  }
  function note(el, text, cls) {
    const div = document.createElement('div'); div.className = cls; div.textContent = text; el.replaceChildren(div);
  }
  const failNote = (el) => note(el, 'Failed to load', 'mt-fail');
  function tipFor(el) {
    const tip = document.createElement('div'); tip.className = 'mt-tip'; tip.hidden = true; el.appendChild(tip);
    return {
      show(lines, x, y) {
        tip.replaceChildren(...lines.filter((l) => l && (l.text || typeof l === 'string')).map((l, i) => { const d = document.createElement('div'); if (i === 0) d.className = 't'; if (l.color) { const s = document.createElement('span'); s.className = 'mt-sw'; s.style.background = l.color; d.appendChild(s); } d.appendChild(document.createTextNode(l.text || l)); return d; }));
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

  // ---------- tables (filter, search, sort, limit, links)
  dash.draw('tbl', (tbody) => {
    const table = tbody.closest('table');
    const d = dash.data(table.dataset.source);
    if (d.status !== 'ok') { tbody.replaceChildren(); return; }
    const ths = Array.from(table.querySelectorAll('thead th'));
    const cols = ths.map((th) => ({ field: th.dataset.field, fmt: th.dataset.fmt || '', right: th.classList.contains('r'), link: th.dataset.link || '' }));
    let rows = d.data.slice();
    if (table.dataset.where) { const w = parseWhere(table.dataset.where); rows = rows.filter((r) => matches(r, w)); }
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
    if (table.dataset.limit) rows = rows.slice(0, +table.dataset.limit);
    if (!rows.length) {
      const tr = document.createElement('tr'); const td = document.createElement('td');
      td.colSpan = cols.length; td.className = 'mt-none'; td.textContent = q ? 'No matches' : 'None yet';
      tr.appendChild(td); tbody.replaceChildren(tr); return;
    }
    const key = table.dataset.rowKey;
    tbody.replaceChildren(...rows.map((r) => {
      const tr = document.createElement('tr');
      cols.forEach((c) => {
        const td = document.createElement('td');
        if (c.right) td.className = 'r';
        const text = c.field === key ? String(r[c.field] ?? '') : fmt(r[c.field], c.fmt);
        const u = c.link ? String(r[c.link] || '') : '';
        if (u && /^https:\/\//.test(u)) {
          const a = document.createElement('a'); a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = text || 'link'; td.appendChild(a);
        } else td.textContent = text;
        tr.appendChild(td);
      });
      return tr;
    }));
  });

  // ---------- called + leaning seat bar
  dash.draw('seatbar', (el) => {
    const d = dash.data('seatbar');
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const ch = el.dataset.chamber;
    const segs = d.data.filter((r) => r.chamber === ch).sort((a, b) => a.order - b.order);
    if (!segs.length) { el.replaceChildren(); return; }
    const total = +segs[0].total;
    const { svg, W } = svgFor(el, 70);
    const top = 22, bh = 28;
    const x = d3.scaleLinear([0, total], [0, W]);
    let acc = 0;
    const parts = segs.map((s) => { const p = { ...s, seats: +s.seats, x0: acc, x1: acc + +s.seats }; acc += +s.seats; return p; }).filter((p) => p.seats > 0);
    const fill = (p) => (p.kind === 'tossup' ? MUTED : PARTY[p.party] || MUTED);
    const rects = svg.append('g').selectAll('rect').data(parts).join('rect')
      .attr('x', (p) => x(p.x0)).attr('width', (p) => Math.max(0.5, x(p.x1) - x(p.x0) - 1))
      .attr('y', top).attr('height', bh).attr('fill', fill).attr('fill-opacity', (p) => (p.kind === 'lean' ? 0.4 : 1));
    const labelled = parts.filter((p) => x(p.x1) - x(p.x0) >= measure(svg, [fInt(p.seats)], 12) + 8);
    svg.append('g').selectAll('text').data(labelled).join('text')
      .attr('x', (p) => (x(p.x0) + x(p.x1)) / 2).attr('y', top + bh / 2).attr('dy', '0.35em').attr('text-anchor', 'middle')
      .attr('fill', (p) => (p.kind === 'won' ? '#fff' : 'var(--color-fg)')).attr('pointer-events', 'none')
      .style('font-size', 'var(--cds-font-size-caption)').style('font-variant-numeric', 'tabular-nums').text((p) => fInt(p.seats));
    const mid = x(total / 2);
    svg.append('line').attr('x1', mid).attr('x2', mid).attr('y1', top - 5).attr('y2', top + bh + 5)
      .attr('stroke', 'var(--color-fg)').attr('stroke-width', 1.5).attr('stroke-dasharray', '3 2');
    svg.append('text').attr('x', mid).attr('y', top - 9).attr('text-anchor', 'middle').attr('fill', 'var(--color-fg-muted)')
      .style('font-size', 'var(--cds-font-size-caption)').text('Majority');
    const tip = tipFor(el);
    const unit = ch === 'governors' ? ' governorships' : ' seats';
    rects.on('pointermove', (event, p) => {
      const [px, py] = pointer(event, el);
      rects.attr('opacity', (o) => (o === p ? 1 : 0.6));
      tip.show([{ text: p.label }, { color: p.kind === 'tossup' ? MUTED : PARTY[p.party], text: fInt(p.seats) + unit }], px, py);
    }).on('pointerleave', () => { rects.attr('opacity', 1); tip.hide(); });
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
    const color = (s) => (s >= thr ? PARTY.D : (ch === 'governors' && s === thr - 1 ? MUTED : PARTY.R));
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

  // ---------- open races: margin with 80% range
  dash.draw('dots', (el) => {
    const d = dash.data(el.dataset.source);
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const rows = d.data.filter((r) => !blank(r.margin) && (!String(r.rating_now).startsWith('Safe') || r.favored !== r.holder)).sort((a, b) => b.margin - a.margin);
    if (!rows.length) { note(el, 'No competitive races left uncalled', 'mt-empty'); return; }
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
        const fav = r.p_win >= 0.5;
        const who = fav ? r.dem : r.rep;
        const p = fav ? r.p_win : 1 - r.p_win, p0 = fav ? r.p_pre : 1 - r.p_pre;
        tip.show([{ text: r.race + ', not called' }, { text: r.dem + ' vs ' + r.rep },
          { color: col(r), text: 'Margin now ' + lead(r.margin, r.chal, 'R') + ' (80%: ' + lead(r.margin_lo, r.chal, 'R') + ' to ' + lead(r.margin_hi, r.chal, 'R') + ')' },
          { text: 'Win chance: ' + who + ' ' + fPct(p) + ', forecast ' + fPct(p0) },
          { text: blank(r.poll_avg) ? 'No polls' : 'Poll average ' + lead(r.poll_avg, r.chal, 'R') + ' across ' + fInt(r.polls) + ' polls' }], px, py);
      })
      .on('pointerleave', () => tip.hide());
  });

  // ---------- House win-probability ladder
  dash.draw('ladder', (el) => {
    const d = dash.data('house_races');
    if (d.status === 'error') { failNote(el); return; }
    if (d.status !== 'ok') { el.replaceChildren(); return; }
    const rows = d.data.slice().sort((a, b) => b.p_win - a.p_win || String(a.district).localeCompare(String(b.district)));
    const { svg, W, H } = svgFor(el, 220);
    const m = { t: 10, r: 8, b: 10, l: measure(svg, ['100%'], 12) + 10 };
    const x = d3.scaleBand(rows.map((r) => r.district), [m.l, W - m.r]).paddingInner(0.2);
    const y = d3.scaleLinear([0, 1], [H - m.b, m.t]);
    const gy = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).tickValues([0, 0.25, 0.5, 0.75, 1]).tickFormat(d3.format('.0%')).tickSize(-(W - m.l - m.r)));
    styleAxis(gy); gy.select('.domain').remove();
    const col = (r) => (r.p_win >= 0.5 ? PARTY[r.pos] || PARTY.D : PARTY[r.neg] || PARTY.R);
    const op = (r) => (r.status === 'Called' ? 1 : 0.5);
    const bars = svg.append('g').selectAll('rect').data(rows).join('rect').attr('x', (r) => x(r.district)).attr('width', x.bandwidth())
      .attr('y', (r) => y(Math.max(0.5, r.p_win))).attr('height', (r) => Math.abs(y(r.p_win) - y(0.5)))
      .attr('rx', Math.min(2, x.bandwidth() / 2)).attr('fill', col).attr('fill-opacity', op);
    svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0.5)).attr('y2', y(0.5)).attr('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
    const tip = tipFor(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('pointermove', (event) => {
        const [px, py] = pointer(event, el);
        const i = Math.max(0, Math.min(rows.length - 1, Math.floor((px - m.l) / x.step()))); const r = rows[i];
        bars.attr('opacity', (b) => (b.district === r.district ? 1 : 0.5));
        const status = r.status === 'Called'
          ? { color: col(r), text: 'Called for ' + r.winner + ' by ' + r.called_by }
          : { color: col(r), text: 'Not called. Margin now ' + lead(r.margin, 'D', r.neg) + ', D win chance ' + fPct(r.p_win) + ' (forecast ' + fPct(r.p_pre) + ')' };
        tip.show([{ text: r.district + ' · ' + r.pvi + ' · held by ' + r.holder }, status, { text: 'Cook ' + r.cook + ', Sabato ' + r.sabato + ', IE ' + r.ie }], px, py);
      })
      .on('pointerleave', () => { bars.attr('opacity', 1); tip.hide(); });
  });

  // ---------- sources list
  dash.draw('srcs', (ul) => {
    const d = dash.data('sources');
    if (d.status !== 'ok') { ul.replaceChildren(); return; }
    ul.replaceChildren(...d.data.map((r) => {
      const li = document.createElement('li');
      if (/^https:\/\//.test(String(r.url))) {
        const a = document.createElement('a'); a.href = r.url; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = r.title; li.appendChild(a);
      } else li.appendChild(document.createTextNode(r.title));
      li.appendChild(document.createTextNode(': ' + r.used_for)); return li;
    }));
  });

  // ---------- controls: tabs, sorting, search
  const TABS = ['overview', 'senate', 'governors', 'house', 'calls', 'method'];
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
  dash.onData(show);
  show();
})();
