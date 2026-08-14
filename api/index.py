from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import time

# --- CACHÉ EN MEMORIA (30 SEGUNDOS) ---
CACHE_DATOS = None
ULTIMA_PETICION_TIME = 0
TIEMPO_RETIENE_CACHE = 30 

class handler(BaseHTTPRequestHandler):

    def consultar_dolar_api(self):
        global CACHE_DATOS, ULTIMA_PETICION_TIME
        
        tiempo_actual = time.time()
        segundos_transcurridos = tiempo_actual - ULTIMA_PETICION_TIME

        # 1. Si pasaron menos de 30 segundos, entregamos la caché
        if CACHE_DATOS is not None and segundos_transcurridos < TIEMPO_RETIENE_CACHE:
            return CACHE_DATOS, f"Caché (restan {int(TIEMPO_RETIENE_CACHE - segundos_transcurridos)}s)"

        # 2. Consultamos DolarApi Venezuela
        url_bcv = "https://ve.dolarapi.com/v1/dolares/oficial"
        url_usdt = "https://ve.dolarapi.com/v1/dolares/paralelo"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        try:
            # Obtener BCV
            req_bcv = urllib.request.Request(url_bcv, headers=headers, method='GET')
            with urllib.request.urlopen(req_bcv, timeout=6) as res_bcv:
                data_bcv = json.loads(res_bcv.read().decode('utf-8'))
                precio_bcv = f"{float(data_bcv['promedio']):.2f}"

            # Obtener Paralelo / USDT
            req_usdt = urllib.request.Request(url_usdt, headers=headers, method='GET')
            with urllib.request.urlopen(req_usdt, timeout=6) as res_usdt:
                data_usdt = json.loads(res_usdt.read().decode('utf-8'))
                precio_usdt = f"{float(data_usdt['promedio']):.2f}"

            # Construimos el objeto resultante
            resultado = {
                "bcv": precio_bcv,
                "usdt": precio_usdt
            }

            CACHE_DATOS = resultado
            ULTIMA_PETICION_TIME = tiempo_actual

            return resultado, "DolarApi Live"

        except Exception as e:
            # Si hay fallo puntual, devolvemos la última caché si existe
            if CACHE_DATOS:
                return CACHE_DATOS, "Caché Fallback"
            
            return {"bcv": "0.00", "usdt": "0.00"}, "Error_Conexion"

    def do_GET(self):
        datos_precios, fuente = self.consultar_dolar_api()

        respuesta = {
            "moneda": "USD / VES",
            "origen": "DolarApi Venezuela",
            "bcv": datos_precios["bcv"],
            "usdt": datos_precios["usdt"],
            "fuente": fuente,
            "status": "online" if fuente != "Error_Conexion" else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode('utf-8'))
