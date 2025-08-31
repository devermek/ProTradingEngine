"""
ProTrading Engine - Configurações Principais
Desenvolvido por: Deverson
"""

class Config:
    # Informações do Sistema
    APP_NAME = "ProTrading Engine"
    VERSION = "1.0.0"
    AUTHOR = "Deverson"
    
    # Símbolos que vamos monitorar
    SYMBOLS = ['PETR4.SA', 'VALE3.SA']
    
    # Configurações de Trading
    INITIAL_CAPITAL = 100000  # R\$ 100 mil (simulação)
    MAX_POSITION_SIZE = 0.05  # 5% máximo por trade
    STOP_LOSS_PERCENT = 0.10  # 10% de stop loss
    TARGET_PERCENT = 0.25     # 25% de alvo
    
    # Configurações de Risco
    MAX_DAILY_LOSS = 0.02     # 2% perda máxima por dia
    MAX_DRAWDOWN = 0.15       # 15% drawdown máximo
    
    # Configurações de Dados
    DATA_UPDATE_INTERVAL = 60  # Atualiza a cada 60 segundos
    
    # Configurações de Alertas
    ENABLE_EMAIL_ALERTS = False    # Vamos configurar depois
    ENABLE_TELEGRAM_ALERTS = False # Vamos configurar depois
    
    # Configurações do Dashboard
    DASHBOARD_PORT = 8501
    DASHBOARD_HOST = "localhost"

# Instância global das configurações
config = Config()