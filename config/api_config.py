"""
Configurações das APIs do sistema
ProTrading Engine v3.1.0 - Alpha Vantage Integration
Desenvolvido por Deverson
"""

# Alpha Vantage Configuration
ALPHA_VANTAGE_API_KEY = "Q43HY5S4MIT7P8XT"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_CALLS_PER_MINUTE = 5  # Limite gratuito
ALPHA_VANTAGE_TIMEOUT = 30  # Timeout requests

# Mapeamento símbolos BR -> US (ADRs)
SYMBOL_MAPPING = {
    "PETR4.SA": "PBR",      # Petrobras ADR
    "VALE3.SA": "VALE",     # Vale ADR
    "ITUB4.SA": "ITUB",     # Itaú ADR
    "BBDC4.SA": "BBDC",     # Bradesco ADR
    "ABEV3.SA": "ABEV",     # Ambev ADR
    "BIDI4.SA": "BIDI",     # Banco Inter ADR
}

# Configurações gerais
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
CACHE_DURATION = 60  # segundos

# Símbolos para monitoramento
BRAZILIAN_SYMBOLS = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
US_SYMBOLS = ["PBR", "VALE", "ITUB", "BBDC"]

# Rate limiting
RATE_LIMIT_DELAY = 12  # segundos entre calls (5 calls/minuto)

print("🔑 Configurações API carregadas")
print(f"📊 Alpha Vantage: {len(SYMBOL_MAPPING)} símbolos mapeados")