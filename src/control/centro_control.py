# Módulo orquestador del centro de control de operaciones
# Responsable: Valery Arboleda Ardila

from datetime import datetime
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


    def obtener_drones_disponibles(self) -> list[Dron]:
        drones_desocupados = []
        for dron in self.flota_drones:
            if dron.disponible:
                drones_desocupados.append(dron)
        return drones_desocupados

    def asignar_dron_a_pedido(self, id_pedido: str) -> bool:
        pedido_encontrado = None
        for p in self.pedidos:
            if p.id_pedido == id_pedido.strip():
                pedido_encontrado = p
                break

        if not pedido_encontrado:
            print(f"No se encontró ningún pedido con ID '{id_pedido}'!")
            return False

        if pedido_encontrado.estado != "PENDIENTE":
            print(f"El pedido con ID '{id_pedido}' no está en estado 'PENDIENTE'!")
            return False

        drones_desocupados = self.obtener_drones_disponibles()

        for dron in drones_desocupados:
            if dron.categoria == pedido_encontrado.categoria_requerida:
                pedido_encontrado.vincular_dron(dron)
                pedido_encontrado.actualizar_estado('ASIGNADO')

                dron.disponible = False
                dron.en_mision = True

                self.generar_log(
                    evento="ASIGNACION_DRON",
                    id_dron=dron.id_dron,
                    id_pedido=pedido_encontrado.id_pedido,
                    detalles=f"Asignacion exitosa! Dron {dron.id_dron} ({dron.categoria}) enlazado al pedido {pedido_encontrado.id_pedido}."
                )

                print(f"El dron {dron.id_dron} ha sido asignado al pedido {pedido_encontrado.id_pedido} exitosamente.")
                return True

        print(f"No hay drones disponibles de la categoría '{pedido_encontrado.categoria_requerida}' en este momento.")
        return False

    def gestionar_retorno_a_base(self, id_dron: str) -> bool:
        dron_encontrado = None
        for dron in self.flota_drones:
            if dron.id_dron == id_dron.strip():
                dron_encontrado = dron
                break

        if not dron_encontrado:
            print(f"No se encontró ningún dron con ID '{id_dron}'!")
            return False

        if not dron_encontrado.en_mision:
            print(f"El dron con ID '{id_dron}' no está actualmente en misión entonces no se puede retornar a la base!")
            return False

        try:
            dron_encontrado.iniciar_retorno_base(self.coordenadas_base)
            print(f"Dron {id_dron} ha iniciado el retorno a la base con éxito!")

            self.generar_log(
                evento="RETORNO_A_BASE",
                id_dron=id_dron,
                id_pedido="N/A",
                detalles=f"Dron {id_dron} en transito de retorno hacia coordenadas base {self.coordenadas_base}."
            )
            return True

        except Exception as e:
            print(f"Error al iniciar el retorno a la base para el dron {id_dron}: {e}")
            return False


    def generar_log(self, evento: str, id_dron: str = None, id_pedido: str = None, detalles: str = "", tipo_evento: str = None) -> LogOperacion:
        tipo = evento or tipo_evento or "EVENTO_GENERAL"
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_log_generado = f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.historial_logs) + 1}"
        texto_detalles = detalles if detalles else f"Registro de sistema: {tipo} procesado."

        nuevo_log = LogOperacion(
            id_log=id_log_generado,
            fecha_hora=fecha_actual,
            tipo_evento=tipo,
            id_dron=id_dron,
            id_pedido=id_pedido,
            detalles=texto_detalles
        )

        self.historial_logs.append(nuevo_log)
        return nuevo_log

