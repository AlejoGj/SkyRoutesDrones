# Script de pruebas unitarias para el controlador de tiempo RelojSimulacion
# Responsable: Módulo de Control y Simulación (UDEM APOO 2026-2)

import unittest
from unittest.mock import patch
import time
from src.control.reloj import RelojSimulacion


class TestRelojSimulacion(unittest.TestCase):
    """
    Suite de pruebas para validar la medición no bloqueante de tiempo (Reloj Delta),
    la precisión en la acumulación de segundos y el reinicio de marcas temporales.
    """

    def setUp(self):
        self.reloj = RelojSimulacion()

    def test_inicializacion_correcta(self):
        """Verifica que el reloj inicialice sus marcas temporales con valores válidos y no pausado."""
        self.assertIsInstance(self.reloj.tiempo_inicio, float)
        self.assertIsInstance(self.reloj.ultima_actualizacion, float)
        self.assertGreater(self.reloj.tiempo_inicio, 0.0)
        self.assertEqual(self.reloj.tiempo_inicio, self.reloj.ultima_actualizacion)
        self.assertFalse(self.reloj.pausado)

    def test_obtener_delta_con_demora_real(self):
        """Verifica que obtener_delta() mida el intervalo real transcurrido y sea estrictamente no negativo."""
        time.sleep(0.03)  # Demora controlada de 30 milisegundos
        delta_t = self.reloj.obtener_delta()

        self.assertIsInstance(delta_t, float)
        self.assertGreaterEqual(delta_t, 0.02)  # Mínimo el tiempo esperado
        self.assertLess(delta_t, 0.5)           # Límite superior razonable

    def test_obtener_delta_reinicia_marca_temporal(self):
        """Verifica que invocaciones sucesivas inmediatas a obtener_delta() reinicien el delta a valores cercanos a cero."""
        time.sleep(0.02)
        delta_1 = self.reloj.obtener_delta()
        delta_2 = self.reloj.obtener_delta()  # Inmediata sin demora

        self.assertGreater(delta_1, 0.01)
        self.assertLess(delta_2, delta_1)
        self.assertGreaterEqual(delta_2, 0.0)

    def test_obtener_tiempo_total_acumulativo(self):
        """Verifica que obtener_tiempo_total_seg() acumule el tiempo sin verse afectado por llamadas a obtener_delta()."""
        time.sleep(0.02)
        self.reloj.obtener_delta()  # Consumir delta

        time.sleep(0.02)
        tiempo_total = self.reloj.obtener_tiempo_total_seg()

        self.assertGreaterEqual(tiempo_total, 0.03)

    def test_reiniciar_restablece_origen_temporal(self):
        """Verifica que reiniciar() restablezca tiempo_inicio y ultima_actualizacion al momento presente."""
        time.sleep(0.03)
        self.assertGreater(self.reloj.obtener_tiempo_total_seg(), 0.02)

        self.reloj.reiniciar()
        tiempo_post_reinicio = self.reloj.obtener_tiempo_total_seg()

        # Justo después de reiniciar, el tiempo transcurrido debe ser prácticamente cero
        self.assertLess(tiempo_post_reinicio, 0.05)

    @patch('time.monotonic')
    def test_precision_matematica_con_reloj_simulado(self, mock_monotonic):
        """
        Valida con precisión matemática determinista el avance de tiempo simulado:
        - Avance de 10.5 segundos.
        - Avance posterior de 4.2 segundos.
        """
        # Configurar tiempo inicial simulado: 1000.0 segundos
        mock_monotonic.return_value = 1000.0
        reloj_deterministico = RelojSimulacion()

        # Simular avance de 10.5 segundos (tiempo = 1010.5)
        mock_monotonic.return_value = 1010.5
        delta_1 = reloj_deterministico.obtener_delta()
        self.assertEqual(delta_1, 10.5)
        self.assertEqual(reloj_deterministico.obtener_tiempo_total_seg(), 10.5)

        # Simular avance de 4.25 segundos adicionales (tiempo = 1014.75)
        mock_monotonic.return_value = 1014.75
        delta_2 = reloj_deterministico.obtener_delta()
        self.assertEqual(delta_2, 4.25)
        self.assertEqual(reloj_deterministico.obtener_tiempo_total_seg(), 14.75)

    @patch('time.monotonic')
    def test_garantia_de_no_negatividad(self, mock_monotonic):
        """Verifica que si monotonic() retrocede (caso anómalo extremo), obtener_delta() nunca sea negativo."""
        mock_monotonic.return_value = 500.0
        reloj_seguro = RelojSimulacion()

        # Simular retroceso temporal anómalo
        mock_monotonic.return_value = 495.0
        delta_anomalo = reloj_seguro.obtener_delta()

        self.assertEqual(delta_anomalo, 0.0)

    def test_independencia_entre_instancias(self):
        """Verifica que múltiples instancias de RelojSimulacion sean totalmente autónomas e independientes."""
        reloj_a = RelojSimulacion()
        time.sleep(0.02)
        reloj_b = RelojSimulacion()

        time.sleep(0.02)
        delta_a = reloj_a.obtener_delta()
        delta_b = reloj_b.obtener_delta()

        # Reloj A tuvo más tiempo transcurrido desde su inicio que el Reloj B
        self.assertGreater(delta_a, delta_b)


if __name__ == "__main__":
    print("================================================================================")
    print(" SKYROUTE - PRUEBAS DE INTEGRIDAD: CONTROLADOR RELOJ SIMULACION")
    print(" Responsable: Alejandro Garcia Jimenez / Modulo de Control")
    print("================================================================================\n")
    unittest.main(verbosity=2)
