function fmt(num, decimals = 2) {
  if (num === null || num === undefined) return "—";
  return num.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function colorClass(num) {
  if (num === null || num === undefined) return "";
  return num >= 0 ? "up" : "down";
}

function pnlText(num, currency = "") {
  if (num === null || num === undefined) return "—";
  const sign = num >= 0 ? "▲ +" : "▼ ";
  return `${sign}${currency}${fmt(Math.abs(num))}`;
}

function setText(id, text, cls = "") {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  if (cls) el.className = cls;
}

async function loadDashboard() {
  let d;
  try {
    const res = await fetch("data.json");
    d = await res.json();
  } catch (e) {
    document.getElementById("updated-date").textContent = "⚠️ 数据加载失败，请检查 data.json";
    console.error("loadDashboard error:", e);
    return;
  }

  // Header
  setText("updated-date", `更新：${d.updated}`);

  // Exchange rate
  const fx = d.exchange_rate;
  const fxText = fx.usd_to_myr
    ? `汇率参考：1 USD = RM ${fmt(fx.usd_to_myr, 4)}（${fx.fetched_at} 自动更新）`
    : "汇率：无法获取";
  setText("fx-note", fxText);

  // Total assets — combined MYR (US stocks converted + M+)
  const usdInMyr = fx.usd_to_myr ? d.us_stocks.total_usd * fx.usd_to_myr : 0;
  const combinedMyr = usdInMyr + (d.mplus.total_myr || 0);
  setText("total-combined-myr", `RM ${fmt(combinedMyr)}`);
  setText("total-usd-note", `（美股 $${fmt(d.us_stocks.total_usd)} × ${fmt(fx.usd_to_myr, 4)} + 马股 RM ${fmt(d.mplus.total_myr)}）`);

  // Historical cumulative P&L in MYR
  const usPnlUsd = (d.totals_usd.moomoo_all_time || 0) + (d.totals_usd.tiger_all_time || 0);
  const usPnlMyr = fx.usd_to_myr ? usPnlUsd * fx.usd_to_myr : null;
  const mplusPnl = d.mplus.all_time_pnl_myr || 0;
  if (usPnlMyr !== null) {
    const totalPnl = usPnlMyr + mplusPnl;
    const el = document.getElementById("total-alltime-pnl");
    el.textContent = `${totalPnl >= 0 ? "▲ +" : "▼ "}RM ${fmt(Math.abs(totalPnl))}`;
    el.className = totalPnl >= 0 ? "up" : "down";
    setText("total-alltime-note", `（美股 $${fmt(usPnlUsd)} × ${fmt(fx.usd_to_myr, 4)} + 马股 RM ${fmt(mplusPnl)}）`);
  }

  // M+ card
  setText("mplus-total", `RM ${fmt(d.mplus.total_myr)}`);
  setText("mplus-equity", d.mplus.equity_myr != null ? `RM ${fmt(d.mplus.equity_myr)}` : "—");
  setText("mplus-cash",   d.mplus.cash_myr   != null ? `RM ${fmt(d.mplus.cash_myr)} （含 Margin 100k）` : "—");
  setText("mplus-alltime", pnlText(d.mplus.all_time_pnl_myr, "RM "), colorClass(d.mplus.all_time_pnl_myr));
  setText("mplus-div-cash", `RM ${fmt(d.mplus.dividends_cash_myr)}`);
  setText("mplus-div-margin", `RM ${fmt(d.mplus.dividends_margin_myr)}`);

  // MooMoo card
  setText("moomoo-total", `$${fmt(d.us_stocks.moomoo_total_usd)}`);
  const latestMonth = d.monthly_usd[d.monthly_usd.length - 1];
  setText("moomoo-monthly", pnlText(latestMonth?.moomoo, "$"), colorClass(latestMonth?.moomoo));
  setText("moomoo-alltime", pnlText(d.totals_usd.moomoo_all_time, "$"), colorClass(d.totals_usd.moomoo_all_time));
  setText("moomoo-equity", d.us_stocks.moomoo_equity_usd != null ? `$${fmt(d.us_stocks.moomoo_equity_usd)}` : "—");
  setText("moomoo-cash",   d.us_stocks.moomoo_cash_usd   != null ? `$${fmt(d.us_stocks.moomoo_cash_usd)}`   : "—");

  // Tiger card
  setText("tiger-total", `$${fmt(d.us_stocks.tiger_total_usd)}`);
  setText("tiger-monthly", pnlText(latestMonth?.tiger, "$"), colorClass(latestMonth?.tiger));
  setText("tiger-alltime", pnlText(d.totals_usd.tiger_all_time, "$"), colorClass(d.totals_usd.tiger_all_time));
  setText("tiger-equity", d.us_stocks.tiger_equity_usd != null ? `$${fmt(d.us_stocks.tiger_equity_usd)}` : "—");
  setText("tiger-cash",   d.us_stocks.tiger_cash_usd   != null ? `$${fmt(d.us_stocks.tiger_cash_usd)}`   : "—");

  // USD Chart — last 24 months with data
  const recentMonths = d.monthly_usd.slice(-24).filter(m => m.tiger !== null || m.moomoo !== null);
  const usdLabels = recentMonths.map(m => m.month);
  new Chart(document.getElementById("chart-usd"), {
    type: "line",
    data: {
      labels: usdLabels,
      datasets: [
        { label: "MooMoo", data: recentMonths.map(m => m.moomoo), borderColor: "#00d4aa", backgroundColor: "transparent", tension: 0.3, spanGaps: true, pointRadius: 3 },
        { label: "Tiger",  data: recentMonths.map(m => m.tiger),  borderColor: "#4a9eff", backgroundColor: "transparent", tension: 0.3, spanGaps: true, pointRadius: 3 },
        { label: "合计",   data: recentMonths.map(m => m.total),  borderColor: "#f0c040", backgroundColor: "transparent", tension: 0.3, spanGaps: true, pointRadius: 3, borderDash: [4, 3] },
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#8aabcc", font: { size: 11 } } } },
      scales: {
        x: { ticks: { color: "#6b8aad", font: { size: 10 }, maxTicksLimit: 8 }, grid: { color: "#1f2f42" } },
        y: { ticks: { color: "#6b8aad", font: { size: 10 } }, grid: { color: "#1f2f42" } }
      }
    }
  });

  // MYR Chart — M+ asset snapshots
  const snaps = d.mplus_snapshots;
  new Chart(document.getElementById("chart-myr"), {
    type: "line",
    data: {
      labels: snaps.map(s => s.date),
      datasets: [{
        label: "M+ 总资产",
        data: snaps.map(s => s.total_myr),
        borderColor: "#b06aff",
        backgroundColor: "rgba(176,106,255,0.08)",
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#8aabcc", font: { size: 11 } } } },
      scales: {
        x: { ticks: { color: "#6b8aad", font: { size: 10 }, maxTicksLimit: 8 }, grid: { color: "#1f2f42" } },
        y: { ticks: { color: "#6b8aad", font: { size: 10 } }, grid: { color: "#1f2f42" } }
      }
    }
  });

  // Monthly Table — last 24 months, newest first
  const tableRows = [...d.monthly_usd].reverse().slice(0, 24);
  const tbody = document.getElementById("monthly-table-body");
  tbody.innerHTML = tableRows.map(m => {
    const moomoo = m.moomoo !== null ? `<span class="${colorClass(m.moomoo)}">${pnlText(m.moomoo, "$")}</span>` : "—";
    const tiger  = m.tiger  !== null ? `<span class="${colorClass(m.tiger)}">${pnlText(m.tiger, "$")}</span>`  : "—";
    const total  = m.total  !== null ? `<span class="${colorClass(m.total)}">${pnlText(m.total, "$")}</span>`  : "—";
    return `<tr><td>${m.month}</td><td>${moomoo}</td><td>${tiger}</td><td>${total}</td></tr>`;
  }).join("");
}

loadDashboard();
