# Módulo de simulación cinemática y física de vuelo
# Responsable: Módulo de Control y Simulación

from __future__ import annotations
from typing import TYPE_CHECKING
from src.geodesia.calculador import CalculadorGeodesico, ICalculadorGeodesico
from src.excepciones.errores import TelemetriaNoAsignadaError

if TYPE_CHECKING:
    from src.flota.dron import Dron


class SimuladorVuelo:
    """
    Motor de simulación física y cinemática para aeronaves en el Valle de Aburrá.
    
    Responsabilidades:
    - Ejecutar pasos de integración temporal discretos (Delta t) sobre aeronaves.
    - Aplicar factores climáticos (viento/lluvia) en la velocidad efectiva de vuelo.
    - Interpolar coordenadas geodésicas proporcionales en cada intervalo.
    - Calcular el consumo polimórfico de batería y actualizar la telemetría del dron.
    - Disparar transiciones de estado al arribar a destino o a la base central.
    """

    def __init__(self, calculador: ICalculadorGeodesico | None = None) -> None:
        self.calculador: ICalculadorGeodesico = calculador if calculador is not None else CalculadorGeodesico()

    def avanzar_paso_tiempo(
        self,
        dron: Dron,
        delta_t: float,
        factor_clima: float = 1.0,
        coordenada_objetivo: tuple[float, float] | None = None
    ) -> dict:
        """
        Avanza la física y telemetría de un dron durante un intervalo discreto de delta_t segundos.

        Soporta simulación multi-fase con propagación de tiempo remanente:
        - Si el dron llega al destino del pedido y aún queda tiempo disponible en delta_t,
          inicia inmediatamente el retorno hacia la base dentro del mismo paso temporal.
        - Si el tiempo remanente alcanza para regresar a la base central, la aeronave aterriza
          y queda marcada como disponible en ese mismo paso.
        - En cada fase acumula el odómetro en telemetría y deduce la batería polimórficamente.
        """
        if delta_t <= 0.0 or not (dron.en_mision or dron.retornando_a_base):
            return {
                "id_dron": dron.id_dron,
                "estado": "ESTACIONARIO",
                "delta_km": 0.0,
                "distancia_restante_km": 0.0,
                "bateria_actual": round(dron.telemetria.bateria, 2) if dron.telemetria else 100.0,
                "ha_llegado": False
            }

        if dron.telemetria is None:
            raise TelemetriaNoAsignadaError(dron.id_dron)

        factor_clima_seguro = max(0.1, min(1.0, float(factor_clima)))
        velocidad_efectiva_kmh = dron.velocidad_promedio_kmh * factor_clima_seguro
        velocidad_efectiva_kms = velocidad_efectiva_kmh / 3600.0

        if velocidad_efectiva_kms <= 0.0:
            return {
                "id_dron": dron.id_dron,
                "estado": "VELOCIDAD_CERO",
                "delta_km": 0.0,
                "distancia_restante_km": 0.0,
                "bateria_actual": round(dron.telemetria.bateria, 2),
                "ha_llegado": False
            }

        tiempo_restante_seg = float(delta_t)
        distancia_total_avanzada_km = 0.0
        estado_operacion = "EN_VUELO"
        ha_llegado_final = False

        # Bucle multi-fase: máximo 2 etapas consecutivas (Misión hacia destino -> Retorno hacia base)
        iteraciones_maximas = 2
        while tiempo_restante_seg > 0.0 and (dron.en_mision or dron.retornando_a_base) and iteraciones_maximas > 0:
            iteraciones_maximas -= 1

            # 1. Determinar el objetivo geográfico y la fase operativa
            if dron.en_mision and dron.pedido_activo is not None:
                objetivo = coordenada_objetivo if coordenada_objetivo is not None else dron.pedido_activo.coordenada_destino
                fase = "MISION"
            elif dron.retornando_a_base and dron.coordenadas_base is not None:
                objetivo = dron.coordenadas_base
                fase = "RETORNO"
            elif coordenada_objetivo is not None:
                objetivo = coordenada_objetivo
                fase = "OBJETIVO_DIRECTO"
            else:
                break

            # 2. Distancia restante y tiempo necesario para completar la etapa
            distancia_etapa_km = dron.calcular_distancia_a_destino(objetivo)
            tiempo_necesario_etapa_seg = (
                distancia_etapa_km / velocidad_efectiva_kms if distancia_etapa_km > 0.05 else 0.0
            )

            # 3. Comprobar si el tiempo cubre toda la etapa o solo un tramo proporcional
            if tiempo_restante_seg >= tiempo_necesario_etapa_seg or distancia_etapa_km <= 0.05:
                # Llegada al final de la etapa
                distancia_avanzada_etapa_km = distancia_etapa_km
                tiempo_consumido_etapa_seg = tiempo_necesario_etapa_seg
                coordenadas_etapa = objetivo
                ha_llegado_etapa = True
            else:
                # Avance fraccionario con el tiempo disponible restante
                distancia_avanzada_etapa_km = velocidad_efectiva_kms * tiempo_restante_seg
                tiempo_consumido_etapa_seg = tiempo_restante_seg
                fraccion = distancia_avanzada_etapa_km / distancia_etapa_km if distancia_etapa_km > 0.0 else 1.0
                coordenadas_etapa = self.calculador.calcular_punto_intermedio(
                    dron.telemetria.coordenadas, objetivo, fraccion
                )
                ha_llegado_etapa = False

            # 4. Consumo de energía polimórfico y acumulación de distancia
            consumo_etapa = dron.calcular_consumo_estimado(distancia_avanzada_etapa_km)
            nueva_bateria = max(0.0, dron.telemetria.bateria - consumo_etapa)
            distancia_total_avanzada_km += distancia_avanzada_etapa_km
            tiempo_restante_seg -= tiempo_consumido_etapa_seg

            # 5. Actualización atómica de telemetría (acumula odómetro si hay cambio geográfico)
            altitud_vuelo = 0.0 if (ha_llegado_etapa and fase == "RETORNO") else 30.0
            motores_vuelo = "STANDBY" if (ha_llegado_etapa and fase == "RETORNO") else "EN_VUELO"

            dron.actualizar_telemetria(
                bateria_o_telemetria=nueva_bateria,
                altitud=altitud_vuelo,
                estado_motores=motores_vuelo,
                coordenadas=coordenadas_etapa
            )

            # 6. Manejo de transiciones al completar la etapa
            if ha_llegado_etapa:
                if fase == "MISION":
                    dron.finalizar_mision_en_destino()
                    estado_operacion = "LLEGADA_A_DESTINO"
                    # dron.retornando_a_base queda en True; si tiempo_restante_seg > 0, el bucle procesará el retorno
                elif fase == "RETORNO":
                    dron.finalizar_retorno_en_base()
                    estado_operacion = "LLEGADA_A_BASE"
                    ha_llegado_final = True
                    break
                else:
                    estado_operacion = "EN_DESTINO"
                    ha_llegado_final = True
                    break
            else:
                estado_operacion = "RETORNANDO_A_BASE" if fase == "RETORNO" else "EN_VUELO"
                ha_llegado_final = False
                break

            # 7. Si la batería se agota por completo, detener operaciones
            if nueva_bateria <= 0.0:
                dron.actualizar_telemetria(altitud=0.0, estado_motores="STANDBY")
                estado_operacion = "BATERIA_AGOTADA"
                break

        # 8. Cálculo de distancia y ETA pendientes del objetivo final
        if dron.en_mision and dron.pedido_activo is not None:
            objetivo_final = dron.pedido_activo.coordenada_destino
        elif dron.retornando_a_base and dron.coordenadas_base is not None:
            objetivo_final = dron.coordenadas_base
        else:
            objetivo_final = None

        if objetivo_final is not None and not ha_llegado_final:
            distancia_pendiente_km = dron.calcular_distancia_a_destino(objetivo_final)
            eta_min = self.calculador.calcular_tiempo_vuelo_min(distancia_pendiente_km, velocidad_efectiva_kmh)
        else:
            distancia_pendiente_km = 0.0
            eta_min = 0.0

        return {
            "id_dron": dron.id_dron,
            "estado": estado_operacion,
            "delta_km": round(distancia_total_avanzada_km, 3),
            "distancia_restante_km": round(distancia_pendiente_km, 3),
            "eta_restante_min": round(eta_min, 2),
            "bateria_actual": round(dron.telemetria.bateria, 2),
            "coordenadas_actuales": dron.telemetria.coordenadas,
            "ha_llegado": ha_llegado_final or (estado_operacion in ("LLEGADA_A_DESTINO", "LLEGADA_A_BASE"))
        }

    def avanzar_flota(
        self,
        flota: list[Dron],
        delta_t: float,
        factor_clima: float = 1.0
    ) -> list[dict]:
        """Avanza la simulación para todas las aeronaves de una flota."""
        reportes = []
        for dron in flota:
            reporte = self.avanzar_paso_tiempo(dron, delta_t, factor_clima)
            reportes.append(reporte)
        return reportes
