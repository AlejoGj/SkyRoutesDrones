# Módulo de telemetría y validación física de aeronaves
# Responsable: Alejandro García Jiménez

from src.excepciones.errores import (
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
    CoordenadaInvalidaError,
)


class TelemetriaDrone:
    def __init__(self, id_dron: str, bateria: float, altitud: float, estado_motores: str, coordenadas: tuple[float, float]):
        self.id_dron = id_dron
        self.bateria = bateria
        self.altitud = altitud
        self.estado_motores = estado_motores.upper().strip()
        self.coordenadas = coordenadas
        if self.validar_datos():
            self.latitud, self.longitud = self.coordenadas


    def validar_datos(self, id_dron: str = None, bateria: float = None, altitud: float = None, estado_motores: str = None, coordenadas: tuple[float, float] = None) -> bool | None:
        
        if id_dron is None:
            id_dron = self.id_dron

        if bateria is None:
            bateria = self.bateria

        if altitud is None:
            altitud = self.altitud

        if estado_motores is None:
            estado_motores = self.estado_motores

        if coordenadas is None:
            coordenadas = self.coordenadas

        
        if not isinstance(id_dron, str) or not id_dron.strip():
            raise ValueError("El ID del dron debe ser una cadena de texto no vacía.")

        if not isinstance(bateria, (float, int)):
            raise ValueError("La batería debe ser un número.")

        if not (0 <= bateria <= 100):
            raise BateriaInvalidaError(bateria)

        if not isinstance(altitud, (float, int)):
            raise ValueError("La altitud debe ser un número.")

        if not (0 <= altitud <= 120):
            raise AltitudInvalidaError(altitud)

        if not isinstance(estado_motores, str) or not estado_motores.strip():
            raise ValueError("El estado del motor debe ser una cadena de texto no vacía.")

        estado_motores = estado_motores.upper().strip()

        if estado_motores not in ("APAGADOS", "STANDBY", "EN_VUELO", "EMERGENCIA"):
            raise EstadoMotorInvalidoError(estado_motores)


        if not isinstance(coordenadas, tuple) or len(coordenadas) != 2:
            raise CoordenadaInvalidaError(coordenadas)


        if not isinstance(coordenadas[0], (float, int)) or not isinstance(coordenadas[1], (float, int)):
            raise CoordenadaInvalidaError(coordenadas)

        
        if not (-90 <= coordenadas[0] <= 90 and -180 <= coordenadas[1] <= 180):
            raise CoordenadaInvalidaError(coordenadas)

        
        if (altitud == 0 and estado_motores == "EN_VUELO") or (altitud > 0 and estado_motores != "EN_VUELO"):
            raise EstadoMotorInvalidoError(estado_motores)

        return True

        

    def actualizar_trama(self, bateria: float, altitud: float, estado_motores: str, coordenadas: tuple[float, float]) -> None:

        if self.validar_datos(bateria = bateria, altitud = altitud, estado_motores = estado_motores, coordenadas = coordenadas):
            self.bateria = bateria
            self.altitud = altitud
            self.estado_motores = estado_motores.upper().strip()
            self.coordenadas = coordenadas
            self.latitud, self.longitud = self.coordenadas

        
