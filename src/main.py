from src.excepciones.errores import (
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
    CoordenadaInvalidaError,
)
from src.telemetria.telemetria import TelemetriaDrone
from src.geodesia.calculador import CalculadorGeodesico
from src.flota.dron import Dron
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.control.log_operacion import LogOperacion
from src.control.centro_control import SistemaCentroControl


def main():
    print("==========================================================")
    print(" SKYROUTE - PRUEBA DE INTEGRACION MODULO HU-05")
    print(" Responsable: Valery Arboleda Ardila")
    print("==========================================================\n")

    # 1. Creacion y validacion de Usuario
    print("[1] Creando usuario solicitante...")
    cliente = Usuario(id_usuario="USR-VAL-01", nombre="Valery Arboleda", rol="CLIENTE")
    print(f"    -> {cliente}")
    print(f"    -> Rol valido: {cliente.validar_rol()} | Usuario valido: {cliente.validar_usuario()}\n")

    # 2. Creacion de Pedido
    print("[2] Registrando solicitud de pedido...")
    destino_entrega = (6.2089, -75.5684)  # El Poblado, Medellin
    pedido = Pedido(
        id_pedido="PED-2026-001",
        usuario_solicitante=cliente,
        categoria_requerida="ENTREGA_LIGERA",
        coordenada_destino=destino_entrega,
        peso_carga_kg=1.8
    )
    print(f"    -> {pedido}")
    print(f"    -> Estado inicial: {pedido.estado} | Dron vinculado: {pedido.dron_asignado}\n")

    # 3. Log de creacion de pedido
    print("[3] Generando log de auditoria para creacion de pedido...")
    log_creacion = LogOperacion(
        id_log="LOG-001",
        tipo_evento="CREACION_PEDIDO",
        id_pedido=pedido.id_pedido,
        detalles="Solicitud de entrega ligera registrada con exito."
    )
    print(log_creacion.formatear_registro())

    # 4. Creacion de Dron y Vinculacion
    print("[4] Instanciando dron y vinculando al pedido...")
    dron_entrega = Dron(
        id_dron="DRON-EL-01",
        modelo_aeronave="DJI-FlyCart-30",
        categoria="ENTREGA_LIGERA",
        velocidad_promedio_kmh=55.0
    )
    pedido.actualizar_estado("ASIGNADO")
    pedido.vincular_dron(dron_entrega)
    print(f"    -> {pedido}")
    print(f"    -> Dron asignado: {pedido.dron_asignado.id_dron} ({pedido.dron_asignado.modelo_aeronave})\n")

    # 5. Log de asignacion
    print("[5] Generando log de auditoria para asignacion...")
    log_asignacion = LogOperacion(
        id_log="LOG-002",
        tipo_evento="ASIGNACION_DRON",
        id_dron=dron_entrega.id_dron,
        id_pedido=pedido.id_pedido,
        detalles=f"Dron {dron_entrega.id_dron} asignado al pedido {pedido.id_pedido}."
    )
    print(log_asignacion.formatear_registro())

    # 6. Prueba defensiva (rechazo de valores invalidos)
    print("[6] Validando rechazo de datos invalidos...")
    errores_atrapados = 0
    try:
        Usuario("U2", "Invalido", "ROL_FALSO")
    except ValueError:
        errores_atrapados += 1

    try:
        Pedido("PED-ERR", cliente, "CATEGORIA_INVENTADA", destino_entrega)
    except ValueError:
        errores_atrapados += 1

    try:
        pedido.vincular_dron("NO_ES_UN_DRON")
    except TypeError:
        errores_atrapados += 1

    print(f"    -> Validaciones defensivas superadas exitosamente ({errores_atrapados}/3 errores controlados).\n")
    print("==========================================================")
    print(" PRUEBA DE HUMO HU-05 CONCLUIDA CON EXITO")
    print("==========================================================")


if __name__ == "__main__":
    main()


