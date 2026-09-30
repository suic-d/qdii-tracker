/**
 * holdings-perspective.js — 跨基金重仓股透视
 *
 * 汇总所有已抓取的 holdings/{code}.json，按股票合计权重 / 出现次数，
 * 找出全市场 QDII 主动基金共同重仓的股票（横向视角，补单只基金持仓的纵向视角）。
 * 纯前端：点击「重仓透视」时拉取 data/holdings/*.json，不依赖后端。
 */
(function () {
  const MODAL_ID = 'holdings-perspective-modal';

  function fundNameByCode() {
    const state = window.STATE || {};
    const map = {};
    if (!state.data) return map;
    for (const cat of Object.keys(state.data)) {
      for (const s of (state.data[cat].series || [])) {
        for (const sh of (s.shares || [])) {
          if (sh.code) map[String(sh.code)] = s.display_name || sh.name || sh.code;
        }
      }
    }
    return map;
  }

  async function collectHoldings() {
    const state = window.STATE || {};
    // 优先用 pipeline 生成的持仓索引，避免对不存在的文件发请求（批量 404）
    let codes = [];
    try {
      const idx = await (await fetch('./data/holdings-index.json?t=' + Date.now())).json();
      codes = (idx.codes || []).map(String);
    } catch (_) {
      for (const cat of ['active', 'global_other', 'global_index']) {
        const src = state.data && state.data[cat];
        if (!src) continue;
        for (const s of (src.series || [])) {
          for (const sh of (s.shares || [])) {
            if (sh.code) codes.push(String(sh.code));
          }
        }
      }
    }
    const results = [];
    await Promise.all(codes.map(async (code) => {
      try {
        const r = await fetch(`./data/holdings/${code}.json`);
        if (!r.ok) return;
        const d = await r.json();
        results.push({ code, holdings: d.holdings || [] });
      } catch (_) { /* 无持仓文件则跳过 */ }
    }));
    return results;
  }

  function aggregate(results, nameMap) {
    const agg = new Map();
    for (const r of results) {
      const fundName = nameMap[r.code] || r.code;
      for (const h of r.holdings) {
        const key = `${h.stock_code || ''}|${h.stock_name || ''}`;
        if (!key.trim()) continue;
        const stockName = h.stock_name || h.stock_code || '';
        const entry = agg.get(key) || { stock_name: stockName, stock_code: h.stock_code || '', funds: [], total_weight: 0 };
        entry.funds.push(fundName);
        entry.total_weight += Number(h.weight) || 0;
        agg.set(key, entry);
      }
    }
    return [...agg.values()]
      .map(e => ({ ...e, count: e.funds.length, avg_weight: e.total_weight / e.funds.length }))
      .sort((a, b) => b.total_weight - a.total_weight);
  }

  function render(rows, totalFunds) {
    const existing = document.getElementById(MODAL_ID);
    if (existing) existing.remove();
    const modal = document.createElement('div');
    modal.id = MODAL_ID;
    modal.className = 'hp-overlay';
    modal.innerHTML = `
      <div class="hp-panel" role="dialog" aria-modal="true" aria-label="跨基金重仓股透视">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-base font-bold">🧺 跨基金重仓股透视</h2>
          <button type="button" class="hp-close" aria-label="关闭" onclick="document.getElementById('${MODAL_ID}').remove()">✕</button>
        </div>
        <p class="text-xs text-stone-500 dark:text-stone-400 mb-3">共汇总 ${totalFunds} 只基金的 Top10 持仓，按「合计权重」降序。</p>
        <div class="hp-scroll">
          <table class="w-full text-xs">
            <thead class="text-stone-500 dark:text-stone-400 text-left">
              <tr>
                <th class="py-2 pr-3 font-medium">股票</th>
                <th class="py-2 pr-3 font-medium text-right">出现次数</th>
                <th class="py-2 pr-3 font-medium text-right">合计权重</th>
                <th class="py-2 pr-3 font-medium text-right">平均权重</th>
                <th class="py-2 font-medium">持有基金（部分）</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100 dark:divide-stone-700/50">
              ${rows.slice(0, 40).map(r => `
                <tr>
                  <td class="py-2 pr-3 font-medium">${r.stock_name}<div class="text-[10px] text-stone-400">${r.stock_code || ''}</div></td>
                  <td class="py-2 pr-3 text-right num">${r.count}</td>
                  <td class="py-2 pr-3 text-right num">${r.total_weight.toFixed(1)}%</td>
                  <td class="py-2 pr-3 text-right num">${r.avg_weight.toFixed(1)}%</td>
                  <td class="py-2 text-stone-500 dark:text-stone-400">${r.funds.slice(0, 3).join('、')}${r.funds.length > 3 ? ` 等 ${r.funds.length} 只` : ''}</td>
                </tr>
              `).join('') || '<tr><td colspan="5" class="py-6 text-center text-stone-400">暂无持仓数据</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>`;
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
    document.body.appendChild(modal);
  }

  async function open() {
    const nameMap = fundNameByCode();
    const results = await collectHoldings();
    const rows = aggregate(results, nameMap);
    render(rows, results.length);
  }

  window.openHoldingsPerspective = open;

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('holdings-perspective-btn');
    if (btn) btn.addEventListener('click', open);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const m = document.getElementById(MODAL_ID);
      if (m) m.remove();
    }
  });
})();
