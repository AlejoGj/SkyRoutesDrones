# Módulo de la entidad Dron y gestión de estados de vuelo
# Responsable: Juan Manuel Pava Higuita

from src.geodesia.calculador import CalculadorGeodesico
from src.telemetria.telemetria import TelemetriaDrone

# Las siguientes importaciones de excepciones son necesarias para poder realizar HU-03
from src.excepciones.errores import (
    ActualizarEstadoDronError,
    EstadoDronDuplicadoError,
)

class Dron:
    def __init__(self, id_dron: str, modelo_aeronave: str, categoria: str, velocidad_promedio_kmh: float, kilometraje_total_km: float, disponible: bool = True)-> None:
        self.id_dron = id_dron
        self.modelo_aeronave = modelo_aeronave
        self.categoria = categoria
        self.velocidad_promedio_kmh = velocidad_promedio_kmh
        self.kilometraje_total_km = kilometraje_total_km
        self.disponible = disponible
        self.telemetria = None  # Inicialmente no hay telemetría asignada
    
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
        
        
    def asignar_telemetria(self, nueva_telemetria):
        pass

    def calcular_distancia_a_destino(self, destino):
        pass

    def estimar_tiempo_llegada_min(self, destino):
        pass

    def iniciar_retorno_base(self, coordenadas_base):
        pass

    def aterrizar_en_base(self):
        pass

    