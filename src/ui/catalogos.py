# Catálogos estáticos, esquemas de fábrica UI y semilla de inicialización base
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

from typing import Any

from src.control.centro_control import (
    FABRICA_DRONES,
    SistemaCentroControl,
    instanciar_dron_desde_fabrica,
)
from src.control.reloj import RelojSimulacion
from src.excepciones.errores import CategoriaDronInvalidoError
from src.telemetria.telemetria import TelemetriaDrone
from src.usuarios.usuario import Usuario

ETIQUETAS_CATEGORIA: dict[str, str] = {
    "ENTREGA_LIGERA": "Entrega Ligera",
    "CARGA_PESADA": "Carga Pesada",
    "VIGILANCIA": "Vigilancia y Seguridad",
    "MAPEO_TOPOGRAFICO": "Mapeo Topográfico",
    "INSPECCION_INFRAESTRUCTURA": "Inspección de Infraestructura",
    "BUSQUEDA_RESCATE": "Búsqueda y Rescate",
}

ESQUEMA_FABRICA: dict[str, dict[str, Any]] = {
    "ENTREGA_LIGERA": {
        "clase": "DronEntregaLigera",
        "velocidad_default": 60.0,
        "modelo_sugerido": "AeroCourier-V4",
        "campos": [
            {"clave": "capacidad_carga_kg", "etiqueta": "Capacidad Máx. (kg)", "tipo": "float", "default": 5.0, "min": 0.5, "max": 15.0, "step": 0.5},
            {"clave": "compartimento_refrigerado", "etiqueta": "Compartimento Refrigerado", "tipo": "bool", "default": True},
            {"clave": "mecanismo_suelta_rapida", "etiqueta": "Mecanismo de Suelta Rápida", "tipo": "bool", "default": True},
        ],
    },
    "CARGA_PESADA": {
        "clase": "DronCargaPesada",
        "velocidad_default": 45.0,
        "modelo_sugerido": "HeavyLifter-OctoX2",
        "campos": [
            {"clave": "volumen_carga_m3", "etiqueta": "Volumen Tolva (m3)", "tipo": "float", "default": 3.0, "min": 0.5, "max": 20.0, "step": 0.5},
            {"clave": "numero_rotores", "etiqueta": "Número de Rotores", "tipo": "int", "default": 8, "min": 4, "max": 16, "step": 2},
            {"clave": "potencia_remolque_w", "etiqueta": "Potencia de Remolque (W)", "tipo": "float", "default": 5200.0, "min": 1000.0, "max": 15000.0, "step": 100.0},
        ],
    },
    "VIGILANCIA": {
        "clase": "DronVigilancia",
        "velocidad_default": 65.0,
        "modelo_sugerido": "SkyGuardian-RTK",
        "campos": [
            {"clave": "resolucion_camara_mp", "etiqueta": "Resolución Cámara (MP)", "tipo": "int", "default": 48, "min": 8, "max": 200, "step": 4},
            {"clave": "vision_nocturna", "etiqueta": "Visión Nocturna Infrarroja", "tipo": "bool", "default": True},
            {"clave": "frecuencia_transmision_ghz", "etiqueta": "Frecuencia Enlace (GHz)", "tipo": "float", "default": 5.8, "min": 2.4, "max": 6.0, "step": 0.1},
        ],
    },
    "MAPEO_TOPOGRAFICO": {
        "clase": "DronMapeo",
        "velocidad_default": 55.0,
        "modelo_sugerido": "TopoLiDAR-Pro",
        "campos": [
            {"clave": "tiene_sensor_lidar", "etiqueta": "Escáner Láser LiDAR", "tipo": "bool", "default": True},
            {"clave": "precision_gps_cm", "etiqueta": "Precisión RTK (cm)", "tipo": "float", "default": 2.5, "min": 0.5, "max": 50.0, "step": 0.5},
            {"clave": "capacidad_almacenamiento_tb", "etiqueta": "Almacenamiento SSD (TB)", "tipo": "float", "default": 2.0, "min": 0.5, "max": 16.0, "step": 0.5},
        ],
    },
    "INSPECCION_INFRAESTRUCTURA": {
        "clase": "DronInspeccion",
        "velocidad_default": 50.0,
        "modelo_sugerido": "SkyInspector-400",
        "campos": [
            {"clave": "zoom_optico_x", "etiqueta": "Zoom Óptico (x)", "tipo": "int", "default": 30, "min": 2, "max": 100, "step": 2},
            {"clave": "rango_sensor_ultrasonico_m", "etiqueta": "Rango Ultrasónico (m)", "tipo": "float", "default": 8.0, "min": 0.5, "max": 30.0, "step": 0.5},
        ],
    },
    "BUSQUEDA_RESCATE": {
        "clase": "DronRescate",
        "velocidad_default": 68.0,
        "modelo_sugerido": "SAR-LifeGuard-II",
        "campos": [
            {"clave": "camara_termica", "etiqueta": "Cámara Termográfica FLIR", "tipo": "bool", "default": True},
            {"clave": "kit_auxilios_equipado", "etiqueta": "Kit Primeros Auxilios", "tipo": "bool", "default": True},
            {"clave": "potencia_altavoz_db", "etiqueta": "Potencia Altavoz SAR (dB)", "tipo": "int", "default": 120, "min": 60, "max": 150, "step": 5},
        ],
    },
}

