# Excepciones de dominio para validaciones de reglas de negocio aeronáuticas
# Responsable: Alejandro García Jiménez

class BateriaInvalidaError(Exception):
    pass


class AltitudInvalidaError(Exception):
    pass


class EstadoMotorInvalidoError(Exception):
    pass


class CoordenadaInvalidaError(Exception):
    pass
