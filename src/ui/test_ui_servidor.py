# Suite de pruebas integrales para el servidor HTTP nativo (http.server) y puente MVC
# Verifica los Requisitos Funcionales RF-01 a RF-10 sin modificar el backend

from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.ui.servidor import crear_servidor


class TestServidorUISkyRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.servidor, cls.puerto = crear_servidor(host="127.0.0.1", puerto_inicial=8890)
        cls.base_url = f"http://127.0.0.1:{cls.puerto}"
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join(timeout=2.0)

    def _get_json(self, ruta: str) -> tuple[int, dict]:
        req = Request(f"{self.base_url}{ruta}", method="GET")
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def _post_json(self, ruta: str, payload: dict) -> tuple[int, dict]:
        cuerpo = json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self.base_url}{ruta}",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def test_01_archivos_estaticos_servidos_correctamente(self) -> None:
        for ruta, fragmento in (
            ("/", "SkyRoutes Drones"),
            ("/estilos.css", "--bg-canvas"),
            ("/app.js", "inicializarAplicacion"),
        ):
            with urlopen(f"{self.base_url}{ruta}", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                texto = resp.read().decode("utf-8")
                self.assertIn(fragmento, texto)

    def test_02_estado_inicial_contiene_las_6_subclases_polimorficas(self) -> None:
        codigo, datos = self._get_json("/api/estado")
        self.assertEqual(codigo, 200)
        self.assertTrue(datos["ok"])
        self.assertEqual(len(datos["flota"]), 6)
        clases = {d["clase_python"] for d in datos["flota"]}
        self.assertEqual(
            clases,
            {
                "DronEntregaLigera",
                "DronRescate",
                "DronCargaPesada",
                "DronVigilancia",
                "DronMapeo",
                "DronInspeccion",
            },
        )

    def test_03_preview_ruta_haversine_y_eta(self) -> None:
        codigo, prev = self._get_json("/api/ruta-preview?id_dron=DR-02&lat=6.2620&lon=-75.5780")
        self.assertEqual(codigo, 200)
        self.assertGreater(prev["distancia_km"], 5.0)
        self.assertGreater(prev["eta_min"], 4.0)
        self.assertGreater(prev["consumo_estimado_pct"], 10.0)

    def test_04_excepciones_dominio_telemetria_rf01_rf02(self) -> None:
        codigo_bat, err_bat = self._post_json("/api/telemetria", {"id_dron": "DR-02", "bateria": -5.0})
        self.assertEqual(codigo_bat, 400)
        self.assertEqual(err_bat["error_tipo"], "BateriaInvalidaError")
        self.assertIn("Regla de Negocio #2", err_bat["regla_negocio"])

        codigo_alt, err_alt = self._post_json(
            "/api/telemetria", {"id_dron": "DR-02", "altitud": 145.0, "estado_motores": "EN_VUELO"}
        )
        self.assertEqual(codigo_alt, 400)
        self.assertEqual(err_alt["error_tipo"], "AltitudInvalidaError")

    def test_05_rechazo_coordenada_fuera_valle_aburra_rf07(self) -> None:
        # Coordenadas de Bogotá (fuera del polígono de Aburrá)
        codigo, err = self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-BOG-99",
                "categoria_requerida": "VIGILANCIA",
                "latitud": 4.7110,
                "longitud": -74.0721,
                "peso_carga_kg": 0.0,
            },
        )
        self.assertEqual(codigo, 400)
        self.assertEqual(err["error_tipo"], "CoordenadaInvalidaError")

    def test_06_ciclo_completo_asignacion_despegue_simulacion_y_retorno(self) -> None:
        # 1. Asignar PED-4029 a DR-02 (Búsqueda y Rescate)
        cod_asig, res_asig = self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-4029"})
        self.assertEqual(cod_asig, 200)
        self.assertEqual(res_asig["dron_enfocado_id"], "DR-02")

        # 2. Despegar misión simulada
        cod_desp, res_desp = self._post_json(
            "/api/pedidos/despachar", {"id_pedido": "PED-4029", "modo": "SIMULADO"}
        )
        self.assertEqual(cod_desp, 200)
        dr02 = next(d for d in res_desp["flota"] if d["id_dron"] == "DR-02")
        self.assertEqual(dr02["altitud"], 30.0)
        self.assertEqual(dr02["estado_motores"], "EN_VUELO")

        # 3. Avanzar parcialmente (120 segundos) -> en tránsito hacia destino
        cod_sync1, res_sync1 = self._post_json("/api/sincronizar", {"paso_fijo_seg": 120.0})
        self.assertEqual(cod_sync1, 200)
        dr02_mid = next(d for d in res_sync1["flota"] if d["id_dron"] == "DR-02")
        self.assertGreater(dr02_mid["progreso_mision_pct"], 10.0)
        self.assertLess(dr02_mid["bateria"], 92.0)

        # 4. Avanzar para completar entrega y quedar a mitad del retorno (300 segundos)
        cod_sync2, res_sync2 = self._post_json("/api/sincronizar", {"paso_fijo_seg": 300.0})
        self.assertEqual(cod_sync2, 200)
        dr02_ret = next(d for d in res_sync2["flota"] if d["id_dron"] == "DR-02")
        self.assertTrue(dr02_ret["retornando_a_base"])

        # 5. Intentar aterrizaje prematuro lejos de la base (> 50m) -> debe denegarse (RF-09)
        cod_land_fail, err_land = self._post_json("/api/drones/aterrizar", {"id_dron": "DR-02"})
        self.assertEqual(cod_land_fail, 400)
        self.assertEqual(err_land["error_tipo"], "ActualizarEstadoDronError")

        # 6. Completar tramo final de retorno (500 segundos) -> aterriza y recupera disponibilidad
        cod_sync3, res_sync3 = self._post_json("/api/sincronizar", {"paso_fijo_seg": 500.0})
        self.assertEqual(cod_sync3, 200)
        dr02_fin = next(d for d in res_sync3["flota"] if d["id_dron"] == "DR-02")
        self.assertTrue(dr02_fin["disponible"])
        self.assertFalse(dr02_fin["retornando_a_base"])
        self.assertEqual(dr02_fin["altitud"], 0.0)

    def test_07_validacion_sobrepeso_entrega_ligera_hu09(self) -> None:
        # Crear pedido con sobrepeso (20 kg > 8 kg máximo de DR-01)
        cod_ped, _ = self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-PESO-01",
                "categoria_requerida": "ENTREGA_LIGERA",
                "latitud": 6.2319,
                "longitud": -75.6105,
                "peso_carga_kg": 20.0,
            },
        )
        self.assertEqual(cod_ped, 200)

        cod_asig, _ = self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-PESO-01"})
        self.assertEqual(cod_asig, 200)

        cod_desp, err_peso = self._post_json(
            "/api/pedidos/despachar", {"id_pedido": "PED-PESO-01", "modo": "SIMULADO"}
        )
        self.assertEqual(cod_desp, 400)
        self.assertEqual(err_peso["error_tipo"], "ActualizarEstadoDronError")

    def test_08_registro_y_cambio_usuario_rf06(self) -> None:
        cod_usr, res_usr = self._post_json(
            "/api/usuarios",
            {
                "accion": "registrar",
                "id_usuario": "USR-DOC-99",
                "nombre": "Mario Saldarriaga",
                "rol": "ADMINISTRADOR",
            },
        )
        self.assertEqual(cod_usr, 200)
        self.assertEqual(res_usr["usuario_activo"]["id_usuario"], "USR-DOC-99")


if __name__ == "__main__":
    unittest.main()
