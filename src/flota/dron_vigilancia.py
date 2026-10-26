# HU-08 Dron de vigilancia
# Responsable: Valery Arboleda Ardila (Sprint 2 - HU-08)

from __future__ import annotations
from typing import TYPE_CHECKING
from src.flota.dron import Dron

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


class DronVigilancia(Dron):
    CATEGORIA_ESPECIALIZADA = "VIGILANCIA"

    def __init__(
        self,
        resolucion_camara_mp: int,
        vision_nocturna: bool,
        frecuencia_transmision_ghz: float,
        id_dron: str,
        modelo_aeronave: str,
        velocidad_promedio_kmh: float = 60.0,
        kilometraje_total_km: float = 0.0,
    ):
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
        )

        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # VALIDACIONES
        # - Resolucion de cámaras
        if not isinstance(resolucion_camara_mp, int):
            raise TypeError("La resolución de la cámara debe ser un número entero (int).")
        if resolucion_camara_mp <= 0:
            raise ValueError("La resolución de la cámara debe ser mayor a 0 MP.")
        self.resolucion_camara_mp = resolucion_camara_mp

        # - Visión nocturna
        if not isinstance(vision_nocturna, bool):
            raise TypeError("El indicador de visión nocturna debe ser un valor booleano (True o False).")
        self.vision_nocturna = vision_nocturna

        # - Frecuencia de transmision
        if not isinstance(frecuencia_transmision_ghz, (float, int)):
            raise TypeError("La frecuencia de transmisión debe ser un número (float o int).")
        if frecuencia_transmision_ghz <= 0:
            raise ValueError("La frecuencia de transmisión debe ser mayor a 0.0 GHz.")
        self.frecuencia_transmision_ghz = float(frecuencia_transmision_ghz)

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        reporte_despegue = super().ejecutar_mision(pedido)
        print(f"{self.id_dron} Ejecutando mision de vigilancia y escolta")
        print(f"Simulando transmisión de video cifrado a {self.frecuencia_transmision_ghz} GHz")
        print("Misión de escolta aérea de cargamento en curso")

        reporte_despegue.update({
            "instrumental_activado": "CAMARAS_Y_VIDEO_CIFRADO",
            "estado_especifico": "Escolta finalizada sin anomalías"
        })
        return reporte_despegue

    def inspeccionar_sistemas_especializados(self) -> str:
        estado_nocturna = "ACTIVADA" if self.vision_nocturna else "DESACTIVADA"
        return f"Diagnóstico Seguridad -> Cámara: {self.resolucion_camara_mp}MP | Visión Nocturna: [{estado_nocturna}] | Enlace Video: {self.frecuencia_transmision_ghz}GHz [OPERATIVOS]"

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        # Teniendo en cuenta que el streaming de video gasta un poco más de energía por km
        return distancia_km * 1.3

