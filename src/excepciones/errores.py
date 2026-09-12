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



""" Las Siguientes excepciones son necesarias para poder realizar HU-03, implementó Juan Manuel Pava Higuita (HU-03) """
class DronError(Exception):
    """ Excepcion base para errores relacionados con drones. """
    def __init__(self, id_dron: str, message: str) -> None:
        super().__init__(f"[Dron {id_dron}]: {message}")
        self.id_dron = id_dron
        self.message = message


class ActualizarEstadoDronError(DronError):
    """ Excepción para errores al actualizar el estado de un dron. """
    def __init__(self, id_dron: str, parametro: str) -> None:
        message = f"{parametro} no es un valor válido para actualizar el estado del dron."
        super().__init__(id_dron, message)
        self.parametro = parametro

class EstadoDronDuplicadoError(DronError):
    """Excepción cuando se intenta cambiar el dron a un estado en el que ya está."""
    def __init__(self, id_dron: str, estado_actual: bool) -> None:
        estado_str = "Disponible" if estado_actual else "No Disponible"
        message = f"El dron ya se encuentra en el estado: {estado_str}."
        super().__init__(id_dron, message)
        self.estado_actual = estado_actual

class AsignarTelemetriaError(DronError):
    """Excepción cuando se intenta asignar un objeto que no es telemetría válida."""
    def __init__(self, id_dron: str, objeto_invalido) -> None: #Objeto invalido es el objeto que no es del tipo TelemetriaDrone, por lo tanto puede ser Any, str, int, float, etc.
        tipo_recibido = type(objeto_invalido).__name__ 
        # type(objeto_invalido).__name__ devuelve el nombre del tipo de objeto recibido. Si se recibe un str, devuelve 'str', si se recibe un int, devuelve 'int', etc.
        message = f"Se espera una instancia de TelemetriaDrone, sin embargo se recibió un objeto de tipo '{tipo_recibido}'."
        super().__init__(id_dron, message)
        self.objeto_invalido = objeto_invalido


