# Módulo de la entidad Dron y gestión de estados de vuelo
# Responsable: Juan Manuel Pava Higuita

from src.geodesia.calculador import CalculadorGeodesico
from src.telemetria.telemetria import TelemetriaDrone

# Las siguientes importaciones de excepciones son necesarias para poder realizar HU-03
from src.excepciones.errores import (
    ActualizarEstadoDronError,
    AsignarTelemetriaError,
    DestinoInvalidoError,
    EstadoDronDuplicadoError,
    TelemetriaNoAsignadaError,
)

class Dron:
    # Constante de clase compartida por todas las instancias (no gasta memoria por objeto)
    CATEGORIAS_VALIDAS = ("ENTREGA_LIGERA", "CARGA_PESADA", "VIGILANCIA", "MAPEO", "INSPECCION", "RESCATE") 
    """
    Esta tupla en el SPRINT 1 se utiliza para validar que el modelo de aeronave del dron sea uno de los modelos permitidos.
    Cuando evolucionemos a SPRINT 2, se podrá eliminar esta constante, transladarse al centro_control y transformarse en un diccionario de modelos de aeronaves para validar el tipo de dron antes de crear la instancia de Dron. Esto permitirá que el dron pueda ser de cualquier modelo de aeronave, siempre y cuando esté registrado en el diccionario de modelos de aeronaves del centro_control.
    
    Ejemplo:
    
    FABRICA_DRONES = {
        "ENTREGA_LIGERA": DronEntregaLigera,
        "CARGA_PESADA": DronCargaPesada,
        "VIGILANCIA": DronVigilancia,
        "MAPEO": DronMapeo,
        "INSPECCION": DronInspeccion,
        "RESCATE": DronRescate
    }
    """
    
    def __init__(self, id_dron: str, modelo_aeronave: str, velocidad_promedio_kmh: float = 60.0, kilometraje_total_km: float = 0.0, disponible: bool = True)-> None:
        self.id_dron = id_dron 
        self.modelo_aeronave = modelo_aeronave
        self.velocidad_promedio_kmh = velocidad_promedio_kmh # Se inicializa la velocidad promedio del dron, si no se pasa un valor, se inicializa en 60.0 km/h
        self.kilometraje_total_km = kilometraje_total_km # Se inicializa el kilomertraje, si no se pasa un valor, se inicializa en 0.0
        self.disponible = disponible # Se inicializa el estado de disponibilidad del dron, si no se pasa un valor, se inicializa en True
        self.telemetria = None  # Inicialmente no hay telemetría asignada
    
    def __post_init__(self):
        pass 
        
        
        
    def __str__(self):
        pass
    
    def __repr__(self):
        pass

    def actualizar_estado_disponibilidad(self, disponible: bool) -> None:
        # Agrego Funcionalidad. HU-03, UML, Responsabilidades no coinciden. Se agrega el atributo disponible (como se dice en el UML) para poder actualizar el estado de disponibilidad del dron.
        if not isinstance(disponible, bool):
            # Lanzo una excepción si el valor proporcionado no es un booleano
            raise ActualizarEstadoDronError(self.id_dron, str(disponible))
        
        if disponible == self.disponible:
            # Lanzo una excepción si el dron ya está en el estado deseado
            raise EstadoDronDuplicadoError(self.id_dron, self.disponible)
        
        # Si pasa las validaciones, actualizo el estado de disponibilidad del dron
        self.disponible = disponible
        
        
    def asignar_telemetria(self, nueva_telemetria) -> None:
        # Validar que el objeto recibido sea estrictamente del tipo TelemetriaDrone
        if not isinstance(nueva_telemetria, TelemetriaDrone):
            raise AsignarTelemetriaError(self.id_dron, nueva_telemetria)
            
        # Si es válido, se asigna con éxito
        self.telemetria = nueva_telemetria

    def calcular_distancia_a_destino(self, destino: tuple) -> float: #type: ignore
        # Calcula la distancia entre el dron y un destino.
        if self.telemetria is None:
            # Si no hay telemetría asignada, lanza una excepción
            raise TelemetriaNoAsignadaError(self.id_dron)
        
        if not isinstance(destino, tuple) or len(destino) != 2:
            raise DestinoInvalidoError(self.id_dron, destino)
        
        return CalculadorGeodesico().calcular_haversine(self.telemetria.coordenadas, destino) #type: ignore (en el momento que se desarrolle la clase CalculadorGeodesico, se podrá eliminar el type: ignore)
        # Se utiliza el método calcular_haversine de la clase CalculadorGeodesico para obtener la distancia en kilómetros entre las coordenadas actuales del dron y el destino proporcionado.
        # Se asume que self.telemetria.coordenadas es una tupla de la forma (latitud, longitud) y que destino también es una tupla de la misma forma.
    
    def estimar_tiempo_llegada_min(self, destino):
        pass

    def iniciar_retorno_base(self, coordenadas_base):
        pass

    def aterrizar_en_base(self):
        pass

    