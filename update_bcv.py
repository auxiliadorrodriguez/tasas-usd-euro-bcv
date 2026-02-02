import json, os, datetime, requests
from bs4 import BeautifulSoup

FILE = "tasa_actual.json"
URL_BCV = "https://www.bcv.org.ve/"

def get_bcv_rates():
    """Extrae solo los precios de forma rápida."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Timeout corto de 10 segundos para no quedar colgados
        response = requests.get(URL_BCV, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        usd = soup.find('div', id='dolar').find('strong').text.strip().replace(',', '.')
        eur = soup.find('div', id='euro').find('strong').text.strip().replace(',', '.')
        
        return {"usd": float(usd), "eur": float(eur)}
    except Exception as e:
        print(f"Error en scraping: {e}")
        return None

def load():
    if not os.path.exists(FILE):
        return {"current": None, "previous": None, "next": {"usd": None, "eur": None, "date": None}}
    with open(FILE) as f:
        return json.load(f)

# ---- Proceso Principal ----
bcv = get_bcv_rates()

if bcv:
    data = load()
    # Calculamos fecha de hoy en Venezuela (UTC-4)
    ahora_ven = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)
    hoy_str = ahora_ven.strftime("%Y-%m-%d")
    manana_str = (ahora_ven + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # Si es la primera vez o el precio cambió respecto al current
    if data["current"] is None or bcv["usd"] != data["current"]["usd"]:
        
        # Si el precio coincide con lo que teníamos en 'next', rotamos
        if bcv["usd"] == data["next"]["usd"]:
            data["previous"] = data["current"]
            data["current"] = data["next"]
            data["next"] = {"usd": None, "eur": None, "date": None}
            print("Rotación completada: next pasó a current.")
        else:
            # Es una tasa nueva (típicamente publicada en la tarde para el día siguiente)
            # Mantenemos la lógica de tu archivo previo
            data["next"] = {"usd": bcv["usd"], "eur": bcv["eur"], "date": manana_str}
            print(f"Nueva tasa detectada. Guardada como 'next' para {manana_str}")

        with open(FILE, "w") as f:
            json.dump(data, f, indent=4)
    else:
        print("No hay cambios en la tasa oficial.")
