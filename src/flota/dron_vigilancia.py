# Módulo de especialización para Dron de Vigilancia y Escolta Aérea
# Historia de Usuario: HU-08 (Valery Arboleda Ardila)
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
# 'DronVigilancia' hereda de la clase abstracta 'Dron', reutilizando el cálculo geodésico,
# la telemetría periódica, el odómetro de vuelo y los protocolos de base.
class DronVigilancia(Dron):
    """
    Subclase especializada en monitoreo de seguridad, patrullaje perimetral y
    escolta aérea de cargamentos críticos en el Valle de Aburrá.
    
    Características Principales:
    - Cámara óptica de alta resolución en Megapíxeles (MP).
    - Sensor electroóptico de visión nocturna (infrarrojo/térmico).
    - Sistema de enlace de transmisión de video cifrado en banda GHz (Gigahertz).
    - Tasa de consumo energético especializada (1.3% de batería por kilómetro) considerando la transmisión continua de video.
    """

    CATEGORIA_ESPECIALIZADA: str = "VIGILANCIA"
    RESOLUCION_DEFAULT_MP: int = 48
    VISION_NOCTURNA_DEFAULT: bool = True
    FRECUENCIA_DEFAULT_GHZ: float = 5.8

    def __init__(
        self,
        resolucion_camara_mp: int = RESOLUCION_DEFAULT_MP,
        vision_nocturna: bool = VISION_NOCTURNA_DEFAULT,
        frecuencia_transmision_ghz: float = FRECUENCIA_DEFAULT_GHZ,
        id_dron: str = None,
        modelo_aeronave: str = None,
        velocidad_promedio_kmh: float = 60.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        **kwargs,
    ) -> None:
        """
        Inicializa un dron de vigilancia y seguridad.
        
        Soporta tanto el orden posicional de aditamentos (resolucion, vision, frecuencia, id, modelo)
        como el orden tradicional (id, modelo, resolucion, vision, frecuencia) para máxima compatibilidad.
        """
        # Manejo flexible de orden posicional para compatibilidad con scripts del equipo
        if isinstance(resolucion_camara_mp, str) and isinstance(id_dron, (int, float)):
            actual_id = resolucion_camara_mp
            actual_modelo = vision_nocturna
            actual_resolucion = frecuencia_transmision_ghz
            actual_vision = id_dron
            actual_frecuencia = modelo_aeronave
            id_dron = actual_id
            modelo_aeronave = actual_modelo
            resolucion_camara_mp = actual_resolucion
            vision_nocturna = actual_vision
            frecuencia_transmision_ghz = actual_frecuencia

        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # PILAR: ENCAPSULAMIENTO PROTEGIDO
        # Asignación a través de setters para validaciones defensivas de dominio
        self.resolucion_camara_mp = resolucion_camara_mp
        self.vision_nocturna = vision_nocturna
        self.frecuencia_transmision_ghz = frecuencia_transmision_ghz

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def resolucion_camara_mp(self) -> int:
        """Retorna la resolución del sensor óptico principal en Megapíxeles (MP)."""
        return self._resolucion_camara_mp

    @resolucion_camara_mp.setter
    def resolucion_camara_mp(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"La resolución de la cámara debe ser un número entero (int). Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La resolución de la cámara debe ser mayor a 0 MP. Recibido: {valor}")
        self._resolucion_camara_mp = valor

    @property
    def vision_nocturna(self) -> bool:
        """Indica si el sistema de visión nocturna está equipado y operativo."""
        return self._vision_nocturna

    @vision_nocturna.setter
    def vision_nocturna(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El indicador de visión nocturna debe ser un valor booleano (True o False). Recibido: {type(valor).__name__}")
        self._vision_nocturna = valor

    @property
    def frecuencia_transmision_ghz(self) -> float:
        """Retorna la frecuencia del enlace de video cifrado en Gigahertz (GHz)."""
        return self._frecuencia_transmision_ghz

    @frecuencia_transmision_ghz.setter
    def frecuencia_transmision_ghz(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La frecuencia de transmisión debe ser un número (float o int). Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La frecuencia de transmisión debe ser mayor a 0.0 GHz. Recibido: {valor}")
        self._frecuencia_transmision_ghz = float(valor)

    # ==========================================================================
    # 4. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO OBLIGATORIO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Sobrescribe 'ejecutar_mision' para ejecutar el protocolo de vigilancia y escolta aérea.
        """
        reporte_despegue = super().ejecutar_mision(pedido)

        print(f"[{self.id_dron}] Ejecutando misión de vigilancia y escolta aérea...")
        print(f"  -> Transmitiendo video cifrado en tiempo real a {self._frecuencia_transmision_ghz} GHz.")
        estado_nocturna = "ACTIVA" if self._vision_nocturna else "INACTIVA"
        print(f"  -> Cámara de {self._resolucion_camara_mp} MP operativa con visión nocturna [{estado_nocturna}].")
        print("  -> Misión de escolta aérea de cargamento en curso.")

        reporte_despegue.update({
            "instrumental_activado": "CAMARAS_Y_VIDEO_CIFRADO",
            "resolucion_mp": self._resolucion_camara_mp,
            "frecuencia_ghz": self._frecuencia_transmision_ghz,
            "vision_nocturna": self._vision_nocturna,
            "estado_especifico": "Escolta finalizada sin anomalías",
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-08 / HU-10)
        
        Aplica la tasa especializada de 1.3% de batería por kilómetro para vigilancia:
            Consumo (%) = distancia_km * 1.3
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 1.3)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-08)
        """
        estado_nocturna = "ACTIVADA" if self._vision_nocturna else "DESACTIVADA"
        return (
            f"Diagnóstico Seguridad -> Cámara: {self._resolucion_camara_mp}MP | "
            f"Visión Nocturna: [{estado_nocturna}] | Enlace Video: {self._frecuencia_transmision_ghz}GHz [OPERATIVOS]"
        )

    def predecir_viabilidad_mision(self, distancia_km: float) -> dict:
        """
        PILAR: POLIMORFISMO EN PREDICCIÓN ENERGÉTICA PRE-DESPEGUE (HU-10)
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km < 0:
            raise ValueError(f"La distancia no puede ser negativa. Recibido: {distancia_km}")

        consumo_estimado = self.calcular_consumo_estimado(distancia_km)
        bateria_actual = self.telemetria.bateria if self.telemetria is not None else 0.0
        tiene_telemetria = self.telemetria is not None

        viable = tiene_telemetria and (bateria_actual >= consumo_estimado)
        bateria_remanente = max(0.0, bateria_actual - consumo_estimado) if viable else 0.0

        if not tiene_telemetria:
            motivo = "Misión no viable: el dron no tiene telemetría asignada."
        elif bateria_actual < consumo_estimado:
            motivo = f"Misión no viable: batería insuficiente ({bateria_actual:.1f}% actual vs. {consumo_estimado:.1f}% requerido por streaming)."
        else:
            motivo = f"Misión viable: autonomía de vigilancia suficiente con remanente proyectado de {bateria_remanente:.1f}%."

        return {
            "id_dron": self.id_dron,
            "tipo_dron": self.__class__.__name__,
            "distancia_km": round(float(distancia_km), 2),
            "consumo_estimado_pct": round(consumo_estimado, 2),
            "bateria_actual_pct": round(bateria_actual, 2),
            "bateria_remanente_pct": round(bateria_remanente, 2),
            "mision_viable": viable,
            "diagnostico_autonomia": motivo,
        }

    # ==========================================================================
    # 5. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base vía 'super().__str__()'
        e integrando el instrumental de seguridad y vigilancia.
        """
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        nocturna_str = "Sí" if self._vision_nocturna else "No"
        return (
            f"{ficha_sin_cierre}\n"
            f"  Instrumental Óptico: Cámara {self._resolucion_camara_mp} MP | Visión Nocturna: [{nocturna_str}]\n"
            f"  Transmisión Video  : Enlace Cifrado {self._frecuencia_transmision_ghz:.1f} GHz | Eficiencia: 1.3% bat/km\n"
            f"{cierre}"
        )

    def __repr__(self) -> str:
        """
        Sobrescribe __repr__ para extender la representación oficial con aditamentos de vigilancia.
        """
        return (
            f"DronVigilancia(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"resolucion_camara_mp={self._resolucion_camara_mp}, vision_nocturna={self._vision_nocturna}, "
            f"frecuencia_transmision_ghz={self._frecuencia_transmision_ghz}, disponible={self.disponible})"
        )
