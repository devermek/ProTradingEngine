"""
ProTrading Engine - Sistema de Alertas
"""
import sqlite3
from datetime import datetime
from data.database import db

class AlertSystem:
    def __init__(self):
        """Inicializa sistema de alertas"""
        self.init_alerts_table()
        self.active_alerts = []
        print("🔔 Sistema de Alertas inicializado!")
    
    def init_alerts_table(self):
        """Cria tabela de alertas"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                trigger_price REAL NOT NULL,
                current_price REAL NOT NULL,
                percentage_change REAL,
                message TEXT,
                triggered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'ACTIVE'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_price_alert(self, symbol, alert_type, threshold_percent):
        """
        Adiciona alerta de preço
        alert_type: 'HIGH' (subiu X%) ou 'LOW' (desceu X%)
        """
        current_data = db.get_latest_price(symbol)
        
        if current_data:
            if alert_type == 'HIGH':
                trigger_price = current_data['price'] * (1 + threshold_percent/100)
            else:  # LOW
                trigger_price = current_data['price'] * (1 - threshold_percent/100)
            
            alert = {
                'symbol': symbol,
                'alert_type': alert_type,
                'threshold_percent': threshold_percent,
                'trigger_price': trigger_price,
                'base_price': current_data['price'],
                'created_at': datetime.now().isoformat()
            }
            
            self.active_alerts.append(alert)
            print(f"🔔 Alerta criado: {symbol} {alert_type} {threshold_percent}%")
            return True
        
        return False
    
    def check_alerts(self):
        """Verifica se algum alerta foi disparado"""
        triggered_alerts = []
        
        for alert in self.active_alerts[:]:  # Cópia da lista
            current_data = db.get_latest_price(alert['symbol'])
            
            if current_data:
                current_price = current_data['price']
                
                # Verifica se alerta foi disparado
                alert_triggered = False
                
                if alert['alert_type'] == 'HIGH' and current_price >= alert['trigger_price']:
                    alert_triggered = True
                elif alert['alert_type'] == 'LOW' and current_price <= alert['trigger_price']:
                    alert_triggered = True
                
                if alert_triggered:
                    # Calcula variação percentual
                    percent_change = ((current_price - alert['base_price']) / alert['base_price']) * 100
                    
                    # Cria mensagem
                    direction = "📈 SUBIU" if percent_change > 0 else "📉 DESCEU"
                    message = f"{direction} {abs(percent_change):.2f}%"
                    
                    # Salva no banco
                    self.save_triggered_alert(alert, current_price, percent_change, message)
                    
                    # Adiciona à lista de disparados
                    triggered_alert = {
                        'symbol': alert['symbol'],
                        'message': message,
                        'current_price': current_price,
                        'percent_change': percent_change,
                        'triggered_at': datetime.now().strftime("%H:%M:%S")
                    }
                    triggered_alerts.append(triggered_alert)
                    
                    # Remove da lista ativa
                    self.active_alerts.remove(alert)
                    
                    print(f"🚨 ALERTA DISPARADO: {alert['symbol']} {message}")
        
        return triggered_alerts
    
    def save_triggered_alert(self, alert, current_price, percent_change, message):
        """Salva alerta disparado no banco"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts 
            (symbol, alert_type, trigger_price, current_price, percentage_change, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert['symbol'],
            alert['alert_type'],
            alert['trigger_price'],
            current_price,
            percent_change,
            message
        ))
        
        conn.commit()
        conn.close()
    
    def get_alert_history(self, limit=10):
        """Pega histórico de alertas"""
        conn = sqlite3.connect(db.db_path)
        
        query = '''
            SELECT * FROM alerts 
            ORDER BY triggered_at DESC 
            LIMIT ?
        '''
        
        import pandas as pd
        result = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return result
    
    def get_active_alerts_count(self):
        """Retorna número de alertas ativos"""
        return len(self.active_alerts)

# Instância global
alert_system = AlertSystem()