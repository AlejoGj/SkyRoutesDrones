# Presentadores y serializadores DTO para el estado del sistema y entidades POO
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.control.centro_control import FABRICA_DRONES, SistemaCentroControl
from src.control.reloj import RelojSimulacion
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
from src.ui.catalogos import (
    ESQUEMA_FABRICA,
    ESTADOS_MOTORES_UI,
    ETIQUETAS_CATEGORIA,
    SUGERENCIAS_DIRECCIONES,
)
from src.ui.sesiones_vuelo import calcular_progreso_lineal
from src.usuarios.usuario import Usuario


def pedido_reservado_para_dron(dron: Dron, pedidos: list[Pedido]) -> Pedido | None:
    """
    Identifica el pedido actualmente vinculado o en tránsito para una aeronave específica.

    Examina primero la referencia directa `dron.pedido_activo`. Si no está asignada,
    recorre la lista de pedidos en memoria buscando coincidencias con estado 'ASIGNADO'
    o 'EN_TRANSITO' asociadas a la aeronave dada.

    Args:
        dron (Dron): Instancia de la aeronave consultada.
        pedidos (list[Pedido]): Lista de pedidos registrados en el centro de control.

    Returns:
        Pedido | None: Instancia del pedido vinculado si existe, o None si el dron está libre.
    """
    if dron.pedido_activo is not None:
        return dron.pedido_activo
    for pedido in pedidos:
        if pedido.dron_asignado is dron and pedido.estado in ("ASIGNADO", "EN_TRANSITO"):
            return pedido
    return None


def extraer_atributos_especializados(dron: Dron) -> list[dict[str, str]]:
    """
    Extrae las especificaciones técnicas particulares de cada subclase especializada de aeronave.

    Inspecciona polimórficamente la instancia de `Dron` para extraer los atributos
    de hardware únicos según su rol operacional y devolverlos formateados para los chips de la UI.

    Args:
        dron (Dron): Instancia de una de las 6 subclases de la flota (`DronEntregaLigera`,
            `DronCargaPesada`, `DronVigilancia`, `DronMapeo`, `DronInspeccion`, `DronRescate`).

    Returns:
        list[dict[str, str]]: Lista de diccionarios con formato `{'etiqueta': str, 'valor': str}`.
    """
    if isinstance(dron, DronEntregaLigera):
        return [
            {"etiqueta": "Capacidad Máx.", "valor": f"{dron.capacidad_carga_kg:.1f} kg"},
            {"etiqueta": "Refrigeración", "valor": "Activa" if dron.compartimento_refrigerado else "Estándar"},
            {"etiqueta": "Suelta Rápida", "valor": "Equipada" if dron.mecanismo_suelta_rapida else "Manual"},
        ]
    if isinstance(dron, DronCargaPesada):
        return [
            {"etiqueta": "Volumen Tolva", "valor": f"{dron.volumen_carga_m3:.1f} m3"},
            {"etiqueta": "Tren Motriz", "valor": f"{dron.numero_rotores} rotores"},
            {"etiqueta": "Remolque", "valor": f"{dron.potencia_remolque_w:.0f} W"},
        ]
    if isinstance(dron, DronVigilancia):
        return [
            {"etiqueta": "Cámara Óptica", "valor": f"{dron.resolucion_camara_mp} MP"},
            {"etiqueta": "Visión Nocturna", "valor": "Infrarroja" if dron.vision_nocturna else "Inactiva"},
            {"etiqueta": "Frecuencia Video", "valor": f"{dron.frecuencia_transmision_ghz} GHz"},
        ]
    if isinstance(dron, DronMapeo):
        return [
            {"etiqueta": "Escáner LiDAR", "valor": "Equipado" if dron.tiene_sensor_lidar else "Fotogrametría"},
            {"etiqueta": "Precisión RTK", "valor": f"+/- {dron.precision_gps_cm} cm"},
            {"etiqueta": "Almacenamiento", "valor": f"{dron.capacidad_almacenamiento_tb:.1f} TB"},
        ]
    if isinstance(dron, DronInspeccion):
        return [
            {"etiqueta": "Zoom Óptico", "valor": f"{dron.zoom_optico_x}x"},
            {"etiqueta": "Sensor Ultrasónico", "valor": f"{dron.rango_sensor_ultrasonico_m:.1f} m"},
            {"etiqueta": "Estabilización", "valor": "Vuelo Estacionario"},
        ]
    if isinstance(dron, DronRescate):
        return [
            {"etiqueta": "Cámara Térmica", "valor": "FLIR Activa" if dron.camara_termica else "Inactiva"},
            {"etiqueta": "Kit Auxilios", "valor": "Equipado" if dron.kit_auxilios_equipado else "Sin kit"},
            {"etiqueta": "Altavoz SAR", "valor": f"{dron.potencia_altavoz_db} dB"},
        ]
    return []


