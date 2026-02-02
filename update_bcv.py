import json, os, datetime, requests
from bs4 import BeautifulSoup

FILE = "tasa_actual.json"
URL_BCV = "https://www.bcv.org.ve/"

def get_bcv_rates():
    """Extrae las tasas oficiales directamente de la web del BCV."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Ignoramos verificación de SSL porque el sitio del BCV suele tener problemas de certificados
        response = requests.get(URL_BCV, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer Dólar
        usd_val = soup.find('div', id='dolar').find('strong').text.strip().replace(',', '.')
        # Extraer Euro
        eur_val = soup.find('div', id='euro').find('strong').text.strip().replace(',', '.')
        
        return {
            "usd": float(usd_val),
            "eur": float(eur_val),
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        print(f"Error extrayendo datos del BCV: {e}")
        return None

def load():
    if not os.path.exists(FILE):
        return {"current": None, "previous": None, "next": None}
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return {"current": None, "previous": None, "next": None}

# ---- Proceso Principal ----
data_bcv = get_bcv_rates()

if data_bcv:
    old = load()
    
    # Solo actualizamos si la fecha es distinta o no hay datos previos
    if old["current"] is None or old["current"]["date"] != data_bcv["date"]:
        new_entry = {
            "date": data_bcv["date"],
            "usd": data_bcv["usd"],
            "eur": data_bcv["eur"]
        }
        
        # Rotación de datos (Mantenemos tu estructura de la captura)
        old["previous"] = old["current"]
        old["current"] = new_entry
        # Nota: 'next' suele ser una proyección, aquí la igualamos al current 
        # o puedes dejarla como estaba si tienes otra fuente para el día siguiente.
        old["next"] = new_entry 
        
        with open(FILE, "w") as f:
            json.dump(old, f, indent=4)
        print(f"Tasas actualizadas: USD {data_bcv['usd']}")
    else:
        print("La tasa para hoy ya está registrada.")
