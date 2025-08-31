"""
ProTrading Engine - Estratégias de Trading
"""
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
from data.database import db

class TradingStrategies:
    def __init__(self):
        """Inicializa sistema de estratégias"""
        self.init_signals_table()
        print("💡 Sistema de Estratégias inicializado!")
    
    def init_signals_table(self):
        """Cria tabela de sinais"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                signal_strength INTEGER NOT NULL,
                current_price REAL NOT NULL,
                target_price REAL,
                stop_loss REAL,
                strategy_name TEXT NOT NULL,
                indicators TEXT,
                reasoning TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_sma(self, prices, period):
        """Calcula Média Móvel Simples"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_rsi(self, prices, period=14):
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50  # Neutro se não há dados suficientes
        
        # Calcula mudanças de preço
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separa ganhos e perdas
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        # Média dos últimos 'period' dias
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze_symbol(self, symbol):
        """Análise completa de um símbolo"""
        try:
            # Pega histórico de preços
            history = db.get_price_history(symbol, limit=50)
            
            if history.empty or len(history) < 5:
                return {
                    'symbol': symbol,
                    'signal': 'NEUTRO',
                    'strength': 5,
                    'current_price': 0.0,
                    'target_price': None,
                    'stop_loss': None,
                    'reasoning': 'Dados insuficientes para análise',
                    'indicators': {
                        'sma_5': None,
                        'sma_20': None,
                        'rsi': 50,
                        'current_price': 0.0
                    }
                }
            
            # Converte para lista de preços
            prices = history['price'].tolist()
            prices.reverse()  # Ordem cronológica
            
            current_price = float(prices[-1])
            
            # Calcula indicadores
            sma_5 = self.calculate_sma(prices, 5)
            sma_20 = self.calculate_sma(prices, 20)
            rsi = self.calculate_rsi(prices)
            
            # Análise de tendência
            trend_signal = self.analyze_trend(current_price, sma_5, sma_20)
            
            # Análise RSI
            rsi_signal = self.analyze_rsi(rsi)
            
            # Combina sinais
            final_signal = self.combine_signals(trend_signal, rsi_signal)
            
            # Calcula preços alvo
            target_price, stop_loss = self.calculate_targets(current_price, final_signal['signal'])
            
            indicators = {
                'sma_5': round(sma_5, 2) if sma_5 else None,
                'sma_20': round(sma_20, 2) if sma_20 else None,
                'rsi': round(rsi, 2),
                'current_price': round(current_price, 2)
            }
            
            result = {
                'symbol': symbol,
                'signal': final_signal['signal'],
                'strength': final_signal['strength'],
                'current_price': round(current_price, 2),
                'target_price': round(target_price, 2) if target_price else None,
                'stop_loss': round(stop_loss, 2) if stop_loss else None,
                'reasoning': final_signal['reasoning'],
                'indicators': indicators
            }
            
            # Salva no banco se for sinal forte
            if final_signal['strength'] >= 7:
                self.save_signal(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Erro na análise de {symbol}: {e}")
            return {
                'symbol': symbol,
                'signal': 'ERRO',
                'strength': 0,
                'current_price': 0.0,
                'target_price': None,
                'stop_loss': None,
                'reasoning': f'Erro na análise: {str(e)}',
                'indicators': {}
            }
    
    def analyze_trend(self, current_price, sma_5, sma_20):
        """Análise de tendência com médias móveis"""
        if not sma_5 or not sma_20:
            return {'signal': 'NEUTRO', 'strength': 5, 'reasoning': 'SMA insuficiente'}
        
        # Preço vs SMA
        price_vs_sma5 = (current_price - sma_5) / sma_5 * 100
        price_vs_sma20 = (current_price - sma_20) / sma_20 * 100
        
        # SMA 5 vs SMA 20
        sma_cross = (sma_5 - sma_20) / sma_20 * 100
        
        if sma_cross > 2 and price_vs_sma5 > 1:
            return {
                'signal': 'COMPRA',
                'strength': min(8, int(5 + abs(sma_cross))),
                'reasoning': f'Tendência de alta: SMA5 > SMA20 ({sma_cross:.1f}%)'
            }
        elif sma_cross < -2 and price_vs_sma5 < -1:
            return {
                'signal': 'VENDA',
                'strength': min(8, int(5 + abs(sma_cross))),
                'reasoning': f'Tendência de baixa: SMA5 < SMA20 ({sma_cross:.1f}%)'
            }
        else:
            return {
                'signal': 'NEUTRO',
                'strength': 5,
                'reasoning': 'Tendência indefinida'
            }
    
    def analyze_rsi(self, rsi):
        """Análise RSI"""
        if rsi > 70:
            return {
                'signal': 'VENDA',
                'strength': min(9, int(5 + (rsi - 70) / 5)),
                'reasoning': f'RSI sobrecomprado ({rsi:.1f})'
            }
        elif rsi < 30:
            return {
                'signal': 'COMPRA',
                'strength': min(9, int(5 + (30 - rsi) / 5)),
                'reasoning': f'RSI sobrevendido ({rsi:.1f})'
            }
        else:
            return {
                'signal': 'NEUTRO',
                'strength': 5,
                'reasoning': f'RSI neutro ({rsi:.1f})'
            }
    
    def combine_signals(self, trend_signal, rsi_signal):
        """Combina sinais de diferentes estratégias"""
        # Se ambos concordam
        if trend_signal['signal'] == rsi_signal['signal'] and trend_signal['signal'] != 'NEUTRO':
            return {
                'signal': trend_signal['signal'],
                'strength': min(10, (trend_signal['strength'] + rsi_signal['strength']) // 2 + 2),
                'reasoning': f"Tendência + RSI: {trend_signal['reasoning']} | {rsi_signal['reasoning']}"
            }
        
        # Se discordam
        elif trend_signal['signal'] != rsi_signal['signal'] and 'NEUTRO' not in [trend_signal['signal'], rsi_signal['signal']]:
            return {
                'signal': 'NEUTRO',
                'strength': 4,
                'reasoning': f"Sinais conflitantes: {trend_signal['reasoning']} vs {rsi_signal['reasoning']}"
            }
        
        # Um é neutro
        else:
            stronger_signal = trend_signal if trend_signal['strength'] > rsi_signal['strength'] else rsi_signal
            return {
                'signal': stronger_signal['signal'],
                'strength': max(3, stronger_signal['strength'] - 1),
                'reasoning': stronger_signal['reasoning']
            }
    
    def calculate_targets(self, current_price, signal):
        """Calcula preços alvo e stop loss"""
        if signal == 'COMPRA':
            target_price = current_price * 1.05  # +5%
            stop_loss = current_price * 0.97     # -3%
        elif signal == 'VENDA':
            target_price = current_price * 0.95  # -5%
            stop_loss = current_price * 1.03     # +3%
        else:
            target_price = None
            stop_loss = None
        
        return target_price, stop_loss
    
    def save_signal(self, signal_data):
        """Salva sinal no banco"""
        try:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_signals 
                (symbol, signal_type, signal_strength, current_price, target_price, 
                 stop_loss, strategy_name, indicators, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data['symbol'],
                signal_data['signal'],
                signal_data['strength'],
                signal_data['current_price'],
                signal_data['target_price'],
                signal_data['stop_loss'],
                'SMA + RSI',
                str(signal_data['indicators']),
                signal_data['reasoning']
            ))
            
            conn.commit()
            conn.close()
            
            print(f"💾 Sinal salvo: {signal_data['symbol']} {signal_data['signal']} (força: {signal_data['strength']})")
        except Exception as e:
            print(f"❌ Erro ao salvar sinal: {e}")
    
    def analyze_all_symbols(self):
        """Analisa todos os símbolos"""
        symbols = ['PETR4.SA', 'VALE3.SA']
        results = {}
        
        print("🔍 Analisando símbolos...")
        
        for symbol in symbols:
            print(f"  📊 Analisando {symbol}...")
            analysis = self.analyze_symbol(symbol)
            results[symbol] = analysis
            
            # Log do resultado
            signal_emoji = {
                'COMPRA': '🟢',
                'VENDA': '🔴',
                'NEUTRO': '🟡',
                'ERRO': '❌'
            }
            
            emoji = signal_emoji.get(analysis['signal'], '⚪')
            print(f"    {emoji} {analysis['signal']} (força: {analysis['strength']}/10)")
        
        return results
    
    def get_signals_history(self, limit=10):
        """Pega histórico de sinais"""
        try:
            conn = sqlite3.connect(db.db_path)
            
            query = '''
                SELECT * FROM trading_signals 
                ORDER BY created_at DESC 
                LIMIT ?
            '''
            
            result = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            
            return result
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return pd.DataFrame()

# Instância global
trading_strategies = TradingStrategies()