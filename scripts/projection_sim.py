import random

def monte_carlo(banca_ini, trades_dia, dias, wr, avg_win_roi, avg_loss_roi, margin_pct, n_runs=1000):
    finais = []
    taxa_custo = 0.015 # 1.5% do margin em taxas OKX (ida e volta somadas)
    for _ in range(n_runs):
        banca = banca_ini
        for dia in range(dias):
            for _ in range(trades_dia):
                margin = banca * margin_pct
                if random.random() < wr:
                    pnl = margin * (avg_win_roi / 100.0) - (margin * taxa_custo)
                else:
                    pnl = -margin * (avg_loss_roi / 100.0) - (margin * taxa_custo)
                banca += pnl
                if banca <= 0:
                    banca = 0
                    break
            if banca <= 0:
                break
        finais.append(banca)
    finais.sort()
    mediana = finais[n_runs // 2]
    p10 = finais[int(n_runs * 0.10)]
    p90 = finais[int(n_runs * 0.90)]
    return mediana, p10, p90

print("PROJECAO MATEMATICA PARA 30 DIAS (BANCA INICIAL $10,000.00)")
print("Premissas: 2% de margem por trade ($200 inicial), 10 trades por dia (300 trades no mes)")
print("Custos operacionais OKX (Taker/Maker fees de entrada e saida) inclusos e deduzidos.")
print("-" * 70)

# Cenario 1: Conservador
m1, p10_1, p90_1 = monte_carlo(10000, 10, 30, wr=0.50, avg_win_roi=8.0, avg_loss_roi=6.0, margin_pct=0.02)
rent1 = ((m1 - 10000) / 10000) * 100
lucro1 = m1 - 10000
print(f"1. CENARIO CONSERVADOR (WR: 50% | Win Medio: +8.0% | Loss Medio: -6.0%):")
print(f"   * Banca Final Estimada: ${m1:,.2f}")
print(f"   * Lucro Liquido no Mes: +${lucro1:,.2f} (+{rent1:.1f}%)")
print(f"   * Faixa de Confianca (10% a 90%): ${p10_1:,.2f} a ${p90_1:,.2f}")
print("-" * 70)

# Cenario 2: Realista / Moderado
m2, p10_2, p90_2 = monte_carlo(10000, 10, 30, wr=0.53, avg_win_roi=10.5, avg_loss_roi=6.0, margin_pct=0.02)
rent2 = ((m2 - 10000) / 10000) * 100
lucro2 = m2 - 10000
print(f"2. CENARIO REALISTA / MODERADO (WR: 53% | Win Medio: +10.5% | Loss Medio: -6.0%):")
print(f"   * Banca Final Estimada: ${m2:,.2f}")
print(f"   * Lucro Liquido no Mes: +${lucro2:,.2f} (+{rent2:.1f}%)")
print(f"   * Faixa de Confianca (10% a 90%): ${p10_2:,.2f} a ${p90_2:,.2f}")
print("-" * 70)

# Cenario 3: Otimista (com captura de outliers como SUI +48% e OP +13%)
m3, p10_3, p90_3 = monte_carlo(10000, 10, 30, wr=0.56, avg_win_roi=14.0, avg_loss_roi=5.8, margin_pct=0.02)
rent3 = ((m3 - 10000) / 10000) * 100
lucro3 = m3 - 10000
print("\n" + "=" * 70)
print("PROJECAO B: SISTEMA SELETIVO DE ALTA CONVICCAO (5 TRADES/DIA = 150 TRADES/MES)")
print("Premissa: Menos overtrading, menos taxas para a OKX, aproveitando os runners (+15% a +45%)")
print("=" * 70)

# Cenario 1: Conservador Seletivo
m1_s, p10_1s, p90_1s = monte_carlo(10000, 5, 30, wr=0.52, avg_win_roi=9.0, avg_loss_roi=6.0, margin_pct=0.02)
lucro1_s = m1_s - 10000
rent1_s = (lucro1_s / 10000) * 100
print(f"1. CENARIO CONSERVADOR SELETIVO (WR: 52% | Win: +9.0% | Loss: -6.0%):")
print(f"   * Banca Final Estimada: ${m1_s:,.2f}")
print(f"   * Lucro Liquido no Mes: +${lucro1_s:,.2f} (+{rent1_s:.1f}%)")
print(f"   * Faixa de Confianca: ${p10_1s:,.2f} a ${p90_1s:,.2f}")
print("-" * 70)

# Cenario 2: Realista / Moderado Seletivo
m2_s, p10_2s, p90_2s = monte_carlo(10000, 5, 30, wr=0.55, avg_win_roi=12.0, avg_loss_roi=6.0, margin_pct=0.02)
lucro2_s = m2_s - 10000
rent2_s = (lucro2_s / 10000) * 100
print(f"2. CENARIO REALISTA / BASE (WR: 55% | Win: +12.0% | Loss: -6.0%):")
print(f"   * Banca Final Estimada: ${m2_s:,.2f}")
print(f"   * Lucro Liquido no Mes: +${lucro2_s:,.2f} (+{rent2_s:.1f}%)")
print(f"   * Faixa de Confianca: ${p10_2s:,.2f} a ${p90_2s:,.2f}")
print("-" * 70)

# Cenario 3: Otimista Seletivo (Surfando fortes impulsos como SUI +48% e OP +13%)
m3_s, p10_3s, p90_3s = monte_carlo(10000, 5, 30, wr=0.58, avg_win_roi=16.0, avg_loss_roi=5.8, margin_pct=0.02)
lucro3_s = m3_s - 10000
rent3_s = (lucro3_s / 10000) * 100
print(f"3. CENARIO OTIMISTA (WR: 58% | Win: +16.0% | Loss: -5.8%):")
print(f"   * Banca Final Estimada: ${m3_s:,.2f}")
print(f"   * Lucro Liquido no Mes: +${lucro3_s:,.2f} (+{rent3_s:.1f}%)")
print(f"   * Faixa de Confianca: ${p10_3s:,.2f} a ${p90_3s:,.2f}")
print("=" * 70)
