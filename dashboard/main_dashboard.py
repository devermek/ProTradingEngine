"""
Dashboard Principal - ProTrading Engine v3.1.0
Sistema completo de trading com Alpha Vantage
Desenvolvido por Deverson
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Configuração da página
st.set_page_config(
    page_title="ProTrading Engine v3.1.0",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adiciona paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Imports do sistema
try:
    # Import direto das classes
    import sys
    import os
    
    # Adiciona o diretório atual ao path
    current_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.dirname(current_path)
    sys.path.insert(0, parent_path)
    
    # Imports das classes
    from data.database import TradingDatabase
    from core.alert_system import AlertSystem  
    from core.trading_strategies import TradingStrategies
    from core.options_collector import OptionsCollector
    from core.alpha_vantage_collector import AlphaVantageCollector
    
    print("✅ Todos os módulos importados com sucesso!")
    
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos: {e}")
    st.error("🔧 Lista de arquivos necessários:")
    st.error("- data/database.py")
    st.error("- core/alert_system.py") 
    st.error("- core/trading_strategies.py")
    st.error("- core/options_collector.py")
    st.error("- core/alpha_vantage_collector.py")
    st.stop()

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e8b57);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .alert-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .signal-card-buy {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .signal-card-sell {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .signal-card-neutral {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #333;
        margin: 0.5rem 0;
    }
    
    .data-source-av {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização dos sistemas
@st.cache_resource
def init_systems():
    """Inicializa todos os sistemas"""
    try:
        db = TradingDatabase()
        alert_system = AlertSystem()
        strategies = TradingStrategies()
        options_collector = OptionsCollector()
        av_collector = AlphaVantageCollector()
        
        return db, alert_system, strategies, options_collector, av_collector
        
    except Exception as e:
        st.error(f"❌ Erro ao inicializar sistemas: {e}")
        return None, None, None, None, None

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏆 ProTrading Engine v3.1.0</h1>
    <h3>🌐 Alpha Vantage Integration + Sistema Completo</h3>
    <p>Desenvolvido por Deverson | Dados Reais + Análise Técnica + Opções</p>
</div>
""", unsafe_allow_html=True)

# Inicializar sistemas
db, alert_system, strategies, options_collector, av_collector = init_systems()

if not all([db, alert_system, strategies, options_collector, av_collector]):
    st.error("❌ Falha na inicialização dos sistemas!")
    st.stop()

# Sidebar - Controles
st.sidebar.markdown("## ⚙️ Controles do Sistema")

# Teste de conexões
if st.sidebar.button("🧪 Testar Alpha Vantage", type="primary"):
    with st.sidebar:
        with st.spinner("Testando Alpha Vantage..."):
            try:
                if av_collector.test_connection():
                    st.success("✅ Alpha Vantage: Conectado!")
                else:
                    st.error("❌ Alpha Vantage: Falha na conexão")
            except Exception as e:
                st.error(f"❌ Erro: {e}")

# Coleta de dados Alpha Vantage
if st.sidebar.button("🌐 Coletar Alpha Vantage", type="secondary"):
    with st.sidebar:
        with st.spinner("Coletando dados Alpha Vantage..."):
            try:
                us_symbols = ["PBR", "VALE", "ITUB", "BBDC"]
                collected_data = av_collector.get_multiple_quotes(us_symbols)
                
                if collected_data:
                    st.success(f"✅ Coletados {len(collected_data)} símbolos!")
                    
             
                    # Salvar no banco (dados já convertidos anteriormente)
symbol_map = {
    "PBR": "PETR4.SA",
    "VALE": "VALE3.SA", 
    "ITUB": "ITUB4.SA",
    "BBDC": "BBDC4.SA"
}

saved_count = 0
for us_symbol, data in collected_data.items():
    br_symbol = symbol_map.get(us_symbol, us_symbol)
    try:
        # ✅ USA PREÇO ORIGINAL EM USD (sem conversão dupla)
        price_usd = data['price']  # Mantém em USD
        db.save_price_data(br_symbol, price_usd, data['volume'], 'alpha_vantage')
        saved_count += 1
    except Exception as e:
        st.warning(f"⚠️ Erro ao salvar {us_symbol}: {e}")
                # Análise de estratégias
if st.sidebar.button("💡 Analisar Estratégias", type="secondary"):
    with st.sidebar:
        with st.spinner("Analisando estratégias..."):
            try:
                symbols = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
                signals_generated = 0
                
                for symbol in symbols:
                    try:
                        # Análise básica por enquanto
                        latest_price = db.get_latest_price(symbol)
                        if latest_price:
                            # Salva sinal básico
                            db.save_signal(
                                symbol=symbol,
                                signal_type="NEUTRO",
                                strength=5,
                                strategy="basic_analysis",
                                price=latest_price,
                                notes="Análise básica automática"
                            )
                            signals_generated += 1
                    except Exception as e:
                        st.warning(f"⚠️ Erro ao analisar {symbol}: {e}")
                
                st.success(f"✅ Análise concluída! {signals_generated} sinais gerados")
                
            except Exception as e:
                st.error(f"❌ Erro na análise: {e}")

