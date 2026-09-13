# Módulo de registro y auditoría de eventos
# Responsable: Valery Arboleda Ardila

from datetime import datetime


class LogOperacion:
    def __init__(
        self,
        id_log: str,
        fecha_hora: str = None,
        tipo_evento: str = "",
        id_dron: str = None,
        id_pedido: str = None,
        detalles: str = ""
    ) -> None:
        # ID_LOG
        if not isinstance(id_log, str):
            raise TypeError("El ID debe ser una cadena de texto. Por favor, intenta de nuevo")

        if not id_log.strip():
            raise ValueError("El ID no puede estár vacío!")
        self.id_log = id_log.strip()

        # FECHA Y HORA (Permite timestamp manual o automatico por omision)
        if fecha_hora is None:
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not isinstance(fecha_hora, str):
            raise TypeError("La fecha y hora deben ser una cadena de texto. Por favor, intenta de nuevo")

        if not fecha_hora.strip():
            raise ValueError("La fecha no puede estár vacía!")
        self.fecha_hora = fecha_hora.strip()

        # TIPO_EVENTO
        if not isinstance(tipo_evento, str):
            raise TypeError("El tipo de evento debe ser una cadena de texto. Por favor, intenta de nuevo")

        if not tipo_evento.strip():
            raise ValueError("El tipo de evento no puede estár vacío!")
        self.tipo_evento = tipo_evento.strip().upper()

        # DATOS ADICIONALES
        self.id_dron = id_dron.strip() if (id_dron and isinstance(id_dron, str)) else "No aplica"
        self.id_pedido = id_pedido.strip() if (id_pedido and isinstance(id_pedido, str)) else "No aplica"
        self.detalles = detalles.strip() if (detalles and isinstance(detalles, str)) else "No hay detalles adicionales"

    def formatear_registro(self) -> str:
        linea = "-" * 40
        return (
            f"\n {linea} \n"
            f" Fecha y hora: {self.fecha_hora} \n"
            f" ID Log: {self.id_log} \n"
            f" Evento: {self.tipo_evento} \n"
            f" Dron: {self.id_dron} \n"
            f" ID Pedido: {self.id_pedido} \n"
            f" Detalles: {self.detalles} \n"
            f" {linea} \n"
        )

    def __str__(self) -> str:
        return self.formatear_registro()

    def __repr__(self) -> str:
        return (
            f"LogOperacion(id_log='{self.id_log}', fecha_hora='{self.fecha_hora}', "
            f"tipo_evento='{self.tipo_evento}', id_dron='{self.id_dron}', id_pedido='{self.id_pedido}')"
        )

