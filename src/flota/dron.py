# Módulo de la entidad Dron y gestión de estados de vuelo
# Responsable: Juan Manuel Pava Higuita (Sprint 1) / Alejandro García Jiménez (Sprint 2 - HU-07)

# 1. from __future__ import annotations (PEP 563):
# Hace que las anotaciones de tipo (Type Hints) se interpreten como cadenas de texto diferidas
# en tiempo de ejecución. Permite referenciar clases en firmas de métodos sin forzar su carga inmediata en memoria.
from __future__ import annotations

# 2. from typing import TYPE_CHECKING:
# 'TYPE_CHECKING' es una bandera de Python:
# - En ejecución real del programa vale False (evita ejecutar imports dentro del 'if').
# - Para el editor / IDE (autocompletado y tipado estático) vale True.
# SOLUCIÓN A IMPORTACIÓN CIRCULAR: 'pedido.py' importa a 'Dron', y 'dron.py' necesita a 'Pedido'.
# Gracias a este patrón, el ciclo se rompe completamente y el programa corre sin errores.
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from src.geodesia.calculador import CalculadorGeodesico, ICalculadorGeodesico
from src.telemetria.telemetria import TelemetriaDrone

if TYPE_CHECKING:
    # Esta importación solo existe para que el IDE reconozca el tipo en: 'ejecutar_mision(self, pedido: Pedido)'
    from src.pedidos.pedido import Pedido

# Las siguientes importaciones de excepciones son necesarias para poder realizar HU-03
from src.excepciones.errores import (
    ActualizarEstadoDronError,
    AsignarTelemetriaError,
    DestinoInvalidoError,
    EstadoDronDuplicadoError,
    TelemetriaNoAsignadaError,
)

