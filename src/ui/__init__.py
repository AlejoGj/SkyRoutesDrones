# Paquete de Interfaz Gráfica Web Nativa (http.server) para SkyRoute Drones

from src.ui.catalogos import (
    ESQUEMA_FABRICA,
    ETIQUETAS_CATEGORIA,
    SUGERENCIAS_DIRECCIONES,
)
from src.ui.controlador import ControladorSkyRoute
from src.ui.manejador_errores import formatear_excepcion_dominio
from src.ui.serializadores import (
    construir_snapshot_estado,
    diagnosticar_candidatos_pedido,
    serializar_dron,
    serializar_pedido,
)
from src.ui.servidor import ManejadorSkyRouteHTTP, crear_servidor, iniciar_aplicacion
from src.ui.sesiones_vuelo import calcular_progreso_lineal

__all__ = [
    "ControladorSkyRoute",
    "ManejadorSkyRouteHTTP",
    "crear_servidor",
    "iniciar_aplicacion",
    "ETIQUETAS_CATEGORIA",
    "ESQUEMA_FABRICA",
    "SUGERENCIAS_DIRECCIONES",
    "formatear_excepcion_dominio",
    "construir_snapshot_estado",
    "diagnosticar_candidatos_pedido",
    "serializar_dron",
    "serializar_pedido",
    "calcular_progreso_lineal",
]
