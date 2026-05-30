# 我的投资 Dashboard

个人投资追踪看板：把 Excel 里的投资数据，自动变成一个网页仪表板，
随时随地用手机/电脑打开就能看资产总览。整合 M+（马股）、MooMoo、Tiger 三个平台。

🌐 **网址**：https://investment-dashboard-2ad.pages.dev

---

## 系统架构

```
投资记录.xlsx（主数据，永远不动原档）
      ↓
export_data.py（读 Excel + 自动抓 USD→MYR 汇率 → 写 data.json）
      ↓
git push（由 Claude 执行）
      ↓
Cloudflare（连接 GitHub 仓库，push 后约 1~2 分钟自动更新）
      ↓
https://investment-dashboard-2ad.pages.dev
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `export_data.py` | 从 `投资记录.xlsx` 读取数据、抓汇率，生成 `data.json` |
| `data.json` | 网页的数据源（脚本自动产生，不用手改） |
| `index.html` | 网页页面（深色主题，手机也能看） |
| `dashboard.js` | 网页逻辑：填数字、画资产走势图（用 Chart.js）|

数据来自桌面的 `投资记录.xlsx`，用到两个工作表：`美股投资账户`（Tiger + MooMoo）、`马股投资账户`（M+）。

## 怎么更新数据（三步）

1. 更新桌面的 `投资记录.xlsx`
2. 运行脚本：`python3 export_data.py`
3. 推送上线：`git add -A && git commit -m "更新数据" && git push origin main`
   → 约 1~2 分钟后网站自动更新

---

## 数据来源与规则（设计要点）

| 平台 | 总资产来源 | 盈亏来源 | 货币 |
|------|-----------|---------|------|
| M+ | 孚展市值 + 现金账户总值 | 持仓盈亏 | MYR |
| MooMoo | 截图顶部资产净值 | 收益日历当月金额 | USD |
| Tiger | 截图顶部总资产 | 盈亏日历各月金额（截图）| USD |

**几个关键规则：**
- **所有数据均由截图分析后输入**：Tiger 各月盈亏直接从盈亏日历截图读取（无需反推）
- **M+ 股息分两类**：现金账户股息已提走（进个人银行，单独显示）；Margin 账户股息留在账户内（已含于总资产，单独标注）
- **M+ Margin 现金**每日重置，需在重置后才截图，否则数字不准
- **汇率**：脚本自动从 api.frankfurter.app 抓 USD→MYR（免费、免注册）

## 注意事项

- ⚠️ 本地直接双击打开 `index.html`（file:// 开头）会显示「数据加载失败」，
  这是浏览器安全限制，**请用上面的网址**看。
- 🔒 原始 Excel（`*.xlsx`）和密钥（`.env`）已设为不上传 GitHub。

---

## 这个网站是怎么盖的（历史记录）

按「先设计 → 再施工」的方式，分 7 步完成（2026-05-30）：

1. Excel 加 M+ 汇总区 + 建 GitHub 仓库
2~4. 写 `export_data.py`（美股 → 马股+汇率 → 组装 data.json）
5. 写 `index.html`（版面 + 深色主题）
6. 写 `dashboard.js`（填数据、画图表）
7. 本地测试 → 推送 → Cloudflare 上线 → 手机验证

> 📁 当初的完整设计书和施工书存放在 `桌面\股票\docs\superpowers\`（specs / plans 两个文件夹），网站已建好，那两份主要作历史存档。

## 不在范围内

- 密码保护（个人使用，不需要）
- 自动定时更新（手动触发）
- M+ 月度盈亏自动计算（数据不完整，只显示快照）
- USD/MYR 统一换算成单一货币（两种货币分开显示）
