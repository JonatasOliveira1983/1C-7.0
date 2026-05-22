import re

def main():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Define ranges to remove (1-indexed inclusive)
    # VaultPage: 3693 to 3932
    # DashboardPage: 3355 to 3689
    # JourneyPage: 3084 to 3329

    ranges_to_remove = [
        (3693, 3932),
        (3355, 3689),
        (3084, 3329)
    ]

    # Sort ranges in descending order so we can delete safely without shifting prior indices
    ranges_to_remove.sort(key=lambda x: x[0], reverse=True)

    page_10d_code = """
        // --- Component: Page10D (Centralized HQ) ---
        const Page10D = () => {
            const vault = useVaultRT(safeJsonParse(localStorage.getItem('vault_status_cache'), { cycle_number: 1, mega_cycle_wins: 0, used_symbols_in_cycle: [], cycle_start_bankroll: 0, cycle_profit: 0 }));
            const slots = useSlotsRT(safeJsonParse(localStorage.getItem('slots_cache'), []));
            const { signals: radarSignals, updated_at: lastPulse } = useRadarPulseRT();
            const { latency, status: pulseStatus } = usePulseMonitor();
            const btcCommandStatus = useBtcCommandCenter();
            
            // Map Best Signals
            const signalsArray = Array.isArray(radarSignals) ? radarSignals : [];
            const deDuplicatedSignals = Object.values(signalsArray.reduce((acc, sig) => {
                const sym = sig.symbol;
                if (!acc[sym] || new Date(sig.timestamp || 0) > new Date(acc[sym].timestamp || 0)) {
                    acc[sym] = sig;
                }
                return acc;
            }, {}));
            const bestSignals = deDuplicatedSignals
                .filter(s => s.symbol && !s.symbol.includes("BTC") && s.score >= 80)
                .sort((a, b) => b.score - a.score)
                .slice(0, 5);

            const handlePanic = async () => {
                if (!confirm("⚠️ ATENÇÃO: Deseja realmente fechar TODAS as posições?")) return;
                try {
                    await fetch(API_BASE + '/panic', { method: 'POST' });
                } catch (e) { alert("Erro ao executar Pânico"); }
            };

            const getPulseColor = () => {
                if (pulseStatus === 'OFFLINE') return 'bg-red-500';
                if (pulseStatus === 'WARNING') return 'bg-amber-500';
                if (pulseStatus === 'DEGRADED') return 'bg-blue-400';
                if (latency < 3000) return 'bg-emerald-500';
                if (latency < 10000) return 'bg-amber-400';
                return 'bg-amber-600';
            };

            return (
                <div className="flex flex-col h-screen main-scrollable v5-bg-deep pb-28">
                    {/* Header Compacto */}
                    <header className="flex-shrink-0 px-4 py-4 bg-black/90 backdrop-blur-xl border-b border-white/5 sticky top-0 z-50">
                        <div className="max-w-3xl mx-auto flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${getPulseColor()} animate-pulse shadow-[0_0_8px_currentColor]`}></span>
                                <span className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">
                                    {pulseStatus === 'OFFLINE' ? 'LOST' : (pulseStatus === 'WARNING' ? 'LAG' : 'STABLE')}
                                </span>
                            </div>
                            <h1 className="text-xl font-display font-black text-white uppercase tracking-[0.2em] text-center ml-4">10D HQ</h1>
                            <div className="flex items-center gap-3">
                                <button onClick={handlePanic} className="w-8 h-8 rounded-full bg-red-500/20 text-red-500 flex items-center justify-center border border-red-500/50 hover:bg-red-500 hover:text-white transition-all">
                                    <span className="material-icons-round text-sm">bolt</span>
                                </button>
                            </div>
                        </div>
                    </header>

                    <main className="flex-1 max-w-3xl mx-auto w-full p-3 space-y-4">
                        {/* 1. Cofre / Progresso do Ciclo */}
                        <section className="glass-card p-4 rounded-2xl border v5-border-primary/40 bg-gradient-to-br from-primary/5 to-transparent relative overflow-hidden">
                            <div className="flex justify-between items-start mb-3 relative z-10">
                                <div>
                                    <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Mega Ciclo {vault.mega_cycle_number || 1}</h2>
                                    <h3 className="text-xl font-display font-bold text-white">Missão Elite <span className="text-primary font-black">1/100</span></h3>
                                </div>
                                <div className="text-right">
                                    <p className="text-[9px] text-slate-500 font-black uppercase">Lucro do Ciclo</p>
                                    <p className={`text-lg font-mono font-bold ${(vault.cycle_profit||0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        ${(vault.cycle_profit||0).toFixed(2)}
                                    </p>
                                </div>
                            </div>
                            <div className="space-y-2 relative z-10">
                                <div className="flex justify-between items-end">
                                    <span className="text-[9px] font-bold uppercase text-primary/80 tracking-widest">Score de Vitórias</span>
                                    <span className="text-sm font-mono font-black text-white">{vault.mega_cycle_wins || 0}/100</span>
                                </div>
                                <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/10 p-[1px]">
                                    <div className="h-full bg-primary rounded-full shadow-[0_0_10px_rgba(255,215,0,0.4)] transition-all duration-1000" style={{ width: `${Math.min(100, (vault.mega_cycle_wins||0))}%` }}></div>
                                </div>
                            </div>
                        </section>

                        {/* 2. Os 4 Slots Ativos */}
                        <section>
                            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-1 flex items-center gap-2">
                                <span className="material-icons-round text-primary text-sm">view_agenda</span>
                                Posições Ativas
                            </h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {slots.filter(s => s && s.id <= 4).map(s => {
                                    const hasTrade = !!s.symbol;
                                    const isRiskFree = hasTrade && (s.visual_status === 'RISK_ZERO' || s.visual_status === 'BIG_SURF');
                                    const isProfit = (s.pnl_percent || 0) >= 0;

                                    return (
                                        <div key={s.id} className={`p-3 rounded-xl border flex items-center justify-between ${hasTrade ? 'bg-[#0a0a0b] border-primary/20 shadow-lg' : 'bg-white/[0.02] border-white/5 opacity-60'}`}>
                                            <div className="flex items-center gap-3">
                                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${hasTrade ? (isProfit ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-500') : 'bg-white/5 text-slate-500'}`}>
                                                    <span className="text-xs font-black">{s.id}</span>
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="text-[12px] font-bold text-white">{hasTrade ? s.symbol.replace('.P', '') : 'Livre'}</span>
                                                        {isRiskFree && <span className="material-icons-round text-[10px] text-emerald-400 animate-pulse">shield</span>}
                                                    </div>
                                                    <span className={`text-[8px] font-bold uppercase tracking-widest ${hasTrade ? (s.side === 'Buy' ? 'text-emerald-400' : 'text-orange-400') : 'text-slate-600'}`}>
                                                        {hasTrade ? `${s.side === 'Buy' ? 'LONG' : 'SHORT'} • ${s.visual_status}` : (s.id <= 2 ? 'ESPERA SCALP' : 'ESPERA SWING')}
                                                    </span>
                                                </div>
                                            </div>
                                            {hasTrade && (
                                                <div className="text-right">
                                                    <div className={`text-[12px] font-mono font-black ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>
                                                        {isProfit ? '+' : ''}{(s.pnl_percent || 0).toFixed(1)}%
                                                    </div>
                                                    <div className="text-[9px] text-slate-500 font-mono">
                                                        {s.entry_price ? `$${Number(s.entry_price).toFixed(s.entry_price < 1 ? 4 : 2)}` : ''}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </section>

                        {/* 3. Radar de Sinais Elite */}
                        <section>
                            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-1 flex items-center gap-2">
                                <span className="material-icons-round text-emerald-500 text-sm">track_changes</span>
                                Alvos Eminentes (Top 5)
                            </h3>
                            <div className="space-y-2">
                                {bestSignals.length === 0 ? (
                                    <div className="p-6 text-center text-slate-600 border border-white/5 rounded-xl bg-white/[0.02]">
                                        <span className="material-icons-round text-2xl mb-1 opacity-50">radar</span>
                                        <p className="text-[10px] uppercase font-mono tracking-widest">Nenhum alvo Elite detectado</p>
                                    </div>
                                ) : (
                                    bestSignals.map((sig, i) => (
                                        <div key={i} className="p-3 rounded-xl bg-white/[0.03] border border-white/10 flex items-start justify-between">
                                            <div>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-xs font-bold text-white">{(sig.symbol||'').replace('.P', '')}</span>
                                                    <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-primary text-black font-black">
                                                        SCORE {sig.score}
                                                    </span>
                                                </div>
                                                <p className="text-[9px] text-slate-400 line-clamp-1 italic">
                                                    "{(sig.reasoning || '').replace(/\|/g, '•')}"
                                                </p>
                                            </div>
                                            {(sig.indicators && sig.indicators.cvd) && (
                                                <div className="text-right pl-2 border-l border-white/10 ml-2">
                                                    <span className="text-[8px] font-black text-slate-500 uppercase block">Momentum</span>
                                                    <span className={`text-[9px] font-mono font-bold ${sig.indicators.cvd >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                        {sig.indicators.cvd >= 0 ? '+' : ''}{(sig.indicators.cvd/1000000).toFixed(1)}M
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </section>
                    </main>
                </div>
            );
        };
"""

    for start_line, end_line in ranges_to_remove:
        # Convert 1-indexed to 0-indexed
        del lines[start_line - 1 : end_line]

    content = "".join(lines)

    # Inject Page10D where SettingsPage starts (since the preceding pages were deleted, SettingsPage is the next component)
    content = content.replace("const SettingsPage = ({ onLogout, theme, setTheme }) => {", page_10d_code + "\n        const SettingsPage = ({ onLogout, theme, setTheme }) => {")

    # 5. Update NavBar
    pattern_navbar_items = re.compile(r'<div className="max-w-4xl mx-auto flex justify-around items-end px-2">.*?</div>', re.DOTALL)
    new_navbar_items = """<div className="max-w-4xl mx-auto flex justify-around items-end px-2">
                        <NavItem to="/" icon="space_dashboard" label="10D" isActive={location.pathname === '/' || location.pathname === '/10d'} />

                        {/* Chat Button - Central Highlight */}
                        <Link
                            to="/chat"
                            className={`flex items-center justify-center w-16 h-16 -mt-6 rounded-full transition-all ${location.pathname === '/chat'
                                ? 'bg-primary text-black shadow-[0_0_30px_rgba(255,215,0,0.4)]'
                                : 'v5-bg-card text-primary border v5-border-primary hover:border-primary/40'
                                }`}
                        >
                            <span className="material-icons-round" style={{ fontSize: '30px' }}>chat</span>
                        </Link>

                        <NavItem to="/config" icon="settings" label="Config" isActive={location.pathname === '/config'} />
                    </div>"""
    content = pattern_navbar_items.sub(new_navbar_items, content)

    # 6. Update App Routes
    pattern_routes = re.compile(r'<Routes>.*?</Routes>', re.DOTALL)
    new_routes = """<Routes>
                            <Route path="/" element={<Page10D />} />
                            <Route path="/10d" element={<Page10D />} />
                            <Route path="/chat" element={<LogsPage />} />
                            <Route path="/config" element={<SettingsPage onLogout={handleLogout} theme={theme} setTheme={setTheme} />} />
                        </Routes>"""
    content = pattern_routes.sub(new_routes, content)

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Substituição concluída com sucesso. Check index.html size.")

if __name__ == "__main__":
    main()
