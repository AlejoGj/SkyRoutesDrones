# Traductor de excepciones de dominio POO a respuestas HTTP/JSON estructuradas (RF-02)
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

from typing import Any

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

MAPA_REGLAS_NEGOCIO: tuple[tuple[type[Exception], str], ...] = (
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


def formatear_excepcion_dominio(exc: Exception) -> dict[str, Any]:
    """
    Convierte una excepción de dominio POO hacia un DTO estructurado en JSON con trazabilidad normativa (RF-02).

    Permite que la API HTTP transmita fallos de validación o violaciones de seguridad aeronáutica
    hacia la interfaz web (`app.js`) sin colapsar el proceso del servidor ni exponer trazas de error
    ininteligibles al usuario final.

    Mapea automáticamente las excepciones hacia su Regla de Negocio correspondiente:
    - BateriaInvalidaError -> Regla de Negocio #2 (rango porcentual de batería [0.0, 100.0]%).
    - AltitudInvalidaError -> Regla de Negocio #3 (techo de vuelo legal UAEAC [0.0, 120.0] m).
    - EstadoMotorInvalidoError -> Regla de Negocio #4 (coherencia física entre altitud y motores).
    - CoordenadaInvalidaError -> Regla de Negocio #5 (geocerca del Valle de Aburrá).
    - GeocodificacionError -> Regla de Negocio #5 (resolución cartográfica metropolitana).
    - CategoriaDronInvalidoError -> Regla de Negocio #8 (categorías de dron autorizadas).
    - ActualizarEstadoDronError -> Regla de Negocio #9 (control de disponibilidad y autonomía de circuito).

    Args:
        exc (Exception): Instancia de la excepción capturada durante la ejecución de un caso de uso.

    Returns:
        dict[str, Any]: Diccionario con la estructura de error estandarizada:
            - ok (bool): False.
            - error_tipo (str): Nombre de la clase de la excepción (ej. 'BateriaInvalidaError').
            - mensaje (str): Mensaje descriptivo del motivo del rechazo.
            - regla_negocio (str): Etiqueta normativa asociada a la regla infringida.
    """
    regla = "Validación de Dominio"
    for clase_exc, etiqueta_regla in MAPA_REGLAS_NEGOCIO:
        if isinstance(exc, clase_exc):
            regla = etiqueta_regla
            break

    return {
        "ok": False,
        "error_tipo": type(exc).__name__,
        "mensaje": str(exc),
        "regla_negocio": regla,
    }
