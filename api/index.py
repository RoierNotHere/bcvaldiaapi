from http.server import BaseHTTPRequestHandler
import cloudscraper
import json

class handler(BaseHTTPRequestHandler):

    def obtener_dolar_bcv(self):
        # Endpoint directo que trae la tasa oficial del BCV sin bloqueos de IP
        url = "https://criptoya.com/api/bcv"
        
        scraper = cloudscraper.create_scraper()
        
        try:
            res = scraper.get(url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                # Criptoya devuelve el valor del dólar BCV directo en un campo float/number
                precio = data.get("usd") or data.get("price")
                if precio:
                    return f"{float(precio):.2f}"
                
                return "Dato_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return "Error_Conexion"

    def do_GET(self):
        dolar_precio = self.obtener_dolar_bcv()

        datos = {
            "moneda": "USD",
            "origen": "Banco Central de Venezuela",
            "precio": dolar_precio,
            "status": "online" if "Error" not in dolar_precio and "Dato" not in dolar_precio else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
