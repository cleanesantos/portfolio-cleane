import streamlit as st
import pandas as pd
import plotly.express as px

# ========== CONFIGURAÇÃO ==========
st.set_page_config(layout="wide", page_title="Tesouro Direto")

# ========== ESTILO SIMPLIFICADO ==========
st.markdown("""
    <style>
        .stApp {
            background-color: #F6F9FF;
        }

        section.main > div {
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# ========== CORES ==========
paleta = ["#0B6970", "#FAB90B", "#E66C37", "#21457E", "#73933C"]

def formatar_valor(valor):
    if valor >= 1_000_000_000:
        return f"{valor/1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"{valor/1_000_000:.2f}M"
    else:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_brasileiro(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ========== DADOS ==========
url = "https://www.tesourotransparente.gov.br/ckan/dataset/f0468ecc-ae97-4287-89c2-6d8139fb4343/resource/e5f90e3a-8f8d-4895-9c56-4bb2f7877920/download/VendasTesouroDireto.csv"
df = pd.read_csv(url, sep=";", encoding="latin1")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("+", "mais")
df["data_venda"] = pd.to_datetime(df["data_venda"], dayfirst=True, errors='coerce')
df["vencimento_do_titulo"] = pd.to_datetime(df["vencimento_do_titulo"], dayfirst=True, errors='coerce')
df["pu"] = df["pu"].astype(str).str.replace(",", ".").astype(float)
df["quantidade"] = df["quantidade"].astype(str).str.replace(",", ".").astype(float)
df["valor"] = df["valor"].astype(str).str.replace(",", ".").astype(float)


# ========== TÍTULO ==========
st.title("📊 Análise de Investimentos no Tesouro Direto")
st.markdown("##### Este painel interativo apresenta uma visão exploratória das vendas de títulos públicos federais.")


# ========== FILTROS ==========
col1, col2, col3 = st.columns(3)
tipo = col1.selectbox("Tipo de Título", ["Todos"] + sorted(df["tipo_titulo"].unique()))
ano = col2.selectbox("Ano de Vencimento", ["Todos"] + sorted(df["vencimento_do_titulo"].dt.year.dropna().astype(int).unique().astype(str)))
periodo_venda = col3.date_input(
    "Período da Venda",
    value=(df["data_venda"].min(), df["data_venda"].max())
)


# ========== FILTRAGEM ==========
filtro = df.copy()
if tipo != "Todos":
    filtro = filtro[filtro["tipo_titulo"] == tipo]
if ano != "Todos":
    filtro = filtro[filtro["vencimento_do_titulo"].dt.year == int(ano)]
if periodo_venda:
    data_inicio, data_fim = periodo_venda
    filtro = filtro[(filtro["data_venda"] >= pd.to_datetime(data_inicio)) &
                    (filtro["data_venda"] <= pd.to_datetime(data_fim))]


# ========== MÉTRICAS ==========
col4, col5, col6, col7 = st.columns(4)
col4.metric("💰 Valor Total Vendido (R$)", f"{filtro['valor'].sum():,.2f}")
col5.metric("📦 Total de Títulos", f"{filtro['quantidade'].sum():,.0f}")
col6.metric("📈 PU Médio", f"{filtro['pu'].mean():,.2f}")
col7.metric("🧮 Qtd. Média por Venda", f"{filtro['quantidade'].mean():,.2f}")

# ========== GRÁFICOS ==========
col8, col9 = st.columns(2)

with col8:
    df_bar = filtro.groupby("tipo_titulo")["valor"].sum().reset_index()
    df_bar.columns = ["Tipo de Título", "Valor"]
    df_bar["Tipo de Título"] = df_bar["Tipo de Título"].str.replace(" ", "<br>")

    df_bar["Rótulo"] = df_bar["Valor"].apply(formatar_valor)
    df_bar["Hover"] = df_bar["Valor"].apply(formatar_brasileiro)

    fig1 = px.bar(
        df_bar,
        x="Tipo de Título",
        y="Valor",
        text="Rótulo",
        color_discrete_sequence=paleta,
        title="Valor por Tipo de Título"
    )

    fig1.update_traces(
        textposition='auto',
        textfont=dict(color='black'),
        marker_line_width=0,
        hovertemplate='%{x}<br>R$ %{customdata}<extra></extra>',
        customdata=df_bar[["Hover"]]
    )

    fig1.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="Valor",
        xaxis_title="Tipo de Título",
        hoverlabel=dict(
            bgcolor="#F0F0F0",
            font_size=12,
            font_color="black"
        ),
        margin=dict(t=80, b=100)
    )

    st.plotly_chart(fig1, use_container_width=True)
with col9:
    df_pie = filtro.groupby("tipo_titulo")["valor"].sum().reset_index()
    df_pie.columns = ["Tipo de Título", "Valor"]
    df_pie["Label"] = df_pie["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    fig2 = px.pie(
        df_pie,
        names="Tipo de Título",
        values="Valor",
        hole=0.4,
        title="Distribuição por Tipo",
        color_discrete_sequence=paleta
    )

    fig2.update_traces(
        textposition="outside",
        textinfo="percent",
        hovertemplate="%{label}<br>Valor: %{customdata}<extra></extra>",
        customdata=df_pie[["Label"]],
        textfont_size=13
    )

    fig2.update_layout(
        showlegend=True,
        hoverlabel=dict(
            bgcolor="#F0F0F0",
            font_size=12,
            font_color="black"
        )
    )

    st.plotly_chart(fig2, use_container_width=True)

col10, col11 = st.columns(2)

with col10:
    df_venc = filtro.groupby(filtro["vencimento_do_titulo"].dt.year)["valor"].sum().reset_index()
    df_venc.columns = ["Ano de Vencimento", "Valor"]
    df_venc["Hover"] = df_venc["Valor"].apply(formatar_brasileiro)

    fig3 = px.bar(df_venc, x="Ano de Vencimento", y="Valor", title="Valor por Ano de Vencimento",
                  color_discrete_sequence=paleta)

    fig3.update_traces(
        hovertemplate="Ano: %{x}<br>Valor: %{customdata}<extra></extra>",
        customdata=df_venc[["Hover"]],
    )

    st.plotly_chart(fig3, use_container_width=True)

with col11:
    df_evol = filtro.groupby("data_venda")["valor"].sum().reset_index()
    df_evol.columns = ["Data da Venda", "Valor"]
    df_evol["Hover"] = df_evol["Valor"].apply(formatar_brasileiro)

    fig4 = px.line(df_evol, x="Data da Venda", y="Valor", title="Evolução Temporal das Vendas")

    fig4.update_traces(
        hovertemplate="Data da Venda: %{x|%b %Y}<br>Valor: %{customdata}<extra></extra>",
        customdata=df_evol[["Hover"]],
        line=dict(color=paleta[0], width=2)
    )

    st.plotly_chart(fig4, use_container_width=True)

# ========== TABELA ==========
# Renomear colunas
filtro_renomeado = filtro.rename(columns={
    "tipo_titulo": "Tipo de Título",
    "vencimento_do_titulo": "Data de Vencimento",
    "data_venda": "Data da Venda",
    "pu": "PU (Preço Unitário)",
    "quantidade": "Quantidade Vendida",
    "valor": "Valor Total (R$)"
})

# Exibir tabela
st.subheader("📄 Tabela Detalhada dos Investimentos")
st.dataframe(filtro_renomeado)

# Botão de download
st.download_button(
    "📥 Baixar CSV filtrado",
    filtro_renomeado.to_csv(index=False, sep=";", decimal=","),
    "dados_filtrados.csv",
    "text/csv"
)


# ========== RODAPÉ ==========

st.markdown("---")
st.markdown(
    '<div style="text-align: center; font-size: 14px;">'
    'Desenvolvido por <a href="https://www.linkedin.com/in/cleannesantos/" target="_blank">Cleane Santos</a> • '
    'Dados: Tesouro Direto • Ferramentas: Python, Streamlit e Plotly'
    '</div>',
    unsafe_allow_html=True
)
