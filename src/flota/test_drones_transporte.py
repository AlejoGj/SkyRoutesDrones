# Script de pruebas exhaustivas para las subclases de drones de transporte y logística
# Historia de Usuario: HU-09 y HU-10 (Juan Manuel Pava Higuita)
# Sprint 2: Herencia, Polimorfismo y Abstracción Formal

import sys
from pathlib import Path

# Garantizar resolución del módulo src ejecutando directamente o como módulo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.flota.dron import Dron
from src.flota.dron_entrega_ligera import DronEntregaLigera
from src.flota.dron_carga_pesada import DronCargaPesada
from src.telemetria.telemetria import TelemetriaDrone
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.excepciones.errores import ActualizarEstadoDronError


def ejecutar_pruebas():
    print("================================================================================")
    print(" SKYROUTE - PRUEBAS DE HERENCIA Y POLIMORFISMO: DRONES DE TRANSPORTE (HU-09, HU-10)")
    print(" Responsable: Juan Manuel Pava Higuita")
    print(" Subclases evaluadas: DronEntregaLigera y DronCargaPesada")
    print("================================================================================\n")

    pruebas_exitosas = 0
    total_pruebas = 0

    # --------------------------------------------------------------------------
    # 1. VERIFICACIÓN DE ABSTRACCIÓN EN LA CLASE BASE DRON
    # --------------------------------------------------------------------------
    print("--- [1] VERIFICACIÓN DE ABSTRACCIÓN EN CLASE BASE DRON ---")
    total_pruebas += 1
    try:
        Dron("DR-GENERIC", "Generico") # type: ignore
        print("[FALLO] Se permitió instanciar la clase abstracta Dron directamente.")
    except TypeError as e:
        print(f"[ÉXITO] Intento de instanciar Dron bloqueado por abstracción: {e}")
        pruebas_exitosas += 1
    print()

    # --------------------------------------------------------------------------
    # 2. INSTANCIACIÓN Y HERENCIA DE DRONENTREGALIGERA (HU-09)
    # --------------------------------------------------------------------------
    print("--- [2] INSTANCIACIÓN Y HERENCIA DE DRONENTREGALIGERA ---")
    total_pruebas += 1
    d_ligero = DronEntregaLigera(
        id_dron="DRON-MED-01",
        modelo_aeronave="AeroCourier-V3",
        velocidad_promedio_kmh=65.0,
        capacidad_carga_kg=4.5,
        compartimento_refrigerado=True,
        mecanismo_suelta_rapida=True,
    )
    if isinstance(d_ligero, Dron) and d_ligero.categoria == "ENTREGA_LIGERA":
        print(f"[ÉXITO] DronEntregaLigera hereda de Dron. Categoría oficial: '{d_ligero.categoria}'.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Fallo en herencia o categoría de DronEntregaLigera.")

    total_pruebas += 1
    if (
        d_ligero.capacidad_carga_kg == 4.5
        and d_ligero.compartimento_refrigerado is True
        and d_ligero.mecanismo_suelta_rapida is True
    ):
        print(f"[ÉXITO] Atributos especializados correctos (Capacidad: {d_ligero.capacidad_carga_kg} kg, Refri: {d_ligero.compartimento_refrigerado}, Suelta: {d_ligero.mecanismo_suelta_rapida}).")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Atributos especializados incorrectos en DronEntregaLigera.")

    # Validaciones defensivas en DronEntregaLigera
    total_pruebas += 1
    capacidad_invalida = False
    try:
        DronEntregaLigera("DR-ERR", "Mod", capacidad_carga_kg=-2.0)
    except ValueError:
        capacidad_invalida = True
    if capacidad_invalida:
        print("[ÉXITO] Capacidad de carga negativa rechazada defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se aceptó capacidad de carga negativa.")

    total_pruebas += 1
    refri_invalido = False
    try:
        DronEntregaLigera("DR-ERR", "Mod", compartimento_refrigerado="no")
    except TypeError:
        refri_invalido = True
    if refri_invalido:
        print("[ÉXITO] Refrigeración no booleana rechazada defensivamente con TypeError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se aceptó refrigeración no booleana.")
    print()

    # --------------------------------------------------------------------------
    # 3. INSTANCIACIÓN Y HERENCIA DE DRONCARGAPESADA (HU-09)
    # --------------------------------------------------------------------------
    print("--- [3] INSTANCIACIÓN Y HERENCIA DE DRONCARGAPESADA ---")
    total_pruebas += 1
    d_pesado = DronCargaPesada(
        id_dron="DRON-IND-01",
        modelo_aeronave="Titan-Octocopter-X8",
        velocidad_promedio_kmh=45.0,
        volumen_carga_m3=3.2,
        numero_rotores=8,
        potencia_remolque_w=5000.0,
    )
    if isinstance(d_pesado, Dron) and d_pesado.categoria == "CARGA_PESADA":
        print(f"[ÉXITO] DronCargaPesada hereda de Dron. Categoría oficial: '{d_pesado.categoria}'.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Fallo en herencia o categoría de DronCargaPesada.")

    total_pruebas += 1
    if (
        d_pesado.volumen_carga_m3 == 3.2
        and d_pesado.numero_rotores == 8
        and d_pesado.potencia_remolque_w == 5000.0
    ):
        print(f"[ÉXITO] Atributos especializados correctos (Volumen: {d_pesado.volumen_carga_m3} m³, Rotores: {d_pesado.numero_rotores}, Potencia: {d_pesado.potencia_remolque_w} W).")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Atributos especializados incorrectos en DronCargaPesada.")

    # Validaciones defensivas en DronCargaPesada
    total_pruebas += 1
    rotores_invalidos = False
    try:
        DronCargaPesada("DR-ERR", "Mod", numero_rotores=2)
    except ValueError:
        rotores_invalidos = True
    if rotores_invalidos:
        print("[ÉXITO] Cantidad de rotores menor a 4 rechazada defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se aceptó dron de carga pesada con menos de 4 rotores.")

    total_pruebas += 1
    potencia_invalida = False
    try:
        DronCargaPesada("DR-ERR", "Mod", potencia_remolque_w=-100.0)
    except ValueError:
        potencia_invalida = True
    if potencia_invalida:
        print("[ÉXITO] Potencia de remolque negativa rechazada defensivamente con ValueError.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se aceptó potencia de remolque negativa.")
    print()

    # --------------------------------------------------------------------------
    # 4. POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-10)
    # --------------------------------------------------------------------------
    print("--- [4] POLIMORFISMO EN CONSUMO ENERGÉTICO ---")
    distancia_prueba_km = 10.0
    consumo_ligero = d_ligero.calcular_consumo_estimado(distancia_prueba_km)
    consumo_pesado = d_pesado.calcular_consumo_estimado(distancia_prueba_km)

    total_pruebas += 1
    # Ligero: 10 * 1.2 = 12.0%
    if abs(consumo_ligero - 12.0) < 1e-4:
        print(f"[ÉXITO] Consumo DronEntregaLigera ({distancia_prueba_km} km): {consumo_ligero:.1f}% (Tasa: 1.2%/km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumo ligero inesperado: {consumo_ligero}")

    total_pruebas += 1
    # Pesado: 10 * (2.5 + (8 * 0.1)) = 10 * 3.3 = 33.0%
    if abs(consumo_pesado - 33.0) < 1e-4:
        print(f"[ÉXITO] Consumo DronCargaPesada ({distancia_prueba_km} km): {consumo_pesado:.1f}% (Tasa: 3.3%/km).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Consumo pesado inesperado: {consumo_pesado}")

    total_pruebas += 1
    if consumo_pesado > (consumo_ligero * 2.0):
        print(f"[ÉXITO] Demostración de Polimorfismo: La carga pesada consume {(consumo_pesado/consumo_ligero):.2f}x más energía por el arrastre.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Diferencial de consumo no demostró impacto polimórfico esperado.")
    print()

    # --------------------------------------------------------------------------
    # 5. DIAGNÓSTICO DE SISTEMAS ESPECIALIZADOS
    # --------------------------------------------------------------------------
    print("--- [5] DIAGNÓSTICO DE SISTEMAS ESPECIALIZADOS ---")
    total_pruebas += 1
    diag_ligero = d_ligero.inspeccionar_sistemas_especializados()
    diag_pesado = d_pesado.inspeccionar_sistemas_especializados()

    if (
        "Capacidad" in diag_ligero
        and "Refrigeraci" in diag_ligero
        and "rotores" in diag_pesado.lower()
        and "remolque" in diag_pesado.lower()
    ):
        print(f"[ÉXITO] Diagnóstico Entrega Ligera : {diag_ligero}")
        print(f"[ÉXITO] Diagnóstico Carga Pesada   : {diag_pesado}")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Textos de diagnóstico incompletos: Ligero='{diag_ligero}', Pesado='{diag_pesado}'")
    print()

    # --------------------------------------------------------------------------
    # 6. EJECUCIÓN OPERATIVA Y RECHAZO POR SOBREPESO (HU-09)
    # --------------------------------------------------------------------------
    print("--- [6] EJECUCIÓN OPERATIVA Y REGLAS DE NEGOCIO ---")
    # Configurar telemetría en base (Olaya Herrera)
    telemetria_ligero = TelemetriaDrone(
        id_dron=d_ligero.id_dron,
        bateria=90.0,
        altitud=0.0,
        estado_motores="APAGADOS",
        coordenadas=(6.2089, -75.5684),
    )
    d_ligero.asignar_telemetria(telemetria_ligero)

    telemetria_pesado = TelemetriaDrone(
        id_dron=d_pesado.id_dron,
        bateria=95.0,
        altitud=0.0,
        estado_motores="APAGADOS",
        coordenadas=(6.2089, -75.5684),
    )
    d_pesado.asignar_telemetria(telemetria_pesado)

    usuario_demo = Usuario("USR-JMP-01", "Juan Manuel Pava", "OPERADOR_VUELO")

    # 6.1 Prueba de rechazo por sobrepeso en DronEntregaLigera (Capacidad: 4.5 kg, Carga: 8.0 kg)
    total_pruebas += 1
    pedido_sobrepeso = Pedido(
        id_pedido="PED-OVERWEIGHT",
        usuario_solicitante=usuario_demo,
        categoria_requerida="ENTREGA_LIGERA",
        coordenada_destino=(6.2505, -75.5681),
        peso_carga_kg=8.0,
    )
    pedido_sobrepeso.vincular_dron(d_ligero)

    sobrepeso_capturado = False
    try:
        d_ligero.ejecutar_mision(pedido_sobrepeso)
    except ActualizarEstadoDronError as e:
        sobrepeso_capturado = True
        print(f"[ÉXITO] Misión rechazada por sobrepeso ({pedido_sobrepeso.peso_carga_kg} kg > {d_ligero.capacidad_carga_kg} kg): {e}")

    if sobrepeso_capturado:
        pruebas_exitosas += 1
    else:
        print("[FALLO] Se permitió el despegue de carga ligera con sobrepeso.")

    # 6.2 Despacho exitoso de entrega ligera (Carga: 2.0 kg)
    total_pruebas += 1
    pedido_ligero_ok = Pedido(
        id_pedido="PED-MED-OK",
        usuario_solicitante=usuario_demo,
        categoria_requerida="ENTREGA_LIGERA",
        coordenada_destino=(6.2505, -75.5681),
        peso_carga_kg=2.0,
    )
    pedido_ligero_ok.vincular_dron(d_ligero)
    reporte_ligero = d_ligero.ejecutar_mision(pedido_ligero_ok)

    if (
        reporte_ligero.get("estado_mision") == "DESPEGUE_EXITOSO"
        and reporte_ligero.get("instrumental_activado") == "COMPARTIMENTO_REFRIGERADO"
        and pedido_ligero_ok.estado == "EN_TRANSITO"
        and d_ligero.en_mision is True
    ):
        print(f"[ÉXITO] Misión de entrega ligera despachada con éxito (Instrumental: {reporte_ligero.get('instrumental_activado')}).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Misión de entrega ligera fallida: {reporte_ligero}")

    # 6.3 Despacho exitoso de carga pesada industrial (Carga: 45.0 kg)
    total_pruebas += 1
    pedido_pesado_ok = Pedido(
        id_pedido="PED-IND-OK",
        usuario_solicitante=usuario_demo,
        categoria_requerida="CARGA_PESADA",
        coordenada_destino=(6.2800, -75.5400),
        peso_carga_kg=45.0,
    )
    pedido_pesado_ok.vincular_dron(d_pesado)
    reporte_pesado = d_pesado.ejecutar_mision(pedido_pesado_ok)

    if (
        reporte_pesado.get("estado_mision") == "DESPEGUE_EXITOSO"
        and reporte_pesado.get("instrumental_activado") == "GANCHO_REMOLQUE_INDUSTRIAL"
        and pedido_pesado_ok.estado == "EN_TRANSITO"
        and d_pesado.en_mision is True
    ):
        print(f"[ÉXITO] Misión de carga pesada despachada con éxito (Instrumental: {reporte_pesado.get('instrumental_activado')}).")
        pruebas_exitosas += 1
    else:
        print(f"[FALLO] Misión de carga pesada fallida: {reporte_pesado}")
    print()

    # --------------------------------------------------------------------------
    # 7. FICHA TÉCNICA MULTILÍNEA ENRIQUECIDA (__STR__)
    # --------------------------------------------------------------------------
    print("--- [7] FICHAS TÉCNICAS MULTILÍNEA (__STR__) ---")
    total_pruebas += 1
    ficha_ligero = str(d_ligero)
    ficha_pesado = str(d_pesado)

    if "Capacidad Máxima" in ficha_ligero and "Refrigeración" in ficha_ligero and "Volumen de Bodega" in ficha_pesado and "Tren de Propulsión" in ficha_pesado:
        print("[ÉXITO] Representaciones multilíneas __str__ incluyen los aditamentos especializados.")
        pruebas_exitosas += 1
    else:
        print("[FALLO] Instrumental ausente en fichas técnicas multilíneas.")
    print()

    # --------------------------------------------------------------------------
    # RESUMEN FINAL DE CERTIFICACIÓN
    # --------------------------------------------------------------------------
    print("================================================================================")
    print(f" RESULTADO FINAL: {pruebas_exitosas}/{total_pruebas} PRUEBAS SUPERADAS EXITOSAMENTE")
    if pruebas_exitosas == total_pruebas:
        print(" [ESTADO: CERTIFICADO] Las HUs (HU-09 y HU-10) cumplen con todos los criterios de aceptación.")
    else:
        print(" [ESTADO: INCOMPLETO] Se detectaron fallos en la suite de pruebas.")
    print("================================================================================")
    return pruebas_exitosas == total_pruebas


if __name__ == "__main__":
    ejecutar_pruebas()
