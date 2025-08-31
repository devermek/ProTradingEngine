"""
Coletor de dados com correção SSL
ProTrading Engine v3.1.0 - SSL Fix
Desenvolvido por Deverson
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import ssl
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuração SSL para contornar problemas de certificado
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DataCollectorFixed:
    """
    Coletor de dados com correções SSL
    """
    
    def __init__(self):
        """
        Inicializa o coletor com configurações SSL
        """
        self.symbols = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
        
        # Configurar sessão com retry e SSL
        self.session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Desabilitar verificação SSL (temporário)
        self.session.verify = False
        
        print("🔧 DataCollector Fixed inicializado")
        print("⚠️ SSL verification desabilitado temporariamente")
    
    def collect_current_price(self, symbol: str) -> Optional[Dict]:
        """
        Coleta preço atual com correções SSL
        """
        print(f"🔄 Coletando {symbol} (SSL fixed)...")
        
        try:
            # Método 1: Histórico recente (mais confiável)
            ticker = yf.Ticker(symbol, session=self.session)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                latest_volume = hist['Volume'].iloc[-1]
                
                result = {
                    'symbol': symbol,
                    'price': float(latest_price),
                    'volume': int(latest_volume),
                    'timestamp': datetime.now().isoformat(),
                    'method': 'history_ssl_fixed'
                }
                
                print(f"✅ {symbol}: R\${result['price']:.2f}")
                return result
            
        except Exception as e:
            print(f"❌ Método 1 falhou para {symbol}: {e}")
        
        try:
            # Método 2: Download direto
            data = yf.download(
                symbol, 
                period="1d", 
                interval="1d", 
                progress=False,
                session=self.session
            )
            
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                latest_volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 0
                
                result = {
                    'symbol': symbol,
                    'price': float(latest_price),
                    'volume': int(latest_volume),
                    'timestamp': datetime.now().isoformat(),
                    'method': 'download_ssl_fixed'
                }
                
                print(f"✅ {symbol}: R\${result['price']:.2f} (download)")
                return result
            
        except Exception as e:
            print(f"❌ Método 2 falhou para {symbol}: {e}")
        
        print(f"❌ Todos os métodos falharam para {symbol}")
        return None
    
    def collect_all_current_prices(self) -> Dict[str, Dict]:
        """
        Coleta preços de todos os símbolos
        """
        print("🔄 Coletando todos os preços (SSL fixed)...")
        
        results = {}
        for symbol in self.symbols:
            price_data = self.collect_current_price(symbol)
            if price_data:
                results[symbol] = price_data
        
        print(f"✅ Coletados {len(results)}/{len(self.symbols)} símbolos")
        return results
    
    def test_connection(self) -> bool:
        """
        Testa conexão com correções SSL
        """
        print("🧪 Testando conexão (SSL fixed)...")
        
        try:
            # Testa com símbolo simples
            result = self.collect_current_price("PETR4.SA")
            
            if result:
                print("✅ Conexão SSL fixed OK!")
                return True
            else:
                print("❌ Conexão SSL fixed falhou!")
                return False
                
        except Exception as e:
            print(f"❌ Teste conexão SSL fixed: {e}")
            return False

# Teste se executado diretamente
if __name__ == "__main__":
    print("🚀 Testando DataCollector SSL Fixed...")
    
    collector = DataCollectorFixed()
    
    # Teste conexão
    if collector.test_connection():
        print("\n📊 Testando coleta completa...")
        all_prices = collector.collect_all_current_prices()
        
        for symbol, data in all_prices.items():
            print(f"✅ {symbol}: R\${data['price']:.2f} ({data['method']})")
    
    else:
        print("❌ Teste falhou!")