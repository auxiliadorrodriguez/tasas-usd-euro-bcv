import json, os, datetime, requests
from bs4نهار import BeautifulSoup
import urllib3

# Deshabilitar advertencias de SSL si el certificado del BCV presenta problemas temporales
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FILE = "tasa_actual.json"
URL_BCV = "https://www.bcv.org.ve/"

def limpiar_valor(texto):
    """Limpia el texto de la tasa: remueve puntos de miles y cambia la coma decimal por punto."""
    # Ejemplo: "45.123,45" -> "45123.45"
    texto = texto.strip()
    # Si usa punto para miles y coma para decimales
    if '.' in texto and ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    elif ',' in texto:
        texto = texto.replace(',', '.')
    return float(texto)

def get_bcv_rates():
    """Extrae las tasas y la fecha de vigencia directamente de la web del BCV."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL_BCV, headers=headers, verify=False, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Forma robusta de encontrar el dolar y el euro en la estructura actual del BCV
        div_dolar = soup.find('div', class_='dinero') or soup.find('div', id='dolar')
        div_euro = soup.find('div', id='euro')

        # Si no encuentra por ID directo, buscamos dentro de las cajas de tipo 'view-tipo-de-cambio'
        if not div_dolar:
            dolar_elem = soup.select_one('.view-tipo-de-cambio .dolar strong, #dolar strong')
        else:
            dolar_elem = div_dolar.find('strong')

        if not div_euro:
            euro_elem = soup.select_one('.view-tipo-de-cambio .euro strong, #euro strong')
        else:
            euro_elem = div_euro.find('strong')

        # Extracción alternativa general por si cambian los contenedores
        if not dolar_elem:
            # Buscar el texto USD o Dolar en la página
            pass

        # Extracción usando los selectores actuales más comunes del BCV
        # El BCV suele usar contenedores con id 'dolar' y 'euro' o clases específicas
        val_usd_str = soup.find('div', id='dolar').find('strong').text.strip() if soup.find('div', id='dolar') else soup.select_one('#dolar strong').text.strip()
        val_eur_str = soup.find('div', id='euro').find('strong').text.strip() if soup.find('div', id='euro') else soup.select_one('#euro strong').text.strip()

        usd = limpiar_valor(val_usd_str)
        eur = limpiar_valor(val_eur_str)
        
        # Extraer fecha de vigencia (ej: "Viernes, 30 Enero 2026")
        fecha_tag = soup.find('span', class_='date-display-single') or soup.find('div', class_='field-tipo-de-cambio')
        fecha_raw = fecha_tag.text.strip() if fecha_tag else ""
        
        # Intentar extraer la fecha mediante palabras clave si el span cambia
        meses = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
        }
        
        # Buscar el formato de fecha en el texto extraído
        partes = fecha_raw.lower().split()
        dia, mes_str, anio = None, None, None
        
        for i, palabra in enumerate(partes):
            if palabra in meses:
                mes_str = meses[palabra]
                if i > 0:
                    # Intentar tomar el número del día anterior o cercano
                    for p in partes[i-2:i]:
                        if p.isdigit():
                            dia = p.zfill(2)
                if i < len(partes) - 1:
                    for p in partes[i+1:i+3]:
                        if p.isdigit() and len(p) == 4:
                            anio = p
                            
        # Si falló el parsing anterior, usar la fecha actual del servidor como respaldo o ajustar
        if not dia or not mes_str or not anio:
            # Fallback seguro usando la fecha actual de Venezuela
            hoy_ve = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)
            fecha_iso = hoy_ve.strftime("%Y-%m-%d")
        else:
            fecha_iso = f"{anio}-{mes_str}-{dia}"
        
        return {"usd": usd, "eur": eur, "date": fecha_iso}
    except Exception as e:
        print(f"Error en scraping: {e}")
        return None

def load():
    if not os.path.exists(FILE):
        return {"current": None, "previous": None, "next": {"usd": None, "eur": None, "date": None}}
    with open(FILE, encoding='utf-8') as f:
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
        if data["next"]["date"] != bcv_data["date"]:
            data["next"] = bcv_data
            print(f"Nueva tasa 'next' detectada para el {bcv_data['date']}")
    
    # Si la fecha del BCV es HOY o ya pasó (y es más reciente que nuestra current)
    elif fecha_bcv >= hoy:
        if data["current"] is None or bcv_data["date"] > data["current"]["date"]:
            data["previous"] = data["current"]
            data["current"] = bcv_data
            if data["next"]["date"] == bcv_data["date"]:
                data["next"] = {"usd": None, "eur": None, "date": None}
            print(f"Actualizada tasa 'current' al {bcv_data['date']}")

    # Guardar cambios
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
