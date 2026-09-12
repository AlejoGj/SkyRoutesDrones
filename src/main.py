# Script principal de integración y pruebas del sistema SkyRoute
# Sprint 1: Integración general entre clases

from src.excepciones.errores import (
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
    CoordenadaInvalidaError,
)
from src.telemetria.telemetria import TelemetriaDrone
from src.geodesia.calculador import CalculadorGeodesico
from src.flota.dron import Dron
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.control.log_operacion import LogOperacion
from src.control.centro_control import SistemaCentroControl


def main():
    pass

