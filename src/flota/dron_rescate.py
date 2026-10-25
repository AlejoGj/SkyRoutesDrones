# Módulo de especialización para Dron de Búsqueda y Rescate
# Responsable: Valery Arboleda Ardila (Sprint 2 - HU-11)

from __future__ import annotations
from typing import TYPE_CHECKING
from src.flota.dron import Dron

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


class DronRescate(Dron):
    CATEGORIA_ESPECIALIZADA = "BUSQUEDA_RESCATE"

    def __init__(
        self,
        id_dron: str = None,
        modelo_aeronave: str = None,
        camara_termica: bool = True,
        kit_auxilios_equipado: bool = True,
        potencia_altavoz_db: int = 110,
        velocidad_promedio_kmh: float = 65.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        potenciaAltavozDb: int = None,
        **kwargs,
    ) -> None:
        # Resolver alias de parámetro camelCase si se suministra
        if potenciaAltavozDb is not None:
            potencia_altavoz_db = potenciaAltavozDb

        # Manejo flexible de orden posicional: permite (camara, kit, potencia, id, modelo) o (id, modelo, camara, kit, potencia)
        if isinstance(id_dron, bool) and (isinstance(potencia_altavoz_db, str) or isinstance(potenciaAltavozDb, str)):
            actual_camara = id_dron
            actual_kit = modelo_aeronave
            actual_potencia = camara_termica
            actual_id = kit_auxilios_equipado
            actual_modelo = potencia_altavoz_db or potenciaAltavozDb
            id_dron = actual_id
            modelo_aeronave = actual_modelo
            camara_termica = actual_camara
            kit_auxilios_equipado = actual_kit
            potencia_altavoz_db = actual_potencia

        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        # Categoría especializada oficial fija
        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # Validación defensiva de cámara térmica
        if not isinstance(camara_termica, bool):
            raise TypeError(f"La cámara térmica debe ser estrictamente booleana (True/False). Recibido: {type(camara_termica).__name__}")
        self.camara_termica = camara_termica

        # Validación defensiva de kit de auxilios
        if not isinstance(kit_auxilios_equipado, bool):
            raise TypeError(f"El indicador de kit de auxilios debe ser booleano (True/False). Recibido: {type(kit_auxilios_equipado).__name__}")
        self.kit_auxilios_equipado = kit_auxilios_equipado

        # Validación defensiva de potencia de altavoz
        if isinstance(potencia_altavoz_db, bool) or not isinstance(potencia_altavoz_db, int):
            raise TypeError(f"La potencia del altavoz debe ser un número entero (dB). Recibido: {type(potencia_altavoz_db).__name__}")
        if potencia_altavoz_db <= 0:
            raise ValueError(f"La potencia del altavoz debe ser mayor a 0 dB. Recibido: {potencia_altavoz_db}")
        self.potencia_altavoz_db = potencia_altavoz_db
        self.potenciaAltavozDb = potencia_altavoz_db

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        reporte_despegue = super().ejecutar_mision(pedido)
        print(f"[{self.id_dron}] Ejecutando misión del protocolo de Búsqueda y Rescate...")
        print(f"  -> Realizando barrido térmico en coordenadas de emergencia y activando altavoz a {self.potencia_altavoz_db} dB.")

        estado_kit = "Kit de auxilios entregado" if self.kit_auxilios_equipado else "Sujeto localizado sin kit"
        if self.kit_auxilios_equipado:
            print(f"  -> {estado_kit} en el punto de coordenadas.")
        else:
            print(f"  -> {estado_kit}.")

        reporte_despegue.update({
            "instrumental_activado": "CAMARA_TERMICA_Y_ALTAVOZ",
            "potencia_altavoz_db": self.potencia_altavoz_db,
            "barrido_termico": "ACTIVO",
            "resultado_rescate": estado_kit,
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        if distancia_km < 0:
            return 0.0
        return distancia_km * 2.0

    def inspeccionar_sistemas_especializados(self) -> str:
        termica = "ENCENDIDA" if self.camara_termica else "APAGADA"
        kit = "EQUIPADO" if self.kit_auxilios_equipado else "NO EQUIPADO"
        return f"Diagnóstico: Cámara Térmica [{termica}] | Kit Auxilios [{kit}] | Altavoz [{self.potencia_altavoz_db} dB]"

