"""
ProTrading Engine - Sistema de Banco de Dados
Versão completa com todos os métodos necessários
Desenvolvido por Deverson
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional

class TradingDatabase:
    def __init__(self, db_path="data/trading_data.db"):
        """Inicializa o banco de dados"""
        # Garante que a pasta data existe
        Path("data").mkdir(exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Cria as tabelas se não existirem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de preços
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER,
                source TEXT DEFAULT 'yahoo',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sinais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                strength REAL NOT NULL,
                strategy TEXT NOT NULL,
                price REAL,
                target_price REAL,
                stop_loss_price REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                triggered_at TEXT
            )
        ''')
        
        # Tabela de opções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                underlying TEXT NOT NULL,
                strike REAL NOT NULL,
                expiry_date TEXT NOT NULL,
                option_type TEXT NOT NULL,
                price REAL NOT NULL,
                bid REAL,
                ask REAL,
                volume INTEGER,
                implied_volatility REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado!")
    
    def save_price_data(self, symbol, price, volume=0, source='manual'):
        """Salva dados de preço no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO prices (symbol, timestamp, price, volume, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, timestamp, price, volume, source))
        
        conn.commit()
        conn.close()
        print(f"💾 Preço salvo: {symbol} = R$ {price:.2f}")
    
    def get_latest_price_data(self, symbol):
        """Obtém o último preço de um símbolo"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT symbol, price, volume, timestamp, source
            FROM prices
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        return df
    
    def get_price_history(self, symbol, days=30):
        """Obtém histórico de preços"""
        conn = sqlite3.connect(self.db_path)
        
        # Data limite
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = '''
            SELECT symbol, price, volume, timestamp, source
            FROM prices
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, date_limit))
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    # ========== MÉTODOS DE COMPATIBILIDADE ==========
    
    def save_price(self, symbol: str, price: float, volume: int = 0):
        """Compatibilidade com save_price"""
        return self.save_price_data(symbol, price, volume)
    
    def get_latest_price(self, symbol: str):
        """Compatibilidade - retorna apenas o preço"""
        try:
            latest = self.get_latest_price_data(symbol)
            if latest is not None and not latest.empty:
                return latest.iloc[0]['price']
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar preço de {symbol}: {e}")
            return None
    
    def get_active_alerts_count(self):
        """Retorna número de alertas ativos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_active = 1')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except:
            return 0
    
    def get_alert_history(self, limit=10):
        """Retorna histórico de alertas"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT symbol, alert_type, threshold, triggered_at
                FROM alerts
                WHERE triggered_at IS NOT NULL
                ORDER BY triggered_at DESC
                LIMIT ?
            '''
            
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            conn.close()
            
            # Converter para lista de dicts
            alerts = []
            for row in results:
                alerts.append({
                    'symbol': row[0],
                    'message': f"{row[1]} alert triggered",
                    'current_price': 0.0,  # Placeholder
                    'triggered_at': row[3]
                })
            
            return alerts
        except:
            return []
    
    def get_options_by_underlying(self, underlying):
        """Retorna opções por ativo"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT underlying, strike, expiry_date, option_type, price, 
                       bid, ask, volume, implied_volatility, timestamp
                FROM options
                WHERE underlying = ?
                ORDER BY expiry_date, strike
            '''
            
            cursor = conn.cursor()
            cursor.execute(query, (underlying,))
            results = cursor.fetchall()
            
            conn.close()
            
            # Converter para lista de dicts
            options = []
            for row in results:
                options.append({
                    'underlying': row[0],
                    'strike': row[1],
                    'expiry_date': row[2],
                    'option_type': row[3],
                    'price': row[4],
                    'bid': row[5],
                    'ask': row[6],
                    'volume': row[7],
                    'implied_volatility': row[8],
                    'timestamp': row[9]
                })
            
            return options
        except:
            return []
    
    def save_signal(self, symbol, signal_type, strength, strategy, price, target_price=None, stop_loss=None, notes=None):
        """Salva sinal de trading"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO signals (symbol, timestamp, signal_type, strength, strategy, price, target_price, stop_loss_price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, timestamp, signal_type, strength, strategy, price, target_price, stop_loss, notes))
        
        conn.commit()
        conn.close()
        print(f"📊 Sinal salvo: {symbol} - {signal_type} (força: {strength})")
    
    def add_price_alert(self, symbol, alert_type, threshold):
        """Adiciona alerta de preço"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (symbol, alert_type, threshold)
            VALUES (?, ?, ?)
        ''', (symbol, alert_type, threshold))
        
        conn.commit()
        conn.close()
        print(f"🔔 Alerta criado: {symbol} {alert_type} {threshold}%")
    
    def check_alerts(self):
        """Verifica alertas disparados (placeholder)"""
        return []  # Retorna lista vazia por enquanto

# Teste do banco se executado diretamente
if __name__ == "__main__":
    print("🧪 Testando TradingDatabase...")
    
    db = TradingDatabase()
    
    # Teste salvar preço
    db.save_price_data("TESTE.SA", 25.50, 1000, "test")
    
    # Teste buscar preço
    latest = db.get_latest_price("TESTE.SA")
    if latest:
        print(f"✅ Último preço TESTE.SA: R$ {latest:.2f}")
    
    # Teste histórico
    history = db.get_price_history("TESTE.SA", 7)
    print(f"📊 Histórico: {len(history)} registros")
    
    print("🎯 Teste concluído!")
    # Instância global para compatibilidade
db = TradingDatabase()

# Exporta tanto a classe quanto a instância
__all__ = ['TradingDatabase', 'db']