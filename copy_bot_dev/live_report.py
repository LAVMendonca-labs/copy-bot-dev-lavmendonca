from __future__ import annotations


def render_live_html(host: str, port: int) -> str:
    base_url = f"http://{host}:{port}"
    template = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Copy Bot Live</title>
  <style>
    :root {{
      --bg: #071411;
      --panel: #0d1f1a;
      --panel-2: #10261f;
      --line: rgba(130, 180, 150, 0.15);
      --ink: #eef8f2;
      --muted: #9db8ab;
      --accent: #2be17d;
      --accent-2: #1fb968;
      --danger: #ef5b5b;
      --warn: #f0b24b;
      --shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top right, rgba(43, 225, 125, 0.12), transparent 25%),
        linear-gradient(180deg, #071411, #08110f 52%, #050907);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", sans-serif;
    }}
    .page {{
      width: min(1380px, calc(100% - 28px));
      margin: 24px auto 48px;
    }}
    .panel {{
      background: linear-gradient(180deg, rgba(16,38,31,0.96), rgba(10,24,20,0.94));
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .hero-main {{ padding: 26px 28px; }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 4vw, 3.2rem);
      letter-spacing: -0.05em;
      line-height: 0.92;
      font-family: "Bahnschrift", "Aptos Display", sans-serif;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
      max-width: 62ch;
    }}
    .hero-side {{
      padding: 22px;
      display: grid;
      gap: 12px;
      align-content: start;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(43, 225, 125, 0.12);
      color: var(--accent);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      font-weight: 700;
    }}
    .pill.bad {{ background: rgba(239, 91, 91, 0.14); color: var(--danger); }}
    .pill.alt {{ background: rgba(255,255,255,0.06); color: var(--ink); }}
    .hero-line {{ color: var(--muted); font-size: 0.92rem; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
      margin-bottom: 18px;
    }}
    .stat {{
      padding: 18px;
      border-radius: 18px;
      background: rgba(255,255,255,0.03);
      border: 1px solid var(--line);
    }}
    .label {{
      display: block;
      color: var(--muted);
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 1.45rem;
      font-weight: 700;
    }}
    .good {{ color: var(--accent); }}
    .bad {{ color: var(--danger); }}
    .warn {{ color: var(--warn); }}
    .section {{
      padding: 22px;
      margin-bottom: 18px;
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 14px;
    }}
    h2 {{
      margin: 0;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
    }}
    .btn {{
      height: 42px;
      border: 0;
      border-radius: 14px;
      padding: 0 16px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: #04120c;
    }}
    .btn.alt {{ background: rgba(255,255,255,0.08); color: var(--ink); }}
    .btn.bad {{ background: rgba(239, 91, 91, 0.16); color: #ffb9b9; }}
    .btn.small {{ height: 34px; padding: 0 12px; border-radius: 12px; font-size: 0.88rem; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.93rem; }}
    th, td {{
      padding: 11px 8px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .sort-head {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 0;
      padding: 0;
      background: transparent;
      color: inherit;
      font: inherit;
      text-transform: inherit;
      letter-spacing: inherit;
      cursor: pointer;
    }}
    .sort-head:hover {{
      color: var(--ink);
    }}
    .sort-arrow {{
      min-width: 16px;
      color: var(--accent);
      font-size: 0.82rem;
      letter-spacing: 0;
      text-transform: none;
    }}
    .mono {{ font-family: "Cascadia Code", "Consolas", monospace; }}
    .muted {{ color: var(--muted); }}
    .copy-row {{ cursor: pointer; }}
    .copy-row.selected {{ background: rgba(43, 225, 125, 0.07); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
    }}
    .tabs {{
      display: inline-flex;
      gap: 8px;
      padding: 4px;
      border-radius: 999px;
      background: rgba(255,255,255,0.04);
    }}
    .tab {{
      height: 34px;
      border-radius: 999px;
      border: 0;
      padding: 0 14px;
      font: inherit;
      cursor: pointer;
      color: var(--muted);
      background: transparent;
    }}
    .tab.active {{
      background: rgba(43, 225, 125, 0.15);
      color: var(--ink);
      font-weight: 700;
    }}
    .detail-empty {{
      padding: 28px 8px 6px;
      color: var(--muted);
      line-height: 1.6;
    }}
    .detail-toolbar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 14px;
    }}
    .inline-control {{
      display: grid;
      gap: 6px;
      min-width: 190px;
    }}
    .inline-control label {{
      color: var(--muted);
      font-size: 0.8rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .inline-control input,
    .inline-control select {{
      min-height: 40px;
      border-radius: 12px;
      background: rgba(255,255,255,0.04);
    }}
    .inline-control select {{
      color: var(--ink);
      background-color: rgba(13, 31, 26, 0.98);
    }}
    .inline-control select option {{
      color: var(--ink);
      background: #0d1f1a;
    }}
    .toolbar-meta {{
      margin-left: auto;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .modal {{
      position: fixed;
      inset: 0;
      display: none;
      place-items: center;
      background: rgba(2, 8, 6, 0.72);
      padding: 16px;
      z-index: 30;
    }}
    .modal.open {{ display: grid; }}
    .modal-card {{
      width: min(840px, 100%);
      max-height: calc(100vh - 24px);
      overflow: auto;
      padding: 24px;
      border-radius: 26px;
      background: linear-gradient(180deg, rgba(16,38,31,0.99), rgba(9,20,17,0.99));
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}
    .modal-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 18px;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}
    .field {{ display: grid; gap: 7px; }}
    .field.full {{ grid-column: 1 / -1; }}
    .field label {{
      color: var(--muted);
      font-size: 0.9rem;
    }}
    input, select {{
      width: 100%;
      min-height: 46px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.04);
      color: var(--ink);
      padding: 0 14px;
      font: inherit;
    }}
    .quick-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .quick-btn {{
      height: 34px;
      padding: 0 12px;
      border-radius: 999px;
      border: 1px solid rgba(43,225,125,0.18);
      background: rgba(43,225,125,0.08);
      color: var(--ink);
      cursor: pointer;
    }}
    .range-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .modal-actions {{
      display: flex;
      gap: 10px;
      justify-content: flex-start;
      margin-top: 18px;
    }}
    @media (max-width: 1100px) {{
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      .hero, .grid-2 {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 720px) {{
      .stats {{ grid-template-columns: 1fr; }}
      .form-grid, .range-row {{ grid-template-columns: 1fr; }}
      .page {{ width: min(100% - 18px, 100%); }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="panel hero-main">
        <h1>Copy Bot<br>Paper Live</h1>
        <p class="sub">Painel local para testar copy trade de qualquer wallet pública da Polymarket com dinheiro fictício. O motor acompanha a atividade da wallet, aplica <strong>slippage</strong>, <strong>price range</strong>, <strong>max total</strong> e <strong>max per market</strong>, e atualiza em tempo real.</p>
      </div>
      <div class="panel hero-side">
        <div class="pill" id="status-pill">Conectando</div>
        <div class="hero-line">Painel: <a href="__BASE_URL__" target="_blank" rel="noreferrer">__BASE_URL__</a></div>
        <div class="hero-line">Estado JSON: <a href="__BASE_URL__/api/state" target="_blank" rel="noreferrer">__BASE_URL__/api/state</a></div>
        <div class="hero-line">Última atualização: <span id="last-update">-</span></div>
        <div class="hero-line">Último erro global: <span id="last-error">nenhum</span></div>
      </div>
    </section>

    <section class="stats">
      <div class="panel stat"><span class="label">Copies</span><span class="value" id="copies-total">0</span></div>
      <div class="panel stat"><span class="label">Ativos</span><span class="value" id="copies-active">0</span></div>
      <div class="panel stat"><span class="label">Banca Total</span><span class="value" id="total-bankroll">$0.00</span></div>
      <div class="panel stat"><span class="label">Equity Total</span><span class="value" id="total-equity">$0.00</span></div>
      <div class="panel stat"><span class="label">PnL Total</span><span class="value" id="total-pnl">$0.00</span></div>
    </section>

    <section class="panel section">
      <div class="section-head">
        <h2>All Copy Trades</h2>
        <button class="btn" id="new-copy-button">+ New copy</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Wallet</th>
              <th>Mode</th>
              <th>Config</th>
              <th>Slippage</th>
              <th>Volume</th>
              <th>Signals</th>
              <th>PNL</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="copies-body"></tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <section class="panel section">
        <div class="section-head">
          <div>
            <h2 id="detail-title">Detalhes do copy</h2>
            <div class="muted" id="detail-subtitle">Selecione um copy para ver posições e eventos.</div>
          </div>
          <div class="tabs">
            <button class="tab active" data-tab="history">History</button>
            <button class="tab" data-tab="positions">Positions</button>
            <button class="tab" data-tab="events">Source events</button>
          </div>
        </div>
        <div id="detail-content"></div>
      </section>

      <section class="panel section">
        <h2>Resumo do copy</h2>
        <div id="copy-summary" class="detail-empty">Nenhum copy selecionado.</div>
      </section>
    </section>
  </div>

  <div class="modal" id="copy-modal">
    <div class="modal-card">
      <div class="modal-head">
        <h2 id="modal-title">New copy</h2>
        <button class="btn alt" id="close-modal-button">Close</button>
      </div>
      <form id="copy-form">
        <input type="hidden" id="copy-id">
        <div class="form-grid">
          <div class="field full">
            <label for="copy-name">Copy name</label>
            <input id="copy-name" required placeholder="Ex: Railbird weather">
          </div>
          <div class="field full">
            <label for="wallet-to-follow">Wallet to follow</label>
            <input id="wallet-to-follow" required placeholder="0x...">
          </div>
          <div class="field">
            <label for="mode">Mode</label>
            <select id="mode">
              <option value="fixed_usdc">Fixed USDC</option>
              <option value="mirror_source_percent">Mirror source %</option>
            </select>
          </div>
          <div class="field" id="fixed-amount-field">
            <label for="fixed-amount-usdc">Fixed amount (USDC)</label>
            <div class="quick-row">
              <button type="button" class="quick-btn" data-fixed="10">$10</button>
              <button type="button" class="quick-btn" data-fixed="20">$20</button>
              <button type="button" class="quick-btn" data-fixed="50">$50</button>
              <button type="button" class="quick-btn" data-fixed="100">$100</button>
            </div>
            <input id="fixed-amount-usdc" type="number" min="0.1" step="0.1" value="10">
          </div>
          <div class="field" id="mirror-percent-field" style="display:none;">
            <label for="mirror-source-percent">Mirror source %</label>
            <input id="mirror-source-percent" type="number" min="1" step="1" value="100">
          </div>
          <div class="field">
            <label for="slippage-pct">Slippage (%)</label>
            <input id="slippage-pct" type="number" min="0" step="0.1" value="3">
          </div>
          <div class="field">
            <label>Price range (cents)</label>
            <div class="range-row">
              <input id="price-min-cents" type="number" min="0" max="100" step="1" value="0">
              <input id="price-max-cents" type="number" min="0" max="100" step="1" value="100">
            </div>
          </div>
          <div class="field">
            <label for="max-total-usdc">Max total (USDC)</label>
            <input id="max-total-usdc" type="number" min="1" step="1" value="100">
          </div>
          <div class="field">
            <label for="max-per-market-usdc">Max per market (USDC)</label>
            <input id="max-per-market-usdc" type="number" min="1" step="1" value="10">
          </div>
          <div class="field">
            <label for="bankroll-usdc">Bankroll (USDC)</label>
            <input id="bankroll-usdc" type="number" min="1" step="1" value="100">
          </div>
          <div class="field">
            <label for="min-trade-usdc">Min trade (USDC)</label>
            <input id="min-trade-usdc" type="number" min="0.1" step="0.1" value="1">
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn" type="submit" id="save-copy-button">Add</button>
          <button class="btn alt" type="button" id="cancel-copy-button">Cancel</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    const fmtMoney = (value) => `$${Number(value || 0).toFixed(2)}`;
    const fmtNum = (value) => Number(value || 0).toFixed(3);
    let appState = null;
    let selectedCopyId = null;
    let activeTab = "history";
    let positionsQuery = "";
    let positionsSort = "value_desc";

    const byId = (id) => document.getElementById(id);

    function sortDirectionFor(key) {{
      if (!positionsSort.startsWith(`${{key}}_`)) {{
        return key === "alpha" ? "asc" : "desc";
      }}
      return positionsSort.endsWith("_asc") ? "asc" : "desc";
    }}

    function sortIndicator(key) {{
      if (!positionsSort.startsWith(`${{key}}_`)) {{
        return "↑↓";
      }}
      return sortDirectionFor(key) === "asc" ? "↑" : "↓";
    }}

    function setMetric(id, value, cssClass = "") {{
      const node = byId(id);
      node.textContent = value;
      node.className = `value ${cssClass}`.trim();
    }}

    function openModal(copy = null) {{
      byId("copy-modal").classList.add("open");
      byId("modal-title").textContent = copy ? "Edit copy" : "New copy";
      byId("save-copy-button").textContent = copy ? "Save" : "Add";
      byId("copy-id").value = copy?.copy_id || "";
      byId("copy-name").value = copy?.copy_name || "";
      byId("wallet-to-follow").value = copy?.wallet_to_follow || "";
      byId("mode").value = copy?.mode || "fixed_usdc";
      byId("fixed-amount-usdc").value = copy?.fixed_amount_usdc ?? 10;
      byId("mirror-source-percent").value = copy?.mirror_source_percent ?? 100;
      byId("slippage-pct").value = copy?.slippage_pct ?? 3;
      byId("price-min-cents").value = copy?.price_range?.[0] ?? 0;
      byId("price-max-cents").value = copy?.price_range?.[1] ?? 100;
      byId("max-total-usdc").value = copy?.max_total_usdc ?? 100;
      byId("max-per-market-usdc").value = copy?.max_per_market_usdc ?? 10;
      byId("bankroll-usdc").value = copy?.bankroll_usdc ?? 100;
      byId("min-trade-usdc").value = copy?.min_trade_usdc ?? 1;
      syncModeFields();
    }}

    function closeModal() {{
      byId("copy-modal").classList.remove("open");
    }}

    function syncModeFields() {{
      const isFixed = byId("mode").value === "fixed_usdc";
      byId("fixed-amount-field").style.display = isFixed ? "grid" : "none";
      byId("mirror-percent-field").style.display = isFixed ? "none" : "grid";
    }}

    function collectFormPayload() {{
      return {{
        copy_id: byId("copy-id").value || undefined,
        copy_name: byId("copy-name").value.trim(),
        wallet_to_follow: byId("wallet-to-follow").value.trim(),
        mode: byId("mode").value,
        fixed_amount_usdc: Number(byId("fixed-amount-usdc").value || 0),
        mirror_source_percent: Number(byId("mirror-source-percent").value || 0),
        slippage_pct: Number(byId("slippage-pct").value || 0),
        price_min_cents: Number(byId("price-min-cents").value || 0),
        price_max_cents: Number(byId("price-max-cents").value || 0),
        max_total_usdc: Number(byId("max-total-usdc").value || 0),
        max_per_market_usdc: Number(byId("max-per-market-usdc").value || 0),
        bankroll_usdc: Number(byId("bankroll-usdc").value || 0),
        min_trade_usdc: Number(byId("min-trade-usdc").value || 0),
      }};
    }}

    async function postJson(url, payload) {{
      const response = await fetch(url, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload || {{}}),
      }});
      const data = await response.json();
      if (!response.ok || !data.ok) {{
        throw new Error(data.error || `request_failed:${{response.status}}`);
      }}
      return data;
    }}

    async function handleFormSubmit(event) {{
      event.preventDefault();
      const payload = collectFormPayload();
      const isEdit = Boolean(payload.copy_id);
      await postJson(isEdit ? "/api/copies/update" : "/api/copies/add", payload);
      closeModal();
    }}

    async function toggleCopy(copyId) {{
      await postJson("/api/copies/toggle", {{ copy_id: copyId }});
    }}

    async function resetCopy(copyId) {{
      await postJson("/api/copies/reset", {{ copy_id: copyId }});
    }}

    async function deleteCopy(copyId) {{
      await postJson("/api/copies/delete", {{ copy_id: copyId }});
      if (selectedCopyId === copyId) {{
        selectedCopyId = null;
      }}
    }}

    function renderSummary(state) {{
      const summary = state.summary || {{}};
      setMetric("copies-total", String(summary.copies_total || 0));
      setMetric("copies-active", String(summary.copies_active || 0));
      setMetric("total-bankroll", fmtMoney(summary.total_bankroll_usdc));
      setMetric("total-equity", fmtMoney(summary.total_equity_usdc), Number(summary.total_pnl_usdc || 0) >= 0 ? "good" : "bad");
      setMetric("total-pnl", fmtMoney(summary.total_pnl_usdc), Number(summary.total_pnl_usdc || 0) >= 0 ? "good" : "bad");
      byId("last-update").textContent = state.last_update_at || "-";
      byId("last-error").textContent = state.last_error || "nenhum";
      const pill = byId("status-pill");
      pill.textContent = state.last_error ? "Com erro" : "Conectado";
      pill.className = state.last_error ? "pill bad" : "pill";
    }}

    function renderCopies(state) {{
      const rows = (state.copies || []);
      const body = byId("copies-body");
      if (!rows.length) {{
        body.innerHTML = `<tr><td colspan="9" class="muted">Nenhum copy cadastrado.</td></tr>`;
        return;
      }}
      if (!selectedCopyId || !rows.find((item) => item.copy_id === selectedCopyId)) {{
        selectedCopyId = rows[0].copy_id;
      }}
      body.innerHTML = rows.map((copy) => {{
        const pnlClass = Number(copy.pnl_usdc || 0) >= 0 ? "good" : "bad";
        const configLabel = copy.mode === "fixed_usdc"
          ? `$${{Number(copy.fixed_amount_usdc || 0).toFixed(2)}}`
          : `${{Number(copy.mirror_source_percent || 0).toFixed(0)}}%`;
        const statusPill = copy.active ? `<span class="pill">active</span>` : `<span class="pill bad">inactive</span>`;
        return `
          <tr class="copy-row ${{copy.copy_id === selectedCopyId ? "selected" : ""}}" data-copy-id="${{copy.copy_id}}">
            <td>
              <strong>${{copy.copy_name}}</strong><br>
              <span class="muted mono">${{copy.wallet_short}}</span>
            </td>
            <td>${{copy.mode === "fixed_usdc" ? "Fixed USDC" : "Mirror Source %"}}</td>
            <td>${{configLabel}}<br><span class="muted small">bank ${{fmtMoney(copy.bankroll_usdc)}}</span></td>
            <td>${{Number(copy.slippage_pct || 0).toFixed(1)}}%<br><span class="muted small">${{copy.price_range[0]}}c - ${{copy.price_range[1]}}c</span></td>
            <td>${{fmtMoney(copy.copied_volume_usdc)}}</td>
            <td>${{copy.signals_executed}} / ${{copy.signals_processed}}</td>
            <td class="${{pnlClass}}">${{fmtMoney(copy.pnl_usdc)}}</td>
            <td>${{statusPill}}</td>
            <td>
              <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <button class="btn small alt" data-action="toggle" data-copy-id="${{copy.copy_id}}">${{copy.active ? "Pause" : "Play"}}</button>
                <button class="btn small alt" data-action="edit" data-copy-id="${{copy.copy_id}}">Edit</button>
                <button class="btn small alt" data-action="reset" data-copy-id="${{copy.copy_id}}">Reset</button>
                <button class="btn small bad" data-action="delete" data-copy-id="${{copy.copy_id}}">Delete</button>
              </div>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    function renderDetail(copy) {{
      if (!copy) {{
        byId("detail-title").textContent = "Detalhes do copy";
        byId("detail-subtitle").textContent = "Selecione um copy para ver posições e eventos.";
        byId("detail-content").innerHTML = `<div class="detail-empty">Nenhum copy selecionado.</div>`;
        byId("copy-summary").innerHTML = `<div class="detail-empty">Nenhum copy selecionado.</div>`;
        return;
      }}
      byId("detail-title").textContent = copy.copy_name;
      byId("detail-subtitle").textContent = `${{copy.wallet_to_follow}}${{copy.source_name ? ` · ${{copy.source_name}}` : ""}}`;
      byId("copy-summary").innerHTML = `
        <div class="table-wrap">
          <table>
            <tbody>
              <tr><th>Wallet</th><td class="mono">${{copy.wallet_to_follow}}</td></tr>
              <tr><th>Mode</th><td>${{copy.mode === "fixed_usdc" ? "Fixed USDC" : "Mirror Source %"}}</td></tr>
              <tr><th>Banca</th><td>${{fmtMoney(copy.bankroll_usdc)}}</td></tr>
              <tr><th>Caixa</th><td>${{fmtMoney(copy.cash_usdc)}}</td></tr>
              <tr><th>Exposição</th><td>${{fmtMoney(copy.open_exposure_usdc)}}</td></tr>
              <tr><th>Equity</th><td class="${{Number(copy.pnl_usdc || 0) >= 0 ? "good" : "bad"}}">${{fmtMoney(copy.equity_usdc)}}</td></tr>
              <tr><th>PnL</th><td class="${{Number(copy.pnl_usdc || 0) >= 0 ? "good" : "bad"}}">${{fmtMoney(copy.pnl_usdc)}}</td></tr>
              <tr><th>Último poll</th><td class="mono">${{copy.last_poll_at || "-"}}</td></tr>
              <tr><th>Último sinal</th><td class="mono">${{copy.last_source_trade_at || "-"}}</td></tr>
              <tr><th>Erro</th><td>${{copy.last_error || "nenhum"}}</td></tr>
            </tbody>
          </table>
        </div>
      `;
      const content = byId("detail-content");
      if (activeTab === "positions") {{
        const allRows = copy.positions || [];
        const query = positionsQuery.trim().toLowerCase();
        const rows = allRows
          .filter((item) => {{
            if (!query) {{
              return true;
            }}
            const haystack = `${{item.question || ""}} ${{item.outcome || ""}}`.toLowerCase();
            return haystack.includes(query);
          }})
          .sort((left, right) => {{
            const leftPnl = Number(left.market_value || 0) - Number(left.cost_basis || 0);
            const rightPnl = Number(right.market_value || 0) - Number(right.cost_basis || 0);
            if (positionsSort === "pnl_desc") {{
              return rightPnl - leftPnl;
            }}
            if (positionsSort === "pnl_asc") {{
              return leftPnl - rightPnl;
            }}
            if (positionsSort === "value_asc") {{
              return Number(left.market_value || 0) - Number(right.market_value || 0);
            }}
            if (positionsSort === "traded_desc") {{
              return Number(right.cost_basis || 0) - Number(left.cost_basis || 0);
            }}
            if (positionsSort === "traded_asc") {{
              return Number(left.cost_basis || 0) - Number(right.cost_basis || 0);
            }}
            if (positionsSort === "avg_desc") {{
              return Number(right.avg_price || 0) - Number(left.avg_price || 0);
            }}
            if (positionsSort === "avg_asc") {{
              return Number(left.avg_price || 0) - Number(right.avg_price || 0);
            }}
            if (positionsSort === "alpha_asc") {{
              return String(left.question || "").localeCompare(String(right.question || ""));
            }}
            if (positionsSort === "alpha_desc") {{
              return String(right.question || "").localeCompare(String(left.question || ""));
            }}
            return Number(right.market_value || 0) - Number(left.market_value || 0);
          }});
        content.innerHTML = allRows.length ? `
          <div class="detail-toolbar">
            <div class="inline-control">
              <label for="positions-filter-input">Filtrar</label>
              <input id="positions-filter-input" placeholder="Cidade, faixa, outcome..." value="${{positionsQuery.replace(/"/g, "&quot;")}}">
            </div>
            <div class="inline-control">
              <label for="positions-sort-select">Top down</label>
              <select id="positions-sort-select">
                <option value="value_desc" ${{positionsSort === "value_desc" ? "selected" : ""}}>Maior valor</option>
                <option value="value_asc" ${{positionsSort === "value_asc" ? "selected" : ""}}>Menor valor</option>
                <option value="pnl_desc" ${{positionsSort === "pnl_desc" ? "selected" : ""}}>Maior PnL</option>
                <option value="pnl_asc" ${{positionsSort === "pnl_asc" ? "selected" : ""}}>Menor PnL</option>
                <option value="traded_desc" ${{positionsSort === "traded_desc" ? "selected" : ""}}>Maior exposição</option>
                <option value="traded_asc" ${{positionsSort === "traded_asc" ? "selected" : ""}}>Menor exposição</option>
                <option value="avg_desc" ${{positionsSort === "avg_desc" ? "selected" : ""}}>Maior preço médio</option>
                <option value="avg_asc" ${{positionsSort === "avg_asc" ? "selected" : ""}}>Menor preço médio</option>
                <option value="alpha_asc" ${{positionsSort === "alpha_asc" ? "selected" : ""}}>A-Z</option>
                <option value="alpha_desc" ${{positionsSort === "alpha_desc" ? "selected" : ""}}>Z-A</option>
              </select>
            </div>
            <div class="toolbar-meta">${{rows.length}} de ${{allRows.length}} posições</div>
          </div>
          ${{
            rows.length ? `
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th><button class="sort-head" type="button" data-sort-key="alpha">Market <span class="sort-arrow">${{sortIndicator("alpha")}}</span></button></th>
                  <th><button class="sort-head" type="button" data-sort-key="avg">AVG → NOW <span class="sort-arrow">${{sortIndicator("avg")}}</span></button></th>
                  <th><button class="sort-head" type="button" data-sort-key="pnl">Status <span class="sort-arrow">${{sortIndicator("pnl")}}</span></button></th>
                  <th><button class="sort-head" type="button" data-sort-key="traded">Traded <span class="sort-arrow">${{sortIndicator("traded")}}</span></button></th>
                  <th><button class="sort-head" type="button" data-sort-key="value">Value <span class="sort-arrow">${{sortIndicator("value")}}</span></button></th>
                </tr>
              </thead>
              <tbody>
                ${{rows.map((item) => {{
                  const pnl = Number(item.market_value || 0) - Number(item.cost_basis || 0);
                  return `
                    <tr>
                      <td>${{item.question}}<br><span class="muted mono">${{item.outcome}}</span></td>
                      <td>${{fmtNum(item.avg_price)}} → ${{fmtNum(item.mark_price)}}</td>
                      <td class="${{pnl >= 0 ? "good" : "bad"}}">${{pnl >= 0 ? "+" : ""}}${{fmtMoney(pnl)}}</td>
                      <td>${{fmtMoney(item.cost_basis)}}</td>
                      <td>${{fmtMoney(item.market_value)}}</td>
                    </tr>
                  `;
                }}).join("")}}
              </tbody>
            </table>
          </div>` : `<div class="detail-empty">Nenhuma posição bate com o filtro atual.</div>`
          }}
        ` : `<div class="detail-empty">Sem posições abertas.</div>`;
        return;
      }}
      if (activeTab === "events") {{
        const rows = copy.recent_events || [];
        content.innerHTML = rows.length ? `
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Time</th><th>Market</th><th>Outcome</th><th>Action</th><th>Amount</th><th>Delta</th></tr>
              </thead>
              <tbody>
                ${{rows.map((item) => `
                  <tr>
                    <td class="mono">${{item.timestamp || "-"}}</td>
                    <td>${{item.question}}</td>
                    <td>${{item.outcome}}</td>
                    <td class="mono">${{item.action}}</td>
                    <td>${{fmtMoney(item.executed_usdc || item.requested_usdc)}}</td>
                    <td class="${{item.accepted ? "good" : "bad"}}">${{item.reason}}</td>
                  </tr>
                `).join("")}}
              </tbody>
            </table>
          </div>` : `<div class="detail-empty">Sem eventos recentes.</div>`;
        return;
      }}
      const rows = copy.history || [];
      content.innerHTML = rows.length ? `
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Time</th><th>Question</th><th>Action</th><th>Source</th><th>Market</th><th>Result</th></tr>
            </thead>
            <tbody>
              ${{rows.map((item) => `
                <tr>
                  <td class="mono">${{item.trade.timestamp || "-"}}</td>
                  <td>${{item.trade.question}}</td>
                  <td class="mono">${{item.trade.action}}</td>
                  <td>${{fmtNum(item.trade.source_price)}}</td>
                  <td>${{fmtNum(item.trade.market_price)}}</td>
                  <td class="${{item.decision.accepted ? "good" : "bad"}}">${{item.decision.reason}}</td>
                </tr>
              `).join("")}}
            </tbody>
          </table>
        </div>` : `<div class="detail-empty">Sem histórico ainda.</div>`;
    }}

    function render(state) {{
      appState = state;
      renderSummary(state);
      renderCopies(state);
      const selected = (state.copies || []).find((item) => item.copy_id === selectedCopyId) || null;
      renderDetail(selected);
    }}

    byId("new-copy-button").addEventListener("click", () => openModal());
    byId("close-modal-button").addEventListener("click", closeModal);
    byId("cancel-copy-button").addEventListener("click", closeModal);
    byId("mode").addEventListener("change", syncModeFields);
    byId("copy-form").addEventListener("submit", handleFormSubmit);
    document.querySelectorAll("[data-fixed]").forEach((button) => {{
      button.addEventListener("click", () => {{
        byId("fixed-amount-usdc").value = button.dataset.fixed;
      }});
    }});

    document.querySelectorAll(".tab").forEach((button) => {{
      button.addEventListener("click", () => {{
        activeTab = button.dataset.tab;
        document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
        button.classList.add("active");
        if (appState) {{
          const selected = (appState.copies || []).find((item) => item.copy_id === selectedCopyId) || null;
          renderDetail(selected);
        }}
      }});
    }});

    document.addEventListener("input", (event) => {{
      if (event.target?.id !== "positions-filter-input") {{
        return;
      }}
      positionsQuery = event.target.value || "";
      if (appState) {{
        const selected = (appState.copies || []).find((item) => item.copy_id === selectedCopyId) || null;
        renderDetail(selected);
      }}
    }});

    document.addEventListener("change", (event) => {{
      if (event.target?.id !== "positions-sort-select") {{
        return;
      }}
      positionsSort = event.target.value || "value_desc";
      if (appState) {{
        const selected = (appState.copies || []).find((item) => item.copy_id === selectedCopyId) || null;
        renderDetail(selected);
      }}
    }});

    document.addEventListener("click", (event) => {{
      const sortButton = event.target.closest("[data-sort-key]");
      if (!sortButton) {{
        return;
      }}
      const key = sortButton.dataset.sortKey;
      const defaultDirection = key === "alpha" ? "asc" : "desc";
      let nextDirection = defaultDirection;
      if (positionsSort.startsWith(`${{key}}_`)) {{
        nextDirection = positionsSort.endsWith("_desc") ? "asc" : "desc";
      }}
      positionsSort = `${{key}}_${{nextDirection}}`;
      if (appState) {{
        const selected = (appState.copies || []).find((item) => item.copy_id === selectedCopyId) || null;
        renderDetail(selected);
      }}
    }});

    byId("copies-body").addEventListener("click", async (event) => {{
      const actionButton = event.target.closest("button[data-action]");
      if (actionButton) {{
        const copyId = actionButton.dataset.copyId;
        const action = actionButton.dataset.action;
        const copy = (appState?.copies || []).find((item) => item.copy_id === copyId);
        if (action === "toggle") {{
          await toggleCopy(copyId);
          return;
        }}
        if (action === "edit" && copy) {{
          openModal(copy);
          return;
        }}
        if (action === "reset") {{
          await resetCopy(copyId);
          return;
        }}
        if (action === "delete") {{
          await deleteCopy(copyId);
          return;
        }}
      }}
      const row = event.target.closest(".copy-row");
      if (!row) {{
        return;
      }}
      selectedCopyId = row.dataset.copyId;
      if (appState) {{
        render(appState);
      }}
    }});

    fetch("/api/state")
      .then((response) => response.json())
      .then(render)
      .catch(() => {{
        byId("status-pill").textContent = "Falha";
        byId("status-pill").className = "pill bad";
      }});

    const source = new EventSource("/events");
    source.onmessage = (event) => render(JSON.parse(event.data));
    source.onerror = () => {{
      byId("status-pill").textContent = "Reconectando";
      byId("status-pill").className = "pill bad";
    }};
  </script>
</body>
</html>"""
    return template.replace("__BASE_URL__", base_url).replace("{{", "{").replace("}}", "}")
