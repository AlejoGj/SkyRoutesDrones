# Controlador de interfaz (Puente MVC / Adaptador hacia el Backend POO)
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

import math
import time
from datetime import datetime
from typing import Any

from src.control.centro_control import (
    FABRICA_DRONES,
    SistemaCentroControl,
    instanciar_dron_desde_fabrica,
)
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
from src.servicios.geocodificador import ServicioGeocodificadorArcGIS
from src.telemetria.telemetria import TelemetriaDrone
from src.usuarios.usuario import Usuario


class ControladorSkyRoute:
    """
    Adaptador / Controlador de presentación que comunica el servidor HTTP nativo
    con el modelo de dominio POO (SistemaCentroControl, FABRICA_DRONES, Dron,
    Pedido, SimuladorVuelo, RelojSimulacion, ServicioGeocodificadorArcGIS y
    ServicioClimaAburra) sin modificar ninguna clase del backend.
    """

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

    def __init__(
        self,
        geocodificador: Any | None = None,
        servicio_clima: Any | None = None,
    ) -> None:
        self.calculador = CalculadorGeodesico()
        self.geocodificador = (
            geocodificador
            if geocodificador is not None
            else ServicioGeocodificadorArcGIS(calculador=self.calculador)
        )
        self.servicio_clima = (
            servicio_clima if servicio_clima is not None else ServicioClimaAburra()
        )

        # Inicialización oficial en Aeropuerto Olaya Herrera (6.219603, -75.586792)
        self.centro = SistemaCentroControl(geocodificador=self.geocodificador)
        self.simulador = SimuladorVuelo(
            calculador=self.calculador,
            centro_control=self.centro,
        )
        self.reloj = RelojSimulacion()

        # Estado de sesión de interfaz (sin pedidos hardcodeados)
        self._usuario_activo_id: str = "USR-01"
        self._nodo_clima_activo: str = "El_Poblado"
        self._clima_actual: dict[str, Any] = {
            "nodo": "El_Poblado",
            "temperatura_c": 22.0,
            "lluvia_mm": 0.0,
            "viento_kmh": 11.5,
            "factor_velocidad": 1.0,
            "vuelo_seguro": True,
            "consultado_en_vivo": False,
        }
        self._sesiones_vuelo: dict[str, dict[str, Any]] = {}
        self._fuentes_geocodificacion: dict[str, str] = {}
        self._contador_secuencial: int = 1

        self._inicializar_entorno_base()

    def _inicializar_entorno_base(self) -> None:
        """
        Registra los 3 integrantes del equipo con los 3 roles oficiales y las
        6 aeronaves especializadas en Olaya Herrera al 100%, con 0 pedidos pre-cargados.
        """
        usuarios_iniciales = [
            Usuario("USR-01", "Alejandro García Jiménez", "CLIENTE"),
            Usuario("USR-02", "Valery Arboleda Ardila", "OPERADOR_VUELO"),
            Usuario("USR-03", "Juan Manuel Pava Higuita", "ADMINISTRADOR"),
        ]
        for usuario in usuarios_iniciales:
            self.centro.registrar_usuario(usuario)

        definicion_flota = [
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

        base = self.centro.coordenadas_base
        for categoria, kwargs in definicion_flota:
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
            self.centro.agregar_dron(dron)

        self.centro.generar_log(
            evento="SISTEMA_INICIADO",
            detalles=(
                f"Torre de Control SkyRoute activa en Olaya Herrera {base} "
                f"con {len(self.centro.flota_drones)} aeronaves especializadas al 100.0%."
            ),
        )
        self.reloj.reiniciar()

    # ==========================================================================
    # BÚSQUEDA INTERNA Y UTILIDADES DE SERIALIZACIÓN
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
        raise ValueError(f"No existe un usuario registrado con ID '{id_limpio}'.")

    def _pedido_reservado_para_dron(self, dron: Dron) -> Pedido | None:
        if dron.pedido_activo is not None:
            return dron.pedido_activo
        for pedido in self.centro.pedidos:
            if pedido.dron_asignado is dron and pedido.estado in ("ASIGNADO", "EN_TRANSITO"):
                return pedido
        return None

    def _extraer_atributos_especializados(self, dron: Dron) -> list[dict[str, str]]:
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

    def _calcular_progreso_lineal(
        self,
        dron: Dron,
        sesion: dict[str, Any] | None,
        distancia_a_base_km: float,
    ) -> dict[str, Any]:
        """
        Calcula el progreso sobre el indicador lineal minimalista de 3 etapas:
        0% (Base Olaya Herrera) -> 50% (Destino de Misión) -> 100% (Retorno en Base).
        """
        tele = dron.telemetria
        bateria = tele.bateria if tele else 0.0

        if sesion is None:
            return {
                "fase_ciclo": "EN_PLATAFORMA" if bateria > 0.0 else "EMERGENCIA_BATERIA",
                "progreso_ciclo_pct": 0.0,
                "etapa_actual": 0,
                "abortado": False,
            }

        ultimo_estado = sesion.get("ultimo_estado_pulso", "")
        abortado = bool(sesion.get("abortado", False))
        dist_ida_total = max(float(sesion.get("distancia_ida_total_km", 0.001)), 0.001)
        dist_ret_total = max(float(sesion.get("distancia_retorno_total_km", 0.001)), 0.001)

        if bateria <= 0.0 or ultimo_estado == "BATERIA_AGOTADA":
            return {
                "fase_ciclo": "EMERGENCIA_BATERIA",
                "progreso_ciclo_pct": round(float(sesion.get("ultimo_progreso_pct", 0.0)), 1),
                "etapa_actual": int(sesion.get("ultima_etapa", 1)),
                "abortado": abortado,
            }

        if dron.en_mision and dron.pedido_activo is not None and dron.pedido_activo.coordenada_destino:
            dist_restante = dron.calcular_distancia_a_destino(dron.pedido_activo.coordenada_destino)
            fraccion_ida = max(0.0, min(1.0, 1.0 - (dist_restante / dist_ida_total)))
            pct = round(fraccion_ida * 50.0, 1)
            sesion["ultimo_progreso_pct"] = pct
            sesion["ultima_etapa"] = 1
            return {
                "fase_ciclo": "HACIA_DESTINO",
                "progreso_ciclo_pct": pct,
                "etapa_actual": 1,
                "abortado": False,
            }

        if dron.retornando_a_base:
            fraccion_ret = max(0.0, min(1.0, 1.0 - (distancia_a_base_km / dist_ret_total)))
            pct = round(50.0 + (fraccion_ret * 50.0), 1)
            sesion["ultimo_progreso_pct"] = pct
            sesion["ultima_etapa"] = 2
            return {
                "fase_ciclo": "RETORNANDO_A_BASE",
                "progreso_ciclo_pct": pct,
                "etapa_actual": 2,
                "abortado": abortado,
            }

        if ultimo_estado == "LLEGADA_A_BASE" or sesion.get("completada_en_base"):
            sesion["ultimo_progreso_pct"] = 100.0
            sesion["ultima_etapa"] = 3
            return {
                "fase_ciclo": "RETORNO_COMPLETADO" if abortado else "MISION_COMPLETADA",
                "progreso_ciclo_pct": 100.0,
                "etapa_actual": 3,
                "abortado": abortado,
            }

        return {
            "fase_ciclo": "RESERVADO_EN_PLATAFORMA",
            "progreso_ciclo_pct": 0.0,
            "etapa_actual": 0,
            "abortado": False,
        }

    def _serializar_dron(self, dron: Dron) -> dict[str, Any]:
        tele = dron.telemetria
        base = self.centro.coordenadas_base
        coords = list(tele.coordenadas) if tele else list(base)
        bateria = round(tele.bateria, 1) if tele else 0.0
        altitud = round(tele.altitud, 1) if tele else 0.0
        motores = tele.estado_motores if tele else "SIN_TELEMETRIA"
        categoria = getattr(dron, "categoria", getattr(dron, "CATEGORIA_ESPECIALIZADA", "ESTANDAR"))

        distancia_a_base_km = (
            round(self.calculador.calcular_haversine(tuple(coords), base), 3) if tele else 0.0
        )
        pedido_vinculado = self._pedido_reservado_para_dron(dron)
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

        factor_clima = float(self._clima_actual.get("factor_velocidad", 1.0))
        velocidad_efectiva_kmh = round(dron.velocidad_promedio_kmh * factor_clima, 1)

        distancia_objetivo_km = 0.0
        eta_min = 0.0
        if en_vuelo_mision and dron.pedido_activo and dron.pedido_activo.coordenada_destino:
            distancia_objetivo_km = round(
                dron.calcular_distancia_a_destino(dron.pedido_activo.coordenada_destino), 2
            )
            eta_min = round(
                self.calculador.calcular_tiempo_vuelo_min(distancia_objetivo_km, velocidad_efectiva_kmh), 1
            )
        elif dron.retornando_a_base:
            distancia_objetivo_km = round(distancia_a_base_km, 2)
            eta_min = round(
                self.calculador.calcular_tiempo_vuelo_min(distancia_objetivo_km, velocidad_efectiva_kmh), 1
            )

        sesion = self._sesiones_vuelo.get(dron.id_dron)
        progreso = self._calcular_progreso_lineal(dron, sesion, distancia_a_base_km)
        tasa_bat_km = round(dron.calcular_consumo_estimado(1.0), 2)
        ultimo_completado = getattr(dron, "ultimo_pedido_completado", None)

        return {
            "id_dron": dron.id_dron,
            "modelo_aeronave": dron.modelo_aeronave,
            "clase_python": type(dron).__name__,
            "categoria": categoria,
            "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(categoria, categoria),
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
            "especificaciones": self._extraer_atributos_especializados(dron),
            "ficha_str": str(dron).strip(),
            "ficha_repr": repr(dron),
            "diagnostico_sistemas": dron.inspeccionar_sistemas_especializados(),
            "historial_telemetria": list(dron.historial_telemetria[-25:]),
            "total_tramas_telemetria": len(dron.historial_telemetria),
        }

    def _diagnosticar_candidatos_pedido(self, pedido: Pedido) -> dict[str, Any]:
        """
        Evalúa las aeronaves de la categoría requerida para mostrar al operador la
        distancia de ida, retorno, consumo ida+vuelta y viabilidad exacta antes de asignar.
        """
        base = self.centro.coordenadas_base
        if pedido.coordenada_destino is None:
            return {"distancia_ida_km": 0.0, "distancia_total_km": 0.0, "candidatos": []}

        dist_ida = self.calculador.calcular_haversine(base, pedido.coordenada_destino)
        dist_ret = self.calculador.calcular_haversine(pedido.coordenada_destino, base)
        dist_total = dist_ida + dist_ret

        candidatos = []
        for dron in self.centro.flota_drones:
            if getattr(dron, "categoria", None) != pedido.categoria_requerida:
                continue
            bat = round(dron.telemetria.bateria, 1) if dron.telemetria else 0.0
            d_ida_dron = dron.calcular_distancia_a_destino(pedido.coordenada_destino) if dron.telemetria else dist_ida
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

    def _serializar_pedido(self, pedido: Pedido) -> dict[str, Any]:
        coords = list(pedido.coordenada_destino) if pedido.coordenada_destino else None
        analisis = self._diagnosticar_candidatos_pedido(pedido)
        return {
            "id_pedido": pedido.id_pedido,
            "usuario_id": pedido.usuario_solicitante.id_usuario,
            "usuario_nombre": pedido.usuario_solicitante.nombre,
            "usuario_rol": pedido.usuario_solicitante.rol,
            "categoria_requerida": pedido.categoria_requerida,
            "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(
                pedido.categoria_requerida, pedido.categoria_requerida
            ),
            "coordenada_destino": coords,
            "direccion_destino": pedido.direccion_destino,
            "fuente_geocodificacion": self._fuentes_geocodificacion.get(pedido.id_pedido),
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

    # ==========================================================================
    # SNAPSHOT GENERAL DEL SISTEMA
    # ==========================================================================

    def obtener_estado_completo(self) -> dict[str, Any]:
        usuario_activo = self._buscar_usuario(self._usuario_activo_id)
        flota_serializada = [self._serializar_dron(d) for d in self.centro.flota_drones]

        sesiones_serializadas: dict[str, Any] = {}
        for id_dron, sesion in self._sesiones_vuelo.items():
            dron_obj = next((d for d in self.centro.flota_drones if d.id_dron == id_dron), None)
            dist_base = (
                round(self.calculador.calcular_haversine(dron_obj.telemetria.coordenadas, self.centro.coordenadas_base), 3)
                if dron_obj and dron_obj.telemetria
                else 0.0
            )
            progreso = (
                self._calcular_progreso_lineal(dron_obj, sesion, dist_base)
                if dron_obj is not None
                else {"fase_ciclo": "EN_PLATAFORMA", "progreso_ciclo_pct": 0.0, "etapa_actual": 0, "abortado": False}
            )
            sesiones_serializadas[id_dron] = {
                **sesion,
                "progreso_lineal": progreso,
            }

        return {
            "ok": True,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "coordenadas_base": list(self.centro.coordenadas_base),
            "nombre_base": "Aeropuerto Olaya Herrera · Medellín",
            "limites_aburra": {
                "lat_min": self.calculador.LAT_MIN_ABURRA,
                "lat_max": self.calculador.LAT_MAX_ABURRA,
                "lon_min": self.calculador.LON_MIN_ABURRA,
                "lon_max": self.calculador.LON_MAX_ABURRA,
            },
            "reloj": {
                "tiempo_total_seg": self.reloj.obtener_tiempo_total_seg(),
                "pausado": self.reloj.pausado,
            },
            "nodos_clima": list(ServicioClimaAburra.NODOS_ABURRA.keys()),
            "clima": self._clima_actual,
            "categorias_permitidas": list(Pedido.categorias_permitidas),
            "etiquetas_categoria": self.ETIQUETAS_CATEGORIA,
            "esquema_fabrica": self.ESQUEMA_FABRICA,
            "categorias_fabrica": list(FABRICA_DRONES.keys()),
            "roles_permitidos": list(Usuario.ROLES_PERMITIDOS),
            "estados_pedido": list(Pedido.estados_permitidos),
            "estados_motores": ["STANDBY", "APAGADOS", "EN_VUELO", "EMERGENCIA"],
            "sugerencias_direcciones": self.SUGERENCIAS_DIRECCIONES,
            "torre_str": str(self.centro).strip(),
            "torre_repr": repr(self.centro),
            "metricas": {
                "total_flota": len(self.centro.flota_drones),
                "disponibles": len(self.centro.obtener_drones_disponibles()),
                "en_aire": sum(1 for d in flota_serializada if d["en_vuelo_activo"]),
                "emergencia_bateria": sum(1 for d in flota_serializada if d["estado_operacional"] == "SIN_BATERIA"),
                "total_pedidos": len(self.centro.pedidos),
                "pedidos_pendientes": sum(1 for p in self.centro.pedidos if p.estado == "PENDIENTE"),
                "pedidos_asignados": sum(1 for p in self.centro.pedidos if p.estado == "ASIGNADO"),
                "pedidos_en_transito": sum(1 for p in self.centro.pedidos if p.estado == "EN_TRANSITO"),
                "pedidos_completados": sum(1 for p in self.centro.pedidos if p.estado == "COMPLETADO"),
                "total_logs": len(self.centro.historial_logs),
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
                for u in self.centro.usuarios_registrados
            ],
            "flota": flota_serializada,
            "pedidos": [self._serializar_pedido(p) for p in reversed(self.centro.pedidos)],
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
                for log in reversed(self.centro.historial_logs)
            ],
        }

    # ==========================================================================
    # CLIMA, GEOCODIFICACIÓN Y PREDICCIÓN POLIMÓRFICA (HU-10)
    # ==========================================================================

    def consultar_clima_nodo(self, nodo: str | None = None) -> dict[str, Any]:
        nodo_elegido = (nodo or self._nodo_clima_activo or "El_Poblado").strip()
        if nodo_elegido not in ServicioClimaAburra.NODOS_ABURRA:
            nodo_elegido = "El_Poblado"

        self._nodo_clima_activo = nodo_elegido
        reporte = self.servicio_clima.obtener_condiciones(nodo_elegido)
        reporte["consultado_en_vivo"] = not bool(reporte.get("fallback", False))
        self._clima_actual = reporte

        estado = self.obtener_estado_completo()
        autorizacion = "Vuelo autorizado" if reporte["vuelo_seguro"] else "Alerta meteorológica activa"
        estado["mensaje_operacion"] = (
            f"Clima actualizado en {nodo_elegido}: {reporte['temperatura_c']:.1f} C, "
            f"viento {reporte['viento_kmh']:.1f} km/h, factor {reporte['factor_velocidad'] * 100:.0f}% ({autorizacion})."
        )
        return estado

    def previsualizar_geocodificacion(self, direccion: str) -> dict[str, Any]:
        dir_limpia = str(direccion or "").strip()
        if not dir_limpia or dir_limpia.lower() == "none":
            raise GeocodificacionError("", "La dirección a geocodificar debe ser una cadena no vacía.")
        detalle = self.geocodificador.obtener_detalle_direccion(dir_limpia)
        coords = tuple(detalle["coordenadas"])
        base = self.centro.coordenadas_base
        dist_ida = self.calculador.calcular_haversine(base, coords)
        dist_ret = self.calculador.calcular_haversine(coords, base)
        return {
            "ok": True,
            "direccion_ingresada": detalle["direccion_ingresada"],
            "latitud": round(float(detalle["latitud"]), 6),
            "longitud": round(float(detalle["longitud"]), 6),
            "coordenadas": [round(float(coords[0]), 6), round(float(coords[1]), 6)],
            "fuente": detalle.get("fuente", type(self.geocodificador).__name__),
            "dentro_valle_aburra": bool(detalle.get("dentro_valle_aburra", True)),
            "distancia_ida_km": round(dist_ida, 2),
            "distancia_ida_vuelta_km": round(dist_ida + dist_ret, 2),
        }

    def comparar_viabilidad_polimorfica(self, distancia_km: float) -> dict[str, Any]:
        try:
            distancia = float(distancia_km)
            if not math.isfinite(distancia) or distancia <= 0.0:
                raise ValueError("La distancia de evaluación debe ser un número finito estrictamente mayor a 0.0 km.")
        except (TypeError, ValueError) as err:
            raise ValueError(f"Distancia de evaluación no válida: {err}")

        comparativa = []
        for dron in self.centro.flota_drones:
            pred = dron.predecir_viabilidad_mision(distancia)
            tasa_km = round(dron.calcular_consumo_estimado(1.0), 2)
            categoria = getattr(dron, "categoria", getattr(dron, "CATEGORIA_ESPECIALIZADA", "ESTANDAR"))
            comparativa.append(
                {
                    **pred,
                    "modelo_aeronave": dron.modelo_aeronave,
                    "categoria": categoria,
                    "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(categoria, categoria),
                    "velocidad_promedio_kmh": dron.velocidad_promedio_kmh,
                    "tasa_consumo_bat_km": tasa_km,
                    "disponible": dron.disponible,
                }
            )

        return {
            "ok": True,
            "distancia_evaluada_km": round(distancia, 2),
            "total_aeronaves": len(comparativa),
            "total_viables": sum(1 for item in comparativa if item["mision_viable"]),
            "resultados": comparativa,
        }

    # ==========================================================================
    # GESTIÓN DE USUARIOS, FLOTA, FÁBRICA Y TELEMETRÍA
    # ==========================================================================

    def gestionar_usuario(self, datos: dict[str, Any]) -> dict[str, Any]:
        accion = str(datos.get("accion", "cambiar")).strip().lower()
        if accion == "registrar":
            id_usr = str(datos.get("id_usuario", "")).strip()
            if not id_usr:
                id_usr = f"USR-{len(self.centro.usuarios_registrados) + 1:02d}"
            nuevo = Usuario(
                id_usuario=id_usr,
                nombre=str(datos.get("nombre", "")),
                rol=str(datos.get("rol", "")),
            )
            self.centro.registrar_usuario(nuevo)
            self._usuario_activo_id = nuevo.id_usuario
            self.centro.generar_log(
                evento="USUARIO_REGISTRADO",
                detalles=f"Usuario '{nuevo.nombre}' ({nuevo.id_usuario}) registrado con rol {nuevo.rol}.",
            )
            mensaje = f"Usuario {nuevo.nombre} ({nuevo.id_usuario} · {nuevo.rol}) registrado correctamente."
        else:
            usuario = self._buscar_usuario(str(datos.get("id_usuario", "")))
            self._usuario_activo_id = usuario.id_usuario
            mensaje = f"Sesión operativa activa cambiada a {usuario.nombre} ({usuario.rol})."

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = mensaje
        return estado

    def crear_dron_desde_fabrica(self, datos: dict[str, Any]) -> dict[str, Any]:
        id_dron = str(datos.get("id_dron", "")).strip()
        categoria = str(datos.get("categoria", "")).strip().upper()
        if categoria not in FABRICA_DRONES:
            raise CategoriaDronInvalidoError(
                id_dron=id_dron or "NUEVO_DRON",
                categoria=categoria,
                categorias_permitidas=tuple(FABRICA_DRONES.keys()),
            )

        if not id_dron:
            prefijo = categoria[:4]
            id_dron = f"DRON-{prefijo}-{len(self.centro.flota_drones) + 1:02d}"

        esquema = self.ESQUEMA_FABRICA.get(categoria, {})
        modelo = str(datos.get("modelo_aeronave", "")).strip() or esquema.get("modelo_sugerido", "SkyRoute-Custom")
        vel_raw = datos.get("velocidad_promedio_kmh")
        try:
            velocidad = float(vel_raw) if vel_raw not in (None, "") else float(esquema.get("velocidad_default", 55.0))
            if not math.isfinite(velocidad):
                velocidad = float(esquema.get("velocidad_default", 55.0))
        except (ValueError, TypeError):
            velocidad = float(esquema.get("velocidad_default", 55.0))

        bat_raw = datos.get("bateria_inicial")
        try:
            bateria_inicial = float(bat_raw) if bat_raw not in (None, "") else 100.0
            if not math.isfinite(bateria_inicial):
                bateria_inicial = 100.0
        except (ValueError, TypeError):
            bateria_inicial = 100.0

        kwargs_especificos: dict[str, Any] = {}
        parametros_entrada = datos.get("parametros", {}) or {}
        for campo in esquema.get("campos", []):
            clave = campo["clave"]
            valor_crudo = parametros_entrada.get(clave, datos.get(clave, campo["default"]))
            if campo["tipo"] == "bool":
                if isinstance(valor_crudo, str):
                    kwargs_especificos[clave] = valor_crudo.strip().lower() in ("true", "1", "si", "sí", "on")
                else:
                    kwargs_especificos[clave] = bool(valor_crudo)
            elif campo["tipo"] == "int":
                kwargs_especificos[clave] = int(float(valor_crudo))
            else:
                kwargs_especificos[clave] = float(valor_crudo)

        nuevo_dron = instanciar_dron_desde_fabrica(
            categoria,
            id_dron=id_dron,
            modelo_aeronave=modelo,
            velocidad_promedio_kmh=velocidad,
            **kwargs_especificos,
        )
        base = self.centro.coordenadas_base
        nuevo_dron.asignar_telemetria(
            TelemetriaDrone(
                id_dron=nuevo_dron.id_dron,
                bateria=bateria_inicial,
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=base,
            )
        )
        nuevo_dron.coordenadas_base = base
        if bateria_inicial < 20.0:
            raise ValueError("La batería inicial para dar de alta en la flota activa debe ser al menos 20.0%.")

        self.centro.agregar_dron(nuevo_dron)
        self.centro.generar_log(
            evento="ALTA_DRON_FABRICA",
            id_dron=nuevo_dron.id_dron,
            detalles=(
                f"Aeronave '{nuevo_dron.id_dron}' ({type(nuevo_dron).__name__} · {modelo}) "
                f"instanciada desde FABRICA_DRONES e incorporada en Olaya Herrera ({bateria_inicial:.1f}%)."
            ),
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Aeronave {nuevo_dron.id_dron} ({type(nuevo_dron).__name__}) creada desde fábrica e incorporada."
        )
        estado["dron_enfocado_id"] = nuevo_dron.id_dron
        return estado

    def recargar_bateria_dron(self, id_dron: str, porcentaje: float = 100.0) -> dict[str, Any]:
        dron = self._buscar_dron(id_dron)
        bat_previa = dron.telemetria.bateria if dron.telemetria else 0.0
        try:
            pct_val = float(porcentaje) if porcentaje not in (None, "") else 100.0
            if not math.isfinite(pct_val):
                pct_val = 100.0
        except (ValueError, TypeError):
            pct_val = 100.0
        dron.recargar_bateria(pct_val)
        # Si quedó en coordenadas de aterrizaje forzoso, reposicionar en plataforma de base al recargar al >= 20%
        if dron.disponible and dron.telemetria and dron.telemetria.coordenadas != self.centro.coordenadas_base:
            dron.telemetria.coordenadas = self.centro.coordenadas_base
            dron.telemetria.latitud, dron.telemetria.longitud = self.centro.coordenadas_base

        self.centro.generar_log(
            evento="RECARGA_BATERIA",
            id_dron=dron.id_dron,
            detalles=(
                f"Estación de mantenimiento en base: batería de {dron.id_dron} "
                f"recargada ({bat_previa:.1f}% -> {dron.telemetria.bateria:.1f}%)."
            ),
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Batería de {dron.id_dron} recargada a {dron.telemetria.bateria:.1f}% (disponible={dron.disponible})."
        )
        estado["dron_enfocado_id"] = dron.id_dron
        return estado

    def gestionar_telemetria_dron(self, datos: dict[str, Any]) -> dict[str, Any]:
        accion = str(datos.get("accion", "inyectar")).strip().lower()
        if accion == "refrescar_flota":
            resultado = self.centro.refrescar_datos_flota()
            total = int(resultado)
            estado = self.obtener_estado_completo()
            estado["mensaje_operacion"] = f"Telemetría de {total} aeronaves sincronizada bajo demanda."
            return estado

        dron = self._buscar_dron(str(datos.get("id_dron", "")))
        bateria = float(datos["bateria"]) if datos.get("bateria") not in (None, "") else None
        altitud = float(datos["altitud"]) if datos.get("altitud") not in (None, "") else None
        motores = str(datos["estado_motores"]).strip().upper() if datos.get("estado_motores") else None

        coordenadas = None
        if datos.get("latitud") not in (None, "") and datos.get("longitud") not in (None, ""):
            coordenadas = (float(datos["latitud"]), float(datos["longitud"]))
            self.calculador.validar_coordenada(coordenadas)

        dron.actualizar_telemetria(
            bateria_o_telemetria=bateria,
            altitud=altitud,
            estado_motores=motores,
            coordenadas=coordenadas,
        )
        if dron.telemetria and dron.telemetria.bateria <= 0.0:
            dron.disponible = False

        self.centro.generar_log(
            evento="TRAMA_TELEMETRIA_MANUAL",
            id_dron=dron.id_dron,
            detalles=(
                f"Trama validada en {dron.id_dron}: Bat={dron.telemetria.bateria:.1f}%, "
                f"Alt={dron.telemetria.altitud:.1f} m, Motores={dron.telemetria.estado_motores}, "
                f"GPS={dron.telemetria.coordenadas}."
            ),
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Trama de telemetría validada e inyectada en {dron.id_dron}."
        estado["dron_enfocado_id"] = dron.id_dron
        return estado

    # ==========================================================================
    # DESPACHO DE PEDIDOS, ASIGNACIÓN Y SIMULACIÓN CINEMÁTICA TEMPORAL
    # ==========================================================================

    def registrar_nuevo_pedido(self, datos: dict[str, Any]) -> dict[str, Any]:
        id_pedido = str(datos.get("id_pedido", "")).strip()
        if not id_pedido:
            id_pedido = f"PED-{int(time.time()) % 100000:05d}-{self._contador_secuencial:02d}"
            self._contador_secuencial += 1

        categoria = str(datos.get("categoria_requerida", "ENTREGA_LIGERA")).strip().upper()
        peso_raw = datos.get("peso_carga_kg", 1.5)
        try:
            peso = float(peso_raw) if peso_raw not in ("", None) else 0.0
            if not math.isfinite(peso):
                raise ValueError("El peso de la carga debe ser un número finito.")
        except (ValueError, TypeError) as err:
            raise ValueError(f"Peso de la carga no válido: {err}")
        direccion = str(datos.get("direccion_destino", "")).strip() or None
        id_usuario = str(datos.get("id_usuario") or self._usuario_activo_id)
        usuario = self._buscar_usuario(id_usuario)

        coordenada_destino = None
        fuente_geo = "COORDENADAS_DIRECTAS"
        lat_raw = datos.get("latitud")
        lon_raw = datos.get("longitud")
        if lat_raw not in (None, "") and lon_raw not in (None, ""):
            coordenada_destino = (float(lat_raw), float(lon_raw))
            self.calculador.validar_coordenada(coordenada_destino)
        elif direccion:
            # Consultar metadatos de fuente cuando sea posible antes de delegar en registrar_pedido
            try:
                detalle = self.geocodificador.obtener_detalle_direccion(direccion)
                fuente_geo = str(detalle.get("fuente", type(self.geocodificador).__name__))
            except Exception:
                fuente_geo = type(self.geocodificador).__name__

        nuevo_pedido = Pedido(
            id_pedido=id_pedido,
            usuario_solicitante=usuario,
            categoria_requerida=categoria,
            coordenada_destino=coordenada_destino,
            peso_carga_kg=peso,
            direccion_destino=direccion,
        )
        self.centro.registrar_pedido(nuevo_pedido)
        self._fuentes_geocodificacion[nuevo_pedido.id_pedido] = fuente_geo

        dist_ida = self.calculador.calcular_haversine(
            self.centro.coordenadas_base, nuevo_pedido.coordenada_destino
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Pedido {nuevo_pedido.id_pedido} registrado hacia {nuevo_pedido.coordenada_destino} "
            f"(distancia ida: {dist_ida:.2f} km, ida+vuelta: {dist_ida * 2:.2f} km)."
        )
        estado["pedido_creado_id"] = nuevo_pedido.id_pedido
        return estado

    def asignar_dron_pedido(self, id_pedido: str, id_dron: str | None = None) -> dict[str, Any]:
        pedido = self._buscar_pedido(id_pedido)
        diagnostico_previo = self._diagnosticar_candidatos_pedido(pedido)
        asignado = self.centro.asignar_dron_a_pedido(pedido.id_pedido, id_dron=id_dron)

        if not asignado:
            candidatos = diagnostico_previo["candidatos"]
            if not candidatos:
                motivo = f"No existen aeronaves registradas en la categoría '{pedido.categoria_requerida}'."
            else:
                partes = []
                for c in candidatos:
                    if not c["disponible"]:
                        partes.append(f"{c['id_dron']} ocupado/no disponible ({c['bateria_actual_pct']:.1f}%)")
                    elif not c["apto_bateria"]:
                        partes.append(
                            f"{c['id_dron']} batería insuficiente ({c['bateria_actual_pct']:.1f}% actual vs "
                            f"{c['consumo_ida_vuelta_pct']:.1f}% requerido ida+vuelta)"
                        )
                    else:
                        partes.append(f"{c['id_dron']} no elegible")
                motivo = "Ninguna aeronave cumple disponibilidad y autonomía ida+vuelta: " + "; ".join(partes) + "."
            raise ActualizarEstadoDronError("FLOTA", motivo)

        dron = pedido.dron_asignado
        if dron is not None and pedido.coordenada_destino is not None:
            dist_ida = dron.calcular_distancia_a_destino(pedido.coordenada_destino)
            dist_ret = self.calculador.calcular_haversine(
                pedido.coordenada_destino, self.centro.coordenadas_base
            )
            self._sesiones_vuelo[dron.id_dron] = {
                "id_dron": dron.id_dron,
                "id_pedido": pedido.id_pedido,
                "categoria": pedido.categoria_requerida,
                "direccion_destino": pedido.direccion_destino or f"{pedido.coordenada_destino}",
                "coordenadas_origen": list(self.centro.coordenadas_base),
                "coordenadas_destino": list(pedido.coordenada_destino),
                "distancia_ida_total_km": round(max(dist_ida, 0.001), 3),
                "distancia_retorno_total_km": round(max(dist_ret, 0.001), 3),
                "tiempo_acumulado_seg": 0.0,
                "instrumental_activado": None,
                "reporte_despegue": None,
                "ultimo_estado_pulso": "ASIGNADO",
                "ultimo_progreso_pct": 0.0,
                "ultima_etapa": 0,
                "abortado": False,
                "completada_en_base": False,
                "certificacion_final": None,
                "pulsos": [],
            }

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Asignación exitosa: {dron.id_dron} ({dron.modelo_aeronave}) reservado para {pedido.id_pedido}."
        )
        estado["dron_enfocado_id"] = dron.id_dron if dron else None
        estado["pedido_enfocado_id"] = pedido.id_pedido
        return estado

    def cancelar_pedido(self, id_pedido: str) -> dict[str, Any]:
        pedido = self._buscar_pedido(id_pedido)
        if pedido.estado not in ("PENDIENTE", "ASIGNADO"):
            raise ValueError(
                f"Solo se pueden cancelar pedidos en estado PENDIENTE o ASIGNADO (actual: {pedido.estado})."
            )

        dron = pedido.dron_asignado
        if dron is not None and dron.pedido_activo is None and not dron.retornando_a_base:
            dron.en_mision = False
            if dron.telemetria is not None and dron.telemetria.bateria >= 20.0:
                dron.disponible = True
            self._sesiones_vuelo.pop(dron.id_dron, None)

        pedido.actualizar_estado("CANCELADO")
        self.centro.generar_log(
            evento="PEDIDO_CANCELADO",
            id_dron=dron.id_dron if dron else None,
            id_pedido=pedido.id_pedido,
            detalles=f"Pedido {pedido.id_pedido} cancelado por el operador antes del despegue.",
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Pedido {pedido.id_pedido} cancelado y recursos liberados."
        return estado

    def despegar_mision(
        self,
        id_pedido: str = "",
        modo_despacho: str = "TEMPORAL",
        actualizar_clima: bool = True,
        id_dron: str = "",
    ) -> dict[str, Any]:
        if not id_pedido and id_dron:
            for p in self.centro.pedidos:
                if p.dron_asignado and p.dron_asignado.id_dron == id_dron and p.estado == "ASIGNADO":
                    pedido = p
                    id_pedido = p.id_pedido
                    break

        pedido = self._buscar_pedido(id_pedido)
        if pedido.estado != "ASIGNADO" or pedido.dron_asignado is None:
            raise ValueError(
                f"El pedido '{pedido.id_pedido}' debe estar en estado ASIGNADO con un dron reservado."
            )

        dron = pedido.dron_asignado

        if actualizar_clima:
            clima = self.servicio_clima.obtener_condiciones(self._nodo_clima_activo)
            clima["consultado_en_vivo"] = not bool(clima.get("fallback", False))
            self._clima_actual = clima

        if modo_despacho.strip().upper() == "INSTANTANEO":
            if isinstance(dron, DronEntregaLigera) and not dron.es_apto_carga(pedido.peso_carga_kg):
                dron.en_mision = False
                dron.disponible = True
                pedido.actualizar_estado("CANCELADO")
                raise ActualizarEstadoDronError(
                    dron.id_dron,
                    f"Misión rechazada por sobrepeso: {pedido.peso_carga_kg:.1f} kg excede {dron.capacidad_carga_kg:.1f} kg.",
                )
            exito = self.centro.despachar_mision(pedido.id_pedido)
            if not exito:
                raise ActualizarEstadoDronError(
                    dron.id_dron,
                    f"El centro de control rechazó el despacho instantáneo del pedido {pedido.id_pedido}.",
                )
            dist_ret = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
            sesion = self._sesiones_vuelo.setdefault(dron.id_dron, {})
            sesion.update(
                {
                    "id_dron": dron.id_dron,
                    "id_pedido": pedido.id_pedido,
                    "categoria": pedido.categoria_requerida,
                    "direccion_destino": pedido.direccion_destino or f"{pedido.coordenada_destino}",
                    "coordenadas_origen": list(self.centro.coordenadas_base),
                    "coordenadas_destino": list(pedido.coordenada_destino),
                    "distancia_ida_total_km": max(dist_ret, 0.001),
                    "distancia_retorno_total_km": max(dist_ret, 0.001),
                    "tiempo_acumulado_seg": 0.0,
                    "ultimo_estado_pulso": "RETORNANDO_A_BASE",
                    "ultimo_progreso_pct": 50.0,
                    "ultima_etapa": 2,
                    "pulsos": [],
                }
            )
            estado = self.obtener_estado_completo()
            estado["mensaje_operacion"] = (
                f"Despacho instantáneo ejecutado para {pedido.id_pedido}; {dron.id_dron} quedó en retorno a base."
            )
            estado["dron_enfocado_id"] = dron.id_dron
            return estado

        # Protocolo formal de despegue cinemático temporal (idéntico a ConsolaSkyRoute Opción 4)
        self.reloj.obtener_delta()
        dron.coordenadas_base = self.centro.coordenadas_base
        try:
            reporte_despegue = dron.ejecutar_mision(pedido)
        except Exception as exc:
            # Si falla por sobrepeso o batería agotada previa al despegue, liberar reserva limpia
            dron.en_mision = False
            dron.pedido_activo = None
            if dron.telemetria is not None and dron.telemetria.bateria >= 20.0:
                dron.disponible = True
            pedido.actualizar_estado("CANCELADO")
            self.centro.generar_log(
                evento="DESPEGUE_RECHAZADO",
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                detalles=f"Despegue cancelado por protocolo de seguridad: {exc}",
            )
            raise

        self.centro.generar_log(
            evento="DESPEGUE_MISION",
            id_dron=dron.id_dron,
            id_pedido=pedido.id_pedido,
            detalles=(
                f"Despegue autorizado y exitoso hacia {pedido.coordenada_destino}. "
                f"Distancia objetivo: {reporte_despegue['distancia_objetivo_km']} km. "
                f"Batería inicial: {dron.telemetria.bateria:.1f}%."
            ),
        )

        dist_ida = float(reporte_despegue.get("distancia_objetivo_km", 0.5))
        dist_ret = self.calculador.calcular_haversine(
            pedido.coordenada_destino, self.centro.coordenadas_base
        )
        self._sesiones_vuelo[dron.id_dron] = {
            "id_dron": dron.id_dron,
            "id_pedido": pedido.id_pedido,
            "categoria": pedido.categoria_requerida,
            "direccion_destino": pedido.direccion_destino or f"{pedido.coordenada_destino}",
            "coordenadas_origen": list(dron.telemetria.coordenadas),
            "coordenadas_destino": list(pedido.coordenada_destino),
            "distancia_ida_total_km": round(max(dist_ida, 0.001), 3),
            "distancia_retorno_total_km": round(max(dist_ret, 0.001), 3),
            "tiempo_acumulado_seg": 0.0,
            "instrumental_activado": reporte_despegue.get("instrumental_activado", "NOMINAL"),
            "reporte_despegue": {
                **reporte_despegue,
                "coordenadas_origen": list(reporte_despegue["coordenadas_origen"]),
                "coordenadas_destino": list(reporte_despegue["coordenadas_destino"]),
            },
            "ultimo_estado_pulso": "DESPEGUE_EXITOSO",
            "ultimo_progreso_pct": 0.0,
            "ultima_etapa": 1,
            "abortado": False,
            "completada_en_base": False,
            "certificacion_final": None,
            "pulsos": [],
        }

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Despegue exitoso: {dron.id_dron} en el aire a {dron.telemetria.altitud:.0f} m "
            f"(Instrumental: {reporte_despegue.get('instrumental_activado', 'NOMINAL')})."
        )
        estado["dron_enfocado_id"] = dron.id_dron
        estado["reporte_despegue"] = self._sesiones_vuelo[dron.id_dron]["reporte_despegue"]
        return estado

    def avanzar_simulacion(
        self,
        id_dron: str | None = None,
        delta_t: float = 30.0,
        usar_reloj_real: bool = False,
        escala_tiempo: float = 15.0,
    ) -> dict[str, Any]:
        """
        Avanza un pulso temporal en un dron específico o en toda la flota activa
        mediante SimuladorVuelo + RelojSimulacion + factor climático vigente.
        """
        delta_reloj = self.reloj.obtener_delta()
        if usar_reloj_real:
            try:
                factor_escala = float(escala_tiempo)
                if not math.isfinite(factor_escala):
                    factor_escala = 1.0
            except (ValueError, TypeError):
                factor_escala = 1.0
            factor_escala = max(0.1, min(100.0, factor_escala))
            if factor_escala == 1.0:
                paso_seg = max(0.5, min(120.0, delta_reloj))
            else:
                paso_seg = max(1.0, min(120.0, delta_reloj * factor_escala))
        else:
            try:
                dt_val = float(delta_t)
                if not math.isfinite(dt_val):
                    dt_val = 30.0
            except (ValueError, TypeError):
                dt_val = 30.0
            paso_seg = max(0.5, min(3600.0, dt_val))

        factor_clima = float(self._clima_actual.get("factor_velocidad", 1.0))

        objetivos: list[Dron] = []
        if id_dron:
            objetivos = [self._buscar_dron(id_dron)]
        else:
            objetivos = [
                d for d in self.centro.flota_drones if (d.en_mision and d.pedido_activo is not None) or d.retornando_a_base
            ]

        pulsos_emitidos: list[dict[str, Any]] = []
        for dron in objetivos:
            estaba_activo = (dron.en_mision and dron.pedido_activo is not None) or dron.retornando_a_base
            if not estaba_activo:
                continue

            pedido_ref = dron.pedido_activo or getattr(dron, "ultimo_pedido_completado", None)
            reporte = self.simulador.avanzar_paso_tiempo(
                dron=dron,
                delta_t=paso_seg,
                factor_clima=factor_clima,
            )

            sesion = self._sesiones_vuelo.setdefault(
                dron.id_dron,
                {
                    "id_dron": dron.id_dron,
                    "id_pedido": pedido_ref.id_pedido if pedido_ref else "N/A",
                    "categoria": getattr(dron, "categoria", "ESTANDAR"),
                    "direccion_destino": (
                        pedido_ref.direccion_destino
                        if pedido_ref and pedido_ref.direccion_destino
                        else "Coordenada objetivo"
                    ),
                    "coordenadas_origen": list(self.centro.coordenadas_base),
                    "coordenadas_destino": (
                        list(pedido_ref.coordenada_destino)
                        if pedido_ref and pedido_ref.coordenada_destino
                        else list(self.centro.coordenadas_base)
                    ),
                    "distancia_ida_total_km": 1.0,
                    "distancia_retorno_total_km": 1.0,
                    "tiempo_acumulado_seg": 0.0,
                    "instrumental_activado": "NOMINAL",
                    "reporte_despegue": None,
                    "ultimo_estado_pulso": "EN_VUELO",
                    "ultimo_progreso_pct": 0.0,
                    "ultima_etapa": 1,
                    "abortado": False,
                    "completada_en_base": False,
                    "certificacion_final": None,
                    "pulsos": [],
                },
            )

            sesion["tiempo_acumulado_seg"] = round(float(sesion.get("tiempo_acumulado_seg", 0.0)) + paso_seg, 1)
            sesion["ultimo_estado_pulso"] = reporte["estado"]

            estado_rep = reporte["estado"]
            if dron.en_mision and dron.pedido_activo is not None:
                fase_texto = "VUELO A DESTINO"
            elif dron.retornando_a_base:
                fase_texto = "RETORNO A BASE"
            elif estado_rep == "BATERIA_AGOTADA":
                fase_texto = "ATERRIZAJE FORZOSO"
            else:
                fase_texto = "ATERRIZADO EN BASE"

            evento_especial = None
            if estado_rep == "LLEGADA_A_DESTINO":
                evento_especial = "Destino alcanzado: pedido COMPLETADO e inicio automático de retorno a base."
            elif estado_rep == "LLEGADA_A_BASE":
                sesion["completada_en_base"] = True
                pedido_final = pedido_ref or self._buscar_pedido_por_id_seguro(sesion.get("id_pedido"))
                evento_especial = "Aterrizaje exitoso en Olaya Herrera: motores en STANDBY y aeronave DISPONIBLE."
                sesion["certificacion_final"] = {
                    "resultado": "EXITO",
                    "titulo": "Misión Finalizada con Éxito",
                    "tiempo_total_seg": sesion["tiempo_acumulado_seg"],
                    "tiempo_total_min": round(sesion["tiempo_acumulado_seg"] / 60.0, 1),
                    "bateria_final_pct": round(dron.telemetria.bateria, 1),
                    "odometro_total_km": round(dron.kilometraje_total_km, 2),
                    "disponibilidad_dron": "DISPONIBLE EN BASE" if dron.disponible else "OCUPADO",
                    "estado_pedido": pedido_final.estado if pedido_final else "COMPLETADO",
                }
            elif estado_rep == "BATERIA_AGOTADA":
                pedido_final = pedido_ref or self._buscar_pedido_por_id_seguro(sesion.get("id_pedido"))
                evento_especial = (
                    f"Emergencia crítica: batería agotada (0.0%). Aterrizaje forzoso en "
                    f"({dron.telemetria.coordenadas[0]:.4f}, {dron.telemetria.coordenadas[1]:.4f})."
                )
                sesion["certificacion_final"] = {
                    "resultado": "EMERGENCIA_BATERIA",
                    "titulo": "Misión Interrumpida por Emergencia Crítica: Batería Agotada (0.0%)",
                    "tiempo_total_seg": sesion["tiempo_acumulado_seg"],
                    "tiempo_total_min": round(sesion["tiempo_acumulado_seg"] / 60.0, 1),
                    "bateria_final_pct": 0.0,
                    "odometro_total_km": round(dron.kilometraje_total_km, 2),
                    "disponibilidad_dron": "NO DISPONIBLE / EMERGENCIA",
                    "estado_pedido": pedido_final.estado if pedido_final else "EN_TRANSITO",
                }

            pulso_item = {
                "id_dron": dron.id_dron,
                "indice": len(sesion["pulsos"]) + 1,
                "t_seg": sesion["tiempo_acumulado_seg"],
                "delta_t_seg": round(paso_seg, 1),
                "fase": fase_texto,
                "coordenadas": [
                    round(dron.telemetria.coordenadas[0], 5),
                    round(dron.telemetria.coordenadas[1], 5),
                ],
                "delta_km": reporte["delta_km"],
                "distancia_restante_km": round(reporte["distancia_restante_km"], 2),
                "eta_restante_min": reporte["eta_restante_min"],
                "bateria_pct": round(dron.telemetria.bateria, 1),
                "estado": estado_rep,
                "evento_especial": evento_especial,
            }
            sesion["pulsos"].append(pulso_item)
            pulsos_emitidos.append(pulso_item)

        estado = self.obtener_estado_completo()
        estado["pulsos_emitidos"] = pulsos_emitidos
        estado["delta_aplicado_seg"] = round(paso_seg, 1)
        if pulsos_emitidos:
            ult = pulsos_emitidos[-1]
            if ult["evento_especial"]:
                estado["mensaje_operacion"] = ult["evento_especial"]
        return estado

    def _buscar_pedido_por_id_seguro(self, id_pedido: str | None) -> Pedido | None:
        if not id_pedido:
            return None
        for p in self.centro.pedidos:
            if p.id_pedido == id_pedido:
                return p
        return None

    def ordenar_retorno_base(self, id_dron: str) -> dict[str, Any]:
        dron = self._buscar_dron(id_dron)
        pedido_cancelado_id = None
        if dron.pedido_activo is not None and dron.pedido_activo.estado == "EN_TRANSITO":
            pedido_cancelado_id = dron.pedido_activo.id_pedido
            dron.pedido_activo.actualizar_estado("CANCELADO")
            dron.pedido_activo = None

        exito = self.centro.gestionar_retorno_a_base(dron.id_dron)
        if not exito:
            raise ActualizarEstadoDronError(
                dron.id_dron,
                "La aeronave no se encuentra en una misión activa para ordenar retorno a base.",
            )

        dist_base = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
        sesion = self._sesiones_vuelo.setdefault(dron.id_dron, {})
        sesion["abortado"] = True
        sesion["distancia_retorno_total_km"] = round(max(dist_base, 0.05), 3)
        sesion["ultimo_estado_pulso"] = "RETORNANDO_A_BASE"

        estado = self.obtener_estado_completo()
        sufijo = f" (pedido {pedido_cancelado_id} marcado CANCELADO)" if pedido_cancelado_id else ""
        estado["mensaje_operacion"] = (
            f"Retorno obligatorio a Olaya Herrera activado para {dron.id_dron} "
            f"({dist_base:.2f} km restantes){sufijo}."
        )
        return estado

    def finalizar_retorno_manual(self, id_dron: str) -> dict[str, Any]:
        dron = self._buscar_dron(id_dron)
        dron.finalizar_retorno_en_base()
        if dron.telemetria is not None:
            dron.actualizar_telemetria(
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=self.centro.coordenadas_base,
            )
        sesion = self._sesiones_vuelo.get(dron.id_dron)
        if sesion is not None:
            sesion["completada_en_base"] = True
            sesion["ultimo_estado_pulso"] = "LLEGADA_A_BASE"
        self.centro.generar_log(
            evento="ATERRIZAJE_MANUAL_BASE",
            id_dron=dron.id_dron,
            detalles=f"Aterrizaje manual validado en Olaya Herrera para {dron.id_dron}.",
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Aterrizaje manual completado: {dron.id_dron} disponible en base."
        return estado

    def controlar_reloj(self, accion: str) -> dict[str, Any]:
        acc = accion.strip().lower()
        if acc == "reiniciar":
            self.reloj.reiniciar()
            self.reloj.pausado = False
            msg = "Reloj de simulación reiniciado a 0.0 s."
        elif acc == "pausar":
            self.reloj.pausado = True
            msg = "Reloj de simulación en pausa."
        elif acc == "reanudar":
            self.reloj.obtener_delta()
            self.reloj.pausado = False
            msg = "Reloj de simulación reanudado."
        else:
            raise ValueError(f"Acción de reloj no reconocida: '{accion}'.")

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = msg
        return estado

    # ==========================================================================
    # TOUR AUTOMATIZADO END-TO-END (OPCIÓN 7 DE CONSOLASKYROUTE)
    # ==========================================================================

    def preparar_tour_guiado(self) -> dict[str, Any]:
        """
        Ejecuta los pasos preparatorios de la Opción 7 de ConsolaSkyRoute:
        1) Verifica batería en ENTREGA_LIGERA (recarga al 100% si está < 35% o en 0%).
        2) Registra pedido con dirección humana 'Parque El Poblado' (1.8 kg).
        3) Asigna aeronave compatible validando autonomía ida+vuelta.
        4) Despega motores e inicia telemetría de vuelo para que la UI anime cada pulso Delta t=25s.
        """
        pasos_tour: list[str] = []

        for d in self.centro.flota_drones:
            if (
                getattr(d, "categoria", None) == "ENTREGA_LIGERA"
                and not d.en_mision
                and not d.retornando_a_base
                and d.telemetria is not None
                and d.telemetria.bateria < 35.0
            ):
                bat_ant = d.telemetria.bateria
                d.recargar_bateria(100.0)
                d.telemetria.coordenadas = self.centro.coordenadas_base
                pasos_tour.append(
                    f"Mantenimiento preventivo en base: {d.id_dron} recargado ({bat_ant:.1f}% -> 100.0%)."
                )

        id_demo = f"DEMO-{int(time.time()) % 10000:04d}-{self._contador_secuencial:02d}"
        self._contador_secuencial += 1
        cliente = self._buscar_usuario("USR-01")

        try:
            detalle = self.geocodificador.obtener_detalle_direccion("Parque El Poblado")
            fuente = str(detalle.get("fuente", type(self.geocodificador).__name__))
        except Exception:
            fuente = type(self.geocodificador).__name__

        pedido = Pedido(
            id_pedido=id_demo,
            usuario_solicitante=cliente,
            categoria_requerida="ENTREGA_LIGERA",
            coordenada_destino=None,
            direccion_destino="Parque El Poblado",
            peso_carga_kg=1.8,
        )
        self.centro.registrar_pedido(pedido)
        self._fuentes_geocodificacion[pedido.id_pedido] = fuente
        pasos_tour.append(
            f"Paso 1: Pedido {pedido.id_pedido} geocodificado hacia 'Parque El Poblado' -> {pedido.coordenada_destino} ({fuente})."
        )

        self.asignar_dron_pedido(pedido.id_pedido)
        dron = pedido.dron_asignado
        pasos_tour.append(
            f"Paso 2: Aeronave compatible {dron.id_dron} ({dron.modelo_aeronave}) vinculada tras validar ida y retorno."
        )

        estado_despegue = self.despegar_mision(pedido.id_pedido, modo_despacho="TEMPORAL", actualizar_clima=True)
        pasos_tour.append(
            f"Paso 3: Despegue autorizado a 30 m; iniciando integración cinemática temporal con pulsos Delta t = 25 s."
        )

        estado_despegue["tour_guiado"] = {
            "id_pedido": pedido.id_pedido,
            "id_dron": dron.id_dron,
            "delta_t_sugerido": 25.0,
            "pasos_ejecutados": pasos_tour,
        }
        estado_despegue["mensaje_operacion"] = (
            f"Tour End-to-End iniciado: {pedido.id_pedido} en vuelo con {dron.id_dron} hacia Parque El Poblado."
        )
        return estado_despegue

    # ==========================================================================
    # CLASIFICACIÓN DE EXCEPCIONES DE DOMINIO (RF-02)
    # ==========================================================================

    @staticmethod
    def formatear_excepcion(exc: Exception) -> dict[str, Any]:
        mapa_reglas: tuple[tuple[type[Exception], str], ...] = (
            (BateriaInvalidaError, "Regla de Negocio #2 · Batería [0.0, 100.0]%"),
            (AltitudInvalidaError, "Regla de Negocio #3 · Techo UAEAC [0.0, 120.0] m"),
            (EstadoMotorInvalidoError, "Regla de Negocio #4 · Coherencia Motores vs Altitud"),
            (CoordenadaInvalidaError, "Regla de Negocio #5 · Polígono Valle de Aburrá"),
            (GeocodificacionError, "Regla de Negocio #5 · Geocodificación Aburrá"),
            (DestinoInvalidoError, "Regla de Negocio #5 · Coordenada Destino"),
            (CategoriaDronInvalidoError, "Regla de Negocio #8 · Categorías Autorizadas"),
            (ActualizarEstadoDronError, "Regla de Negocio #9 · Control Operacional y Autonomía"),
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
