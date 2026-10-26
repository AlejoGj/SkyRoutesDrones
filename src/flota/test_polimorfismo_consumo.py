# Script de pruebas para Polimorfismo en Consumo Energético y Fichas Técnicas Multilínea
# Historia de Usuario: HU-10 (Juan Manuel Pava Higuita)
# Sprint 2: Herencia, Polimorfismo y Abstracción Formal

import sys
from pathlib import Path

# Garantizar resolución del módulo src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.flota.dron import Dron
from src.flota.dron_entrega_ligera import DronEntregaLigera
from src.flota.dron_carga_pesada import DronCargaPesada
from src.telemetria.telemetria import TelemetriaDrone


def ejecutar_pruebas():
    print("================================================================================")
    print(" SKYROUTE - CERTIFICACIÓN DE POLIMORFISMO DE CONSUMO Y FICHAS TÉCNICAS (HU-10)")
    print(" Responsable: Juan Manuel Pava Higuita")
    print(" Objetivo: Consumo energético diferenciado, predicción pre-despegue y __repr__/__str__")
    print("================================================================================\n")

    pruebas_exitosas = 0
    total_pruebas = 0

    # Inicializar aeronaves representativas
    dron_ligero = DronEntregaLigera(
        id_dron="DR-LIGERO-01",
        modelo_aeronave="AeroCourier-V3",
        capacidad_carga_kg=4.0,
        compartimento_refrigerado=True,
        mecanismo_suelta_rapida=True,
    )
    dron_pesado_8r = DronCargaPesada(
        id_dron="DR-PESADO-X8",
        modelo_aeronave="Titan-Octocopter",
        volumen_carga_m3=3.0,
        numero_rotores=8,
        potencia_remolque_w=5200.0,
    )
    dron_pesado_6r = DronCargaPesada(
        id_dron="DR-PESADO-X6",
        modelo_aeronave="HeavyLifter-Hexa",
        volumen_carga_m3=2.0,
        numero_rotores=6,
        potencia_remolque_w=4000.0,
    )

    # --------------------------------------------------------------------------
    # 1. POLIMORFISMO MATEMÁTICO EN FÓRMULAS DE CONSUMO (RF-04, RF-10)
    # --------------------------------------------------------------------------
    print("--- [1] FÓRMULAS MATEMÁTICAS POLIMÓRFICAS DE CONSUMO ---")
    distancia_base_km = 10.0

    # 1.1 Dron Ligero: tasa fija de 1.2% por km -> 12.0%
    total_pruebas += 1
    consumo_l = dron_ligero.calcular_consumo_estimado(distancia_base_km)
    if abs(consumo_l - 12.0) < 1e-4:
        print(f"[ÉXITO] DronEntregaLigera (10 km): {consumo_l:.2f}% de batería (Tasa esperada: 1.20%/km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumo ligero incorrecto: {consumo_l}")

    # 1.2 Dron Pesado (8 rotores): tasa polinómica = 2.5 + (8 * 0.1) = 3.3% por km -> 33.0%
    total_pruebas += 1
    consumo_p8 = dron_pesado_8r.calcular_consumo_estimado(distancia_base_km)
    if abs(consumo_p8 - 33.0) < 1e-4:
        print(f"[ÉXITO] DronCargaPesada 8 rotores (10 km): {consumo_p8:.2f}% (Tasa esperada: 3.30%/km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumo pesado (8 rotores) incorrecto: {consumo_p8}")

    # 1.3 Dron Pesado (6 rotores): tasa polinómica = 2.5 + (6 * 0.1) = 3.1% por km -> 31.0%
    total_pruebas += 1
    consumo_p6 = dron_pesado_6r.calcular_consumo_estimado(distancia_base_km)
    if abs(consumo_p6 - 31.0) < 1e-4:
        print(f"[ÉXITO] DronCargaPesada 6 rotores (10 km): {consumo_p6:.2f}% (Tasa esperada: 3.10%/km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumo pesado (6 rotores) incorrecto: {consumo_p6}")

    # 1.4 Manejo seguro de distancia cero o negativa
    total_pruebas += 1
    if dron_ligero.calcular_consumo_estimado(0.0) == 0.0 and dron_pesado_8r.calcular_consumo_estimado(-5.0) == 0.0:
        print("[ÉXITO] Distancias nulas y negativas retornan 0.0% de consumo defensivamente.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Falla en manejo defensivo de distancias <= 0.")
    print()

    # --------------------------------------------------------------------------
    # 2. EVALUACIÓN DE RUTAS OPERATIVAS DEL VALLE DE ABURRÁ
    # --------------------------------------------------------------------------
    print("--- [2] IMPACTO ENERGÉTICO EN RUTAS REALES DEL VALLE DE ABURRÁ ---")
    rutas_valle = [
        ("Urbana Centro-Sur (Santa Fe a Parque Berrío)", 5.95),
        ("Corredor Metropolitano (Sabaneta a Bello)", 21.23),
        ("Troncal Valle de Aburrá (Caldas Sur a Barbosa Norte)", 60.30),
    ]

    print(f"{'Ruta Operativa':<45} | {'Distancia':<9} | {'Ligero (1.2%)':<14} | {'Pesado X8 (3.3%)':<16} | {'Factor'}")
    print("-" * 100)

    total_pruebas += 1
    rutas_ok = True
    for nombre_ruta, dist_km in rutas_valle:
        c_lig = dron_ligero.calcular_consumo_estimado(dist_km)
        c_pes = dron_pesado_8r.calcular_consumo_estimado(dist_km)
        factor = c_pes / c_lig if c_lig > 0 else 0
        if c_pes <= c_lig:
            rutas_ok = False
        print(f"{nombre_ruta:<45} | {dist_km:>6.2f} km | {c_lig:>10.2f}%    | {c_pes:>12.2f}%      | {factor:.2f}x")
    print("-" * 100)

    if rutas_ok:
        print("[ÉXITO] Demostración de Polimorfismo: En todas las rutas el dron pesado consume 2.75x más batería.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Incoherencia en cálculo polimórfico de rutas.")
    print()

    # --------------------------------------------------------------------------
    # 3. PREDICCIÓN DE VIABILIDAD ENERGÉTICA PRE-DESPEGUE (HU-10)
    # --------------------------------------------------------------------------
    print("--- [3] PREDICCIÓN DE VIABILIDAD ENERGÉTICA PRE-DESPEGUE ---")
    # Asignar telemetrías con distintos niveles de batería
    telemetria_80pct = TelemetriaDrone(
        id_dron=dron_ligero.id_dron,
        bateria=80.0,
        altitud=0.0,
        estado_motores="STANDBY",
        coordenadas=(6.2089, -75.5684),
    )
    dron_ligero.asignar_telemetria(telemetria_80pct)

    telemetria_25pct = TelemetriaDrone(
        id_dron=dron_pesado_8r.id_dron,
        bateria=25.0,
        altitud=0.0,
        estado_motores="STANDBY",
        coordenadas=(6.2089, -75.5684),
    )
    dron_pesado_8r.asignar_telemetria(telemetria_25pct)

    # 3.1 Vuelo viable para dron ligero (15 km requiere 18%, batería en 80% -> Viable)
    total_pruebas += 1
    pred_ligero = dron_ligero.predecir_viabilidad_mision(15.0)
    if pred_ligero["mision_viable"] is True and abs(pred_ligero["bateria_remanente_pct"] - 62.0) < 1e-4:
        print(f"[ÉXITO] Predicción Ligero (15 km): {pred_ligero['diagnostico_autonomia']}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Falla en predicción viable para dron ligero: {pred_ligero}")

    # 3.2 Vuelo NO viable para dron pesado (15 km requiere 49.5%, batería en 25% -> Inviable)
    total_pruebas += 1
    pred_pesado = dron_pesado_8r.predecir_viabilidad_mision(15.0)
    if pred_pesado["mision_viable"] is False and pred_pesado["consumo_estimado_pct"] == 49.5:
        print(f"[ÉXITO] Predicción Pesado (15 km): {pred_pesado['diagnostico_autonomia']}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Falla en predicción inviable para dron pesado: {pred_pesado}")

    # 3.3 Validación sin telemetría asignada
    total_pruebas += 1
    pred_sin_telemetria = dron_pesado_6r.predecir_viabilidad_mision(10.0)
    if pred_sin_telemetria["mision_viable"] is False and "telemetr" in pred_sin_telemetria["diagnostico_autonomia"]:
        print(f"[ÉXITO] Detección de falta de telemetría: {pred_sin_telemetria['diagnostico_autonomia']}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] No se detectó ausencia de telemetría: {pred_sin_telemetria}")
    print()

    # --------------------------------------------------------------------------
    # 4. FICHAS TÉCNICAS MULTILÍNEA Y __REPR__ EXTENDIDO (HU-10)
    # --------------------------------------------------------------------------
    print("--- [4] FICHAS TÉCNICAS MULTILÍNEA Y __REPR__ EXTENDIDO ---")
    total_pruebas += 1
    repr_l = repr(dron_ligero)
    repr_p = repr(dron_pesado_8r)
    if (
        "capacidad_carga_kg" in repr_l
        and "mecanismo_suelta_rapida" in repr_l
        and "volumen_carga_m3" in repr_p
        and "numero_rotores" in repr_p
    ):
        print(f"[ÉXITO] __repr__ DronEntregaLigera : {repr_l}")
        print(f"[ÉXITO] __repr__ DronCargaPesada   : {repr_p}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] __repr__ incompleto: L='{repr_l}', P='{repr_p}'")

    total_pruebas += 1
    str_l = str(dron_ligero)
    str_p = str(dron_pesado_8r)
    if "Eficiencia Consumo : 1.2% bat/km" in str_l and "Eficiencia Consumo : 3.3% bat/km" in str_p:
        print("[ÉXITO] Fichas técnicas multilínea (__str__) visualizan claramente la eficiencia de consumo.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Tasa de eficiencia ausente en fichas técnicas multilíneas.")
    print()

    # --------------------------------------------------------------------------
    # RESUMEN FINAL
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(f" RESULTADO FINAL: {pruebas_exitosas}/{total_pruebas} PRUEBAS SUPERADAS EXITOSAMENTE")
    if pruebas_exitosas == total_pruebas:
        print(" [ESTADO: CERTIFICADO] La HU-10 cumple con todos los criterios de aceptación.")
    else:
        print(" [ESTADO: INCOMPLETO] Se detectaron fallos en la suite de pruebas.")
    print("================================================================================")
    return pruebas_exitosas == total_pruebas


if __name__ == "__main__":
    ejecutar_pruebas()
