# Script de pruebas unitarias para el servicio de geocodificación OpenStreetMap Nominatim
# Responsable: Módulo de Servicios y Geodesia (UDEM APOO 2026-2)

import unittest
from unittest.mock import patch, MagicMock
from src.servicios.geocodificador import (
    IServicioGeocodificador,
    ServicioGeocodificadorLocal,
    ServicioGeocodificadorOSM,
    ServicioGeocodificadorGoogle,
    ServicioGeocodificadorArcGIS,
)
from src.control.centro_control import SistemaCentroControl
from src.pedidos.pedido import Pedido
from src.usuarios.usuario import Usuario
from src.geodesia.calculador import CalculadorGeodesico
from src.excepciones.errores import GeocodificacionError, CoordenadaInvalidaError


class TestIServicioGeocodificadorProtocol(unittest.TestCase):
    """Verifica que las implementaciones cumplan con el contrato IServicioGeocodificador (Protocol)."""

    def test_implementaciones_cumplen_protocolo(self):
        local_geo = ServicioGeocodificadorLocal()
        osm_geo = ServicioGeocodificadorOSM()
        google_geo = ServicioGeocodificadorGoogle()
        arcgis_geo = ServicioGeocodificadorArcGIS()

        self.assertIsInstance(local_geo, IServicioGeocodificador)
        self.assertIsInstance(osm_geo, IServicioGeocodificador)
        self.assertIsInstance(google_geo, IServicioGeocodificador)
        self.assertIsInstance(arcgis_geo, IServicioGeocodificador)


class TestServicioGeocodificadorLocal(unittest.TestCase):
    """Pruebas unitarias para el proveedor 100% offline y determinista."""

    def setUp(self):
        self.local = ServicioGeocodificadorLocal()

    def test_resolucion_puntos_locales_conocidos(self):
        poblado = self.local.geocodificar_direccion("Parque El Poblado")
        self.assertEqual(poblado, (6.2089, -75.5684))

        envigado = self.local.geocodificar_direccion("Parque de Envigado")
        self.assertEqual(envigado, (6.1759, -75.5917))

    def test_detalle_direccion_local(self):
        detalle = self.local.obtener_detalle_direccion("Sabaneta")
        self.assertEqual(detalle["fuente"], "CATALOGO_LOCAL_ABURRA")
        self.assertTrue(detalle["dentro_valle_aburra"])
        self.assertEqual(detalle["coordenadas"], (6.1515, -75.6166))

    def test_direccion_desconocida_lanza_geocodificacion_error(self):
        with self.assertRaises(GeocodificacionError):
            self.local.geocodificar_direccion("Barrio Inexistente 999")

    def test_direccion_vacia_lanza_geocodificacion_error(self):
        with self.assertRaises(GeocodificacionError):
            self.local.geocodificar_direccion("")


