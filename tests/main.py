import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# ===== CONFIGURAÇÃO MOBILE =====
st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== CSS RESPONSIVO =====
st.markdown("""
<style>
/* Mobile First - Responsividade */
@media (max-width: 768px) {
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
    }
    
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
    }
    
    .stSelectbox > div > div {
        font-size: 1.1rem;
    }
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ===== FUNÇÕES PRINCIPAIS =====
@st.cache_data(ttl=300)  # Cache por 5 minutos
def buscar_dados_acao(ticker, periodo="1mo"):
    """Busca dados da ação"""
    try:
        acao = yf.Ticker(ticker)
        dados = acao.history(period=periodo)
        return dados
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return None

def criar_grafico_mobile(df, titulo="Gráfico"):
    """Cria gráfico otimizado para mobile"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Preço',
        line=dict(width=3, color='#1f77b4')
    ))
    
    fig.update_layout(
        title={
            'text': titulo,
            'x': 0.5,
            'font': {'size': 16}
        },
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="Preço (R$)",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# ===== LAYOUT PRINCIPAL =====
def main():
    # Header
    st.markdown("# 📈 Dashboard Financeiro")
    st.markdown("*Análise de ações em tempo real - Mobile Friendly*")
    
    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("# ⚙️ Configurações")
        
        # Ações favoritas
        st.markdown("### 🎯 Ações Favoritas")
        acoes_disponiveis = [
            "PETR4.SA", "VALE3.SA", "ITUB4.SA", 
            "BBDC4.SA", "ABEV3.SA", "MGLU3.SA"
        ]
        
        favoritas = st.multiselect(
            "Selecione:",
            acoes_disponiveis,
            default=["PETR4.SA", "VALE3.SA"]
        )
        
        # Período de análise
        st.markdown("### ⏰ Período")
        periodo = st.selectbox(
            "Análise:",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            format_func=lambda x: {
                "1d": "1 dia",
                "5d": "5 dias", 
                "1mo": "1 mês",
                "3mo": "3 meses",
                "6mo": "6 meses",
                "1y": "1 ano"
            }[x]
        )
        
        # Botão de atualização
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # ===== CONTEÚDO PRINCIPAL =====
    
    # Seleção de ação principal
    st.markdown("## 🎯 Análise de Ação")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        acao_selecionada = st.selectbox(
            "Escolha uma ação para análise:",
            acoes_disponiveis,
            key="acao_principal"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Analisar"):
            st.session_state.analisar = True
    
    # Buscar e exibir dados
    if acao_selecionada:
        with st.spinner("🔍 Buscando dados..."):
            dados = buscar_dados_acao(acao_selecionada, periodo)
        
        if dados is not None and not dados.empty:
            # Calcular métricas
            preco_atual = dados['Close'].iloc[-1]
            preco_anterior = dados['Close'].iloc[-2] if len(dados) > 1 else preco_atual
            variacao = preco_atual - preco_anterior
            variacao_pct = (variacao / preco_anterior) * 100
            
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="💰 Preço Atual",
                    value=f"R$ {preco_atual:.2f}",
                    delta=f"R$ {variacao:.2f}"
                )
            
            with col2:
                st.metric(
                    label="�� Variação %",
                    value=f"{variacao_pct:.2f}%",
                    delta=f"{variacao_pct:.2f}%"
                )
            
            with col3:
                volume = dados['Volume'].iloc[-1]
                st.metric(
                    label="📈 Volume",
                    value=f"{volume:,.0f}",
                    delta="Último dia"
                )
            
            # Gráfico principal
            st.markdown("### 📈 Gráfico de Preços")
            fig = criar_grafico_mobile(dados, f"{acao_selecionada} - {periodo}")
            st.plotly_chart(fig, use_container_width=True)
            
            # Dados resumidos
            st.markdown("### 📋 Resumo dos Dados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔢 Estatísticas:**")
                st.write(f"• **Máxima:** R$ {dados['High'].max():.2f}")
                st.write(f"• **Mínima:** R$ {dados['Low'].min():.2f}")
                st.write(f"• **Média:** R$ {dados['Close'].mean():.2f}")
            
            with col2:
                st.markdown("**📊 Últimos 5 dias:**")
                ultimos_dados = dados[['Close', 'Volume']].tail(5)
                st.dataframe(
                    ultimos_dados.round(2),
                    use_container_width=True
                )
        
        else:
            st.error("❌ Não foi possível carregar os dados da ação.")
    
    # ===== SEÇÃO DE FAVORITAS =====
    if favoritas:
        st.markdown("## ⭐ Suas Ações Favoritas")
        
        # Criar colunas responsivas para favoritas
        num_cols = min(len(favoritas), 3)
        cols = st.columns(num_cols)
        
        for i, acao in enumerate(favoritas):
            with cols[i % num_cols]:
                dados_fav = buscar_dados_acao(acao, "1d")
                if dados_fav is not None and not dados_fav.empty:
                    preco = dados_fav['Close'].iloc[-1]
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>{acao}</h4>
                        <h2>R$ {preco:.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("*📱 Dashboard otimizado para mobile | Dados via Yahoo Finance*")

# ===== EXECUTAR APP =====
if __name__ == "__main__":
    main()
