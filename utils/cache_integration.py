import streamlit as st
from datetime import datetime
from typing import Dict, Any

def show_cache_status(cache_manager) -> None:
    """Mostra status do cache na interface"""
    stats = cache_manager.get_stats()
    
    st.markdown("### 📊 Cache Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Items Cached", stats['total_items'])
    
    with col2:
        st.metric("Cache Size", f"{stats['cache_size_mb']:.2f} MB")
    
    if st.button("🗑️ Limpar Cache"):
        cache_manager.cache.clear()
        cache_manager.cache_times.clear()
        st.success("Cache limpo!")
        st.rerun()

def cache_stock_data(cache_manager, symbol: str, data: Any, ttl: int = 300) -> None:
    """Cache específico para dados de ações"""
    key = f"stock_data:{symbol}"
    cache_manager.set(key, data, ttl)

def get_cached_stock_data(cache_manager, symbol: str) -> Any:
    """Recupera dados de ações do cache"""
    key = f"stock_data:{symbol}"
    return cache_manager.get(key)
