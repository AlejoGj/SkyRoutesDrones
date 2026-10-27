# Módulo de especialización para Dron de Búsqueda y Rescate
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
# 'DronRescate' hereda de la clase abstracta base 'Dron'.
class DronRescate(Dron):
    """
    Subclase especializada en protocolos de contingencia, búsqueda y rescate (SAR),
    y localización térmica de personas o aeronaves extraviadas en el Valle de Aburrá.
    
    Características Principales:
    - Cámara termográfica infrarroja para detección de firmas de calor corporal.
    - Kit de primeros auxilios y supervivencia aerotransportado para lanzamiento en coordenadas de rescate.
    - Altavoz acústico de alta potencia en decibelios (dB) para comunicación con sobrevivientes.
    - Tasa de consumo energético especializada (2.0% de batería por kilómetro) por equipamiento activo y altavoz.
    """

    CATEGORIA_ESPECIALIZADA: str = "BUSQUEDA_RESCATE"
    CAMARA_TERMICA_DEFAULT: bool = True
    KIT_AUXILIOS_DEFAULT: bool = True
    POTENCIA_ALTAVOZ_DEFAULT_DB: int = 110

    def __init__(
        self,
        id_dron: str,
        modelo_aeronave: str,
        camara_termica: bool = CAMARA_TERMICA_DEFAULT,
        kit_auxilios_equipado: bool = KIT_AUXILIOS_DEFAULT,
        potencia_altavoz_db: int = POTENCIA_ALTAVOZ_DEFAULT_DB,
        velocidad_promedio_kmh: float = 65.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        potenciaAltavozDb: int = None
    ) -> None:
        """
        Inicializa un dron de búsqueda y rescate con equipamiento especializado validado.
        Soporta alias camelCase ('potenciaAltavozDb') para compatibilidad con el modelo UML.
        """
        # Resolver alias de parámetro camelCase si se suministra
        if potenciaAltavozDb is not None:
            potencia_altavoz_db = potenciaAltavozDb


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
        self.camara_termica = camara_termica
        self.kit_auxilios_equipado = kit_auxilios_equipado
        self.potencia_altavoz_db = potencia_altavoz_db
        self.potencia_altavoz_db = potencia_altavoz_db

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def camara_termica(self) -> bool:
        """Indica si el sensor termográfico infrarrojo está habilitado."""
        return self._camara_termica

    @camara_termica.setter
    def camara_termica(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"La cámara térmica debe ser estrictamente booleana (True/False). Recibido: {type(valor).__name__}")
        self._camara_termica = valor

    @property
    def kit_auxilios_equipado(self) -> bool:
        """Indica si el contenedor con kit de primeros auxilios está cargado."""
        return self._kit_auxilios_equipado

    @kit_auxilios_equipado.setter
    def kit_auxilios_equipado(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El indicador de kit de auxilios debe ser booleano (True/False). Recibido: {type(valor).__name__}")
        self._kit_auxilios_equipado = valor

    @property
    def potencia_altavoz_db(self) -> int:
        """Retorna la potencia acústica del altavoz de comunicación en decibelios (dB)."""
        return self._potencia_altavoz_db

    @potencia_altavoz_db.setter
    def potencia_altavoz_db(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"La potencia del altavoz debe ser un número entero (dB). Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La potencia del altavoz debe ser mayor a 0 dB. Recibido: {valor}")
        self._potencia_altavoz_db = valor

    # Alias camelCase para compatibilidad hacia atrás
    @property
    def potenciaAltavozDb(self) -> int:
        return self._potencia_altavoz_db

    @potenciaAltavozDb.setter
    def potenciaAltavozDb(self, valor: int) -> None:
        self.potencia_altavoz_db = valor

    # ==========================================================================
    # 4. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO OBLIGATORIO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Sobrescribe 'ejecutar_mision' para ejecutar el protocolo de búsqueda y rescate.
        """
        reporte_despegue = super().ejecutar_mision(pedido)

        print(f"[{self.id_dron}] Ejecutando misión del protocolo de Búsqueda y Rescate...")
        print(f"  -> Realizando barrido térmico en coordenadas de emergencia y activando altavoz a {self._potencia_altavoz_db} dB.")

        estado_kit = "Kit de auxilios entregado" if self._kit_auxilios_equipado else "Sujeto localizado sin kit"
        if self._kit_auxilios_equipado:
            print(f"  -> {estado_kit} en el punto de coordenadas.")
        else:
            print(f"  -> {estado_kit}.")

        reporte_despegue.update({
            "instrumental_activado": "CAMARA_TERMICA_Y_ALTAVOZ",
            "potencia_altavoz_db": self._potencia_altavoz_db,
            "barrido_termico": "ACTIVO",
            "resultado_rescate": estado_kit,
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-10 / HU-11)
        
        Aplica la tasa especializada de 2.0% de batería por kilómetro para rescate:
            Consumo (%) = distancia_km * 2.0
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 2.0)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-11)
        """
        termica = "ENCENDIDA" if self._camara_termica else "APAGADA"
        kit = "EQUIPADO" if self._kit_auxilios_equipado else "NO EQUIPADO"
        return f"Diagnóstico: Cámara Térmica [{termica}] | Kit Auxilios [{kit}] | Altavoz [{self._potencia_altavoz_db} dB]"

    def predecir_viabilidad_mision(self, distancia_km: float) -> dict:
        """
        PILAR: POLIMORFISMO EN PREDICCIÓN ENERGÉTICA PRE-DESPEGUE (HU-10)
        Reutiliza la lógica base de Dron y especializa el motivo de rescate SAR.
        """
        reporte = super().predecir_viabilidad_mision(distancia_km)
        if reporte["mision_viable"]:
            reporte["diagnostico_autonomia"] = (
                f"Misión viable: autonomía SAR suficiente con remanente proyectado de {reporte['bateria_remanente_pct']:.1f}%."
            )
        elif self.telemetria is not None:
            reporte["diagnostico_autonomia"] = (
                f"Misión no viable: batería insuficiente ({reporte['bateria_actual_pct']:.1f}% actual vs. "
                f"{reporte['consumo_estimado_pct']:.1f}% requerido por protocolo SAR)."
            )
        return reporte

    # ==========================================================================
    # 5. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base vía 'super().__str__()'
        e integrando los aditamentos de búsqueda y rescate.
        """
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        termica = "Sí" if self._camara_termica else "No"
        kit = "Sí" if self._kit_auxilios_equipado else "No"
        return (
            f"{ficha_sin_cierre}\n"
            f"  Instrumental       : Térmica: [{termica}] | Kit Auxilio: [{kit}] | Altavoz: [{self._potencia_altavoz_db} dB]\n"
            f"  Eficiencia Consumo : 2.0% bat/km (Tasa Rescate SAR)\n"
            f"{cierre}"
        )

    def __repr__(self) -> str:
        """
        Sobrescribe __repr__ para extender la representación oficial con aditamentos de rescate.
        """
        return (
            f"DronRescate(id_dron='{self.id_dron}', modelo_aeronave='{self.modelo_aeronave}', "
            f"camara_termica={self._camara_termica}, kit_auxilios_equipado={self._kit_auxilios_equipado}, "
            f"potencia_altavoz_db={self._potencia_altavoz_db}, disponible={self.disponible})"
        )
