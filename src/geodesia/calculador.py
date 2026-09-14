# Módulo de cálculos geodésicos (Haversine) y estimación de tiempo de vuelo (ETA)
# Responsable: Alejandro García Jiménez

import math
from src.excepciones.errores import CoordenadaInvalidaError

class CalculadorGeodesico:
    # Límites geográficos oficiales del Valle de Aburrá:
    # Latitud Norte: 5°58' a 6°30' -> [5.9667, 6.5000]
    # Longitud Oeste: 75°43' a 75°21' -> [-75.7167, -75.3500]
    LAT_MIN_ABURRA: float = 5.9667
    LAT_MAX_ABURRA: float = 6.5000
    LON_MIN_ABURRA: float = -75.7167
    LON_MAX_ABURRA: float = -75.3500

    def __init__(self):
        self.radio_tierra_km: float = 6371

    # se añade funcion no especificada en el documento
    # esto buscando respetar el principio de responsabilidad unica
    def _validar_coordenada(self, coordenada: tuple[float, float]) -> None:
        """Valida que una coordenada sea una tupla numérica y esté estrictamente dentro del Valle de Aburrá."""
        if not isinstance(coordenada, tuple) or len(coordenada) != 2:
            raise CoordenadaInvalidaError(coordenada)
        lat, lon = coordenada
        if not isinstance(lat, (float, int)) or not isinstance(lon, (float, int)):
            raise CoordenadaInvalidaError(coordenada)
        if not (self.LAT_MIN_ABURRA <= lat <= self.LAT_MAX_ABURRA and self.LON_MIN_ABURRA <= lon <= self.LON_MAX_ABURRA):
            raise CoordenadaInvalidaError(
                coordenada,
                f"Coordenadas '{coordenada}' fuera del área operativa del Valle de Aburrá. "
                f"Deben estar delimitadas en latitud [{self.LAT_MIN_ABURRA}, {self.LAT_MAX_ABURRA}] (5°58' a 6°30' N) "
                f"y longitud [{self.LON_MIN_ABURRA}, {self.LON_MAX_ABURRA}] (75°43' a 75°21' W)."
            )


    def calcular_haversine(self, origen: tuple[float, float], destino: tuple[float, float]) -> float:
        
        self._validar_coordenada(origen)
        self._validar_coordenada(destino)

        # Desempaquetado de coordenadas (asumiendo que ingresan en grados decimales)
        lat1, lon1 = origen
        lat2, lon2 = destino
        

        # Las funciones trigonométricas de la librería 'math' requieren 
        # que los ángulos estén en radianes, no en grados. 
        # Calculamos los deltas (diferencias) directamente en radianes.
        dLon = math.radians(lon2 - lon1)
        dLat = math.radians(lat2 - lat1)


        # También es indispensable convertir las latitudes base a radianes 
        # para poder calcular correctamente sus cosenos más adelante.
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        
        
        # Cálculo del 'semiverseno' (haversine) del ángulo central.
        # La variable 'a' representa el cuadrado de la mitad de la distancia de la cuerda 
        # en línea recta entre los dos puntos a través del interior de la esfera.
        # Combina la diferencia de latitudes con el efecto de la diferencia de longitudes, 
        # este último afectado por los cosenos de las latitudes ya que los meridianos 
        # se van estrechando a medida que nos acercamos a los polos.
        a = math.sin(dLat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dLon / 2) ** 2

        # Para prevenir errores de redondeo en cálculos con puntos muy cercanos o antipodales,
        # ajustamos el valor de 'a' para asegurarnos de que esté estrictamente en el rango [0, 1].
        a = max(0.0, min(1.0, a))

        # Cálculo del ángulo central 'c' (en radianes).
        # Se utiliza la función 'atan2' (arcotangente de dos parámetros) en lugar de 'asin' 
        # porque es numéricamente más estable y evita errores de redondeo en distancias 
        # muy grandes o antipodales (puntos opuestos en el planeta).
        # 'c' nos da la distancia angular sobre la superficie de la esfera.

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


        # Conversión de distancia angular a distancia lineal.
        # Multiplicamos el ángulo central 'c' (en radianes) por el radio de la esfera (R).
        # Por definición geométrica, Arco = Radio * Ángulo. Al usar el radio en kilómetros, 
        # el resultado final se obtiene directamente en esa misma unidad métrica.   
        return self.radio_tierra_km * c


    def calcular_tiempo_vuelo_min(self, distancia_km: float, velocidad_km_h: float) -> float:
        # Evitar división por cero o velocidades no válidas
        if velocidad_km_h <= 0.0 or distancia_km <= 0.0:
            return 0.0
        return (distancia_km / velocidad_km_h) * 60.0