class TestServicioGeocodificadorOSM(unittest.TestCase):
    def setUp(self):
        self.calculador = CalculadorGeodesico()
        self.geocodificador = ServicioGeocodificadorOSM(calculador=self.calculador)

    @patch('requests.get')
    def test_geocodificacion_osm_exitosa(self, mock_get):
        """Verifica que una respuesta válida de OpenStreetMap retorne las coordenadas validadas."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "6.244200",
                "lon": "-75.581200",
                "display_name": "Calle 44 (San Juan), Medellín, Valle de Aburrá, Colombia"
            }
        ]
        mock_get.return_value = mock_response

        coords = self.geocodificador.geocodificar_direccion("Calle 44 # 50-10, Medellin")

        self.assertIsInstance(coords, tuple)
        self.assertEqual(len(coords), 2)
        self.assertAlmostEqual(coords[0], 6.2442, places=4)
        self.assertAlmostEqual(coords[1], -75.5812, places=4)

        # Verificar parámetros enviados a la API de Nominatim
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"]["countrycodes"], "co")
        self.assertEqual(kwargs["params"]["bounded"], 1)
        self.assertIn("User-Agent", kwargs["headers"])

    @patch('requests.get')
    def test_geocodificacion_fuera_del_valle_lanza_coordenada_invalida(self, mock_get):
        """Verifica que si la API retorna un punto fuera del Valle de Aburrá (ej. Bogotá), se rechace."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "4.711000",
                "lon": "-74.072100",
                "display_name": "Plaza de Bolívar, Bogotá, Colombia"
            }
        ]
        mock_get.return_value = mock_response

        with self.assertRaises(CoordenadaInvalidaError):
            self.geocodificador.geocodificar_direccion("Plaza de Bolívar, Bogotá")

    def test_direccion_vacia_lanza_geocodificacion_error(self):
        """Verifica que direcciones vacías o solo con espacios sean rechazadas con GeocodificacionError."""
        with self.assertRaises(GeocodificacionError):
            self.geocodificador.geocodificar_direccion("")

        with self.assertRaises(GeocodificacionError):
            self.geocodificador.geocodificar_direccion("   ")

    @patch('requests.get')
    def test_direccion_no_encontrada_lanza_geocodificacion_error(self, mock_get):
        """Verifica que direcciones que no existen ni en OSM ni en catálogo lancen GeocodificacionError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []  # Sin resultados
        mock_get.return_value = mock_response

        with self.assertRaises(GeocodificacionError):
            self.geocodificador.geocodificar_direccion("LugarInexistente12345XYZ")

    def test_contingencia_catalogo_puntos_referencia(self):
        """Verifica que puntos icónicos del Valle se resuelvan incluso ante contingencias de red."""
        coords = self.geocodificador.geocodificar_direccion("Parque Berrio")
        self.assertIsInstance(coords, tuple)
        self.assertAlmostEqual(coords[0], 6.2498, places=3)
        self.assertAlmostEqual(coords[1], -75.5694, places=3)

    @patch('requests.get')
    def test_obtener_detalle_direccion(self, mock_get):
        """Verifica el formato del reporte estructurado de geocodificación."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"lat": "6.208900", "lon": "-75.568400", "display_name": "El Poblado, Medellín"}
        ]
        mock_get.return_value = mock_response

        detalle = self.geocodificador.obtener_detalle_direccion("Parque El Poblado")

        self.assertIn("direccion_ingresada", detalle)
        self.assertIn("coordenadas", detalle)
        self.assertIn("latitud", detalle)
        self.assertIn("longitud", detalle)
        self.assertTrue(detalle["dentro_valle_aburra"])

    def test_normalizacion_nomenclatura_colombiana(self):
        """Verifica que 'Cl' y 'Cra' se expandan y se generen consultas con cruces viales."""
        candidatos = self.geocodificador.generar_consultas_candidatas("Cl 32D # 65C-81, Medellin, Antioquia, Colombia")
        self.assertGreaterEqual(len(candidatos), 3)
        # Debe contener la calle principal y el cruce con Carrera
        self.assertTrue(any("Calle 32D con Carrera 65C" in c for c in candidatos))
        self.assertTrue(any("Calle 32D" in c for c in candidatos))

    @patch('requests.get')
    def test_rechazo_degradacion_ciudad_cuando_busca_calle(self, mock_get):
        """
        Verifica que si Nominatim degrada a nivel de ciudad (addresstype='city', lat=6.269732),
        el servicio rechace la ciudad y busque la siguiente alternativa o fallback en lugar
        de retornar erróneamente el centroide de Medellín.
        """
        # Primera llamada (consulta exacta): Nominatim devuelve centroide de Medellín (degradación)
        resp_ciudad = MagicMock()
        resp_ciudad.status_code = 200
        resp_ciudad.json.return_value = [
            {
                "lat": "6.269732",
                "lon": "-75.602560",
                "class": "boundary",
                "type": "administrative",
                "addresstype": "city",
                "display_name": "Medellín, Antioquia, Colombia"
            }
        ]

        # Segunda llamada (cruce vial 'Calle 32D con Carrera 65C'): Nominatim devuelve la vía correcta en Belén
        resp_via = MagicMock()
        resp_via.status_code = 200
        resp_via.json.return_value = [
            {
                "lat": "6.237573",
                "lon": "-75.585115",
                "class": "highway",
                "type": "residential",
                "addresstype": "road",
                "display_name": "Calle 32D, Belén, Medellín, Antioquia, Colombia"
            }
        ]

        mock_get.side_effect = [resp_ciudad, resp_via]

        coords = self.geocodificador.geocodificar_direccion("Cl 32D # 65C-81, Medellin, Antioquia, Colombia")

        # Debe haber rechazado 6.269732 y retornado las coordenadas de la vía en Belén
        self.assertEqual(coords, (6.237573, -75.585115))
        self.assertNotEqual(coords, (6.269732, -75.602560))

    def test_resolucion_calle_32d_contingencia_local(self):
        """Verifica que 'Cl 32D # 65C-81' resuelva a Belén (6.2376, -75.5851) mediante el catálogo local."""
        coords = self.geocodificador.proveedor_fallback.geocodificar_direccion("Cl 32D # 65C-81, Medellin")
        self.assertEqual(coords, (6.2376, -75.5851))


