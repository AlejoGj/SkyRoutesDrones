import unittest
import time
from src.flota.dron import Dron
from src.pedidos.pedido import Pedido
from src.usuarios.usuario import Usuario
from src.telemetria.telemetria import TelemetriaDrone
from src.control.simulador import SimuladorVuelo
from src.control.reloj import RelojSimulacion
from src.servicios.clima import ServicioClimaAburra
from src.geodesia.calculador import CalculadorGeodesico


class DronMock(Dron):
    """Subclase concreta de Dron para pruebas unitarias de simulación."""
    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        return round(distancia_km * 1.5, 2)

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        return super().ejecutar_mision(pedido)

    def inspeccionar_sistemas_especializados(self) -> str:
        return "SISTEMAS_OK"


class TestSimuladorVuelo(unittest.TestCase):
    def setUp(self):
        self.calculador = CalculadorGeodesico()
        self.simulador = SimuladorVuelo(calculador=self.calculador)

        self.coord_base = (6.2089, -75.5684)  # El Poblado
        self.coord_destino = (6.2442, -75.5812)  # Medellín Centro

        self.dron = DronMock(
            id_dron="DRON-SIM-01",
            modelo_aeronave="SkyCargo-X1",
            velocidad_promedio_kmh=60.0,
            kilometraje_total_km=0.0,
            disponible=True,
            calculador=self.calculador
        )

        self.telemetria = TelemetriaDrone(
            id_dron="DRON-SIM-01",
            bateria=100.0,
            altitud=0.0,
            estado_motores="STANDBY",
            coordenadas=self.coord_base
        )
        self.dron.asignar_telemetria(self.telemetria)

        self.usuario = Usuario(id_usuario="USR-01", nombre="Alejandro", rol="CLIENTE")
        self.pedido = Pedido(
            id_pedido="PED-SIM-01",
            usuario_solicitante=self.usuario,
            categoria_requerida="ENTREGA_LIGERA",
            coordenada_destino=self.coord_destino,
            peso_carga_kg=2.0
        )

    def test_simulacion_estacionario(self):
        """Si delta_t es 0 o el dron no está en misión ni retornando, no avanza."""
        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=0.0)
        self.assertEqual(reporte["estado"], "ESTACIONARIO")
        self.assertEqual(reporte["delta_km"], 0.0)

    def test_simulacion_paso_parcial_en_vuelo(self):
        """Un dron en misión avanza proporcionalmente con delta_t sin llegar al destino."""
        self.dron.ejecutar_mision(self.pedido)
        self.assertTrue(self.dron.en_mision)

        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=30.0, factor_clima=1.0)
        self.assertEqual(reporte["id_dron"], "DRON-SIM-01")
        self.assertEqual(reporte["estado"], "EN_VUELO")
        self.assertGreater(reporte["delta_km"], 0.0)
        self.assertLess(reporte["bateria_actual"], 100.0)
        self.assertFalse(reporte["ha_llegado"])
        self.assertEqual(self.pedido.estado, "EN_TRANSITO")

    def test_simulacion_entrega_y_retorno_parcial_mismo_tick(self):
        """
        Multi-Fase: Delta t es suficiente para cubrir la ida (entrega) y avanzar
        parcialmente en el camino de regreso hacia la base dentro del mismo tick.
        """
        self.dron.ejecutar_mision(self.pedido)
        distancia_ida = self.calculador.calcular_haversine(self.coord_base, self.coord_destino)
        # A 60 km/h (1 km/min = 0.01667 km/s): tiempo ida = dist / 0.01667
        tiempo_ida_seg = (distancia_ida / (60.0 / 3600.0))
        # Asignamos tiempo de ida + 60 segundos adicionales para el retorno
        delta_t = tiempo_ida_seg + 60.0

        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=delta_t, factor_clima=1.0)

        # 1. El pedido debió completarse en este mismo tick
        self.assertEqual(self.pedido.estado, "COMPLETADO")
        self.assertFalse(self.dron.en_mision)
        # 2. El dron debe estar en fase de retorno y haber avanzado más que la distancia de ida
        self.assertTrue(self.dron.retornando_a_base)
        self.assertEqual(reporte["estado"], "RETORNANDO_A_BASE")
        self.assertGreater(reporte["delta_km"], distancia_ida)
        # 3. Odómetro debe acumular la ida más el tramo de vuelta
        self.assertGreater(self.dron.kilometraje_total_km, distancia_ida)

    def test_simulacion_ciclo_completo_ida_y_retorno_un_solo_tick(self):
        """
        Multi-Fase: Con un delta_t suficientemente grande (ej. 15 minutos),
        el dron va al cliente, entrega el paquete, regresa a la base central,
        aterriza y queda disponible en un solo paso temporal.
        """
        self.dron.ejecutar_mision(self.pedido)

        # 1000 segundos (> 16 min) es más que suficiente para ida y vuelta (~8.3 km a 60 km/h = ~500 s)
        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=1000.0)

        # Verificaciones del pedido
        self.assertEqual(self.pedido.estado, "COMPLETADO")
        # Verificaciones del dron
        self.assertFalse(self.dron.en_mision)
        self.assertFalse(self.dron.retornando_a_base)
        self.assertTrue(self.dron.disponible)
        self.assertEqual(reporte["estado"], "LLEGADA_A_BASE")
        self.assertTrue(reporte["ha_llegado"])
        self.assertEqual(self.telemetria.altitud, 0.0)
        self.assertEqual(self.telemetria.estado_motores, "STANDBY")
        # Verificación de coordenadas finales en la base
        self.assertEqual(self.telemetria.coordenadas, self.coord_base)
        # Verificación del odómetro (ida + vuelta completa)
        distancia_ida = self.calculador.calcular_haversine(self.coord_base, self.coord_destino)
        self.assertAlmostEqual(self.dron.kilometraje_total_km, distancia_ida * 2, delta=0.1)


class TestComponentesAuxiliaresSimulacion(unittest.TestCase):
    def test_reloj_simulacion_delta_y_reinicio(self):
        """Verifica que RelojSimulacion mida intervalos monotonic sin valores negativos."""
        reloj = RelojSimulacion()
        time.sleep(0.01)
        delta_t = reloj.obtener_delta()
        self.assertGreater(delta_t, 0.0)
        self.assertGreater(reloj.obtener_tiempo_total_seg(), 0.0)

        reloj.reiniciar()
        self.assertLess(reloj.obtener_tiempo_total_seg(), 0.1)

    def test_servicio_clima_aburra_estructura_y_fallback(self):
        """Verifica que ServicioClimaAburra retorne las claves requeridas y active fallback seguro."""
        servicio = ServicioClimaAburra()
        clima = servicio.obtener_condiciones("Medellin_Centro")

        self.assertIn("nodo", clima)
        self.assertIn("temperatura_c", clima)
        self.assertIn("viento_kmh", clima)
        self.assertIn("factor_velocidad", clima)
        self.assertIn("vuelo_seguro", clima)
        self.assertIsInstance(clima["factor_velocidad"], (int, float))
        self.assertGreaterEqual(clima["factor_velocidad"], 0.1)


if __name__ == "__main__":
    unittest.main()
