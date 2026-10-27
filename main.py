#!/usr/bin/env python3
"""
================================================================================
 SKYROUTE DRONES - CENTRO DE CONTROL DE OPERACIONES METROPOLITANO (VALLE DE ABURRÁ)
================================================================================
 Sistema Integrado de Gestión de Flota, Pedidos, Geocodificación y Simulación Temporal
 Asignatura: Análisis y Programación Orientada a Objetos (APOO 2026-2)
 Universidad de Medellín
================================================================================
"""

import sys
import time
from typing import Optional

# Configurar salida UTF-8 en consolas Windows cuando sea posible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota import (
    Dron,
    DronEntregaLigera,
    DronCargaPesada,
    DronVigilancia,
    DronMapeo,
    DronInspeccion,
    DronRescate,
)
from src.telemetria.telemetria import TelemetriaDrone
from src.control.centro_control import (
    SistemaCentroControl,
    FABRICA_DRONES,
    instanciar_dron_desde_fabrica,
)
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo
from src.servicios.geocodificador import (
    IServicioGeocodificador,
    ServicioGeocodificadorArcGIS,
    ServicioGeocodificadorGoogle,
    ServicioGeocodificadorOSM,
    ServicioGeocodificadorLocal,
)
from src.servicios.clima import ServicioClimaAburra
from src.geodesia.calculador import CalculadorGeodesico
from src.excepciones.errores import (
    GeocodificacionError,
    CoordenadaInvalidaError,
    ActualizarEstadoDronError,
)


