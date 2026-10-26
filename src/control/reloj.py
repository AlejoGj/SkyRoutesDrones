import time

class RelojSimulacion:
    """
    Controlador de tiempo no bloqueante para simulación discreta de telemetría.
    Utiliza time.monotonic() para evitar distorsiones por cambios de hora del SO.
    """
    def __init__(self):
        self.tiempo_inicio = time.monotonic()
        self.ultima_actualizacion = self.tiempo_inicio
        self.pausado = False

    def obtener_tiempo_total_seg(self) -> float:
        """Retorna los segundos totales transcurridos desde que inició el sistema."""
        return round(time.monotonic() - self.tiempo_inicio, 2)

    def obtener_delta(self) -> float:
        """
        Retorna los segundos exactos transcurridos desde la última invocación del hook.
        Reinicia la marca temporal para el siguiente ciclo.
        """
        ahora = time.monotonic()
        delta_t = ahora - self.ultima_actualizacion
        self.ultima_actualizacion = ahora
        return max(0.0, delta_t)

    def reiniciar(self):
        """Reinicia el reloj de simulación."""
        self.tiempo_inicio = time.monotonic()
        self.ultima_actualizacion = self.tiempo_inicio