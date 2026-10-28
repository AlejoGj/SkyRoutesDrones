# Módulo orquestador del centro de control de operaciones
# Responsable: Valery Arboleda Ardila (Sprint 2 - HU-12)

from datetime import datetime
from typing import Any
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota.dron import Dron
from src.control.log_operacion import LogOperacion
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo
from src.servicios.clima import ServicioClimaAburra
from src.servicios.geocodificador import (
    IServicioGeocodificador,
    ServicioGeocodificadorArcGIS,
    ServicioGeocodificadorGoogle,
    ServicioGeocodificadorOSM,
)
from src.excepciones.errores import GeocodificacionError, CoordenadaInvalidaError

# Subclases especializadas de la flota (Sprint 2)
from src.flota.dron_inspeccion import DronInspeccion
from src.flota.dron_rescate import DronRescate

# Intentos de importación tolerantes a fallos para subclases en desarrollo por compañeros (HU-08 y HU-09)
try:
    from src.flota.dron_vigilancia import DronVigilancia
except ImportError:
    DronVigilancia = None

try:
    from src.flota.dron_mapeo import DronMapeo
except ImportError:
    DronMapeo = None

try:
    from src.flota.dron_entrega_ligera import DronEntregaLigera
except ImportError:
    DronEntregaLigera = None

try:
    from src.flota.dron_carga_pesada import DronCargaPesada
except ImportError:
    DronCargaPesada = None


# Catálogo / Registro de fábrica para instanciar y validar subclases a partir de una categoría (HU-12)
FABRICA_DRONES: dict[str, type[Dron]] = {
    'INSPECCION_INFRAESTRUCTURA': DronInspeccion,
    'BUSQUEDA_RESCATE': DronRescate,
}

if DronVigilancia is not None:
    FABRICA_DRONES['VIGILANCIA'] = DronVigilancia
if DronMapeo is not None:
    FABRICA_DRONES['MAPEO_TOPOGRAFICO'] = DronMapeo
if DronEntregaLigera is not None:
    FABRICA_DRONES['ENTREGA_LIGERA'] = DronEntregaLigera
if DronCargaPesada is not None:
    FABRICA_DRONES['CARGA_PESADA'] = DronCargaPesada


def registrar_subclase_en_fabrica(categoria: str, clase_dron: type[Dron]) -> None:
    """
    Permite registrar o extender dinámicamente el catálogo de la fábrica de drones (HU-12).
    """
    if not isinstance(categoria, str) or not categoria.strip():
        raise ValueError("La categoría debe ser una cadena de texto no vacía.")
    if not isinstance(clase_dron, type) or not issubclass(clase_dron, Dron):
        raise TypeError("El parámetro debe ser una subclase válida de Dron.")
    FABRICA_DRONES[categoria.strip()] = clase_dron


def instanciar_dron_desde_fabrica(categoria: str, *args, **kwargs) -> Dron:
    """
    Instancia una subclase de dron a partir de la categoría registrada en FABRICA_DRONES (RF-08, Sprint 2).
    """
    if categoria not in FABRICA_DRONES:
        raise ValueError(f"Categoría '{categoria}' no registrada en FABRICA_DRONES.")
    clase_dron = FABRICA_DRONES[categoria]
    return clase_dron(*args, **kwargs)



class ResumenRefrescoFlota(dict):
    """
    Estructura de datos para el resultado de refrescar_datos_flota().
    Hereda de dict para proporcionar acceso completo a:
    - 'delta_segundos': float (tiempo transcurrido en el pulso)
    - 'clima': dict (condiciones meteorológicas vigentes y factor de velocidad)
    - 'reportes_aeronaves': list[dict] (reportes cinemáticos de drones procesados)
    - 'total_aeronaves': int (total de aeronaves registradas en la flota)
    - 'drones_activos': int (aeronaves con avance en vuelo o retorno)

    Implementa __int__ y __index__ para garantizar compatibilidad retroactiva
    con cualquier código o test que espere un entero con el número de aeronaves.
    """
    def __int__(self) -> int:
        return int(self.get("total_aeronaves", len(self.get("reportes_aeronaves", []))))

    def __index__(self) -> int:
        return self.__int__()


