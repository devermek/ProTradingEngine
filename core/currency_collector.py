import requests
from datetime import datetime

class CurrencyCollector:
    def get_usd_brl_rate(self):
        try:
            response = requests.get('https://economia.awesomeapi.com.br/last/USD-BRL', timeout=10)
            data = response.json()
            rate = float(data['USDBRL']['bid'])
            print(f"✅ Cotação USD/BRL: {rate:.4f}")
            return rate
        except:
            print("⚠️ Usando cotação padrão: 5.20")
            return 5.20
    
    def convert_usd_to_brl(self, usd_amount):
        rate = self.get_usd_brl_rate()
        return usd_amount * rate
