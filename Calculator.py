import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lost Ark Calculator - Oreha", layout="wide")

st.title("⚒️ Calculadora Expert de Oreha (Lost Ark)")
st.markdown("---")

# --- SIDEBAR: INPUTS (Entrada de Dados) ---
with st.sidebar:
    st.header("1. Configuração de Mercado")
    
    # Preços Blue Crystal e Energia
    bc_price = st.number_input("Preço Blue Crystal (95un)", value=14000, step=100)
    oreha_price = st.number_input("Preço Oreha (UNITÁRIO)", value=32.0, step=0.1, help="Preço de 1 unidade, não do pacote de 10.")
    craft_cost = st.number_input("Custo Craft (Gold)", value=376, step=1)
    
    st.markdown("### 🪵 Preços de Materiais (Pacotes de 100)")
    price_timber_100 = st.number_input("Timber (100un)", value=123)
    price_tender_100 = st.number_input("Tender Timber (100un)", value=267)
    price_abidos_100 = st.number_input("Abidos Timber (100un)", value=1450)
    
    tax_rate = 0.05 # 5% fixo

    st.markdown("---")
    st.header("2. Sua Coleta (Inventário)")
    qty_timber = st.number_input("Qtd Timber", value=5000, step=100)
    qty_tender = st.number_input("Qtd Tender", value=1000, step=100)
    qty_abidos = st.number_input("Qtd Abidos", value=200, step=10)

# --- CÁLCULOS PRINCIPAIS (BACKEND) ---

# 1. Custo da Energia
# Pacote Pequeno: 230 BC por 10 potes = 23 BC/pote
cost_energy_small = (bc_price / 95) * 23
# Pacote Grande: 330 BC por 15 potes = 22 BC/pote (Melhor)
cost_energy_large = (bc_price / 95) * 22

# 2. Preços Unitários Reais (Base para cálculos)
u_timber = price_timber_100 / 100
u_tender = price_tender_100 / 100
u_abidos = price_abidos_100 / 100

# 3. Cenário A: Venda de Materiais Brutos (Considerando Lotes de 100)
# Só vende o que tem em pacotes fechados de 100
sell_timber = (int(qty_timber / 100) * 100) * u_timber
sell_tender = (int(qty_tender / 100) * 100) * u_tender
sell_abidos = (int(qty_abidos / 100) * 100) * u_abidos

total_sell_raw = (sell_timber + sell_tender + sell_abidos) * (1 - tax_rate)

# 4. Cenário B: Craft Otimizado (Com Conversão de Sobras)
# Passo 4.1: Crafts Base (Limitado pelo menor recurso)
crafts_base = int(min(qty_timber / 86, qty_tender / 45, qty_abidos / 33))

# Passo 4.2: Calcular Sobras após crafts base
rem_timber = qty_timber - (crafts_base * 86)
rem_tender = qty_tender - (crafts_base * 45)
# Abidos sobra quase zero ou o que não deu pra fechar o lote de 33

# Passo 4.3: Conversão de Pó (Regra de Lotes: 100 Timber->80 Pó / 50 Tender->80 Pó)
powder_from_timber = int(rem_timber / 100) * 80
powder_from_tender = int(rem_tender / 50) * 80
total_powder = powder_from_timber + powder_from_tender

# Passo 4.4: Novos Abidos gerados (100 Pó -> 10 Abidos)
new_abidos = int(total_powder / 100) * 10

# Passo 4.5: Crafts Extras (Assumindo Timber/Tender suficientes para acompanhar, pois sobram muito)
crafts_extra = int(new_abidos / 33)

total_crafts = crafts_base + crafts_extra

# Receita e Custos do Craft
# 1 Craft = 10 Orehas
revenue_oreha = (total_crafts * 10 * oreha_price) * (1 - tax_rate)
cost_gold_craft = total_crafts * craft_cost

# Lucro Craft (Ignorando custo energia por enquanto para comparar com venda bruta)
profit_craft_operational = revenue_oreha - cost_gold_craft

# 5. Decisão de Arbitragem (Conversão vs Venda)
# Custo de oportunidade para gerar 10 Abidos (que custam 10 * u_abidos no mkt)
market_val_10_abidos = 10 * u_abidos

# Via Timber: Precisa de 125 Timber (1.25 pacotes de 100)
cost_conv_timber = (125 * u_timber) * (1 - tax_rate) 
# Via Tender: Precisa de 62.5 Tender (0.625 pacotes de 100)
cost_conv_tender = (62.5 * u_tender) * (1 - tax_rate)

# Decisões
decision_timber = "CONVERTER ✅" if cost_conv_timber < market_val_10_abidos else "VENDER E COMPRAR 💲"
decision_tender = "CONVERTER ✅" if cost_conv_tender < market_val_10_abidos else "VENDER E COMPRAR 💲"