class SistemaCentroControl:
    LAT_BASE: float = 6.219603
    LON_BASE: float = -75.586792
    COORDENADAS_BASE: tuple[float, float] = (LAT_BASE, LON_BASE)

    def __init__(
        self,
        geocodificador: IServicioGeocodificador | None = None,
        reloj: RelojSimulacion | None = None,
        servicio_clima: ServicioClimaAburra | None = None,
        simulador: SimuladorVuelo | None = None,
    ) -> None:
        self.flota_drones: list[Dron] = []
        self.usuarios_registrados: list[Usuario] = []
        self.pedidos: list[Pedido] = []
        self.historial_logs: list[LogOperacion] = []
        self.coordenadas_base: tuple[float, float] = self.COORDENADAS_BASE
        self.geocodificador: IServicioGeocodificador = (
            geocodificador if geocodificador is not None else ServicioGeocodificadorArcGIS()
        )
        self.reloj: RelojSimulacion = reloj if reloj is not None else RelojSimulacion()
        self.servicio_clima: ServicioClimaAburra = (
            servicio_clima if servicio_clima is not None else ServicioClimaAburra()
        )
        self.simulador: SimuladorVuelo = (
            simulador if simulador is not None else SimuladorVuelo(centro_control=self)
        )
        self._cache_clima: dict[str, Any] | None = None
        self._nodo_cache_clima: str = ""
        self._ts_cache_clima: float = 0.0

    def _obtener_clima_con_cache(
        self,
        nombre_nodo: str = "Medellin_Centro",
        ttl_segundos: float = 60.0,
    ) -> dict[str, Any]:
        """
        Retorna las condiciones climáticas del nodo solicitado utilizando un caché
        en memoria para evitar latencias de red y consumo excesivo de la API pública.
        """
        import time
        ahora = time.time()
        if (
            self._cache_clima is not None
            and self._nodo_cache_clima == nombre_nodo
            and (ahora - self._ts_cache_clima) < ttl_segundos
        ):
            return self._cache_clima

        try:
            clima = self.servicio_clima.obtener_condiciones(nombre_nodo)
        except Exception:
            clima = {
                "nodo": nombre_nodo,
                "temperatura_c": 22.0,
                "lluvia_mm": 0.0,
                "viento_kmh": 12.0,
                "factor_velocidad": 1.0,
                "vuelo_seguro": True,
                "fallback": True,
            }

        self._cache_clima = clima
        self._nodo_cache_clima = nombre_nodo
        self._ts_cache_clima = ahora
        return clima

    def agregar_dron(self, dron: Dron) -> Dron:
        if not isinstance(dron, Dron):
            raise TypeError("El parámetro debe ser un objeto válido de la clase Dron.")

        for d in self.flota_drones:
            if d.id_dron == dron.id_dron:
                raise ValueError(f"El dron con ID '{dron.id_dron}' ya está registrado en la flota.")


        if not dron.disponible or dron.en_mision:
            raise ValueError(f"El dron '{dron.id_dron}' debe estar completamente libre (disponible y no en misión) para ingresar a la flota activa.")

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
        Ahora asigna el dron evaluando la compatibilidad dinámicamente usando FABRICA_DRONES.
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

        # Ahora aqui buscamos la clase específica que requiere el pedido en nuestro diccionario de las constantes del principio
        clase_requerida = FABRICA_DRONES.get(pedido_encontrado.categoria_requerida)

        for dron in drones_desocupados:
            categoria_dron = getattr(dron, "categoria", getattr(dron, "modelo_aeronave", None))
            if categoria_dron == pedido_encontrado.categoria_requerida:
                # Validar autonomía completa para la operación (ida + retorno a base)
                if dron.telemetria is not None:
                    if dron.telemetria.bateria <= 0.0:
                        print(f"El dron {dron.id_dron} tiene batería 0.0% (agotada). Descartado para la misión.")
                        continue

                    distancia_ida = dron.calcular_distancia_a_destino(pedido_encontrado.coordenada_destino)
                    base = dron.coordenadas_base or self.coordenadas_base
                    distancia_retorno = dron.calculador.calcular_haversine(pedido_encontrado.coordenada_destino, base)
                    if distancia_retorno is None:
                        distancia_retorno = distancia_ida
                    distancia_total = distancia_ida + distancia_retorno
                    consumo_requerido = dron.calcular_consumo_estimado(distancia_total)

                    if dron.telemetria.bateria < consumo_requerido:
                        print(
                            f"El dron {dron.id_dron} tiene batería insuficiente ({dron.telemetria.bateria:.1f}% "
                            f"vs {consumo_requerido:.1f}% requeridos para ida y vuelta). Buscando otra aeronave..."
                        )
                        continue

                # Fijar base en dron si no la tenía
                if dron.coordenadas_base is None:
                    dron.coordenadas_base = self.coordenadas_base

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

        print(f"No hay drones disponibles de la categoría '{pedido_encontrado.categoria_requerida}' con batería suficiente en este momento.")
        return False

    def despachar_mision(self, id_pedido: str) -> bool:
        """
        Ciclo para el método despachar misión (HU-12):
        1. Localizar el pedido y validar estado ASIGNADO
        2. Iniciar el tránsito (EN_TRANSITO)
        3. Invocar al método ejecutar_mision de forma polimórfica
        4. Finalizar la misión (COMPLETADO)
        5. Generar log de auditoría con la información técnica devuelta
        6. Ordenar el retorno automático a la base
        """
        if not isinstance(id_pedido, str) or not id_pedido.strip():
            print("El ID del pedido debe ser una cadena de texto no vacía.")
            return False

        # 1. Aqui comenzamos localizando el pedido
        id_pedido_limpio = id_pedido.strip()
        pedido_encontrado = None
        for p in self.pedidos:
            if p.id_pedido == id_pedido_limpio:
                pedido_encontrado = p
                break

        # Validaciones defensivas
        if not pedido_encontrado:
            print(f"No se encontró ningún pedido con ID '{id_pedido}'!")
            return False

        if pedido_encontrado.estado != "ASIGNADO":
            print(f"El pedido con ID '{id_pedido}' no está en estado 'ASIGNADO' (Estado actual: {pedido_encontrado.estado}).")
            return False

        dron_ejecutor = pedido_encontrado.dron_asignado
        if not dron_ejecutor:
            print(f"El pedido con ID '{id_pedido}' no tiene un dron asignado.")
            return False

        # 2. Actualizamos el estado ya que aqui inicia el tránsito
        pedido_encontrado.actualizar_estado('EN_TRANSITO')
        print(f"Misión {id_pedido_limpio} iniciada. Dron {dron_ejecutor.id_dron} en tránsito.")

        # 3. Invocación polimórfica
        try:
            # Habilitar disponibilidad de despegue para el dron reservado para este pedido
            dron_ejecutor.disponible = True

            # Si la aeronave no cuenta aún con telemetría en base, inicializar telemetría nominal de despegue
            if getattr(dron_ejecutor, 'telemetria', None) is None:
                from src.telemetria.telemetria import TelemetriaDrone
                dron_ejecutor.asignar_telemetria(
                    TelemetriaDrone(
                        id_dron=dron_ejecutor.id_dron,
                        bateria=100.0,
                        altitud=0.0,
                        estado_motores='APAGADOS',
                        coordenadas=self.coordenadas_base
                    )
                )

            resultado_mision = dron_ejecutor.ejecutar_mision(pedido_encontrado)

            # 4. Finaliza misión
            pedido_encontrado.actualizar_estado('COMPLETADO')

            # 5. Genera el Log pero ahora con la info devuelta
            self.generar_log(
                evento="MISION_COMPLETADA",
                id_dron=dron_ejecutor.id_dron,
                id_pedido=id_pedido_limpio,
                detalles=f"Resultado técnico: {resultado_mision}"
            )
            print(f"Misión {id_pedido_limpio} completada con éxito.")

            # 6. Apenas termina la misión hacemos que vuelva a la base
            self.gestionar_retorno_a_base(dron_ejecutor.id_dron)
            return True

        except Exception as e:
            print(f"Error crítico durante la ejecución polimórfica de la misión: {e}")
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

    def refrescar_datos_flota(
        self,
        nombre_nodo: str = "Medellin_Centro",
        delta_t: float | None = None,
        factor_clima: float | None = None,
    ) -> ResumenRefrescoFlota:
        """
        Hook ejecutado al pulsar el botón de actualización o en el ciclo de simulación temporal.
        Calcula el delta de tiempo transcurrido (mediante RelojSimulacion o provisto),
        obtiene el factor climático del Valle de Aburrá (vía ServicioClimaAburra con caché),
        y avanza la cinemática, posición y descarga polimórfica de batería de toda la flota
        activa (en misión o retornando a base) mediante el SimuladorVuelo desacoplado.
        """
        if delta_t is None:
            delta_segundos = self.reloj.obtener_delta()
        else:
            delta_segundos = max(0.0, float(delta_t))

        if factor_clima is not None:
            clima = {
                "nodo": nombre_nodo,
                "temperatura_c": 22.0,
                "lluvia_mm": 0.0,
                "viento_kmh": 12.0,
                "factor_velocidad": float(factor_clima),
                "vuelo_seguro": True,
            }
            factor_velocidad = float(factor_clima)
        else:
            clima = self._obtener_clima_con_cache(nombre_nodo)
            factor_velocidad = float(clima.get("factor_velocidad", 1.0))

        reportes: list[dict[str, Any]] = []
        drones_activos = 0

        for dron in self.flota_drones:
            esta_activo = bool(
                (dron.en_mision and getattr(dron, "pedido_activo", None) is not None)
                or dron.retornando_a_base
            )
            if not esta_activo:
                continue

            drones_activos += 1
            objetivo = None
            if dron.retornando_a_base:
                objetivo = dron.coordenadas_base or self.coordenadas_base
            elif dron.en_mision:
                if dron.pedido_activo is not None:
                    objetivo = dron.pedido_activo.coordenada_destino
                else:
                    for ped in self.pedidos:
                        if ped.dron_asignado and ped.dron_asignado.id_dron == dron.id_dron:
                            objetivo = ped.coordenada_destino
                            break

            reporte_dron = self.simulador.avanzar_paso_tiempo(
                dron=dron,
                delta_t=delta_segundos,
                factor_clima=factor_velocidad,
                coordenada_objetivo=objetivo,
            )
            reportes.append(reporte_dron)

        total_flota = len(self.flota_drones)
        texto_detalles = (
            f"Paso de tiempo: {delta_segundos:.2f}s | Clima {clima.get('nodo', nombre_nodo)}: "
            f"{clima.get('temperatura_c', 22.0)}°C, Viento: {clima.get('viento_kmh', 0.0)}km/h | "
            f"Flota: {total_flota} aeronave(s) (Activas en vuelo: {drones_activos})"
        )
        self.generar_log(evento="REFRESCO_TELEMETRIA", detalles=texto_detalles)

        return ResumenRefrescoFlota({
            "delta_segundos": delta_segundos,
            "clima": clima,
            "reportes_aeronaves": reportes,
            "total_aeronaves": total_flota,
            "drones_activos": drones_activos,
        })

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