class ConsolaSkyRoute:
    """Consola interactiva para el Centro de Control de Operaciones SkyRoute Drones."""

    LINEA_DOBLE = "=" * 78
    LINEA_SIMPLE = "-" * 78

    def __init__(self) -> None:
        self.calculador = CalculadorGeodesico()
        self.servicio_clima = ServicioClimaAburra()
        self.geocodificador = ServicioGeocodificadorArcGIS(calculador=self.calculador)

        # Inicialización del orquestador central (Base en Medellín: Olaya Herrera)
        self.centro = SistemaCentroControl(
            geocodificador=self.geocodificador
        )

        # Motores de simulación temporal
        self.simulador = SimuladorVuelo(calculador=self.calculador, centro_control=self.centro)
        self.reloj = RelojSimulacion()

        # Cargar datos nominales de inicialización
        self._inicializar_entorno_base()

    def _inicializar_entorno_base(self) -> None:
        """Carga inicial de usuarios y aeronaves de todas las categorías especializadas."""
        # 1. Usuarios representativos
        self.cliente = Usuario("USR-01", "Alejandro García Jiménez", "CLIENTE")
        self.operador = Usuario("USR-02", "Valery Arboleda Ardila", "OPERADOR_VUELO")
        self.centro.registrar_usuario(self.cliente)
        self.centro.registrar_usuario(self.operador)

        # 2. Flota completa polimórfica (6 categorías oficiales)
        drones_iniciales = [
            DronEntregaLigera(
                id_dron="DRON-ENT-01",
                modelo_aeronave="AeroCourier-V3",
                capacidad_carga_kg=4.5,
                compartimento_refrigerado=True,
                mecanismo_suelta_rapida=True,
                velocidad_promedio_kmh=60.0
            ),
            DronCargaPesada(
                id_dron="DRON-CAR-02",
                modelo_aeronave="HeavyLifter-OctoX",
                volumen_carga_m3=3.0,
                numero_rotores=8,
                potencia_remolque_w=5200.0,
                velocidad_promedio_kmh=45.0
            ),
            DronVigilancia(
                id_dron="DRON-VIG-03",
                modelo_aeronave="SkyGuardian-Pro",
                resolucion_camara_mp=48,
                vision_nocturna=True,
                frecuencia_transmision_ghz=5.8,
                velocidad_promedio_kmh=65.0
            ),
            DronMapeo(
                id_dron="DRON-MAP-04",
                modelo_aeronave="TopoLiDAR-RTK",
                tiene_sensor_lidar=True,
                precision_gps_cm=2.5,
                capacidad_almacenamiento_tb=2.0,
                velocidad_promedio_kmh=55.0
            ),
            DronInspeccion(
                id_dron="DRON-INSP-05",
                modelo_aeronave="SkyInspector-300",
                zoom_optico_x=30,
                rango_sensor_ultrasonico_m=8.0,
                velocidad_promedio_kmh=50.0
            ),
            DronRescate(
                id_dron="DRON-RESC-06",
                modelo_aeronave="SAR-LifeGuard",
                camara_termica=True,
                kit_auxilios_equipado=True,
                potencia_altavoz_db=120,
                velocidad_promedio_kmh=68.0
            ),
        ]

        for dron in drones_iniciales:
            # Asignar telemetría inicial en tierra (base central)
            dron.asignar_telemetria(
                TelemetriaDrone(
                    id_dron=dron.id_dron,
                    bateria=100.0,
                    altitud=0.0,
                    estado_motores="STANDBY",
                    coordenadas=self.centro.coordenadas_base
                )
            )
            self.centro.agregar_dron(dron)

    def barra_bateria(self, porcentaje: float, ancho: int = 15) -> str:
        """Genera una barra visual en consola del nivel de batería."""
        bloques = int(round((porcentaje / 100.0) * ancho))
        bloques = max(0, min(ancho, bloques))
        barra = "#" * bloques + "-" * (ancho - bloques)
        return f"[{barra}] {porcentaje:5.1f}%"

    def encabezado(self, titulo: str) -> None:
        print(f"\n{self.LINEA_DOBLE}")
        print(f" {titulo.center(76)}")
        print(f"{self.LINEA_DOBLE}\n")

    def pausar(self) -> None:
        input("\nPresione [ENTER] para continuar...")

    # --------------------------------------------------------------------------
    # OPCIÓN 1: ESTADO DEL CENTRO DE CONTROL Y FICHAS TÉCNICAS
    # --------------------------------------------------------------------------
    def ver_estado_flota(self) -> None:
        self.encabezado("ESTADO GENERAL DEL CENTRO DE CONTROL Y FLOTA ACTIVA")
        print(self.centro)

        print("\n--- DETALLE DE AERONAVES EN BASE ---")
        for idx, dron in enumerate(self.centro.flota_drones, start=1):
            bat = dron.telemetria.bateria if dron.telemetria else 0.0
            estado = "DISPONIBLE" if dron.disponible else ("EN MISIÓN" if dron.en_mision else "NO DISPONIBLE")
            print(f"[{idx}] {dron.id_dron:15} | Cat: {dron.categoria:25} | {self.barra_bateria(bat)} | {estado}")

        opcion = input("\n¿Desea ver la ficha técnica completa (__str__) de alguna aeronave? (Número / 0 para volver): ").strip()
        if opcion.isdigit():
            num = int(opcion)
            if 1 <= num <= len(self.centro.flota_drones):
                dron_sel = self.centro.flota_drones[num - 1]
                print(dron_sel)
                print(f"  Diagnóstico de Sistemas : {dron_sel.inspeccionar_sistemas_especializados()}")
                print(f"  Representación Oficial  : {repr(dron_sel)}")
                self.pausar()

    # --------------------------------------------------------------------------
    # OPCIÓN 2: REGISTRO DE PEDIDOS CON GEOCODIFICACIÓN
    # --------------------------------------------------------------------------
    def registrar_pedido_interactivo(self) -> Optional[Pedido]:
        self.encabezado("REGISTRO DE PEDIDO VÍA GEOCODIFICACIÓN (ESRI ARCGIS WORLD GEOCODER)")
        print("Categorías disponibles:")
        for idx, cat in enumerate(Pedido.categorias_permitidas, start=1):
            print(f"  [{idx}] {cat}")

        cat_op = input("\nSeleccione número de categoría (por defecto 1 - ENTREGA_LIGERA): ").strip()
        cat_idx = int(cat_op) - 1 if cat_op.isdigit() and 1 <= int(cat_op) <= len(Pedido.categorias_permitidas) else 0
        categoria_elegida = Pedido.categorias_permitidas[cat_idx]

        print(f"\nCategoría seleccionada: {categoria_elegida}")
        print("Ejemplos de direcciones válidas en el Valle de Aburrá:")
        print("  - Parque Berrio, Medellin")
        print("  - Parque El Poblado")
        print("  - Centro Comercial Santafe")
        print("  - Parque de Envigado")
        print("  - Parque de Bello")
        print("  - Sabaneta")

        direccion = input("\nIngrese la dirección de destino: ").strip()
        if not direccion:
            print("[CANCELADO] La dirección no puede estar vacía.")
            self.pausar()
            return None

        peso = 1.5
        peso_input = input("Ingrese peso de la carga en kg (por defecto 1.5): ").strip()
        if peso_input:
            try:
                peso = float(peso_input)
            except ValueError:
                peso = 1.5

        id_pedido = f"PED-{int(time.time()) % 100000:05d}"
        try:
            print("\n-> Contactando servicio de geocodificación (ArcGIS World Geocoder)...")
            pedido = Pedido(
                id_pedido=id_pedido,
                usuario_solicitante=self.cliente,
                categoria_requerida=categoria_elegida,
                coordenada_destino=None,
                direccion_destino=direccion,
                peso_carga_kg=peso
            )
            self.centro.registrar_pedido(pedido)

            distancia = self.calculador.calcular_haversine(self.centro.coordenadas_base, pedido.coordenada_destino)
            print(f"\n[ÉXITO] Pedido registrado correctamente:")
            print(f"  ID Pedido            : {pedido.id_pedido}")
            print(f"  Dirección Ingresada  : '{pedido.direccion_destino}'")
            print(f"  Coordenadas Resueltas: {pedido.coordenada_destino}")
            print(f"  Distancia desde Base : {distancia:.2f} km")
            print(f"  Estado Inicial       : {pedido.estado}")
            self.pausar()
            return pedido

        except (GeocodificacionError, CoordenadaInvalidaError) as e:
            print(f"\n[ERROR DE GEOCODIFICACIÓN] No fue posible resolver el destino:")
            print(f"  Detalle: {e}")
            self.pausar()
            return None

    # --------------------------------------------------------------------------
    # OPCIÓN 3: ASIGNACIÓN DE DRON COMPATIBLE
    # --------------------------------------------------------------------------
    def asignar_dron_interactivo(self) -> None:
        self.encabezado("ASIGNACIÓN INTELIGENTE DE DRONES A PEDIDOS PENDIENTES")
        pedidos_pendientes = [p for p in self.centro.pedidos if p.estado == "PENDIENTE"]
        if not pedidos_pendientes:
            print("No hay pedidos en estado PENDIENTE en este momento.")
            self.pausar()
            return

        print("Pedidos pendientes de asignación:")
        for idx, p in enumerate(pedidos_pendientes, start=1):
            print(f"[{idx}] {p.id_pedido} | Categoría: {p.categoria_requerida:25} | Destino: {p.coordenada_destino}")

        sel = input("\nSeleccione el número del pedido a asignar: ").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(pedidos_pendientes)):
            print("[CANCELADO] Selección inválida.")
            self.pausar()
            return

        pedido = pedidos_pendientes[int(sel) - 1]
        print(f"\nBuscando aeronave compatible con la categoría '{pedido.categoria_requerida}'...")
        exito = self.centro.asignar_dron_a_pedido(pedido.id_pedido)
        if exito:
            print(f"[ÉXITO] Aeronave '{pedido.dron_asignado.id_dron}' vinculada al pedido '{pedido.id_pedido}'.")
        else:
            print("[AVISO] No hay drones compatibles desocupados en este momento.")
        self.pausar()

    # --------------------------------------------------------------------------
    # OPCIÓN 4: SIMULACIÓN TEMPORAL DE VUELO MULTI-ETAPA (RELOJ + SIMULADOR)
    # --------------------------------------------------------------------------
    def simular_vuelo_interactivo(self) -> None:
        self.encabezado("SIMULADOR CINEMÁTICO DE VUELO CON RELOJ TEMPORAL")
        pedidos_asignados = [p for p in self.centro.pedidos if p.estado == "ASIGNADO" and p.dron_asignado is not None]

        if not pedidos_asignados:
            print("No hay pedidos en estado 'ASIGNADO' listos para despegar.")
            print("Por favor registre un pedido (Opción 2) y asígnele un dron (Opción 3).")
            self.pausar()
            return

        print("Pedidos asignados listos para despegue y simulación:")
        for idx, p in enumerate(pedidos_asignados, start=1):
            dron = p.dron_asignado
            print(f"[{idx}] {p.id_pedido} | Dron: {dron.id_dron} ({dron.categoria}) | Destino: {p.coordenada_destino}")

        sel = input("\nSeleccione el número de misión a volar: ").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(pedidos_asignados)):
            print("[CANCELADO] Selección inválida.")
            self.pausar()
            return

        pedido = pedidos_asignados[int(sel) - 1]
        dron = pedido.dron_asignado

        # 1. Consulta meteorológica en tiempo real
        clima = self.servicio_clima.obtener_condiciones("El_Poblado")
        factor_clima = clima["factor_velocidad"]
        print(f"\n--- REPORTE METEOROLÓGICO (OPEN-METEO VALLE DE ABURRÁ) ---")
        print(f"  Temperatura       : {clima['temperatura_c']:.1f} °C")
        print(f"  Velocidad Viento  : {clima['viento_kmh']:.1f} km/h")
        print(f"  Precipitación     : {clima['lluvia_mm']:.1f} mm")
        print(f"  Factor de Clima   : {factor_clima * 100:.0f}% de rendimiento nominal")
        print(f"  Vuelo Autorizado  : {'SÍ' if clima['vuelo_seguro'] else 'ALERTA METEOROLÓGICA'}")

        # 2. Despegue formal
        print(f"\n--- INICIANDO PROTOCOLO DE DESPEGUE ---")
        try:
            reporte_despegue = dron.ejecutar_mision(pedido)
            self.centro.generar_log(
                evento="DESPEGUE_MISION",
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                detalles=f"Despegue autorizado y exitoso hacia {pedido.coordenada_destino}. Distancia objetivo: {reporte_despegue['distancia_objetivo_km']} km. Batería inicial: {dron.telemetria.bateria:.1f}%."
            )
            print(f"[DESPEGUE EXITOSO] {dron.id_dron} en el aire a {dron.telemetria.altitud} m.")
            print(f"  Distancia Objetivo: {reporte_despegue['distancia_objetivo_km']} km")
            print(f"  Consumo Proyectado: {reporte_despegue['consumo_estimado']}%")
            print(f"  Instrumental Activo: {reporte_despegue.get('instrumental_activado', 'NOMINAL')}")
        except ActualizarEstadoDronError as e:
            print(f"[DESPEGUE CANCELADO]: {e}")
            self.pausar()
            return

        # 3. Menú de ejecución de la simulación
        print(f"\n{self.LINEA_SIMPLE}")
        print(" MODALIDAD DE SIMULACIÓN TEMPORAL:")
        print("  [1] Simulación Automática Animada (Reloj continuo hasta retorno a base)")
        print("  [2] Simulación Paso a Paso Discreta (Usted controla cada pulso Delta t)")
        print(f"{self.LINEA_SIMPLE}")
        modo = input("Seleccione modalidad (1 o 2, defecto 1): ").strip()
        modo_paso_a_paso = modo == "2"

        paso_segundos = 30.0
        if modo_paso_a_paso:
            p_in = input("Ingrese duración del salto temporal Delta t en segundos (defecto 30s): ").strip()
            if p_in:
                try:
                    paso_segundos = max(5.0, float(p_in))
                except ValueError:
                    paso_segundos = 30.0

        tiempo_total_mision_seg = 0.0
        print(f"\n{self.LINEA_SIMPLE}")
        print(f" {'T(s)':>5} | {'FASE OPERACIONAL':<22} | {'COORDENADAS GPS':<20} | {'RESTANTE':>9} | {'BATERÍA':<15} | {'ESTADO'}")
        print(f"{self.LINEA_SIMPLE}")

        # Bucle de integración física y cinemática
        while dron.en_mision or dron.retornando_a_base:
            reporte = self.simulador.avanzar_paso_tiempo(
                dron=dron,
                delta_t=paso_segundos,
                factor_clima=factor_clima
            )
            tiempo_total_mision_seg += paso_segundos

            fase_desc = "VUELO A DESTINO" if dron.en_mision else ("RETORNO A BASE" if dron.retornando_a_base else "ATERRIZADO")
            coords_str = f"({dron.telemetria.coordenadas[0]:.4f}, {dron.telemetria.coordenadas[1]:.4f})"
            barra = self.barra_bateria(dron.telemetria.bateria, ancho=8)

            print(
                f" {tiempo_total_mision_seg:5.0f} | "
                f"{fase_desc:<22} | "
                f"{coords_str:<20} | "
                f"{reporte['distancia_restante_km']:6.2f} km | "
                f"{barra:<15} | "
                f"{reporte['estado']}"
            )

            if reporte["estado"] == "LLEGADA_A_DESTINO":
                print(f"  >>> [EVENTO DESTINO] ¡Aeronave alcanzó las coordenadas del pedido! Pedido completado.")
                print(f"  >>> [TRANSICIÓN AUTOMÁTICA] Dron inicia fase de retorno a la base central.")
            elif reporte["estado"] == "LLEGADA_A_BASE":
                print(f"  >>> [EVENTO BASE] ¡Dron aterrizó con éxito en la base! Motores en STANDBY. Dron disponible.")
                break
            elif reporte["estado"] == "BATERIA_AGOTADA":
                print(f"  >>> [EMERGENCIA] Batería agotada por completo. Aterrizaje forzoso.")
                break

            if modo_paso_a_paso:
                sig = input("  Presione [ENTER] para avanzar el siguiente Delta t (o 'q' para auto-completar): ").strip()
                if sig.lower() == 'q':
                    modo_paso_a_paso = False
            else:
                time.sleep(0.3)

        print(f"{self.LINEA_SIMPLE}")
        if dron.telemetria.bateria <= 0.0:
            print(f"\n[MISIÓN INTERRUMPIDA POR EMERGENCIA CRÍTICA: BATERÍA AGOTADA (0.0%)]")
        else:
            print(f"\n[MISIÓN FINALIZADA CON ÉXITO]")
        print(f"  Tiempo Total de Operación : {tiempo_total_mision_seg / 60.0:.1f} minutos ({tiempo_total_mision_seg:.0f} s)")
        print(f"  Batería Final Remanente   : {dron.telemetria.bateria:.1f}%")
        print(f"  Odómetro Total Acumulado  : {dron.kilometraje_total_km:.2f} km")
        print(f"  Disponibilidad Dron       : {'DISPONIBLE' if dron.disponible else 'NO DISPONIBLE / EMERGENCIA'}")
        print(f"  Estado del Pedido         : {pedido.estado}")
        self.pausar()

    # --------------------------------------------------------------------------
    # OPCIÓN 5: COMPARACIÓN POLIMÓRFICA DE CONSUMO ENERGÉTICO (HU-10)
    # --------------------------------------------------------------------------
    def comparar_consumo_polimorfico(self) -> None:
        self.encabezado("COMPARATIVA POLIMÓRFICA DE EFICIENCIA ENERGÉTICA (HU-10)")
        distancia = 15.0
        d_in = input("Ingrese distancia a evaluar en km (defecto 15.0 km): ").strip()
        if d_in:
            try:
                distancia = max(1.0, float(d_in))
            except ValueError:
                distancia = 15.0

        print(f"\nEvaluando predicción de viabilidad para una ruta de {distancia:.1f} km a través de la flota:\n")
        print(f"{'AERONAVE':<15} | {'CATEGORÍA':<25} | {'CONSUMO':>9} | {'VIABLE':<7} | {'DIAGNÓSTICO TÉCNICO'}")
        print(self.LINEA_SIMPLE)

        for dron in self.centro.flota_drones:
            pred = dron.predecir_viabilidad_mision(distancia)
            viable_str = "SÍ" if pred["mision_viable"] else "NO"
            print(
                f"{dron.id_dron:<15} | "
                f"{dron.categoria:<25} | "
                f"{pred['consumo_estimado_pct']:6.1f} % | "
                f"{viable_str:<7} | "
                f"{pred['diagnostico_autonomia']}"
            )
        print(self.LINEA_SIMPLE)
        print("Demostración de Polimorfismo: Cada subclase calcula su consumo según sus aditamentos físicos.")
        self.pausar()

    # --------------------------------------------------------------------------
    # OPCIÓN 6: AUDITORÍA Y BITÁCORA DE OPERACIONES
    # --------------------------------------------------------------------------
    def ver_bitacora_auditoria(self) -> None:
        self.encabezado("BITÁCORA DE AUDITORÍA Y REGISTROS OPERACIONALES (LOGS)")
        logs = self.centro.historial_logs
        if not logs:
            print("No hay eventos registrados en la bitácora aún.")
        else:
            print(f"Total de registros emitidos: {len(logs)}\n")
            ultimos = logs[-10:]
            for log in ultimos:
                print(log.formatear_registro())
                print(self.LINEA_SIMPLE)
        self.pausar()

    # --------------------------------------------------------------------------
    # OPCIÓN 7: TOUR AUTOMATIZADO / DEMOSTRACIÓN COMPLETA
    # --------------------------------------------------------------------------
    def ejecutar_demo_guiada(self) -> None:
        self.encabezado("TOUR AUTOMATIZADO: DEMOSTRACIÓN END-TO-END DE SPRINT 2")
        print("Este tour ejecutará automáticamente:")
        print("  1. Creación de pedido con dirección humana geocodificada en OSM Nominatim.")
        print("  2. Asignación automática de la aeronave especializada compatible.")
        print("  3. Simulación cinemática temporal (Vuelo -> Entrega -> Retorno a Base).")
        print("  4. Comprobación de integridad de estados y auditoría.\n")
        self.pausar()

        # Asegurar que el dron de entrega ligera para la demo cuente con carga suficiente en base
        for d in self.centro.flota_drones:
            if d.categoria == "ENTREGA_LIGERA" and d.telemetria and d.telemetria.bateria < 30.0:
                print(f"  [MANTENIMIENTO BASE] Recargando {d.id_dron} en estación de carga ({d.telemetria.bateria:.1f}% -> 100.0%)...")
                d.recargar_bateria(100.0)

        # 1. Crear Pedido
        print("[PASO 1] Registrando pedido en 'Parque El Poblado'...")
        pedido = Pedido(
            id_pedido=f"DEMO-{int(time.time()) % 10000:04d}",
            usuario_solicitante=self.cliente,
            categoria_requerida="ENTREGA_LIGERA",
            coordenada_destino=None,
            direccion_destino="Parque El Poblado",
            peso_carga_kg=1.8
        )
        self.centro.registrar_pedido(pedido)
        print(f"  -> Destino resuelto: {pedido.coordenada_destino}")

        # 2. Asignar
        print("\n[PASO 2] Asignando aeronave compatible...")
        if not self.centro.asignar_dron_a_pedido(pedido.id_pedido):
            print("  [ERROR] No se pudo asignar aeronave con batería suficiente para la demo.")
            self.pausar()
            return

        dron = pedido.dron_asignado
        print(f"  -> Aeronave asignada: {dron.id_dron} ({dron.modelo_aeronave} - {dron.categoria})")

        # 3. Despegar y Simular
        print("\n[PASO 3] Despegan motores y comienza integración cinemática con Reloj...")
        try:
            reporte_despegue = dron.ejecutar_mision(pedido)
            self.centro.generar_log(
                evento="DESPEGUE_MISION",
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                detalles=f"Despegue autorizado y exitoso hacia {pedido.coordenada_destino}. Distancia objetivo: {reporte_despegue['distancia_objetivo_km']} km. Batería inicial: {dron.telemetria.bateria:.1f}%."
            )
        except ActualizarEstadoDronError as e:
            print(f"  [DESPEGUE BLOQUEADO POR PROTOCOLO DE SEGURIDAD]: {e}")
            self.pausar()
            return

        paso_t = 25.0
        tiempo_acum = 0.0
        while dron.en_mision or dron.retornando_a_base:
            reporte = self.simulador.avanzar_paso_tiempo(dron, delta_t=paso_t, factor_clima=1.0)
            tiempo_acum += paso_t
            fase = "HACIA DESTINO" if dron.en_mision else "RETORNO A BASE"
            print(f"  t={tiempo_acum:4.0f}s | {fase:14} | GPS: {dron.telemetria.coordenadas} | Restante: {reporte['distancia_restante_km']:.2f} km | {self.barra_bateria(dron.telemetria.bateria, 6)}")
            if reporte["estado"] == "BATERIA_AGOTADA":
                print(f"  >>> [EMERGENCIA CRÍTICA] ¡Batería agotada por completo (0.0%)! Aterrizaje forzoso en {dron.telemetria.coordenadas}.")
                break
            elif reporte["estado"] == "LLEGADA_A_BASE":
                break
            time.sleep(0.2)

        # 4. Estado final
        print(f"\n[PASO 4] Certificación de misión:")
        print(f"  Pedido Final : {pedido.estado}")
        if dron.telemetria.bateria <= 0.0:
            estado_dron_str = "EMERGENCIA / BATERÍA AGOTADA (ATERRIZAJE FORZOSO)"
        elif dron.disponible:
            estado_dron_str = "DISPONIBLE EN BASE"
        else:
            estado_dron_str = "OCUPADO"
        print(f"  Dron Estado  : {estado_dron_str}")
        print(f"  Batería Final: {dron.telemetria.bateria:.1f}%")
        self.pausar()

    # --------------------------------------------------------------------------
    # BUCLE PRINCIPAL DEL MENÚ
    # --------------------------------------------------------------------------
    def ejecutar(self) -> None:
        while True:
            print(f"\n{self.LINEA_DOBLE}")
            print(" SKYROUTE DRONES - CENTRO DE CONTROL DE OPERACIONES (APOO SPRINT 2)")
            print(f" Base Central: Olaya Herrera {self.centro.coordenadas_base} | Flota: {len(self.centro.flota_drones)} aeronaves")
            print(f"{self.LINEA_DOBLE}")
            print("  [1] Ver Estado de Torre de Control y Fichas Técnicas Multilínea (__str__)")
            print("  [2] Registrar Nuevo Pedido con Dirección (Geocodificación OSM / Local)")
            print("  [3] Asignar Dron Compatible a Pedido Pendiente")
            print("  [4] 🚀 Simulación Temporal de Vuelo y Retorno (Reloj + SimuladorVuelo)")
            print("  [5] Comparativa Polimórfica de Consumo y Autonomía (HU-10)")
            print("  [6] Consultar Bitácora de Auditoría y Logs Operacionales")
            print("  [7] Ejecutar Tour de Demostración Guiada (End-to-End)")
            print("  [0] Salir de la Plataforma")
            print(self.LINEA_DOBLE)

            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                self.ver_estado_flota()
            elif opcion == "2":
                self.registrar_pedido_interactivo()
            elif opcion == "3":
                self.asignar_dron_interactivo()
            elif opcion == "4":
                self.simular_vuelo_interactivo()
            elif opcion == "5":
                self.comparar_consumo_polimorfico()
            elif opcion == "6":
                self.ver_bitacora_auditoria()
            elif opcion == "7":
                self.ejecutar_demo_guiada()
            elif opcion == "0":
                print("\nCerrando sesión en la Torre de Control SkyRoute. ¡Buen vuelo!")
                break
            else:
                print("\n[AVISO] Opción no válida. Por favor seleccione un número del menú.")


def main():
    try:
        app = ConsolaSkyRoute()
        app.ejecutar()
    except KeyboardInterrupt:
        print("\n\nOperación interrumpida por el usuario. Cerrando centro de control...")
        sys.exit(0)


if __name__ == "__main__":
    main()
