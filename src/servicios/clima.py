import requests

class ServicioClimaAburra:
    """
    Servicio de telemetría meteorológica en tiempo real para el Valle de Aburrá.
    Cero autenticación (Open-Meteo No-Auth).
    """
    NODOS_ABURRA = {
        "Medellin_Centro": {"lat": 6.2442, "lon": -75.5812},
        "El_Poblado": {"lat": 6.2089, "lon": -75.5684},
        "Belen": {"lat": 6.2319, "lon": -75.6105},
        "Envigado": {"lat": 6.1759, "lon": -75.5917},
        "Bello": {"lat": 6.3373, "lon": -75.5579},
        "Sabaneta": {"lat": 6.1515, "lon": -75.6166}
    }

    def __init__(self):
        self.url_base = "https://api.open-meteo.com/v1/forecast"

    def obtener_condiciones(self, nombre_nodo: str = "Medellin_Centro") -> dict:
        coordenadas = self.NODOS_ABURRA.get(nombre_nodo, self.NODOS_ABURRA["Medellin_Centro"])
        parametros = {
            "latitude": coordenadas["lat"],
            "longitude": coordenadas["lon"],
            "current": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m",
            "timezone": "America/Bogota"
        }

        try:
            resp = requests.get(self.url_base, params=parametros, timeout=4)
            resp.raise_for_status()
            datos = resp.json()["current"]
            viento = datos["wind_speed_10m"]
            lluvia = datos["precipitation"]

            # Factor de reducción de velocidad: viento fuerte reduce rendimiento
            factor_velocidad = 0.80 if viento > 25.0 else (0.90 if viento > 15.0 else 1.0)

            return {
                "nodo": nombre_nodo,
                "temperatura_c": datos["temperature_2m"],
                "lluvia_mm": lluvia,
                "viento_kmh": viento,
                "factor_velocidad": factor_velocidad,
                "vuelo_seguro": lluvia < 2.0 and viento < 35.0
            }
        except Exception as e:
            # Tolerancia a fallos: valores por defecto si no hay conexión
            return {
                "nodo": nombre_nodo,
                "temperatura_c": 22.0,
                "lluvia_mm": 0.0,
                "viento_kmh": 12.0,
                "factor_velocidad": 1.0,
                "vuelo_seguro": True,
                "fallback": True
            }