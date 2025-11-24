import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lost Ark Calculator - Oreha", layout="wide")

st.title("⚒️ Calculadora Expert de Oreha (Lost Ark)",help="Ferramenta para otimizar lucros com crafting de Oreha usando Timber, Tender e Abidos.Todos os cálculos consideram taxas de mercado e custos de crafting. Use a aba 'Laboratório' para análises de ROI baseadas em runs de coleta.")
st.markdown("---")

# --- FUNÇÃO DE CÁLCULO (O CÉREBRO DA PLANILHA) ---
def calculate_optimized_revenue(q_timber, q_tender, q_abidos, u_tim, u_ten, u_abi, price_oreha, cost_craft, tax):
    """
    Calcula o lucro máximo possível dado um conjunto de materiais,
    considerando venda bruta vs craft otimizado com conversão.
    Retorna: (Lucro Melhor Opção, Descrição da Opção, Dados do Craft)
    """
    # 1. Venda Bruta
    sell_val = ((int(q_timber / 100) * 100) * u_tim + 
                (int(q_tender / 100) * 100) * u_ten + 
                (int(q_abidos / 100) * 100) * u_abi) * (1 - tax)

    # 2. Craft Otimizado
    crafts_base = int(min(q_timber / 86, q_tender / 45, q_abidos / 33))
    
    # Sobras
    rem_timber = q_timber - (crafts_base * 86)
    rem_tender = q_tender - (crafts_base * 45)
    
    # Conversão de Pó
    powder = (int(rem_timber / 100) * 80) + (int(rem_tender / 50) * 80)
    new_abidos = int(powder / 100) * 10
    
    # Crafts Extras
    crafts_extra = int(new_abidos / 33)
    total_crafts = crafts_base + crafts_extra
    
    # Receita Craft
    rev_oreha = (total_crafts * 10 * price_oreha) * (1 - tax)
    cost_gold = total_crafts * cost_craft
    profit_craft = rev_oreha - cost_gold
    
    # Retorna o melhor valor e detalhes
    if profit_craft > sell_val:
        return profit_craft, "CRAFTAR", total_crafts, sell_val
    else:
        return sell_val, "VENDER MAT", total_crafts, profit_craft

# --- SIDEBAR: INPUTS GERAIS ---
with st.sidebar:
    st.header("1. Configuração de Mercado")
    bc_price = st.number_input("Preço Blue Crystal (95un)", value=14000, step=100)
    oreha_price = st.number_input("Preço Oreha (UNITÁRIO)", value=32.0, step=0.1)
    craft_cost = st.number_input("Custo Craft (Gold)", value=376, step=1)
    
    st.markdown("### 🪵 Preços Materiais (Pacote 100)")
    price_timber_100 = st.number_input("Timber (100un)", value=123)
    price_tender_100 = st.number_input("Tender (100un)", value=267)
    price_abidos_100 = st.number_input("Abidos (100un)", value=1450)
    
    tax_rate = 0.05 

    st.markdown("---")
    st.header("2. Seu Inventário Atual")
    qty_timber = st.number_input("Qtd Timber", value=5000, step=100)
    qty_tender = st.number_input("Qtd Tender", value=1000, step=100)
    qty_abidos = st.number_input("Qtd Abidos", value=200, step=10)

# --- PREPARAÇÃO DE DADOS GLOBAIS ---
u_timber = price_timber_100 / 100
u_tender = price_tender_100 / 100
u_abidos = price_abidos_100 / 100

# Custo da Energia (Gold)
cost_energy_small_unit = (bc_price / 95) * (230/10) # 23 BC/pote
cost_energy_large_unit = (bc_price / 95) * (330/15) # 22 BC/pote

# --- CÁLCULO INVENTÁRIO ATUAL (USANDO A FUNÇÃO) ---
best_profit_inv, decision_inv, total_crafts_inv, other_val_inv = calculate_optimized_revenue(
    qty_timber, qty_tender, qty_abidos, u_timber, u_tender, u_abidos, oreha_price, craft_cost, tax_rate
)

# --- FRONTEND PRINCIPAL ---

# Métricas do Inventário
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Lucro Potencial (Hoje)", f"{best_profit_inv:,.0f} g", delta=f"{best_profit_inv - other_val_inv:,.0f} vs outra opção")
with col2:
    st.metric("Melhor Ação", decision_inv)
with col3:
    st.metric("Crafts Totais", f"{total_crafts_inv}")
with col4:
    # Max BC Price baseado no inventário não faz tanto sentido quanto na experimentação, 
    # mas mantivemos a lógica de ROI baseada no custo unitário de energia
    roi_bc = (best_profit_inv / 22) * 95 if total_crafts_inv > 0 else 0 
    st.metric("Ref. Preço BC", f"{roi_bc:,.0f}", help="Valor meramente ilustrativo para o inventário atual.")
with col5:
    st.metric("Vale apena comprar poção de energia?", "✅ SIM" if roi_bc > bc_price else "❌ NÃO", help="Baseado no ROI estimado.")

st.markdown("---")

# Abas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparativo", "🏭 Detalhes Conversão", "⚖️ Arbitragem", "🧪 Laboratório (ROI)"])

