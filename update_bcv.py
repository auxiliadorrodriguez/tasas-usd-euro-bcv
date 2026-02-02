import json, os, datetime, requests
from bs4 import BeautifulSoup

FILE = "tasa_actual.json"
URL_BCV = "https://www.bcv.org.ve/"

def get_bcv_rates():
    """Extrae las tasas y la fecha de vigencia directamente de la web del BCV."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(URL_BCV, headers=headers, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        usd = soup.find('div', id='dolar').find('strong').text.strip().replace(',', '.')
        eur = soup.find('div', id='euro').find('strong').text.strip().replace(',', '.')
        
        # Extraer fecha de vigencia (ej: "Viernes, 30 Enero 2026")
        fecha_raw = soup.find('span', class_='date-display-single').text.strip()
        
        meses = {
            "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
            "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
            "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
        }
        
        partes = fecha_raw.split()
        fecha_iso = f"{partes[3]}-{meses[partes[2]]}-{partes[1].zfill(2)}"
        
        return {"usd": float(usd), "eur": float(eur), "date": fecha_iso}
    except Exception as e:
        print(f"Error en scraping: {e}")
        return None

def load():
    if not os.path.exists(FILE):
        return {"current": None, "previous": None, "next": {"usd": None, "eur": None, "date": None}}
    with open(FILE) as f:
        return json.load(f)

# ---- Lógica Principal ----
bcv_data = get_bcv_rates()

if bcv_data:
    data = load()
    # Usamos la fecha actual de Venezuela (UTC-4)
    hoy = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)).date()
    fecha_bcv = datetime.datetime.strptime(bcv_data["date"], "%Y-%m-%d").date()

    # Si la fecha que publica el BCV es FUTURA respecto a hoy
    if fecha_bcv > hoy:
        # Solo actualizamos 'next' si es una fecha nueva
        if data["next"]["date"] != bcv_data["date"]:
            data["next"] = bcv_data
            print(f"Nueva tasa 'next' detectada para el {bcv_data['date']}")
    
    # Si la fecha del BCV es HOY o ya pasó (y es más reciente que nuestra current)
    elif fecha_bcv >= hoy:
        if data["current"] is None or bcv_data["date"] > data["current"]["date"]:
            data["previous"] = data["current"]
            data["current"] = bcv_data
            # Al entrar una nueva current, limpiamos next si ya se alcanzó esa fecha
            if data["next"]["date"] == bcv_data["date"]:
                data["next"] = {"usd": None, "eur": None, "date": None}
            print(f"Actualizada tasa 'current' al {bcv_data['date']}")

    # Guardar cambios
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)
