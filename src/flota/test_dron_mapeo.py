"""
Suite de Pruebas Unitarias para DronMapeo (HU-08)
Historia de Usuario: HU-08 (Juan Manuel Pava Higuita)
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
from src.flota.dron_mapeo import DronMapeo
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.telemetria.telemetria import TelemetriaDrone


class TestDronMapeo(unittest.TestCase):
    """Pruebas unitarias de herencia, validaciones defensivas y polimorfismo para DronMapeo."""

    def setUp(self):
        self.dron = DronMapeo(
            id_dron="DRON-MAP-01",
            modelo_aeronave="GeoMapper-RTK-3D",
            tiene_sensor_lidar=True,
            precision_gps_cm=2.5,
            capacidad_almacenamiento_tb=2.0,
            velocidad_promedio_kmh=45.0,
            kilometraje_total_km=0.0,
        )

    def test_01_herencia_y_categoria(self):
        """Verifica que DronMapeo herede de Dron y tenga la categoría oficial 'MAPEO_TOPOGRAFICO'."""
        self.assertTrue(issubclass(DronMapeo, Dron))
        self.assertIsInstance(self.dron, Dron)
        self.assertEqual(self.dron.categoria, "MAPEO_TOPOGRAFICO")

    def test_02_atributos_propios(self):
        """Verifica asignación correcta de atributos propios especializados."""
        self.assertTrue(self.dron.tiene_sensor_lidar)
        self.assertEqual(self.dron.precision_gps_cm, 2.5)
        self.assertEqual(self.dron.capacidad_almacenamiento_tb, 2.0)

    def test_03_validacion_sensor_lidar(self):
        """Verifica validación booleana estricta para el sensor LiDAR."""
        with self.assertRaises(TypeError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                tiene_sensor_lidar="True",
            )
        with self.assertRaises(TypeError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                tiene_sensor_lidar=1,
            )

    def test_04_validacion_precision_gps(self):
        """Verifica validaciones de tipo numérico y rango positivo para precision_gps_cm."""
        with self.assertRaises(TypeError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                precision_gps_cm="2.5",
            )
        with self.assertRaises(TypeError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                precision_gps_cm=True,
            )
        with self.assertRaises(ValueError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                precision_gps_cm=0.0,
            )
        with self.assertRaises(ValueError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                precision_gps_cm=-1.5,
            )

    def test_05_validacion_almacenamiento(self):
        """Verifica validaciones de tipo numérico y rango positivo para capacidad_almacenamiento_tb."""
        with self.assertRaises(TypeError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                capacidad_almacenamiento_tb="2TB",
            )
        with self.assertRaises(ValueError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                capacidad_almacenamiento_tb=0.0,
            )
        with self.assertRaises(ValueError):
            DronMapeo(
                id_dron="DR-TEST",
                modelo_aeronave="Test",
                capacidad_almacenamiento_tb=-2.0,
            )

    def test_06_calcular_consumo_estimado(self):
        """Verifica la tasa polimórfica de consumo del 1.4% por km y manejo defensivo."""
        # 10 km * 1.4% = 14.0%
        self.assertAlmostEqual(self.dron.calcular_consumo_estimado(10.0), 14.0, places=2)
        # Distancia nula o negativa retorna 0.0
        self.assertEqual(self.dron.calcular_consumo_estimado(0.0), 0.0)
        self.assertEqual(self.dron.calcular_consumo_estimado(-5.0), 0.0)

    def test_07_inspeccionar_sistemas_especializados(self):
        """Verifica que el diagnóstico técnico reporte el sensor LiDAR, GPS RTK y almacenamiento."""
        diag = self.dron.inspeccionar_sistemas_especializados()
        self.assertIn("LiDAR", diag)
        self.assertIn("Precisión GPS", diag)
        self.assertIn("Almacenamiento", diag)
        self.assertIn("OPERATIVOS", diag)

    def test_08_ejecutar_mision(self):
        """Verifica el flujo polimórfico de ejecución de misión cartográfica con telemetría."""
        telemetria = TelemetriaDrone(
            id_dron=self.dron.id_dron,
            bateria=90.0,
            altitud=0.0,
            estado_motores="STANDBY",
            coordenadas=(6.2089, -75.5684),
        )
        self.dron.asignar_telemetria(telemetria)

        usuario = Usuario(id_usuario="USR-01", nombre="Cliente Catastro", rol="CLIENTE")
        pedido = Pedido(
            id_pedido="PED-MAP-001",
            usuario_solicitante=usuario,
            categoria_requerida="MAPEO_TOPOGRAFICO",
            coordenada_destino=(6.2505, -75.5681),
        )
        pedido.vincular_dron(self.dron)

        reporte = self.dron.ejecutar_mision(pedido)

        self.assertEqual(reporte["estado_mision"], "DESPEGUE_EXITOSO")
        self.assertEqual(reporte["instrumental_activado"], "SENSOR_LIDAR_Y_GPS_RTK")
        self.assertEqual(reporte["precision_levantamiento_cm"], 2.5)
        self.assertEqual(reporte["espacio_almacenamiento_tb"], 2.0)
        self.assertEqual(pedido.estado, "EN_TRANSITO")
        self.assertTrue(self.dron.en_mision)

    def test_09_fichas_tecnicas_str_y_repr(self):
        """Verifica que __str__ y __repr__ incluyan los aditamentos especializados."""
        ficha_str = str(self.dron)
        self.assertIn("Instrumental LiDAR", ficha_str)
        self.assertIn("Precisión GPS", ficha_str)
        self.assertIn("Almacenamiento", ficha_str)

        ficha_repr = repr(self.dron)
        self.assertIn("tiene_sensor_lidar=True", ficha_repr)
        self.assertIn("precision_gps_cm=2.5", ficha_repr)
        self.assertIn("capacidad_almacenamiento_tb=2.0", ficha_repr)


if __name__ == "__main__":
    unittest.main()
