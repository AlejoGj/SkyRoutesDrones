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

        

    def actualizar_trama(
        self,
        bateria: float = None,
        altitud: float = None,
        estado_motores: str = None,
        coordenadas: tuple[float, float] = None
    ) -> None:
        
        # Si un dato no se envía, conserva el que ya tiene la aeronave:
        nueva_bateria = bateria if bateria is not None else self.bateria
        nueva_altitud = altitud if altitud is not None else self.altitud
        nuevo_estado_motor = estado_motores if estado_motores is not None else self.estado_motores
        nuevas_coords = coordenadas if coordenadas is not None else self.coordenadas
        

        if self.validar_datos(bateria = nueva_bateria, altitud = nueva_altitud, estado_motores = nuevo_estado_motor, coordenadas = nuevas_coords):
            self.bateria = nueva_bateria
            self.altitud = nueva_altitud
            self.estado_motores = nuevo_estado_motor.upper().strip()
            self.coordenadas = nuevas_coords
            self.latitud, self.longitud = self.coordenadas

    def __str__(self) -> str:
        return (
            f"[Telemetría {self.id_dron}] Batería: {self.bateria:.1f}% | "
            f"Altitud: {self.altitud:.1f} m | Motores: {self.estado_motores} | "
            f"GPS: {self.coordenadas}"
        )

    def __repr__(self) -> str:
        return (
            f"TelemetriaDrone(id_dron='{self.id_dron}', bateria={self.bateria}, "
            f"altitud={self.altitud}, estado_motores='{self.estado_motores}', "
            f"coordenadas={self.coordenadas})"
        )

        
