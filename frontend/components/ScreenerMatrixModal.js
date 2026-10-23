(function() {
    const ScreenerMatrixModal = ({ isOpen, onClose }) => {
        if (!isOpen) return null;

        const [data, setData] = React.useState([]);
        const [universe, setUniverse] = React.useState("all");
        const [btcClimate, setBtcClimate] = React.useState("ALTCOIN_EXPANSION");
        const [btcDominance, setBtcDominance] = React.useState(57.5);
        const [ignitionsCount, setIgnitionsCount] = React.useState(0);
        const [loading, setLoading] = React.useState(true);
        const [filterAction, setFilterAction] = React.useState("ALL");
        const [search, setSearch] = React.useState("");
        const [copied, setCopied] = React.useState(false);
        const [lastUpdated, setLastUpdated] = React.useState(null);

        const fetchMatrix = async (selectedUniverse = universe) => {
            try {
                const res = await fetch(`/api/v1/market/screener-matrix?universe=${selectedUniverse}`);
                if (res.ok) {
                    const json = await res.json();
                    setData(json.data || []);
                    if (json.btc_climate) setBtcClimate(json.btc_climate);
                    if (json.btc_dominance) setBtcDominance(json.btc_dominance);
                    if (json.bot_ignitions_detected !== undefined) setIgnitionsCount(json.bot_ignitions_detected);
                    setLastUpdated(new Date().toLocaleTimeString());
                }
            } catch (err) {
                console.error("Erro ao carregar Screener Matrix:", err);
            } finally {
                setLoading(false);
            }
        };

        React.useEffect(() => {
            fetchMatrix(universe);
            const interval = setInterval(() => fetchMatrix(universe), 5000);
            return () => clearInterval(interval);
        }, [universe]);

        const handleUniverseChange = (newUni) => {
            setUniverse(newUni);
            setLoading(true);
            fetchMatrix(newUni);
        };

        const copyAiContext = async () => {
            try {
                const res = await fetch(`/api/v1/market/ai-context?universe=${universe}&top_limit=8`);
                if (res.ok) {
                    const json = await res.json();
                    const text = JSON.stringify(json.context, null, 2);
                    await navigator.clipboard.writeText(text);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 3000);
                }
            } catch (err) {
                console.error("Erro ao copiar contexto de IA:", err);
            }
        };

        const filtered = (data || []).filter(item => {
            const matchesSearch = item.symbol.toLowerCase().includes(search.toLowerCase()) ||
                                  item.pair.toLowerCase().includes(search.toLowerCase());
            if (!matchesSearch) return false;
            if (filterAction === "ALL") return true;
            if (filterAction === "BOT_IGNITION") return item.bot_ignition === true;
            if (filterAction === "EXP_IGNITION") return item["1c_exp"] >= 70;
            return item.action === filterAction;
        });

        return (
            <div className="fixed inset-0 z-[12000] flex items-center justify-center p-3 md:p-6 bg-black/85 backdrop-blur-md">
                <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col rounded-2xl bg-[#0b0e11] border border-[#2b3139] shadow-2xl overflow-hidden text-gray-100">
                    
                    {/* Header */}
                    <div className="flex flex-wrap items-center justify-between p-4 md:p-5 border-b border-[#2b3139] bg-[#12161c]">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-[#fcd535]/10 border border-[#fcd535]/30 flex items-center justify-center text-[#fcd535]">
                                <span className="material-icons-round text-2xl">radar</span>
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h2 className="text-base md:text-lg font-bold tracking-wide uppercase font-mono text-white">
                                        Radar Universal Encryptos
                                    </h2>
                                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase bg-[#fcd535]/10 text-[#fcd535] border border-[#fcd535]/20">
                                        {universe === 'all' ? '507 Contratos OKX' : 'Top 30 Titãs'}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-400 font-mono mt-0.5">
                                    Detecção de Aceleração Smart Money • Robôs em Ignição: <strong className="text-[#fcd535]">{ignitionsCount}</strong> • Atualizado: {lastUpdated || "Sincronizando..."}
                                </p>
                            </div>
                        </div>

                        {/* Top Actions & Macro Badges */}
                        <div className="flex items-center gap-2 mt-3 md:mt-0">
                            {/* Universe Toggle */}
                            <div className="flex items-center bg-[#1e2329] p-0.5 rounded-lg border border-[#2b3139] font-mono text-xs">
                                <button
                                    onClick={() => handleUniverseChange('all')}
                                    className={`px-2.5 py-1 rounded-md font-bold transition-all ${
                                        universe === 'all' ? 'bg-[#fcd535] text-black shadow-sm' : 'text-gray-400 hover:text-white'
                                    }`}
                                >
                                    Universal (507)
                                </button>
                                <button
                                    onClick={() => handleUniverseChange('titans')}
                                    className={`px-2.5 py-1 rounded-md font-bold transition-all ${
                                        universe === 'titans' ? 'bg-[#fcd535] text-black shadow-sm' : 'text-gray-400 hover:text-white'
                                    }`}
                                >
                                    Titãs (30)
                                </button>
                            </div>

                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1e2329] border border-[#2b3139] font-mono text-xs">
                                <span className="text-gray-400">BTC.D:</span>
                                <span className="text-white font-bold">{btcDominance}%</span>
                                <span className="text-gray-600">|</span>
                                <span className="text-[#0ecb81] font-bold">{btcClimate}</span>
                            </div>

                            <button
                                onClick={copyAiContext}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-xs font-bold transition-all border ${
                                    copied 
                                    ? 'bg-[#0ecb81]/20 border-[#0ecb81] text-[#0ecb81]' 
                                    : 'bg-[#fcd535]/15 hover:bg-[#fcd535]/25 border-[#fcd535]/40 text-[#fcd535]'
                                }`}
                                title="Copia o contexto de mercado em JSON semântico para qualquer LLM (Claude, ChatGPT, Hermes)"
                            >
                                <span className="material-icons-round text-base">{copied ? 'done' : 'content_copy'}</span>
                                {copied ? 'Contexto Copiado!' : 'Copiar para IA (JSON)'}
                            </button>

                            <button
                                onClick={onClose}
                                className="w-8 h-8 rounded-lg flex items-center justify-center bg-[#1e2329] hover:bg-[#2b3139] text-gray-400 hover:text-white transition-colors"
                            >
                                <span className="material-icons-round text-lg">close</span>
                            </button>
                        </div>
                    </div>

                    {/* Filter & Search Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#181d24] border-b border-[#2b3139] font-mono text-xs">
                        <div className="flex items-center gap-1 overflow-x-auto">
                            {[
                                { id: 'ALL', label: 'Todos' },
                                { id: 'BOT_IGNITION', label: `Robôs Ligados (${ignitionsCount})` },
                                { id: 'EXP_IGNITION', label: '1C-EXP >= 70' },
                                { id: 'LONG', label: 'LONG' },
                                { id: 'SHORT', label: 'SHORT' }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setFilterAction(tab.id)}
                                    className={`px-3 py-1 rounded-md transition-colors font-bold ${
                                        filterAction === tab.id
                                        ? 'bg-[#fcd535] text-black shadow-sm'
                                        : 'bg-[#1e2329] text-gray-400 hover:text-white'
                                    }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        <div className="relative min-w-[200px]">
                            <span className="material-icons-round absolute left-2.5 top-1.5 text-gray-400 text-sm">search</span>
                            <input
                                type="text"
                                placeholder="Filtrar por moeda (ex: SUI, TIA, SOL)..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="w-full pl-8 pr-3 py-1 bg-[#0b0e11] border border-[#2b3139] rounded-md text-white placeholder-gray-500 text-xs focus:outline-none focus:border-[#fcd535]"
                            />
                        </div>
                    </div>

                    {/* Table View */}
                    <div className="flex-1 overflow-y-auto p-4">
                        {loading && data.length === 0 ? (
                            <div className="py-20 flex flex-col items-center justify-center text-gray-500 font-mono">
                                <div className="w-8 h-8 border-2 border-[#fcd535]/30 border-t-[#fcd535] rounded-full animate-spin mb-3"></div>
                                Varrendo {universe === 'all' ? '507 Contratos OKX' : '30 Titãs'} em tempo real...
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left font-mono text-xs border-collapse">
                                    <thead>
                                        <tr className="border-b border-[#2b3139] text-gray-400 uppercase tracking-wider text-[11px] pb-2">
                                            <th className="py-2.5 px-3">Ativo</th>
                                            <th className="py-2.5 px-3">Preço</th>
                                            <th className="py-2.5 px-3">24h</th>
                                            <th className="py-2.5 px-3">Volume 24h</th>
                                            <th className="py-2.5 px-3 min-w-[140px]">1C-EXP (Aceleração)</th>
                                            <th className="py-2.5 px-3 min-w-[120px]">Canal H1</th>
                                            <th className="py-2.5 px-3">Status dos Robôs</th>
                                            <th className="py-2.5 px-3 text-center">Sinal Laya</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#1e2329]">
                                        {filtered.map(row => {
                                            const isExpHigh = row["1c_exp"] >= 70;
                                            const isRangeFloor = row["1c_range"] <= 20;
                                            const isRangeCeil = row["1c_range"] >= 80;

                                            return (
                                                <tr key={row.symbol} className="hover:bg-[#181d24]/60 transition-colors">
                                                    {/* Symbol with Ignition Badge */}
                                                    <td className="py-3 px-3 font-bold text-white flex items-center gap-2">
                                                        <span className={`w-2 h-2 rounded-full ${row.bot_ignition ? 'bg-[#0ecb81] shadow-[0_0_8px_#0ecb81]' : 'bg-gray-600'}`}></span>
                                                        <span>{row.pair}</span>
                                                        {row.bot_ignition && (
                                                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#0ecb81]/15 text-[#0ecb81] border border-[#0ecb81]/30 font-bold uppercase">
                                                                ROBÔS ON
                                                            </span>
                                                        )}
                                                    </td>

                                                    {/* Price */}
                                                    <td className="py-3 px-3 text-gray-100 font-semibold">
                                                        ${row.price < 0.1 ? row.price.toFixed(6) : row.price < 1 ? row.price.toFixed(4) : row.price.toFixed(2)}
                                                    </td>

                                                    {/* 24h Change */}
                                                    <td className={`py-3 px-3 font-bold ${row.change_24h >= 0 ? 'text-[#0ecb81]' : 'text-[#f6465d]'}`}>
                                                        {row.change_24h >= 0 ? '+' : ''}{row.change_24h}%
                                                    </td>

                                                    {/* Volume 24h */}
                                                    <td className="py-3 px-3 text-gray-400">
                                                        ${(row.vol_ccy_24h / 1_000_000).toFixed(1)}M
                                                    </td>

                                                    {/* 1C-EXP Progress */}
                                                    <td className="py-3 px-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="flex-1 h-2 bg-[#1e2329] rounded-full overflow-hidden border border-[#2b3139]">
                                                                <div 
                                                                    className={`h-full rounded-full transition-all duration-500 ${
                                                                        isExpHigh ? 'bg-[#fcd535] shadow-[0_0_8px_#fcd535]' : row["1c_exp"] >= 45 ? 'bg-[#0ecb81]' : 'bg-gray-600'
                                                                    }`}
                                                                    style={{ width: `${Math.min(100, row["1c_exp"])}%` }}
                                                                ></div>
                                                            </div>
                                                            <span className={`text-[11px] font-bold ${isExpHigh ? 'text-[#fcd535]' : 'text-gray-300'}`}>
                                                                {row["1c_exp"]}
                                                            </span>
                                                        </div>
                                                    </td>

                                                    {/* 1C-RANGE Meter */}
                                                    <td className="py-3 px-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="flex-1 h-2 bg-[#1e2329] rounded-full overflow-hidden border border-[#2b3139] relative">
                                                                <div 
                                                                    className={`h-full rounded-full transition-all duration-500 ${
                                                                        isRangeFloor ? 'bg-[#0ecb81]' : isRangeCeil ? 'bg-[#f6465d]' : 'bg-blue-400'
                                                                    }`}
                                                                    style={{ width: `${Math.max(5, Math.min(100, row["1c_range"]))}%` }}
                                                                ></div>
                                                            </div>
                                                            <span className="text-[11px] text-gray-300 font-bold">
                                                                {row["1c_range"]}%
                                                            </span>
                                                        </div>
                                                    </td>

                                                    {/* Bot Status & Setup */}
                                                    <td className="py-3 px-3">
                                                        <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${
                                                            row.bot_ignition 
                                                            ? 'bg-[#fcd535]/10 border-[#fcd535]/30 text-[#fcd535]' 
                                                            : 'bg-[#1e2329] border-[#2b3139] text-gray-400'
                                                        }`}>
                                                            {row.bot_status || row.setup}
                                                        </span>
                                                    </td>

                                                    {/* Signal / Action */}
                                                    <td className="py-3 px-3 text-center">
                                                        <span className={`inline-block text-[10px] px-2.5 py-0.5 rounded font-bold uppercase ${
                                                            row.action === 'LONG' 
                                                            ? 'bg-[#0ecb81]/20 text-[#0ecb81] border border-[#0ecb81]/40' 
                                                            : row.action === 'SHORT'
                                                            ? 'bg-[#f6465d]/20 text-[#f6465d] border border-[#f6465d]/40'
                                                            : 'bg-gray-800 text-gray-400 border border-gray-700'
                                                        }`}>
                                                            {row.action}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>

                    {/* Footer Info */}
                    <div className="p-3 bg-[#0d1015] border-t border-[#2b3139] flex flex-wrap items-center justify-between font-mono text-[11px] text-gray-400">
                        <div className="flex items-center gap-4">
                            <span>Universo Ativo: <strong className="text-white">{universe === 'all' ? '507 Pares OKX' : '30 Titãs'}</strong></span>
                            <span>•</span>
                            <span>Exibindo: <strong className="text-[#fcd535]">{filtered.length}</strong> altcoins</span>
                            <span>•</span>
                            <span>Invariante Never Give Back Ativa (Alavancagem 15x)</span>
                        </div>
                        <div className="text-gray-500">
                            1Crypten Sovereign Intelligence • Padrão Lamborghini Zero Emojis
                        </div>
                    </div>

                </div>
            </div>
        );
    };

    window.ScreenerMatrixModal = ScreenerMatrixModal;
})();
