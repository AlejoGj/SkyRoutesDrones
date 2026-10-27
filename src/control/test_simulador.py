import unittest
import time
from src.flota.dron import Dron
from src.pedidos.pedido import Pedido
from src.usuarios.usuario import Usuario
from src.telemetria.telemetria import TelemetriaDrone
from src.control.centro_control import SistemaCentroControl
from src.control.simulador import SimuladorVuelo
from src.control.reloj import RelojSimulacion
from src.servicios.clima import ServicioClimaAburra
from src.geodesia.calculador import CalculadorGeodesico


from src.excepciones.errores import ActualizarEstadoDronError


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

        self.coord_base = SistemaCentroControl.COORDENADAS_BASE  # Olaya Herrera (6.219603, -75.586792)
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

    def test_bloqueo_despegue_bateria_cero(self):
        """No permite despegar si el dron tiene batería 0.0%."""
        self.telemetria.actualizar_trama(bateria=0.0)
        with self.assertRaises(ActualizarEstadoDronError) as ctx:
            self.dron.ejecutar_mision(self.pedido)
        self.assertIn("agotada", str(ctx.exception).lower())

    def test_bloqueo_despegue_bateria_insuficiente_para_retorno(self):
        """
        Bloquea el despegue si la batería alcanza para llegar al destino (ida),
        pero no para completar la operación completa (ida + retorno a la base).
        """
        distancia_ida = self.calculador.calcular_haversine(self.coord_base, self.coord_destino)
        consumo_ida = self.dron.calcular_consumo_estimado(distancia_ida)
        # Batería suficiente para ida pero insuficiente para el retorno a base
        self.telemetria.actualizar_trama(bateria=consumo_ida + 0.5)
        with self.assertRaises(ActualizarEstadoDronError) as ctx:
            self.dron.ejecutar_mision(self.pedido)
        self.assertIn("batería insuficiente", str(ctx.exception).lower())
        self.assertIn("retorno", str(ctx.exception).lower())

    def test_simulacion_bloqueo_dron_bateria_cero_no_se_desplaza(self):
        """Un dron con batería 0.0% no puede avanzar en la simulación temporal."""
        self.telemetria.actualizar_trama(bateria=0.0)
        self.dron.en_mision = True
        coord_inicial = self.telemetria.coordenadas

        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=30.0)
        self.assertEqual(reporte["estado"], "BATERIA_AGOTADA")
        self.assertEqual(reporte["delta_km"], 0.0)
        self.assertEqual(reporte["bateria_actual"], 0.0)
        self.assertEqual(self.telemetria.coordenadas, coord_inicial)
        self.assertFalse(self.dron.en_mision)
        self.assertFalse(self.dron.disponible)

    def test_simulacion_agotamiento_bateria_en_vuelo_aterrizaje_emergencia(self):
        """
        Si la batería se agota en pleno vuelo, el dron recorre únicamente la
        distancia permitida por su energía remanente y realiza aterrizaje de emergencia.
        """
        # Le damos batería suficiente para autorizar despegue (ida + vuelta ~9.3%)
        self.telemetria.actualizar_trama(bateria=15.0)
        self.dron.ejecutar_mision(self.pedido)

        # Forzamos batería remanente mínima simulando pérdida acelerada
        self.telemetria.actualizar_trama(bateria=1.0)
        reporte = self.simulador.avanzar_paso_tiempo(self.dron, delta_t=100.0)

        self.assertEqual(reporte["estado"], "BATERIA_AGOTADA")
        self.assertEqual(reporte["bateria_actual"], 0.0)
        self.assertGreater(reporte["delta_km"], 0.0)
        self.assertEqual(self.telemetria.altitud, 0.0)
        self.assertFalse(self.dron.en_mision)
        self.assertFalse(self.dron.disponible)

    def test_recarga_bateria_en_base(self):
        """Verifica que el dron pueda recargar batería cuando está en la base."""
        self.telemetria.actualizar_trama(bateria=5.0)
        self.dron.recargar_bateria(100.0)
        self.assertEqual(self.telemetria.bateria, 100.0)
        self.assertTrue(self.dron.disponible)

        # No debe permitir recargar mientras está en misión
        self.dron.en_mision = True
        with self.assertRaises(ActualizarEstadoDronError):
            self.dron.recargar_bateria(100.0)

    def test_centro_control_no_asigna_dron_con_bateria_insuficiente(self):
        """Verifica que el centro de control no asigne una aeronave si su batería no cubre ida y vuelta."""
        centro = SistemaCentroControl()
        self.dron.categoria = "ENTREGA_LIGERA"
        # Batería insuficiente para ida y vuelta (~9.3% requerido)
        self.telemetria.actualizar_trama(bateria=5.0)
        centro.agregar_dron(self.dron)
        centro.registrar_pedido(self.pedido)

        asignado = centro.asignar_dron_a_pedido(self.pedido.id_pedido)
        self.assertFalse(asignado)
        self.assertIsNone(self.pedido.dron_asignado)

    def test_simulador_emite_logs_llegada_destino_y_base(self):
        """Verifica que el simulador registre logs de LLEGADA_A_DESTINO y LLEGADA_A_BASE en el centro de control."""
        centro = SistemaCentroControl()
        simulador_con_logs = SimuladorVuelo(calculador=self.calculador, centro_control=centro)

        self.dron.ejecutar_mision(self.pedido)
        centro.generar_log(
            evento="DESPEGUE_MISION",
            id_dron=self.dron.id_dron,
            id_pedido=self.pedido.id_pedido,
            detalles="Despegue de prueba"
        )

        # Un tick suficientemente largo para completar la misión completa (ida + retorno)
        simulador_con_logs.avanzar_paso_tiempo(self.dron, delta_t=1000.0)

        tipos_evento = [log.tipo_evento for log in centro.historial_logs]
        self.assertIn("DESPEGUE_MISION", tipos_evento)
        self.assertIn("LLEGADA_A_DESTINO", tipos_evento)
        self.assertIn("LLEGADA_A_BASE", tipos_evento)


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