class TestIntegracionCentroControlGeocodificador(unittest.TestCase):
    """Pruebas de integración entre SistemaCentroControl, Pedido y el servicio de geocodificación."""

    def setUp(self):
        self.usuario = Usuario(id_usuario="USR-TEST-01", nombre="Ana Ruiz", rol="CLIENTE")
        self.geocodificador_local = ServicioGeocodificadorLocal()
        self.centro = SistemaCentroControl(geocodificador=self.geocodificador_local)

    def test_pedido_con_direccion_resuelve_coordenadas_automaticamente(self):
        """Al registrar un pedido con solo dirección textual, el centro de control resuelve las coordenadas."""
        pedido = Pedido(
            id_pedido="PED-GEO-01",
            usuario_solicitante=self.usuario,
            categoria_requerida="ENTREGA_LIGERA",
            coordenada_destino=None,
            direccion_destino="Parque El Poblado"
        )
        self.assertIsNone(pedido.coordenada_destino)

        pedido_registrado = self.centro.registrar_pedido(pedido)

        self.assertEqual(pedido_registrado.id_pedido, "PED-GEO-01")
        self.assertIsNotNone(pedido_registrado.coordenada_destino)
        self.assertEqual(pedido_registrado.coordenada_destino, (6.2089, -75.5684))
        self.assertIn(pedido_registrado, self.centro.pedidos)

        # Verificar que se generó log de auditoría
        logs_geo = [l for l in self.centro.historial_logs if l.tipo_evento == "GEOCODIFICACION_EXITOSA"]
        self.assertEqual(len(logs_geo), 1)
        self.assertEqual(logs_geo[0].id_pedido, "PED-GEO-01")

    def test_pedido_con_coordenadas_preexistentes_no_invoca_geocodificacion(self):
        """Si el pedido ya trae coordenadas exactas, se respetan sin necesidad de llamar al geocodificador."""
        coords_exactas = (6.2500, -75.5700)
        pedido = Pedido(
            id_pedido="PED-GEO-02",
            usuario_solicitante=self.usuario,
            categoria_requerida="ENTREGA_LIGERA",
            coordenada_destino=coords_exactas,
            direccion_destino="Cualquier direccion"
        )

        self.centro.registrar_pedido(pedido)
        self.assertEqual(pedido.coordenada_destino, coords_exactas)

        # No debe haber logs de geocodificación
        logs_geo = [l for l in self.centro.historial_logs if l.tipo_evento == "GEOCODIFICACION_EXITOSA"]
        self.assertEqual(len(logs_geo), 0)

    def test_pedido_con_direccion_invalida_se_rechaza_y_registra_auditoria(self):
        """Si la dirección no puede ser resuelta, se lanza GeocodificacionError y se crea log de rechazo."""
        pedido = Pedido(
            id_pedido="PED-GEO-FAIL",
            usuario_solicitante=self.usuario,
            categoria_requerida="ENTREGA_LIGERA",
            direccion_destino="Calle Inexistente En El Valle 9999"
        )

        with self.assertRaises(GeocodificacionError):
            self.centro.registrar_pedido(pedido)

        # El pedido no debe estar en la lista activa del centro
        self.assertNotIn(pedido, self.centro.pedidos)

        # Debe existir un log de rechazo
        logs_rechazo = [l for l in self.centro.historial_logs if l.tipo_evento == "PEDIDO_RECHAZADO_DIRECCION_INVALIDA"]
        self.assertEqual(len(logs_rechazo), 1)
        self.assertEqual(logs_rechazo[0].id_pedido, "PED-GEO-FAIL")


class TestServicioGeocodificadorGoogle(unittest.TestCase):
    """Pruebas unitarias para el proveedor Google Maps Geocoding API con contingencia multinivel."""

    def setUp(self):
        self.calculador = CalculadorGeodesico()
        self.geocodificador = ServicioGeocodificadorGoogle(
            api_key="TEST_API_KEY_GOOGLE",
            calculador=self.calculador
        )

    @patch('requests.get')
    def test_google_geocodificacion_exitosa(self, mock_get):
        """Verifica que una respuesta válida de Google Maps retorne coordenadas geodésicas de alta precisión."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "geometry": {
                        "location": {"lat": 6.237573, "lng": -75.585115}
                    },
                    "formatted_address": "Cl. 32d #65C-81, Belén, Medellín, Antioquia, Colombia"
                }
            ]
        }
        mock_get.return_value = mock_resp

        coords = self.geocodificador.geocodificar_direccion("Cl 32D # 65C-81, Medellin, Antioquia, Colombia")

        self.assertEqual(coords, (6.237573, -75.585115))
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["key"], "TEST_API_KEY_GOOGLE")
        self.assertEqual(kwargs["params"]["components"], "country:CO")

    @patch('requests.get')
    def test_google_fuera_del_valle_lanza_coordenada_invalida(self, mock_get):
        """Verifica que si Google retorna una ubicación fuera de Aburrá (ej. Bogotá), se dispare CoordenadaInvalidaError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "geometry": {
                        "location": {"lat": 4.711000, "lng": -74.072100}
                    }
                }
            ]
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(CoordenadaInvalidaError):
            self.geocodificador.geocodificar_direccion("Plaza de Bolívar, Bogotá")

    def test_google_sin_api_key_delega_a_fallback(self):
        """Si no se suministra API Key, el servicio delega transparentemente a la contingencia sin error."""
        geo_sin_key = ServicioGeocodificadorGoogle(api_key="", calculador=self.calculador)
        coords = geo_sin_key.geocodificar_direccion("Parque Berrio")
        self.assertEqual(coords, (6.2498, -75.5694))

    @patch('requests.get')
    def test_google_zero_results_delega_a_fallback(self, mock_get):
        """Si Google responde ZERO_RESULTS, se delega al proveedor de respaldo."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ZERO_RESULTS", "results": []}
        mock_get.return_value = mock_resp

        coords = self.geocodificador.geocodificar_direccion("Parque Berrio")
        self.assertEqual(coords, (6.2498, -75.5694))

    @patch('requests.get')
    def test_google_obtener_detalle_direccion(self, mock_get):
        """Verifica la generación del metadato estructurado con fuente Google."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "geometry": {
                        "location": {"lat": 6.237573, "lng": -75.585115}
                    }
                }
            ]
        }
        mock_get.return_value = mock_resp

        detalle = self.geocodificador.obtener_detalle_direccion("Cl 32D # 65C-81, Medellin")
        self.assertEqual(detalle["fuente"], "GOOGLE_MAPS_GEOCODING")
        self.assertEqual(detalle["coordenadas"], (6.237573, -75.585115))
        self.assertTrue(detalle["dentro_valle_aburra"])


