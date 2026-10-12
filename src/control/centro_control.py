# Módulo orquestador del centro de control de operaciones
# Responsable: Valery Arboleda Ardila

from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota.dron import Dron
from src.control.log_operacion import LogOperacion


class SistemaCentroControl:
    def __init__(self, lat_base: float = 6.2089, lon_base: float = -75.5684) -> None:
        self.flota_drones: list[Dron] = []
        self.usuarios_registrados: list[Usuario] = []
        self.pedidos: list[Pedido] = []
        self.historial_logs: list[LogOperacion] = []
        self.coordenadas_base: tuple[float, float] = (float(lat_base), float(lon_base))

    def agregar_dron(self, dron: Dron) -> Dron:
        if not isinstance(dron, Dron):
            raise TypeError("El parámetro debe ser un objeto válido de la clase Dron.")

        for d in self.flota_drones:
            if d.id_dron == dron.id_dron:
                raise ValueError(f"El dron con ID '{dron.id_dron}' ya está registrado en la flota.")

        self.flota_drones.append(dron)
        print(f"Dron '{dron.id_dron}' ({dron.modelo_aeronave} - {dron.categoria}) agregado a la flota exitosamente.")
        return dron


    def registrar_usuario(self, usuario: Usuario) -> Usuario:
        if not isinstance(usuario, Usuario):
            raise TypeError("El parámetro debe ser un objeto válido de la clase Usuario.")

        for u in self.usuarios_registrados:
            if u.id_usuario == usuario.id_usuario:
                raise ValueError(f"El usuario con ID '{usuario.id_usuario}' ya está registrado.")

        self.usuarios_registrados.append(usuario)
        print(f"Usuario '{usuario.nombre}' (Rol: {usuario.rol}) registrado exitosamente.")
        return usuario

    def registrar_pedido(self, pedido: Pedido) -> Pedido:
        if not isinstance(pedido, Pedido):
            raise TypeError("El parámetro debe ser un objeto válido de la clase Pedido!")

        for p in self.pedidos:
            if p.id_pedido == pedido.id_pedido:
                raise ValueError(f"El pedido con ID '{pedido.id_pedido}' ya está registrado!")

        self.pedidos.append(pedido)
        print(f"Pedido '{pedido.id_pedido}' (Categoría: {pedido.categoria_requerida}) registrado exitosamente.")
        return pedido


    def asignar_dron_a_pedido(self, id_pedido):
        pass

    def gestionar_retorno_a_base(self, id_dron):
        pass

    def generar_log(self, tipo_evento, id_dron=None, id_pedido=None, detalles=""):
        pass