SUGERENCIAS_DIRECCIONES: list[dict[str, str]] = [
    {"etiqueta": "Parque El Poblado", "direccion": "Parque El Poblado"},
    {"etiqueta": "Universidad de Medellín", "direccion": "Universidad de Medellin"},
    {"etiqueta": "Cra 80 # 30-15, Medellín", "direccion": "Cra 80 # 30-15, Medellín"},
    {"etiqueta": "Parque Berrío", "direccion": "Parque Berrio, Medellin"},
    {"etiqueta": "Centro Comercial Santafé", "direccion": "Centro Comercial Santafe"},
    {"etiqueta": "Parque de Envigado", "direccion": "Parque de Envigado"},
    {"etiqueta": "Parque de Bello", "direccion": "Parque de Bello"},
    {"etiqueta": "Parque de Sabaneta", "direccion": "Parque de Sabaneta"},
]

ESTADOS_MOTORES_UI: list[str] = ["STANDBY", "APAGADOS", "EN_VUELO", "EMERGENCIA"]

DEFINICION_USUARIOS_INICIALES: list[tuple[str, str, str]] = [
    ("USR-01", "Alejandro García Jiménez", "CLIENTE"),
    ("USR-02", "Valery Arboleda Ardila", "OPERADOR_VUELO"),
    ("USR-03", "Juan Manuel Pava Higuita", "ADMINISTRADOR"),
]

DEFINICION_FLOTA_INICIAL: list[tuple[str, dict[str, Any]]] = [
    (
        "ENTREGA_LIGERA",
        {
            "id_dron": "DRON-ENT-01",
            "modelo_aeronave": "AeroCourier-V3",
            "capacidad_carga_kg": 4.5,
            "compartimento_refrigerado": True,
            "mecanismo_suelta_rapida": True,
            "velocidad_promedio_kmh": 60.0,
        },
    ),
    (
        "CARGA_PESADA",
        {
            "id_dron": "DRON-CAR-02",
            "modelo_aeronave": "HeavyLifter-OctoX",
            "volumen_carga_m3": 3.0,
            "numero_rotores": 8,
            "potencia_remolque_w": 5200.0,
            "velocidad_promedio_kmh": 45.0,
        },
    ),
    (
        "VIGILANCIA",
        {
            "id_dron": "DRON-VIG-03",
            "modelo_aeronave": "SkyGuardian-Pro",
            "resolucion_camara_mp": 48,
            "vision_nocturna": True,
            "frecuencia_transmision_ghz": 5.8,
            "velocidad_promedio_kmh": 65.0,
        },
    ),
    (
        "MAPEO_TOPOGRAFICO",
        {
            "id_dron": "DRON-MAP-04",
            "modelo_aeronave": "TopoLiDAR-RTK",
            "tiene_sensor_lidar": True,
            "precision_gps_cm": 2.5,
            "capacidad_almacenamiento_tb": 2.0,
            "velocidad_promedio_kmh": 55.0,
        },
    ),
    (
        "INSPECCION_INFRAESTRUCTURA",
        {
            "id_dron": "DRON-INSP-05",
            "modelo_aeronave": "SkyInspector-300",
            "zoom_optico_x": 30,
            "rango_sensor_ultrasonico_m": 8.0,
            "velocidad_promedio_kmh": 50.0,
        },
    ),
    (
        "BUSQUEDA_RESCATE",
        {
            "id_dron": "DRON-RESC-06",
            "modelo_aeronave": "SAR-LifeGuard",
            "camara_termica": True,
            "kit_auxilios_equipado": True,
            "potencia_altavoz_db": 120,
            "velocidad_promedio_kmh": 68.0,
        },
    ),
]


