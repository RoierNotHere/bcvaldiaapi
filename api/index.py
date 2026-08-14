from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import time

# --- VARIABLES GLOBALES PARA LA CACHÉ ---
PRECIO_EN_CACHE = None
ULTIMA_PETICION_TIME = 0
TIEMPO_RETIENE_CACHE = 30  # Protege el límite de CriptoYa (30 segundos entre llamadas reales)

class handler(BaseHTTPRequestHandler):

    def consultar_criptoya(self):
        global PRECIO_EN_CACHE, ULTIMA_PETICION_TIME
        
        tiempo_actual = time.time()
        segundos_transcurridos = tiempo_actual - ULTIMA_PETICION_TIME

        # 1. SI HAN PASADO MENOS DE 30s, DEVOLVEMOS EL DATO GUARDADO
        if PRECIO_EN_CACHE is not None and segundos_transcurridos < TIEMPO_RETIENE_CACHE:
            return PRECIO_EN_CACHE, f"Cache (espera {int(TIEMPO_RETIENE_CACHE - segundos_transcurridos)}s)"

        # 2. SI YA PASARON LOS 30s, HACEMOS LA CONSULTA REAL A CRIPTOYA
        url = "https://criptoya.com/api/binancep2p/USDT/VES/1"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    precio_ask = data.get("ask")
                    
                    if precio_ask:
                        # Guardamos el nuevo precio y reseteamos el reloj
                        precio_final = f"{float(precio_ask):.2f}"
                        PRECIO_EN_CACHE = precio_final
                        ULTIMA_PETICION_TIME = tiempo_actual
                        
                        return precio_final, "CriptoYa Live"
            
            # Si falla CriptoYa pero teníamos algo guardado, entregamos lo viejo
            if PRECIO_EN_CACHE:
                return PRECIO_EN_CACHE, "Cache Fallback"
                
            return "Dato_No_Encontrado", "Error"

        except Exception as e:
            if PRECIO_EN_CACHE:
                return PRECIO_EN_CACHE, "Cache Fallback Exception"
            return "Error_Conexion", "Error"

    def do_GET(self):
        precio, fuente = self.consultar_criptoya()

        datos = {
            "moneda": "USDT",
            "par": "VES",
            "origen": "Binance P2P (vía CriptoYa)",
            "precio": precio,
            "fuente": fuente,
            "status": "online" if "Error" not in precio and "Dato" not in precio else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
