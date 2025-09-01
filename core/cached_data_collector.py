import streamlit as st
from core.alpha_vantage_collector import AlphaVantageCollector
from utils.cache_integration import cache_stock_data, get_cached_stock_data

class CachedDataCollector:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.collector = AlphaVantageCollector()
    
    def get_stock_data(self, symbol: str, force_refresh: bool = False):
        """Coleta dados com cache inteligente"""
        
        # Verificar cache primeiro (se não forçar refresh)
        if not force_refresh:
            cached_data = get_cached_stock_data(self.cache_manager, symbol)
            if cached_data:
                st.info(f"📦 Dados de {symbol} carregados do cache")
                return cached_data
        
        # Buscar dados frescos
        try:
            st.info(f"🔄 Buscando dados frescos de {symbol}...")
            fresh_data = self.collector.get_daily_data(symbol)
            
            if fresh_data is not None:
                # Cachear os dados
                cache_stock_data(self.cache_manager, symbol, fresh_data, ttl=300)
                st.success(f"✅ Dados de {symbol} atualizados e cacheados")
                return fresh_data
            else:
                st.error(f"❌ Erro ao buscar dados de {symbol}")
                return None
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            return None
