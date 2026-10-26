"""
Suite de Pruebas Unitarias de Orquestación Polimórfica y Despacho de Misiones (HU-12)
Sprint 2: Herencia, Polimorfismo y Abstracción Formal
Responsable: Valery Arboleda Ardila
"""

import sys
import os
import unittest

# Asegurar resolución del paquete raíz 'src'
RUTA_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if RUTA_RAIZ not in sys.path:
    sys.path.insert(0, RUTA_RAIZ)

from src.control.centro_control import (
    SistemaCentroControl,
    FABRICA_DRONES,
)
from src.flota.dron import Dron
from src.flota.dron_inspeccion import DronInspeccion
from src.flota.dron_rescate import DronRescate
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.telemetria.telemetria import TelemetriaDrone


class TestFabricaDrones(unittest.TestCase):
    """Pruebas del registro de fábrica dinámico de aeronaves (FABRICA_DRONES)."""

    def test_01_catalogo_contiene_subclases_asistencia(self):
        """Verifica que FABRICA_DRONES incluya DronInspeccion y DronRescate."""
        self.assertIn("INSPECCION_INFRAESTRUCTURA", FABRICA_DRONES)
        self.assertIn("BUSQUEDA_RESCATE", FABRICA_DRONES)
        self.assertIs(FABRICA_DRONES["INSPECCION_INFRAESTRUCTURA"], DronInspeccion)
        self.assertIs(FABRICA_DRONES["BUSQUEDA_RESCATE"], DronRescate)

    def test_02_instanciar_desde_fabrica_inspeccion(self):
        """Comprueba la instanciación de DronInspeccion mediante el diccionario de fábrica."""
        clase_insp = FABRICA_DRONES.get("INSPECCION_INFRAESTRUCTURA")
        dron = clase_insp(
            id_dron="DRON-INSP-FAB-01",
            modelo_aeronave="DJI-Insp-Pro",
            zoom_optico_x=20,
            rango_sensor_ultrasonico_m=6.5
        )
        self.assertIsInstance(dron, DronInspeccion)
        self.assertIsInstance(dron, Dron)
        self.assertEqual(dron.categoria, "INSPECCION_INFRAESTRUCTURA")
        self.assertEqual(dron.zoom_optico_x, 20)

    def test_03_instanciar_desde_fabrica_rescate(self):
        """Comprueba la instanciación de DronRescate mediante el diccionario de fábrica."""
        clase_resc = FABRICA_DRONES.get("BUSQUEDA_RESCATE")
        dron = clase_resc(
            id_dron="DRON-RESC-FAB-01",
            modelo_aeronave="Rescue-X",
            camara_termica=True,
            kit_auxilios_equipado=True,
            potencia_altavoz_db=110
        )
        self.assertIsInstance(dron, DronRescate)
        self.assertIsInstance(dron, Dron)
        self.assertEqual(dron.categoria, "BUSQUEDA_RESCATE")
        self.assertTrue(dron.camara_termica)

    def test_04_agregar_dron_no_disponible_o_en_mision_lanza_error(self):
        """Verifica que agregar_dron rechace drones ocupados o en misión."""
        centro = SistemaCentroControl()
        dron_ocupado = DronInspeccion("DRON-BUSY", "Matrice-300", 10, 5.0, disponible=False)
        with self.assertRaises(ValueError):
            centro.agregar_dron(dron_ocupado)

    def test_05_registro_dinamico_de_subclases(self):
        """Comprueba que FABRICA_DRONES acepte nuevas subclases directamente."""
        class DronPrueba(Dron):
            def ejecutar_mision(self, pedido):
                return {"prueba": True}
            def calcular_consumo_estimado(self, d):
                return d * 1.0
            def inspeccionar_sistemas_especializados(self):
                return "OK"

        FABRICA_DRONES["TEST_EXPERIMENTAL"] = DronPrueba
        self.assertIn("TEST_EXPERIMENTAL", FABRICA_DRONES)
        self.assertIs(FABRICA_DRONES["TEST_EXPERIMENTAL"], DronPrueba)


