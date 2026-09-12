# Módulo de telemetría y validación física de aeronaves
# Responsable: Alejandro García Jiménez

from src.excepciones.errores import (
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
    CoordenadaInvalidaError,
)


class TelemetriaDrone:
    def __init__(self, id_dron, bateria, altitud, estado_motores, coordenadas):
        pass

    def validar_datos(self):
        pass

    def actualizar_trama(self, bateria, altitud, estado_motores, coordenadas):
        pass
