# Módulo orquestador del centro de control de operaciones
# Responsable: Valery Arboleda Ardila

from datetime import datetime
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota.dron import Dron
from src.control.log_operacion import LogOperacion
from src.servicios.geocodificador import (
    IServicioGeocodificador,
    ServicioGeocodificadorOSM,
)
from src.excepciones.errores import GeocodificacionError, CoordenadaInvalidaError



class SistemaCentroControl:
    def __init__(
        self,
        lat_base: float = 6.2089,
        lon_base: float = -75.5684,
        geocodificador: IServicioGeocodificador | None = None
    ) -> None:
        self.flota_drones: list[Dron] = []
        self.usuarios_registrados: list[Usuario] = []
        self.pedidos: list[Pedido] = []
        self.historial_logs: list[LogOperacion] = []
        self.coordenadas_base: tuple[float, float] = (float(lat_base), float(lon_base))
        self.geocodificador: IServicioGeocodificador = (
            geocodificador if geocodificador is not None else ServicioGeocodificadorOSM()
        )

    def agregar_dron(self, dron: Dron) -> Dron:
        if not isinstance(dron, Dron):
            raise TypeError("El parámetro debe ser un objeto válido de la clase Dron.")

        for d in self.flota_drones:
            if d.id_dron == dron.id_dron:
                raise ValueError(f"El dron con ID '{dron.id_dron}' ya está registrado en la flota.")

        self.flota_drones.append(dron)
        categoria_dron = getattr(dron, "categoria", getattr(dron, "modelo_aeronave", "ESTANDAR"))
        print(f"Dron '{dron.id_dron}' ({dron.modelo_aeronave} - {categoria_dron}) agregado a la flota exitosamente.")
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

        # Si el pedido no cuenta con coordenadas pero tiene una dirección textual,
        # se delega la resolución geográfica al servicio inyectado (OSM o Catálogo Local)
        if pedido.coordenada_destino is None and pedido.direccion_destino:
            try:
                pedido.coordenada_destino = self.geocodificador.geocodificar_direccion(pedido.direccion_destino)
                self.generar_log(
                    evento="GEOCODIFICACION_EXITOSA",
                    id_pedido=pedido.id_pedido,
                    detalles=f"Direccion '{pedido.direccion_destino}' resuelta exitosamente a {pedido.coordenada_destino}."
                )
            except (GeocodificacionError, CoordenadaInvalidaError) as e:
                self.generar_log(
                    evento="PEDIDO_RECHAZADO_DIRECCION_INVALIDA",
                    id_pedido=pedido.id_pedido,
                    detalles=f"Fallo en geocodificacion para direccion '{pedido.direccion_destino}': {e}"
                )
                print(f"[RECHAZADO] No se pudo geocodificar la direccion del pedido '{pedido.id_pedido}': {e}")
                raise e

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
        """
        Cruza información para buscar el primer dron disponible compatible
        con la categoría solicitada por el pedido y realiza la asignación (RF-08).
        """
        if not isinstance(id_pedido, str) or not id_pedido.strip():
            print("El ID del pedido debe ser una cadena de texto no vacía.")
            return False

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
            categoria_dron = getattr(dron, "categoria", getattr(dron, "modelo_aeronave", None))
            if categoria_dron == pedido_encontrado.categoria_requerida:
                pedido_encontrado.vincular_dron(dron)
                pedido_encontrado.actualizar_estado('ASIGNADO')

                dron.disponible = False
                dron.en_mision = True

                self.generar_log(
                    evento="ASIGNACION_DRON",
                    id_dron=dron.id_dron,
                    id_pedido=pedido_encontrado.id_pedido,
                    detalles=f"Asignacion exitosa! Dron {dron.id_dron} ({categoria_dron}) enlazado al pedido {pedido_encontrado.id_pedido}."
                )

                print(f"El dron {dron.id_dron} ha sido asignado al pedido {pedido_encontrado.id_pedido} exitosamente.")
                return True

        print(f"No hay drones disponibles de la categoría '{pedido_encontrado.categoria_requerida}' en este momento.")
        return False

    def gestionar_retorno_a_base(self, id_dron: str) -> bool:
        """
        Ordena el regreso obligatorio de una aeronave a la base central de la empresa (RF-09).
        """
        if not isinstance(id_dron, str) or not id_dron.strip():
            print("El ID del dron debe ser una cadena de texto no vacía.")
            return False

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

    def refrescar_datos_flota(self) -> int:
        drones_actualizados = len(self.flota_drones)
        self.generar_log(
            evento="REFRESCO_TELEMETRIA",
            detalles=f"Telemetria y estado de {drones_actualizados} aeronave(s) de la flota actualizados bajo demanda."
        )
        print(f"Telemetría y estado de {drones_actualizados} aeronave(s) en la flota actualizados con éxito.")
        return drones_actualizados

    def __str__(self) -> str:
        linea = "=" * 55
        return (
            f"\n{linea}\n"
            f" TORRE DE CONTROL SKYROUTE - CENTRO DE OPERACIONES\n"
            f" Base Central: {self.coordenadas_base}\n"
            f" Flota Activa: {len(self.flota_drones)} aeronaves\n"
            f" Drones Disponibles: {len(self.obtener_drones_disponibles())}\n"
            f" Usuarios Registrados: {len(self.usuarios_registrados)}\n"
            f" Pedidos Gestionados: {len(self.pedidos)}\n"
            f" Registros de Auditoría: {len(self.historial_logs)}\n"
            f"{linea}\n"
        )

    def __repr__(self) -> str:
        return (
            f"SistemaCentroControl(flota={len(self.flota_drones)}, "
            f"usuarios={len(self.usuarios_registrados)}, pedidos={len(self.pedidos)}, "
            f"base={self.coordenadas_base})"
        )