class Dron(ABC):
    def __init__(
        self,
        id_dron: str,
        modelo_aeronave: str,
        velocidad_promedio_kmh: float = 60.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador: ICalculadorGeodesico | None = None,
    ) -> None:
        self.id_dron = id_dron 
        self.modelo_aeronave = modelo_aeronave
        self.velocidad_promedio_kmh = velocidad_promedio_kmh # Se inicializa la velocidad promedio del dron, si no se pasa un valor, se inicializa en 60.0 km/h
        self.kilometraje_total_km = kilometraje_total_km # Se inicializa el kilomertraje, si no se pasa un valor, se inicializa en 0.0
        self.disponible = disponible # Se inicializa el estado de disponibilidad del dron, si no se pasa un valor, se inicializa en True
        self.calculador = calculador if calculador is not None else CalculadorGeodesico()
        self._historial_telemetria: list[str] = [] # Bitácora interna privada (mutable solo por la clase)

        
        """ Banderas Operacionales Para UH-03 y UH-04 """
        self.en_mision = False
        self.retornando_a_base = False
        self.coordenadas_base = None
        self.pedido_activo: Pedido | None = None  # Referencia al Pedido actualmente en tránsito
        
        """ Colaboradores de la Entidad Dron """
        self.telemetria = None  # Inicialmente no hay telemetría asignada
        
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
        # Leemos telemetría colaborando directamente con el objeto TelemetriaDrone
        if self.telemetria is not None:
            bateria_str = f"{self.telemetria.bateria:.1f}%"
            altitud_str = f"{self.telemetria.altitud:.1f} m"
            gps_str = f"{self.telemetria.coordenadas}"
        else:
            bateria_str = "Sin telemetría"
            altitud_str = "N/A"
            gps_str = "Sin señal GPS"
        return (
            f"\n==================== FICHA DE DRON ====================\n"
            f"  ID: {self.id_dron} | Modelo: {self.modelo_aeronave} | Tipo: {self.__class__.__name__}\n"
            f"  Estado Operacional : [{estado_str}]\n"
            f"  Batería Restante   : {bateria_str} | Altitud: {altitud_str}\n"
            f"  Ubicación GPS      : {gps_str}\n"
            f"  Velocidad Crucero  : {self.velocidad_promedio_kmh:.1f} km/h\n"
            f"  Odómetro Acumulado : {self.kilometraje_total_km:.2f} km\n"
            f"========================================================"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"disponible={self.disponible})"
        )

    
    @abstractmethod
    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Lógica base de despegue y salida a misión para cualquier aeronave de la flota.
        
        CICLO DE VIDA CON SIMULACIÓN Y TELEMETRÍA (NO INSTANTÁNEO):
        -----------------------------------------------------------
        1. 'ejecutar_mision(pedido)':
           - Valida disponibilidad y autonomía de batería para cubrir la distancia estimada.
           - Eleva el dron a altitud de crucero (30 m) y enciende motores ('EN_VUELO').
           - NO teletransporta las coordenadas: el dron permanece en su punto de origen para iniciar el viaje.
           - Pasa el pedido a 'EN_TRANSITO' y activa la bandera 'self.en_mision = True'.
        
        2. Durante el vuelo (Reloj Delta / Telemetría periódica):
           - La posición del dron se va actualizando progresivamente hacia 'pedido.coordenada_destino'.
           - El pedido permanece 'EN_TRANSITO'.
        
        3. Al alcanzar las coordenadas de destino (distancia <= 50 metros):
           - Se invoca 'finalizar_mision_en_destino()' para ejecutar la labor especializada
             de la subclase (soltar carga, escanear LiDAR, transmitir video) y pasar el pedido a 'COMPLETADO'.

        GUÍA DE IMPLEMENTACIÓN PARA SUBCLASES HIJAS:
        -------------------------------------------
        def ejecutar_mision(self, pedido: Pedido) -> dict:
            # 1. Ejecutar despegue común, flags y validaciones (deja pedido en 'EN_TRANSITO'):
            reporte_despegue = super().ejecutar_mision(pedido)

            # 2. Configurar o activar instrumental especializado de la subclase antes de partir:
            reporte_despegue.update({
                "instrumental_activado": "CÁMARA_4K" # o TOLVA_REFRIGERADA, LIDAR, etc.
            })
            return reporte_despegue
        """
        if not self.disponible:
            raise ActualizarEstadoDronError(self.id_dron, "El dron no está disponible para despegar.")

        if self.telemetria is None:
            raise TelemetriaNoAsignadaError(self.id_dron)

        # 1. Validación de autonomía y consumo estimado antes de despegar
        distancia_estimada_km = self.calcular_distancia_a_destino(pedido.coordenada_destino)
        consumo_estimado = self.calcular_consumo_estimado(distancia_estimada_km)
        if self.telemetria.bateria < consumo_estimado:
            raise ActualizarEstadoDronError(
                self.id_dron,
                f"Batería insuficiente ({self.telemetria.bateria:.1f}%) para la misión. Se requiere mínimo {consumo_estimado:.1f}%."
            )

        # 2. Mutación de banderas operacionales (inicia vuelo activo)
        self.disponible = False
        self.en_mision = True
        self.retornando_a_base = False
        self.pedido_activo = pedido

        # 3. Transición a vuelo en telemetría (despegue sin teletransportación de coordenadas)
        self.actualizar_telemetria(
            altitud=30.0,
            estado_motores="EN_VUELO"
        )

        # 4. Actualización del pedido a estado activo
        pedido.actualizar_estado("EN_TRANSITO")

        return {
            "id_dron": self.id_dron,
            "id_pedido": pedido.id_pedido,
            "estado_mision": "DESPEGUE_EXITOSO",
            "distancia_objetivo_km": round(distancia_estimada_km, 2),
            "consumo_estimado": round(consumo_estimado, 2),
            "coordenadas_origen": self.telemetria.coordenadas,
            "coordenadas_destino": pedido.coordenada_destino
        }

    
    @abstractmethod
    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        ...


    @abstractmethod
    def inspeccionar_sistemas_especializados(self) -> str:
        ...


    def actualizar_estado_disponibilidad(self, disponible: bool) -> None:
        # Agrego Funcionalidad. HU-03, UML, Responsabilidades no coinciden. Se agrega el atributo disponible (como se dice en el UML) para poder actualizar el estado de disponibilidad del dron.
        if not isinstance(disponible, bool):
            # Lanzo una excepción si el valor proporcionado no es un booleano
            raise ActualizarEstadoDronError(self.id_dron, str(disponible))
        
        if disponible == self.disponible:
            # Lanzo una excepción si el dron ya está en el estado deseado
            raise EstadoDronDuplicadoError(self.id_dron, self.disponible)
        
        if disponible and (self.en_mision or self.retornando_a_base):
            motivo = "en misión activa" if self.en_mision else "retornando a base"
            raise ActualizarEstadoDronError(self.id_dron, f"No se puede marcar como disponible: la aeronave se encuentra {motivo}")
        
        # Si pasa las validaciones, actualizo el estado de disponibilidad del dron
        self.disponible = disponible
        
        
    def asignar_telemetria(self, nueva_telemetria: TelemetriaDrone) -> None:
        # Validar que el objeto recibido sea estrictamente del tipo TelemetriaDrone
        if not isinstance(nueva_telemetria, TelemetriaDrone):
            raise AsignarTelemetriaError(self.id_dron, nueva_telemetria)
        
        # Validar coherencia de identificador entre el dron y la telemetría
        if nueva_telemetria.id_dron != self.id_dron:
            raise AsignarTelemetriaError(self.id_dron, f"Incoherencia: la telemetría pertenece al dron '{nueva_telemetria.id_dron}', no a '{self.id_dron}'")
        
        # Si ya había una telemetría previa, calcular la distancia recorrida y acumular kilometraje
        if self.telemetria is not None:
            distancia_recorrida = self.calculador.calcular_haversine(self.telemetria.coordenadas, nueva_telemetria.coordenadas)
            if distancia_recorrida is not None:
                self.kilometraje_total_km += distancia_recorrida
        
        # Asignar la telemetría inicial al dron
        self.telemetria = nueva_telemetria

        # Registrar la captura técnica inicial en el log de telemetría (inmutable)
        self._historial_telemetria.append(repr(self.telemetria))

    def actualizar_telemetria(
        self,
        bateria_o_telemetria: float | TelemetriaDrone | None = None,
        altitud: float = None,
        estado_motores: str = None,
        coordenadas: tuple[float, float] = None
    ) -> None:
        """
        Actualiza los datos de telemetría del dron in-place reutilizando la instancia existente
        de TelemetriaDrone mediante su método actualizar_trama(...).
        
        Soporta recibir los parámetros individuales (bateria, altitud, estado_motores, coordenadas)
        o directamente una nueva instancia de TelemetriaDrone.
        """
        if self.telemetria is None:
            raise TelemetriaNoAsignadaError(self.id_dron)
        
        if isinstance(bateria_o_telemetria, TelemetriaDrone):
            if bateria_o_telemetria.id_dron != self.id_dron:
                raise AsignarTelemetriaError(self.id_dron, f"Incoherencia: la telemetría pertenece al dron '{bateria_o_telemetria.id_dron}', no a '{self.id_dron}'")
            nueva_bateria = bateria_o_telemetria.bateria
            altitud = bateria_o_telemetria.altitud
            estado_motores = bateria_o_telemetria.estado_motores
            nuevas_coordenadas = bateria_o_telemetria.coordenadas
        else:
            nueva_bateria = bateria_o_telemetria
            nuevas_coordenadas = coordenadas

        # Calcular kilometraje acumulado si hubo desplazamiento antes de mutar las coordenadas
        if nuevas_coordenadas is not None and self.telemetria.coordenadas != nuevas_coordenadas:
            distancia = self.calculador.calcular_haversine(self.telemetria.coordenadas, nuevas_coordenadas)
            if distancia is not None:
                self.kilometraje_total_km += distancia

        # Reutilizar el objeto de telemetría llamando a su método especializado actualizar_trama
        self.telemetria.actualizar_trama(
            bateria=nueva_bateria,
            altitud=altitud,
            estado_motores=estado_motores,
            coordenadas=nuevas_coordenadas
        )

        # Registrar la captura técnica inmutable en el historial
        self._historial_telemetria.append(repr(self.telemetria))

    @property
    def historial_telemetria(self) -> tuple[str, ...]:
        """
        Bitácora inmutable de capturas técnicas de telemetría del dron.
        Retorna una tupla congelada para impedir alteraciones, eliminaciones o vaciados externos.
        """
        return tuple(self._historial_telemetria)


    def calcular_distancia_a_destino(self, destino: tuple) -> float: #type: ignore
        # Calcula la distancia entre el dron y un destino.
        if self.telemetria is None:
            # Si no hay telemetría asignada, lanza una excepción
            raise TelemetriaNoAsignadaError(self.id_dron)
        
        if not isinstance(destino, tuple) or len(destino) != 2:
            raise DestinoInvalidoError(self.id_dron, destino)
        
        return self.calculador.calcular_haversine(self.telemetria.coordenadas, destino)
        # Se utiliza el método calcular_haversine de la clase CalculadorGeodesico para obtener la distancia en kilómetros entre las coordenadas actuales del dron y el destino proporcionado.
        # Se asume que self.telemetria.coordenadas es una tupla de la forma (latitud, longitud) y que destino también es una tupla de la misma forma.
    
    def estimar_tiempo_llegada_min(self, destino: tuple) -> float:
        # Calculamos la distancia hasta el destino
        distancia_km = self.calcular_distancia_a_destino(destino)
        # Delegamos el cálculo del tiempo al calculador
        return self.calculador.calcular_tiempo_vuelo_min(distancia_km, self.velocidad_promedio_kmh) # type: ignore (en el momento que se desarrolle la clase CalculadorGeodesico, se podrá eliminar el type: ignore)

    def iniciar_retorno_base(self, coordenadas_base: tuple = None) -> None:
        base = coordenadas_base if coordenadas_base is not None else self.coordenadas_base
        if base is None:
            base = (6.2089, -75.5684)  # Base predeterminada SkyRoute (Olaya Herrera)
        if not isinstance(base, tuple) or len(base) != 2:
            raise DestinoInvalidoError(self.id_dron, base)
            
        self.coordenadas_base = base  # Guardamos la base de destino
        self.retornando_a_base = True
        self.en_mision = False
        self.disponible = False

    def finalizar_retorno_en_base(self) -> None:
        # 1. Comprobar que realmente esté en proceso de retorno
        if not self.retornando_a_base:
            raise ActualizarEstadoDronError(self.id_dron, "Operación inválida: el dron no se encuentra en estado de retorno a base.")

        # 2. Comprobar posición actual respecto a la base (tolerancia máxima de aterrizaje: 0.05 km = 50 metros)
        if self.telemetria is not None and self.coordenadas_base is not None:
            distancia_a_base = self.calculador.calcular_haversine(self.telemetria.coordenadas, self.coordenadas_base)
            if distancia_a_base is not None and distancia_a_base > 0.05:
                raise ActualizarEstadoDronError(
                    self.id_dron, 
                    f"Aterrizaje denegado: el dron se encuentra a {distancia_a_base:.2f} km de la base."
                )

        # Confirmación de aterrizaje en base
        self.retornando_a_base = False
        self.en_mision = False
        self.disponible = True
        self.coordenadas_base = None

    def finalizar_mision_en_destino(self) -> dict:
        """
        Finaliza formalmente la misión cuando el dron alcanza las coordenadas de destino.
        Valida que el dron esté en misión y a menos de 50 metros del objetivo.
        Actualiza el pedido a 'COMPLETADO' y libera la bandera 'en_mision'.
        """
        if not self.en_mision or self.pedido_activo is None:
            raise ActualizarEstadoDronError(
                self.id_dron,
                "Operación inválida: el dron no se encuentra en ninguna misión activa."
            )

        # Comprobar proximidad al destino (tolerancia máxima de entrega: 0.05 km = 50 metros)
        if self.telemetria is not None:
            distancia_a_destino = self.calcular_distancia_a_destino(self.pedido_activo.coordenada_destino)
            if distancia_a_destino is not None and distancia_a_destino > 0.05:
                raise ActualizarEstadoDronError(
                    self.id_dron,
                    f"Misión no finalizada: el dron se encuentra a {distancia_a_destino:.2f} km del destino objetivo."
                )

        pedido_completado = self.pedido_activo
        pedido_completado.actualizar_estado("COMPLETADO")
        
        self.en_mision = False
        self.pedido_activo = None
        self.iniciar_retorno_base()

        return {
            "id_dron": self.id_dron,
            "id_pedido": pedido_completado.id_pedido,
            "estado_mision": "COMPLETADA_EN_DESTINO",
            "coordenadas_llegada": self.telemetria.coordenadas if self.telemetria else None
        }

