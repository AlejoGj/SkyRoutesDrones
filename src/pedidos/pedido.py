# Módulo de gestión de pedidos y solicitudes de servicio
# Responsable: Valery Arboleda Ardila

from src.usuarios.usuario import Usuario


class Pedido:
    def __init__(self, id_pedido, usuario_solicitante, categoria_requerida, coordenada_destino, peso_carga_kg=0.0):
        pass

    def actualizar_estado(self, nuevo_estado):
        pass

    def vincular_dron(self, dron):
        pass

    def __repr__(self):
        pass
