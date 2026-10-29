"""Módulo de excepciones de dominio aeronáutico y del sistema."""

from src.excepciones.errores import (
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
    CoordenadaInvalidaError,
    DronError,
    ActualizarEstadoDronError,
    EstadoDronDuplicadoError,
    AsignarTelemetriaError,
    TelemetriaNoAsignadaError,
    DestinoInvalidoError,
    CategoriaDronInvalidoError,
    GeocodificacionError,
)

__all__ = [
    "BateriaInvalidaError",
    "AltitudInvalidaError",
    "EstadoMotorInvalidoError",
    "CoordenadaInvalidaError",
    "DronError",
    "ActualizarEstadoDronError",
    "EstadoDronDuplicadoError",
    "AsignarTelemetriaError",
    "TelemetriaNoAsignadaError",
    "DestinoInvalidoError",
    "CategoriaDronInvalidoError",
    "GeocodificacionError",
]
