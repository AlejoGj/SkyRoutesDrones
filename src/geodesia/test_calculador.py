# Script de pruebas unitarias para el modulo de calculos geodesicos
# Historia de Usuario: HU-02 (Alejandro Garcia Jimenez)
# Contexto geografico: Operaciones de aeronaves sobre el Valle de Aburra
# Limites geograficos del Valle: 5°58' N a 6°30' N (5.9667° a 6.5000°) y 75°43' W a 75°21' W (-75.7167° a -75.3500°)

import sys
from pathlib import Path

# Garantizar resolucion del modulo src ejecutando directamente o como modulo
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.geodesia.calculador import CalculadorGeodesico
from src.excepciones.errores import CoordenadaInvalidaError


def ejecutar_pruebas():
    print("================================================================================ \n"
          " SKYROUTE - PRUEBA DE INTEGRIDAD (USO DE IA PARA PRUEBAS EXAHUSTIVAS) (HU-02)\n"
          " Responsable: Alejandro Garcia Jimenez\n"
          " Contexto: Operaciones y rutas sobre el Valle de Aburra\n"
          "================================================================================\n")

    pruebas_exitosas = 0
    total_pruebas = 0
    calculador = CalculadorGeodesico()

    # --------------------------------------------------------------------------
    # 1. VERIFICACION DE CONSTANTES Y ESTADO INICIAL
    # --------------------------------------------------------------------------
    print("--- [1] ATRIBUTOS Y CONFIGURACION INICIAL ---")
    total_pruebas += 1
    if calculador.radio_tierra_km in (6371, 6371.0):
        print(f"[EXITO] Radio medio terrestre configurado correctamente ({calculador.radio_tierra_km} km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Radio de la tierra incorrecto: {calculador.radio_tierra_km}")
    print()

    # --------------------------------------------------------------------------
    # 2. CALCULO DE DISTANCIAS EN EL VALLE DE ABURRA (HAVERSINE)
    # --------------------------------------------------------------------------
    print("--- [2] CALCULO DE DISTANCIAS EN EL VALLE DE ABURRA (HAVERSINE) ---")

    # 2.1 Ruta Urbana Centro - Sur (Medellin: CC Santafe a Parque Berrio)
    total_pruebas += 1
    coord_santafe = (6.1974, -75.5746)  # El Poblado
    coord_berrio = (6.2505, -75.5681)   # Centro Medellin
    distancia_medellin = calculador.calcular_haversine(coord_santafe, coord_berrio)

    if isinstance(distancia_medellin, float) and 5.8 < distancia_medellin < 6.1:
        print(f"[EXITO] Ruta urbana (Santafe a Parque Berrio): {distancia_medellin:.3f} km.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Distancia urbana fuera de rango esperado: {distancia_medellin}")

    # 2.2 Misma ubicacion en base operativa (origen == destino)
    total_pruebas += 1
    distancia_cero = calculador.calcular_haversine(coord_berrio, coord_berrio)
    if abs(distancia_cero) < 1e-6:
        print(f"[EXITO] Distancia en la misma base (punto a si mismo): {distancia_cero:.4f} km.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Distancia en mismo punto debio ser 0.0, obtenida: {distancia_cero}")

    # 2.3 Corredor Metropolitano Sur a Norte (Sabaneta a Bello)
    total_pruebas += 1
    coord_sabaneta = (6.1510, -75.6160)  # Sur metropolitano
    coord_bello = (6.3330, -75.5580)     # Norte metropolitano
    distancia_metropolitana = calculador.calcular_haversine(coord_sabaneta, coord_bello)

    # Distancia esperada aproximada: 21.23 km
    if 21.0 < distancia_metropolitana < 21.5:
        print(f"[EXITO] Corredor metropolitano (Sabaneta a Bello): {distancia_metropolitana:.2f} km.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Distancia Sabaneta-Bello fuera de rango esperado: {distancia_metropolitana}")

    # 2.4 Ruta Troncal Extremo Sur a Extremo Norte (Caldas 5°58' N a Barbosa entrada)
    total_pruebas += 1
    coord_caldas_sur = (5.9667, -75.6350)    # Límite sur: 5°58' N
    coord_barbosa_norte = (6.4350, -75.3600) # Barbosa (dentro del límite este: 75°21.6' W)
    distancia_troncal = calculador.calcular_haversine(coord_caldas_sur, coord_barbosa_norte)

    # Distancia esperada aproximada: 60.30 km
    if 59.5 < distancia_troncal < 61.5:
        print(f"[EXITO] Troncal Valle de Aburra (Caldas Sur a Barbosa Norte): {distancia_troncal:.2f} km.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Distancia Caldas-Barbosa fuera de rango esperado: {distancia_troncal}")

    # 2.5 Diagonal maxima geografica del cuadrante del Valle de Aburra
    # De vertice suroccidental (5°58' N, 75°43' W) a vertice nororiental (6°30' N, 75°21' W)
    total_pruebas += 1
    vertice_so = (5.9667, -75.7167)  # 5°58' N, 75°43' W
    vertice_ne = (6.5000, -75.3500)  # 6°30' N, 75°21' W
    distancia_diagonal_max = calculador.calcular_haversine(vertice_so, vertice_ne)

    # Distancia esperada aproximada: 71.83 km
    if 71.0 < distancia_diagonal_max < 72.5:
        print(f"[EXITO] Diagonal maxima geografica del Valle de Aburra: {distancia_diagonal_max:.2f} km.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Diagonal maxima fuera de rango: {distancia_diagonal_max}")
    print()

    # --------------------------------------------------------------------------
    # 3. VALIDACION DEFENSIVA DE COORDENADAS (RN-05, RF-02)
    # --------------------------------------------------------------------------
    print("--- [3] VALIDACION DEFENSIVA Y EXCEPCIONES DE COORDENADAS (RN-05, RF-02) ---")

    # 3.1 Origen no es tupla
    total_pruebas += 1
    try:
        calculador.calcular_haversine([6.25, -75.56], coord_berrio)  # type: ignore
        print("[FALLO] Origen en lista debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Origen no-tupla interceptado correctamente: {e}")
        pruebas_exitosas += 1

    # 3.2 Destino no es tupla
    total_pruebas += 1
    try:
        calculador.calcular_haversine(coord_santafe, "6.25, -75.56")  # type: ignore
        print("[FALLO] Destino en string debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Destino no-tupla interceptado correctamente: {e}")
        pruebas_exitosas += 1

    # 3.3 Tupla con longitud distinta de 2
    total_pruebas += 1
    try:
        calculador.calcular_haversine((6.25,), coord_berrio)  # type: ignore
        print("[FALLO] Tupla de 1 elemento debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Tupla de longitud incompleta interceptada: {e}")
        pruebas_exitosas += 1

    # 3.4 Elementos de coordenada no numericos
    total_pruebas += 1
    try:
        calculador.calcular_haversine(coord_santafe, ("6.25", -75.56))  # type: ignore
        print("[FALLO] Coordenada con valor string debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Coordenada no numerica interceptada: {e}")
        pruebas_exitosas += 1

    # 3.5 Latitud superior al limite norte del Valle de Aburra (6°30' N = 6.5000)
    total_pruebas += 1
    try:
        calculador.calcular_haversine((6.5100, -75.5600), coord_berrio)
        print("[FALLO] Latitud > 6.5000 debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Latitud fuera del Valle (Norte > 6°30') interceptada: {e}")
        pruebas_exitosas += 1

    # 3.6 Latitud inferior al limite sur del Valle de Aburra (5°58' N = 5.9667)
    total_pruebas += 1
    try:
        calculador.calcular_haversine(coord_santafe, (5.9500, -75.5600))
        print("[FALLO] Latitud < 5.9667 debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Latitud fuera del Valle (Sur < 5°58') interceptada: {e}")
        pruebas_exitosas += 1

    # 3.7 Longitud fuera del limite este del Valle (75°21' W = -75.3500)
    total_pruebas += 1
    try:
        calculador.calcular_haversine((6.2500, -75.3000), coord_berrio)
        print("[FALLO] Longitud > -75.3500 debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Longitud fuera del Valle (Este > 75°21' W) interceptada: {e}")
        pruebas_exitosas += 1

    # 3.8 Longitud fuera del limite oeste del Valle (75°43' W = -75.7167)
    total_pruebas += 1
    try:
        calculador.calcular_haversine(coord_santafe, (6.2500, -75.7500))
        print("[FALLO] Longitud < -75.7167 debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Longitud fuera del Valle (Oeste < 75°43' W) interceptada: {e}")
        pruebas_exitosas += 1

    # 3.9 Coordenada global fuera de Colombia (Bogota)
    total_pruebas += 1
    try:
        calculador.calcular_haversine(coord_santafe, (4.7110, -74.0721))
        print("[FALLO] Coordenada fuera del Valle de Aburra debio disparar CoordenadaInvalidaError.")
    except CoordenadaInvalidaError as e:
        print(f"[EXITO] Ubicacion foranea interceptada correctamente: {e}")
        pruebas_exitosas += 1
    print()

    # --------------------------------------------------------------------------
    # 4. ESTIMACION DE TIEMPO DE VUELO (ETA) PARA RUTAS DEL VALLE (RF-10, HU-02)
    # --------------------------------------------------------------------------
    print("--- [4] ESTIMACION DE TIEMPO DE VUELO (ETA) PARA RUTAS DEL VALLE (RF-10, HU-02) ---")

    # 4.1 Vuelo urbano rapido en Medellin (5.95 km a 40 km/h)
    total_pruebas += 1
    eta_medellin = calculador.calcular_tiempo_vuelo_min(distancia_km=distancia_medellin, velocidad_km_h=40.0)
    tiempo_esperado_med = (distancia_medellin / 40.0) * 60.0
    if abs(eta_medellin - tiempo_esperado_med) < 1e-4:
        print(f"[EXITO] ETA urbano Medellin: {distancia_medellin:.2f} km a 40.0 km/h = {eta_medellin:.2f} min.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] ETA urbano Medellin incorrecto: {eta_medellin}")

    # 4.2 Vuelo metropolitano Sabaneta - Bello (21.23 km a 60 km/h)
    total_pruebas += 1
    eta_metropolitano = calculador.calcular_tiempo_vuelo_min(distancia_km=distancia_metropolitana, velocidad_km_h=60.0)
    tiempo_esperado_metro = (distancia_metropolitana / 60.0) * 60.0
    if abs(eta_metropolitano - tiempo_esperado_metro) < 1e-4:
        print(f"[EXITO] ETA metropolitano (Sabaneta-Bello): {distancia_metropolitana:.2f} km a 60.0 km/h = {eta_metropolitano:.2f} min.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] ETA metropolitano incorrecto: {eta_metropolitano}")

    # 4.3 Vuelo troncal completo Caldas - Barbosa (62.20 km a 65 km/h)
    total_pruebas += 1
    eta_troncal = calculador.calcular_tiempo_vuelo_min(distancia_km=distancia_troncal, velocidad_km_h=65.0)
    tiempo_esperado_troncal = (distancia_troncal / 65.0) * 60.0
    if abs(eta_troncal - tiempo_esperado_troncal) < 1e-4:
        print(f"[EXITO] ETA troncal Valle (Caldas-Barbosa): {distancia_troncal:.2f} km a 65.0 km/h = {eta_troncal:.2f} min.")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] ETA troncal incorrecto: {eta_troncal}")

    # 4.4 Manejo defensivo: Velocidad cero (evitar ZeroDivisionError)
    total_pruebas += 1
    eta_cero_vel = calculador.calcular_tiempo_vuelo_min(distancia_km=15.0, velocidad_km_h=0.0)
    if eta_cero_vel == 0.0:
        print("[EXITO] Velocidad 0 km/h protegida contra division por cero (retorna 0.0 min).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Velocidad 0 debio retornar 0.0, obtenido: {eta_cero_vel}")

    # 4.5 Manejo defensivo: Velocidad negativa
    total_pruebas += 1
    eta_vel_neg = calculador.calcular_tiempo_vuelo_min(distancia_km=15.0, velocidad_km_h=-50.0)
    if eta_vel_neg == 0.0:
        print("[EXITO] Velocidad negativa controlada defensivamente (retorna 0.0 min).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Velocidad negativa debio retornar 0.0, obtenido: {eta_vel_neg}")

    # 4.6 Manejo defensivo: Distancia cero o negativa
    total_pruebas += 1
    eta_dist_neg = calculador.calcular_tiempo_vuelo_min(distancia_km=-5.0, velocidad_km_h=50.0)
    if eta_dist_neg == 0.0:
        print("[EXITO] Distancia negativa controlada (retorna 0.0 min).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Distancia negativa debio retornar 0.0, obtenido: {eta_dist_neg}")
    print()

    # --------------------------------------------------------------------------
    # BALANCE FINAL
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(f" RESUMEN DE PRUEBAS UNITARIAS: {pruebas_exitosas}/{total_pruebas} superadas exitosamente.")
    if pruebas_exitosas == total_pruebas:
        print(" [ESTADO: CERTIFICADO] Todas las pruebas del Valle de Aburra superadas con exito.")
    else:
        print(" [ESTADO: REVISAR] Algunas pruebas unitarias no pasaron.")
    print("================================================================================\n")


if __name__ == "__main__":
    ejecutar_pruebas()