def crear_clima_inicial_default() -> dict[str, Any]:
    """
    Construye las condiciones meteorológicas predeterminadas para el arranque de la UI.

    Establece valores nominales seguros para el nodo inicial 'El_Poblado' antes de que el
    operador solicite una sincronización en vivo con el servicio meteorológico de Open-Meteo.

    Returns:
        dict[str, Any]: Diccionario representativo del reporte meteorológico:
            - nodo (str): Nombre del sector de referencia ('El_Poblado').
            - temperatura_c (float): Temperatura ambiente nominal (22.0 °C).
            - lluvia_mm (float): Precipitación pluvial (0.0 mm).
            - viento_kmh (float): Velocidad del viento (11.5 km/h).
            - factor_velocidad (float): Coeficiente de modulación de velocidad de crucero (1.0).
            - vuelo_seguro (bool): Bandera booleana de autorización de vuelo (True).
            - consultado_en_vivo (bool): False (indica valor estático de arranque).
    """
    return {
        "nodo": "El_Poblado",
        "temperatura_c": 22.0,
        "lluvia_mm": 0.0,
        "viento_kmh": 11.5,
        "factor_velocidad": 1.0,
        "vuelo_seguro": True,
        "consultado_en_vivo": False,
    }


def inicializar_semilla_sistema(centro: SistemaCentroControl, reloj: RelojSimulacion) -> None:
    """
    Inicializa el estado base canónico del Centro de Control según los requerimientos de entrega.

    Ejecuta el protocolo de arranque operativo:
    1. Registra a los 3 integrantes del equipo con los 3 roles de seguridad RBAC:
       - 'USR-01' Alejandro García Jiménez (CLIENTE).
       - 'USR-02' Valery Arboleda Ardila (OPERADOR_VUELO).
       - 'USR-03' Juan Manuel Pava Higuita (ADMINISTRADOR).
    2. Instancia a través de `FABRICA_DRONES` las 6 aeronaves especializadas de la flota.
    3. Asigna la trama de telemetría nominal a cada dron en el vertipuerto Olaya Herrera:
       - Batería al 100.0%.
       - Altitud en 0.0 m.
       - Motores en reposo ('STANDBY').
       - Coordenadas geográficas base: (6.219603, -75.586792).
    4. Garantiza que la torre inicie con 0 pedidos pre-cargados (sin datos 'hardcodeados').
    5. Registra el evento 'SISTEMA_INICIADO' en la bitácora de auditoría y reinicia el reloj.

    Args:
        centro (SistemaCentroControl): Instancia de la torre de control que recibirá la flota y usuarios.
        reloj (RelojSimulacion): Instancia del temporizador monotónico del sistema.
    """
    for id_usr, nombre, rol in DEFINICION_USUARIOS_INICIALES:
        centro.registrar_usuario(Usuario(id_usr, nombre, rol))

    base = centro.coordenadas_base
    for categoria, kwargs in DEFINICION_FLOTA_INICIAL:
        dron = instanciar_dron_desde_fabrica(categoria, **kwargs)
        dron.asignar_telemetria(
            TelemetriaDrone(
                id_dron=dron.id_dron,
                bateria=100.0,
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=base,
            )
        )
        dron.coordenadas_base = base
        centro.agregar_dron(dron)

    centro.generar_log(
        evento="SISTEMA_INICIADO",
        detalles=(
            f"Torre de Control SkyRoute activa en Olaya Herrera {base} "
            f"con {len(centro.flota_drones)} aeronaves especializadas al 100.0%."
        ),
    )
    reloj.reiniciar()


