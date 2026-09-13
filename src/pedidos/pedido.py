# Módulo de gestión de pedidos y solicitudes de servicio
# Responsable: Valery Arboleda Ardila

from src.usuarios.usuario import Usuario
from src.flota.dron import Dron


class Pedido:
    categorias_permitidas: list[str] = [
        'ENTREGA_LIGERA',
        'CARGA_PESADA',
        'VIGILANCIA',
        'MAPEO_TOPOGRAFICO',
        'INSPECCION_INFRAESTRUCTURA',
        'BUSQUEDA_RESCATE'
    ]
    estados_permitidos: list[str] = [
        'PENDIENTE',
        'ASIGNADO',
        'EN_TRANSITO',
        'COMPLETADO',
        'CANCELADO'
    ]

    def __init__(
        self,
        id_pedido: str,
        usuario_solicitante: Usuario,
        categoria_requerida: str,
        coordenada_destino: tuple[float, float],
        peso_carga_kg: float = 0.0
    ) -> None:
        # ID DEL PEDIDO
        if not isinstance(id_pedido, str):
            raise TypeError("El ID del pedido debe ser una cadena de texto. Por favor, intenta de nuevo")

        if not id_pedido.strip():
            raise ValueError("El ID del pedido no puede estar vacío. Por favor, intenta de nuevo.")
        self.id_pedido = id_pedido.strip()

        # USUARIO SOLICITANTE
        if not isinstance(usuario_solicitante, Usuario):
            raise TypeError("El usuario solicitante debe ser un objeto válido de la clase Usuario! Por favor, intenta de nuevo")
        self.usuario_solicitante = usuario_solicitante

        # CATEGORIA
        if not isinstance(categoria_requerida, str):
            raise TypeError("La categoria requerida debe ser una cadena de texto. Por favor, intenta de nuevo")
        categoria_limpia = categoria_requerida.strip().upper()

        if categoria_limpia not in self.categorias_permitidas:
            raise ValueError("La categoría no es válida. Por favor, intenta de nuevo.")
        self.categoria_requerida = categoria_limpia

        # COORDENADA DEL DESTINO
        if not isinstance(coordenada_destino, tuple):
            raise TypeError("Las coordenadas del destino deben ser una tupla. Por favor, intenta de nuevo")
        if not coordenada_destino:
            raise ValueError("Las coordenadas no pueden estar vacías. Por favor, intenta de nuevo.")
        if len(coordenada_destino) != 2:
            raise ValueError("Las coordenadas deben contener exactamente dos valores: (latitud, longitud).")
        self.coordenada_destino = coordenada_destino

        # PESO_CARGA
        if isinstance(peso_carga_kg, bool) or not isinstance(peso_carga_kg, (int, float)):
            raise TypeError("El peso de la carga debe ser un número. Por favor, intenta de nuevo")
        if peso_carga_kg < 0:
            raise ValueError("El peso no puede ser menor a 0,0. Por favor intenta de nuevo.")
        self.peso_carga_kg = float(peso_carga_kg)

        # ESTADO Y DRON ASIGNADO
        self.estado = 'PENDIENTE'
        self.dron_asignado = None

    def actualizar_estado(self, nuevo_estado: str) -> None:
        if not isinstance(nuevo_estado, str):
            raise TypeError("El nuevo estado debe ser una cadena de texto. Por favor, intenta de nuevo")

        estado_limpio = nuevo_estado.strip().upper()

        if estado_limpio not in self.estados_permitidos:
            raise ValueError("El estado no es válido. Por favor, intenta de nuevo.")
        self.estado = estado_limpio

    def vincular_dron(self, dron: Dron) -> None:
        if not isinstance(dron, Dron):
            raise TypeError("El dron a vincular debe ser un objeto de la clase 'Dron', Por favor, intenta de nuevo.")
        self.dron_asignado = dron

    def __str__(self) -> str:
        dron_info = self.dron_asignado.id_dron if self.dron_asignado else "Sin asignar"
        return (
            f"Pedido [{self.id_pedido}] - Cat: {self.categoria_requerida} - "
            f"Estado: {self.estado} - Dron: {dron_info} - Destino: {self.coordenada_destino}"
        )

    def __repr__(self) -> str:
        dron_id = f"'{self.dron_asignado.id_dron}'" if self.dron_asignado else "None"
        return (
            f"Pedido(id_pedido='{self.id_pedido}', usuario_solicitante='{self.usuario_solicitante.id_usuario}', "
            f"categoria_requerida='{self.categoria_requerida}', estado='{self.estado}', dron_asignado={dron_id})"
        )