def diagnosticar_candidatos_pedido(
    pedido: Pedido,
    flota: list[Dron],
    coordenadas_base: tuple[float, float],
    calculador: CalculadorGeodesico,
) -> dict[str, Any]:
    """
    Evalúa la viabilidad cinemática y energética de la flota para un pedido antes de su asignación.

    Aplica la Regla de Negocio de **Autonomía de Circuito Completo** (RN-10):
    Calcula la distancia de ida al destino más el regreso obligatorio al vertipuerto central,
    y computa mediante el método polimórfico `calcular_consumo_estimado()` el gasto de batería
    exacto que requeriría cada aeronave de la categoría solicitada.

    Args:
        pedido (Pedido): Pedido cuya asignación se está diagnosticando.
        flota (list[Dron]): Lista completa de aeronaves registradas en la torre de control.
        coordenadas_base (tuple[float, float]): Coordenadas del vertipuerto central Olaya Herrera.
        calculador (CalculadorGeodesico): Instancia del motor geodésico Haversine.

    Returns:
        dict[str, Any]: Diagnóstico cuantitativo:
            - distancia_ida_km (float): Distancia ortodrómica desde la base al destino.
            - distancia_retorno_km (float): Distancia de retorno desde el destino a la base.
            - distancia_total_km (float): Circuito completo ida + vuelta.
            - candidatos (list[dict]): Lista de aeronaves evaluadas con banderas de elegibilidad
              (`disponible`, `apto_bateria`, `apto_peso`, `consumo_ida_vuelta_pct`).
    """
    if pedido.coordenada_destino is None:
        return {"distancia_ida_km": 0.0, "distancia_total_km": 0.0, "candidatos": []}

    dist_ida = calculador.calcular_haversine(coordenadas_base, pedido.coordenada_destino)
    dist_ret = calculador.calcular_haversine(pedido.coordenada_destino, coordenadas_base)
    dist_total = dist_ida + dist_ret

    candidatos = []
    for dron in flota:
        if getattr(dron, "categoria", None) != pedido.categoria_requerida:
            continue
        bat = round(dron.telemetria.bateria, 1) if dron.telemetria else 0.0
        d_ida_dron = (
            dron.calcular_distancia_a_destino(pedido.coordenada_destino)
            if dron.telemetria
            else dist_ida
        )
        d_tot_dron = d_ida_dron + dist_ret
        consumo_req = round(dron.calcular_consumo_estimado(d_tot_dron), 1)
        apto_peso = True
        if isinstance(dron, DronEntregaLigera):
            apto_peso = dron.es_apto_carga(pedido.peso_carga_kg)

        candidatos.append(
            {
                "id_dron": dron.id_dron,
                "modelo_aeronave": dron.modelo_aeronave,
                "disponible": dron.disponible,
                "bateria_actual_pct": bat,
                "consumo_ida_vuelta_pct": consumo_req,
                "apto_bateria": bat > 0.0 and bat >= consumo_req,
                "apto_peso": apto_peso,
                "elegible_ahora": dron.disponible and bat > 0.0 and bat >= consumo_req and apto_peso,
            }
        )

    return {
        "distancia_ida_km": round(dist_ida, 2),
        "distancia_retorno_km": round(dist_ret, 2),
        "distancia_total_km": round(dist_total, 2),
        "candidatos": candidatos,
    }