class TestAsignacionPolimorfica(unittest.TestCase):
    """Pruebas de asignación inteligente evaluando compatibilidad polimórfica (RF-08)."""

    def setUp(self):
        self.centro = SistemaCentroControl(lat_base=6.2089, lon_base=-75.5684)
        self.cliente = Usuario("USR-01", "Valery Arboleda", "CLIENTE")
        self.centro.registrar_usuario(self.cliente)

        self.dron_insp = DronInspeccion("DRON-INSP-01", "Matrice-300", 25, 7.0)
        self.dron_resc = DronRescate("DRON-RESC-01", "Lifeguard-1", True, True, 115)
        self.centro.agregar_dron(self.dron_insp)
        self.centro.agregar_dron(self.dron_resc)

    def test_06_asignacion_exitosa_por_subclase_inspeccion(self):
        """Comprueba la asignación polimórfica de DronInspeccion a pedido de infraestructura."""
        pedido = Pedido("PED-INSP-10", self.cliente, "INSPECCION_INFRAESTRUCTURA", (6.21, -75.57), 2.0)
        self.centro.registrar_pedido(pedido)

        asignado = self.centro.asignar_dron_a_pedido("PED-INSP-10")
        self.assertTrue(asignado)
        self.assertIs(pedido.dron_asignado, self.dron_insp)
        self.assertEqual(pedido.estado, "ASIGNADO")
        self.assertFalse(self.dron_insp.disponible)

    def test_07_asignacion_exitosa_por_subclase_rescate(self):
        """Comprueba la asignación polimórfica de DronRescate a pedido de emergencia."""
        pedido = Pedido("PED-RESC-20", self.cliente, "BUSQUEDA_RESCATE", (6.22, -75.58), 3.0)
        self.centro.registrar_pedido(pedido)

        asignado = self.centro.asignar_dron_a_pedido("PED-RESC-20")
        self.assertTrue(asignado)
        self.assertIs(pedido.dron_asignado, self.dron_resc)
        self.assertEqual(pedido.estado, "ASIGNADO")
        self.assertFalse(self.dron_resc.disponible)

    def test_08_asignacion_falla_si_no_hay_dron_compatible_disponible(self):
        """Comprueba que retorne False cuando no existan aeronaves compatibles libres."""
        self.dron_insp.disponible = False
        pedido = Pedido("PED-INSP-30", self.cliente, "INSPECCION_INFRAESTRUCTURA", (6.21, -75.57), 1.0)
        self.centro.registrar_pedido(pedido)

        self.assertFalse(self.centro.asignar_dron_a_pedido("PED-INSP-30"))

    def test_09_asignacion_defensiva_id_invalido(self):
        """Comprueba que IDs vacíos o inexistentes sean rechazados de forma segura."""
        self.assertFalse(self.centro.asignar_dron_a_pedido(""))
        self.assertFalse(self.centro.asignar_dron_a_pedido("   "))
        self.assertFalse(self.centro.asignar_dron_a_pedido(None))
        self.assertFalse(self.centro.asignar_dron_a_pedido("PED-INEXISTENTE"))


