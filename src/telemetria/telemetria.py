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
        self.estado_motores = estado_motores.upper()
        self.coordenadas = coordenadas
        self.validar_datos()
        self.latitud, self.longitud = self.coordenadas


    def validar_datos(self) -> None:
        if not isinstance(self.id_dron, str) or not self.id_dron.strip():
            raise ValueError("El ID del dron debe ser una cadena de texto no vacía.")

        if not isinstance(self.bateria, (float, int)):
            raise ValueError("La batería debe ser un número.")

        if not (0 <= self.bateria <= 100):
            raise BateriaInvalidaError(self.bateria)

        if not isinstance(self.altitud, (float, int)):
            raise ValueError("La altitud debe ser un número.")

        if not (0 <= self.altitud <= 120):
            raise AltitudInvalidaError(self.altitud)

        if not isinstance(self.estado_motores, str) or not self.estado_motores.strip():
            raise ValueError("El estado del motor debe ser una cadena de texto no vacía.")

        if self.estado_motores not in ("APAGADOS", "STANDBY", "EN_VUELO", "EMERGENCIA"):
            raise EstadoMotorInvalidoError(self.estado_motores)


        if not isinstance(self.coordenadas, tuple) or len(self.coordenadas) != 2:
            raise CoordenadaInvalidaError(self.coordenadas)


        if not isinstance(self.coordenadas[0], (float, int)) or not isinstance(self.coordenadas[1], (float, int)):
            raise CoordenadaInvalidaError(self.coordenadas)

        
        if not (-90 <= self.coordenadas[0] <= 90 and -180 <= self.coordenadas[1] <= 180):
            raise CoordenadaInvalidaError(self.coordenadas)

        

        if (self.altitud == 0 and self.estado_motores.upper() == "EN_VUELO") or (self.altitud > 0 and self.estado_motores.upper() != "EN_VUELO"):
            raise EstadoMotorInvalidoError(self.estado_motores)

        

    def actualizar_trama(self, bateria: float, altitud: float, estado_motores: str, coordenadas: tuple[float, float]) -> None:
        pass    
        