with tab1:
    fig = go.Figure(data=[
        go.Bar(name='Venda Materiais', x=['Retorno Gold'], y=[other_val_inv if decision_inv == "CRAFTAR" else best_profit_inv], marker_color='#FFA07A'),
        go.Bar(name='Melhor Opção', x=['Retorno Gold'], y=[best_profit_inv], marker_color='#90EE90')
    ])
    fig.update_layout(title='Comparação: Otimização do Inventário', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.info("Esta aba mostra os detalhes matemáticos da aba 1 (Inventário).")
    # Recalculando apenas para display (ou poderia retornar da função se quisesse expandir)
    st.write("A lógica interna já converteu suas sobras de Timber/Tender em Pó e adicionou aos crafts totais mostrados acima.")

with tab3:
    st.subheader("Devo Converter ou Vender/Comprar?")
    c_arb1, c_arb2 = st.columns(2)
    
    val_10_abidos = 10 * u_abidos
    cost_conv_timber = (125 * u_timber) * (1 - tax_rate)
    cost_conv_tender = (62.5 * u_tender) * (1 - tax_rate)
    
    with c_arb1:
        st.markdown("**Timber:** " + ("✅ CONVERTER" if cost_conv_timber < val_10_abidos else "💲 VENDER/COMPRAR"))
        st.caption(f"Custo Conv: {cost_conv_timber:.0f}g vs Mercado: {val_10_abidos:.0f}g")
    with c_arb2:
        st.markdown("**Tender:** " + ("✅ CONVERTER" if cost_conv_tender < val_10_abidos else "💲 VENDER/COMPRAR"))
        st.caption(f"Custo Conv: {cost_conv_tender:.0f}g vs Mercado: {val_10_abidos:.0f}g")

# --- ABA 4: EXPERIMENTAÇÃO (A NOVIDADE) ---
with tab4:
    st.header("🔬 Análise de ROI (Experimentação)")
    st.markdown("Preencha aqui os dados de uma 'run' de teste (ex: gastando 10 potes) para saber o preço justo do cristal.")
    
    # Inputs da Experimentação (Separados do Inventário)
    c_exp1, c_exp2, c_exp3, c_exp4 = st.columns(4)
    with c_exp1:
        exp_pots = st.number_input("Potes Usados", value=10, step=1)
    with c_exp2:
        exp_timber = st.number_input("Timber Coletado", value=18011) # Valor padrão do seu CSV
    with c_exp3:
        exp_tender = st.number_input("Tender Coletado", value=3918)
    with c_exp4:
        exp_abidos = st.number_input("Abidos Coletado", value=1065)
        
    st.markdown("---")
    
    # Cálculos da Experimentação
    # Usamos a mesma função "inteligente" para descobrir quanto dinheiro esses materiais geram no melhor cenário
    exp_revenue, exp_strategy, exp_crafts, _ = calculate_optimized_revenue(
        exp_timber, exp_tender, exp_abidos, u_timber, u_tender, u_abidos, oreha_price, craft_cost, tax_rate
    )
    
    # Análise por Pote
    gold_per_pot = exp_revenue / exp_pots
    cost_per_pot_actual = cost_energy_large_unit # Custo atual baseado no BC de 14k
    profit_per_pot = gold_per_pot - cost_per_pot_actual
    
    # Break Even (Preço Justo)
    # Fórmula: (Ouro gerado por 1 pote / Custo em BC de 1 pote) * 95
    fair_value_small = (gold_per_pot / 23) * 95 # Pacote 10 (230 BC) = 23 BC/pote
    fair_value_large = (gold_per_pot / 22) * 95 # Pacote 15 (330 BC) = 22 BC/pote
    
    # Display dos Resultados da Experiência
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Receita Total (Run)", f"{exp_revenue:,.0f} g", help="Valor bruto gerado pelos materiais (Melhor cenário)")
    with m2:
        st.metric("Receita Média / Pote", f"{gold_per_pot:,.0f} g", help="Quanto cada pote gerou de ouro")
    with m3:
        if profit_per_pot > 0:
            st.success(f"Lucro Real: +{profit_per_pot:,.0f} g/pote")
        else:
            st.error(f"Prejuízo: {profit_per_pot:,.0f} g/pote")

    st.subheader("🏷️ Qual o preço justo do Blue Crystal?")
    st.caption("Se o preço do mercado estiver ABAIXO destes valores, vale a pena comprar o pacote.")

    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.markdown("#### Pacote Pequeno (10 un)")
        st.metric("Valor Justo (Break-even)", f"{fair_value_small:,.0f}", delta=f"{fair_value_small - bc_price:,.0f} Margem")
        if bc_price < fair_value_small:
            st.success("✅ COMPRA SEGURA")
        else:
            st.error("❌ NÃO COMPRE")
            
    with col_res2:
        st.markdown("#### Pacote Grande (15 un)")
        st.metric("Valor Justo (Break-even)", f"{fair_value_large:,.0f}", delta=f"{fair_value_large - bc_price:,.0f} Margem")
        if bc_price < fair_value_large:
            st.success("✅ COMPRA SEGURA")
        else:
            st.error("❌ NÃO COMPRE")
            
    st.info(f"""
    **Análise:**
    Com os materiais coletados, cada pote de energia rendeu **{gold_per_pot:,.0f} gold**.
    Considerando a eficiência do pacote grande (22 BC/pote), você poderia pagar até **{fair_value_large:,.0f} gold** no Blue Crystal e ainda sair no zero a zero.
    Como o mercado está **{bc_price:,.0f}**, você tem um lucro "infinito" comprando energia agora.
    """)