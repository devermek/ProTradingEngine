"""
ProTrading Engine - Coletor de Dados
"""
import requests
import json
import time
from datetime import datetime
from data.database import db

class DataCollector:
    def __init__(self):
        """Inicializa o coletor"""
        self.symbols = ['PETR4.SA', 'VALE3.SA']
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        print("🔄 DataCollector inicializado!")
    
    def get_current_price(self, symbol):
        """Pega preço atual de uma ação"""
        try:
            url = f"{self.base_url}{symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    
                    price_data = {
                        'symbol': symbol,
                        'price': meta.get('regularMarketPrice'),
                        'currency': meta.get('currency'),
                        'timestamp': datetime.now().isoformat(),
                        'market_state': meta.get('marketState', 'UNKNOWN')
                    }
                    
                    return price_data
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao coletar {symbol}: {e}")
            return None
    
    def collect_all_current_prices(self):
        """Coleta preços atuais de todos os símbolos"""
        print("📊 Coletando preços atuais...")
        
        collected_data = {}
        
        for symbol in self.symbols:
            print(f"  📈 Coletando {symbol}...")
            
            price_data = self.get_current_price(symbol)
            
            if price_data and price_data['price']:
                # Salva no banco
                db.save_price(symbol, price_data['price'])
                
                # Armazena para retorno
                collected_data[symbol] = price_data
                
                print(f"  ✅ {symbol}: R$ {price_data['price']:.2f}")
            else:
                print(f"  ❌ Falha ao coletar {symbol}")
            
            # Pausa para não sobrecarregar
            time.sleep(1)
        
        print(f"✅ Coleta concluída! {len(collected_data)} símbolos coletados")
        return collected_data
    
    def start_continuous_collection(self, interval_seconds=60):
        """Inicia coleta contínua"""
        print(f"🔄 Iniciando coleta contínua (intervalo: {interval_seconds}s)")
        
        while True:
            try:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Coletando dados...")
                self.collect_all_current_prices()
                
                print(f"💤 Próxima coleta em {interval_seconds} segundos...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n🛑 Coleta interrompida pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro na coleta contínua: {e}")
                time.sleep(interval_seconds)

# Instância global
data_collector = DataCollector()