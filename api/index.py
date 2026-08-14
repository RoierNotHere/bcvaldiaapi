from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json
import random
import time

class handler(BaseHTTPRequestHandler):

    def obtener_dolar_bcv(self):
        # Usamos una fuente espejo confiable que replica la tasa del BCV sin geobloqueo
        url = "https://monitordolarvenezuela.com/"
        
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
            res = scraper.get(url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscamos la casilla del BCV en la plataforma
                # Monitor Dolar suele marcar la tasa oficial en contenedores específicos
                box = soup.find("div", {"id": "bcv"}) or soup.find("div", class_="bcv")
                
                if not box:
                    # Búsqueda alternativa por texto en la página
                    for card in soup.find_all("div"):
                        if "BCV" in card.get_text():
                            box = card
                            break

                if box:
                    # Buscamos la etiqueta del precio dentro de la casilla
                    precio_tag = box.find("h3") or box.find("p") or box.find("span", class_="precio")
                    if precio_tag:
                        precio_raw = precio_tag.get_text(strip=True).replace('Bs.', '').replace('Bs', '').strip()
                        precio_limpio = precio_raw.replace('.', '').replace(',', '.')
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
            "origen": "Banco Central de Venezuela (vía Espejo)",
            "precio": dolar_precio,
            "status": "online" if "Error" not in dolar_precio else "offline"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