class TestDespachoPolimorfico(unittest.TestCase):
    """Pruebas del método despachar_mision y su ciclo completo de 6 etapas (HU-12)."""

    def setUp(self):
        self.centro = SistemaCentroControl(lat_base=6.2089, lon_base=-75.5684)
        self.cliente = Usuario("USR-01", "Valery Arboleda", "CLIENTE")
        self.centro.registrar_usuario(self.cliente)

        self.dron_insp = DronInspeccion("DRON-INSP-01", "Matrice-300", 30, 8.5)
        self.dron_insp.asignar_telemetria(
            TelemetriaDrone(
                id_dron="DRON-INSP-01",
                bateria=100.0,
                altitud=0.0,
                estado_motores="APAGADOS",
                coordenadas=(6.2089, -75.5684)
            )
        )
        self.centro.agregar_dron(self.dron_insp)

        self.dron_resc = DronRescate("DRON-RESC-01", "Lifeguard-1", True, True, 120)
        self.dron_resc.asignar_telemetria(
            TelemetriaDrone(
                id_dron="DRON-RESC-01",
                bateria=100.0,
                altitud=0.0,
                estado_motores="APAGADOS",
                coordenadas=(6.2089, -75.5684)
            )
        )
        self.centro.agregar_dron(self.dron_resc)

    def test_10_despacho_completo_mision_inspeccion(self):
        """Verifica el ciclo de vida completo de despacho para DronInspeccion."""
        pedido = Pedido("PED-101", self.cliente, "INSPECCION_INFRAESTRUCTURA", (6.2300, -75.5700), 2.0)
        self.centro.registrar_pedido(pedido)
        self.centro.asignar_dron_a_pedido("PED-101")

        despacho_ok = self.centro.despachar_mision("PED-101")
        self.assertTrue(despacho_ok)
        self.assertEqual(pedido.estado, "COMPLETADO")
        self.assertTrue(self.dron_insp.retornando_a_base)

        # Verificar generación de log de auditoría especializado
        logs_mision = [log for log in self.centro.historial_logs if log.tipo_evento == "MISION_COMPLETADA"]
        self.assertEqual(len(logs_mision), 1)
        self.assertIn("SENSOR_ULTRASONICO_Y_ZOOM", logs_mision[0].detalles)
        self.assertIn("DRON-INSP-01", logs_mision[0].id_dron)

    def test_11_despacho_completo_mision_rescate(self):
        """Verifica el ciclo de vida completo de despacho para DronRescate."""
        pedido = Pedido("PED-202", self.cliente, "BUSQUEDA_RESCATE", (6.2400, -75.5800), 3.5)
        self.centro.registrar_pedido(pedido)
        self.centro.asignar_dron_a_pedido("PED-202")

        despacho_ok = self.centro.despachar_mision("PED-202")
        self.assertTrue(despacho_ok)
        self.assertEqual(pedido.estado, "COMPLETADO")
        self.assertTrue(self.dron_resc.retornando_a_base)

        logs_mision = [log for log in self.centro.historial_logs if log.tipo_evento == "MISION_COMPLETADA"]
        self.assertEqual(len(logs_mision), 1)
        self.assertIn("CAMARA_TERMICA_Y_ALTAVOZ", logs_mision[0].detalles)
        self.assertIn("DRON-RESC-01", logs_mision[0].id_dron)

    def test_12_despacho_rechaza_pedido_no_asignado(self):
        """Verifica que despachar_mision rechace pedidos en estado PENDIENTE."""
        pedido = Pedido("PED-303", self.cliente, "INSPECCION_INFRAESTRUCTURA", (6.2300, -75.5700), 1.0)
        self.centro.registrar_pedido(pedido)

        # El pedido está PENDIENTE (no se ha asignado)
        self.assertFalse(self.centro.despachar_mision("PED-303"))
        self.assertEqual(pedido.estado, "PENDIENTE")

    def test_13_despacho_defensivo_id_invalido(self):
        """Verifica rechazo defensivo ante IDs inválidos o pedidos inexistentes."""
        self.assertFalse(self.centro.despachar_mision(""))
        self.assertFalse(self.centro.despachar_mision("   "))
        self.assertFalse(self.centro.despachar_mision(None))
        self.assertFalse(self.centro.despachar_mision("PED-FANTASMA"))

    def test_14_despacho_controla_falla_por_bateria_insuficiente(self):
        """Verifica que si la aeronave no tiene batería para la distancia, retorne False sin explotar."""
        centro_aislado = SistemaCentroControl(lat_base=6.2089, lon_base=-75.5684)
        centro_aislado.registrar_usuario(self.cliente)

        dron_agotado = DronInspeccion("DRON-INSP-LOW", "Matrice-Low", 10, 5.0)
        dron_agotado.asignar_telemetria(
            TelemetriaDrone(
                id_dron="DRON-INSP-LOW",
                bateria=1.0,  # Batería mínima insuficiente
                altitud=0.0,
                estado_motores="APAGADOS",
                coordenadas=(6.2089, -75.5684)
            )
        )
        centro_aislado.agregar_dron(dron_agotado)

        # Destino lejano (varios km)
        pedido = Pedido("PED-LEJOS", self.cliente, "INSPECCION_INFRAESTRUCTURA", (6.3500, -75.5000), 1.0)
        centro_aislado.registrar_pedido(pedido)
        centro_aislado.asignar_dron_a_pedido("PED-LEJOS")

        # El despacho debe capturar la excepción y retornar False de manera controlada
        resultado = centro_aislado.despachar_mision("PED-LEJOS")
        self.assertFalse(resultado)


def ejecutar_suite():
    suite = unittest.TestLoader().loadTestsFromNames([
        __name__ + ".TestFabricaDrones",
        __name__ + ".TestAsignacionPolimorfica",
        __name__ + ".TestDespachoPolimorfico",
    ])
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    if resultado.wasSuccessful():
        print("\n" + "=" * 80)
        print(" RESULTADO FINAL: 14/14 PRUEBAS DE HU-12 SUPERADAS EXITOSAMENTE")
        print(" [ESTADO: CERTIFICADO] Orquestación polimórfica y despacho validados.")
        print("=" * 80)
    return resultado.wasSuccessful()


if __name__ == "__main__":
    exito = ejecutar_suite()
    sys.exit(0 if exito else 1)
