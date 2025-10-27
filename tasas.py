from datetime import datetime, timedelta
import requests
import json
import os

class DolarVzlaSmart:
    API_URL = "https://api.dolarvzla.com/public/exchange-rate/list"

    def __init__(self):
        texto = """
        01/01/2025 - Año Nuevo - FN
        03/03/2025 - Carnaval - FN
        04/03/2025 - Carnaval - FN
        17/04/2025 - Semana Santa - FN
        18/04/2025 - Semana Santa - FN
        19/04/2025 - Semana Santa - FN
        01/05/2025 - Día del Trabajador - FN
        24/06/2025 - Batalla de Carabobo - FN
        05/07/2025 - Día de la Independencia - FN
        24/07/2025 - Natalicio del Libertador - FN
        12/10/2025 - Día de la Resistencia Indígena - FN
        24/12/2025 - Nochebuena - FN
        25/12/2025 - Natividad de Nuestro Señor - FN
        31/12/2025 - Fin de Año - FN
        06/01/2025 - Día de Reyes - FBN
        13/01/2025 - Día de la Divina Pastora - FBN
        19/03/2025 - Día de San José - FBN
        29/05/2025 - Ascensión del Señor - FBN
        13/06/2025 - Día de San Antonio - FBN
        19/06/2025 - Corpus Christi - FBN
        23/06/2025 - Día de San Pedro y San Pablo - FBN
        15/08/2025 - Asunción de Nuestra Señora - FBN
        11/09/2025 - Día de la Virgen de Coromoto - FBN
        26/10/2025 - Día de José Gregorio Hernández - FBN
        01/11/2025 - Día de Todos los Santos - FBN
        18/11/2025 - Día de la Virgen del Rosario de Chiquinquirá - FBN
        08/12/2025 - Día de la Inmaculada Concepción - FBN
        """
        self.feriados = self._parse_feriados(texto)

    def _parse_feriados(self, texto):
        fechas = set()
        for línea in texto.strip().splitlines():
            try:
                parte = línea.strip().split(" - ")[0]
                fechas.add(datetime.strptime(parte, "%d/%m/%Y").strftime("%Y-%m-%d"))
            except Exception:
                continue
        return fechas

    def es_feriado(self, fecha):
        return fecha.strftime("%Y-%m-%d") in self.feriados

    def es_finde(self, fecha):
        return fecha.weekday() >= 5

    def es_habil(self, fecha):
        return not (self.es_finde(fecha) or self.es_feriado(fecha))

    def descargar_rates(self):
        r = requests.get(self.API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        rates = sorted(data["rates"], key=lambda x: x["date"], reverse=True)
        return rates

    def seleccionar_rates(self, rates):
        hoy = datetime.now().date()
        fecha_mas_reciente = datetime.strptime(rates[0]["date"], "%Y-%m-%d").date()

        # Si la API ya tiene una fecha FUTURA → ya publicaron la "next"
        if fecha_mas_reciente > hoy:
            necesito = 3
        else:
            necesito = 2 if self.es_habil(hoy) else 3

        if len(rates) < necesito:
            raise ValueError(f"La API solo devolvió {len(rates)} registros")
        return rates[:necesito]

    def pct(self, curr, prev):
        return {
            "usd": round(((curr["usd"] - prev["usd"]) / prev["usd"]) * 100, 10),
            "eur": round(((curr["eur"] - prev["eur"]) / prev["eur"]) * 100, 10),
        }

    def transformar(self):
        rates = self.seleccionar_rates(self.descargar_rates())
        if len(rates) == 2:
            curr, prev = rates
            out = {
                "current": curr,
                "previous": prev,
                "next": {"usd": None, "eur": None, "date": None},
                "changePercentage": self.pct(curr, prev),
            }
        else:
            next, curr, prev = rates
            out = {
                "current": curr,
                "previous": prev,
                "next": next,
                "changePercentage": self.pct(curr, prev),
            }
        return out

if __name__ == "__main__":
    dv = DolarVzlaSmart()
    import json, os
    OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "tasa_actual.json")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dv.transformar(), f, ensure_ascii=False, indent=2)
    print("JSON guardado en:", OUTPUT_PATH)
