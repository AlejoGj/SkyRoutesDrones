# Módulo de geocodificación de direcciones hacia coordenadas geodésicas (OpenStreetMap Nominatim / Catálogo Local)
# Contexto geográfico: Valle de Aburrá (Antioquia, Colombia)
# Responsable: Módulo de Servicios y Geodesia

from __future__ import annotations
from typing import Protocol, runtime_checkable
import os
import re
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
        "calle 32d": (6.2376, -75.5851),
        "belen": (6.2375, -75.5851),
        "belén": (6.2375, -75.5851),
        "laureles": (6.2425, -75.5925),
        "estadio": (6.2570, -75.5900),
        "cerro nutibara": (6.2360, -75.5800),
        "pueblito paisa": (6.2360, -75.5800),
        "unicentro": (6.2390, -75.5880),
    }

    def __init__(self, calculador: ICalculadorGeodesico | None = None) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        # Normalizar prefijos viales para compatibilidad con el catálogo offline (ej. 'cl 32d' -> 'calle 32d')
        dir_normalizada = direccion
        for patron, reemplazo in ServicioGeocodificadorOSM.MAPA_PREFIJOS_VIALES:
            dir_normalizada = re.sub(patron, reemplazo, dir_normalizada, flags=re.IGNORECASE)

        dir_lower = dir_normalizada.strip().lower()
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
    Incorpora normalización avanzada de nomenclatura colombiana (Calles, Carreras, cruces '#')
    y filtrado defensivo contra degradación de búsqueda a nivel de ciudad.
    """

    URL_NOMINATIM: str = "https://nominatim.openstreetmap.org/search"
    USER_AGENT: str = "SkyRouteDrones-UDEM/2.0 (ingenieria@skyroute.udem.edu.co)"

    MAPA_PREFIJOS_VIALES: list[tuple[str, str]] = [
        (r"\b(cl|cll|c)\.?(?=\s+\d)", "Calle"),
        (r"\b(cra|cr|kra|kr|k)\.?(?=\s+\d)", "Carrera"),
        (r"\b(diag|dg)\.?(?=\s+\d)", "Diagonal"),
        (r"\b(tv|trans|transv)\.?(?=\s+\d)", "Transversal"),
        (r"\b(av|avda)\.?(?=\s+)", "Avenida"),
        (r"\b(cq|circ)\.?(?=\s+\d)", "Circular"),
        (r"\b(autop)\.?(?=\s+)", "Autopista"),
    ]

    PATRON_CUADRICULA: re.Pattern = re.compile(
        r"^(?P<tipo_via>Calle|Carrera|Diagonal|Transversal|Avenida|Circular|Autopista)\s+"
        r"(?P<num_via>[0-9]+[A-Za-z]?(?:\s+(?:sur|este|oeste|norte))?)\s*"
        r"(?:#|no\.?|n°|num\.?|con|\s)\s*"
        r"(?P<num_cruce>[0-9]+[A-Za-z]?(?:\s+(?:sur|este|oeste|norte))?)"
        r"(?:\s*-\s*(?P<placa>[0-9]+))?",
        re.IGNORECASE
    )

    CRUCES_COMPLEMENTARIOS: dict[str, str] = {
        "calle": "Carrera",
        "carrera": "Calle",
        "diagonal": "Transversal",
        "transversal": "Diagonal",
    }

    TIPOS_NO_DESEADOS_SI_BUSCA_VIA: set[str] = {
        "city", "town", "municipality", "administrative", "state",
        "country", "county", "region", "province"
    }

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
        """Enriquece y expande prefijos abreviados de la dirección con el contexto del Valle de Aburrá."""
        texto_limpio = direccion.strip()
        for patron, reemplazo in self.MAPA_PREFIJOS_VIALES:
            texto_limpio = re.sub(patron, reemplazo, texto_limpio, flags=re.IGNORECASE)

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

    def generar_consultas_candidatas(self, direccion: str) -> list[str]:
        """
        Genera una lista jerárquica de consultas candidatas para resolver direcciones colombianas en OSM:
          1. Dirección exacta normalizada (con placa/puerta si se especificó).
          2. Cruce / Intersección vial ('Calle X con Carrera Y, Municipio').
          3. Cruce alternativo ('Calle X y Carrera Y, Municipio').
          4. Vía principal ('Calle X, Municipio').
        """
        texto_normalizado = direccion.strip()
        for patron, reemplazo in self.MAPA_PREFIJOS_VIALES:
            texto_normalizado = re.sub(patron, reemplazo, texto_normalizado, flags=re.IGNORECASE)

        municipios_aburra = (
            "medellin", "medellín", "bello", "envigado", "itagui", "itagüí",
            "sabaneta", "caldas", "la estrella", "copacabana", "girardota", "barbosa"
        )
        mun_encontrado = "Medellín"
        for m in municipios_aburra:
            if m in texto_normalizado.lower():
                mun_encontrado = m.capitalize()
                break

        # Limpiar información redundante de municipio/país para aislar la cuadrícula vial
        texto_base = texto_normalizado
        for m in municipios_aburra:
            texto_base = re.sub(rf",?\s*{m}.*", "", texto_base, flags=re.IGNORECASE)
        texto_base = re.sub(r",?\s*(?:antioquia|colombia|valle de aburr[aá]).*", "", texto_base, flags=re.IGNORECASE).strip().rstrip(",")

        coincidencia = self.PATRON_CUADRICULA.search(texto_base)
        if not coincidencia:
            return [self.normalizar_consulta(direccion)]

        tipo_v = coincidencia.group("tipo_via").capitalize()
        num_v = coincidencia.group("num_via").strip()
        num_c = coincidencia.group("num_cruce").strip()
        placa = coincidencia.group("placa")
        tipo_c = self.CRUCES_COMPLEMENTARIOS.get(tipo_v.lower(), "Carrera")

        candidatos = []
        if placa:
            candidatos.append(f"{tipo_v} {num_v} #{num_c}-{placa}, {mun_encontrado}, Colombia")
        candidatos.append(f"{tipo_v} {num_v} con {tipo_c} {num_c}, {mun_encontrado}, Colombia")
        candidatos.append(f"{tipo_v} {num_v} y {tipo_c} {num_c}, {mun_encontrado}, Colombia")
        candidatos.append(f"{tipo_v} {num_v}, {mun_encontrado}, Colombia")

        vistos = set()
        candidatos_unicos = []
        for c in candidatos:
            if c not in vistos:
                vistos.add(c)
                candidatos_unicos.append(c)
        return candidatos_unicos

    def _es_resultado_valido(self, item: dict, requiere_nivel_via: bool) -> bool:
        """
        Filtro defensivo: Rechaza resultados degradados a nivel de ciudad o departamento
        cuando la consulta original del usuario buscaba una vía o predio específico.
        """
        if not requiere_nivel_via:
            return True

        addresstype = (item.get("addresstype") or "").lower()
        clase = (item.get("class") or "").lower()
        tipo = (item.get("type") or "").lower()

        # Si Nominatim descartó la vía y devolvió la ciudad o municipio completo
        if addresstype in self.TIPOS_NO_DESEADOS_SI_BUSCA_VIA:
            return False
        if clase == "boundary" and tipo in ("administrative", "city"):
            return False
        return True

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        candidatos = self.generar_consultas_candidatas(direccion)
        requiere_nivel_via = any(
            p in direccion.lower()
            for p in ("calle", "carrera", "diagonal", "transversal", "avenida", "cl", "cra", "diag", "tv", "cr", "kr")
        )

        headers = {
            "User-Agent": self.USER_AGENT
        }

        for query in candidatos:
            parametros = {
                "q": query,
                "format": "json",
                "limit": 3,
                "countrycodes": "co",
                "viewbox": f"{self.calculador.LON_MIN_ABURRA},{self.calculador.LAT_MAX_ABURRA},{self.calculador.LON_MAX_ABURRA},{self.calculador.LAT_MIN_ABURRA}",
                "bounded": 1,
                "addressdetails": 1
            }

            try:
                resp = requests.get(self.URL_NOMINATIM, params=parametros, headers=headers, timeout=5)
                if resp.status_code == 200:
                    datos = resp.json()
                    if datos and isinstance(datos, list):
                        for item in datos:
                            if not self._es_resultado_valido(item, requiere_nivel_via):
                                continue

                            lat = round(float(item["lat"]), 6)
                            lon = round(float(item["lon"]), 6)
                            coordenadas = (lat, lon)

                            # Validación de pertenencia obligatoria al Valle de Aburrá (RN-05)
                            self.calculador.validar_coordenada(coordenadas)
                            return coordenadas
            except CoordenadaInvalidaError:
                # Violación de regla de negocio: se relanza para que el usuario conozca que el punto está fuera
                raise
            except Exception:
                # Fallos técnicos/red: se continúa con el siguiente candidato o fallback
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


class ServicioGeocodificadorGoogle(IServicioGeocodificador):
    """
    Servicio de geocodificación mediante Google Maps Geocoding API.
    Ofrece la máxima precisión para la resolución de direcciones con nomenclatura colombiana
    (Calles, Carreras, diagonales, transversales, cruces '#', placas y códigos postales).

    Características:
    - Búsqueda restringida a Colombia (components=country:CO) y delimitada al Valle de Aburrá (bounds).
    - Carga automática de credenciales desde 'GOOGLE_MAPS_API_KEY' o parámetro directo.
    - Cadena de contingencia multinivel: Si la clave no está configurada, hay problemas de cuota
      o fallos de red, delega transparentemente en OpenStreetMap (Nominatim) y en el catálogo local.
    """

    URL_GOOGLE: str = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(
        self,
        api_key: str | None = None,
        calculador: ICalculadorGeodesico | None = None,
        proveedor_fallback: IServicioGeocodificador | None = None
    ) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()
        self.api_key: str = (api_key or os.environ.get("GOOGLE_MAPS_API_KEY", "")).strip()
        self.proveedor_fallback: IServicioGeocodificador = (
            proveedor_fallback if proveedor_fallback is not None else ServicioGeocodificadorOSM(self.calculador)
        )

    def normalizar_consulta(self, direccion: str) -> str:
        """Enriquece la dirección con el contexto metropolitano de Antioquia, Colombia."""
        texto_limpio = direccion.strip()
        texto_lower = texto_limpio.lower()

        municipios_aburra = (
            "medellin", "medellín", "bello", "envigado", "itagui", "itagüí",
            "sabaneta", "caldas", "la estrella", "copacabana", "girardota", "barbosa"
        )
        tiene_municipio = any(m in texto_lower for m in municipios_aburra)

        if not tiene_municipio:
            return f"{texto_limpio}, Medellín, Antioquia, Colombia"
        elif "colombia" not in texto_lower:
            return f"{texto_limpio}, Antioquia, Colombia"
        return texto_limpio

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        query = self.normalizar_consulta(direccion)

        # Si hay API Key configurada, consultar Google Maps Geocoding API
        if self.api_key:
            parametros = {
                "address": query,
                "components": "country:CO",
                "bounds": (
                    f"{self.calculador.LAT_MIN_ABURRA},{self.calculador.LON_MIN_ABURRA}|"
                    f"{self.calculador.LAT_MAX_ABURRA},{self.calculador.LON_MAX_ABURRA}"
                ),
                "key": self.api_key
            }

            try:
                resp = requests.get(self.URL_GOOGLE, params=parametros, timeout=5)
                if resp.status_code == 200:
                    datos = resp.json()
                    status = datos.get("status", "")

                    if status == "OK" and datos.get("results"):
                        resultado = datos["results"][0]
                        loc = resultado["geometry"]["location"]
                        lat = round(float(loc["lat"]), 6)
                        lon = round(float(loc["lng"]), 6)
                        coordenadas = (lat, lon)

                        # Validación obligatoria de permanencia en el Valle de Aburrá (RN-05)
                        self.calculador.validar_coordenada(coordenadas)
                        return coordenadas
                    elif status == "ZERO_RESULTS":
                        pass
            except CoordenadaInvalidaError:
                raise
            except Exception:
                pass

        # Cadena de contingencia multinivel: delegar a OpenStreetMap / Catálogo Local
        try:
            return self.proveedor_fallback.geocodificar_direccion(direccion)
        except GeocodificacionError:
            raise GeocodificacionError(
                direccion,
                f"No se pudieron encontrar coordenadas válidas dentro del área operativa del Valle de Aburrá para: '{direccion}'."
            )

    def obtener_detalle_direccion(self, direccion: str) -> dict:
        coordenadas = self.geocodificar_direccion(direccion)
        fuente = "GOOGLE_MAPS_GEOCODING" if self.api_key else getattr(self.proveedor_fallback, "__class__", type(self)).__name__
        return {
            "direccion_ingresada": direccion,
            "coordenadas": coordenadas,
            "latitud": coordenadas[0],
            "longitud": coordenadas[1],
            "fuente": fuente,
            "dentro_valle_aburra": True
        }


class ServicioGeocodificadorArcGIS(IServicioGeocodificador):
    """
    Servicio de geocodificación mediante Esri ArcGIS World Geocoding Service.
    Ofrece excelente soporte nativo para la nomenclatura vial colombiana (malla vial IGAC)
    sin requerir autenticación obligatoria para consultas puntuales (findAddressCandidates).

    Características:
    - Búsqueda restringida a Colombia (countryCode=COL) y acotada al Valle de Aburrá (searchExtent).
    - Filtrado de calidad por Score (confianza mínima >= 70.0%).
    - Inversión automática de ejes: ArcGIS entrega x=longitud, y=latitud.
    - Cadena de contingencia multinivel hacia OSM / Catálogo Local ante fallos o scores bajos.
    """

    URL_ARCGIS: str = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    SCORE_MINIMO: float = 70.0

    def __init__(
        self,
        calculador: ICalculadorGeodesico | None = None,
        proveedor_fallback: IServicioGeocodificador | None = None,
        score_minimo: float = 70.0
    ) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()
        self.proveedor_fallback: IServicioGeocodificador = (
            proveedor_fallback if proveedor_fallback is not None else ServicioGeocodificadorOSM(self.calculador)
        )
        self.score_minimo: float = float(score_minimo)

    def normalizar_consulta(self, direccion: str) -> str:
        """Enriquece la dirección con el contexto metropolitano de Medellín, Antioquia, Colombia."""
        texto_limpio = direccion.strip()
        texto_lower = texto_limpio.lower()

        municipios_aburra = (
            "medellin", "medellín", "bello", "envigado", "itagui", "itagüí",
            "sabaneta", "caldas", "la estrella", "copacabana", "girardota", "barbosa"
        )
        tiene_municipio = any(m in texto_lower for m in municipios_aburra)

        if not tiene_municipio:
            return f"{texto_limpio}, Medellín, Antioquia, Colombia"
        elif "colombia" not in texto_lower:
            return f"{texto_limpio}, Antioquia, Colombia"
        return texto_limpio

    def geocodificar_direccion(self, direccion: str) -> tuple[float, float]:
        if not isinstance(direccion, str) or not direccion.strip():
            raise GeocodificacionError(str(direccion), "La dirección a geocodificar debe ser una cadena no vacía.")

        query = self.normalizar_consulta(direccion)

        # Delimitar al rectángulo del Valle de Aburrá: xmin, ymin, xmax, ymax (lon_min, lat_min, lon_max, lat_max)
        search_extent = (
            f"{self.calculador.LON_MIN_ABURRA},{self.calculador.LAT_MIN_ABURRA},"
            f"{self.calculador.LON_MAX_ABURRA},{self.calculador.LAT_MAX_ABURRA}"
        )

        params = {
            "SingleLine": query,
            "f": "json",
            "maxLocations": 1,
            "countryCode": "COL",
            "searchExtent": search_extent,
            "outFields": "Match_addr,Addr_type,Score"
        }

        try:
            resp = requests.get(self.URL_ARCGIS, params=params, timeout=5)
            if resp.status_code == 200:
                datos = resp.json()
                candidatos = datos.get("candidates", [])

                if candidatos:
                    mejor_resultado = candidatos[0]
                    score = float(mejor_resultado.get("score", 0.0))

                    if score >= self.score_minimo:
                        coords = mejor_resultado["location"]
                        # ArcGIS retorna x (longitud) e y (latitud)
                        lat = round(float(coords["y"]), 6)
                        lon = round(float(coords["x"]), 6)
                        coordenadas = (lat, lon)

                        # Validación obligatoria de permanencia en el Valle de Aburrá (RN-05)
                        self.calculador.validar_coordenada(coordenadas)
                        return coordenadas
        except CoordenadaInvalidaError:
            raise
        except Exception:
            # Fallos técnicos o de red se absorben para delegar en la contingencia
            pass

        # Cadena de contingencia: delegar a OpenStreetMap / Catálogo Local
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
            "fuente": "ARCGIS_WORLD_GEOCODER",
            "dentro_valle_aburra": True
        }
