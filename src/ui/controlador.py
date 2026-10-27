# Controlador de interfaz (Puente MVC / Adaptador hacia el Backend POO)
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.control.centro_control import SistemaCentroControl
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo
from src.excepciones.errores import (
    ActualizarEstadoDronError,
    AltitudInvalidaError,
    AsignarTelemetriaError,
    BateriaInvalidaError,
    CategoriaDronInvalidoError,
    CoordenadaInvalidaError,
    DestinoInvalidoError,
    DronError,
    EstadoDronDuplicadoError,
    EstadoMotorInvalidoError,
    GeocodificacionError,
    TelemetriaNoAsignadaError,
)
from src.flota import (
    Dron,
    DronCargaPesada,
    DronEntregaLigera,
    DronInspeccion,
    DronMapeo,
    DronRescate,
    DronVigilancia,
)
from src.geodesia.calculador import CalculadorGeodesico
from src.pedidos.pedido import Pedido
from src.servicios.clima import ServicioClimaAburra
from src.telemetria.telemetria import TelemetriaDrone
from src.usuarios.usuario import Usuario


class ControladorSkyRoute:
    """
    Adaptador / Controlador de presentación que comunica el servidor HTTP nativo
    con el modelo de dominio POO (SistemaCentroControl, Dron, Pedido, SimuladorVuelo)
    sin modificar ninguna clase del backend.
    """

    DESTINOS_REFERENCIA: list[dict[str, Any]] = [
        {"nombre": "Hosp. San Vicente Fundación", "lat": 6.2620, "lon": -75.5780, "zona": "Medellín Centro-Norte"},
        {"nombre": "Universidad de Medellín", "lat": 6.2319, "lon": -75.6105, "zona": "Belén Los Alpes"},
        {"nombre": "Parque El Poblado", "lat": 6.2089, "lon": -75.5684, "zona": "El Poblado"},
        {"nombre": "Parque Berrío", "lat": 6.2498, "lon": -75.5694, "zona": "La Candelaria"},
        {"nombre": "Aeropuerto Olaya Herrera", "lat": 6.2200, "lon": -75.5900, "zona": "Guayabal"},
        {"nombre": "Centro Comercial Santafé", "lat": 6.1973, "lon": -75.5742, "zona": "El Poblado"},
        {"nombre": "Parque Principal de Envigado", "lat": 6.1759, "lon": -75.5917, "zona": "Envigado"},
        {"nombre": "Parque Principal de Bello", "lat": 6.3373, "lon": -75.5579, "zona": "Bello"},
        {"nombre": "Parque de Sabaneta", "lat": 6.1515, "lon": -75.6166, "zona": "Sabaneta"},
    ]

    ETIQUETAS_CATEGORIA: dict[str, str] = {
        "ENTREGA_LIGERA": "Entrega Ligera",
        "CARGA_PESADA": "Carga Pesada",
        "VIGILANCIA": "Vigilancia",
        "MAPEO_TOPOGRAFICO": "Mapeo Topográfico",
        "INSPECCION_INFRAESTRUCTURA": "Inspección Infraest.",
        "BUSQUEDA_RESCATE": "Búsqueda y Rescate",
    }

    def __init__(self) -> None:
        # Coordenadas de la Base Central SkyRoute en Medellín (Valle de Aburrá)
        self.calculador = CalculadorGeodesico()
        self.centro = SistemaCentroControl(lat_base=6.2089, lon_base=-75.5684)
        self.reloj = RelojSimulacion()
        self.simulador = SimuladorVuelo(calculador=self.calculador)
        self.servicio_clima = ServicioClimaAburra()

        # Metadatos auxiliares exclusivos de presentación (progreso visual de trayectos)
        self._rutas_visuales: dict[str, dict[str, Any]] = {}
        self._usuario_activo_id: str = "USR-OPE-01"
        self._ultima_sincronizacion: str = datetime.now().strftime("%H:%M:%S")
        self._clima_cache: dict[str, Any] = {
            "nodo": "Medellin_Centro",
            "temperatura_c": 22.4,
            "lluvia_mm": 0.0,
            "viento_kmh": 11.5,
            "factor_velocidad": 1.0,
            "vuelo_seguro": True,
        }

        self._inicializar_escenario_operativo()

    def _inicializar_escenario_operativo(self) -> None:
        """Instancia usuarios, las 6 subclases de drones y un pedido inicial de demostración."""
        usuarios_iniciales = [
            Usuario(id_usuario="USR-OPE-01", nombre="Alejandro García", rol="OPERADOR_VUELO"),
            Usuario(id_usuario="USR-ADM-02", nombre="Juan Manuel Pava", rol="ADMINISTRADOR"),
            Usuario(id_usuario="USR-CLI-03", nombre="Valery Arboleda", rol="CLIENTE"),
        ]
        for usuario in usuarios_iniciales:
            self.centro.registrar_usuario(usuario)

        base = self.centro.coordenadas_base

        # Instanciación polimórfica de las 6 subclases especializadas del Sprint 2
        flota_inicial: list[tuple[Dron, float]] = [
            (
                DronEntregaLigera(
                    id_dron="DR-01",
                    modelo_aeronave="SkyCart-Med L1",
                    velocidad_promedio_kmh=60.0,
                    capacidad_carga_kg=8.0,
                    compartimento_refrigerado=True,
                    mecanismo_suelta_rapida=True,
                ),
                96.0,
            ),
            (
                DronRescate(
                    id_dron="DR-02",
                    modelo_aeronave="SkyRoutes-Hexa",
                    velocidad_promedio_kmh=65.0,
                    camara_termica=True,
                    kit_auxilios_equipado=True,
                    potencia_altavoz_db=115,
                ),
                92.0,
            ),
            (
                DronCargaPesada(
                    id_dron="DR-03",
                    modelo_aeronave="HeavyLifter-X8",
                    velocidad_promedio_kmh=48.0,
                    volumen_carga_m3=3.2,
                    numero_rotores=8,
                    potencia_remolque_w=5200.0,
                ),
                98.0,
            ),
            (
                DronVigilancia(
                    id_dron="DR-04",
                    modelo_aeronave="Sentinel-300 RTK",
                    velocidad_promedio_kmh=62.0,
                    resolucion_camara_mp=48,
                    vision_nocturna=True,
                    frecuencia_transmision_ghz=5.8,
                ),
                90.0,
            ),
            (
                DronMapeo(
                    id_dron="DR-05",
                    modelo_aeronave="TerraScan-LiDAR",
                    velocidad_promedio_kmh=46.0,
                    tiene_sensor_lidar=True,
                    precision_gps_cm=1.8,
                    capacidad_almacenamiento_tb=4.0,
                ),
                94.0,
            ),
            (
                DronInspeccion(
                    id_dron="DR-06",
                    modelo_aeronave="InfraZoom-U50",
                    velocidad_promedio_kmh=52.0,
                    zoom_optico_x=30,
                    rango_sensor_ultrasonico_m=6.5,
                ),
                89.0,
            ),
        ]

        for dron, bateria_inicial in flota_inicial:
            telemetria = TelemetriaDrone(
                id_dron=dron.id_dron,
                bateria=bateria_inicial,
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=base,
            )
            dron.asignar_telemetria(telemetria)
            dron.coordenadas_base = base
            self.centro.agregar_dron(dron)

        # Pedido inicial alineado con el prototipo de documentación
        pedido_demo = Pedido(
            id_pedido="PED-4029",
            usuario_solicitante=usuarios_iniciales[2],
            categoria_requerida="BUSQUEDA_RESCATE",
            coordenada_destino=(6.2620, -75.5780),
            peso_carga_kg=2.4,
            direccion_destino="Hosp. San Vicente Fundación",
        )
        self.centro.registrar_pedido(pedido_demo)
        self.centro.generar_log(
            evento="SISTEMA_INICIADO",
            detalles="Torre de Control SkyRoute inicializada con 6 subclases polimórficas activas.",
        )
        self.reloj.reiniciar()

    # ==========================================================================
    # SERIALIZACIÓN DE ENTIDADES DE DOMINIO
    # ==========================================================================

    def _buscar_dron(self, id_dron: str) -> Dron:
        id_limpio = str(id_dron or "").strip()
        for dron in self.centro.flota_drones:
            if dron.id_dron == id_limpio:
                return dron
        raise ValueError(f"No existe una aeronave registrada con ID '{id_limpio}'.")

    def _buscar_pedido(self, id_pedido: str) -> Pedido:
        id_limpio = str(id_pedido or "").strip()
        for pedido in self.centro.pedidos:
            if pedido.id_pedido == id_limpio:
                return pedido
        raise ValueError(f"No existe un pedido registrado con ID '{id_limpio}'.")

    def _buscar_usuario(self, id_usuario: str) -> Usuario:
        id_limpio = str(id_usuario or "").strip()
        for usuario in self.centro.usuarios_registrados:
            if usuario.id_usuario == id_limpio:
                return usuario
        return self.centro.usuarios_registrados[0]

    def _extraer_atributos_especializados(self, dron: Dron) -> list[dict[str, str]]:
        """Obtiene de forma limpia las especificaciones técnicas propias de cada subclase."""
        specs: list[dict[str, str]] = []
        if isinstance(dron, DronEntregaLigera):
            specs = [
                {"etiqueta": "Capacidad Máx.", "valor": f"{dron.capacidad_carga_kg:.1f} kg"},
                {"etiqueta": "Refrigeración", "valor": "Activa" if dron.compartimento_refrigerado else "Estándar"},
                {"etiqueta": "Suelta Rápida", "valor": "Equipada" if dron.mecanismo_suelta_rapida else "Manual"},
            ]
        elif isinstance(dron, DronCargaPesada):
            specs = [
                {"etiqueta": "Volumen Tolva", "valor": f"{dron.volumen_carga_m3:.1f} m³"},
                {"etiqueta": "Tren Motriz", "valor": f"{dron.numero_rotores} rotores"},
                {"etiqueta": "Remolque", "valor": f"{dron.potencia_remolque_w:.0f} W"},
            ]
        elif isinstance(dron, DronVigilancia):
            specs = [
                {"etiqueta": "Cámara Óptica", "valor": f"{dron.resolucion_camara_mp} MP"},
                {"etiqueta": "Visión Nocturna", "valor": "Infrarroja" if dron.vision_nocturna else "Inactiva"},
                {"etiqueta": "Frecuencia Video", "valor": f"{dron.frecuencia_transmision_ghz} GHz"},
            ]
        elif isinstance(dron, DronMapeo):
            specs = [
                {"etiqueta": "Escáner LiDAR", "valor": "Equipado" if dron.tiene_sensor_lidar else "Fotogrametría"},
                {"etiqueta": "Precisión RTK", "valor": f"±{dron.precision_gps_cm} cm"},
                {"etiqueta": "Memoria SSD", "valor": f"{dron.capacidad_almacenamiento_tb:.1f} TB"},
            ]
        elif isinstance(dron, DronInspeccion):
            specs = [
                {"etiqueta": "Zoom Óptico", "valor": f"{dron.zoom_optico_x}x"},
                {"etiqueta": "Sensor Ultrasónico", "valor": f"{dron.rango_sensor_ultrasonico_m:.1f} m"},
                {"etiqueta": "Estabilización", "valor": "Estacionaria"},
            ]
        elif isinstance(dron, DronRescate):
            specs = [
                {"etiqueta": "Cámara Térmica", "valor": "FLIR Activa" if dron.camara_termica else "Inactiva"},
                {"etiqueta": "Kit Auxilios", "valor": "Equipado" if dron.kit_auxilios_equipado else "Sin kit"},
                {"etiqueta": "Altavoz SAR", "valor": f"{dron.potencia_altavoz_db} dB"},
            ]
        return specs

    def _serializar_dron(self, dron: Dron) -> dict[str, Any]:
        tele = dron.telemetria
        coords = list(tele.coordenadas) if tele else list(self.centro.coordenadas_base)
        bateria = round(tele.bateria, 1) if tele else 0.0
        altitud = round(tele.altitud, 1) if tele else 0.0
        motores = tele.estado_motores if tele else "SIN_TELEMETRIA"

        categoria = getattr(dron, "categoria", getattr(dron, "CATEGORIA_ESPECIALIZADA", "GENERAL"))
        ruta_meta = self._rutas_visuales.get(dron.id_dron, {})

        # Cálculos geodésicos y progreso de misión / retorno (RF-03, RF-09, RF-10)
        base = self.centro.coordenadas_base
        destino_objetivo = list(base)
        distancia_objetivo_km = 0.0
        eta_min = 0.0
        progreso_mision_pct = 0.0
        progreso_retorno_pct = 0.0
        distancia_a_base_km = round(self.calculador.calcular_haversine(tuple(coords), base), 3) if tele else 0.0

        if dron.en_mision and dron.pedido_activo is not None and dron.pedido_activo.coordenada_destino:
            dest_tuple = dron.pedido_activo.coordenada_destino
            destino_objetivo = list(dest_tuple)
            distancia_objetivo_km = round(dron.calcular_distancia_a_destino(dest_tuple), 2)
            eta_min = round(dron.estimar_tiempo_llegada_min(dest_tuple), 1)
            dist_total = ruta_meta.get("distancia_ida_total_km") or max(distancia_objetivo_km, 0.001)
            avance = max(0.0, dist_total - distancia_objetivo_km)
            progreso_mision_pct = round(min(100.0, (avance / dist_total) * 100.0), 1)
        elif dron.retornando_a_base:
            destino_objetivo = list(base)
            distancia_objetivo_km = round(distancia_a_base_km, 2)
            eta_min = round(dron.estimar_tiempo_llegada_min(base), 1)
            dist_ret_total = ruta_meta.get("distancia_retorno_total_km") or max(distancia_a_base_km, 0.001)
            if distancia_a_base_km <= 0.05:
                progreso_retorno_pct = 100.0
            else:
                avance_ret = max(0.0, dist_ret_total - distancia_a_base_km)
                progreso_retorno_pct = round(min(99.0, (avance_ret / dist_ret_total) * 100.0), 1)
            progreso_mision_pct = 100.0
        elif ruta_meta.get("ultimo_destino"):
            dest_prev = tuple(ruta_meta["ultimo_destino"])
            destino_objetivo = list(dest_prev)
            distancia_objetivo_km = round(self.calculador.calcular_haversine(tuple(coords), dest_prev), 2)
            eta_min = round(
                self.calculador.calcular_tiempo_vuelo_min(distancia_objetivo_km, dron.velocidad_promedio_kmh), 1
            )

        if dron.retornando_a_base:
            estado_operacional = "RETORNANDO_A_BASE"
        elif dron.en_mision and dron.pedido_activo is not None:
            estado_operacional = "EN_MISION"
        elif not dron.disponible:
            estado_operacional = "RESERVADO"
        else:
            estado_operacional = "DISPONIBLE"

        consumo_10km = round(dron.calcular_consumo_estimado(10.0), 2)

        return {
            "id_dron": dron.id_dron,
            "modelo_aeronave": dron.modelo_aeronave,
            "clase_python": type(dron).__name__,
            "categoria": categoria,
            "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(categoria, categoria),
            "velocidad_promedio_kmh": dron.velocidad_promedio_kmh,
            "kilometraje_total_km": round(dron.kilometraje_total_km, 2),
            "disponible": dron.disponible,
            "en_mision": dron.en_mision,
            "retornando_a_base": dron.retornando_a_base,
            "estado_operacional": estado_operacional,
            "pedido_activo_id": dron.pedido_activo.id_pedido if dron.pedido_activo else None,
            "bateria": bateria,
            "altitud": altitud,
            "en_norma_uaeac": 0.0 <= altitud <= 120.0,
            "estado_motores": motores,
            "coordenadas": coords,
            "distancia_a_base_km": distancia_a_base_km,
            "puede_aterrizar_en_base": dron.retornando_a_base and distancia_a_base_km <= 0.05,
            "destino_actual": destino_objetivo,
            "distancia_objetivo_km": distancia_objetivo_km,
            "eta_min": eta_min,
            "progreso_mision_pct": progreso_mision_pct,
            "progreso_retorno_pct": progreso_retorno_pct,
            "consumo_10km_pct": consumo_10km,
            "especificaciones": self._extraer_atributos_especializados(dron),
            "ficha_str": str(dron).strip(),
            "ficha_repr": repr(dron),
            "diagnostico_sistemas": dron.inspeccionar_sistemas_especializados(),
            "ultimo_reporte_mision": ruta_meta.get("ultimo_reporte"),
        }

    def _serializar_pedido(self, pedido: Pedido) -> dict[str, Any]:
        coords = list(pedido.coordenada_destino) if pedido.coordenada_destino else None
        base = self.centro.coordenadas_base
        distancia_base_km = (
            round(self.calculador.calcular_haversine(base, pedido.coordenada_destino), 2)
            if pedido.coordenada_destino
            else 0.0
        )

        # Buscar dron compatible sugerido si aún está PENDIENTE
        dron_sugerido_id = None
        viabilidad = None
        dron_referencia = pedido.dron_asignado

        if dron_referencia is None and pedido.estado == "PENDIENTE":
            for dron in self.centro.obtener_drones_disponibles():
                if getattr(dron, "categoria", None) == pedido.categoria_requerida:
                    dron_referencia = dron
                    dron_sugerido_id = dron.id_dron
                    break

        if dron_referencia is not None and pedido.coordenada_destino is not None:
            dist = dron_referencia.calcular_distancia_a_destino(pedido.coordenada_destino)
            consumo = round(dron_referencia.calcular_consumo_estimado(dist), 1)
            eta = round(dron_referencia.estimar_tiempo_llegada_min(pedido.coordenada_destino), 1)
            bat_actual = round(dron_referencia.telemetria.bateria, 1) if dron_referencia.telemetria else 0.0
            apto_peso = True
            if isinstance(dron_referencia, DronEntregaLigera):
                apto_peso = dron_referencia.es_apto_carga(pedido.peso_carga_kg)
            viabilidad = {
                "id_dron": dron_referencia.id_dron,
                "distancia_km": round(dist, 2),
                "eta_min": eta,
                "consumo_estimado_pct": consumo,
                "bateria_actual_pct": bat_actual,
                "apto_bateria": bat_actual >= consumo,
                "apto_peso": apto_peso,
                "es_viable": (bat_actual >= consumo) and apto_peso,
            }

        return {
            "id_pedido": pedido.id_pedido,
            "usuario_id": pedido.usuario_solicitante.id_usuario,
            "usuario_nombre": pedido.usuario_solicitante.nombre,
            "categoria_requerida": pedido.categoria_requerida,
            "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(
                pedido.categoria_requerida, pedido.categoria_requerida
            ),
            "coordenada_destino": coords,
            "direccion_destino": pedido.direccion_destino,
            "peso_carga_kg": pedido.peso_carga_kg,
            "estado": pedido.estado,
            "dron_asignado_id": pedido.dron_asignado.id_dron if pedido.dron_asignado else None,
            "dron_sugerido_id": dron_sugerido_id,
            "distancia_desde_base_km": distancia_base_km,
            "viabilidad": viabilidad,
            "str": str(pedido),
            "repr": repr(pedido),
        }

    # ==========================================================================
    # OPERACIONES EXPUESTAS AL SERVIDOR HTTP
    # ==========================================================================

    def obtener_estado_completo(self) -> dict[str, Any]:
        usuario_activo = self._buscar_usuario(self._usuario_activo_id)
        return {
            "ok": True,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "ultima_sincronizacion": self._ultima_sincronizacion,
            "coordenadas_base": list(self.centro.coordenadas_base),
            "radio_tierra_km": self.calculador.radio_tierra_km,
            "limites_aburra": {
                "lat_min": self.calculador.LAT_MIN_ABURRA,
                "lat_max": self.calculador.LAT_MAX_ABURRA,
                "lon_min": self.calculador.LON_MIN_ABURRA,
                "lon_max": self.calculador.LON_MAX_ABURRA,
            },
            "tiempo_activo_seg": self.reloj.obtener_tiempo_total_seg(),
            "clima": self._clima_cache,
            "usuario_activo": {
                "id_usuario": usuario_activo.id_usuario,
                "nombre": usuario_activo.nombre,
                "rol": usuario_activo.rol,
            },
            "usuarios": [
                {"id_usuario": u.id_usuario, "nombre": u.nombre, "rol": u.rol}
                for u in self.centro.usuarios_registrados
            ],
            "flota": [self._serializar_dron(d) for d in self.centro.flota_drones],
            "pedidos": [self._serializar_pedido(p) for p in reversed(self.centro.pedidos)],
            "logs": [
                {
                    "id_log": log.id_log,
                    "fecha_hora": log.fecha_hora,
                    "tipo_evento": log.tipo_evento,
                    "id_dron": log.id_dron,
                    "id_pedido": log.id_pedido,
                    "detalles": log.detalles,
                }
                for log in reversed(self.centro.historial_logs[-30:])
            ],
            "destinos_referencia": self.DESTINOS_REFERENCIA,
        }

    def calcular_preview_ruta(self, id_dron: str, lat: float, lon: float) -> dict[str, Any]:
        """Calcula distancia ortodrómica Haversine (RF-03), ETA (RF-10) y consumo polimórfico (HU-10)."""
        destino = (float(lat), float(lon))
        self.calculador.validar_coordenada(destino)
        dron = self._buscar_dron(id_dron)
        distancia_km = dron.calcular_distancia_a_destino(destino)
        eta_min = dron.estimar_tiempo_llegada_min(destino)
        consumo_pct = dron.calcular_consumo_estimado(distancia_km)
        return {
            "ok": True,
            "id_dron": dron.id_dron,
            "origen": list(dron.telemetria.coordenadas) if dron.telemetria else list(self.centro.coordenadas_base),
            "destino": list(destino),
            "distancia_km": round(distancia_km, 2),
            "eta_min": round(eta_min, 1),
            "velocidad_kmh": dron.velocidad_promedio_kmh,
            "consumo_estimado_pct": round(consumo_pct, 2),
        }

    def registrar_nuevo_pedido(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Registra una solicitud de servicio validando dominio y geocodificación (RF-07)."""
        id_pedido = str(datos.get("id_pedido", "")).strip()
        categoria = str(datos.get("categoria_requerida", "")).strip().upper()
        peso_raw = datos.get("peso_carga_kg", 0.0)
        peso = float(peso_raw) if peso_raw not in ("", None) else 0.0
        direccion = str(datos.get("direccion_destino", "")).strip() or None
        id_usuario = str(datos.get("id_usuario") or self._usuario_activo_id)
        usuario = self._buscar_usuario(id_usuario)

        coordenada_destino = None
        lat_raw = datos.get("latitud")
        lon_raw = datos.get("longitud")
        if lat_raw not in (None, "") and lon_raw not in (None, ""):
            coordenada_destino = (float(lat_raw), float(lon_raw))
            # Validar pertenencia al Valle de Aburrá (Regla de Negocio #5)
            self.calculador.validar_coordenada(coordenada_destino)

        nuevo_pedido = Pedido(
            id_pedido=id_pedido,
            usuario_solicitante=usuario,
            categoria_requerida=categoria,
            coordenada_destino=coordenada_destino,
            peso_carga_kg=peso,
            direccion_destino=direccion,
        )
        self.centro.registrar_pedido(nuevo_pedido)
        self.centro.generar_log(
            evento="SOLICITUD_REGISTRADA",
            id_pedido=nuevo_pedido.id_pedido,
            detalles=(
                f"Solicitud registrada en categoría {nuevo_pedido.categoria_requerida} "
                f"con destino {nuevo_pedido.coordenada_destino} y carga {nuevo_pedido.peso_carga_kg:.1f} kg."
            ),
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Solicitud {nuevo_pedido.id_pedido} registrada en estado PENDIENTE."
        estado["pedido_creado_id"] = nuevo_pedido.id_pedido
        return estado

    def asignar_dron(self, id_pedido: str) -> dict[str, Any]:
        """Ejecuta el cruce inteligente de recursos en SistemaCentroControl (RF-08)."""
        pedido = self._buscar_pedido(id_pedido)
        asignado = self.centro.asignar_dron_a_pedido(pedido.id_pedido)
        if not asignado:
            raise ActualizarEstadoDronError(
                "FLOTA",
                f"No hay aeronaves disponibles para la categoría '{pedido.categoria_requerida}'.",
            )

        dron = pedido.dron_asignado
        if dron and pedido.coordenada_destino:
            dist_ida = dron.calcular_distancia_a_destino(pedido.coordenada_destino)
            self._rutas_visuales[dron.id_dron] = {
                "origen": list(dron.telemetria.coordenadas) if dron.telemetria else list(self.centro.coordenadas_base),
                "ultimo_destino": list(pedido.coordenada_destino),
                "distancia_ida_total_km": max(dist_ida, 0.001),
                "distancia_retorno_total_km": max(dist_ida, 0.001),
                "ultimo_reporte": None,
            }

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Cruce exitoso: {dron.id_dron} ({dron.modelo_aeronave}) vinculado al pedido {pedido.id_pedido}."
        )
        estado["dron_enfocado_id"] = dron.id_dron if dron else None
        return estado

    def iniciar_vuelo_mision(self, id_pedido: str, modo: str = "SIMULADO") -> dict[str, Any]:
        """
        Despacha polimórficamente la misión asignada (HU-12):
        - Modo 'SIMULADO': Ejecuta dron.ejecutar_mision(pedido) y permite ver el avance progresivo con Reloj Delta.
        - Modo 'INSTANTANEO': Ejecuta centro.despachar_mision(id_pedido) completando misión e iniciando retorno.
        """
        pedido = self._buscar_pedido(id_pedido)
        if pedido.estado != "ASIGNADO" or pedido.dron_asignado is None:
            raise ValueError(f"El pedido '{pedido.id_pedido}' debe estar en estado ASIGNADO con un dron vinculado.")

        dron = pedido.dron_asignado

        if modo.upper() == "INSTANTANEO":
            # Validación previa polimórfica para propagar excepciones de dominio claras (sobrepeso / batería)
            if isinstance(dron, DronEntregaLigera) and not dron.es_apto_carga(pedido.peso_carga_kg):
                dron.disponible = True
                dron.en_mision = False
                pedido.actualizar_estado("CANCELADO")
                raise ActualizarEstadoDronError(
                    dron.id_dron,
                    f"Misión rechazada por sobrepeso: {pedido.peso_carga_kg:.1f} kg excede el máximo de {dron.capacidad_carga_kg:.1f} kg.",
                )

            exito = self.centro.despachar_mision(pedido.id_pedido)
            if not exito:
                raise ActualizarEstadoDronError(
                    dron.id_dron, f"No fue posible completar el despacho del pedido {pedido.id_pedido}."
                )
            estado = self.obtener_estado_completo()
            estado["mensaje_operacion"] = (
                f"Misión {pedido.id_pedido} despachada polimórficamente; {dron.id_dron} en protocolo de retorno."
            )
            estado["dron_enfocado_id"] = dron.id_dron
            return estado

        # Modo SIMULADO (telemetría progresiva con SimuladorVuelo y RelojSimulacion)
        self.reloj.obtener_delta()  # Reinicia marca delta justo al despegar
        dron.coordenadas_base = self.centro.coordenadas_base
        dron.disponible = True  # Habilita bandera de despegue para el dron reservado

        try:
            reporte_despegue = dron.ejecutar_mision(pedido)
        except Exception:
            # Si es rechazado por sobrepeso o batería insuficiente, liberar aeronave y cancelar pedido
            dron.disponible = True
            dron.en_mision = False
            dron.pedido_activo = None
            pedido.actualizar_estado("CANCELADO")
            self.centro.generar_log(
                evento="MISION_RECHAZADA",
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                detalles="Despegue abortado por regla de negocio de seguridad o capacidad.",
            )
            raise

        dist_ida = reporte_despegue.get("distancia_objetivo_km", 1.0)
        self._rutas_visuales[dron.id_dron] = {
            "origen": list(dron.telemetria.coordenadas),
            "ultimo_destino": list(pedido.coordenada_destino),
            "distancia_ida_total_km": max(float(dist_ida), 0.001),
            "distancia_retorno_total_km": max(float(dist_ida), 0.001),
            "ultimo_reporte": reporte_despegue,
        }

        self.centro.generar_log(
            evento="DESPEGUE_POLIMORFICO",
            id_dron=dron.id_dron,
            id_pedido=pedido.id_pedido,
            detalles=f"Despegue autorizado a 30 m. Instrumental: {reporte_despegue.get('instrumental_activado', 'ACTIVO')}.",
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Despegue exitoso: {dron.id_dron} en vuelo hacia destino ({dist_ida:.2f} km)."
        )
        estado["dron_enfocado_id"] = dron.id_dron
        return estado

    def sincronizar_flota(
        self,
        factor_tiempo: float = 1.0,
        paso_fijo_seg: float | None = None,
        consultar_clima: bool = False,
    ) -> dict[str, Any]:
        """
        Hook no bloqueante de sincronización bajo demanda (RF-05):
        Mide el intervalo real con RelojSimulacion.obtener_delta() y avanza la física
        de todas las aeronaves activas mediante SimuladorVuelo.
        """
        delta_real = self.reloj.obtener_delta()
        multiplicador = max(1.0, min(120.0, float(factor_tiempo)))
        delta_efectivo = float(paso_fijo_seg) if paso_fijo_seg is not None else (delta_real * multiplicador)

        if consultar_clima:
            self._clima_cache = self.servicio_clima.obtener_condiciones("Medellin_Centro")

        factor_clima = float(self._clima_cache.get("factor_velocidad", 1.0))

        # Capturar distancias de retorno si algún dron pasa de misión a retorno en este paso
        estaban_en_mision = {d.id_dron: d.en_mision for d in self.centro.flota_drones}

        reportes = self.simulador.avanzar_flota(
            self.centro.flota_drones,
            delta_t=delta_efectivo,
            factor_clima=factor_clima,
        )

        for dron, rep in zip(self.centro.flota_drones, reportes):
            estado_rep = rep.get("estado")
            if estaban_en_mision.get(dron.id_dron) and dron.retornando_a_base:
                dist_ret = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
                meta = self._rutas_visuales.setdefault(dron.id_dron, {})
                meta["distancia_retorno_total_km"] = max(dist_ret, meta.get("distancia_ida_total_km", 0.5))
                self.centro.generar_log(
                    evento="MISION_COMPLETADA_RETORNO",
                    id_dron=dron.id_dron,
                    detalles=f"Objetivo alcanzado. Iniciando retorno obligatorio a base ({dist_ret:.2f} km).",
                )
            elif estado_rep == "LLEGADA_A_BASE":
                self.centro.generar_log(
                    evento="ATERRIZAJE_EN_BASE",
                    id_dron=dron.id_dron,
                    detalles=f"Dron {dron.id_dron} aterrizó en sede central y recuperó disponibilidad.",
                )

        # Invocar método oficial de sincronización del Centro de Control (RF-05)
        if consultar_clima or paso_fijo_seg is not None or multiplicador == 1.0:
            self.centro.refrescar_datos_flota()

        self._ultima_sincronizacion = datetime.now().strftime("%H:%M:%S")
        estado = self.obtener_estado_completo()
        estado["delta_real_seg"] = round(delta_real, 2)
        estado["delta_simulado_seg"] = round(delta_efectivo, 1)
        estado["reportes_simulacion"] = reportes
        return estado

    def ordenar_retorno_base(self, id_dron: str) -> dict[str, Any]:
        """Activa el protocolo de retorno obligatorio a la sede central (RF-09)."""
        dron = self._buscar_dron(id_dron)
        if dron.pedido_activo is not None and dron.pedido_activo.estado == "EN_TRANSITO":
            dron.pedido_activo.actualizar_estado("CANCELADO")
            dron.pedido_activo = None

        exito = self.centro.gestionar_retorno_a_base(dron.id_dron)
        if not exito:
            raise ActualizarEstadoDronError(
                dron.id_dron,
                "La aeronave no se encuentra en una misión activa para iniciar retorno.",
            )

        dist_base = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
        meta = self._rutas_visuales.setdefault(dron.id_dron, {})
        meta["distancia_retorno_total_km"] = max(dist_base, 0.05)

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Retorno obligatorio activado para {dron.id_dron} ({dist_base:.2f} km a base)."
        return estado

    def finalizar_retorno_dron(self, id_dron: str) -> dict[str, Any]:
        """
        Verifica tolerancia física de 50 metros y aterriza el dron en base (RF-09).
        Si está a > 0.05 km, Dron.finalizar_retorno_en_base() lanza ActualizarEstadoDronError.
        """
        dron = self._buscar_dron(id_dron)
        dron.finalizar_retorno_en_base()
        if dron.telemetria is not None:
            dron.actualizar_telemetria(
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=self.centro.coordenadas_base,
            )
        self.centro.generar_log(
            evento="RETORNO_FINALIZADO",
            id_dron=dron.id_dron,
            detalles=f"Disponibilidad desbloqueada para {dron.id_dron} tras validación en coordenadas base.",
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Retorno finalizado: {dron.id_dron} disponible en plataforma."
        return estado

    def actualizar_telemetria_manual(self, datos: dict[str, Any]) -> dict[str, Any]:
        """
        Permite validar e inyectar tramas de telemetría (RF-01) y demostrar
        las excepciones de dominio ante valores fuera de norma (RF-02).
        """
        id_dron = str(datos.get("id_dron", "")).strip()
        dron = self._buscar_dron(id_dron)

        bateria = float(datos["bateria"]) if datos.get("bateria") not in (None, "") else None
        altitud = float(datos["altitud"]) if datos.get("altitud") not in (None, "") else None
        motores = str(datos["estado_motores"]).strip().upper() if datos.get("estado_motores") else None

        coordenadas = None
        if datos.get("latitud") not in (None, "") and datos.get("longitud") not in (None, ""):
            coordenadas = (float(datos["latitud"]), float(datos["longitud"]))
            # Validar también polígono operativo del Valle de Aburrá (Regla de Negocio #5)
            self.calculador.validar_coordenada(coordenadas)

        dron.actualizar_telemetria(
            bateria_o_telemetria=bateria,
            altitud=altitud,
            estado_motores=motores,
            coordenadas=coordenadas,
        )
        self.centro.generar_log(
            evento="TRAMA_TELEMETRIA_VALIDADA",
            id_dron=dron.id_dron,
            detalles=(
                f"Trama aceptada -> Bat: {dron.telemetria.bateria:.1f}%, "
                f"Alt: {dron.telemetria.altitud:.1f} m, Motores: {dron.telemetria.estado_motores}."
            ),
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Trama de telemetría validada y aplicada a {dron.id_dron}."
        return estado

    def recargar_bateria_base(self, id_dron: str) -> dict[str, Any]:
        """Recarga al 100% la batería de una aeronave estacionada en base."""
        dron = self._buscar_dron(id_dron)
        if not dron.disponible or dron.en_mision or dron.retornando_a_base:
            raise ActualizarEstadoDronError(
                dron.id_dron, "Solo se puede recargar una aeronave disponible y estacionada en base."
            )
        dron.actualizar_telemetria(
            bateria_o_telemetria=100.0,
            altitud=0.0,
            estado_motores="STANDBY",
            coordenadas=self.centro.coordenadas_base,
        )
        self.centro.generar_log(
            evento="MANTENIMIENTO_BATERIA",
            id_dron=dron.id_dron,
            detalles=f"Banco energético de {dron.id_dron} recargado al 100.0% en plataforma.",
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Batería de {dron.id_dron} restablecida al 100.0%."
        return estado

    def gestionar_usuario(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Permite cambiar el usuario activo o registrar un nuevo perfil (RF-06)."""
        accion = str(datos.get("accion", "cambiar")).lower()
        if accion == "registrar":
            nuevo = Usuario(
                id_usuario=str(datos.get("id_usuario", "")),
                nombre=str(datos.get("nombre", "")),
                rol=str(datos.get("rol", "")),
            )
            self.centro.registrar_usuario(nuevo)
            self._usuario_activo_id = nuevo.id_usuario
            self.centro.generar_log(
                evento="USUARIO_REGISTRADO",
                detalles=f"Usuario '{nuevo.nombre}' ({nuevo.id_usuario}) dado de alta con rol {nuevo.rol}.",
            )
            msg = f"Usuario {nuevo.nombre} ({nuevo.rol}) registrado y activo."
        else:
            usuario = self._buscar_usuario(str(datos.get("id_usuario", "")))
            self._usuario_activo_id = usuario.id_usuario
            msg = f"Sesión activa cambiada a {usuario.nombre} ({usuario.rol})."

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = msg
        return estado

    # ==========================================================================
    # CLASIFICACIÓN DE EXCEPCIONES DE DOMINIO (RF-02)
    # ==========================================================================

    @staticmethod
    def formatear_excepcion(exc: Exception) -> dict[str, Any]:
        """Mapea cualquier excepción disparada por el backend a su Regla de Negocio oficial."""
        mapa_reglas: tuple[tuple[type[Exception], str], ...] = (
            (BateriaInvalidaError, "Regla de Negocio #2 · Batería [0.0, 100.0]%"),
            (AltitudInvalidaError, "Regla de Negocio #3 · Techo UAEAC [0.0, 120.0] m"),
            (EstadoMotorInvalidoError, "Regla de Negocio #4 · Coherencia Motores vs Altitud"),
            (CoordenadaInvalidaError, "Regla de Negocio #5 · Polígono Valle de Aburrá"),
            (GeocodificacionError, "Regla de Negocio #5 · Geocodificación Aburrá"),
            (DestinoInvalidoError, "Regla de Negocio #5 · Coordenada Destino"),
            (CategoriaDronInvalidoError, "Regla de Negocio #8 · Categorías Autorizadas"),
            (ActualizarEstadoDronError, "Regla de Negocio #9 · Control Operacional y Retorno"),
            (EstadoDronDuplicadoError, "Regla de Negocio #9 · Transición de Disponibilidad"),
            (TelemetriaNoAsignadaError, "Regla de Negocio #1 · Integridad de Telemetría"),
            (AsignarTelemetriaError, "Regla de Negocio #1 · Coherencia de Trama"),
            (DronError, "Regla de Dominio Aeronáutico"),
        )

        regla = "Validación de Dominio"
        for clase_exc, etiqueta_regla in mapa_reglas:
            if isinstance(exc, clase_exc):
                regla = etiqueta_regla
                break

        return {
            "ok": False,
            "error_tipo": type(exc).__name__,
            "mensaje": str(exc),
            "regla_negocio": regla,
        }
