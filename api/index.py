from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import time

# --- CACHÉ EN MEMORIA (30 SEGUNDOS) ---
CACHE_DATOS = None
ULTIMA_PETICION_TIME = 0
TIEMPO_RETIENE_CACHE = 30 

class handler(BaseHTTPRequestHandler):

    def consultar_precios(self):
        global CACHE_DATOS, ULTIMA_PETICION_TIME
        
        tiempo_actual = time.time()
        segundos_transcurridos = tiempo_actual - ULTIMA_PETICION_TIME

        # 1. Si no han pasado 30s, servimos desde la caché
        if CACHE_DATOS is not None and segundos_transcurridos < TIEMPO_RETIENE_CACHE:
            return CACHE_DATOS, f"Cache (restan {int(TIEMPO_RETIENE_CACHE - segundos_transcurridos)}s)"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        # Extracción de fallbacks de la caché previa
        bcv_usd = float(CACHE_DATOS["bcv"]["usd"]) if CACHE_DATOS else 0.0
        bcv_euro = float(CACHE_DATOS["bcv"]["euro"]) if CACHE_DATOS else 0.0
        
        binance_c = float(CACHE_DATOS["binance_p2p"]["usdt_compra"]) if CACHE_DATOS else 0.0
        binance_v = float(CACHE_DATOS["binance_p2p"]["usdt_venta"]) if CACHE_DATOS else 0.0
        
        dolarvzla_c = float(CACHE_DATOS["dolarvzla"]["usdt_compra"]) if CACHE_DATOS else 0.0
        dolarvzla_v = float(CACHE_DATOS["dolarvzla"]["usdt_venta"]) if CACHE_DATOS else 0.0

        # 2. Consultar BCV USD y EURO desde DolarApi
        try:
            url_dolarapi = "https://ve.dolarapi.com/v1/cotizaciones"
            req_dolar = urllib.request.Request(url_dolarapi, headers=headers, method='GET')
            with urllib.request.urlopen(req_dolar, timeout=6) as res_dolar:
                data_dolar = json.loads(res_dolar.read().decode('utf-8'))
                for item in data_dolar:
                    if item.get("moneda") == "USD":
                        bcv_usd = float(item.get("promedio", 0.0))
                    elif item.get("moneda") == "EUR":
                        bcv_euro = float(item.get("promedio", 0.0))
        except Exception:
            pass

        # 3. Consultar Binance P2P desde CriptoYa (totalAsk = Venta, totalBid = Compra)
        try:
            url_criptoya = "https://criptoya.com/api/saldo/USDT/VES/1"
            req_criptoya = urllib.request.Request(url_criptoya, headers=headers, method='GET')
            with urllib.request.urlopen(req_criptoya, timeout=6) as res_criptoya:
                data_criptoya = json.loads(res_criptoya.read().decode('utf-8'))
                binance_c = float(data_criptoya.get("totalBid", 0.0))  # Compra
                binance_v = float(data_criptoya.get("totalAsk", 0.0))  # Venta
        except Exception:
            pass

        # 4. Consultar DolarVzla (Ratio USDT a VES)
        try:
            url_dvzla = "https://api.dolarvzla.com/public/usdt/exchange-rate"
            req_dvzla = urllib.request.Request(url_dvzla, headers=headers, method='GET')
            with urllib.request.urlopen(req_dvzla, timeout=6) as res_dvzla:
                data_dvzla = json.loads(res_dvzla.read().decode('utf-8'))
                
                # Manejo de respuesta directo o anidado en 'current'
                datos_rate = data_dvzla.get("current", data_dvzla)
                dolarvzla_c = float(datos_rate.get("buy", datos_rate.get("bid", 0.0)))
                dolarvzla_v = float(datos_rate.get("sell", datos_rate.get("ask", 0.0)))
        except Exception:
            pass

        # --- CÁLCULOS MATEMÁTICOS Y MATRICES ---
        promedio_binance = (binance_c + binance_v) / 2 if (binance_c and binance_v) else 0.0
        diferencia_absoluta = promedio_binance - bcv_usd if (promedio_binance and bcv_usd) else 0.0
        diferencia_porcentual = (diferencia_absoluta / bcv_usd * 100) if bcv_usd else 0.0
        promedio_dolarvzla = (dolarvzla_c + dolarvzla_v) / 2 if (dolarvzla_c and dolarvzla_v) else 0.0

        resultado = {
            "bcv": {
                "usd": f"{bcv_usd:.2f}",
                "euro": f"{bcv_euro:.2f}"
            },
            "binance_p2p": {
                "usdt_compra": f"{binance_c:.2f}",
                "usdt_venta": f"{binance_v:.2f}",
                "usdt_promedio": f"{promedio_binance:.2f}"
            },
            "brecha_binance_bcv": {
                "diferencia_absoluta": f"{diferencia_absoluta:.2f}",
                "diferencia_porcentual": f"{diferencia_porcentual:.2f}%"
            },
            "dolarvzla": {
                "usdt_compra": f"{dolarvzla_c:.2f}",
                "usdt_venta": f"{dolarvzla_v:.2f}",
                "usdt_promedio": f"{promedio_dolarvzla:.2f}"
            }
        }

        CACHE_DATOS = resultado
        ULTIMA_PETICION_TIME = tiempo_actual

        return resultado, "Live Data"

    def do_GET(self):
        datos_precios, fuente = self.consultar_precios()

        respuesta = {
            "fuente": fuente,
            "status": "online" if float(datos_precios["bcv"]["usd"]) > 0 else "offline",
            "datos": datos_precios
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(respuesta, ensure_ascii=False).encode('utf-8'))
