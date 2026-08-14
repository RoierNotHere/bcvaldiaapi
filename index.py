from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json
import random
import time
import urllib3

# Desactivamos advertencias de certificados viejos del BCV
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class handler(BaseHTTPRequestHandler):

    def obtener_dolar_bcv(self):
        url = "https://www.bcv.org.ve/"
        
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            
            time.sleep(random.uniform(1.0, 2.0))
            
            # verify=False por los certificados del sitio del BCV
            res = scraper.get(url, headers=headers, timeout=15, verify=False)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscamos la etiqueta <strong class="strong-tb"> dentro del div id="dolar"
                dolar_box = soup.find("div", {"id": "dolar"})
                if dolar_box:
                    tag = dolar_box.find("strong", {"class": "strong-tb"})
                    if tag:
                        precio_raw = tag.get_text(strip=True)
                        precio_limpio = precio_raw.replace(',', '.')
                        precio_float = round(float(precio_limpio), 2)
                        return f"{precio_float:.2f}"
                
                return "Tag_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return "Error_Conexion"

    def do_GET(self):
        dolar_precio = self.obtener_dolar_bcv()

        datos = {
            "moneda": "USD",
            "origen": "Banco Central de Venezuela",
            "precio": dolar_precio,
            "status": "online" if "Error" not in dolar_precio else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))