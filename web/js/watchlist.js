/**
 * watchlist.js — 自选关注 + 首屏概览仪表盘
 *
 * 收藏存入 localStorage（key: qdii-favs，值为 default_share_code 数组），
 * 跨场外/场内统一。首屏在 main-content 顶部渲染「自选概览」：自选涨跌 + 溢价警报。
 * 依赖 main.js 暴露的 window.STATE / window.renderCategory（普通 script，全局作用域）。
 */
(function () {
  const KEY = 'qdii-favs';

  function getFavs() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (_) {
      return [];
    }
  }

  function saveFavs(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (_) {}
  }

  function isFav(code) {
    return getFavs().includes(String(code));
  }

  function toggleFav(code) {
    code = String(code);
    const list = getFavs();
    const idx = list.indexOf(code);
    if (idx >= 0) list.splice(idx, 1);
    else list.push(code);
    saveFavs(list);
    if (typeof window.renderCategory === 'function') {
      window.renderCategory('offshore');
      window.renderCategory('etf');
    }
    renderWatchlist();
  }

  // 遍历 STATE.data 所有分类，按 default_share_code 找到收藏的 series + 默认份额
  function collectFavs() {
    const state = window.STATE || {};
    const favs = getFavs();
    if (!favs.length || !state.data) return [];
    const result = [];
    for (const cat of ['sp500', 'nasdaq_passive', 'active', 'global_index', 'global_other', 'etf']) {
      const src = state.data[cat];
      if (!src) continue;
      for (const s of (src.series || [])) {
        if (favs.includes(String(s.default_share_code))) {
          const def = (s.shares || []).find(sh => sh.code === s.default_share_code) || (s.shares || [])[0];
          result.push({ series: s, def, isEtf: cat === 'etf', cat });
        }
      }
    }
    return result;
  }

  function pct(v) {
    if (v == null || v === '') return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  function renderWatchlist() {
    const root = document.getElementById('watchlist-dashboard');
    if (!root) return;
    const favs = collectFavs();
    if (!favs.length) {
      root.classList.add('hidden');
      return;
    }
    root.classList.remove('hidden');

    const cards = favs.map(({ series, def, isEtf }) => {
      const chg = isEtf ? (def.etf_change_pct != null ? def.etf_change_pct : def.daily_change) : def.daily_change;
      const premium = isEtf ? pct(def.etf_premium) : null;
      const name = isEtf ? def.name : series.display_name;
      const chgHtml = chg == null
        ? '<span class="text-stone-400">--</span>'
        : `<span class="${chg > 0 ? 'up' : chg < 0 ? 'down' : 'text-stone-400'}">${chg > 0 ? '+' : ''}${chg.toFixed(2)}%</span>`;
      const premiumHtml = premium == null
        ? ''
        : `<span class="text-rose-600 dark:text-rose-400">溢价 ${premium > 0 ? '+' : ''}${premium.toFixed(2)}%</span>`;
      return `<button type="button" class="watch-card" data-code="${def.code}" onclick="event.stopPropagation(); window.toggleFav('${def.code}')" title="点击取消自选">
        <div class="font-medium truncate">${name}</div>
        <div class="text-xs text-stone-500 dark:text-stone-400 truncate">${def.code}</div>
        <div class="text-xs mt-1">${chgHtml}${premiumHtml ? ' · ' + premiumHtml : ''}</div>
      </button>`;
    }).join('');

    const alerts = favs
      .filter(({ isEtf, def }) => isEtf && pct(def.etf_premium) != null && pct(def.etf_premium) > 3)
      .map(({ def }) => `<span class="watch-alert">⚠️ ${def.name} 溢价 ${pct(def.etf_premium).toFixed(2)}%</span>`)
      .join('');

    root.innerHTML = `
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-bold">⭐ 自选概览</h2>
        <span class="text-xs text-stone-400 dark:text-stone-500">点击卡片取消自选 · 共 ${favs.length} 只</span>
      </div>
      ${alerts ? `<div class="flex flex-wrap gap-2 mb-3">${alerts}</div>` : ''}
      <div class="watch-grid">${cards}</div>`;
  }

  window.getFavs = getFavs;
  window.isFav = isFav;
  window.toggleFav = toggleFav;
  window.renderWatchlist = renderWatchlist;
})();
