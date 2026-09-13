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
        
class TelemetriaNoAsignadaError(DronError):
    """Excepción cuando se intenta calcular la distancia a un destino sin telemetría asignada."""
    def __init__(self, id_dron: str) -> None:
        message = "No se puede calcular la distancia: el dron no tiene telemetría asignada."
        super().__init__(id_dron, message)
        
class DestinoInvalidoError(DronError):
    """Excepción cuando se intenta calcular la distancia a un destino inválido."""
    def __init__(self, id_dron: str, destino) -> None:
        message = f"El destino proporcionado '{destino}' no es válido. Debe ser una tupla con latitud y longitud."
        super().__init__(id_dron, message)
        self.destino = destino
        
class CategoriaDronInvalidoError(DronError):
    """Excepción cuando el modelo o categoría no pertenece a la flota permitida."""
    def __init__(self, id_dron: str, categoria: str, categorias_permitidas: tuple) -> None:
        message = f"La categoría '{categoria}' no es válida. Opciones permitidas: {categorias_permitidas}."
        super().__init__(id_dron, message)
        self.categoria = categoria
        self.categorias_permitidas = categorias_permitidas


