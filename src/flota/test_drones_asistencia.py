# Script de pruebas exhaustivas para las subclases de drones de asistencia y contingencia
# Historia de Usuario: HU-11 (Valery Arboleda Ardila)
# Sprint 2: Herencia, Polimorfismo y Abstracción Formal

import sys
from pathlib import Path

# Garantizar resolucion del modulo src ejecutando directamente o como modulo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.flota.dron import Dron
from src.flota.dron_inspeccion import DronInspeccion

from src.flota.dron_rescate import DronRescate
from src.telemetria.telemetria import TelemetriaDrone
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido


def ejecutar_pruebas():
    print("================================================================================")
    print(" SKYROUTE - PRUEBAS DE HERENCIA Y POLIMORFISMO: DRONES DE ASISTENCIA (HU-11)")
    print(" Responsable: Valery Arboleda Ardila")
    print(" Subclases evaluadas: DronInspeccion y DronRescate")
    print("================================================================================\n")

    pruebas_exitosas = 0
    total_pruebas = 0

    # --------------------------------------------------------------------------
    # 1. VERIFICACION DE ABSTRACCION DE LA CLASE BASE DRON
    # --------------------------------------------------------------------------
    print("--- [1] VERIFICACION DE ABSTRACCION EN CLASE BASE DRON ---")
    total_pruebas += 1
    try:
        Dron("DR-GENERIC", "Generico")
        print("[FALLO] Se permitio instanciar la clase abstracta Dron directamente.")
    except TypeError as e:
        print(f"[EXITO] Intento de instanciar Dron bloqueado por abstraccion: {e}")
        pruebas_exitosas += 1
    print()

    # --------------------------------------------------------------------------
    # 2. INSTANCIACION Y HERENCIA DE DRONINSPECCION
    # --------------------------------------------------------------------------
    print("--- [2] INSTANCIACION Y HERENCIA DE DRONINSPECCION ---")
    total_pruebas += 1
    d_insp = DronInspeccion(
        id_dron="DRON-INSP-01",
        modelo_aeronave="Matrice 300 RTK",
        zoom_optico_x=30,
        rango_sensor_ultrasonico_m=8.5,
        velocidad_promedio_kmh=52.0,
    )
    if isinstance(d_insp, Dron) and d_insp.categoria == "INSPECCION_INFRAESTRUCTURA":
        print(f"[EXITO] DronInspeccion hereda de Dron. Categoria oficial: '{d_insp.categoria}'.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Fallo en herencia o categoria de DronInspeccion.")

    total_pruebas += 1
    if d_insp.zoom_optico_x == 30 and d_insp.rango_sensor_ultrasonico_m == 8.5:
        print(f"[EXITO] Atributos especializados correctos (Zoom: {d_insp.zoom_optico_x}x, Ultrasonico: {d_insp.rango_sensor_ultrasonico_m}m).")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Atributos especializados incorrectos en DronInspeccion.")

    # Validaciones defensivas de DronInspeccion
    total_pruebas += 1
    zoom_rechazado = False
    try:
        DronInspeccion("DR-ERR", "Mod", zoom_optico_x=0)
    except ValueError:
        zoom_rechazado = True
    if zoom_rechazado:
        print("[EXITO] Zoom optico <= 0 rechazado defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se acepto zoom optico <= 0.")

    total_pruebas += 1
    rango_rechazado = False
    try:
        DronInspeccion("DR-ERR", "Mod", rango_sensor_ultrasonico_m=-1.5)
    except ValueError:
        rango_rechazado = True
    if rango_rechazado:
        print("[EXITO] Rango ultrasonico negativo rechazado defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se acepto rango ultrasonico negativo.")
    print()

    # --------------------------------------------------------------------------
    # 3. INSTANCIACION Y HERENCIA DE DRONRESCATE
    # --------------------------------------------------------------------------
    print("--- [3] INSTANCIACION Y HERENCIA DE DRONRESCATE ---")
    total_pruebas += 1
    d_resc = DronRescate(
        id_dron="DRON-RESC-01",
        modelo_aeronave="SAR-Searcher-X",
        camara_termica=True,
        kit_auxilios_equipado=True,
        potencia_altavoz_db=125,
        velocidad_promedio_kmh=68.0,
    )
    if isinstance(d_resc, Dron) and d_resc.categoria == "BUSQUEDA_RESCATE":
        print(f"[EXITO] DronRescate hereda de Dron. Categoria oficial: '{d_resc.categoria}'.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Fallo en herencia o categoria de DronRescate.")

    total_pruebas += 1
    if d_resc.camara_termica is True and d_resc.kit_auxilios_equipado is True and d_resc.potencia_altavoz_db == 125:
        print(f"[EXITO] Atributos especializados de rescate correctos (Termica: {d_resc.camara_termica}, Kit: {d_resc.kit_auxilios_equipado}, Altavoz: {d_resc.potencia_altavoz_db} dB).")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Atributos de rescate incorrectos.")

    # Validaciones defensivas de DronRescate
    total_pruebas += 1
    altavoz_rechazado = False
    try:
        DronRescate("DR-ERR", "Mod", potencia_altavoz_db=-20)
    except ValueError:
        altavoz_rechazado = True
    if altavoz_rechazado:
        print("[EXITO] Potencia de altavoz negativa rechazada defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se acepto potencia de altavoz negativa.")

    total_pruebas += 1
    termica_rechazada = False
    try:
        DronRescate("DR-ERR", "Mod", camara_termica="TRUE_STRING")
    except TypeError:
        termica_rechazada = True
    if termica_rechazada:
        print("[EXITO] Tipo no booleano en camara termica rechazado defensivamente con TypeError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se acepto valor no booleano en camara termica.")
    print()

    # --------------------------------------------------------------------------
    # 4. POLIMORFISMO EN CALCULO DE CONSUMO ENERGETICO
    # --------------------------------------------------------------------------
    print("--- [4] POLIMORFISMO EN CALCULO DE CONSUMO ESTIMADO ---")
    total_pruebas += 1
    distancia_prueba = 12.0  # km
    consumo_insp = d_insp.calcular_consumo_estimado(distancia_prueba)
    consumo_resc = d_resc.calcular_consumo_estimado(distancia_prueba)

    esperado_insp = 12.0 * 1.5  # 18.0%
    esperado_resc = 12.0 * 2.0  # 24.0%

    if abs(consumo_insp - esperado_insp) < 1e-4 and abs(consumo_resc - esperado_resc) < 1e-4:
        print(f"[EXITO] Consumo diferenciado para {distancia_prueba} km:")
        print(f"        -> DronInspeccion: {consumo_insp:.1f}% (factor 1.5 %/km)")
        print(f"        -> DronRescate   : {consumo_resc:.1f}% (factor 2.0 %/km)")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumos polimorficos incorrectos: Insp={consumo_insp}, Resc={consumo_resc}")
    print()

    # --------------------------------------------------------------------------
    # 5. DIAGNOSTICO DE SISTEMAS ESPECIALIZADOS
    # --------------------------------------------------------------------------
    print("--- [5] DIAGNOSTICO DE SISTEMAS ESPECIALIZADOS ---")
    total_pruebas += 1
    diag_insp = d_insp.inspeccionar_sistemas_especializados()
    diag_resc = d_resc.inspeccionar_sistemas_especializados()

    if "Zoom" in diag_insp and ("Ultrasonico" in diag_insp or "Ultrasónico" in diag_insp) and ("Termica" in diag_resc or "Térmica" in diag_resc) and "Altavoz" in diag_resc:
        print(f"[EXITO] Diagnostico Inspeccion : {diag_insp}")
        print(f"[EXITO] Diagnostico Rescate    : {diag_resc}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Textos de diagnostico incorrectos: Insp='{diag_insp}', Resc='{diag_resc}'")
    print()


    # --------------------------------------------------------------------------
    # 6. EJECUCION POLIMORFICA DE MISIONES CON TELEMETRIA Y PEDIDOS
    # --------------------------------------------------------------------------
    print("--- [6] EJECUCION POLIMORFICA DE MISIONES ---")
    # Configurar telemetria para despegue
    telemetria_insp = TelemetriaDrone(
        id_dron=d_insp.id_dron,
        bateria=90.0,
        altitud=0.0,
        estado_motores="APAGADOS",
        coordenadas=(6.2089, -75.5684),
    )
    d_insp.asignar_telemetria(telemetria_insp)

    telemetria_resc = TelemetriaDrone(
        id_dron=d_resc.id_dron,
        bateria=95.0,
        altitud=0.0,
        estado_motores="APAGADOS",
        coordenadas=(6.2089, -75.5684),
    )
    d_resc.asignar_telemetria(telemetria_resc)

    usuario_demo = Usuario("USR-VAL-01", "Valery Arboleda", "OPERADOR_VUELO")
    pedido_insp = Pedido(
        id_pedido="PED-INSP-101",
        usuario_solicitante=usuario_demo,
        categoria_requerida="INSPECCION_INFRAESTRUCTURA",
        coordenada_destino=(6.2505, -75.5681),
    )
    pedido_resc = Pedido(
        id_pedido="PED-RESC-202",
        usuario_solicitante=usuario_demo,
        categoria_requerida="BUSQUEDA_RESCATE",
        coordenada_destino=(6.2800, -75.5400),
    )

    pedido_insp.vincular_dron(d_insp)
    pedido_resc.vincular_dron(d_resc)

    # Ejecutar mision inspeccion
    total_pruebas += 1
    reporte_insp = d_insp.ejecutar_mision(pedido_insp)
    if (
        reporte_insp.get("estado_mision") == "DESPEGUE_EXITOSO"
        and reporte_insp.get("instrumental_activado") == "SENSOR_ULTRASONICO_Y_ZOOM"
        and pedido_insp.estado == "EN_TRANSITO"
        and d_insp.en_mision is True
    ):
        print(f"[EXITO] Mision de inspeccion ejecutada con exito (Instrumental: {reporte_insp.get('instrumental_activado')}).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Mision de inspeccion fallida: {reporte_insp}")

    # Ejecutar mision rescate
    total_pruebas += 1
    reporte_resc = d_resc.ejecutar_mision(pedido_resc)
    if (
        reporte_resc.get("estado_mision") == "DESPEGUE_EXITOSO"
        and reporte_resc.get("instrumental_activado") == "CAMARA_TERMICA_Y_ALTAVOZ"
        and reporte_resc.get("resultado_rescate") == "Kit de auxilios entregado"
        and pedido_resc.estado == "EN_TRANSITO"
        and d_resc.en_mision is True
    ):
        print(f"[EXITO] Mision de rescate ejecutada con exito (Instrumental: {reporte_resc.get('instrumental_activado')}).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Mision de rescate fallida: {reporte_resc}")
    print()

    # --------------------------------------------------------------------------
    # 7. FICHA TECNICA MULTILINEA ENRIQUECIDA (__STR__)
    # --------------------------------------------------------------------------
    print("--- [7] FICHAS TECNICAS MULTILINEA (__STR__) ---")
    total_pruebas += 1
    ficha_insp = str(d_insp)
    ficha_resc = str(d_resc)
    if "Sensor Ultrasónico" in ficha_insp and "Térmica" in ficha_resc and "Altavoz" in ficha_resc:
        print("[EXITO] Representaciones multilineas __str__ incluyen el instrumental especializado.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Instrumental ausente en fichas tecnicas multilineas.")
    print()

    # --------------------------------------------------------------------------
    # RESUMEN DE PRUEBAS
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(f" RESULTADO FINAL: {pruebas_exitosas}/{total_pruebas} PRUEBAS SUPERADAS EXITOSAMENTE")
    if pruebas_exitosas == total_pruebas:
        print(" [ESTADO: CERTIFICADO] La HU-11 cumple con todos los criterios de aceptacion.")
    else:
        print(" [ESTADO: INCOMPLETO] Se detectaron fallos en la suite de pruebas.")
    print("================================================================================")
    return pruebas_exitosas == total_pruebas


if __name__ == "__main__":
    ejecutar_pruebas()
