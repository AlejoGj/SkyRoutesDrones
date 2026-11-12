# Gestión de sesiones de vuelo en interfaz, cálculo de progreso lineal y registro de pulsos
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

from typing import Any

from src.flota import Dron
from src.pedidos.pedido import Pedido


def calcular_progreso_lineal(
    dron: Dron,
    sesion: dict[str, Any] | None,
    distancia_a_base_km: float,
) -> dict[str, Any]:
    """
    Calcula el estado y porcentaje de avance sobre el indicador cinemático lineal de 3 etapas.

    Mapea el recorrido continuo de la aeronave en una escala normalizada de 0% a 100%:
    - Etapa 0 (0.0%): Aeronave posicionada en vertipuerto base (Aeropuerto Olaya Herrera).
    - Etapa 1 (0.1% - 50.0%): Vuelo de ida hacia las coordenadas del destino del pedido.
    - Etapa 2 (50.1% - 99.9%): Vuelo de retorno hacia la base tras entrega o cancelación.
    - Etapa 3 (100.0%): Aterrizaje confirmado en plataforma y motores en reposo (STANDBY).

    Gestiona además condiciones críticas de seguridad aeronáutica:
    - Batería agotada (0.0%): Transiciona a fase 'EMERGENCIA_BATERIA' congelando la posición.
    - Misión abortada: Conserva la bandera 'abortado=True' durante el trayecto de retorno.

    Args:
        dron (Dron): Instancia polimórfica de la aeronave bajo seguimiento.
        sesion (dict[str, Any] | None): Diccionario de sesión activa de vuelo en la UI.
        distancia_a_base_km (float): Distancia ortodrómica actual del dron hacia Olaya Herrera.

    Returns:
        dict[str, Any]: Diccionario con las claves de progreso para el indicador visual:
            - fase_ciclo (str): Nombre descriptivo de la fase cinemática actual.
            - progreso_ciclo_pct (float): Porcentaje de avance acotado entre [0.0, 100.0].
            - etapa_actual (int): Número de hito (0: Base, 1: Hacia Destino, 2: Retorno, 3: Completado).
            - abortado (bool): Indica si el vuelo fue interrumpido anticipadamente por el operador.
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


def crear_sesion_base(
    id_dron: str,
    id_pedido: str,
    categoria: str,
    direccion_destino: str,
    coordenadas_origen: tuple[float, float] | list[float],
    coordenadas_destino: tuple[float, float] | list[float],
    distancia_ida_km: float,
    distancia_retorno_km: float,
    ultimo_estado_pulso: str = "ASIGNADO",
    ultimo_progreso_pct: float = 0.0,
    ultima_etapa: int = 0,
    instrumental_activado: str | None = None,
    reporte_despegue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye la estructura de datos estandarizada para rastrear una misión de vuelo en la UI.

    Centraliza las 17 propiedades requeridas por el frontend web para renderizar la cabina
    operativa, la bitácora de pulsos en vivo, la tarjeta de viaje y la certificación de cierre.

    Args:
        id_dron (str): Identificador único de la aeronave asignada (ej. 'DRON-ENT-01').
        id_pedido (str): Identificador único del pedido en tránsito (ej. 'PED-00123').
        categoria (str): Categoría aeronáutica requerida (ej. 'ENTREGA_LIGERA').
        direccion_destino (str): Cadena de dirección legible o representación de coordenadas.
        coordenadas_origen (tuple[float, float] | list[float]): Par (lat, lon) del punto de despegue.
        coordenadas_destino (tuple[float, float] | list[float]): Par (lat, lon) del punto de entrega.
        distancia_ida_km (float): Kilómetros ortodrómicos desde la base al destino.
        distancia_retorno_km (float): Kilómetros ortodrómicos desde el destino de regreso a la base.
        ultimo_estado_pulso (str, optional): Estado cinemático inicial. Defaults to 'ASIGNADO'.
        ultimo_progreso_pct (float, optional): Porcentaje lineal inicial. Defaults to 0.0.
        ultima_etapa (int, optional): Hito del viaje inicial. Defaults to 0.
        instrumental_activado (str | None, optional): Diagnóstico de carga/cámara activada.
        reporte_despegue (dict[str, Any] | None, optional): Payload emitido por `dron.ejecutar_mision()`.

    Returns:
        dict[str, Any]: Diccionario con la sesión inicializada y lista vacía de pulsos históricos.
    """
    return {
        "id_dron": id_dron,
        "id_pedido": id_pedido,
        "categoria": categoria,
        "direccion_destino": direccion_destino,
        "coordenadas_origen": list(coordenadas_origen),
        "coordenadas_destino": list(coordenadas_destino),
        "distancia_ida_total_km": round(max(float(distancia_ida_km), 0.001), 3),
        "distancia_retorno_total_km": round(max(float(distancia_retorno_km), 0.001), 3),
        "tiempo_acumulado_seg": 0.0,
        "instrumental_activado": instrumental_activado,
        "reporte_despegue": reporte_despegue,
        "ultimo_estado_pulso": ultimo_estado_pulso,
        "ultimo_progreso_pct": ultimo_progreso_pct,
        "ultima_etapa": ultima_etapa,
        "abortado": False,
        "completada_en_base": False,
        "certificacion_final": None,
        "pulsos": [],
    }


