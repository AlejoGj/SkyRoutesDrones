# Módulo de geocodificación de direcciones hacia coordenadas geodésicas (OpenStreetMap Nominatim / Catálogo Local)
# Contexto geográfico: Valle de Aburrá (Antioquia, Colombia)
# Responsable: Módulo de Servicios y Geodesia

from __future__ import annotations
from typing import Protocol, runtime_checkable
import requests
from src.geodesia.calculador import CalculadorGeodesico, ICalculadorGeodesico
from src.excepciones.errores import GeocodificacionError, CoordenadaInvalidaError


@runtime_checkable
class IServicioGeocodificador(Protocol):
    """
    Contrato abstracto / interfaz para proveedores de geocodificación en el Valle de Aburrá.
    Permite desacoplar el orquestador del proveedor técnico real (OSM, Google, Catálogo Local, Mocks).
    """

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        """Convierte una dirección textual en coordenadas (latitud, longitud) validadas dentro de Aburrá."""
        ...

    def obtener_detalle_direccion(self, direccion: str) -> dict:
        """Retorna un diccionario estructurado con coordenadas, dirección y metadatos de validación."""
        ...


class ServicioGeocodificadorLocal(IServicioGeocodificador):
    """
    Proveedor de geocodificación determinista 100% offline basado en catálogo de referencia metropolitana.
    Garantiza cero caídas por red, ideal para pruebas unitarias y entornos sin conexión a internet.
    """

    PUNTOS_REFERENCIA_ABURRA: dict[str, tuple[float, float]] = {
        "parque berrio": (6.2498, -75.5694),
        "el poblado": (6.2089, -75.5684),
        "parque el poblado": (6.2089, -75.5684),
        "centro comercial santafe": (6.1973, -75.5742),
        "universidad de medellin": (6.2319, -75.6105),
        "parque de envigado": (6.1759, -75.5917),
        "parque de bello": (6.3373, -75.5579),
        "parque de sabaneta": (6.1515, -75.6166),
        "aeropuerto olaya herrera": (6.2200, -75.5900),
        "caldas": (6.0917, -75.6358),
        "itagui": (6.1719, -75.6111),
        "copacabana": (6.3467, -75.5089),
        "girardota": (6.3758, -75.4475),
        "barbosa": (6.4383, -75.3314),
    }

    def __init__(self, calculador: ICalculadorGeodesico | None = None) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        dir_lower = direccion.strip().lower()
        for clave, coords in self.PUNTOS_REFERENCIA_ABURRA.items():
            if clave in dir_lower or dir_lower in clave:
                self.calculador.validar_coordenada(coords)
                return coords

        raise GeocodificacionError(
            direccion,
            f"No se encontraron coordenadas en el catálogo local del Valle de Aburrá para: '{direccion}'."
        )

    def obtener_detalle_direccion(self, direccion: str) -> dict:
        coordenadas = self.geocodificar_direccion(direccion)
        return {
            "direccion_ingresada": direccion,
            "coordenadas": coordenadas,
            "latitud": coordenadas[0],
            "longitud": coordenadas[1],
            "fuente": "CATALOGO_LOCAL_ABURRA",
            "dentro_valle_aburra": True
        }


class ServicioGeocodificadorOSM(IServicioGeocodificador):
    """
    Servicio de geocodificación mediante la API pública de OpenStreetMap (Nominatim),
    restringida al viewbox del Valle de Aburrá con colchón de contingencia local.
    """

    URL_NOMINATIM: str = "https://nominatim.openstreetmap.org/search"
    USER_AGENT: str = "SkyRouteDrones-UDEM/2.0 (ingenieria@skyroute.udem.edu.co)"

    def __init__(
        self,
        calculador: ICalculadorGeodesico | None = None,
        proveedor_fallback: IServicioGeocodificador | None = None
    ) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()
        self.proveedor_fallback: IServicioGeocodificador = (
            proveedor_fallback if proveedor_fallback is not None else ServicioGeocodificadorLocal(self.calculador)
        )

    def normalizar_consulta(self, direccion: str) -> str:
        """Enriquece la dirección con el contexto del Valle de Aburrá si no contiene municipio."""
        texto_limpio = direccion.strip()
        texto_lower = texto_limpio.lower()

        municipios_aburra = (
            "medellin", "medellín", "bello", "envigado", "itagui", "itagüí",
            "sabaneta", "caldas", "la estrella", "copacabana", "girardota", "barbosa"
        )
        tiene_municipio = any(m in texto_lower for m in municipios_aburra)

        if not tiene_municipio:
            return f"{texto_limpio}, Medellín, Valle de Aburrá, Colombia"
        elif "colombia" not in texto_lower:
            return f"{texto_limpio}, Antioquia, Colombia"
        return texto_limpio

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        query = self.normalizar_consulta(direccion)

        parametros = {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "co",
            "viewbox": f"{self.calculador.LON_MIN_ABURRA},{self.calculador.LAT_MAX_ABURRA},{self.calculador.LON_MAX_ABURRA},{self.calculador.LAT_MIN_ABURRA}",
            "bounded": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": self.USER_AGENT
        }

        try:
            resp = requests.get(self.URL_NOMINATIM, params=parametros, headers=headers, timeout=5)
            if resp.status_code == 200:
                datos = resp.json()
                if datos and len(datos) > 0:
                    lat = round(float(datos[0]["lat"]), 6)
                    lon = round(float(datos[0]["lon"]), 6)
                    coordenadas = (lat, lon)

                    # Validación de pertenencia obligatoria al Valle de Aburrá (RN-05)
                    self.calculador.validar_coordenada(coordenadas)
                    return coordenadas
        except CoordenadaInvalidaError:
            # Violación de regla de negocio: se relanza para que el usuario conozca que el punto está fuera
            raise
        except Exception:
            # Fallos técnicos/red: se absorben para intentar resolución por fallback
            pass

        # Intento de resolución mediante el proveedor de contingencia local
        try:
            return self.proveedor_fallback.geocodificar_direccion(direccion)
        except GeocodificacionError:
            raise GeocodificacionError(
                direccion,
                f"No se pudieron encontrar coordenadas válidas dentro del área operativa del Valle de Aburrá para: '{direccion}'."
            )

    def obtener_detalle_direccion(self, direccion: str) -> dict:
        coordenadas = self.geocodificar_direccion(direccion)
        return {
            "direccion_ingresada": direccion,
            "coordenadas": coordenadas,
            "latitud": coordenadas[0],
            "longitud": coordenadas[1],
            "fuente": "OPENSTREETMAP_NOMINATIM",
            "dentro_valle_aburra": True
        }
