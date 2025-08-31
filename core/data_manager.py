"""
Gerenciador de múltiplas fontes de dados
Combina Yahoo Finance + Alpha Vantage para máxima confiabilidade
ProTrading Engine v3.1.0 - Alpha Vantage Integration
Desenvolvido por Deverson
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import sys
import os

# Corrige imports - adiciona diretório pai ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importa coletores existentes (sem imports relativos)
from core.data_collector import DataCollector
from core.alpha_vantage_collector import AlphaVantageCollector

# Adiciona config ao path
config_dir = os.path.join(parent_dir, 'config')
sys.path.append(config_dir)

try:
    from api_config import SYMBOL_MAPPING, BRAZILIAN_SYMBOLS, US_SYMBOLS
except ImportError:
    print("⚠️ Usando configuração padrão de símbolos")
    SYMBOL_MAPPING = {
        "PETR4.SA": "PBR",
        "VALE3.SA": "VALE",
        "ITUB4.SA": "ITUB",
        "BBDC4.SA": "BBDC"
    }
    BRAZILIAN_SYMBOLS = ["PETR4.SA", "VALE3.SA"]
    US_SYMBOLS = ["PBR", "VALE"]

# ... resto do código permanece igual ...

class DataManager:
    """
    Gerenciador centralizado de dados financeiros
    Combina múltiplas fontes para máxima confiabilidade
    """
    
    def __init__(self):
        """
        Inicializa gerenciador de dados
        """
        self.yahoo_collector = DataCollector()
        self.av_collector = AlphaVantageCollector()
        self.symbol_mapping = SYMBOL_MAPPING
        
        print("🔄 Data Manager inicializado")
        print(f"📊 Fontes: Yahoo Finance + Alpha Vantage")
        print(f"🗺️ Símbolos mapeados: {len(self.symbol_mapping)}")
    
    def get_symbol_mapping(self, br_symbol: str) -> Optional[str]:
        """
        Obtém símbolo US correspondente ao BR
        
        Args:
            br_symbol (str): Símbolo brasileiro (ex: PETR4.SA)
            
        Returns:
            Optional[str]: Símbolo US (ex: PBR) ou None
        """
        return self.symbol_mapping.get(br_symbol)
    
    def get_current_price_yahoo(self, symbol: str) -> Optional[Dict]:
        """
        Obtém preço atual via Yahoo Finance
        
        Args:
            symbol (str): Símbolo da ação
            
        Returns:
            Optional[Dict]: Dados do preço ou None
        """
        try:
            print(f"🟡 Yahoo Finance: coletando {symbol}...")
            price_data = self.yahoo_collector.collect_current_price(symbol)
            
            if price_data:
                result = {
                    'symbol': symbol,
                    'price': price_data['price'],
                    'volume': price_data['volume'],
                    'timestamp': price_data['timestamp'],
                    'source': 'yahoo_finance',
                    'currency': 'BRL' if '.SA' in symbol else 'USD',
                    'market': 'BR' if '.SA' in symbol else 'US'
                }
                print(f"✅ Yahoo {symbol}: R${result['price']:.2f}")
                return result
                
        except Exception as e:
            print(f"❌ Erro Yahoo Finance para {symbol}: {e}")
        
        return None
    
    def get_current_price_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Obtém preço atual via Alpha Vantage
        
        Args:
            symbol (str): Símbolo da ação
            
        Returns:
            Optional[Dict]: Dados do preço ou None
        """
        try:
            print(f"🟢 Alpha Vantage: coletando {symbol}...")
            av_data = self.av_collector.get_quote(symbol)
            
            if av_data:
                result = {
                    'symbol': symbol,
                    'price': av_data['price'],
                    'volume': av_data['volume'],
                    'change': av_data['change'],
                    'change_percent': av_data['change_percent'],
                    'open': av_data['open'],
                    'high': av_data['high'],
                    'low': av_data['low'],
                    'previous_close': av_data['previous_close'],
                    'timestamp': av_data['timestamp'],
                    'source': 'alpha_vantage',
                    'currency': 'USD',
                    'market': 'US'
                }
                print(f"✅ Alpha Vantage {symbol}: ${result['price']:.2f}")
                return result
                
        except Exception as e:
            print(f"❌ Erro Alpha Vantage para {symbol}: {e}")
        
        return None
    
    def get_best_price(self, br_symbol: str) -> Optional[Dict]:
        """
        Obtém melhor preço disponível (Yahoo + Alpha Vantage)
        
        Args:
            br_symbol (str): Símbolo brasileiro
            
        Returns:
            Optional[Dict]: Melhor preço disponível
        """
        print(f"🔍 Buscando melhor preço para {br_symbol}...")
        
        # Tenta Yahoo Finance primeiro (dados BR)
        yahoo_data = self.get_current_price_yahoo(br_symbol)
        
        # Tenta Alpha Vantage com símbolo US
        us_symbol = self.get_symbol_mapping(br_symbol)
        av_data = None
        if us_symbol:
            av_data = self.get_current_price_alpha_vantage(us_symbol)
        
        # Retorna dados disponíveis com preferência
        if yahoo_data and av_data:
            print(f"✅ Ambas fontes disponíveis para {br_symbol}")
            # Retorna Yahoo (dados BR) mas inclui dados US
            yahoo_data['us_data'] = av_data
            yahoo_data['comparison'] = {
                'br_price_brl': yahoo_data['price'],
                'us_price_usd': av_data['price'],
                'br_volume': yahoo_data['volume'],
                'us_volume': av_data['volume'],
                'currency_note': 'BR em R$, US em USD'
            }
            return yahoo_data
        
        elif yahoo_data:
            print(f"✅ Dados Yahoo disponíveis para {br_symbol}")
            return yahoo_data
        
        elif av_data:
            print(f"✅ Dados Alpha Vantage disponíveis para {us_symbol}")
            return av_data
        
        else:
            print(f"❌ Nenhuma fonte disponível para {br_symbol}")
            return None
    
    def get_market_comparison(self, br_symbol: str) -> Optional[Dict]:
        """
        Compara preços entre mercado BR e US
        
        Args:
            br_symbol (str): Símbolo brasileiro
            
        Returns:
            Optional[Dict]: Comparação de mercados
        """
        us_symbol = self.get_symbol_mapping(br_symbol)
        if not us_symbol:
            print(f"❌ Símbolo US não encontrado para {br_symbol}")
            return None
        
        print(f"🌎 Comparando mercados: {br_symbol} vs {us_symbol}")
        
        # Coleta dados de ambos mercados
        br_data = self.get_current_price_yahoo(br_symbol)
        us_data = self.get_current_price_alpha_vantage(us_symbol)
        
        if not br_data or not us_data:
            print("❌ Dados insuficientes para comparação")
            return None
        
        # Monta comparação
        comparison = {
            'br_symbol': br_symbol,
            'us_symbol': us_symbol,
            'br_price_brl': br_data['price'],
            'us_price_usd': us_data['price'],
            'br_volume': br_data.get('volume', 0),
            'us_volume': us_data.get('volume', 0),
            'br_change_percent': br_data.get('change_percent', 0),
            'us_change_percent': us_data.get('change_percent', 0),
            'timestamp': datetime.now().isoformat(),
            'note': 'Preços em moedas diferentes (BRL vs USD)',
            'sources': {
                'br_source': br_data['source'],
                'us_source': us_data['source']
            }
        }
        
        print(f"📊 BR: R${comparison['br_price_brl']:.2f} | US: ${comparison['us_price_usd']:.2f}")
        return comparison
    
    def collect_all_data(self) -> Dict:
        """
        Coleta dados de todas as fontes para todos os símbolos
        
        Returns:
            Dict: Dados coletados de todas as fontes
        """
        print("🔄 Coletando dados de todas as fontes...")
        print("=" * 50)
        
        results = {
            'yahoo_data': {},
            'alpha_vantage_data': {},
            'comparisons': {},
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_symbols': 0,
                'yahoo_success': 0,
                'av_success': 0,
                'comparisons_made': 0,
                'errors': []
            }
        }
        
        # Símbolos para coletar
        br_symbols = BRAZILIAN_SYMBOLS
        
        for br_symbol in br_symbols:
            print(f"\n�� Processando {br_symbol}...")
            results['summary']['total_symbols'] += 1
            
            # Yahoo Finance (BR)
            yahoo_data = self.get_current_price_yahoo(br_symbol)
            if yahoo_data:
                results['yahoo_data'][br_symbol] = yahoo_data
                results['summary']['yahoo_success'] += 1
            else:
                results['summary']['errors'].append(f"Yahoo Finance falhou para {br_symbol}")
            
            # Alpha Vantage (US)
            us_symbol = self.get_symbol_mapping(br_symbol)
            if us_symbol:
                av_data = self.get_current_price_alpha_vantage(us_symbol)
                if av_data:
                    results['alpha_vantage_data'][us_symbol] = av_data
                    results['summary']['av_success'] += 1
                else:
                    results['summary']['errors'].append(f"Alpha Vantage falhou para {us_symbol}")
                
                # Comparação
                if yahoo_data and av_data:
                    comparison = self.get_market_comparison(br_symbol)
                    if comparison:
                        results['comparisons'][br_symbol] = comparison
                        results['summary']['comparisons_made'] += 1
        
        print("\n" + "=" * 50)
        print("✅ COLETA CONCLUÍDA!")
        print(f"📊 Yahoo Finance: {results['summary']['yahoo_success']}/{results['summary']['total_symbols']}")
        print(f"🌐 Alpha Vantage: {results['summary']['av_success']}/{len(US_SYMBOLS)}")
        print(f"🌎 Comparações: {results['summary']['comparisons_made']}")
        
        if results['summary']['errors']:
            print(f"⚠️ Erros: {len(results['summary']['errors'])}")
            for error in results['summary']['errors']:
                print(f"   - {error}")
        
        return results
    
    def get_enhanced_quote(self, br_symbol: str) -> Optional[Dict]:
        """
        Obtém cotação enriquecida com dados de ambas as fontes
        
        Args:
            br_symbol (str): Símbolo brasileiro
            
        Returns:
            Optional[Dict]: Cotação enriquecida
        """
        print(f"🎯 Cotação enriquecida para {br_symbol}")
        
        # Coleta dados Yahoo
        yahoo_data = self.get_current_price_yahoo(br_symbol)
        
        # Coleta dados Alpha Vantage
        us_symbol = self.get_symbol_mapping(br_symbol)
        av_data = None
        if us_symbol:
            av_data = self.get_current_price_alpha_vantage(us_symbol)
        
        if not yahoo_data and not av_data:
            return None
        
        # Monta resposta enriquecida
        enhanced = {
            'symbol': br_symbol,
            'timestamp': datetime.now().isoformat(),
            'sources_available': [],
            'primary_data': None,
            'secondary_data': None,
            'comparison': None
        }
        
        if yahoo_data:
            enhanced['sources_available'].append('yahoo_finance')
            enhanced['primary_data'] = yahoo_data
        
        if av_data:
            enhanced['sources_available'].append('alpha_vantage')
            if not enhanced['primary_data']:
                enhanced['primary_data'] = av_data
            else:
                enhanced['secondary_data'] = av_data
        
        # Se temos ambos, cria comparação
        if yahoo_data and av_data:
            enhanced['comparison'] = {
                'br_price_brl': yahoo_data['price'],
                'us_price_usd': av_data['price'],
                'volume_ratio': yahoo_data['volume'] / av_data['volume'] if av_data['volume'] > 0 else 0,
                'note': 'Comparação entre mercados BR e US'
            }
        
        print(f"✅ Cotação enriquecida: {len(enhanced['sources_available'])} fontes")
        return enhanced
    
    def test_all_connections(self) -> Dict:
        """
        Testa todas as conexões
        
        Returns:
            Dict: Status das conexões
        """
        print("🧪 Testando todas as conexões...")
        print("=" * 40)
        
        results = {
            'yahoo_finance': {
                'status': False,
                'test_symbol': 'PETR4.SA',
                'response_time': 0,
                'error': None
            },
            'alpha_vantage': {
                'status': False,
                'test_symbol': 'PBR',
                'response_time': 0,
                'error': None
            },
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'FAIL'
        }
        
        # Testa Yahoo Finance
        print("\n🟡 Testando Yahoo Finance...")
        start_time = datetime.now()
        try:
            yahoo_test = self.yahoo_collector.collect_current_price("PETR4.SA")
            results['yahoo_finance']['response_time'] = (datetime.now() - start_time).total_seconds()
            
            if yahoo_test:
                results['yahoo_finance']['status'] = True
                print(f"✅ Yahoo Finance OK ({results['yahoo_finance']['response_time']:.2f}s)")
            else:
                results['yahoo_finance']['error'] = "Retorno vazio"
                print("❌ Yahoo Finance: retorno vazio")
                
        except Exception as e:
            results['yahoo_finance']['error'] = str(e)
            results['yahoo_finance']['response_time'] = (datetime.now() - start_time).total_seconds()
            print(f"❌ Yahoo Finance: {e}")
        
        # Testa Alpha Vantage
        print("\n🟢 Testando Alpha Vantage...")
        start_time = datetime.now()
        try:
            av_test = self.av_collector.test_connection()
            results['alpha_vantage']['response_time'] = (datetime.now() - start_time).total_seconds()
            
            if av_test:
                results['alpha_vantage']['status'] = True
                print(f"✅ Alpha Vantage OK ({results['alpha_vantage']['response_time']:.2f}s)")
            else:
                results['alpha_vantage']['error'] = "Teste de conexão falhou"
                print("❌ Alpha Vantage: teste falhou")
                
        except Exception as e:
            results['alpha_vantage']['error'] = str(e)
            results['alpha_vantage']['response_time'] = (datetime.now() - start_time).total_seconds()
            print(f"❌ Alpha Vantage: {e}")
        
        # Status geral
        if results['yahoo_finance']['status'] and results['alpha_vantage']['status']:
            results['overall_status'] = 'EXCELLENT'
        elif results['yahoo_finance']['status'] or results['alpha_vantage']['status']:
            results['overall_status'] = 'PARTIAL'
        else:
            results['overall_status'] = 'FAIL'
        
        print("\n" + "=" * 40)
        print(f"🎯 STATUS GERAL: {results['overall_status']}")
        
        return results

# Teste rápido se executado diretamente
if __name__ == "__main__":
    print("🚀 Testando Data Manager...")
    
    manager = DataManager()
    
    # Teste conexões
    connection_status = manager.test_all_connections()
    
    if connection_status['overall_status'] != 'FAIL':
        print("\n🎯 Testando coleta de dados...")
        
        # Teste cotação enriquecida
        enhanced = manager.get_enhanced_quote("PETR4.SA")
        if enhanced:
            print(f"✅ Cotação enriquecida PETR4.SA:")
            print(f"   Fontes: {enhanced['sources_available']}")
            if enhanced['comparison']:
                print(f"   BR: R${enhanced['comparison']['br_price_brl']:.2f}")
                print(f"   US: ${enhanced['comparison']['us_price_usd']:.2f}")
        
        # Teste coleta completa
        print("\n📊 Testando coleta completa...")
        all_data = manager.collect_all_data()
        print(f"✅ Coleta completa: {all_data['summary']}")
    
    else:
        print("❌ Falha nas conexões!")