(function(){
  const DATA = window.__DASH_DATA__; const draws = {}; const onData = [];
  function res(id){ const d = DATA[id]; if (!d) return {status:'missing', data:[], rows:[], columns:[], meta:[]};
    return {status:'ok', data:d, rows:d, columns: d.length ? Object.keys(d[0]) : [], meta:[], refreshing:false}; }
  function runOne(name){ (draws[name]||[]).forEach(fn => document.querySelectorAll('[data-draw="'+name+'"]').forEach(el => {
      if (el.closest('[hidden]')) return; try { fn(el); } catch(e){ console.error(e); } })); }
  function runAll(){ onData.forEach(f => { try { f(); } catch(e){ console.error(e); } }); Object.keys(draws).forEach(runOne); }
  window.dash = {
    data: res,
    onData: fn => { onData.push(fn); },
    draw: (name, fn) => { if (fn) { (draws[name] = draws[name] || []).push(typeof fn === 'function' ? fn : (el => (fn.update||fn.mount)(el))); } else runOne(name); },
    calc: () => {}, loader: () => {}, params: () => ({}), setParams: () => {}, resetParams: () => {}, refresh: () => {},
    setLink: name => { history.replaceState(null, '', '#' + name); },
    colors: ['#3B6FB6', '#C2793A', '#4E9A6E', '#8A63C9', '#C25B8A', '#5B8FA8', '#A0884F', '#6D6D6D']
  };
  window.__dashRunAll = runAll;
  let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(runAll, 120); });
  new MutationObserver(() => { clearTimeout(t); t = setTimeout(runAll, 0); }).observe(document.documentElement, {attributes:true, subtree:true, attributeFilter:['hidden']});
})();
