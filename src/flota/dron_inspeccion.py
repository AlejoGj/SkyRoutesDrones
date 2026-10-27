# Módulo de especialización para Dron de Inspección de Infraestructura
# Historia de Usuario: HU-11 (Valery Arboleda Ardila)
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
# 'DronInspeccion' hereda formalmente de la clase abstracta base 'Dron'.
class DronInspeccion(Dron):
    """
    Subclase especializada en el diagnóstico de vertipuertos, antenas de comunicación
    y plataformas elevadas en el Valle de Aburrá.
    
    Características Principales:
    - Cámara óptica de alta magnificación con zoom óptico (x).
    - Sensor ultrasónico de distancia para vuelo estacionario a distancia segura de colisión (metros).
    - Tasa de consumo energético especializada (1.5% de batería por kilómetro) por maniobras de precisión.
    """

    CATEGORIA_ESPECIALIZADA: str = "INSPECCION_INFRAESTRUCTURA"
    ZOOM_DEFAULT_X: int = 10
    ULTRASONICO_DEFAULT_M: float = 5.0

    def __init__(
        self,
        id_dron: str,
        modelo_aeronave: str,
        zoom_optico_x: int = ZOOM_DEFAULT_X,
        rango_sensor_ultrasonico_m: float = ULTRASONICO_DEFAULT_M,
        velocidad_promedio_kmh: float = 50.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None
    ) -> None:
        """
        Inicializa un dron de inspección técnica con atributos específicos validados.
        """
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        self.categoria = self.CATEGORIA_ESPECIALIZADA


        # Asignación a través de setters para validaciones defensivas de dominio
        self.zoom_optico_x = zoom_optico_x
        self.rango_sensor_ultrasonico_m = rango_sensor_ultrasonico_m

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def zoom_optico_x(self) -> int:
        """Retorna el factor de aumento óptico de la cámara (ej. 10x, 30x)."""
        return self._zoom_optico_x

    @zoom_optico_x.setter
    def zoom_optico_x(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"El zoom óptico debe ser un número entero. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"El factor de zoom óptico debe ser estrictamente mayor a 0x. Recibido: {valor}")
        self._zoom_optico_x = valor

    @property
    def rango_sensor_ultrasonico_m(self) -> float:
        """Retorna la distancia de seguridad del sensor ultrasónico de colisión en metros (m)."""
        return self._rango_sensor_ultrasonico_m

    @rango_sensor_ultrasonico_m.setter
    def rango_sensor_ultrasonico_m(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"El rango del sensor ultrasónico debe ser numérico. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"El rango del sensor ultrasónico debe ser estrictamente mayor a 0 metros. Recibido: {valor}")
        self._rango_sensor_ultrasonico_m = float(valor)

    # ==========================================================================
    # 4. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO OBLIGATORIO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Sobrescribe 'ejecutar_mision' para ejecutar el protocolo de inspección técnica.
        """
        reporte_despegue = super().ejecutar_mision(pedido)

        print(f"[{self.id_dron}] Ejecutando misión de inspección de infraestructura...")
        print(f"  -> Manteniendo vuelo estacionario a distancia segura de {self._rango_sensor_ultrasonico_m:.1f} m mediante ultrasonido.")
        print(f"  -> Escaneando antenas y vertipuertos con zoom óptico de {self._zoom_optico_x}x.")

        reporte_despegue.update({
            "instrumental_activado": "SENSOR_ULTRASONICO_Y_ZOOM",
            "zoom_aplicado": f"{self._zoom_optico_x}x",
            "distancia_seguridad_m": self._rango_sensor_ultrasonico_m,
            "estado_especifico": "Inspección finalizada",
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-10 / HU-11)
        
        Aplica la tasa especializada de 1.5% de batería por kilómetro para inspección:
            Consumo (%) = distancia_km * 1.5
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 1.5)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-11)
        """
        return f"Diagnóstico: Zoom Óptico {self._zoom_optico_x}x, Sensor Ultrasónico {self._rango_sensor_ultrasonico_m:.1f}m [OPERATIVOS]"



    def predecir_viabilidad_mision(self, distancia_km: float) -> dict:
        """
        PILAR: POLIMORFISMO EN PREDICCIÓN ENERGÉTICA PRE-DESPEGUE (HU-10)
        Reutiliza la lógica base de Dron y especializa el motivo de inspección.
        """
        reporte = super().predecir_viabilidad_mision(distancia_km)
        if reporte["mision_viable"]:
            reporte["diagnostico_autonomia"] = (
                f"Misión viable: autonomía de inspección suficiente con remanente proyectado de {reporte['bateria_remanente_pct']:.1f}%."
            )
        elif self.telemetria is not None:
            reporte["diagnostico_autonomia"] = (
                f"Misión no viable: batería insuficiente ({reporte['bateria_actual_pct']:.1f}% actual vs. "
                f"{reporte['consumo_estimado_pct']:.1f}% requerido por inspección estacionaria)."
            )
        return reporte

    # ==========================================================================
    # 5. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base vía 'super().__str__()'
        e integrando los aditamentos de inspección técnica.
        """
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        return (
            f"{ficha_sin_cierre}\n"
            f"  Instrumental       : Zoom Óptico {self._zoom_optico_x}x | Sensor Ultrasónico {self._rango_sensor_ultrasonico_m:.1f} m\n"
            f"  Eficiencia Consumo : 1.5% bat/km (Tasa Inspección)\n"
            f"{cierre}"
        )

    def __repr__(self) -> str:
        """
        Sobrescribe __repr__ para extender la representación oficial con aditamentos de inspección.
        """
        return (
            f"DronInspeccion(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"zoom_optico_x={self._zoom_optico_x}, rango_sensor_ultrasonico_m={self._rango_sensor_ultrasonico_m}, "
            f"disponible={self.disponible})"
        )
