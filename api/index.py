from http.server import BaseHTTPRequestHandler
import cloudscraper
import json

class handler(BaseHTTPRequestHandler):

    def obtener_p2p_binance(self):
        # Endpoint de CriptoYa para Binance P2P USDT/VES
        url = "https://criptoya.com/api/binancep2p/USDT/VES/1"
        
        scraper = cloudscraper.create_scraper()
        
        try:
            res = scraper.get(url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                # 'ask' representa la mejor oferta de venta en P2P
                precio_ask = data.get("ask")
                
                if precio_ask:
                    return f"{float(precio_ask):.2f}"
                
                return "Dato_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return "Error_Conexion"

    def do_GET(self):
        precio_usdt = self.obtener_p2p_binance()

        datos = {
            "moneda": "USDT",
            "par": "VES",
            "origen": "Binance P2P (vía CriptoYa)",
            "precio": precio_usdt,
            "status": "online" if "Error" not in precio_usdt and "Dato" not in precio_usdt else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
