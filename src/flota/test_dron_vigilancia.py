"""
Suite de Pruebas Unitarias para DronVigilancia (HU-08)
Sprint 2: Herencia, Polimorfismo y Abstracción Formal
"""

import sys
import os
import unittest

# Asegurar resolución del paquete raíz 'src'
RUTA_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if RUTA_RAIZ not in sys.path:
    sys.path.insert(0, RUTA_RAIZ)

from src.flota.dron import Dron
from src.flota.dron_vigilancia import DronVigilancia
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.telemetria.telemetria import TelemetriaDrone


class TestDronVigilancia(unittest.TestCase):
    """Pruebas de herencia, validaciones y polimorfismo para DronVigilancia."""

    def setUp(self):
        self.dron = DronVigilancia(
            resolucion_camara_mp=48,
            vision_nocturna=True,
            frecuencia_transmision_ghz=5.8,
            id_dron="DRON-VIG-01",
            modelo_aeronave="DJI-Matrice-300",
            velocidad_promedio_kmh=65.0,
            kilometraje_total_km=0.0
        )

    def test_01_herencia_y_categoria(self):
        """Verifica que herede de Dron y tenga la categoría fija 'VIGILANCIA'."""
        self.assertTrue(issubclass(DronVigilancia, Dron))
        self.assertIsInstance(self.dron, Dron)
        self.assertEqual(self.dron.categoria, "VIGILANCIA")

    def test_02_atributos_propios(self):
        """Verifica asignación correcta de atributos propios especializados."""
        self.assertEqual(self.dron.resolucion_camara_mp, 48)
        self.assertTrue(self.dron.vision_nocturna)
        self.assertEqual(self.dron.frecuencia_transmision_ghz, 5.8)

    def test_03_validacion_resolucion_camara(self):
        """Verifica validaciones de tipo y rango para resolucion_camara_mp."""
        with self.assertRaises(TypeError):
            DronVigilancia(
                resolucion_camara_mp="48",
                vision_nocturna=True,
                frecuencia_transmision_ghz=5.8,
                id_dron="DRON-TEST",
                modelo_aeronave="Test"
            )
        with self.assertRaises(ValueError):
            DronVigilancia(
                resolucion_camara_mp=0,
                vision_nocturna=True,
                frecuencia_transmision_ghz=5.8,
                id_dron="DRON-TEST",
                modelo_aeronave="Test"
            )

    def test_04_validacion_vision_nocturna(self):
        """Verifica validación de tipo booleano para vision_nocturna."""
        with self.assertRaises(TypeError):
            DronVigilancia(
                resolucion_camara_mp=48,
                vision_nocturna="True",
                frecuencia_transmision_ghz=5.8,
                id_dron="DRON-TEST",
                modelo_aeronave="Test"
            )

    def test_05_validacion_frecuencia_transmision(self):
        """Verifica validaciones de tipo y rango para frecuencia_transmision_ghz."""
        with self.assertRaises(TypeError):
            DronVigilancia(
                resolucion_camara_mp=48,
                vision_nocturna=True,
                frecuencia_transmision_ghz="5.8",
                id_dron="DRON-TEST",
                modelo_aeronave="Test"
            )
        with self.assertRaises(ValueError):
            DronVigilancia(
                resolucion_camara_mp=48,
                vision_nocturna=True,
                frecuencia_transmision_ghz=-1.0,
                id_dron="DRON-TEST",
                modelo_aeronave="Test"
            )

    def test_06_inspeccionar_sistemas_especializados(self):
        """Verifica que el diagnóstico reporte cámara, visión nocturna y enlace de video."""
        reporte_activa = self.dron.inspeccionar_sistemas_especializados()
        self.assertIn("48MP", reporte_activa)
        self.assertIn("ACTIVADA", reporte_activa)
        self.assertIn("5.8GHz", reporte_activa)

        dron_sin_nocturna = DronVigilancia(
            resolucion_camara_mp=24,
            vision_nocturna=False,
            frecuencia_transmision_ghz=2.4,
            id_dron="DRON-VIG-02",
            modelo_aeronave="Matrice-200"
        )
        reporte_desactiva = dron_sin_nocturna.inspeccionar_sistemas_especializados()
        self.assertIn("DESACTIVADA", reporte_desactiva)

    def test_07_calcular_consumo_estimado(self):
        """Verifica el cálculo de consumo polimórfico (1.3% por km)."""
        consumo = self.dron.calcular_consumo_estimado(10.0)
        self.assertAlmostEqual(consumo, 13.0, places=2)

    def test_08_ejecutar_mision(self):
        """Verifica la ejecución de misión simulando escolta y video cifrado."""
        # Configurar telemetría para habilitar despegue
        telemetria = TelemetriaDrone(
            id_dron="DRON-VIG-01",
            bateria=100.0,
            altitud=0.0,
            estado_motores="APAGADOS",
            coordenadas=(6.2089, -75.5684)
        )
        self.dron.asignar_telemetria(telemetria)

        usuario = Usuario("USR-01", "Valery Arboleda", "CLIENTE")
        pedido = Pedido(
            id_pedido="PED-VIG-01",
            usuario_solicitante=usuario,
            categoria_requerida="VIGILANCIA",
            coordenada_destino=(6.2500, -75.5700),
            peso_carga_kg=1.0
        )

        reporte = self.dron.ejecutar_mision(pedido)
        self.assertIsInstance(reporte, dict)
        self.assertEqual(reporte.get("instrumental_activado"), "CAMARAS_Y_VIDEO_CIFRADO")
        self.assertEqual(reporte.get("estado_especifico"), "Escolta finalizada sin anomalías")
        self.assertTrue(self.dron.en_mision)
        self.assertFalse(self.dron.disponible)


def ejecutar_pruebas():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDronVigilancia)
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    if resultado.wasSuccessful():
        print("\n" + "=" * 80)
        print(" RESULTADO FINAL: 8/8 PRUEBAS DE DRONVIGILANCIA SUPERADAS EXITOSAMENTE")
        print(" [ESTADO: CERTIFICADO] HU-08 cumple con todos los criterios de aceptación.")
        print("=" * 80)
    return resultado.wasSuccessful()


if __name__ == "__main__":
    exito = ejecutar_pruebas()
    sys.exit(0 if exito else 1)
