"""
Debug Yahoo Finance
ProTrading Engine v3.1.0
Desenvolvido por Deverson
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

import yfinance as yf
from datetime import datetime

def test_yahoo_direct():
    """Testa Yahoo Finance diretamente"""
    print("🧪 TESTE DIRETO YAHOO FINANCE")
    print("=" * 40)
    
    symbols = ["PETR4.SA", "VALE3.SA", "^BVSP", "AAPL"]
    
    for symbol in symbols:
        print(f"\n📊 Testando {symbol}...")
        
        try:
            # Teste direto yfinance
            ticker = yf.Ticker(symbol)
            
            # Teste 1: Info
            print(f"   Teste 1 - Info:")
            try:
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                volume = info.get('volume') or info.get('regularMarketVolume', 0)
                name = info.get('longName', 'N/A')
                
                print(f"     ✅ Nome: {name}")
                print(f"     ✅ Preço: {current_price}")
                print(f"     ✅ Volume: {volume}")
            except Exception as e:
                print(f"     ❌ Info falhou: {e}")
            
            # Teste 2: Histórico
            print(f"   Teste 2 - Histórico:")
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    latest_volume = hist['Volume'].iloc[-1]
                    print(f"     ✅ Último preço: {latest_price:.2f}")
                    print(f"     ✅ Volume: {latest_volume:,.0f}")
                else:
                    print(f"     ❌ Histórico vazio")
            except Exception as e:
                print(f"     ❌ Histórico falhou: {e}")
            
            # Teste 3: Fast Info
            print(f"   Teste 3 - Fast Info:")
            try:
                fast_info = ticker.fast_info
                last_price = fast_info.get('lastPrice')
                market_price = fast_info.get('regularMarketPrice')
                print(f"     ✅ Last Price: {last_price}")
                print(f"     ✅ Market Price: {market_price}")
            except Exception as e:
                print(f"     ❌ Fast Info falhou: {e}")
            
        except Exception as e:
            print(f"❌ {symbol} - Erro geral: {e}")

def test_yahoo_collector():
    """Testa nosso coletor Yahoo"""
    print("\n🔧 TESTE NOSSO COLETOR YAHOO")
    print("=" * 40)
    
    try:
        from data_collector import DataCollector
        collector = DataCollector()
        symbols = ["PETR4.SA", "VALE3.SA"]
        
        for symbol in symbols:
            print(f"\n📊 Testando {symbol} com nosso coletor...")
            
            try:
                result = collector.collect_current_price(symbol)
                
                if result:
                    print(f"✅ {symbol}:")
                    print(f"   Preço: R\${result['price']:.2f}")
                    print(f"   Volume: {result['volume']:,}")
                    print(f"   Timestamp: {result['timestamp']}")
                else:
                    print(f"❌ {symbol}: Retorno vazio")
                    
            except Exception as e:
                print(f"❌ {symbol}: Erro no coletor: {e}")
    
    except ImportError as e:
        print(f"❌ Erro ao importar DataCollector: {e}")

def test_connection():
    """Testa conectividade básica"""
    print("\n🌐 TESTE CONECTIVIDADE")
    print("=" * 40)
    
    import requests
    
    # Teste 1: Internet
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"✅ Internet: {response.status_code}")
    except Exception as e:
        print(f"❌ Internet: {e}")
    
    # Teste 2: Yahoo Finance
    try:
        response = requests.get("https://finance.yahoo.com", timeout=10)
        print(f"✅ Yahoo Finance site: {response.status_code}")
    except Exception as e:
        print(f"❌ Yahoo Finance site: {e}")
    
    # Teste 3: API Yahoo
    try:
        response = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/AAPL", timeout=10)
        print(f"✅ Yahoo API: {response.status_code}")
    except Exception as e:
        print(f"❌ Yahoo API: {e}")

def test_alternative_methods():
    """Testa métodos alternativos"""
    print("\n🔄 MÉTODOS ALTERNATIVOS")
    print("=" * 40)
    
    symbols = ["PETR4.SA", "VALE3.SA"]
    
    for symbol in symbols:
        print(f"\n📊 Métodos alternativos {symbol}...")
        
        # Método 1: Download direto
        try:
            data = yf.download(symbol, period="1d", interval="1d", progress=False)
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                print(f"   ✅ Download direto: R\${latest_price:.2f}")
            else:
                print(f"   ❌ Download direto: vazio")
        except Exception as e:
            print(f"   ❌ Download direto: {e}")
        
        # Método 2: Ticker com retry
        try:
            for attempt in range(3):
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        latest_price = hist['Close'].iloc[-1]
                        print(f"   ✅ Retry {attempt+1}: R\${latest_price:.2f}")
                        break
                except:
                    if attempt == 2:
                        print(f"   ❌ Retry falhou após 3 tentativas")
                    continue
        except Exception as e:
            print(f"   ❌ Método retry: {e}")

if __name__ == "__main__":
    print("🚀 DEBUG YAHOO FINANCE - ProTrading Engine v3.1.0")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now()}")
    
    test_connection()
    test_yahoo_direct()
    test_yahoo_collector()
    test_alternative_methods()
    
    print("\n" + "=" * 60)
    print("🎯 DEBUG CONCLUÍDO!")
    print("📋 Analise os resultados acima para identificar o problema")
    print("💡 Se algum método funcionou, podemos usar esse!")