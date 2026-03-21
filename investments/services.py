import requests
from decimal import Decimal

class FinanceService:
    # Tu token real de Banxico
    BMX_TOKEN = "6da73080abf1112cf0fcd83b92a61c9574d99da1d327b39a2716f9d5044bb776"

    @staticmethod
    def get_crypto_price_mxn(api_id):
        """Traducido de coingecko.php"""
        if not api_id:
            return None
            
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={api_id}&vs_currencies=mxn"
        headers = {'User-Agent': 'BIOR-Invest-App'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Retorna el precio como Float para cálculos
                return float(data[api_id]['mxn']) if api_id in data else None
        except Exception as e:
            print(f"Error en CoinGecko Service: {e}")
        return None

    @classmethod
    def get_banxico_data(cls, serie='SF43936'):
        """Traducido de banxico.php y get_cetes_rate.php"""
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/oportuno"
        headers = {
            "Bmx-Token": cls.BMX_TOKEN,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Extraemos el dato según la estructura de la API de Banxico
                valor = data['bmx']['series'][0]['datos'][0]['dato']
                return float(valor)
        except Exception as e:
            print(f"Error en Banxico Service: {e}")
        return 0.00