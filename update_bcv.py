import json, os, datetime, requests
from bs4 import BeautifulSoup

FILE = "tasa_actual.json"
URL_BCV = "https://www.bcv.org.ve/"

def get_bcv_rates():
    """Extrae solo los precios. La fecha la manejamos por sistema."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # verify=False y un timeout corto para que no se quede pegado
        response = requests.get(URL_BCV, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        usd = soup.find('div', id='dolar').find('strong').text.strip().replace(',', '.')
        eur = soup.find('div', id='euro').find('strong').text.strip().replace(',', '.')
        
        return {"usd": float(usd), "eur": float(eur)}
    except Exception as e:
        print(f"Error rápido: {e}")
        return None

def load():
    if not os.path.exists(FILE):
        return {"current": None, "previous": None, "next": {"usd": None, "eur": None, "date": None}}
    with open(FILE) as f:
        return json.load(f)

# ---- Proceso ----
bcv = get_bcv_rates()

if bcv:
    data = load()
    # Obtenemos la fecha de hoy en Venezuela (UTC-4)
    hoy = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4))
    hoy_str = hoy.strftime("%Y-%m-%d")
    mañana_str = (hoy + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # Si no hay datos, inicializamos
    if data["current"] is None:
        data["current"] = {"usd": bcv["usd"], "eur": bcv["eur"], "date": hoy_str}
        print("Inicializado archivo por primera vez.")
    
    # ¿Es una tasa nueva? (Diferente a la que tenemos en current)
    elif bcv["usd"] != data["current"]["usd"]:
        
        # Si la tasa nueva es la que ya teníamos en 'next', la movemos a 'current'
        if bcv["usd"] == data["next"]["usd"]:
            data["previous"] = data["current"]
            data["current"] = data["next"]
            data["next"] = {"usd": None, "eur": None, "date": None}
            print("La tasa 'next' ahora es la 'current'.")
        else:
            # Si es una tasa totalmente nueva (típico de las 4:30 PM)
            # La guardamos en 'next' porque el BCV siempre publica para el día siguiente
            data["next"] = {"usd": bcv["usd"], "eur": bcv["eur"], "date": mañana_str}
            print(f"Nueva tasa detectada y guardada como 'next' para {mañana_str}")

    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)