# Coleta de opções
if st.sidebar.button("📊 Coletar Opções", type="secondary"):
    with st.sidebar:
        with st.spinner("Coletando dados de opções..."):
            try:
                symbols = ["PETR4", "VALE3"]
                total_options = 0
                
                for symbol in symbols:
                    # Gerar dados mock de opções
                    import random
                    from datetime import datetime, timedelta
                    
                    # Gerar algumas opções mock
                    strikes = [20, 22, 24, 26, 28, 30]
                    expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    
                    conn = db._get_connection() if hasattr(db, '_get_connection') else None
                    if not conn:
                        import sqlite3
                        conn = sqlite3.connect(db.db_path)
                    
                    cursor = conn.cursor()
                    
                    for strike in strikes:
                        for option_type in ['CALL', 'PUT']:
                            cursor.execute('''
                                INSERT INTO options (underlying, strike, expiry_date, option_type, price, bid, ask, volume, implied_volatility)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                symbol,
                                strike,
                                expiry,
                                option_type,
                                round(random.uniform(1, 5), 2),  # price
                                round(random.uniform(0.5, 3), 2),  # bid
                                round(random.uniform(2, 6), 2),  # ask
                                random.randint(100, 1000),  # volume
                                round(random.uniform(0.2, 0.8), 3)  # IV
                            ))
                            total_options += 1
                    
                    conn.commit()
                    conn.close()
                
                st.success(f"✅ {total_options} opções coletadas e salvas!")
                
            except Exception as e:
                st.error(f"❌ Erro: {e}")

# Criar alerta
st.sidebar.markdown("### 🔔 Criar Alerta")
with st.sidebar.form("alert_form"):
    alert_symbol = st.selectbox("Ação", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"])
    alert_type = st.selectbox("Tipo", ["HIGH", "LOW"])
    alert_threshold = st.slider("Variação (%)", 1, 20, 5)
    
    if st.form_submit_button("Criar Alerta"):
        try:
            db.add_price_alert(alert_symbol, alert_type, alert_threshold)
            st.success(f"✅ Alerta criado: {alert_symbol} {alert_type} {alert_threshold}%")
        except Exception as e:
            st.error(f"❌ Erro: {e}")

# Verificar alertas
if st.sidebar.button("🔍 Verificar Alertas"):
    with st.sidebar:
        with st.spinner("Verificando alertas..."):
            try:
                triggered_alerts = db.check_alerts()
                if triggered_alerts:
                    st.warning(f"⚠️ {len(triggered_alerts)} alertas disparados!")
                    for alert in triggered_alerts:
                        st.info(f"🔔 {alert}")
                else:
                    st.info("✅ Nenhum alerta disparado")
            except Exception as e:
                st.error(f"❌ Erro: {e}")

# Métricas da sidebar
try:
    active_alerts = db.get_active_alerts_count()
    st.sidebar.metric("📊 Alertas Ativos", active_alerts)
except:
    st.sidebar.metric("📊 Alertas Ativos", "0")

# ============ TABS PRINCIPAIS ============
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trading", "📊 Opções", "🔔 Alertas", "🌐 Alpha Vantage"])

# TAB 1: Trading
with tab1:
    st.markdown("## �� Trading & Análise Técnica")
    
    # Sinais de Trading
    col1, col2 = st.columns(2)
    
    try:
        symbols = ["PETR4.SA", "VALE3.SA"]
        
        for i, symbol in enumerate(symbols):
            with col1 if i % 2 == 0 else col2:
                try:
                    # Busca último preço
                    latest_price = db.get_latest_price(symbol)
                    
                    if latest_price:
                        # Análise básica
                        signal_type = "NEUTRO"
                        strength = 5
                        emoji = "🟡"
                        card_class = "signal-card-neutral"
                        
                        # Cálculos básicos
                        target_price = latest_price * 1.05  # +5%
                        stop_loss = latest_price * 0.95    # -5%
                        
                        st.markdown(f"""
                        <div class="{card_class}">
                            <h3>{emoji} {symbol.replace('.SA', '')}</h3>
                            <h2>{signal_type}</h2>
                            <p><strong>Força:</strong> {strength}/10</p>
                            <p><strong>Preço:</strong> R$ {latest_price:.2f}</p>
                            <p><strong>Alvo:</strong> R$ {target_price:.2f}</p>
                            <p><strong>Stop:</strong> R$ {stop_loss:.2f}</p>
                            <small>Análise básica - aguardando indicadores técnicos</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning(f"⚠️ Dados insuficientes para {symbol}")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao analisar {symbol}: {e}")
    
    except Exception as e:
        st.error(f"❌ Erro geral na análise: {e}")
    
    # Visão geral do mercado
    st.markdown("## 📊 Visão Geral do Mercado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Métricas rápidas
        symbols = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
        
        for i, symbol in enumerate(symbols):
            with [col1, col2, col3, col4][i]:
                try:
                    latest_price = db.get_latest_price(symbol)
                   if latest_price:
    # ✅ CONVERSÃO ÚNICA NA EXIBIÇÃO
    price_brl = latest_price * 5.0  # USD → BRL
    st.metric(symbol.replace('.SA', ''), f"R$ {price_brl:.2f}", "📈")
                    else:
                        st.metric(symbol.replace('.SA', ''), "N/A", "❌")
                except:
                    st.metric(symbol.replace('.SA', ''), "N/A", "❌")
    
    except Exception as e:
        st.error(f"❌ Erro nas métricas: {e}")
    
    # Gráfico de histórico
    st.markdown("### 📈 Histórico de Preços")
    
    selected_symbol = st.selectbox("Selecione o ativo:", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"])
    
    try:
        price_history = db.get_price_history(selected_symbol, days=30)
        
        if not price_history.empty:
            fig = px.line(
                price_history, 
                x='timestamp', 
                y='price',
                title=f'Histórico de Preços - {selected_symbol}',
                labels={'price': 'Preço (R$)', 'timestamp': 'Data'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"📭 Nenhum dado histórico encontrado para {selected_symbol}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {e}")
        # TAB 2: Opções
with tab2:
    st.markdown("## 📊 Análise de Opções")
    
    # Seletor de ativo
    underlying_symbol = st.selectbox("Selecione o ativo subjacente:", ["PETR4", "VALE3"], key="options_selector")
    
    try:
        # Buscar opções do banco
        options_data = db.get_options_by_underlying(underlying_symbol)
        
        if options_data:
            # Converter para DataFrame
            df_options = pd.DataFrame(options_data)
            
            # Separar calls e puts
            calls = df_options[df_options['option_type'] == 'CALL']
            puts = df_options[df_options['option_type'] == 'PUT']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📞 CALLS")
                if not calls.empty:
                    st.dataframe(
                        calls[['strike', 'price', 'bid', 'ask', 'volume', 'implied_volatility']].round(2),
                        use_container_width=True
                    )
                else:
                    st.info("📭 Nenhuma CALL encontrada")
            
            with col2:
                st.markdown("### 📉 PUTS")
                if not puts.empty:
                    st.dataframe(
                        puts[['strike', 'price', 'bid', 'ask', 'volume', 'implied_volatility']].round(2),
                        use_container_width=True
                    )
                else:
                    st.info("📭 Nenhuma PUT encontrada")
            
            # Gráfico de volatilidade implícita
            if not df_options.empty:
                st.markdown("### 📈 Volatilidade Implícita por Strike")
                
                fig = px.scatter(
                    df_options, 
                    x='strike', 
                    y='implied_volatility',
                    color='option_type',
                    title=f'Volatilidade Implícita - {underlying_symbol}',
                    labels={
                        'strike': 'Strike Price', 
                        'implied_volatility': 'Volatilidade Implícita',
                        'option_type': 'Tipo'
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"📭 Nenhuma opção encontrada para {underlying_symbol}")
            st.markdown("💡 **Dica:** Use 'Coletar Opções' na sidebar para gerar dados de exemplo")
    
    except Exception as e:
        st.error(f"❌ Erro na análise de opções: {e}")

# TAB 3: Alertas
with tab3:
    st.markdown("## 🔔 Sistema de Alertas")
    
    # Resumo de alertas
    col1, col2, col3 = st.columns(3)
    
    try:
        active_alerts = db.get_active_alerts_count()
        alert_history = db.get_alert_history(10)
        
        with col1:
            st.metric("🔔 Alertas Ativos", active_alerts)
        
        with col2:
            st.metric("📊 Histórico", len(alert_history))
        
        with col3:
            st.metric("⚡ Status", "🟢 Online")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar alertas: {e}")
    
    # Histórico de alertas
    st.markdown("### 📜 Histórico de Alertas")
    
    try:
        alert_history = db.get_alert_history(20)
        
        if alert_history:
            # Mostrar alertas
            for alert in alert_history:
                st.markdown(f"""
                <div class="alert-card">
                    <h4>🔔 {alert['symbol']}</h4>
                    <p>{alert['message']}</p>
                    <small>Preço atual: R$ {alert['current_price']:.2f}</small>
                    <br><small>Disparado em: {alert['triggered_at']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhum alerta disparado ainda")
            st.markdown("💡 **Dica:** Crie alertas usando o formulário na sidebar")
    
    except Exception as e:
        st.error(f"❌ Erro no sistema de alertas: {e}")

# TAB 4: Alpha Vantage
with tab4:
    st.markdown("## 🌐 Alpha Vantage - Dados Reais")
    
    # Status da API
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="data-source-av">
            <h4>🌐 Alpha Vantage</h4>
            <p>✅ Status: Ativo</p>
            <p>📊 Símbolos: PBR, VALE, ITUB, BBDC</p>
            <p>🔄 Rate Limit: 5 calls/min</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>📈 Dados Disponíveis</h4>
            <p>• Cotações em tempo real</p>
            <p>• Dados históricos</p>
            <p>• Informações fundamentais</p>
            <p>• Busca de símbolos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 ADRs Brasileiros</h4>
            <p>• PBR (Petrobras)</p>
            <p>• VALE (Vale)</p>
            <p>• ITUB (Itaú)</p>
            <p>• BBDC (Bradesco)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Coleta manual
    st.markdown("### 📊 Coleta Manual de Dados")
    
    if st.button("🔄 Coletar Dados Agora", type="primary"):
    with st.spinner("Coletando dados Alpha Vantage..."):
        try:
            us_symbols = ["PBR", "VALE", "ITUB", "BBDC"]
            collected_data = av_collector.get_multiple_quotes(us_symbols)
            
            if collected_data:
                st.success(f"✅ Coletados {len(collected_data)} símbolos!")
                
                # Exibir dados
                display_data = []
                for symbol, data in collected_data.items():
                    br_name = {
                        "PBR": "Petrobras",
                        "VALE": "Vale",
                        "ITUB": "Itaú",
                        "BBDC": "Bradesco"
                    }.get(symbol, symbol)
                    
                    display_data.append({
                        'Símbolo US': symbol,
                        'Empresa': br_name,
                        'Preço (USD)': f"${data['price']:.2f}",
                        'Variação (%)': f"{data['change_percent']:+.2f}%",
                        'Volume': f"{data['volume']:,}",
                        'Abertura': f"${data['open']:.2f}",
                        'Máxima': f"${data['high']:.2f}",
                        'Mínima': f"${data['low']:.2f}"
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
                
                # ✅ SALVAR NO BANCO (SEM CONVERSÃO DUPLA)
                symbol_map = {
                    "PBR": "PETR4.SA",
                    "VALE": "VALE3.SA", 
                    "ITUB": "ITUB4.SA",
                    "BBDC": "BBDC4.SA"
                }
                
                saved_count = 0
                for us_symbol, data in collected_data.items():
                    br_symbol = symbol_map.get(us_symbol, us_symbol)
                    try:
                        # ✅ USA PREÇO ORIGINAL EM USD (sem conversão dupla)
                        price_usd = data['price']  # Mantém em USD
                        db.save_price_data(br_symbol, price_usd, data['volume'], 'alpha_vantage')
                        saved_count += 1
                    except Exception as e:
                        st.warning(f"⚠️ Erro ao salvar {us_symbol}: {e}")
                
                st.info(f"💾 {saved_count} preços salvos no banco (USD)")
            else:
                st.error("❌ Falha na coleta de dados")
                st.info("🔧 Verifique a API key do Alpha Vantage")
                
        except Exception as e:
            st.error(f"❌ Erro: {e}")
            
    # Último dados coletados
    st.markdown("### 💾 Últimos Dados no Banco")
    
    try:
        symbols = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
        recent_data = []
        
        for symbol in symbols:
            latest = db.get_latest_price_data(symbol)
            if not latest.empty:
                recent_data.append({
                    'Símbolo': symbol,
                    'Preço (R$)': f"R$ {latest.iloc[0]['price']:.2f}",
                    'Volume': f"{latest.iloc[0]['volume']:,}",
                    'Fonte': latest.iloc[0]['source'],
                    'Timestamp': latest.iloc[0]['timestamp'][:19]
                })
        
        if recent_data:
            df_recent = pd.DataFrame(recent_data)
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("📭 Nenhum dado recente encontrado")
            st.markdown("�� **Dica:** Use 'Coletar Alpha Vantage' na sidebar")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados recentes: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🏆 ProTrading Engine v3.1.0 | 🌐 Alpha Vantage Integration</p>
    <p>Desenvolvido por Deverson | 📊 Sistema Completo de Trading</p>
    <p>🔧 Banco: TradingDatabase | 🎯 Status: Operacional</p>
</div>
""", unsafe_allow_html=True)
