# Módulo orquestador del centro de control de operaciones
# Responsable: Valery Arboleda Ardila

from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota.dron import Dron
from src.control.log_operacion import LogOperacion


class SistemaCentroControl:
    def __init__(self, lat_base=6.2089, lon_base=-75.5684):
        pass

    def registrar_usuario(self, usuario):
        pass

    def agregar_dron(self, dron):
        pass

    def registrar_pedido(self, pedido):
        pass

    def asignar_dron_a_pedido(self, id_pedido):
        pass

    def gestionar_retorno_a_base(self, id_dron):
        pass

    def generar_log(self, tipo_evento, id_dron=None, id_pedido=None, detalles=""):
        pass