def extraer_parametros_fabrica(
    datos: dict[str, Any],
    total_flota_actual: int,
) -> tuple[str, str, str, float, float, dict[str, Any]]:
    """
    Valida, normaliza y extrae los parámetros de entrada del formulario de fabricación de drones.

    Aplica el esquema declarativo de la fábrica (`ESQUEMA_FABRICA`) según la categoría elegida,
    garantizando el casteo riguroso de tipos (bool, int, float) para evitar que cadenas de texto
    crudo de los formularios web provoquen errores de tipo en las clases de dominio.

    Args:
        datos (dict[str, Any]): Carga útil enviada en la petición HTTP desde la UI.
        total_flota_actual (int): Número actual de aeronaves registradas (para autogenerar IDs correlativos).

    Returns:
        tuple[str, str, str, float, float, dict[str, Any]]: Tupla con los parámetros normalizados:
            - categoria (str): Identificador en mayúsculas de la categoría en `FABRICA_DRONES`.
            - id_dron (str): Identificador único suministrado o generado ('DRON-XXXX-NN').
            - modelo (str): Denominación del modelo de aeronave.
            - velocidad (float): Velocidad promedio de crucero en km/h.
            - bateria_inicial (float): Nivel inicial de batería en porcentaje [20.0, 100.0].
            - kwargs_especificos (dict[str, Any]): Argumentos técnicos particulares para la subclase.

    Raises:
        CategoriaDronInvalidoError: Si la categoría no existe en el catálogo `FABRICA_DRONES`.
    """
    categoria = str(datos.get("categoria", "")).strip().upper()
    if categoria not in FABRICA_DRONES:
        raise CategoriaDronInvalidoError(categoria)

    id_dron = str(datos.get("id_dron", "")).strip()
    if not id_dron:
        prefijo = categoria[:4]
        id_dron = f"DRON-{prefijo}-{total_flota_actual + 1:02d}"

    esquema = ESQUEMA_FABRICA.get(categoria, {})
    modelo = (
        str(datos.get("modelo_aeronave", "")).strip()
        or esquema.get("modelo_sugerido", "SkyRoute-Custom")
    )
    vel_raw = datos.get("velocidad_promedio_kmh")
    velocidad = (
        float(vel_raw)
        if vel_raw not in (None, "")
        else float(esquema.get("velocidad_default", 55.0))
    )
    bat_raw = datos.get("bateria_inicial")
    bateria_inicial = float(bat_raw) if bat_raw not in (None, "") else 100.0

    kwargs_especificos: dict[str, Any] = {}
    parametros_entrada = datos.get("parametros", {}) or {}
    for campo in esquema.get("campos", []):
        clave = campo["clave"]
        valor_crudo = parametros_entrada.get(clave, datos.get(clave, campo["default"]))
        if campo["tipo"] == "bool":
            if isinstance(valor_crudo, str):
                kwargs_especificos[clave] = valor_crudo.strip().lower() in (
                    "true",
                    "1",
                    "si",
                    "sí",
                    "on",
                )
            else:
                kwargs_especificos[clave] = bool(valor_crudo)
        elif campo["tipo"] == "int":
            kwargs_especificos[clave] = int(float(valor_crudo))
        else:
            kwargs_especificos[clave] = float(valor_crudo)

    return categoria, id_dron, modelo, velocidad, bateria_inicial, kwargs_especificos