class TestServicioGeocodificadorArcGIS(unittest.TestCase):
    """Pruebas unitarias para el proveedor Esri ArcGIS World Geocoding Service."""

    def setUp(self):
        self.calculador = CalculadorGeodesico()
        self.geocodificador = ServicioGeocodificadorArcGIS(calculador=self.calculador)

    @patch('requests.get')
    def test_arcgis_geocodificacion_exitosa(self, mock_get):
        """Verifica que una respuesta válida de ArcGIS retorne lat/lon en el orden correcto tras invertir x e y."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "address": "Calle 32D # 65C-81, Medellín, Antioquia, 050030",
                    "location": {"x": -75.585115, "y": 6.237573},
                    "score": 98.5,
                    "attributes": {
                        "Match_addr": "Calle 32D # 65C-81, Medellín, Antioquia",
                        "Addr_type": "PointAddress",
                        "Score": 98.5
                    }
                }
            ]
        }
        mock_get.return_value = mock_resp

        coords = self.geocodificador.geocodificar_direccion("Cl 32D # 65C-81, Medellin, Antioquia, Colombia")

        self.assertEqual(coords, (6.237573, -75.585115))
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["countryCode"], "COL")
        self.assertEqual(kwargs["params"]["f"], "json")
        self.assertIn("-75.7167", kwargs["params"]["searchExtent"])

    @patch('requests.get')
    def test_arcgis_fuera_del_valle_lanza_coordenada_invalida(self, mock_get):
        """Verifica que si ArcGIS retorna una ubicación fuera de Aburrá (ej. Bogotá), se dispare CoordenadaInvalidaError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "location": {"x": -74.072100, "y": 4.711000},
                    "score": 100.0
                }
            ]
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(CoordenadaInvalidaError):
            self.geocodificador.geocodificar_direccion("Plaza de Bolívar, Bogotá")

    @patch('requests.get')
    def test_arcgis_score_bajo_delega_a_fallback(self, mock_get):
        """Si el score devuelto es menor al umbral (70%), delega a la contingencia."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "location": {"x": -75.5694, "y": 6.2498},
                    "score": 45.0
                }
            ]
        }
        mock_get.return_value = mock_resp

        coords = self.geocodificador.geocodificar_direccion("Parque Berrio")
        self.assertEqual(coords, (6.2498, -75.5694))

    @patch('requests.get')
    def test_arcgis_sin_candidatos_delega_a_fallback(self, mock_get):
        """Si la lista de candidatos está vacía, delega a la contingencia."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": []}
        mock_get.return_value = mock_resp

        coords = self.geocodificador.geocodificar_direccion("Parque Berrio")
        self.assertEqual(coords, (6.2498, -75.5694))

    @patch('requests.get')
    def test_arcgis_obtener_detalle_direccion(self, mock_get):
        """Verifica el reporte estructurado de metadatos para ArcGIS."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "location": {"x": -75.585115, "y": 6.237573},
                    "score": 95.0
                }
            ]
        }
        mock_get.return_value = mock_resp

        detalle = self.geocodificador.obtener_detalle_direccion("Cl 32D # 65C-81, Medellin")
        self.assertEqual(detalle["fuente"], "ARCGIS_WORLD_GEOCODER")
        self.assertEqual(detalle["coordenadas"], (6.237573, -75.585115))
        self.assertTrue(detalle["dentro_valle_aburra"])


if __name__ == "__main__":
    unittest.main()
