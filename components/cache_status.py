# components/cache_status.py
import streamlit as st
from datetime import datetime

def show_cache_status(cache_manager):
    """Mostra status do cache na sidebar"""
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("📊 Cache Status")
        
        stats = cache_manager.get_cache_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Items", stats['total_items'])
        with col2:
            st.metric("Tamanho", f"{stats['total_size_mb']:.2f}MB")
        
        # Botão para limpar cache
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            st.session_state.cache_data = {}
            st.session_state.cache_timestamps = {}
            st.success("Cache limpo!")
            st.rerun()

def show_data_freshness(symbol: str, data_type: str, cache_manager):
    """Mostra quando os dados foram atualizados"""
    key = cache_manager._generate_key(symbol, data_type)
    
    if key in st.session_state.cache_timestamps:
        timestamp = st.session_state.cache_timestamps[key]
        time_diff = datetime.now() - timestamp
        
        if time_diff.seconds < 60:
            st.success(f"✅ Dados atualizados há {time_diff.seconds}s")
        elif time_diff.seconds < 300:  # 5 minutos
            st.info(f"🔄 Dados atualizados há {time_diff.seconds//60}min")
        else:
            st.warning("⚠️ Dados podem estar desatualizados")
    else:
        st.info("🆕 Carregando dados...")
