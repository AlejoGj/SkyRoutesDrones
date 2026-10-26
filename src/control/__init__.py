"""Módulo de centro de control y registro de operaciones."""

from src.control.centro_control import SistemaCentroControl, FABRICA_DRONES
from src.control.log_operacion import LogOperacion

__all__ = [
    "SistemaCentroControl",
    "LogOperacion",
    "FABRICA_DRONES",
]
