# Suite de pruebas integrales para el servidor HTTP nativo (http.server) y puente MVC v2
# Verifica el acoplamiento completo con todos los cambios de Develop sin tocar el backend

from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.servicios.geocodificador import ServicioGeocodificadorArcGIS, ServicioGeocodificadorLocal
from src.ui.controlador import ControladorSkyRoute
from src.ui.servidor import crear_servidor


class _ClimaDeterministaTest:
    """Stub determinista sin llamadas de red para pruebas rápidas del servidor HTTP."""

    def obtener_condiciones(self, nombre_nodo: str = "El_Poblado") -> dict:
        return {
            "nodo": nombre_nodo,
            "temperatura_c": 23.0,
            "lluvia_mm": 0.0,
            "viento_kmh": 10.0,
            "factor_velocidad": 1.0,
            "vuelo_seguro": True,
        }


class TestServidorUISkyRouteV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        controlador_test = ControladorSkyRoute(
            geocodificador=ServicioGeocodificadorLocal(),
            servicio_clima=_ClimaDeterministaTest(),
        )
        cls.servidor, cls.puerto = crear_servidor(
            host="127.0.0.1",
            puerto_inicial=8890,
            controlador=controlador_test,
        )
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

    def test_01_estaticos_y_ausencia_estricta_de_emojis(self) -> None:
        for ruta, fragmento in (
            ("/", "SkyRoute Drones"),
            ("/estilos.css", "--bg-canvas"),
            ("/app.js", "renderizarCabinaOperaciones"),
        ):
            with urlopen(f"{self.base_url}{ruta}", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                texto = resp.read().decode("utf-8")
                self.assertIn(fragmento, texto)

        carpeta_ui = Path(__file__).resolve().parent
        for archivo in carpeta_ui.rglob("*"):
            if archivo.suffix in (".py", ".html", ".css", ".js"):
                contenido = archivo.read_text(encoding="utf-8")
                for ch in contenido:
                    cp = ord(ch)
                    es_emoji = (
                        0x1F300 <= cp <= 0x1FAFF
                        or 0x2600 <= cp <= 0x27BF
                        or 0xFE00 <= cp <= 0xFE0F
                    )
                    self.assertFalse(
                        es_emoji,
                        f"Se detectó un caracter tipo emoji ({hex(cp)}) en {archivo.name}",
                    )

    def test_02_configuracion_por_defecto_usa_arcgis_y_base_olaya_herrera(self) -> None:
        ctrl_real = ControladorSkyRoute()
        self.assertIsInstance(ctrl_real.geocodificador, ServicioGeocodificadorArcGIS)
        self.assertEqual(ctrl_real.centro.coordenadas_base, (6.219603, -75.586792))
        self.assertEqual(len(ctrl_real.centro.pedidos), 0)

    def test_03_estado_inicial_cero_pedidos_6_drones_y_3_roles(self) -> None:
        codigo, datos = self._get_json("/api/estado")
        self.assertEqual(codigo, 200)
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["coordenadas_base"], [6.219603, -75.586792])
        self.assertEqual(len(datos["pedidos"]), 0)
        self.assertEqual(len(datos["flota"]), 6)
        self.assertEqual(len(datos["usuarios"]), 3)
        roles = {u["rol"] for u in datos["usuarios"]}
        self.assertEqual(roles, {"CLIENTE", "OPERADOR_VUELO", "ADMINISTRADOR"})

    def test_04_geocodificacion_preview_y_comparador_polimorfico_hu10(self) -> None:
        cod_geo, det = self._post_json("/api/geocodificar", {"direccion": "Parque El Poblado"})
        self.assertEqual(cod_geo, 200)
        self.assertTrue(det["dentro_valle_aburra"])
        self.assertGreater(det["distancia_ida_vuelta_km"], 3.0)

        cod_poly, poly = self._get_json("/api/polimorfismo/viabilidad?distancia_km=15.0")
        self.assertEqual(cod_poly, 200)
        self.assertEqual(poly["total_aeronaves"], 6)
        self.assertEqual(poly["total_viables"], 6)

    def test_05_excepciones_dominio_telemetria_y_geocerca(self) -> None:
        cod_bat, err_bat = self._post_json(
            "/api/flota/telemetria",
            {"accion": "inyectar", "id_dron": "DRON-RESC-06", "bateria": -4.0},
        )
        self.assertEqual(cod_bat, 400)
        self.assertEqual(err_bat["error_tipo"], "BateriaInvalidaError")

        cod_alt, err_alt = self._post_json(
            "/api/flota/telemetria",
            {
                "accion": "inyectar",
                "id_dron": "DRON-RESC-06",
                "altitud": 140.0,
                "estado_motores": "EN_VUELO",
            },
        )
        self.assertEqual(cod_alt, 400)
        self.assertEqual(err_alt["error_tipo"], "AltitudInvalidaError")

        cod_bog, err_bog = self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-BOG-01",
                "categoria_requerida": "VIGILANCIA",
                "latitud": 4.7110,
                "longitud": -74.0721,
                "peso_carga_kg": 0.5,
            },
        )
        self.assertEqual(cod_bog, 400)
        self.assertEqual(err_bog["error_tipo"], "CoordenadaInvalidaError")

    def test_06_ciclo_completo_pedido_asignacion_simulacion_lineal_y_certificacion(self) -> None:
        # 1. Crear pedido geocodificado hacia Universidad de Medellín
        cod_ped, res_ped = self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-UDEM-01",
                "categoria_requerida": "MAPEO_TOPOGRAFICO",
                "direccion_destino": "Universidad de Medellin",
                "peso_carga_kg": 1.2,
            },
        )
        self.assertEqual(cod_ped, 200)
        self.assertEqual(res_ped["pedido_creado_id"], "PED-UDEM-01")

        # 2. Asignar dron compatible (DRON-MAP-04)
        cod_asig, res_asig = self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-UDEM-01"})
        self.assertEqual(cod_asig, 200)
        self.assertEqual(res_asig["dron_enfocado_id"], "DRON-MAP-04")

        # 3. Despegar misión temporal
        cod_desp, res_desp = self._post_json(
            "/api/misiones/despegar",
            {"id_pedido": "PED-UDEM-01", "modo_despacho": "TEMPORAL"},
        )
        self.assertEqual(cod_desp, 200)
        dron_air = next(d for d in res_desp["flota"] if d["id_dron"] == "DRON-MAP-04")
        self.assertEqual(dron_air["altitud"], 30.0)
        self.assertEqual(dron_air["progreso_lineal"]["etapa_actual"], 1)

        # 4. Avanzar pulsos discretos hasta completar retorno en Olaya Herrera
        for _ in range(15):
            cod_p, res_p = self._post_json(
                "/api/simulacion/paso",
                {"id_dron": "DRON-MAP-04", "delta_t": 45.0},
            )
            self.assertEqual(cod_p, 200)
            dron_act = next(d for d in res_p["flota"] if d["id_dron"] == "DRON-MAP-04")
            if not dron_act["en_vuelo_activo"]:
                break

        self.assertTrue(dron_act["disponible"])
        self.assertEqual(dron_act["progreso_lineal"]["progreso_ciclo_pct"], 100.0)
        sesion = res_p["sesiones_vuelo"]["DRON-MAP-04"]
        self.assertEqual(sesion["certificacion_final"]["resultado"], "EXITO")

    def test_07_emergencia_bateria_agotada_y_estacion_recarga(self) -> None:
        # Crear y despegar misión en INSPECCION_INFRAESTRUCTURA (DRON-INSP-05)
        self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-INSP-99",
                "categoria_requerida": "INSPECCION_INFRAESTRUCTURA",
                "direccion_destino": "Parque de Bello",
                "peso_carga_kg": 1.0,
            },
        )
        self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-INSP-99"})
        self._post_json("/api/misiones/despegar", {"id_pedido": "PED-INSP-99"})

        # Simular drenaje severo de batería en pleno vuelo (2.0% restante)
        cod_tele, _ = self._post_json(
            "/api/flota/telemetria",
            {
                "accion": "inyectar",
                "id_dron": "DRON-INSP-05",
                "bateria": 2.0,
                "altitud": 30.0,
                "estado_motores": "EN_VUELO",
            },
        )
        self.assertEqual(cod_tele, 200)

        # Avanzar pulso largo -> debe disparar BATERIA_AGOTADA (0.0%) y aterrizaje forzoso
        cod_paso, res_paso = self._post_json(
            "/api/simulacion/paso",
            {"id_dron": "DRON-INSP-05", "delta_t": 300.0},
        )
        self.assertEqual(cod_paso, 200)
        dron_em = next(d for d in res_paso["flota"] if d["id_dron"] == "DRON-INSP-05")
        self.assertEqual(dron_em["bateria"], 0.0)
        self.assertEqual(dron_em["estado_operacional"], "SIN_BATERIA")
        self.assertFalse(dron_em["disponible"])

        # Recargar en estación de mantenimiento al 100% -> recupera disponibilidad
        cod_rec, res_rec = self._post_json(
            "/api/flota/recargar",
            {"id_dron": "DRON-INSP-05", "porcentaje": 100.0},
        )
        self.assertEqual(cod_rec, 200)
        dron_ok = next(d for d in res_rec["flota"] if d["id_dron"] == "DRON-INSP-05")
        self.assertEqual(dron_ok["bateria"], 100.0)
        self.assertTrue(dron_ok["disponible"])

    def test_08_alta_desde_fabrica_tour_guiado_y_cancelacion(self) -> None:
        # 1. Crear aeronave nueva mediante FABRICA_DRONES
        cod_fab, res_fab = self._post_json(
            "/api/flota/fabrica",
            {
                "categoria": "VIGILANCIA",
                "id_dron": "DRON-VIG-07",
                "modelo_aeronave": "Sentinel-X2",
                "velocidad_promedio_kmh": 64.0,
                "bateria_inicial": 95.0,
                "parametros": {
                    "resolucion_camara_mp": 64,
                    "vision_nocturna": True,
                    "frecuencia_transmision_ghz": 5.8,
                },
            },
        )
        self.assertEqual(cod_fab, 200)
        self.assertEqual(len(res_fab["flota"]), 7)

        # 2. Preparar Tour Guiado End-to-End
        cod_tour, res_tour = self._post_json("/api/demo/preparar", {})
        self.assertEqual(cod_tour, 200)
        self.assertIn("tour_guiado", res_tour)
        self.assertEqual(res_tour["tour_guiado"]["id_dron"], "DRON-ENT-01")

        # 3. Crear y cancelar pedido pendiente
        self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-CANC-01",
                "categoria_requerida": "CARGA_PESADA",
                "direccion_destino": "Parque de Sabaneta",
                "peso_carga_kg": 12.0,
            },
        )
        cod_canc, res_canc = self._post_json(
            "/api/pedidos/cancelar", {"id_pedido": "PED-CANC-01"}
        )
        self.assertEqual(cod_canc, 200)
        ped_c = next(p for p in res_canc["pedidos"] if p["id_pedido"] == "PED-CANC-01")
        self.assertEqual(ped_c["estado"], "CANCELADO")

    def test_09_despacho_concurrente_multidron_y_foco_desacoplado(self) -> None:
        """Verifica que dos aeronaves puedan volar simultáneamente y avanzar juntas con id_dron=None sin forzar foco."""
        # 1. Crear y despegar primera misión con DRON-CAR-02 (Carga Pesada)
        self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-CONC-01",
                "categoria_requerida": "CARGA_PESADA",
                "direccion_destino": "Parque de El Poblado",
                "peso_carga_kg": 5.0,
            },
        )
        self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-CONC-01", "id_dron": "DRON-CAR-02"})
        cod_d1, res_d1 = self._post_json(
            "/api/misiones/despegar",
            {"id_pedido": "PED-CONC-01", "id_dron": "DRON-CAR-02"},
        )
        self.assertEqual(cod_d1, 200)

        # 2. Crear y despegar segunda misión concurrente con DRON-VIG-03 (Vigilancia)
        self._post_json(
            "/api/pedidos",
            {
                "id_pedido": "PED-CONC-02",
                "categoria_requerida": "VIGILANCIA",
                "direccion_destino": "Parque de Envigado",
                "peso_carga_kg": 0.5,
            },
        )
        self._post_json("/api/pedidos/asignar", {"id_pedido": "PED-CONC-02", "id_dron": "DRON-VIG-03"})
        cod_d2, res_d2 = self._post_json(
            "/api/misiones/despegar",
            {"id_pedido": "PED-CONC-02", "id_dron": "DRON-VIG-03"},
        )
        self.assertEqual(cod_d2, 200)

        # 3. Comprobar que ambas aeronaves están en vuelo activo en la flota
        d1 = next(d for d in res_d2["flota"] if d["id_dron"] == "DRON-CAR-02")
        d2 = next(d for d in res_d2["flota"] if d["id_dron"] == "DRON-VIG-03")
        self.assertTrue(d1["en_vuelo_activo"])
        self.assertTrue(d2["en_vuelo_activo"])

        # 4. Avanzar pulso global con id_dron: None (ambos drones avanzan a la vez)
        cod_paso, res_paso = self._post_json(
            "/api/simulacion/paso",
            {"id_dron": None, "delta_t": 30.0, "usar_reloj_real": False},
        )
        self.assertEqual(cod_paso, 200)

        # Verificación: no secuestra el foco (dron_enfocado_id es None)
        self.assertIsNone(res_paso.get("dron_enfocado_id"))

        # Verificación: ambos drones emitieron pulso y consumieron batería
        ids_pulsos = [p["id_dron"] for p in res_paso["pulsos_emitidos"]]
        self.assertIn("DRON-CAR-02", ids_pulsos)
        self.assertIn("DRON-VIG-03", ids_pulsos)

        d1_post = next(d for d in res_paso["flota"] if d["id_dron"] == "DRON-CAR-02")
        d2_post = next(d for d in res_paso["flota"] if d["id_dron"] == "DRON-VIG-03")
        self.assertLess(d1_post["bateria"], d1["bateria"])
        self.assertLess(d2_post["bateria"], d2["bateria"])
        self.assertGreater(d1_post["kilometraje_total_km"], 0.0)
        self.assertGreater(d2_post["kilometraje_total_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
