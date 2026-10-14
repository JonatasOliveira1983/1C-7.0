/* ==========================================================================
   1CRYPTEN 7.0 — LAMBORGHINI UNIFIED SHELL & SIDEBAR DRAWER
   Motorsport precision, Jet Black canvas, Lamborghini Gold accents.
   No emojis — 100% Crisp Vector SVGs.
   ========================================================================== */

(function () {
  const ICONS = {
    menu: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
    close: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    cockpit: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
    sandbox: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><path d="M10 2v7.31M14 9.3V1.99M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/></svg>`,
    hermes: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
    radar: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>`,
    docs: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    captain: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    flash: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
    oracle: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><circle cx="12" cy="12" r="3"/><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/></svg>`,
    kronos: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    chat: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
    pulse: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    plutus: `<svg class="sh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M15.5 10.5H10a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H8.5"/></svg>`
  };

  window.SHELL_ICONS = ICONS;

  window.toggleSidebar = function () {
    const el = document.getElementById("app-sidebar");
    const ov = document.getElementById("app-sidebar-overlay");
    if (el) el.classList.toggle("sidebar-open");
    if (ov) ov.classList.toggle("active");
  };

  function setVitalDot(vitalName, state, label) {
    const dot = document.querySelector(`.sh-vital-dot[data-vital="${vitalName}"]`);
    if (!dot) return;
    if (state === "ok") {
      dot.style.background = "#00E676";
      dot.style.boxShadow = "0 0 6px rgba(0, 230, 118, 0.6)";
    } else if (state === "warn") {
      dot.style.background = "#FFC000";
      dot.style.boxShadow = "0 0 6px rgba(255, 192, 0, 0.6)";
    } else {
      dot.style.background = "#FF1744";
      dot.style.boxShadow = "0 0 6px rgba(255, 23, 68, 0.6)";
    }
  }

  function mountSidebar(activePage) {
    // Overlay
    const overlayEl = document.createElement("div");
    overlayEl.id = "app-sidebar-overlay";
    overlayEl.onclick = window.toggleSidebar;
    document.body.appendChild(overlayEl);

    // Sidebar Drawer
    const sidebarEl = document.createElement("aside");
    sidebarEl.id = "app-sidebar";
    sidebarEl.innerHTML = `
      <!-- Brand & Close Bar -->
      <div style="padding: 16px 14px 14px 14px; border-bottom: 1px solid #1c1c1c; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="width: 14px; height: 14px; background: #FFC000; transform: rotate(45deg); flex-shrink: 0;"></div>
          <div>
            <div style="font-weight: 900; font-size: 13px; letter-spacing: 0.12em; color: #FFFFFF; text-transform: uppercase;">
              1CRYPTEN <span style="color: #FFC000;">7.0</span>
            </div>
            <div style="font-family: var(--font-mono); font-size: 9px; color: #777777; letter-spacing: 0.08em; text-transform: uppercase;">
              HFT MOTORSPORT OS
            </div>
          </div>
        </div>
        <button onclick="window.toggleSidebar()" class="sh-close-btn" title="Fechar Menu">
          ${ICONS.close}
        </button>
      </div>

      <!-- Quick Action -->
      <div style="padding: 12px 14px 6px 14px;">
        <a href="/hermes" style="display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; height: 36px; background: #FFC000; color: #000000; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; text-decoration: none; border: 1px solid #FFC000; transition: all 0.15s ease;">
          ${ICONS.chat}
          <span>CHAT HERMES AI</span>
        </a>
      </div>

      <!-- Scrollable Navigation & Fleet -->
      <div class="sh-scroll">
        
        <!-- Navigation Section -->
        <div class="sh-sec-title">PÁGINAS DO SISTEMA</div>
        <div style="display: flex; flex-direction: column; gap: 2px; padding: 0 10px;">
          <a href="/" class="sh-link ${activePage === 'cockpit' ? 'active' : ''}">
            ${ICONS.cockpit}
            <span>COCKPIT TÁTICO</span>
            <span class="sh-badge-subtle">HFT</span>
          </a>
          <a href="/hermes" class="sh-link ${activePage === 'hermes' ? 'active' : ''}">
            ${ICONS.hermes}
            <span>HERMES ORCHESTRATOR</span>
            <span class="sh-badge-gold">AI</span>
          </a>
          <a href="/mercado" class="sh-link ${activePage === 'market' ? 'active' : ''}">
            ${ICONS.radar}
            <span>RADAR & MERCADO</span>
          </a>
          <a href="/plutus" class="sh-link ${activePage === 'plutus' ? 'active' : ''}">
            ${ICONS.plutus}
            <span>PLUTUS (VIVER DE RENDA)</span>
            <span class="sh-badge-gold">ARCA</span>
          </a>
          <a href="/docs" target="_blank" class="sh-link">
            ${ICONS.docs}
            <span>API DOCS (SWAGGER)</span>
          </a>
        </div>

        <!-- Fleet Section -->
        <div class="sh-sec-title" style="margin-top: 18px;">AGENTES DA FROTA</div>
        <div style="display: flex; flex-direction: column; gap: 2px; padding: 0 10px;">
          <a href="/hermes" class="sh-link">
            ${ICONS.hermes}
            <span>HERMES · ORQUESTRADOR</span>
            <span class="sh-status-pill ok">ON</span>
          </a>
          <a href="/plutus" class="sh-link">
            ${ICONS.plutus}
            <span>PLUTUS · MÉTODO ARCA</span>
            <span class="sh-status-pill ok">ON</span>
          </a>
          <div class="sh-link" style="cursor: default;">
            ${ICONS.captain}
            <span>CAPTAIN · 50X CONSENSO</span>
            <span class="sh-status-pill standby">STANDBY</span>
          </div>
          <div class="sh-link" style="cursor: default;">
            ${ICONS.flash}
            <span>FLASH · ESCADINHA 1s</span>
            <span class="sh-status-pill standby">STANDBY</span>
          </div>
          <a href="/mercado" class="sh-link">
            ${ICONS.oracle}
            <span>ORACLE · REGIME ADX</span>
            <span class="sh-status-pill ok">ON</span>
          </a>
          <a href="/" class="sh-link">
            ${ICONS.kronos}
            <span>KRONOS · AAAI ENGINE</span>
            <span class="sh-status-pill ok">ON</span>
          </a>
        </div>

        <!-- Vitals Telemetry Section -->
        <div class="sh-sec-title" style="margin-top: 18px;">TELEMETRIA DOS MOTORES</div>
        <div id="vitals-strip" style="padding: 6px 14px; display: flex; flex-direction: column; gap: 8px;">
          <div class="sh-vital-item">
            <span class="sh-vital-dot" data-vital="hermes"></span>
            <span style="font-family: var(--font-mono); font-size: 10px; color: #AAAAAA;">HERMES AGENT ENGINE</span>
            <span style="margin-left: auto; font-family: var(--font-mono); font-size: 9px; color: #00E676;">ONLINE</span>
          </div>
          <div class="sh-vital-item">
            <span class="sh-vital-dot" data-vital="deepseek"></span>
            <span style="font-family: var(--font-mono); font-size: 10px; color: #AAAAAA;">DEEPSEEK / LLM BRIDGE</span>
            <span style="margin-left: auto; font-family: var(--font-mono); font-size: 9px; color: #00E676;">READY</span>
          </div>
          <div class="sh-vital-item">
            <span class="sh-vital-dot" data-vital="okx"></span>
            <span style="font-family: var(--font-mono); font-size: 10px; color: #AAAAAA;">OKX WS / MARKET FEED</span>
            <span style="margin-left: auto; font-family: var(--font-mono); font-size: 9px; color: #00E676;">CONNECTED</span>
          </div>
          <div class="sh-vital-item">
            <span class="sh-vital-dot" data-vital="db"></span>
            <span style="font-family: var(--font-mono); font-size: 10px; color: #AAAAAA;">SANDBOX DB PERSISTENCE</span>
            <span style="margin-left: auto; font-family: var(--font-mono); font-size: 9px; color: #00E676;">SYNCED</span>
          </div>
        </div>

      </div>

      <!-- Footer Signature -->
      <div style="padding: 12px 14px; border-top: 1px solid #1c1c1c; background: #050505; display: flex; flex-direction: column; gap: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; font-family: var(--font-mono); font-size: 9px; color: #666666;">
          <span>PORT: 8085</span>
          <span style="color: #FFC000;">DEFESA L0 ATIVA</span>
        </div>
        <div style="font-family: var(--font-mono); font-size: 8px; color: #444444; letter-spacing: 0.05em;">
          1CRYPTEN 7.0 • SHA-256 AUDITED
        </div>
      </div>
    `;
    document.body.appendChild(sidebarEl);
  }

  function mountHeader(activePage) {
    const headerEl = document.createElement("header");
    headerEl.id = "lamborghini-header";
    headerEl.innerHTML = `
      <div class="shell-header-bar" style="height: 52px; background: #0B0E11; border-bottom: 1px solid #2B3139; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 100; position: sticky; top: 0;">
        
        <!-- Left: Hamburger Toggle & Brand -->
        <div style="display: flex; align-items: center; gap: 12px;">
          <button id="shell-sidebar-toggle" onclick="window.toggleSidebar()" class="shell-menu-btn" title="Abrir Menu Lateral">
            ${ICONS.menu}
          </button>

          <a href="/" style="display: flex; align-items: center; gap: 10px; text-decoration: none;">
            <canvas class="thinking-orb-canvas" data-state="solving" data-size="22" data-color="#FCD535" width="22" height="22" style="width:22px;height:22px;"></canvas>
            <span style="font-weight: 900; font-size: 14px; letter-spacing: 0.12em; color: #EAECEF; text-transform: uppercase;">
              1CRYPTEN <span style="color: #FCD535;">7.0</span>
            </span>
          </a>

          <span class="shell-sep desktop-only" style="color: #2B3139; font-size: 11px;">|</span>
          
          <div class="header-fleet-pills desktop-only" style="display: flex; align-items: center; gap: 8px;">
            <canvas class="thinking-orb-canvas" data-state="listening" data-size="14" data-color="#0ECB81" width="14" height="14" style="width:14px;height:14px;"></canvas>
            <span style="font-family: var(--font-mono); font-size: 10px; color: #848E9C; text-transform: uppercase; letter-spacing: 0.05em;">
              HERMES • CAPTAIN • FLASH • KRONOS • PLUTUS
            </span>
          </div>
        </div>

        <!-- Center: Navigation (Desktop Quick Links) -->
        <nav class="desktop-nav" style="display: flex; align-items: center; gap: 4px;">
          <a href="/" class="nav-item ${activePage === 'cockpit' ? 'active' : ''}">
            ${ICONS.cockpit} <span>COCKPIT</span>
          </a>
          <a href="/plutus" class="nav-item ${activePage === 'plutus' ? 'active' : ''}">
            ${ICONS.plutus} <span>PLUTUS</span>
          </a>
          <a href="/hermes" class="nav-item ${activePage === 'hermes' ? 'active' : ''}">
            ${ICONS.hermes} <span>HERMES</span>
          </a>
          <a href="/mercado" class="nav-item ${activePage === 'market' ? 'active' : ''}">
            ${ICONS.radar} <span>RADAR</span>
          </a>
          <a href="/docs" target="_blank" class="nav-item">
            ${ICONS.docs} <span>DOCS</span>
          </a>
        </nav>

        <!-- Right: Telemetry & State -->
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="text-align: right;">
            <span style="display: block; font-size: 9px; color: #848E9C; text-transform: uppercase; letter-spacing: 0.08em;">NET WORTH</span>
            <span id="shell-networth" style="font-family: var(--font-mono); font-size: 13px; font-weight: 800; color: #FCD535;">$10,000.00</span>
          </div>
          <span id="shell-mode" class="badge-gold">PAPER</span>
        </div>
      </div>
    `;

    // Inject Unified Shell Styles
    const styleEl = document.createElement("style");
    styleEl.textContent = `
      .sh-ico {
        width: 15px;
        height: 15px;
        min-width: 15px;
        min-height: 15px;
        max-width: 15px;
        max-height: 15px;
        flex-shrink: 0;
        display: inline-block;
        vertical-align: middle;
      }

      .shell-menu-btn {
        background: transparent;
        border: 1px solid #282828;
        color: #CCCCCC;
        width: 34px;
        height: 34px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        padding: 0;
        transition: all 0.15s ease;
      }
      .shell-menu-btn:hover {
        border-color: #FFC000;
        color: #FFC000;
        background: #141414;
      }

      /* Desktop Nav Bar */
      .nav-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        color: #888888;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        text-decoration: none;
        border: 1px solid transparent;
        transition: all 0.15s ease;
      }
      .nav-item:hover {
        color: #FFFFFF;
        background: #141414;
        border-color: #282828;
      }
      .nav-item.active {
        color: #000000;
        background: #FFC000;
        border-color: #FFC000;
      }

      /* Sidebar Drawer */
      #app-sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        width: 290px;
        max-width: 86vw;
        background: #080808;
        border-right: 1px solid #202020;
        transform: translateX(-100%);
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        user-select: none;
      }
      #app-sidebar.sidebar-open {
        transform: translateX(0);
        box-shadow: 16px 0 50px rgba(0, 0, 0, 0.9);
      }

      /* Overlay */
      #app-sidebar-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.75);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        z-index: 9990;
      }
      #app-sidebar-overlay.active {
        display: block;
      }

      .sh-close-btn {
        background: transparent;
        border: 1px solid #222222;
        color: #888888;
        width: 28px;
        height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .sh-close-btn:hover {
        color: #FFC000;
        border-color: #FFC000;
        background: #141414;
      }

      .sh-sec-title {
        padding: 8px 14px 4px 14px;
        font-size: 9px;
        font-family: var(--font-mono);
        text-transform: uppercase;
        color: #666666;
        font-weight: 800;
        letter-spacing: 0.1em;
      }

      .sh-scroll {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
        padding: 6px 0;
      }
      .sh-scroll::-webkit-scrollbar {
        width: 4px;
      }
      .sh-scroll::-webkit-scrollbar-thumb {
        background: #222222;
      }

      .sh-link {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        text-align: left;
        padding: 8px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #888888;
        text-decoration: none;
        border: 1px solid transparent;
        border-left: 2px solid transparent;
        transition: all 0.12s ease;
      }
      .sh-link:hover {
        color: #FFFFFF;
        background: #141414;
        border-color: #242424;
      }
      .sh-link.active {
        color: #FFFFFF;
        background: #141414;
        border-left-color: #FFC000;
        border-right-color: #242424;
        border-top-color: #242424;
        border-bottom-color: #242424;
      }
      .sh-link.active .sh-ico {
        color: #FFC000;
      }

      .sh-badge-gold {
        margin-left: auto;
        font-size: 9px;
        font-family: var(--font-mono);
        padding: 1px 6px;
        background: rgba(255, 192, 0, 0.15);
        color: #FFC000;
        border: 1px solid rgba(255, 192, 0, 0.4);
        font-weight: 800;
      }

      .sh-badge-subtle {
        margin-left: auto;
        font-size: 9px;
        font-family: var(--font-mono);
        padding: 1px 6px;
        background: #181818;
        color: #777777;
        border: 1px solid #282828;
        font-weight: 700;
      }

      .sh-status-pill {
        margin-left: auto;
        font-size: 8px;
        font-family: var(--font-mono);
        padding: 1px 5px;
        font-weight: 800;
        letter-spacing: 0.05em;
      }
      .sh-status-pill.ok {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.3);
      }
      .sh-status-pill.standby {
        background: rgba(136, 136, 136, 0.12);
        color: #888888;
        border: 1px solid #333333;
      }

      .sh-vital-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #0f0f0f;
        padding: 6px 10px;
        border: 1px solid #1a1a1a;
      }
      .sh-vital-dot {
        width: 6px;
        height: 6px;
        background: #00E676;
        box-shadow: 0 0 6px rgba(0, 230, 118, 0.6);
        display: inline-block;
        flex-shrink: 0;
      }

      .app-bottom-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: rgba(10, 10, 10, 0.96);
        border-top: 1px solid #1c1c1c;
        display: none;
        align-items: center;
        justify-content: space-around;
        z-index: 999;
        backdrop-filter: blur(8px);
        padding-bottom: env(safe-area-inset-bottom, 0px);
      }
      .bbar-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 3px;
        color: #777777;
        text-decoration: none;
        font-size: 9px;
        font-family: var(--font-mono);
        text-transform: uppercase;
        flex: 1;
        height: 100%;
        transition: all 0.15s ease;
      }
      .bbar-item:hover, .bbar-item.active {
        color: #FFC000;
      }

      @media (max-width: 820px) {
        .desktop-nav { display: none !important; }
        .desktop-only { display: none !important; }
        .shell-header-bar { padding: 0 10px !important; }
        .app-bottom-bar { display: flex !important; }
      }
    `;
    document.head.appendChild(styleEl);
    document.body.prepend(headerEl);

    // Mount Mobile Bottom Bar
    function mountBottomBar(page) {
      if (document.getElementById("app-bottom-bar")) return;
      const bbar = document.createElement("nav");
      bbar.id = "app-bottom-bar";
      bbar.className = "app-bottom-bar mobile-only";
      bbar.innerHTML = `
        <a href="/cockpit" class="bbar-item ${page === 'cockpit' ? 'active' : ''}">
          ${ICONS.cockpit}
          <span>Cockpit</span>
        </a>
        <a href="/plutus" class="bbar-item ${page === 'plutus' ? 'active' : ''}">
          ${ICONS.plutus}
          <span>Plutus</span>
        </a>
        <a href="/mercado" class="bbar-item ${page === 'market' ? 'active' : ''}">
          ${ICONS.radar}
          <span>Radar</span>
        </a>
        <a href="/hermes" class="bbar-item ${page === 'hermes' ? 'active' : ''}">
          ${ICONS.hermes}
          <span>Hermes</span>
        </a>
        <button onclick="window.toggleSidebar()" class="bbar-item" style="background: none; border: none; cursor: pointer;">
          ${ICONS.menu}
          <span>Menu</span>
        </button>
      `;
      document.body.appendChild(bbar);
    }
    mountBottomBar(activePage);

    // Mount the Sidebar & Overlay
    mountSidebar(activePage);

    // Auto-update Net Worth from /api/sandbox/unified-state
    async function syncVitals() {
      try {
        const res = await fetch("/api/sandbox/unified-state");
        if (res.ok) {
          const data = await res.json();
          const bal = data.consolidated_balance || data.virtual_balance || data.unified_balance || 10000;
          const networthEl = document.getElementById("shell-networth");
          if (networthEl) {
            networthEl.textContent = "$" + Number(bal).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          }
          setVitalDot("hermes", "ok");
          setVitalDot("deepseek", "ok");
          setVitalDot("okx", "ok");
          setVitalDot("db", "ok");
        }
      } catch (e) {
        setVitalDot("hermes", "warn");
      }
    }
    syncVitals();
    setInterval(syncVitals, 5000);

    // Auto-init Thinking Orbs after mounting header & sidebar
    if (window.ThinkingOrbsManager) {
      window.ThinkingOrbsManager.autoInit();
    }
  }

  window.mountLamborghiniShell = mountHeader;
})();
