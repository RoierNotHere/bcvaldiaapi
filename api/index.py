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

        # 1. Si pasaron menos de 30s, devolvemos lo guardado
        if CACHE_DATOS is not None and segundos_transcurridos < TIEMPO_RETIENE_CACHE:
            return CACHE_DATOS, f"Cache (restan {int(TIEMPO_RETIENE_CACHE - segundos_transcurridos)}s)"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        precio_bcv = CACHE_DATOS["bcv"] if CACHE_DATOS else "0.00"
        precio_usdt = CACHE_DATOS["usdt"] if CACHE_DATOS else "0.00"

        # 2. Consultar BCV Oficial desde DolarApi
        try:
            url_bcv = "https://ve.dolarapi.com/v1/dolares/oficial"
            req_bcv = urllib.request.Request(url_bcv, headers=headers, method='GET')
            with urllib.request.urlopen(req_bcv, timeout=6) as res_bcv:
                data_bcv = json.loads(res_bcv.read().decode('utf-8'))
                precio_bcv = f"{float(data_bcv['promedio']):.2f}"
        except Exception:
            pass # Si falla DolarApi, mantiene el último BCV de la caché

        # 3. Consultar USDT Binance P2P desde CriptoYa
        try:
            url_usdt = "https://criptoya.com/api/binancep2p/USDT/VES/1"
            req_usdt = urllib.request.Request(url_usdt, headers=headers, method='GET')
            with urllib.request.urlopen(req_usdt, timeout=6) as res_usdt:
                data_usdt = json.loads(res_usdt.read().decode('utf-8'))
                if "ask" in data_usdt:
                    precio_usdt = f"{float(data_usdt['ask']):.2f}"
        except Exception:
            pass # Si falla CriptoYa, mantiene el último USDT de la caché

        resultado = {
            "bcv": precio_bcv,
            "usdt": precio_usdt
        }

        # Actualizamos la caché global
        CACHE_DATOS = resultado
        ULTIMA_PETICION_TIME = tiempo_actual

        return resultado, "Live Data"

    def do_GET(self):
        datos_precios, fuente = self.consultar_precios()

        respuesta = {
            "moneda": "USD / VES",
            "bcv": datos_precios["bcv"],
            "usdt": datos_precios["usdt"],
            "fuente": fuente,
            "status": "online" if datos_precios["bcv"] != "0.00" else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode('utf-8'))
