# Módulo de la entidad Dron y gestión de estados de vuelo
# Responsable: Juan Manuel Pava Higuita

from src.geodesia.calculador import CalculadorGeodesico
from src.telemetria.telemetria import TelemetriaDrone


class Dron:
    def __init__(self, id_dron, modelo_aeronave, categoria, velocidad_promedio_kmh, telemetria=None):
        pass

    def asignar_telemetria(self, nueva_telemetria):
        pass

    def calcular_distancia_a_destino(self, destino):
        pass

    def estimar_tiempo_llegada_min(self, destino):
        pass

    def iniciar_retorno_base(self, coordenadas_base):
        pass

    def aterrizar_en_base(self):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass
