# Script de pruebas y demostracion del modulo de telemetria
# Historia de Usuario: HU-01 (Alejandro Garcia Jimenez)

import sys
from pathlib import Path

# Garantizar resolucion del modulo src ejecutando directamente o como modulo
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# 1. Entidad principal bajo prueba
from src.telemetria.telemetria import TelemetriaDrone

# 2. Excepciones de dominio asociadas (orden alfabetico)
from src.excepciones.errores import (
    AltitudInvalidaError,
    BateriaInvalidaError,
    CoordenadaInvalidaError,
    EstadoMotorInvalidoError,
)

# 3. Entidad colaboradora de flota
from src.flota.dron import Dron


def ejecutar_pruebas():
    print("================================================================================ \n"+
    " SKYROUTE - PRUEBA DE INTEGRIDAD (USO DE IA PARA PRUEBAS EXAHUSTIVAS) (HU-01)"+
    " Responsable: Alejandro Garcia \n"+
    "================================================================================\n")

    pruebas_exitosas = 0
    total_pruebas = 0

    # --------------------------------------------------------------------------
    # 1. CASOS DE INSTANCIACION VALIDA Y FORMATO DE CONSOLA (RF-01, RF-04)
    # --------------------------------------------------------------------------
    print("--- [1] INSTANCIACIONES VALIDAS Y REPRESENTACION (RF-01, RF-04) ---")

    # 1.1 Dron en vuelo sobre Medellin (Parque Berrio hacia CC Santafe)
    total_pruebas += 1
    t_vuelo = TelemetriaDrone(
        id_dron="DRON-MED-001",
        bateria=85.5,
        altitud=45.0,
        estado_motores="EN_VUELO",
        coordenadas=(6.2518, -75.5636)
    )
    if t_vuelo.latitud == 6.2518 and t_vuelo.longitud == -75.5636:
        print("[EXITO] Instanciacion de telemetria en vuelo correcta.")
        print(f"        -> __str__ : {t_vuelo}")
        print(f"        -> __repr__: {repr(t_vuelo)}")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Las coordenadas no fueron desempaquetadas adecuadamente.")

    # 1.2 Dron en tierra en base central
    total_pruebas += 1
    t_tierra = TelemetriaDrone(
        id_dron="DRON-MED-002",
        bateria=100.0,
        altitud=0.0,
        estado_motores="STANDBY",
        coordenadas=(6.2089, -75.5684)
    )
    if t_tierra.altitud == 0.0 and t_tierra.estado_motores == "STANDBY":
        print("[EXITO] Instanciacion de telemetria en tierra (base) correcta.")
        print(f"        -> __str__ : {t_tierra}")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Los datos de telemetria en tierra difieren de lo esperado.")

    # 1.3 Validacion autonoma sin argumentos
    total_pruebas += 1
    if t_vuelo.validar_datos() and t_tierra.validar_datos():
        print("[EXITO] Invocacion de validar_datos() sin argumentos auditada correctamente.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] validar_datos() sin argumentos no retorno True.")
    print()

    # --------------------------------------------------------------------------
    # 2. VALIDACIONES DEFENSIVAS Y EXCEPCIONES DE DOMINIO (RF-02)
    # --------------------------------------------------------------------------
    print("--- [2] DISPARO CONTROLADO DE EXCEPCIONES DE DOMINIO (RF-02) ---")

    # 2.1 Bateria negativa (< 0.0%)
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", -5.0, 10.0, "EN_VUELO", (6.25, -75.56))
        print("[FALLO] Bateria negativa debio disparar BateriaInvalidaError.")
    except BateriaInvalidaError as e:
        print(f"[EXITO] Bateria negativa interceptada correctamente: {e}")
        pruebas_exitosas += 1

    # 2.2 Bateria excesiva (> 100.0%)
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 105.0, 10.0, "EN_VUELO", (6.25, -75.56))
        print("[FALLO] Bateria superior al 100% debio disparar BateriaInvalidaError.")
    except BateriaInvalidaError as e:
        print(f"[EXITO] Bateria excesiva interceptada correctamente: {e}")
        pruebas_exitosas += 1

    # 2.3 Altitud sobre el techo aeronautico (> 120.0 m)
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 135.0, "EN_VUELO", (6.25, -75.56))
        print("[FALLO] Altitud mayor a 120m debio disparar AltitudInvalidaError.")
    except AltitudInvalidaError as e:
        print(f"[EXITO] Techo de vuelo superado interceptado correctamente: {e}")
        pruebas_exitosas += 1

    # 2.4 Incoherencia fisica 1: Altitud positiva con motores apagados
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 30.0, "APAGADOS", (6.25, -75.56))
        print("[FALLO] Vuelo con motores apagados debio disparar EstadoMotorInvalidoError.")
    except EstadoMotorInvalidoError as e:
        print(f"[EXITO] Incoherencia (aire con motores apagados) interceptada: {e}")
        pruebas_exitosas += 1

    # 2.5 Incoherencia fisica 2: Altitud 0 con motores en vuelo
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 0.0, "EN_VUELO", (6.25, -75.56))
        print("[FALLO] Tierra con motores en vuelo debio disparar EstadoMotorInvalidoError.")
    except EstadoMotorInvalidoError as e:
        print(f"[EXITO] Incoherencia (tierra con motores en vuelo) interceptada: {e}")
        pruebas_exitosas += 1

    # 2.6 Estado de motor no reconocido en catalogo
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 0.0, "DESCONOCIDO", (6.25, -75.56))
        print("[FALLO] Estado no perteneciente al catalogo debio disparar EstadoMotorInvalidoError.")
    except EstadoMotorInvalidoError as e:
        print(f"[EXITO] Estado fuera de catalogo interceptado correctamente: {e}")
        pruebas_exitosas += 1

    # 2.7 Latitud fuera de límites ([-90.0, 90.0])
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 0.0, "STANDBY", (95.0, -75.56))
        print("[FALLO] Latitud fuera de limites debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Latitud invalida interceptada correctamente: {e}")
        pruebas_exitosas += 1

    # 2.8 Longitud fuera de límites ([-180.0, 180.0])
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 0.0, "STANDBY", (6.25, -190.0))
        print("[FALLO] Longitud fuera de limites debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Longitud invalida interceptada correctamente: {e}")
        pruebas_exitosas += 1

    # 2.9 Formato de coordenadas no valido (string en lugar de tupla)
    total_pruebas += 1
    try:
        TelemetriaDrone("DRON-ERR", 90.0, 0.0, "STANDBY", "6.25,-75.56")
        print("[FALLO] Coordenadas sin tupla debieron disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Formato no tupla interceptado correctamente: {e}")
        pruebas_exitosas += 1
    print()

    # --------------------------------------------------------------------------
    # 3. ACTUALIZACION DE TRAMA BAJO DEMANDA Y ATOMICIDAD (RF-05)
    # --------------------------------------------------------------------------
    print("--- [3] ACTUALIZACION DE TRAMA Y GARANTIA DE ATOMICIDAD (RF-05) ---")

    dron_sensor = TelemetriaDrone("DRON-SENSOR-01", 100.0, 0.0, "STANDBY", (6.2089, -75.5684))
    print(f"Estado inicial del dron: {dron_sensor}")

    # 3.1 Actualizacion exitosa (despegue)
    total_pruebas += 1
    dron_sensor.actualizar_trama(
        bateria=98.0,
        altitud=35.0,
        estado_motores="EN_VUELO",
        coordenadas=(6.2120, -75.5700)
    )
    if dron_sensor.bateria == 98.0 and dron_sensor.altitud == 35.0 and dron_sensor.latitud == 6.2120:
        print(f"[EXITO] Actualizacion valida aplicada con exito:")
        print(f"        -> Nuevo estado: {dron_sensor}")
        pruebas_exitosas += 1
    else:
        print("[FALLO] La actualizacion valida no reflejo los nuevos valores.")

    # 3.2 Actualizacion invalida: verificar que el dron NO corrompe su estado anterior
    total_pruebas += 1
    bateria_previa = dron_sensor.bateria
    altitud_previa = dron_sensor.altitud
    motores_previos = dron_sensor.estado_motores
    coordenadas_previas = dron_sensor.coordenadas

    try:
        # Intento de envio con bateria corrupta (150%)
        dron_sensor.actualizar_trama(
            bateria=150.0,
            altitud=50.0,
            estado_motores="EN_VUELO",
            coordenadas=(6.2200, -75.5750)
        )
        print("[FALLO] La actualizacion corrupta debio lanzar BateriaInvalidaError.")
    except BateriaInvalidaError:
        # Validar manualmente que los atributos no cambiaron
        estado_intacto = (
            dron_sensor.bateria == bateria_previa and
            dron_sensor.altitud == altitud_previa and
            dron_sensor.estado_motores == motores_previos and
            dron_sensor.coordenadas == coordenadas_previas
        )
        if estado_intacto:
            print("[EXITO] Garantia de atomicidad comprobada: la falla no altero los datos del dron.")
            pruebas_exitosas += 1
        else:
            print("[FALLO] El estado del dron muto a pesar de que la actualizacion fue rechazada.")
    print()

    # --------------------------------------------------------------------------
    # 4. COLABORACION ENTRE CLASES (DRON + TELEMETRIA - SPRINT 1)
    # --------------------------------------------------------------------------
    print("--- [4] COLABORACION ENTRE CLASES: TELEMETRIA ASIGNADA A DRON ---")
    total_pruebas += 1

    dron_flota = Dron(
        id_dron="DRON-MED-001",
        modelo_aeronave="Matrice-300-RTK",
        categoria="ENTREGA_LIGERA",
        velocidad_promedio_kmh=60.0
    )
    dron_flota.asignar_telemetria(t_vuelo)

    if dron_flota.telemetria == t_vuelo:
        print(f"[EXITO] Objeto TelemetriaDrone vinculado satisfactoriamente al Dron {dron_flota.id_dron}.")
        print(f"        -> Telemetria vinculada: {dron_flota.telemetria}")
        print(f"        -> Ficha tecnica del dron:\n{dron_flota}")
        pruebas_exitosas += 1
    else:
        print("[FALLO] La telemetria no se asigno correctamente a la entidad Dron.")
    print()

    # --------------------------------------------------------------------------
    # RESUMEN FINAL
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(f" RESUMEN DE PRUEBAS: {pruebas_exitosas} de {total_pruebas} verificaciones exitosas.")
    if pruebas_exitosas == total_pruebas:
        print(" ESTADO: Todas las reglas de negocio, metodos y excepciones operan al 100%.")
    else:
        print(" ESTADO: Se detectaron fallos en la ejecucion.")
    print("================================================================================")


if __name__ == "__main__":
    ejecutar_pruebas()
