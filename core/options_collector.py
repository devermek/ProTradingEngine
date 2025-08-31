"""
ProTrading Engine - Coletor de Dados de Opções v3.0.0
Sistema completo de coleta, análise e gerenciamento de opções
Desenvolvido por: Deverson
Data: 2025
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from data.database import db
import json
import time
import ssl
import urllib3
import math
import warnings

# Configurações
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Simulação scipy.stats.norm para evitar dependência
class MockNorm:
    @staticmethod
    def cdf(x):
        """Aproximação CDF normal padrão"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def pdf(x):
        """Aproximação PDF normal padrão"""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

norm = MockNorm()

class OptionsCollector:
    """
    Sistema completo de coleta e análise de opções
    
    Funcionalidades:
    - Geração de dados simulados realistas
    - Cálculo de Greeks (Black-Scholes)
    - Análise de volatilidade implícita
    - Chain de opções completa
    - Estatísticas e rankings
    - Detecção de anomalias
    """
    
    def __init__(self):
        """Inicializa o sistema de opções"""
        self.init_options_tables()
        self.session = self.create_session()
        self.risk_free_rate = 0.1075  # Selic atual ~10.75%
        print("📊 Sistema de Opções v3.0.0 inicializado!")
        print(f"💰 Taxa livre de risco: {self.risk_free_rate:.2%}")
    
    def create_session(self):
        """Cria sessão HTTP robusta para futuras APIs"""
        session = requests.Session()
        session.verify = False
        session.timeout = 30
        session.headers.update({
            'User-Agent': 'ProTrading Engine v3.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session
    
    def init_options_tables(self):
        """Inicializa todas as tabelas de opções no banco"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Tabela principal de opções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS options_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                underlying TEXT NOT NULL,
                option_type TEXT NOT NULL,
                strike REAL NOT NULL,
                expiry_date TEXT NOT NULL,
                price REAL NOT NULL,
                bid REAL,
                ask REAL,
                volume INTEGER DEFAULT 0,
                open_interest INTEGER DEFAULT 0,
                implied_volatility REAL,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                rho REAL,
                intrinsic_value REAL,
                time_value REAL,
                moneyness REAL,
                days_to_expiry INTEGER,
                bid_ask_spread REAL,
                mid_price REAL,
                last_update TEXT DEFAULT CURRENT_TIMESTAMP,
                data_source TEXT DEFAULT 'SIMULATED',
                quality_score REAL DEFAULT 1.0,
                UNIQUE(symbol, last_update)
            )
        ''')
        
        # Tabela resumo chains por vencimento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS options_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                underlying TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                total_calls INTEGER DEFAULT 0,
                total_puts INTEGER DEFAULT 0,
                total_volume INTEGER DEFAULT 0,
                total_open_interest INTEGER DEFAULT 0,
                max_volume_call TEXT,
                max_volume_put TEXT,
                max_oi_call TEXT,
                max_oi_put TEXT,
                avg_iv_calls REAL,
                avg_iv_puts REAL,
                iv_skew REAL,
                strike_range_min REAL,
                strike_range_max REAL,
                atm_strike REAL,
                pcr_volume REAL,
                pcr_oi REAL,
                days_to_expiry INTEGER,
                last_update TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("💾 Tabelas de opções criadas/atualizadas!")
    
    def get_current_stock_price(self, symbol):
        """
        Obtém preço atual da ação
        
        Args:
            symbol (str): Símbolo da ação (ex: PETR4)
            
        Returns:
            float: Preço atual da ação
        """
        try:
            # Tenta pegar do banco primeiro
            price_data = db.get_latest_price(f'{symbol}.SA')
            if price_data:
                return float(price_data['price'])
            
            # Preços padrão baseados em dados históricos reais
            default_prices = {
                'PETR4': 32.50,   # Petrobras
                'VALE3': 55.80,   # Vale
                'ITUB4': 28.90,   # Itaú
                'BBDC4': 22.40,   # Bradesco
                'ABEV3': 12.30,   # Ambev
                'WEGE3': 45.20,   # WEG
                'MGLU3': 8.75,    # Magazine Luiza
                'JBSS3': 28.60,   # JBS
                'SUZB3': 52.30,   # Suzano
                'CSNA3': 18.90    # CSN
            }
            
            price = default_prices.get(symbol, 30.0)
            return price
            
        except Exception as e:
            print(f"❌ Erro ao obter preço {symbol}: {e}")
            return 30.0
    
    def calculate_time_to_expiry(self, expiry_date):
        """
        Calcula tempo até vencimento em anos
        
        Args:
            expiry_date (str): Data vencimento YYYY-MM-DD
            
        Returns:
            float: Tempo em anos
        """
        try:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            today = datetime.now()
            days = (expiry - today).days
            return max(1/365, days / 365.0)  # Mínimo 1 dia
        except:
            return 30/365  # Default 30 dias
    
    def calculate_days_to_expiry(self, expiry_date):
        """
        Calcula dias até vencimento
        
        Args:
            expiry_date (str): Data vencimento
            
        Returns:
            int: Dias até vencimento
        """
        try:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            today = datetime.now()
            return max(1, (expiry - today).days)
        except:
            return 30
    
    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """
        Calcula preço Black-Scholes
        
        Args:
            S (float): Preço ação atual
            K (float): Strike
            T (float): Tempo vencimento (anos)
            r (float): Taxa livre risco
            sigma (float): Volatilidade
            option_type (str): 'call' ou 'put'
            
        Returns:
            float: Preço teórico opção
        """
        try:
            if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
                return 0.01
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type.lower() == 'call':
                price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:  # put
                price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
            return max(0.01, price)
            
        except Exception as e:
            print(f"❌ Erro Black-Scholes: {e}")
            return 0.01
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """
        Calcula todos os Greeks
        
        Args:
            S (float): Preço ação
            K (float): Strike
            T (float): Tempo vencimento
            r (float): Taxa livre risco
            sigma (float): Volatilidade
            option_type (str): 'call' ou 'put'
            
        Returns:
            dict: Greeks calculados
        """
        try:
            if T <= 0 or sigma <= 0:
                return {
                    'delta': 0.0,
                    'gamma': 0.0,
                    'theta': 0.0,
                    'vega': 0.0,
                    'rho': 0.0
                }
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            # Delta
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
            else:
                delta = norm.cdf(d1) - 1
            
            # Gamma (igual para call e put)
            gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
            
            # Theta
            theta_common = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
            if option_type.lower() == 'call':
                theta = (theta_common - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
            else:
                theta = (theta_common + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
            
            # Vega (igual para call e put)
            vega = S * norm.pdf(d1) * math.sqrt(T) / 100
            
            # Rho
            if option_type.lower() == 'call':
                rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
            else:
                rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            print(f"❌ Erro cálculo Greeks: {e}")
            return {
                'delta': 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }
    
    def calculate_intrinsic_value(self, S, K, option_type):
        """
        Calcula valor intrínseco
        
        Args:
            S (float): Preço ação
            K (float): Strike
            option_type (str): 'CALL' ou 'PUT'
            
        Returns:
            float: Valor intrínseco
        """
        if option_type.upper() == 'CALL':
            return max(0, S - K)
        else:  # PUT
            return max(0, K - S)
    
    def generate_realistic_iv(self, S, K, T, option_type):
        """
        Gera volatilidade implícita realista
        
        Args:
            S (float): Preço ação
            K (float): Strike
            T (float): Tempo vencimento
            option_type (str): Tipo opção
            
        Returns:
            float: Volatilidade implícita
        """
        try:
            # Base IV entre 20-60%
            base_iv = 0.25 + (abs(hash(f"{S}{K}")) % 35) / 100
            
            # Moneyness effect (smile)
            moneyness = S / K
            if option_type.upper() == 'PUT':
                # Puts OTM têm IV maior (skew)
                if moneyness > 1.0:  # OTM put
                    base_iv *= (1.1 + 0.2 * (moneyness - 1))
            else:  # CALL
                # Calls OTM têm IV ligeiramente maior
                if moneyness < 1.0:  # OTM call
                    base_iv *= (1.05 + 0.1 * (1 - moneyness))
            
            # Time effect (IV maior para vencimentos próximos)
            if T < 0.1:  # Menos de 36 dias
                base_iv *= 1.2
            elif T > 0.5:  # Mais de 6 meses
                base_iv *= 0.9
            
            return min(1.0, max(0.1, base_iv))
            
        except:
            return 0.30  # Default 30%
    
    def generate_realistic_volume(self, S, K, T, option_type, iv):
        """
        Gera volume realista baseado em características da opção
        
        Args:
            S (float): Preço ação
            K (float): Strike
            T (float): Tempo vencimento
            option_type (str): Tipo opção
            iv (float): Volatilidade implícita
            
        Returns:
            int: Volume negociado
        """
        try:
            # Base volume
            base_volume = abs(hash(f"{S}{K}{option_type}")) % 1000
            
            # ATM têm mais volume
            moneyness = S / K
            if 0.95 <= moneyness <= 1.05:  # ATM
                base_volume *= 3
            elif 0.90 <= moneyness <= 1.10:  # Near ATM
                base_volume *= 2
            
            # Vencimentos próximos têm mais volume
            if T < 0.1:  # Menos de 36 dias
                base_volume *= 2
            elif T > 0.5:  # Mais de 6 meses
                base_volume *= 0.5
            
            # IV alta atrai mais interesse
            if iv > 0.40:
                base_volume *= 1.5
            
            return int(base_volume)
            
        except:
            return abs(hash(f"{S}{K}")) % 500
    
    def generate_mock_options_data(self, underlying):
        """
        Gera dados simulados realistas de opções
        
        Args:
            underlying (str): Símbolo ação (ex: PETR4)
            
        Returns:
            list: Lista de opções geradas
        """
        print(f"🎭 Gerando dados realistas para {underlying}...")
        
        try:
            # Preço atual da ação
            current_price = self.get_current_stock_price(underlying)
            
            # Gera vencimentos (próximos 2-3 meses)
            today = datetime.now()
            expiry_dates = [
                (today + timedelta(days=30)).strftime('%Y-%m-%d'),
                (today + timedelta(days=60)).strftime('%Y-%m-%d'),
                (today + timedelta(days=90)).strftime('%Y-%m-%d')
            ]
            
            options_data = []
            
            for expiry_date in expiry_dates:
                T = self.calculate_time_to_expiry(expiry_date)
                days_to_expiry = self.calculate_days_to_expiry(expiry_date)
                
                # Gera strikes ao redor do preço atual (±20%)
                strike_range = current_price * 0.20
                num_strikes = 15  # Mais strikes para melhor cobertura
                
                strikes = []
                for i in range(-7, 8):  # 15 strikes
                    strike = current_price + (i * strike_range / 7)
                    # Arredonda para múltiplos de 0.50
                    strike = round(strike * 2) / 2
                    if strike > 0:
                        strikes.append(strike)
                
                for strike in strikes:
                    # Gera CALL
                    call_iv = self.generate_realistic_iv(current_price, strike, T, 'CALL')
                    call_price = self.black_scholes_price(
                        current_price, strike, T, self.risk_free_rate, call_iv, 'call'
                    )
                    
                    # Adiciona ruído realista ao preço
                    noise = 1 + (abs(hash(f"{underlying}{strike}{expiry_date}call")) % 20 - 10) / 100
                    call_price *= noise
                    call_price = max(0.01, call_price)
                    
                    # Bid/Ask spread realista
                    spread_pct = 0.05 + (abs(hash(f"{strike}")) % 10) / 200  # 5-10%
                    call_bid = call_price * (1 - spread_pct/2)
                    call_ask = call_price * (1 + spread_pct/2)
                    
                    # Volume e OI
                    call_volume = self.generate_realistic_volume(
                        current_price, strike, T, 'CALL', call_iv
                    )
                    call_oi = call_volume * (2 + abs(hash(f"{strike}call")) % 5)
                    
                    # Greeks
                    call_greeks = self.calculate_greeks(
                        current_price, strike, T, self.risk_free_rate, call_iv, 'call'
                    )
                    
                    # Valores derivados
                    intrinsic = self.calculate_intrinsic_value(current_price, strike, 'CALL')
                    time_value = call_price - intrinsic
                    moneyness = current_price / strike
                    bid_ask_spread = (call_ask - call_bid) / call_price if call_price > 0 else 0
                    mid_price = (call_bid + call_ask) / 2
                    
                    call_data = {
                        'symbol': f"{underlying}C{int(strike*100)}{expiry_date.replace('-', '')}",
                        'underlying': underlying,
                        'option_type': 'CALL',
                        'strike': round(strike, 2),
                        'expiry_date': expiry_date,
                        'price': round(call_price, 2),
                        'bid': round(call_bid, 2),
                        'ask': round(call_ask, 2),
                        'volume': call_volume,
                        'open_interest': call_oi,
                        'implied_volatility': round(call_iv, 4),
                        'delta': call_greeks['delta'],
                        'gamma': call_greeks['gamma'],
                        'theta': call_greeks['theta'],
                        'vega': call_greeks['vega'],
                        'rho': call_greeks['rho'],
                        'intrinsic_value': round(intrinsic, 2),
                        'time_value': round(time_value, 2),
                        'moneyness': round(moneyness, 4),
                        'days_to_expiry': days_to_expiry,
                        'bid_ask_spread': round(bid_ask_spread, 4),
                        'mid_price': round(mid_price, 2)
                    }
                    options_data.append(call_data)
                    
                    # Gera PUT
                    put_iv = self.generate_realistic_iv(current_price, strike, T, 'PUT')
                    put_price = self.black_scholes_price(
                        current_price, strike, T, self.risk_free_rate, put_iv, 'put'
                    )
                    
                    # Adiciona ruído realista
                    noise = 1 + (abs(hash(f"{underlying}{strike}{expiry_date}put")) % 20 - 10) / 100
                    put_price *= noise
                    put_price = max(0.01, put_price)
                    
                    # Bid/Ask spread
                    spread_pct = 0.05 + (abs(hash(f"{strike}put")) % 10) / 200
                    put_bid = put_price * (1 - spread_pct/2)
                    put_ask = put_price * (1 + spread_pct/2)
                    
                    # Volume e OI
                    put_volume = self.generate_realistic_volume(
                        current_price, strike, T, 'PUT', put_iv
                    )
                    put_oi = put_volume * (2 + abs(hash(f"{strike}put")) % 5)
                    
                    # Greeks
                    put_greeks = self.calculate_greeks(
                        current_price, strike, T, self.risk_free_rate, put_iv, 'put'
                    )
                    
                    # Valores derivados
                    intrinsic = self.calculate_intrinsic_value(current_price, strike, 'PUT')
                    time_value = put_price - intrinsic
                    moneyness = current_price / strike
                    bid_ask_spread = (put_ask - put_bid) / put_price if put_price > 0 else 0
                    mid_price = (put_bid + put_ask) / 2
                    
                    put_data = {
                        'symbol': f"{underlying}P{int(strike*100)}{expiry_date.replace('-', '')}",
                        'underlying': underlying,
                        'option_type': 'PUT',
                        'strike': round(strike, 2),
                        'expiry_date': expiry_date,
                        'price': round(put_price, 2),
                        'bid': round(put_bid, 2),
                        'ask': round(put_ask, 2),
                        'volume': put_volume,
                        'open_interest': put_oi,
                        'implied_volatility': round(put_iv, 4),
                        'delta': put_greeks['delta'],
                        'gamma': put_greeks['gamma'],
                        'theta': put_greeks['theta'],
                        'vega': put_greeks['vega'],
                        'rho': put_greeks['rho'],
                        'intrinsic_value': round(intrinsic, 2),
                        'time_value': round(time_value, 2),
                        'moneyness': round(moneyness, 4),
                        'days_to_expiry': days_to_expiry,
                        'bid_ask_spread': round(bid_ask_spread, 4),
                        'mid_price': round(mid_price, 2)
                    }
                    options_data.append(put_data)
            
            print(f"🎭 {len(options_data)} opções realistas geradas para {underlying}")
            return options_data
            
        except Exception as e:
            print(f"❌ Erro ao gerar dados {underlying}: {e}")
            return []
    
    def collect_options_data_alternative(self, underlying):
        """
        Método alternativo de coleta (simulado para desenvolvimento)
        
        Args:
            underlying (str): Símbolo ação
            
        Returns:
            dict: Dados opções organizados
        """
        print(f"📊 Coletando opções para {underlying} (método avançado)...")
        
        try:
            # Gera dados simulados realistas
            options_data = self.generate_mock_options_data(underlying)
            
            # Organiza em calls e puts
            calls = [opt for opt in options_data if opt['option_type'] == 'CALL']
            puts = [opt for opt in options_data if opt['option_type'] == 'PUT']
            
            return {
                'calls': calls,
                'puts': puts,
                'underlying': underlying,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Erro na coleta alternativa {underlying}: {e}")
            return {
                'calls': [],
                'puts': [],
                'underlying': underlying,
                'success': False
            }
    
    def save_options_data(self, options_data):
        """
        Salva dados de opções no banco
        
        Args:
            options_data (dict): Dados opções para salvar
            
        Returns:
            int: Número de opções salvas
        """
        try:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            all_options = options_data['calls'] + options_data['puts']
            
            for option in all_options:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO options_data 
                        (symbol, underlying, option_type, strike, expiry_date, price, bid, ask, 
                         volume, open_interest, implied_volatility, delta, gamma, theta, vega, rho,
                         intrinsic_value, time_value, moneyness, days_to_expiry, bid_ask_spread, mid_price,
                         data_source, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        option['symbol'], option['underlying'], option['option_type'], 
                        option['strike'], option['expiry_date'], option['price'], 
                        option['bid'], option['ask'], option['volume'], option['open_interest'],
                        option['implied_volatility'], option['delta'], option['gamma'], 
                        option['theta'], option['vega'], option['rho'],
                        option['intrinsic_value'], option['time_value'], option['moneyness'],
                        option['days_to_expiry'], option['bid_ask_spread'], option['mid_price'],
                        'SIMULATED_V3', 1.0
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"❌ Erro ao salvar {option['symbol']}: {e}")
            
            # Salva resumo das chains
            self.save_chain_summaries_advanced(options_data)
            
            conn.commit()
            conn.close()
            
            print(f"💾 {saved_count} opções salvas para {options_data['underlying']}")
            return saved_count
            
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {e}")
            return 0
    
    def save_chain_summaries_advanced(self, options_data):
        """
        Salva resumos avançados das chains por vencimento
        
        Args:
            options_data (dict): Dados das opções
        """
        try:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Agrupa por vencimento
            expiries = set()
            for option in options_data['calls'] + options_data['puts']:
                expiries.add(option['expiry_date'])
            
            underlying = options_data['underlying']
            current_price = self.get_current_stock_price(underlying)
            
            for expiry in expiries:
                calls_expiry = [c for c in options_data['calls'] if c['expiry_date'] == expiry]
                puts_expiry = [p for p in options_data['puts'] if p['expiry_date'] == expiry]
                
                if not calls_expiry and not puts_expiry:
                    continue
                
                # Estatísticas básicas
                total_calls = len(calls_expiry)
                total_puts = len(puts_expiry)
                total_volume = sum(c['volume'] for c in calls_expiry) + sum(p['volume'] for p in puts_expiry)
                total_oi = sum(c['open_interest'] for c in calls_expiry) + sum(p['open_interest'] for p in puts_expiry)
                
                # Opções com maior volume/OI
                max_vol_call = max(calls_expiry, key=lambda x: x['volume'])['symbol'] if calls_expiry else ''
                max_vol_put = max(puts_expiry, key=lambda x: x['volume'])['symbol'] if puts_expiry else ''
                max_oi_call = max(calls_expiry, key=lambda x: x['open_interest'])['symbol'] if calls_expiry else ''
                max_oi_put = max(puts_expiry, key=lambda x: x['open_interest'])['symbol'] if puts_expiry else ''
                
                # IV médio
                avg_iv_calls = sum(c['implied_volatility'] for c in calls_expiry) / len(calls_expiry) if calls_expiry else 0
                avg_iv_puts = sum(p['implied_volatility'] for p in puts_expiry) / len(puts_expiry) if puts_expiry else 0
                
                # IV Skew (puts vs calls)
                iv_skew = avg_iv_puts - avg_iv_calls if avg_iv_calls > 0 else 0
                
                # Range de strikes
                all_strikes = [opt['strike'] for opt in calls_expiry + puts_expiry]
                strike_min = min(all_strikes) if all_strikes else 0
                strike_max = max(all_strikes) if all_strikes else 0
                
                # ATM strike (mais próximo do preço atual)
                atm_strike = min(all_strikes, key=lambda x: abs(x - current_price)) if all_strikes else current_price
                
                # Put/Call ratios
                call_volume = sum(c['volume'] for c in calls_expiry)
                put_volume = sum(p['volume'] for p in puts_expiry)
                call_oi = sum(c['open_interest'] for c in calls_expiry)
                put_oi = sum(p['open_interest'] for p in puts_expiry)
                
                pcr_volume = put_volume / call_volume if call_volume > 0 else 0
                pcr_oi = put_oi / call_oi if call_oi > 0 else 0
                
                # Dias até vencimento
                days_to_expiry = calls_expiry[0]['days_to_expiry'] if calls_expiry else puts_expiry[0]['days_to_expiry']
                
                cursor.execute('''
                    INSERT OR REPLACE INTO options_chain 
                    (underlying, expiry_date, total_calls, total_puts, total_volume, total_open_interest,
                     max_volume_call, max_volume_put, max_oi_call, max_oi_put,
                     avg_iv_calls, avg_iv_puts, iv_skew, strike_range_min, strike_range_max,
                     atm_strike, pcr_volume, pcr_oi, days_to_expiry)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    underlying, expiry, total_calls, total_puts, total_volume, total_oi,
                    max_vol_call, max_vol_put, max_oi_call, max_oi_put,
                    avg_iv_calls, avg_iv_puts, iv_skew, strike_min, strike_max,
                    atm_strike, pcr_volume, pcr_oi, days_to_expiry
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao salvar resumos avançados: {e}")
    
    def collect_all_options(self, symbols=['PETR4', 'VALE3']):
        """
        Coleta opções para múltiplos símbolos
        
        Args:
            symbols (list): Lista símbolos para coletar
            
        Returns:
            int: Total de opções coletadas
        """
        print("🚀 Iniciando coleta completa de opções...")
        
        total_collected = 0
        
        for symbol in symbols:
            print(f"\n📊 Processando {symbol}...")
            
            # Coleta dados
            options_data = self.collect_options_data_alternative(symbol)
            
            if options_data['success']:
                # Salva no banco
                saved = self.save_options_data(options_data)
                total_collected += saved
                print(f"✅ {symbol}: {saved} opções salvas")
            else:
                print(f"❌ Falha na coleta de {symbol}")
        
        print(f"\n🎉 Coleta concluída! {total_collected} opções coletadas.")
        return total_collected
    
    def get_options_by_underlying(self, underlying, limit=100):
        """
        Obtém opções de um ativo específico
        
        Args:
            underlying (str): Símbolo ativo
            limit (int): Limite registros
            
        Returns:
            pd.DataFrame: Opções encontradas
        """
        try:
            conn = sqlite3.connect(db.db_path)
            
            query = '''
                SELECT * FROM options_data 
                WHERE underlying = ? 
                ORDER BY expiry_date, option_type, strike 
                LIMIT ?
            '''
            
            result = pd.read_sql_query(query, conn, params=(underlying, limit))
            conn.close()
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao buscar opções {underlying}: {e}")
            return pd.DataFrame()
    
    def get_chain_summary(self, underlying=None):
        """
        Obtém resumo das chains
        
        Args:
            underlying (str, optional): Filtrar por ativo
            
        Returns:
            pd.DataFrame: Resumo chains
        """
        try:
            conn = sqlite3.connect(db.db_path)
            
            if underlying:
                query = '''
                    SELECT * FROM options_chain 
                    WHERE underlying = ? 
                    ORDER BY expiry_date DESC
                '''
                result = pd.read_sql_query(query, conn, params=(underlying,))
            else:
                query = '''
                    SELECT * FROM options_chain 
                    ORDER BY underlying, expiry_date DESC
                '''
                result = pd.read_sql_query(query, conn)
            
            conn.close()
            return result
            
        except Exception as e:
            print(f"❌ Erro ao buscar resumo chains: {e}")
            return pd.DataFrame()
    
    def get_top_volume_options(self, limit=10):
        """
        Obtém opções com maior volume
        
        Args:
            limit (int): Limite de registros
            
        Returns:
            pd.DataFrame: Top volume opções
        """
        try:
            conn = sqlite3.connect(db.db_path)
            
            query = '''
                SELECT symbol, underlying, option_type, strike, expiry_date, 
                       price, volume, open_interest, implied_volatility
                FROM options_data 
                WHERE volume > 0
                ORDER BY volume DESC 
                LIMIT ?
            '''
            
            result = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao buscar top volume: {e}")
            return pd.DataFrame()
    
    def get_options_analysis(self, underlying):
        """
        Análise completa das opções de um ativo
        
        Args:
            underlying (str): Símbolo ativo
            
        Returns:
            dict: Análise completa
        """
        try:
            options_df = self.get_options_by_underlying(underlying, limit=1000)
            
            if options_df.empty:
                return {}
            
            # Estatísticas básicas
            total_options = len(options_df)
            total_calls = len(options_df[options_df['option_type'] == 'CALL'])
            total_puts = len(options_df[options_df['option_type'] == 'PUT'])
            
            # Volume e OI
            total_volume = options_df['volume'].sum()
            total_oi = options_df['open_interest'].sum()
            avg_iv = options_df['implied_volatility'].mean()
            
            # Opção com maior volume
            max_volume_idx = options_df['volume'].idxmax()
            max_volume_option = options_df.loc[max_volume_idx]
            
            return {
                'total_options': total_options,
                'total_calls': total_calls,
                'total_puts': total_puts,
                'total_volume': total_volume,
                'total_oi': total_oi,
                'avg_iv': avg_iv,
                'max_volume_option': {
                    'symbol': max_volume_option['symbol'],
                    'type': max_volume_option['option_type'],
                    'strike': max_volume_option['strike'],
                    'volume': max_volume_option['volume']
                }
            }
            
        except Exception as e:
            print(f"❌ Erro na análise {underlying}: {e}")
            return {}

# Instância global
options_collector = OptionsCollector()