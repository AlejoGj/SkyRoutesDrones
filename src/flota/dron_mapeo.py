# Módulo de especialización para Dron de Mapeo Topográfico y Cartografía Aérea
# Historia de Usuario: HU-08 (Juan Manuel Pava Higuita)
# Sprint 2: Herencia, Polimorfismo y Abstracción Formal

# ==============================================================================
# 1. IMPORTACIONES Y CONTROL DE TIPADO DIFERIDO (PEP 563 & PEP 484)
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
from src.flota.dron import Dron
from src.excepciones.errores import ActualizarEstadoDronError

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


# ==============================================================================
# 2. DEFINICIÓN DE CLASE Y APLICACIÓN DE PILARES DE POO
# ==============================================================================
# PILAR: HERENCIA
# 'DronMapeo' hereda de la clase abstracta 'Dron', reutilizando el cálculo geodésico,
# la telemetría periódica, el odómetro de vuelo y los protocolos de base.
class DronMapeo(Dron):
    """
    Subclase especializada en levantamiento tridimensional, fotogrametría aérea y
    cartografía urbana de laderas, cuencas y vertipuertos en el Valle de Aburrá.
    
    Características Principales:
    - Escáner láser LiDAR aerotransportado para generación de nubes de puntos 3D de alta densidad.
    - Georreferenciación centimétrica de alta precisión mediante GPS diferencial RTK (± cm).
    - Unidad de almacenamiento de estado sólido (SSD) en Terabytes (TB) para captura de datos masivos.
    - Tasa de consumo energético especializada (1.4% de batería por kilómetro) considerando el consumo de sensores activos.
    """

    CATEGORIA_ESPECIALIZADA: str = "MAPEO_TOPOGRAFICO"
    LIDAR_DEFAULT: bool = True
    PRECISION_GPS_DEFAULT_CM: float = 2.5
    ALMACENAMIENTO_DEFAULT_TB: float = 2.0

    def __init__(
        self,
        id_dron: str = None,
        modelo_aeronave: str = None,
        tiene_sensor_lidar: bool = LIDAR_DEFAULT,
        precision_gps_cm: float = PRECISION_GPS_DEFAULT_CM,
        capacidad_almacenamiento_tb: float = ALMACENAMIENTO_DEFAULT_TB,
        velocidad_promedio_kmh: float = 45.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        **kwargs,
    ) -> None:
        """
        Inicializa un dron de mapeo topográfico y cartografía aérea.
        
        Permite orden posicional estándar (id, modelo, lidar, precision, almacenamiento)
        o invertido para máxima tolerancia y compatibilidad con scripts del equipo.
        """
        # Tolerancia a orden posicional alternativo (lidar, precision, almacenamiento, id, modelo)
        if isinstance(id_dron, bool) and isinstance(precision_gps_cm, str):
            actual_lidar = id_dron
            actual_precision = modelo_aeronave
            actual_almacenamiento = tiene_sensor_lidar
            actual_id = precision_gps_cm
            actual_modelo = capacidad_almacenamiento_tb
            id_dron = actual_id
            modelo_aeronave = actual_modelo
            tiene_sensor_lidar = actual_lidar
            precision_gps_cm = actual_precision
            capacidad_almacenamiento_tb = actual_almacenamiento

        # Invocación al constructor padre (Herencia)
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        # Categoría especializada oficial fija (RF-07, HU-08)
        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # PILAR: ENCAPSULAMIENTO PROTEGIDO
        # Atributos protegidos con guión simple (_) accesibles en la jerarquía,
        # asignados mediante setters para garantizar integridad de dominio.
        self.tiene_sensor_lidar = tiene_sensor_lidar
        self.precision_gps_cm = precision_gps_cm
        self.capacidad_almacenamiento_tb = capacidad_almacenamiento_tb

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def tiene_sensor_lidar(self) -> bool:
        """Indica si el sensor LiDAR de pulsos láser está activo y equipado."""
        return self._tiene_sensor_lidar

    @tiene_sensor_lidar.setter
    def tiene_sensor_lidar(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El indicador de sensor LiDAR debe ser booleano (True/False). Recibido: {type(valor).__name__}")
        self._tiene_sensor_lidar = valor

    @property
    def precision_gps_cm(self) -> float:
        """Retorna la precisión de georreferenciación centimétrica RTK (cm)."""
        return self._precision_gps_cm

    @precision_gps_cm.setter
    def precision_gps_cm(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La precisión GPS debe ser numérica. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La precisión GPS debe ser estrictamente mayor a 0 cm. Recibido: {valor}")
        self._precision_gps_cm = float(valor)

    @property
    def capacidad_almacenamiento_tb(self) -> float:
        """Retorna la capacidad del disco SSD aerotransportado en Terabytes (TB)."""
        return self._capacidad_almacenamiento_tb

    @capacidad_almacenamiento_tb.setter
    def capacidad_almacenamiento_tb(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La capacidad de almacenamiento debe ser numérica. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La capacidad de almacenamiento debe ser mayor a 0 TB. Recibido: {valor}")
        self._capacidad_almacenamiento_tb = float(valor)

    # ==========================================================================
    # 4. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO OBLIGATORIO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Sobrescribe 'ejecutar_mision' para ejecutar el protocolo de mapeo y escaneo láser 3D.
        
        FLUJO DE EJECUCIÓN:
        1. Lógica base: Valida batería, disponibilidad, altitud de despegue y pasa pedido a 'EN_TRANSITO'.
        2. Simulación cartográfica: Escaneo de nube de puntos 3D y georreferenciación centimétrica.
        3. Enriquecimiento del reporte: Agrega metadatos topográficos al informe de misión.
        """
        reporte_despegue = super().ejecutar_mision(pedido)

        print(f"[{self.id_dron}] Iniciando misión de levantamiento topográfico y cartografía aérea...")
        if self._tiene_sensor_lidar:
            print("  -> Sensor LiDAR activo escaneando nube de puntos 3D de alta densidad.")
        else:
            print("  -> Sensor LiDAR inactivo. Operando mediante fotogrametría estándar.")
        print(f"  -> Georreferenciación centimétrica RTK fijada a ±{self._precision_gps_cm:.1f} cm de precisión.")
        print(f"  -> Almacenando capturas georreferenciadas en disco SSD de {self._capacidad_almacenamiento_tb:.1f} TB.")

        reporte_despegue.update({
            "instrumental_activado": "SENSOR_LIDAR_Y_GPS_RTK" if self._tiene_sensor_lidar else "FOTOGRAMETRIA_ESTANDAR",
            "precision_levantamiento_cm": self._precision_gps_cm,
            "espacio_almacenamiento_tb": self._capacidad_almacenamiento_tb,
            "nube_puntos_generada": "NUBE_3D_LASER_DENSIDAD_ALTA",
            "estado_especifico": "Levantamiento topográfico 3D completado con éxito",
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-08 / HU-10)
        
        Aplica una tasa especializada del 1.4% de batería por kilómetro:
            Consumo (%) = distancia_km * 1.4
        
        El sensor LiDAR y el procesamiento de nubes de puntos consumen energía continua adicional.
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 1.4)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-08)
        
        Reporta el estado del sensor LiDAR, precisión GPS centimétrica y disco de memoria.
        """
        lidar_estado = "CALIBRADO_Y_ACTIVO" if self._tiene_sensor_lidar else "NO_EQUIPADO"
        return (
            f"Diagnóstico Topográfico -> Sensor LiDAR: [{lidar_estado}] | "
            f"Precisión GPS: ±{self._precision_gps_cm:.1f}cm RTK | Almacenamiento: {self._capacidad_almacenamiento_tb:.1f}TB SSD [OPERATIVOS]"
        )

    # ==========================================================================
    # 5. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base vía 'super().__str__()'
        e integrando las especificaciones cartográficas y de precisión RTK.
        """
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        lidar_str = "Sí" if self._tiene_sensor_lidar else "No"
        return (
            f"{ficha_sin_cierre}\n"
            f"  Instrumental LiDAR : [{lidar_str}] | Precisión GPS: ±{self._precision_gps_cm:.1f} cm (RTK)\n"
            f"  Almacenamiento     : {self._capacidad_almacenamiento_tb:.1f} TB SSD | Eficiencia: 1.4% bat/km\n"
            f"{cierre}"
        )

    def __repr__(self) -> str:
        """
        Sobrescribe __repr__ para extender la representación oficial con los aditamentos cartográficos.
        """
        return (
            f"DronMapeo(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"tiene_sensor_lidar={self._tiene_sensor_lidar}, precision_gps_cm={self._precision_gps_cm}, "
            f"capacidad_almacenamiento_tb={self._capacidad_almacenamiento_tb}, disponible={self.disponible})"
        )
