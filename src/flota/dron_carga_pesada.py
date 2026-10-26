# Módulo de especialización para Dron de Carga Pesada (Logística Industrial)
# Responsable: Juan Manuel Pava Higuita (Sprint 2 - HU-09, HU-10)

# ==============================================================================
# 1. IMPORTACIONES Y CONTROL DE TIPADO DIFERIDO (PEP 563 & PEP 484)
# ==============================================================================
# 'from __future__ import annotations' permite interpretar las anotaciones de tipos
# como cadenas diferidas en tiempo de ejecución, optimizando la resolución de tipos.
from __future__ import annotations

# 'TYPE_CHECKING' previene el ciclo de importación entre 'pedido.py' y este módulo.
# En tiempo de ejecución es False; para herramientas de análisis estático es True.
from typing import TYPE_CHECKING
from src.flota.dron import Dron
from src.excepciones.errores import ActualizarEstadoDronError

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


# ==============================================================================
# 2. DEFINICIÓN DE CLASE Y APLICACIÓN DE PILARES DE POO
# ==============================================================================
# PILAR: HERENCIA
# 'DronCargaPesada' hereda de la clase abstracta 'Dron', reutilizando el cálculo geodésico,
# la telemetría periódica, el odómetro de vuelo y los protocolos de base.
class DronCargaPesada(Dron):
    """
    Subclase especializada en el remolque y traslado de cargamentos voluminosos e industriales.
    
    Características Principales:
    - Diseñado para operaciones inter-bodegas en el Valle de Aburrá (ej. Caldas, Sabaneta, Guayabal).
    - Tren motriz industrial de alto empuje (hexacóptero u octocóptero, mínimo 4 rotores).
    - Gancho de remolque electromagnético de alta potencia (Watts) para anclaje de contenedores.
    - Bodega o tolva volumétrica medida en metros cúbicos (m³).
    - Tasa de consumo energético polinómica por arrastre y cantidad de rotores activos.
    """

    # Constantes oficiales del sistema SkyRoute
    CATEGORIA_ESPECIALIZADA: str = "CARGA_PESADA"
    VOLUMEN_DEFAULT_M3: float = 2.5
    ROTORES_DEFAULT: int = 8
    POTENCIA_REMOLQUE_DEFAULT_W: float = 4500.0

    def __init__(
        self,
        id_dron: str,
        modelo_aeronave: str,
        velocidad_promedio_kmh: float = 50.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        volumen_carga_m3: float = VOLUMEN_DEFAULT_M3,
        numero_rotores: int = ROTORES_DEFAULT,
        potencia_remolque_w: float = POTENCIA_REMOLQUE_DEFAULT_W,
    ) -> None:
        """
        Inicializa una aeronave de transporte pesado industrial.
        
        Invoca el constructor base de 'Dron' mediante 'super().__init__(...)' para delegar
        la inicialización de identificadores, cinemática y calculador geodésico, y
        asigna a través de setters sus aditamentos industriales.
        """
        # Delegación al constructor padre (Herencia)
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        # Categoría oficial fijada para despacho en SistemaCentroControl y Pedido
        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # PILAR: ENCAPSULAMIENTO PROTEGIDO
        # Atributos protegidos con guión simple (_) para no quebrar la cadena de herencia,
        # asignados mediante setters para garantizar integridad de dominio aeronáutico.
        self.volumen_carga_m3 = volumen_carga_m3
        self.numero_rotores = numero_rotores
        self.potencia_remolque_w = potencia_remolque_w

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def volumen_carga_m3(self) -> float:
        """Retorna el volumen útil de carga en metros cúbicos (m³)."""
        return self._volumen_carga_m3

    @volumen_carga_m3.setter
    def volumen_carga_m3(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"El volumen de carga debe ser numérico. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"El volumen de carga debe ser estrictamente mayor a 0 m³. Recibido: {valor}")
        self._volumen_carga_m3 = float(valor)

    @property
    def numero_rotores(self) -> int:
        """Retorna la cantidad de motores/rotores industriales de la aeronave."""
        return self._numero_rotores

    @numero_rotores.setter
    def numero_rotores(self, valor: int) -> None:
        # Validación de tipo entero (no booleano ni decimal)
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"El número de rotores debe ser un número entero. Recibido: {type(valor).__name__}")
        # Un dron de carga pesada requiere configuración mínima cuadricóptero/hexacóptero para sustentar peso
        if valor < 4:
            raise ValueError(f"Un dron de carga pesada requiere al menos 4 rotores para sustentación. Recibido: {valor}")
        self._numero_rotores = valor

    @property
    def potencia_remolque_w(self) -> float:
        """Retorna la potencia del sistema electromagnético de remolque en Watts (W)."""
        return self._potencia_remolque_w

    @potencia_remolque_w.setter
    def potencia_remolque_w(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La potencia de remolque debe ser numérica. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La potencia de remolque debe ser estrictamente mayor a 0 W. Recibido: {valor}")
        self._potencia_remolque_w = float(valor)

    # ==========================================================================
    # 4. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO ABSTRACTO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Sobrescribe 'ejecutar_mision' para ejecutar el protocolo logístico de carga pesada.
        
        FLUJO DE EJECUCIÓN:
        1. Invocación de la Lógica Base: Llama a 'super().ejecutar_mision(pedido)' para
           validar disponibilidad, autonomía energética, activar motores en vuelo y poner
           el pedido en 'EN_TRANSITO'.
        2. Simulación de Acople: Simula la sujeción electromagnética del contenedor industrial.
        3. Enriquecimiento del Reporte: Retorna el informe técnico con volumen, potencia y rotores.
        """
        # Delegación al despegue base (Herencia y Abstracción)
        reporte_despegue = super().ejecutar_mision(pedido)

        # Registro en consola de operaciones industriales
        print(f"[{self.id_dron}] Iniciando operación logística de Carga Pesada...")
        print(f"  -> Acoplando contenedor de {self._volumen_carga_m3:.1f} m³ mediante gancho electromagnético.")
        print(f"  -> Tracción activa con {self._numero_rotores} rotores industriales ({self._potencia_remolque_w:.0f} W).")

        # Metadatos especializados devueltos al centro de control
        reporte_despegue.update({
            "instrumental_activado": "GANCHO_REMOLQUE_INDUSTRIAL",
            "volumen_carga_m3": self._volumen_carga_m3,
            "potencia_remolque_w": self._potencia_remolque_w,
            "numero_rotores": self._numero_rotores,
            "estado_especifico": "Carga pesada asegurada en tránsito inter-bodegas",
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-10)
        
        Calcula el consumo de batería aplicando la fórmula polinómica para carga pesada:
            Consumo (%) = distancia_km * (2.5 + (numero_rotores * 0.1))
        
        El consumo es notablemente superior al de un dron ligero debido al peso estructural,
        el arrastre del contenedor exterior y la energía requerida por múltiples motores.
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        tasa_consumo = 2.5 + (self._numero_rotores * 0.1)
        return float(distancia_km * tasa_consumo)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-09)
        
        Genera el informe de inspección técnica del tren de propulsión y el gancho de carga.
        """
        return (
            f"Diagnóstico: Tren Industrial ({self._numero_rotores} rotores) | "
            f"Volumen: {self._volumen_carga_m3:.1f}m³ | Remolque: {self._potencia_remolque_w:.0f}W [OPERATIVOS]"
        )

    def predecir_viabilidad_mision(self, distancia_km: float) -> dict:
        """
        PILAR: POLIMORFISMO EN PREDICCIÓN ENERGÉTICA PRE-DESPEGUE (HU-10)
        
        Evalúa y predice con exactitud técnica si la batería actual del dron industrial
        soportará la misión antes del despegue, aplicando la tasa polinómica según
        sus rotores activos y el arrastre de carga pesada.
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
            motivo = f"Misión no viable: batería insuficiente ({bateria_actual:.1f}% actual vs. {consumo_estimado:.1f}% requerido por arrastre industrial)."
        else:
            motivo = f"Misión viable: autonomía pesada suficiente con remanente proyectado de {bateria_remanente:.1f}%."

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
    # 5. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA (HU-10)
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base vía 'super().__str__()'
        e integrando las especificaciones industriales de la bodega, rotores y eficiencia energética.
        """
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        tasa_consumo = 2.5 + (self._numero_rotores * 0.1)
        return (
            f"{ficha_sin_cierre}\n"
            f"  Volumen de Bodega  : {self._volumen_carga_m3:.1f} m³\n"
            f"  Tren de Propulsión : {self._numero_rotores} rotores | Remolque: {self._potencia_remolque_w:.0f} W\n"
            f"  Eficiencia Consumo : {tasa_consumo:.1f}% bat/km (Base 2.5% + {self._numero_rotores} rotores x 0.1%)\n"
            f"{cierre}"
        )

    def __repr__(self) -> str:
        """
        Sobrescribe __repr__ para extender la representación técnica oficial con
        los parámetros especializados de carga pesada (HU-10).
        """
        return (
            f"DronCargaPesada(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"volumen_carga_m3={self._volumen_carga_m3}, numero_rotores={self._numero_rotores}, "
            f"potencia_remolque_w={self._potencia_remolque_w}, disponible={self.disponible})"
        )
