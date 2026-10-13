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
    print(" SKYROUTE - PRUEBA DE INTEGRACION ORQUESTADOR (HU-06)")
    print(" Responsable: Valery Arboleda Ardila")
    print("==========================================================\n")

    # 1. Instanciacion de la Torre de Control
    print("[1] Inicializando SistemaCentroControl...")
    centro_control = SistemaCentroControl(lat_base=6.2089, lon_base=-75.5684)
    print(f"    -> {repr(centro_control)}\n")

    # 2. Registro de Usuarios
    print("[2] Registrando usuarios en la plataforma...")
    cliente_valery = Usuario(id_usuario="USR-VAL-01", nombre="Valery Arboleda", rol="CLIENTE")
    operador_juan = Usuario(id_usuario="USR-OPE-02", nombre="Juan Manuel Pava", rol="OPERADOR_VUELO")
    centro_control.registrar_usuario(cliente_valery)
    centro_control.registrar_usuario(operador_juan)
    print(f"    -> Usuarios activos: {len(centro_control.usuarios_registrados)}\n")

    # 3. Registro de Flota de Drones
    print("[3] Registrando aeronaves en la flota...")
    dron_vigilancia = Dron(
        id_dron="DRON-VIG-01",
        modelo_aeronave="DJI-Matrice-300",
        categoria="VIGILANCIA",
        velocidad_promedio_kmh=65.0
    )
    dron_entrega = Dron(
        id_dron="DRON-ENT-02",
        modelo_aeronave="DJI-FlyCart-30",
        categoria="ENTREGA_LIGERA",
        velocidad_promedio_kmh=55.0
    )
    dron_carga = Dron(
        id_dron="DRON-CAR-03",
        modelo_aeronave="HeavyLifter-X8",
        categoria="CARGA_PESADA",
        velocidad_promedio_kmh=45.0
    )
    centro_control.agregar_dron(dron_vigilancia)
    centro_control.agregar_dron(dron_entrega)
    centro_control.agregar_dron(dron_carga)
    print(f"    -> Flota total: {len(centro_control.flota_drones)} aeronaves registradas\n")

    # 4. Registro de Pedidos
    print("[4] Registrando pedidos en el centro de control...")
    pedido_1 = Pedido(
        id_pedido="PED-2026-101",
        usuario_solicitante=cliente_valery,
        categoria_requerida="ENTREGA_LIGERA",
        coordenada_destino=(6.2089, -75.5684),
        peso_carga_kg=2.0
    )
    pedido_2 = Pedido(
        id_pedido="PED-2026-102",
        usuario_solicitante=cliente_valery,
        categoria_requerida="CARGA_PESADA",
        coordenada_destino=(6.2442, -75.5812),
        peso_carga_kg=15.5
    )
    centro_control.registrar_pedido(pedido_1)
    centro_control.registrar_pedido(pedido_2)
    print(f"    -> Pedidos pendientes: {len(centro_control.pedidos)}\n")

    # 5. Asignacion Inteligente de Drones (Cruce de Categorias)
    print("[5] Ejecutando algoritmo de asignacion inteligente...")
    asignacion_1 = centro_control.asignar_dron_a_pedido("PED-2026-101")
    asignacion_2 = centro_control.asignar_dron_a_pedido("PED-2026-102")
    print(f"    -> Asignacion Pedido 1: {asignacion_1} (Dron: {pedido_1.dron_asignado.id_dron})")
    print(f"    -> Asignacion Pedido 2: {asignacion_2} (Dron: {pedido_2.dron_asignado.id_dron})\n")

    # 6. Refresco de Datos de Flota bajo Demanda (RF-05)
    print("[6] Refrescando datos de la flota bajo demanda (RF-05)...")
    centro_control.refrescar_datos_flota()
    print()

    # 7. Protocolo de Retorno a Base Post-Mision (RF-09)
    print("[7] Gestionando retorno a base post-mision (RF-09)...")
    retorno_exitoso = centro_control.gestionar_retorno_a_base("DRON-ENT-02")
    print(f"    -> Retorno activado para DRON-ENT-02: {retorno_exitoso}")
    print(f"    -> Estado DRON-ENT-02: retornando={dron_entrega.retornando_a_base}, en_mision={dron_entrega.en_mision}, disponible={dron_entrega.disponible}\n")

    # 8. Validaciones Defensivas del Orquestador
    print("[8] Ejecutando pruebas defensivas...")
    errores_controlados = 0
    try:
        centro_control.registrar_usuario(cliente_valery)  # Duplicado
    except ValueError:
        errores_controlados += 1

    try:
        centro_control.agregar_dron(dron_entrega)  # Duplicado
    except ValueError:
        errores_controlados += 1

    try:
        centro_control.registrar_pedido(pedido_1)  # Duplicado
    except ValueError:
        errores_controlados += 1

    if not centro_control.asignar_dron_a_pedido("PED-INEXISTENTE"):
        errores_controlados += 1

    if not centro_control.gestionar_retorno_a_base("DRON-VIG-01"):  # No esta en mision
        errores_controlados += 1

    print(f"    -> Validaciones superadas: {errores_controlados}/5 controles defensivos verificados exitosamente.\n")

    # 9. Estado Final y Resumen de Auditoria
    print("[9] Estado consolidado de la Torre de Control:")
    print(centro_control)
    print(f"Ultimo registro de auditoria emitido:")
    print(centro_control.historial_logs[-1].formatear_registro())

    print("==========================================================")
    print(" INTEGRACION GENERAL HU-06 COMPLETADA EXITOSAMENTE")
    print("==========================================================")



if __name__ == "__main__":
    main()


