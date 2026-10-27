"""Módulo de servicios externos (meteorología, geocodificación OpenStreetMap)."""
from src.servicios.clima import ServicioClimaAburra
from src.servicios.geocodificador import (
    IServicioGeocodificador,
    ServicioGeocodificadorLocal,
    ServicioGeocodificadorOSM,
    ServicioGeocodificadorGoogle,
    ServicioGeocodificadorArcGIS,
)

__all__ = [
    "ServicioClimaAburra",
    "IServicioGeocodificador",
    "ServicioGeocodificadorLocal",
    "ServicioGeocodificadorOSM",
    "ServicioGeocodificadorGoogle",
    "ServicioGeocodificadorArcGIS",
]