# 6. Max Bid Blue Crystal
# Pega o melhor cenário (Venda Bruta ou Craft) e divide pelo custo em BC da energia (22 BC)
best_return = max(total_sell_raw, profit_craft_operational)
max_bc_price = (best_return / 22) * 95 # 22 é o custo em BC de 1 pote no pacote grande


# --- LAYOUT PRINCIPAL (FRONTEND) ---

# Métricas Principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Lucro Líquido (Craft)", f"{profit_craft_operational:,.0f} g", delta=f"{profit_craft_operational - total_sell_raw:,.0f} vs Venda")
with col2:
    st.metric("Melhor Decisão", "CRAFTAR" if profit_craft_operational > total_sell_raw else "VENDER MAT")
with col3:
    st.metric("Crafts Totais", f"{total_crafts}", help=f"Base: {crafts_base} + Extras Conversão: {crafts_extra}")
with col4:
    st.metric("Max Pagar no BC", f"{max_bc_price:,.0f}", delta=f"{max_bc_price - bc_price:,.0f} Margem")

st.markdown("---")

# Abas de Análise
tab1, tab2, tab3 = st.tabs(["📊 Comparativo Visual", "🏭 Detalhes da Conversão", "⚖️ Arbitragem de Mercado"])

with tab1:
    # Gráfico de Barras comparando Venda vs Craft
    fig = go.Figure(data=[
        go.Bar(name='Venda Materiais', x=['Retorno Gold'], y=[total_sell_raw], marker_color='#FFA07A'),
        go.Bar(name='Craft Otimizado', x=['Retorno Gold'], y=[profit_craft_operational], marker_color='#90EE90')
    ])
    fig.update_layout(title='Comparação: Vender Bruto vs Craftar (Otimizado)', barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"**Custo da Energia:** {cost_energy_large:,.0f} gold (Baseado no pacote de 330 BC). Esse valor deve ser descontado do lucro acima para saber o dinheiro real no bolso.")

with tab2:
    st.subheader("Otimização de Sobras (NPC Exchange)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Sobras Iniciais:**")
        st.write(f"Timber: {rem_timber:,.0f}")
        st.write(f"Tender: {rem_tender:,.0f}")
    with c2:
        st.write(f"**Conversão Intermediária:**")
        st.write(f"Pó Gerado: {total_powder:,.0f}")
        st.write(f"Novos Abidos: {new_abidos:,.0f}")
    with c3:
        st.success(f"**Ganho Real:** +{crafts_extra} Crafts Extras")
        
    st.caption("*O cálculo respeita os lotes mínimos de troca (100 Timber -> 80 Pó / 50 Tender -> 80 Pó).")

with tab3:
    st.subheader("Devo Converter ou Vender e Comprar?")
    st.write("Esta análise verifica se queimar madeira no NPC sai mais barato do que comprar Abidos pronto.")
    
    col_arb1, col_arb2 = st.columns(2)
    
    with col_arb1:
        st.markdown("#### Timber (Madeira Comum)")
        st.write(f"Custo Oportunidade (Vender): **{cost_conv_timber:.1f}g**")
        st.write(f"Valor 10 Abidos (Comprar): **{market_val_10_abidos:.1f}g**")
        if decision_timber == "CONVERTER ✅":
            st.success(f"Decisão: **{decision_timber}**")
        else:
            st.warning(f"Decisão: **{decision_timber}**")
            
    with col_arb2:
        st.markdown("#### Tender (Madeira Incomum)")
        st.write(f"Custo Oportunidade (Vender): **{cost_conv_tender:.1f}g**")
        st.write(f"Valor 10 Abidos (Comprar): **{market_val_10_abidos:.1f}g**")
        if decision_tender == "CONVERTER ✅":
            st.success(f"Decisão: **{decision_tender}**")
        else:
            st.warning(f"Decisão: **{decision_tender}**")

    st.markdown("---")
    st.subheader("Vale a pena comprar Materiais para Craftar?")
    
    # Custo para comprar mat para 1 craft
    cost_buy_mats = (86 * u_timber) + (45 * u_tender) + (33 * u_abidos)
    total_cost_buy_craft = cost_buy_mats + craft_cost
    revenue_1_craft = (10 * oreha_price) * (1 - tax_rate)
    profit_buy_craft = revenue_1_craft - total_cost_buy_craft
    
    st.write(f"Custo para fazer 1 Craft (Comprando tudo): **{total_cost_buy_craft:,.1f}g**")
    st.write(f"Receita Líquida de 1 Craft (10 Orehas): **{revenue_1_craft:,.1f}g**")
    
    if profit_buy_craft > 0:
        st.success(f"**SIM! Lucro de {profit_buy_craft:.1f}g por unidade de crafting.** COMPRE TUDO AGORA!")
    else:
        st.error(f"**NÃO.** Prejuízo de {profit_buy_craft:.1f}g se comprar materiais.")