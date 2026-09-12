# Módulo de la entidad Dron y gestión de estados de vuelo
# Responsable: Juan Manuel Pava Higuita

from src.geodesia.calculador import CalculadorGeodesico
from src.telemetria.telemetria import TelemetriaDrone

# Las siguientes importaciones de excepciones son necesarias para poder realizar HU-03
from src.excepciones.errores import (
    ActualizarEstadoDronError,
    AsignarTelemetriaError,
    CategoriaDronInvalidoError,
    DestinoInvalidoError,
    EstadoDronDuplicadoError,
    TelemetriaNoAsignadaError,
)

class Dron:
    # Constante de clase compartida por todas las instancias (no gasta memoria por objeto)
    CATEGORIAS_VALIDAS = ("ENTREGA_LIGERA", "CARGA_PESADA", "VIGILANCIA", "MAPEO_TOPOGRAFICO", "INSPECCION_INFRAESTRUCTURA", "BUSQUEDA_RESCATE")
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
    def __init__(self, id_dron: str, modelo_aeronave: str, categoria: str, velocidad_promedio_kmh: float = 60.0, kilometraje_total_km: float = 0.0, disponible: bool = True)-> None:
        self.id_dron = id_dron 
        self.modelo_aeronave = modelo_aeronave
        self.categoria = categoria # Se inicializa la categoría del dron. La categoría debe ser una de las categorías válidas definidas en la constante CATEGORIAS_VALIDAS. Este atributo se desechará en el SPRINT 2, ya que esta será la clase base de la que heredarán las subclases de drones, y cada subclase representará un modelo de aeronave específico, por lo que no será necesario almacenar la categoría en el objeto Dron.
        self.velocidad_promedio_kmh = velocidad_promedio_kmh # Se inicializa la velocidad promedio del dron, si no se pasa un valor, se inicializa en 60.0 km/h
        self.kilometraje_total_km = kilometraje_total_km # Se inicializa el kilomertraje, si no se pasa un valor, se inicializa en 0.0
        self.disponible = disponible # Se inicializa el estado de disponibilidad del dron, si no se pasa un valor, se inicializa en True
        
        """ Banderas Operacionales Para UH-03 y UH-04 """
        self.en_mision = False
        self.retornando_a_base = False
        
        """ Colaboradores de la Entidad Dron """
        self.telemetria = None  # Inicialmente no hay telemetría asignada
        self.calculador = CalculadorGeodesico()  # Se crea una instancia de CalculadorGeodesico para poder calcular distancias y tiempos de vuelo
        
        self.__post_init__() # Al no ser una @dataclass se llama manualmente al método __post_init__ para realizar validaciones adicionales después de la inicialización del objeto.
    
    def __post_init__(self):
        # A. Si no es texto -> TypeError
        if not isinstance(self.id_dron, str):
            raise TypeError(f"El id_dron debe ser un texto (str). Recibido: {type(self.id_dron).__name__}")

        # Si es texto pero son puros espacios "" o "   " -> ValueError
        if not self.id_dron.strip():
            raise ValueError("El id_dron no puede ser una cadena vacía ni contener solo espacios.")

        # Si es texto y tiene contenido, se limpia de espacios en blanco
        self.id_dron = self.id_dron.strip()
        
        # Si no es texto -> TypeError
        if not isinstance(self.modelo_aeronave, str):
            raise TypeError(f"El modelo_aeronave debe ser texto (str). Recibido: {type(self.modelo_aeronave).__name__}")

        # Si está vacío -> ValueError
        if not self.modelo_aeronave.strip():
            raise ValueError("El modelo_aeronave no puede estar vacío (ejemplo válido: 'DR-76K', 'Matrice 300').")
        # Si es texto y tiene contenido, se limpia de espacios en blanco
        self.modelo_aeronave = self.modelo_aeronave.strip()
        
        # Si no es texto -> TypeError
        if not isinstance(self.categoria, str):
            raise TypeError(f"La categoría debe ser un texto (str). Recibido: {type(self.categoria).__name__}")

        # Si es texto, pero NO pertenece al catálogo de SkyRoute -> Excepción de Dominio Propia
        categoria_limpia = self.categoria.strip().upper()
        if categoria_limpia not in self.CATEGORIAS_VALIDAS:
            raise CategoriaDronInvalidoError(self.id_dron, self.categoria, self.CATEGORIAS_VALIDAS)
        # Si es texto y pertenece al catálogo de SkyRoute, se limpia de espacios en blanco y se asigna a self.categoria
        self.categoria = categoria_limpia
        
        # En Python bool es subclase de int (True == 1). Si pasan True, lo rechazamos -> TypeError
        if isinstance(self.velocidad_promedio_kmh, bool) or not isinstance(self.velocidad_promedio_kmh, (int, float)):
            raise TypeError(f"La velocidad debe ser numérica. Recibido: {type(self.velocidad_promedio_kmh).__name__}")
        
        # Si es 0 o negativa -> ValueError (evita división por cero en ETA)
        if self.velocidad_promedio_kmh <= 0.0:
            raise ValueError(f"La velocidad promedio debe ser estrictamente mayor a 0 km/h. Recibido: {self.velocidad_promedio_kmh}")
        
        # Convertimos a float para asegurar consistencia en cálculos posteriores
        self.velocidad_promedio_kmh = float(self.velocidad_promedio_kmh)
        
        # Validación de tipo numérico -> TypeError
        if isinstance(self.kilometraje_total_km, bool) or not isinstance(self.kilometraje_total_km, (int, float)):
            raise TypeError(f"El kilometraje debe ser numérico. Recibido: {type(self.kilometraje_total_km).__name__}")

        # Validación de valor no negativo -> ValueError
        if self.kilometraje_total_km < 0.0:
            raise ValueError(f"El kilometraje acumulado no puede ser un número negativo. Recibido: {self.kilometraje_total_km}")

        # Convertimos a float para asegurar consistencia en cálculos posteriores
        self.kilometraje_total_km = float(self.kilometraje_total_km)
        
        # Si pasan un string como "si" o un número como 1 -> TypeError
        if not isinstance(self.disponible, bool):
            raise TypeError(f"La disponibilidad debe ser estrictamente booleana (True/False). Recibido: {type(self.disponible).__name__}")
        
        
    def __str__(self) -> str:
        # Determinamos el estado legible
        if self.retornando_a_base:
            estado_str = "RETORNANDO A BASE"
        elif self.en_mision:
            estado_str = "EN MISIÓN"
        elif self.disponible:
            estado_str = "DISPONIBLE"
        else:
            estado_str = "NO DISPONIBLE"
        # Leemos telemetría de forma segura colaborando con el objeto telemetria
        bateria = getattr(self.telemetria, 'bateria', None)
        bateria_str = f"{bateria:.1f}%" if bateria is not None else "Sin telemetría" # Type: ignore (en el momento que se desarrolle la clase TelemetriaDrone, se podrá eliminar el type: ignore)
        altitud = getattr(self.telemetria, 'altitud', None)
        altitud_str = f"{altitud:.1f} m" if altitud is not None else "N/A" # Type: ignore (en el momento que se desarrolle la clase TelemetriaDrone, se podrá eliminar el type: ignore)
        gps = getattr(self.telemetria, 'coordenadas', None)
        gps_str = f"{gps}" if gps is not None else "Sin señal GPS" # Type: ignore (en el momento que se desarrolle la clase TelemetriaDrone, se podrá eliminar el type: ignore)
        return (
            f"\n==================== FICHA DE DRON ====================\n"
            f"  ID: {self.id_dron} | Modelo: {self.modelo_aeronave} | Cat: {self.categoria}\n"
            f"  Estado Operacional : [{estado_str}]\n"
            f"  Batería Restante   : {bateria_str} | Altitud: {altitud_str}\n"
            f"  Ubicación GPS      : {gps_str}\n"
            f"  Velocidad Crucero  : {self.velocidad_promedio_kmh:.1f} km/h\n"
            f"  Odómetro Acumulado : {self.kilometraje_total_km:.2f} km\n"
            f"========================================================"
        )

    def __repr__(self) -> str:
        return (
            f"Dron(id_dron='{self.id_dron}', modelo='{self.modelo_aeronave}', "
            f"categoria='{self.categoria}', disponible={self.disponible}, "
            f"kilometraje_total_km={self.kilometraje_total_km})"
        ) 

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
        
        if self.telemetria is not None and hasattr(self.telemetria, 'coordenadas') and hasattr(nueva_telemetria, 'coordenadas'):
            # Calcular la distancia recorrida entre la telemetría actual y la nueva telemetría
            distancia_recorrida = self.calculador.calcular_haversine(self.telemetria.coordenadas, nueva_telemetria.coordenadas) #type: ignore  
            if distancia_recorrida is not None:
                self.kilometraje_total_km += distancia_recorrida # type: ignore (en el momento que se desarrolle la clase CalculadorGeodesico, se podrá eliminar el type: ignore)
        
        # Actualizar la telemetría del dron con la nueva telemetría proporcionada
        self.telemetria = nueva_telemetria

    def calcular_distancia_a_destino(self, destino: tuple) -> float: #type: ignore
        # Calcula la distancia entre el dron y un destino.
        if self.telemetria is None:
            # Si no hay telemetría asignada, lanza una excepción
            raise TelemetriaNoAsignadaError(self.id_dron)
        
        if not isinstance(destino, tuple) or len(destino) != 2:
            raise DestinoInvalidoError(self.id_dron, destino)
        
        return self.calculador.calcular_haversine(self.telemetria.coordenadas, destino) #type: ignore (en el momento que se desarrolle la clase CalculadorGeodesico, se podrá eliminar el type: ignore)
        # Se utiliza el método calcular_haversine de la clase CalculadorGeodesico para obtener la distancia en kilómetros entre las coordenadas actuales del dron y el destino proporcionado.
        # Se asume que self.telemetria.coordenadas es una tupla de la forma (latitud, longitud) y que destino también es una tupla de la misma forma.
    
    def estimar_tiempo_llegada_min(self, destino: tuple) -> float:
        # Calculamos la distancia hasta el destino
        distancia_km = self.calcular_distancia_a_destino(destino)
        # Delegamos el cálculo del tiempo al calculador
        return self.calculador.calcular_tiempo_vuelo_min(distancia_km, self.velocidad_promedio_kmh) # type: ignore (en el momento que se desarrolle la clase CalculadorGeodesico, se podrá eliminar el type: ignore)

    def iniciar_retorno_base(self, coordenadas_base: tuple) -> None:
        if not isinstance(coordenadas_base, tuple) or len(coordenadas_base) != 2:
            raise DestinoInvalidoError(self.id_dron, coordenadas_base)
            
        self.retornando_a_base = True
        self.en_mision = False
        self.disponible = False

    def finalizar_retorno_en_base(self) -> None:
        self.retornando_a_base = False
        self.en_mision = False
        self.disponible = True

    