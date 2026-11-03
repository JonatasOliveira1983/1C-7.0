with open("backend/app/services/laya_router_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Elevar score de corte de 88% para 92%
old_score_cutoff = '''                # 2. TRAVA 1: Score Sniper Mínimo (>= 88%)
                if c_score < 88:
                    continue'''

new_score_cutoff = '''                # 2. TRAVA 1: Score Sniper de Elite (>= 92%)
                # Exige confluência máxima de book, fluxo e heatmap. Elimina entradas afoitas em sinais mornos.
                if c_score < 92:
                    continue'''

assert old_score_cutoff in content, "old_score_cutoff not found in laya_router_service.py"
content = content.replace(old_score_cutoff, new_score_cutoff, 1)

# 2. Cadência de Mesa: Intervalo Mínimo de 15 Minutos entre Abertura de Trades (Nunca encher 4 slots juntos)
old_cadence_block = '''        # Permite ate max_allowed_slots ordens ativas simultaneas respeitando a blindagem diária
        if len(active_trades) < max_allowed_slots:'''

new_cadence_block = '''        # [V180-CADENCIA-SNIPER]: Intervalo de respiro mínimo de 15 minutos (900s) entre novas aberturas.
        # Impede a metralhadora de slots: o mercado precisa provar absorção antes de arriscar novo capital.
        last_trade_open_ts = getattr(self, "_last_global_trade_open_ts", 0.0)
        time_since_last_open = time.time() - last_trade_open_ts
        if len(active_trades) > 0 and time_since_last_open < 900:
            rem_cadence = int(900 - time_since_last_open)
            self.log_thought(
                "SISTEMA",
                f"CADÊNCIA SNIPER ATIVA: Aguardando maturação do mercado ({rem_cadence}s restantes). Proibido abrir ordens em rajada.",
                action="CADENCIA_HOLD",
                confidence=95
            )
            return best_setup

        # Permite ate max_allowed_slots ordens ativas simultaneas respeitando a blindagem diária
        if len(active_trades) < max_allowed_slots:'''

assert old_cadence_block in content, "old_cadence_block not found in laya_router_service.py"
content = content.replace(old_cadence_block, new_cadence_block, 1)

# 3. Registrar timestamp global de abertura de trade
old_save_ts = '''                await database_service.save_sandbox_trade(trade_data)
                self._last_traded_pair = clean_sym'''

new_save_ts = '''                await database_service.save_sandbox_trade(trade_data)
                self._last_traded_pair = clean_sym
                self._last_global_trade_open_ts = time.time()'''

assert old_save_ts in content, "old_save_ts not found in laya_router_service.py"
content = content.replace(old_save_ts, new_save_ts, 1)

# 4. Exigência Rigorosa de Vela 5M Fechada a Favor da Entrada (Regra Anti-Faca / Anti-Locomotiva)
old_5m_checks = '''        if direction == "SHORT":
            wick_ratio = upper_wick_ratio
            is_green_expansion = (cl_curr >= o_curr) and (wick_ratio < 0.25)

            # 1. TICK_REJECTION_INDEX (Pavio superior de exaustão >= 15%)
            if is_green_expansion:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXAUSTAO_INSUFICIENTE (Vela 5M compradora sem pavio de absorção: pavio {wick_ratio*100:.1f}% vs min 25%. Proibido adivinhar topo)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Locomotiva sem exaustão)
            if total_gain >= 0.025 and wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Alta agressiva de +{total_gain*100:.1f}% sem recuo em 5M. Proibido vender locomotiva)",
                    "metrics": metrics
                }

            # 3. MSB_CONFIRMATION: Não vender se vela estiver no topo sem pavio de rejeição real
            if h_curr >= h1 * 0.999 and wick_ratio < 0.25 and cl_curr >= l1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_ATIVA (Vela 5M sustentando topo em ${h_curr:.4f} sem pavio de rejeição ({wick_ratio*100:.1f}% vs min 25%). Aguardar confirmação real)",
                    "metrics": metrics
                }

        elif direction == "LONG":
            wick_ratio = lower_wick_ratio
            is_red_expansion = (cl_curr <= o_curr) and (wick_ratio < 0.25)

            # 1. TICK_REJECTION_INDEX (Pavio inferior de absorção >= 15%)
            if is_red_expansion:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXAUSTAO_INSUFICIENTE (Vela 5M vendedora sem pavio de absorção: pavio {wick_ratio*100:.1f}% vs min 25%. Proibido adivinhar fundo)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Queda Livre sem absorção)
            if total_drop >= 0.025 and wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Queda agressiva de -{total_drop*100:.1f}% sem respiro em 5M. Proibido comprar faca caindo)",
                    "metrics": metrics
                }

            # 3. MSB_CONFIRMATION: Não comprar se vela estiver na mínima sem absorção real
            if l_curr <= l1 * 1.001 and wick_ratio < 0.25 and cl_curr <= h1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_ATIVA (Vela 5M renovando mínimas em ${l_curr:.4f} sem absorção ({wick_ratio*100:.1f}% vs min 25%). Aguardar absorção do fundo local)",
                    "metrics": metrics
                }'''

new_5m_checks = '''        if direction == "SHORT":
            wick_ratio = upper_wick_ratio
            # [REGRA DE OURO 5M SHORT]: Proibido abrir SHORT em vela verde ou sem confirmação de topo!
            if cl_curr > o_curr:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VELA_VERDE (Vela 5M atual em alta [C: {cl_curr} > O: {o_curr}]. Proibido vender no susto enquanto compradores estão empurrando)",
                    "metrics": metrics
                }

            # 1. TICK_REJECTION_INDEX (Pavio superior de exaustão >= 20%)
            if wick_ratio < 0.20 and cl_curr >= o_curr * 0.998:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXAUSTAO_INSUFICIENTE (Vela 5M sem pavio de rejeição vendedor: {wick_ratio*100:.1f}% vs min 20%. Proibido adivinhar topo)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Locomotiva sem exaustão)
            if total_gain >= 0.015:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Alta agressiva de +{total_gain*100:.1f}% nas últimas velas de 5M. Aguardar exaustão)",
                    "metrics": metrics
                }

        elif direction == "LONG":
            wick_ratio = lower_wick_ratio
            # [REGRA DE OURO 5M LONG]: Proibido abrir LONG em vela vermelha ou faca caindo!
            if cl_curr < o_curr:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VELA_VERMELHA (Vela 5M atual em queda [C: {cl_curr} < O: {o_curr}]. Proibido tentar adivinhar fundo em faca caindo)",
                    "metrics": metrics
                }

            # 1. TICK_REJECTION_INDEX (Pavio inferior de absorção >= 20%)
            if wick_ratio < 0.20 and cl_curr <= o_curr * 1.002:
                return {
                    "is_safe": False,
                    "reason": f"VETO_ABSORCAO_INSUFICIENTE (Vela 5M sem pavio de absorção comprador: {wick_ratio*100:.1f}% vs min 20%. Aguardar baleias absorverem)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Queda Livre sem absorção)
            if total_drop >= 0.015:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Despejo agressivo de -{total_drop*100:.1f}% nas últimas velas de 5M. Proibido comprar faca caindo)",
                    "metrics": metrics
                }'''

assert old_5m_checks in content, "old_5m_checks not found in laya_router_service.py"
content = content.replace(old_5m_checks, new_5m_checks, 1)

with open("backend/app/services/laya_router_service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("laya_router_service.py updated with: Score >= 92%, Cadence 15min, and Strict 5M Candle Direction!")