def crear_sesion_contingencia(
    dron: Dron,
    pedido_ref: Pedido | None,
    coordenadas_base: tuple[float, float],
) -> dict[str, Any]:
    """
    Crea una sesión sintética de contingencia para aeronaves activas sin registro previo.

    Se invoca de forma defensiva si se solicita avanzar la simulación cinemática sobre una
    aeronave que ya se encontraba en vuelo o retorno pero cuyo registro de sesión no existía en memoria.

    Args:
        dron (Dron): Aeronave activa en vuelo.
        pedido_ref (Pedido | None): Pedido asociado a la aeronave si existe.
        coordenadas_base (tuple[float, float]): Coordenadas del vertipuerto de referencia.

    Returns:
        dict[str, Any]: Sesión válida y tipada para no interrumpir el flujo visual de la UI.
    """
    return crear_sesion_base(
        id_dron=dron.id_dron,
        id_pedido=pedido_ref.id_pedido if pedido_ref else "N/A",
        categoria=getattr(dron, "categoria", "ESTANDAR"),
        direccion_destino=(
            pedido_ref.direccion_destino
            if pedido_ref and pedido_ref.direccion_destino
            else "Coordenada objetivo"
        ),
        coordenadas_origen=coordenadas_base,
        coordenadas_destino=(
            pedido_ref.coordenada_destino
            if pedido_ref and pedido_ref.coordenada_destino
            else coordenadas_base
        ),
        distancia_ida_km=1.0,
        distancia_retorno_km=1.0,
        ultimo_estado_pulso="EN_VUELO",
        ultimo_progreso_pct=0.0,
        ultima_etapa=1,
        instrumental_activado="NOMINAL",
    )


def registrar_pulso_en_sesion(
    dron: Dron,
    sesion: dict[str, Any],
    reporte: dict[str, Any],
    paso_seg: float,
    pedido_final: Pedido | None,
) -> dict[str, Any]:
    """
    Registra el avance físico de un pulso cinemático discreto en la bitácora de la sesión.

    Actualiza contadores de tiempo de vuelo, estados operacionales y detecta eventos
    cardinales de la misión aeronáutica:
    - 'LLEGADA_A_DESTINO': Concluye la etapa 1 y prepara el regreso.
    - 'LLEGADA_A_BASE': Genera la certificación formal de misión exitosa (`EXITO`).
    - 'BATERIA_AGOTADA': Dispara el protocolo de emergencia crítica (`EMERGENCIA_BATERIA`).

    Args:
        dron (Dron): Aeronave que experimentó el pulso cinemático.
        sesion (dict[str, Any]): Diccionario de la sesión de vuelo que será mutado.
        reporte (dict[str, Any]): Reporte emitido por `SimuladorVuelo.avanzar_paso_tiempo()`.
        paso_seg (float): Delta temporal aplicado en segundos reales o escalados (Delta t).
        pedido_final (Pedido | None): Pedido vinculado para certificar el estado terminal.

    Returns:
        dict[str, Any]: Diccionario con la trama del pulso cinemático generado para consumo de la UI.
    """
    sesion["tiempo_acumulado_seg"] = round(
        float(sesion.get("tiempo_acumulado_seg", 0.0)) + paso_seg, 1
    )
    estado_rep = reporte["estado"]
    sesion["ultimo_estado_pulso"] = estado_rep

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
        evento_especial = (
            "Destino alcanzado: pedido COMPLETADO e inicio automático de retorno a base."
        )
    elif estado_rep == "LLEGADA_A_BASE":
        sesion["completada_en_base"] = True
        evento_especial = (
            "Aterrizaje exitoso en Olaya Herrera: motores en STANDBY y aeronave DISPONIBLE."
        )
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
    return pulso_item
