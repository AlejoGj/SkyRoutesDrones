# Excepciones de dominio para validaciones de reglas de negocio aeronáuticas
# Responsable: Alejandro García Jiménez

class BateriaInvalidaError(Exception):
    """Excepción cuando el nivel de batería viola el rango permitido [0.0, 100.0]%."""
    def __init__(self, bateria_invalida: float, message: str = None) -> None:
        if message is None:
            message = f"Nivel de batería '{bateria_invalida}%' inválido. Debe estar estrictamente en el rango [0.0, 100.0]%."
        super().__init__(message)
        self.bateria_invalida = bateria_invalida


class AltitudInvalidaError(Exception):
    """Excepción cuando la altitud de vuelo sobrepasa el techo aeronáutico o es negativa."""
    def __init__(self, altitud_invalida: float, message: str = None) -> None:
        if message is None:
            message = f"Altitud '{altitud_invalida} m' inválida. Debe estar delimitada en el rango [0.0, 120.0] m."
        super().__init__(message)
        self.altitud_invalida = altitud_invalida


class EstadoMotorInvalidoError(Exception):
    """Excepción cuando el estado de los motores no pertenece al catálogo o viola la coherencia de vuelo."""
    def __init__(self, estado_motor_invalido: str, message: str = None) -> None:
        if message is None:
            message = (
                f"Estado de motor '{estado_motor_invalido}' inválido o incoherente con la altitud. "
                "Opciones permitidas: ('APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA')."
            )
        super().__init__(message)
        self.estado_motor_invalido = estado_motor_invalido


class CoordenadaInvalidaError(Exception):
    """Excepción cuando las coordenadas geográficas son de formato incorrecto o salen de los límites geodésicos."""
    def __init__(self, coordenada_invalida, message: str = None) -> None:
        if message is None:
            message = (
                f"Coordenadas '{coordenada_invalida}' inválidas. Deben ser una tupla (latitud, longitud) "
                "con latitud en [-90.0, 90.0] y longitud en [-180.0, 180.0]."
            )
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


