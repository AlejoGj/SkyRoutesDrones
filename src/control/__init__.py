"""Módulo de centro de control, simulación cinemática y registro de operaciones."""

from src.control.centro_control import (
    SistemaCentroControl,
    FABRICA_DRONES,
    registrar_subclase_en_fabrica,
    instanciar_dron_desde_fabrica,
)
from src.control.log_operacion import LogOperacion
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo

