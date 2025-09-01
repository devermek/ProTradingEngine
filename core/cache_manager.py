# core/cache_manager.py
import streamlit as st
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict

class CacheManager:
    """Sistema de cache inteligente para dados financeiros"""
    
    def __init__(self):
        # Inicializa o cache no session_state se não existir
        if 'cache_data' not in st.session_state:
            st.session_state.cache_data = {}
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
    
    def _generate_key(self, symbol: str, data_type: str, **kwargs) -> str:
        """Gera chave única para o cache"""
        key_data = f"{symbol}_{data_type}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, key: str, ttl_minutes: int = 5) -> bool:
        """Verifica se o cache ainda é válido"""
        if key not in st.session_state.cache_timestamps:
            return False
        
        cached_time = st.session_state.cache_timestamps[key]
        expiry_time = cached_time + timedelta(minutes=ttl_minutes)
        return datetime.now() < expiry_time
    
    def get(self, symbol: str, data_type: str, ttl_minutes: int = 5, **kwargs) -> Optional[Any]:
        """Recupera dados do cache se válidos"""
        key = self._generate_key(symbol, data_type, **kwargs)
        
        if self._is_cache_valid(key, ttl_minutes):
            return st.session_state.cache_data.get(key)
        
        return None
    
    def set(self, symbol: str, data_type: str, data: Any, **kwargs) -> None:
        """Armazena dados no cache"""
        key = self._generate_key(symbol, data_type, **kwargs)
        st.session_state.cache_data[key] = data
        st.session_state.cache_timestamps[key] = datetime.now()
    
    def clear_expired(self, ttl_minutes: int = 5) -> None:
        """Remove caches expirados"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in st.session_state.cache_timestamps.items():
            if current_time > timestamp + timedelta(minutes=ttl_minutes):
                expired_keys.append(key)
        
        for key in expired_keys:
            st.session_state.cache_data.pop(key, None)
            st.session_state.cache_timestamps.pop(key, None)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do cache"""
        return {
            'total_items': len(st.session_state.cache_data),
            'total_size_mb': len(str(st.session_state.cache_data)) / (1024 * 1024)
        }