def serializar_dron(
    dron: Dron,
    centro: SistemaCentroControl,
    calculador: CalculadorGeodesico,
    clima_actual: dict[str, Any],
    sesiones_vuelo: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Serializa el estado integral, telemetría sensorial y diagnóstico de una aeronave para la UI.

    Transforma la entidad orientada a objetos `Dron` en un Data Transfer Object (DTO)
    apto para serialización JSON. Incorpora cálculo de velocidad efectiva modulada por clima,
    cálculo de ETA a destino o base, odómetro acumulado, bandera de tolerancia de vertipuerto
    (`puede_aterrizar_manual` a <= 50 m) y progreso lineal de la misión.

    Args:
        dron (Dron): Instancia de la aeronave a serializar.
        centro (SistemaCentroControl): Torre de control con acceso a vertipuerto y pedidos.
        calculador (CalculadorGeodesico): Motor geodésico para cálculo de distancias y ETA.
        clima_actual (dict[str, Any]): Reporte meteorológico vigente en el nodo activo.
        sesiones_vuelo (dict[str, dict[str, Any]]): Diccionario de sesiones activas en la interfaz.

    Returns:
        dict[str, Any]: Diccionario con las propiedades operativas, sensoriales y visuales del dron.
    """
    tele = dron.telemetria
    base = centro.coordenadas_base
    coords = list(tele.coordenadas) if tele else list(base)
    bateria = round(tele.bateria, 1) if tele else 0.0
    altitud = round(tele.altitud, 1) if tele else 0.0
    motores = tele.estado_motores if tele else "SIN_TELEMETRIA"
    categoria = getattr(dron, "categoria", getattr(dron, "CATEGORIA_ESPECIALIZADA", "ESTANDAR"))

    distancia_a_base_km = (
        round(calculador.calcular_haversine(tuple(coords), base), 3) if tele else 0.0
    )
    pedido_vinculado = pedido_reservado_para_dron(dron, centro.pedidos)
    en_vuelo_mision = bool(dron.en_mision and dron.pedido_activo is not None)

    if bateria <= 0.0:
        estado_operacional = "SIN_BATERIA"
        etiqueta_estado = "EMERGENCIA 0.0%"
    elif dron.retornando_a_base:
        estado_operacional = "RETORNANDO_A_BASE"
        etiqueta_estado = "RETORNANDO A BASE"
    elif en_vuelo_mision:
        estado_operacional = "EN_MISION"
        etiqueta_estado = "EN VUELO A DESTINO"
    elif not dron.disponible:
        estado_operacional = "RESERVADO"
        etiqueta_estado = (
            f"RESERVADO ({pedido_vinculado.id_pedido})"
            if pedido_vinculado is not None
            else "NO DISPONIBLE"
        )
    else:
        estado_operacional = "DISPONIBLE"
        etiqueta_estado = "DISPONIBLE EN BASE"

    factor_clima = float(clima_actual.get("factor_velocidad", 1.0))
    velocidad_efectiva_kmh = round(dron.velocidad_promedio_kmh * factor_clima, 1)

    distancia_objetivo_km = 0.0
    eta_min = 0.0
    if en_vuelo_mision and dron.pedido_activo and dron.pedido_activo.coordenada_destino:
        distancia_objetivo_km = round(
            dron.calcular_distancia_a_destino(dron.pedido_activo.coordenada_destino), 2
        )
        eta_min = round(
            calculador.calcular_tiempo_vuelo_min(distancia_objetivo_km, velocidad_efectiva_kmh), 1
        )
    elif dron.retornando_a_base:
        distancia_objetivo_km = round(distancia_a_base_km, 2)
        eta_min = round(
            calculador.calcular_tiempo_vuelo_min(distancia_objetivo_km, velocidad_efectiva_kmh), 1
        )

    sesion = sesiones_vuelo.get(dron.id_dron)
    progreso = calcular_progreso_lineal(dron, sesion, distancia_a_base_km)
    tasa_bat_km = round(dron.calcular_consumo_estimado(1.0), 2)
    ultimo_completado = getattr(dron, "ultimo_pedido_completado", None)

    return {
        "id_dron": dron.id_dron,
        "modelo_aeronave": dron.modelo_aeronave,
        "clase_python": type(dron).__name__,
        "categoria": categoria,
        "categoria_etiqueta": ETIQUETAS_CATEGORIA.get(categoria, categoria),
        "velocidad_promedio_kmh": dron.velocidad_promedio_kmh,
        "velocidad_efectiva_kmh": velocidad_efectiva_kmh,
        "tasa_consumo_bat_km": tasa_bat_km,
        "kilometraje_total_km": round(dron.kilometraje_total_km, 2),
        "disponible": dron.disponible,
        "en_mision": dron.en_mision,
        "en_vuelo_activo": en_vuelo_mision or dron.retornando_a_base,
        "retornando_a_base": dron.retornando_a_base,
        "puede_recargar": not (dron.en_mision or dron.retornando_a_base),
        "puede_aterrizar_manual": bool(dron.retornando_a_base and distancia_a_base_km <= 0.05),
        "estado_operacional": estado_operacional,
        "etiqueta_estado": etiqueta_estado,
        "pedido_activo_id": dron.pedido_activo.id_pedido if dron.pedido_activo else None,
        "pedido_vinculado_id": pedido_vinculado.id_pedido if pedido_vinculado else None,
        "ultimo_pedido_id": ultimo_completado.id_pedido if ultimo_completado else None,
        "bateria": bateria,
        "altitud": altitud,
        "estado_motores": motores,
        "coordenadas": coords,
        "distancia_a_base_km": distancia_a_base_km,
        "distancia_objetivo_km": distancia_objetivo_km,
        "eta_min": eta_min,
        "progreso_lineal": progreso,
        "especificaciones": extraer_atributos_especializados(dron),
        "ficha_str": str(dron).strip(),
        "ficha_repr": repr(dron),
        "diagnostico_sistemas": dron.inspeccionar_sistemas_especializados(),
        "historial_telemetria": list(dron.historial_telemetria[-25:]),
        "total_tramas_telemetria": len(dron.historial_telemetria),
    }


def serializar_pedido(
    pedido: Pedido,
    centro: SistemaCentroControl,
    calculador: CalculadorGeodesico,
    fuentes_geocodificacion: dict[str, str],
) -> dict[str, Any]:
    """
    Serializa un pedido comercial junto con su análisis predictivo de viabilidad para la UI.

    Args:
        pedido (Pedido): Entidad comercial del pedido a serializar.
        centro (SistemaCentroControl): Torre de control centralizada.
        calculador (CalculadorGeodesico): Motor geodésico Haversine.
        fuentes_geocodificacion (dict[str, str]): Registro histórico de la fuente cartográfica utilizada.

    Returns:
        dict[str, Any]: Diccionario DTO con datos de usuario solicitante, destino geográfico dual,
            estado actual y candidatos aptos de la flota.
    """
    coords = list(pedido.coordenada_destino) if pedido.coordenada_destino else None
    analisis = diagnosticar_candidatos_pedido(
        pedido=pedido,
        flota=centro.flota_drones,
        coordenadas_base=centro.coordenadas_base,
        calculador=calculador,
    )
    return {
        "id_pedido": pedido.id_pedido,
        "usuario_id": pedido.usuario_solicitante.id_usuario,
        "usuario_nombre": pedido.usuario_solicitante.nombre,
        "usuario_rol": pedido.usuario_solicitante.rol,
        "categoria_requerida": pedido.categoria_requerida,
        "categoria_etiqueta": ETIQUETAS_CATEGORIA.get(
            pedido.categoria_requerida, pedido.categoria_requerida
        ),
        "coordenada_destino": coords,
        "direccion_destino": pedido.direccion_destino,
        "fuente_geocodificacion": fuentes_geocodificacion.get(pedido.id_pedido),
        "peso_carga_kg": round(pedido.peso_carga_kg, 2),
        "estado": pedido.estado,
        "dron_asignado_id": pedido.dron_asignado.id_dron if pedido.dron_asignado else None,
        "dron_asignado_modelo": (
            pedido.dron_asignado.modelo_aeronave if pedido.dron_asignado else None
        ),
        "distancia_ida_km": analisis["distancia_ida_km"],
        "distancia_ida_vuelta_km": analisis["distancia_total_km"],
        "candidatos": analisis["candidatos"],
        "str": str(pedido),
        "repr": repr(pedido),
    }


def construir_snapshot_estado(
    centro: SistemaCentroControl,
    calculador: CalculadorGeodesico,
    reloj: RelojSimulacion,
    usuario_activo: Usuario,
    clima_actual: dict[str, Any],
    sesiones_vuelo: dict[str, dict[str, Any]],
    fuentes_geocodificacion: dict[str, str],
) -> dict[str, Any]:
    """
    Construye el snapshot consolidado y atómico del sistema para el consumo de la Single-Page Application (SPA).

    Empaqueta en una sola estructura inmutable el estado completo de la torre de control:
    - Metadatos geográficos y límites de la geocerca metropolitana del Valle de Aburrá.
    - Estado del reloj de simulación monotónico y del clima en el nodo activo.
    - Catálogos de categorías, esquemas dinámicos de fábrica y roles de seguridad RBAC.
    - Métricas globales de torre (drones en vuelo, disponibles, pedidos por estado, logs).
    - Estado serializado de la flota, pedidos, sesiones cinemáticas y bitácora estructurada de eventos.

    Args:
        centro (SistemaCentroControl): Instancia de la torre de control.
        calculador (CalculadorGeodesico): Motor geodésico Haversine.
        reloj (RelojSimulacion): Temporizador monotónico de simulación.
        usuario_activo (Usuario): Usuario que mantiene la sesión operativa en la UI.
        clima_actual (dict[str, Any]): Condiciones meteorológicas vigentes.
        sesiones_vuelo (dict[str, dict[str, Any]]): Sesiones cinemáticas indexadas por dron.
        fuentes_geocodificacion (dict[str, str]): Registro de fuentes cartográficas por pedido.

    Returns:
        dict[str, Any]: Carga útil completa para refrescar la interfaz reactiva sin recargas de página.
    """
    flota_serializada = [
        serializar_dron(d, centro, calculador, clima_actual, sesiones_vuelo)
        for d in centro.flota_drones
    ]

    sesiones_serializadas: dict[str, Any] = {}
    for id_dron, sesion in sesiones_vuelo.items():
        dron_obj = next((d for d in centro.flota_drones if d.id_dron == id_dron), None)
        dist_base = (
            round(
                calculador.calcular_haversine(
                    dron_obj.telemetria.coordenadas, centro.coordenadas_base
                ),
                3,
            )
            if dron_obj and dron_obj.telemetria
            else 0.0
        )
        progreso = (
            calcular_progreso_lineal(dron_obj, sesion, dist_base)
            if dron_obj is not None
            else {
                "fase_ciclo": "EN_PLATAFORMA",
                "progreso_ciclo_pct": 0.0,
                "etapa_actual": 0,
                "abortado": False,
            }
        )
        sesiones_serializadas[id_dron] = {
            **sesion,
            "progreso_lineal": progreso,
        }

    return {
        "ok": True,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "coordenadas_base": list(centro.coordenadas_base),
        "nombre_base": "Aeropuerto Olaya Herrera · Medellín",
        "limites_aburra": {
            "lat_min": calculador.LAT_MIN_ABURRA,
            "lat_max": calculador.LAT_MAX_ABURRA,
            "lon_min": calculador.LON_MIN_ABURRA,
            "lon_max": calculador.LON_MAX_ABURRA,
        },
        "reloj": {
            "tiempo_total_seg": reloj.obtener_tiempo_total_seg(),
            "pausado": reloj.pausado,
        },
        "nodos_clima": list(ServicioClimaAburra.NODOS_ABURRA.keys()),
        "clima": clima_actual,
        "categorias_permitidas": list(Pedido.categorias_permitidas),
        "etiquetas_categoria": ETIQUETAS_CATEGORIA,
        "esquema_fabrica": ESQUEMA_FABRICA,
        "categorias_fabrica": list(FABRICA_DRONES.keys()),
        "roles_permitidos": list(Usuario.ROLES_PERMITIDOS),
        "estados_pedido": list(Pedido.estados_permitidos),
        "estados_motores": ESTADOS_MOTORES_UI,
        "sugerencias_direcciones": SUGERENCIAS_DIRECCIONES,
        "torre_str": str(centro).strip(),
        "torre_repr": repr(centro),
        "metricas": {
            "total_flota": len(centro.flota_drones),
            "disponibles": len(centro.obtener_drones_disponibles()),
            "en_aire": sum(1 for d in flota_serializada if d["en_vuelo_activo"]),
            "emergencia_bateria": sum(
                1 for d in flota_serializada if d["estado_operacional"] == "SIN_BATERIA"
            ),
            "total_pedidos": len(centro.pedidos),
            "pedidos_pendientes": sum(1 for p in centro.pedidos if p.estado == "PENDIENTE"),
            "pedidos_asignados": sum(1 for p in centro.pedidos if p.estado == "ASIGNADO"),
            "pedidos_en_transito": sum(1 for p in centro.pedidos if p.estado == "EN_TRANSITO"),
            "pedidos_completados": sum(1 for p in centro.pedidos if p.estado == "COMPLETADO"),
            "total_logs": len(centro.historial_logs),
        },
        "usuario_activo": {
            "id_usuario": usuario_activo.id_usuario,
            "nombre": usuario_activo.nombre,
            "rol": usuario_activo.rol,
            "str": str(usuario_activo),
        },
        "usuarios": [
            {
                "id_usuario": u.id_usuario,
                "nombre": u.nombre,
                "rol": u.rol,
                "valido": u.validar_usuario(),
                "str": str(u),
                "repr": repr(u),
            }
            for u in centro.usuarios_registrados
        ],
        "flota": flota_serializada,
        "pedidos": [
            serializar_pedido(p, centro, calculador, fuentes_geocodificacion)
            for p in reversed(centro.pedidos)
        ],
        "sesiones_vuelo": sesiones_serializadas,
        "logs": [
            {
                "id_log": log.id_log,
                "fecha_hora": log.fecha_hora,
                "tipo_evento": log.tipo_evento,
                "id_dron": log.id_dron,
                "id_pedido": log.id_pedido,
                "detalles": log.detalles,
                "registro_formateado": log.formatear_registro(),
            }
            for log in reversed(centro.historial_logs)
        ],
    }
