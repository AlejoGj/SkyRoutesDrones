# Excepciones de dominio para validaciones de reglas de negocio aeronáuticas
# Responsable: Alejandro García Jiménez

class BateriaInvalidaError(Exception):
    def __init__(self, bateria_invalida: int, message: str = "Batería inválida.") -> None:
        super().__init__(message)
        self.bateria_invalida = bateria_invalida


class AltitudInvalidaError(Exception):
    def __init__(self, altitud_invalida: float, message: str = "Altitud inválida.") -> None:
        super().__init__(message)
        self.altitud_invalida = altitud_invalida


class EstadoMotorInvalidoError(Exception):
    def __init__(self, estado_motor_invalido: str, message: str = "Estado del motor inválido.") -> None:    
        super().__init__(message)
        self.estado_motor_invalido = estado_motor_invalido


class CoordenadaInvalidaError(Exception):
    def __init__(self, coordenada_invalida: tuple, message: str = "Coordenada inválida.") -> None:
        super().__init__(message)
        self.coordenada_invalida = coordenada_invalida
