# Módulo de cálculos geodésicos (Haversine) y estimación de tiempo de vuelo (ETA)
# Responsable: Alejandro García Jiménez

import math
from src.excepciones.errores import CoordenadaInvalidaError

class CalculadorGeodesico:
    def __init__(self):
        self.radio_tierra_km: float = 6371

    


    def calcular_haversine(self, origen: tuple[float, float], destino: tuple[float, float]) -> float:
        
        

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
        return self.radioTierraKm * c


    def calcular_tiempo_vuelo_min(self, distancia_km: float, velocidad_km_h: float) -> float:
        return (distancia_km / velocidad_km_h) * 60

    
