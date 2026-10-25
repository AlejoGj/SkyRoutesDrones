# Módulo de especialización para Dron de Inspección de Infraestructura
# Responsable: Valery Arboleda Ardila (Sprint 2 - HU-11)

from __future__ import annotations
from typing import TYPE_CHECKING
from src.flota.dron import Dron

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


class DronInspeccion(Dron):
    CATEGORIA_ESPECIALIZADA = "INSPECCION_INFRAESTRUCTURA"

    def __init__(
        self,
        id_dron: str = None,
        modelo_aeronave: str = None,
        zoom_optico_x: int = 10,
        rango_sensor_ultrasonico_m: float = 5.0,
        velocidad_promedio_kmh: float = 50.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        **kwargs,
    ) -> None:
        # Manejo flexible de orden posicional: permite (zoom, rango, id, modelo) o (id, modelo, zoom, rango)
        if isinstance(id_dron, (int, float)) and isinstance(zoom_optico_x, (str, type(None))):
            actual_zoom = id_dron
            actual_rango = modelo_aeronave
            actual_id = zoom_optico_x
            actual_modelo = rango_sensor_ultrasonico_m
            id_dron = actual_id
            modelo_aeronave = actual_modelo
            zoom_optico_x = actual_zoom
            rango_sensor_ultrasonico_m = actual_rango

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

        # Validación defensiva de zoom óptico
        if isinstance(zoom_optico_x, bool) or not isinstance(zoom_optico_x, int):
            raise TypeError(f"El zoom óptico debe ser un número entero. Recibido: {type(zoom_optico_x).__name__}")
        if zoom_optico_x <= 0:
            raise ValueError(f"El factor de zoom óptico debe ser estrictamente mayor a 0x. Recibido: {zoom_optico_x}")
        self.zoom_optico_x = zoom_optico_x

        # Validación defensiva de sensor ultrasónico
        if isinstance(rango_sensor_ultrasonico_m, bool) or not isinstance(rango_sensor_ultrasonico_m, (int, float)):
            raise TypeError(f"El rango del sensor ultrasónico debe ser numérico. Recibido: {type(rango_sensor_ultrasonico_m).__name__}")
        if rango_sensor_ultrasonico_m <= 0:
            raise ValueError(f"El rango del sensor ultrasónico debe ser estrictamente mayor a 0 metros. Recibido: {rango_sensor_ultrasonico_m}")
        self.rango_sensor_ultrasonico_m = float(rango_sensor_ultrasonico_m)

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        pass

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        pass

    def inspeccionar_sistemas_especializados(self) -> str:
        pass
