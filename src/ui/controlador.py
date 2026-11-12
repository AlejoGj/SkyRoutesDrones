# Controlador de interfaz (Puente MVC / Fachada hacia el Backend POO)
# Proyecto: SkyRoute - Sistema de Gestión y Telemetría para Drones (UDEM)

from __future__ import annotations

import time
from typing import Any

from src.control.centro_control import (
    SistemaCentroControl,
    instanciar_dron_desde_fabrica,
)
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo
from src.excepciones.errores import ActualizarEstadoDronError
from src.flota import Dron, DronEntregaLigera
from src.geodesia.calculador import CalculadorGeodesico
from src.pedidos.pedido import Pedido
from src.servicios.clima import ServicioClimaAburra
from src.servicios.geocodificador import ServicioGeocodificadorArcGIS
from src.telemetria.telemetria import TelemetriaDrone
from src.ui.catalogos import (
    ESQUEMA_FABRICA,
    ETIQUETAS_CATEGORIA,
    SUGERENCIAS_DIRECCIONES,
    crear_clima_inicial_default,
    extraer_parametros_fabrica,
    inicializar_semilla_sistema,
)
from src.ui.manejador_errores import formatear_excepcion_dominio
from src.ui.serializadores import (
    construir_snapshot_estado,
    diagnosticar_candidatos_pedido,
    extraer_atributos_especializados,
    pedido_reservado_para_dron,
    serializar_dron,
    serializar_pedido,
)
from src.ui.sesiones_vuelo import (
    calcular_progreso_lineal,
    crear_sesion_base,
    crear_sesion_contingencia,
    registrar_pulso_en_sesion,
)
from src.usuarios.usuario import Usuario


class ControladorSkyRoute:
    """
    Orquestador y Fachada de presentación que comunica el servidor HTTP nativo
    con el modelo de dominio POO (SistemaCentroControl, FABRICA_DRONES, Dron,
    Pedido, SimuladorVuelo, RelojSimulacion, ServicioGeocodificadorArcGIS y
    ServicioClimaAburra), delegando catálogos, serialización DTO, sesiones de
    vuelo y manejo de excepciones en módulos cohesivos dentro de `src/ui/`.
    """

    ETIQUETAS_CATEGORIA = ETIQUETAS_CATEGORIA
    ESQUEMA_FABRICA = ESQUEMA_FABRICA
    SUGERENCIAS_DIRECCIONES = SUGERENCIAS_DIRECCIONES

    def __init__(
        self,
        geocodificador: Any | None = None,
        servicio_clima: Any | None = None,
    ) -> None:
        """
        Inicializa el adaptador MVC y los subsistemas de dominio en Olaya Herrera.

        Args:
            geocodificador (Any | None, optional): Servicio cartográfico inyectado.
                Si es None, se utiliza `ServicioGeocodificadorArcGIS`.
            servicio_clima (Any | None, optional): Servicio meteorológico inyectado.
                Si es None, se utiliza `ServicioClimaAburra`.
        """
        self.calculador = CalculadorGeodesico()
        self.geocodificador = (
            geocodificador
            if geocodificador is not None
            else ServicioGeocodificadorArcGIS(calculador=self.calculador)
        )
        self.servicio_clima = (
            servicio_clima if servicio_clima is not None else ServicioClimaAburra()
        )

        # Inicialización oficial en Aeropuerto Olaya Herrera (6.219603, -75.586792)
        self.centro = SistemaCentroControl(geocodificador=self.geocodificador)
        self.simulador = SimuladorVuelo(
            calculador=self.calculador,
            centro_control=self.centro,
        )
        self.reloj = RelojSimulacion()

        # Estado de sesión de interfaz
        self._usuario_activo_id: str = "USR-01"
        self._nodo_clima_activo: str = "El_Poblado"
        self._clima_actual: dict[str, Any] = crear_clima_inicial_default()
        self._sesiones_vuelo: dict[str, dict[str, Any]] = {}
        self._fuentes_geocodificacion: dict[str, str] = {}
        self._contador_secuencial: int = 1

        self._inicializar_entorno_base()

    def _inicializar_entorno_base(self) -> None:
        """Carga los 3 usuarios oficiales y las 6 aeronaves base al 100% de batería."""
        inicializar_semilla_sistema(self.centro, self.reloj)

    # ==========================================================================
    # BÚSQUEDA INTERNA Y DELEGACIÓN DE SERIALIZACIÓN
    # ==========================================================================

    def _buscar_dron(self, id_dron: str) -> Dron:
        """
        Busca una aeronave registrada en la flota por su ID alfanumérico.

        Args:
            id_dron (str): Identificador único de la aeronave.

        Returns:
            Dron: Instancia de la aeronave encontrada.

        Raises:
            ValueError: Si no existe un dron registrado con el ID proporcionado.
        """
        id_limpio = str(id_dron or "").strip()
        for dron in self.centro.flota_drones:
            if dron.id_dron == id_limpio:
                return dron
        raise ValueError(f"No existe una aeronave registrada con ID '{id_limpio}'.")

    def _buscar_pedido(self, id_pedido: str) -> Pedido:
        """
        Busca un pedido registrado en el centro de control por su ID alfanumérico.

        Args:
            id_pedido (str): Identificador único del pedido.

        Returns:
            Pedido: Instancia del pedido encontrado.

        Raises:
            ValueError: Si no existe un pedido registrado con el ID proporcionado.
        """
        id_limpio = str(id_pedido or "").strip()
        for pedido in self.centro.pedidos:
            if pedido.id_pedido == id_limpio:
                return pedido
        raise ValueError(f"No existe un pedido registrado con ID '{id_limpio}'.")

    def _buscar_pedido_por_id_seguro(self, id_pedido: str | None) -> Pedido | None:
        """
        Búsqueda segura de pedidos que devuelve None en lugar de elevar excepciones.

        Args:
            id_pedido (str | None): Identificador del pedido.

        Returns:
            Pedido | None: Pedido encontrado o None si no existe o el ID es nulo.
        """
        if not id_pedido:
            return None
        for p in self.centro.pedidos:
            if p.id_pedido == id_pedido:
                return p
        return None

    def _buscar_usuario(self, id_usuario: str) -> Usuario:
        """
        Busca un usuario registrado en el sistema por su identificador.

        Args:
            id_usuario (str): Identificador único del usuario.

        Returns:
            Usuario: Instancia del usuario encontrado.

        Raises:
            ValueError: Si no existe un usuario registrado con el ID dado.
        """
        id_limpio = str(id_usuario or "").strip()
        for usuario in self.centro.usuarios_registrados:
            if usuario.id_usuario == id_limpio:
                return usuario
        raise ValueError(f"No existe un usuario registrado con ID '{id_limpio}'.")

    def _pedido_reservado_para_dron(self, dron: Dron) -> Pedido | None:
        """Delega en el módulo de serialización la consulta del pedido asignado al dron."""
        return pedido_reservado_para_dron(dron, self.centro.pedidos)

    def _extraer_atributos_especializados(self, dron: Dron) -> list[dict[str, str]]:
        """Delega en el módulo de serialización la extracción de atributos específicos del dron."""
        return extraer_atributos_especializados(dron)

    def _calcular_progreso_lineal(
        self,
        dron: Dron,
        sesion: dict[str, Any] | None,
        distancia_a_base_km: float,
    ) -> dict[str, Any]:
        """Delega en el módulo de sesiones el cálculo del indicador lineal de 3 etapas."""
        return calcular_progreso_lineal(dron, sesion, distancia_a_base_km)

    def _serializar_dron(self, dron: Dron) -> dict[str, Any]:
        """Delega en el módulo de serialización la conversión de la aeronave a DTO JSON."""
        return serializar_dron(
            dron=dron,
            centro=self.centro,
            calculador=self.calculador,
            clima_actual=self._clima_actual,
            sesiones_vuelo=self._sesiones_vuelo,
        )

    def _diagnosticar_candidatos_pedido(self, pedido: Pedido) -> dict[str, Any]:
        """Delega en el módulo de serialización el análisis de autonomía de circuito para un pedido."""
        return diagnosticar_candidatos_pedido(
            pedido=pedido,
            flota=self.centro.flota_drones,
            coordenadas_base=self.centro.coordenadas_base,
            calculador=self.calculador,
        )

    def _serializar_pedido(self, pedido: Pedido) -> dict[str, Any]:
        """Delega en el módulo de serialización la conversión del pedido a DTO JSON."""
        return serializar_pedido(
            pedido=pedido,
            centro=self.centro,
            calculador=self.calculador,
            fuentes_geocodificacion=self._fuentes_geocodificacion,
        )

    def obtener_estado_completo(self) -> dict[str, Any]:
        """
        Genera el snapshot integral del Centro de Control para consumo del frontend.

        Empaqueta la flota activa, pedidos, sesiones cinemáticas, bitácora de auditoría,
        métricas operativas, reloj monotónico y condiciones climáticas vigentes.

        Returns:
            dict[str, Any]: Snapshot completo serializable en formato JSON.
        """
        usuario_activo = self._buscar_usuario(self._usuario_activo_id)
        return construir_snapshot_estado(
            centro=self.centro,
            calculador=self.calculador,
            reloj=self.reloj,
            usuario_activo=usuario_activo,
            clima_actual=self._clima_actual,
            sesiones_vuelo=self._sesiones_vuelo,
            fuentes_geocodificacion=self._fuentes_geocodificacion,
        )

    # ==========================================================================
    # CLIMA, GEOCODIFICACIÓN Y PREDICCIÓN POLIMÓRFICA (HU-10)
    # ==========================================================================

    def consultar_clima_nodo(self, nodo: str | None = None) -> dict[str, Any]:
        """
        Consulta las condiciones meteorológicas en tiempo real para un nodo del Valle de Aburrá.

        Actualiza el factor de modulación de velocidad de vuelo del sistema y autoriza o
        alerta sobre las condiciones atmosféricas en la cabina de control.

        Args:
            nodo (str | None, optional): Nombre del nodo meteorológico ('El_Poblado', 'Bello',
                'Envigado', 'Itagui', 'La_Estrella', 'Sabaneta'). Defaults to None.

        Returns:
            dict[str, Any]: Snapshot actualizado del sistema con mensaje de confirmación meteorológica.
        """
        nodo_elegido = (nodo or self._nodo_clima_activo or "El_Poblado").strip()
        if nodo_elegido not in ServicioClimaAburra.NODOS_ABURRA:
            nodo_elegido = "El_Poblado"

        self._nodo_clima_activo = nodo_elegido
        reporte = self.servicio_clima.obtener_condiciones(nodo_elegido)
        reporte["consultado_en_vivo"] = not bool(reporte.get("fallback", False))
        self._clima_actual = reporte

        estado = self.obtener_estado_completo()
        autorizacion = "Vuelo autorizado" if reporte["vuelo_seguro"] else "Alerta meteorológica activa"
        estado["mensaje_operacion"] = (
            f"Clima actualizado en {nodo_elegido}: {reporte['temperatura_c']:.1f} C, "
            f"viento {reporte['viento_kmh']:.1f} km/h, factor {reporte['factor_velocidad'] * 100:.0f}% ({autorizacion})."
        )
        return estado

    def previsualizar_geocodificacion(self, direccion: str) -> dict[str, Any]:
        """
        Previsualiza la resolución cartográfica de una dirección urbana sin crear un pedido (RF-11).

        Permite al operador verificar interactivamente en la UI las coordenadas calculadas,
        la fuente cartográfica utilizada (ArcGIS/Google/OSM/Local) y la distancia desde la base.

        Args:
            direccion (str): Dirección urbana o punto de referencia en el Valle de Aburrá.

        Returns:
            dict[str, Any]: Coordenadas resueltas, fuente, validación de geocerca y distancias ida/vuelta.
        """
        detalle = self.geocodificador.obtener_detalle_direccion(direccion)
        coords = tuple(detalle["coordenadas"])
        base = self.centro.coordenadas_base
        dist_ida = self.calculador.calcular_haversine(base, coords)
        dist_ret = self.calculador.calcular_haversine(coords, base)
        return {
            "ok": True,
            "direccion_ingresada": detalle["direccion_ingresada"],
            "latitud": round(float(detalle["latitud"]), 6),
            "longitud": round(float(detalle["longitud"]), 6),
            "coordenadas": [round(float(coords[0]), 6), round(float(coords[1]), 6)],
            "fuente": detalle.get("fuente", type(self.geocodificador).__name__),
            "dentro_valle_aburra": bool(detalle.get("dentro_valle_aburra", True)),
            "distancia_ida_km": round(dist_ida, 2),
            "distancia_ida_vuelta_km": round(dist_ida + dist_ret, 2),
        }

    def comparar_viabilidad_polimorfica(self, distancia_km: float) -> dict[str, Any]:
        """
        Genera la comparativa polimórfica de viabilidad energética para toda la flota (HU-10).

        Evalúa para una distancia dada cómo respondería cada una de las 6 subclases especializadas,
        calculando consumos de batería según su arquitectura aerodinámica y tren motriz.

        Args:
            distancia_km (float): Distancia de vuelo a evaluar en kilómetros (> 0.0).

        Returns:
            dict[str, Any]: Tabla comparativa con viabilidad, consumo estimado y diagnósticos.

        Raises:
            ValueError: Si la distancia es menor o igual a 0.0 km.
        """
        distancia = float(distancia_km)
        if distancia <= 0.0:
            raise ValueError("La distancia de evaluación debe ser mayor a 0.0 km.")

        comparativa = []
        for dron in self.centro.flota_drones:
            pred = dron.predecir_viabilidad_mision(distancia)
            tasa_km = round(dron.calcular_consumo_estimado(1.0), 2)
            categoria = getattr(dron, "categoria", getattr(dron, "CATEGORIA_ESPECIALIZADA", "ESTANDAR"))
            comparativa.append(
                {
                    **pred,
                    "modelo_aeronave": dron.modelo_aeronave,
                    "categoria": categoria,
                    "categoria_etiqueta": self.ETIQUETAS_CATEGORIA.get(categoria, categoria),
                    "velocidad_promedio_kmh": dron.velocidad_promedio_kmh,
                    "tasa_consumo_bat_km": tasa_km,
                    "disponible": dron.disponible,
                }
            )

        return {
            "ok": True,
            "distancia_evaluada_km": round(distancia, 2),
            "total_aeronaves": len(comparativa),
            "total_viables": sum(1 for item in comparativa if item["mision_viable"]),
            "resultados": comparativa,
        }

    # ==========================================================================
    # GESTIÓN DE USUARIOS, FLOTA, FÁBRICA Y TELEMETRÍA
    # ==========================================================================

    def gestionar_usuario(self, datos: dict[str, Any]) -> dict[str, Any]:
        """
        Administra el registro o cambio de usuario activo en la sesión de la interfaz (RF-06).

        Args:
            datos (dict[str, Any]): Carga útil con acción ('registrar' o 'cambiar'), ID, nombre y rol.

        Returns:
            dict[str, Any]: Snapshot actualizado del sistema con el nuevo usuario activo.
        """
        accion = str(datos.get("accion", "cambiar")).strip().lower()
        if accion == "registrar":
            id_usr = str(datos.get("id_usuario", "")).strip()
            if not id_usr:
                id_usr = f"USR-{len(self.centro.usuarios_registrados) + 1:02d}"
            nuevo = Usuario(
                id_usuario=id_usr,
                nombre=str(datos.get("nombre", "")),
                rol=str(datos.get("rol", "")),
            )
            self.centro.registrar_usuario(nuevo)
            self._usuario_activo_id = nuevo.id_usuario
            self.centro.generar_log(
                evento="USUARIO_REGISTRADO",
                detalles=f"Usuario '{nuevo.nombre}' ({nuevo.id_usuario}) registrado con rol {nuevo.rol}.",
            )
            mensaje = f"Usuario {nuevo.nombre} ({nuevo.id_usuario} · {nuevo.rol}) registrado correctamente."
        else:
            usuario = self._buscar_usuario(str(datos.get("id_usuario", "")))
            self._usuario_activo_id = usuario.id_usuario
            mensaje = f"Sesión operativa activa cambiada a {usuario.nombre} ({usuario.rol})."

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = mensaje
        return estado

    def crear_dron_desde_fabrica(self, datos: dict[str, Any]) -> dict[str, Any]:
        """
        Instancia y da de alta una nueva aeronave especializada mediante `FABRICA_DRONES`.

        Valida el nivel de batería inicial (>= 20.0%), inicializa la telemetría en la base
        y registra el evento 'ALTA_DRON_FABRICA' en la bitácora de auditoría.

        Args:
            datos (dict[str, Any]): Parámetros del formulario de fábrica (categoría, ID, modelo, velocidad, batería).

        Returns:
            dict[str, Any]: Snapshot actualizado con la aeronave incorporada y enfocada en cabina.

        Raises:
            ValueError: Si la batería inicial es menor al 20.0%.
        """
        (
            categoria,
            id_dron,
            modelo,
            velocidad,
            bateria_inicial,
            kwargs_especificos,
        ) = extraer_parametros_fabrica(datos, len(self.centro.flota_drones))

        nuevo_dron = instanciar_dron_desde_fabrica(
            categoria,
            id_dron=id_dron,
            modelo_aeronave=modelo,
            velocidad_promedio_kmh=velocidad,
            **kwargs_especificos,
        )
        base = self.centro.coordenadas_base
        nuevo_dron.asignar_telemetria(
            TelemetriaDrone(
                id_dron=nuevo_dron.id_dron,
                bateria=bateria_inicial,
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=base,
            )
        )
        nuevo_dron.coordenadas_base = base
        if bateria_inicial < 20.0:
            raise ValueError(
                "La batería inicial para dar de alta en la flota activa debe ser al menos 20.0%."
            )

        self.centro.agregar_dron(nuevo_dron)
        self.centro.generar_log(
            evento="ALTA_DRON_FABRICA",
            id_dron=nuevo_dron.id_dron,
            detalles=(
                f"Aeronave '{nuevo_dron.id_dron}' ({type(nuevo_dron).__name__} · {modelo}) "
                f"instanciada desde FABRICA_DRONES e incorporada en Olaya Herrera ({bateria_inicial:.1f}%)."
            ),
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Aeronave {nuevo_dron.id_dron} ({type(nuevo_dron).__name__}) creada desde fábrica e incorporada."
        )
        estado["dron_enfocado_id"] = nuevo_dron.id_dron
        return estado

    def recargar_bateria_dron(self, id_dron: str, porcentaje: float = 100.0) -> dict[str, Any]:
        """
        Ejecuta el protocolo de mantenimiento y recarga energética en la estación del vertipuerto.

        Si la aeronave se encontraba inmovilizada en coordenadas de aterrizaje de emergencia
        (0.0%), recargarla al >= 20% restaura su posición en la plataforma de Olaya Herrera.

        Args:
            id_dron (str): Identificador único de la aeronave a recargar.
            porcentaje (float, optional): Nivel porcentual objetivo [0.0, 100.0]. Defaults to 100.0.

        Returns:
            dict[str, Any]: Snapshot actualizado con el nuevo nivel de batería del dron.
        """
        dron = self._buscar_dron(id_dron)
        bat_previa = dron.telemetria.bateria if dron.telemetria else 0.0
        dron.recargar_bateria(float(porcentaje))
        if dron.disponible and dron.telemetria and dron.telemetria.coordenadas != self.centro.coordenadas_base:
            dron.telemetria.coordenadas = self.centro.coordenadas_base
            dron.telemetria.latitud, dron.telemetria.longitud = self.centro.coordenadas_base

        self.centro.generar_log(
            evento="RECARGA_BATERIA",
            id_dron=dron.id_dron,
            detalles=(
                f"Estación de mantenimiento en base: batería de {dron.id_dron} "
                f"recargada ({bat_previa:.1f}% -> {dron.telemetria.bateria:.1f}%)."
            ),
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Batería de {dron.id_dron} recargada a {dron.telemetria.bateria:.1f}% (disponible={dron.disponible})."
        )
        estado["dron_enfocado_id"] = dron.id_dron
        return estado

    def gestionar_telemetria_dron(self, datos: dict[str, Any]) -> dict[str, Any]:
        """
        Permite la sincronización periódica de la flota o la inyección manual de telemetría (RF-01, RF-05).

        Valida rangos WGS84, coherencia motriz (altitud > 0 requiere motores 'EN_VUELO')
        y techo legal de altitud (120 m).

        Args:
            datos (dict[str, Any]): Carga útil con acción ('refrescar_flota' o 'inyectar') y valores sensoriales.

        Returns:
            dict[str, Any]: Snapshot del sistema actualizado tras procesar la trama.
        """
        accion = str(datos.get("accion", "inyectar")).strip().lower()
        if accion == "refrescar_flota":
            resultado = self.centro.refrescar_datos_flota()
            total = int(resultado)
            estado = self.obtener_estado_completo()
            estado["mensaje_operacion"] = f"Telemetría de {total} aeronaves sincronizada bajo demanda."
            return estado

        dron = self._buscar_dron(str(datos.get("id_dron", "")))
        bateria = float(datos["bateria"]) if datos.get("bateria") not in (None, "") else None
        altitud = float(datos["altitud"]) if datos.get("altitud") not in (None, "") else None
        motores = str(datos["estado_motores"]).strip().upper() if datos.get("estado_motores") else None

        coordenadas = None
        if datos.get("latitud") not in (None, "") and datos.get("longitud") not in (None, ""):
            coordenadas = (float(datos["latitud"]), float(datos["longitud"]))
            self.calculador.validar_coordenada(coordenadas)

        dron.actualizar_telemetria(
            bateria_o_telemetria=bateria,
            altitud=altitud,
            estado_motores=motores,
            coordenadas=coordenadas,
        )
        if dron.telemetria and dron.telemetria.bateria <= 0.0:
            dron.disponible = False

        self.centro.generar_log(
            evento="TRAMA_TELEMETRIA_MANUAL",
            id_dron=dron.id_dron,
            detalles=(
                f"Trama validada en {dron.id_dron}: Bat={dron.telemetria.bateria:.1f}%, "
                f"Alt={dron.telemetria.altitud:.1f} m, Motores={dron.telemetria.estado_motores}, "
                f"GPS={dron.telemetria.coordenadas}."
            ),
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Trama de telemetría validada e inyectada en {dron.id_dron}."
        estado["dron_enfocado_id"] = dron.id_dron
        return estado

    # ==========================================================================
    # DESPACHO DE PEDIDOS, ASIGNACIÓN Y SIMULACIÓN CINEMÁTICA TEMPORAL
    # ==========================================================================

    def registrar_nuevo_pedido(self, datos: dict[str, Any]) -> dict[str, Any]:
        """
        Registra una nueva solicitud de servicio con soporte geográfico dual (RF-07, RF-11).

        Acepta tanto coordenadas numéricas directas como direcciones de texto resueltas
        por la cadena de geocodificación metropolitana.

        Args:
            datos (dict[str, Any]): Carga útil con categoría, peso de carga, usuario y destino.

        Returns:
            dict[str, Any]: Snapshot del sistema con el pedido registrado en estado 'PENDIENTE'.
        """
        id_pedido = str(datos.get("id_pedido", "")).strip()
        if not id_pedido:
            id_pedido = f"PED-{int(time.time()) % 100000:05d}-{self._contador_secuencial:02d}"
            self._contador_secuencial += 1

        categoria = str(datos.get("categoria_requerida", "ENTREGA_LIGERA")).strip().upper()
        peso_raw = datos.get("peso_carga_kg", 1.5)
        peso = float(peso_raw) if peso_raw not in ("", None) else 0.0
        direccion = str(datos.get("direccion_destino", "")).strip() or None
        id_usuario = str(datos.get("id_usuario") or self._usuario_activo_id)
        usuario = self._buscar_usuario(id_usuario)

        coordenada_destino = None
        fuente_geo = "COORDENADAS_DIRECTAS"
        lat_raw = datos.get("latitud")
        lon_raw = datos.get("longitud")
        if lat_raw not in (None, "") and lon_raw not in (None, ""):
            coordenada_destino = (float(lat_raw), float(lon_raw))
            self.calculador.validar_coordenada(coordenada_destino)
        elif direccion:
            try:
                detalle = self.geocodificador.obtener_detalle_direccion(direccion)
                fuente_geo = str(detalle.get("fuente", type(self.geocodificador).__name__))
            except Exception:
                fuente_geo = type(self.geocodificador).__name__

        nuevo_pedido = Pedido(
            id_pedido=id_pedido,
            usuario_solicitante=usuario,
            categoria_requerida=categoria,
            coordenada_destino=coordenada_destino,
            peso_carga_kg=peso,
            direccion_destino=direccion,
        )
        self.centro.registrar_pedido(nuevo_pedido)
        self._fuentes_geocodificacion[nuevo_pedido.id_pedido] = fuente_geo

        dist_ida = self.calculador.calcular_haversine(
            self.centro.coordenadas_base, nuevo_pedido.coordenada_destino
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Pedido {nuevo_pedido.id_pedido} registrado hacia {nuevo_pedido.coordenada_destino} "
            f"(distancia ida: {dist_ida:.2f} km, ida+vuelta: {dist_ida * 2:.2f} km)."
        )
        estado["pedido_creado_id"] = nuevo_pedido.id_pedido
        return estado

    def asignar_dron_pedido(self, id_pedido: str) -> dict[str, Any]:
        """
        Asigna una aeronave compatible a un pedido validando autonomía de circuito completo (RF-08).

        Si ninguna aeronave cumple con disponibilidad y autonomía de ida + vuelta,
        eleva una excepción estructurada detallando los motivos exactos de rechazo.

        Args:
            id_pedido (str): Identificador único del pedido en estado 'PENDIENTE'.

        Returns:
            dict[str, Any]: Snapshot del sistema con el pedido 'ASIGNADO' y la aeronave reservada.

        Raises:
            ActualizarEstadoDronError: Si no hay drones compatibles con autonomía suficiente.
        """
        pedido = self._buscar_pedido(id_pedido)
        diagnostico_previo = self._diagnosticar_candidatos_pedido(pedido)
        asignado = self.centro.asignar_dron_a_pedido(pedido.id_pedido)

        if not asignado:
            candidatos = diagnostico_previo["candidatos"]
            if not candidatos:
                motivo = f"No existen aeronaves registradas en la categoría '{pedido.categoria_requerida}'."
            else:
                partes = []
                for c in candidatos:
                    if not c["disponible"]:
                        partes.append(f"{c['id_dron']} ocupado/no disponible ({c['bateria_actual_pct']:.1f}%)")
                    elif not c["apto_bateria"]:
                        partes.append(
                            f"{c['id_dron']} batería insuficiente ({c['bateria_actual_pct']:.1f}% actual vs "
                            f"{c['consumo_ida_vuelta_pct']:.1f}% requerido ida+vuelta)"
                        )
                    else:
                        partes.append(f"{c['id_dron']} no elegible")
                motivo = "Ninguna aeronave cumple disponibilidad y autonomía ida+vuelta: " + "; ".join(partes) + "."
            raise ActualizarEstadoDronError("FLOTA", motivo)

        dron = pedido.dron_asignado
        if dron is not None and pedido.coordenada_destino is not None:
            dist_ida = dron.calcular_distancia_a_destino(pedido.coordenada_destino)
            dist_ret = self.calculador.calcular_haversine(
                pedido.coordenada_destino, self.centro.coordenadas_base
            )
            self._sesiones_vuelo[dron.id_dron] = crear_sesion_base(
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                categoria=pedido.categoria_requerida,
                direccion_destino=pedido.direccion_destino or f"{pedido.coordenada_destino}",
                coordenadas_origen=self.centro.coordenadas_base,
                coordenadas_destino=pedido.coordenada_destino,
                distancia_ida_km=dist_ida,
                distancia_retorno_km=dist_ret,
                ultimo_estado_pulso="ASIGNADO",
                ultimo_progreso_pct=0.0,
                ultima_etapa=0,
            )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Asignación exitosa: {dron.id_dron} ({dron.modelo_aeronave}) reservado para {pedido.id_pedido}."
        )
        estado["dron_enfocado_id"] = dron.id_dron if dron else None
        estado["pedido_enfocado_id"] = pedido.id_pedido
        return estado

    def cancelar_pedido(self, id_pedido: str) -> dict[str, Any]:
        """
        Cancela una solicitud de servicio antes de su despegue y libera la aeronave asignada.

        Args:
            id_pedido (str): Identificador único del pedido en estado 'PENDIENTE' o 'ASIGNADO'.

        Returns:
            dict[str, Any]: Snapshot del sistema con el pedido cancelado y la flota liberada.

        Raises:
            ValueError: Si el pedido ya se encuentra en tránsito o completado.
        """
        pedido = self._buscar_pedido(id_pedido)
        if pedido.estado not in ("PENDIENTE", "ASIGNADO"):
            raise ValueError(
                f"Solo se pueden cancelar pedidos en estado PENDIENTE o ASIGNADO (actual: {pedido.estado})."
            )

        dron = pedido.dron_asignado
        if dron is not None and dron.pedido_activo is None and not dron.retornando_a_base:
            dron.en_mision = False
            if dron.telemetria is not None and dron.telemetria.bateria >= 20.0:
                dron.disponible = True
            self._sesiones_vuelo.pop(dron.id_dron, None)

        pedido.actualizar_estado("CANCELADO")
        self.centro.generar_log(
            evento="PEDIDO_CANCELADO",
            id_dron=dron.id_dron if dron else None,
            id_pedido=pedido.id_pedido,
            detalles=f"Pedido {pedido.id_pedido} cancelado por el operador antes del despegue.",
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Pedido {pedido.id_pedido} cancelado y recursos liberados."
        return estado

    def despegar_mision(
        self,
        id_pedido: str = "",
        modo_despacho: str = "TEMPORAL",
        actualizar_clima: bool = True,
        id_dron: str = "",
    ) -> dict[str, Any]:
        """
        Autoriza y ejecuta el despegue físico de la aeronave para iniciar una misión (RF-12).

        Soporta dos modalidades de despacho:
        - 'TEMPORAL': Despega a 30 m de altitud crucero y prepara la simulación continua por pulsos.
        - 'INSTANTANEO': Ejecuta el despacho completo de ida y retorno en una sola operación atómica.

        Args:
            id_pedido (str, optional): ID del pedido a despachar.
            modo_despacho (str, optional): 'TEMPORAL' o 'INSTANTANEO'. Defaults to 'TEMPORAL'.
            actualizar_clima (bool, optional): Consulta condiciones meteorológicas antes de volar.
            id_dron (str, optional): ID del dron si se busca despachar por aeronave.

        Returns:
            dict[str, Any]: Snapshot actualizado con la aeronave en el aire y la sesión iniciada.

        Raises:
            ValueError: Si el pedido no está en estado 'ASIGNADO' con dron vinculado.
            ActualizarEstadoDronError: Si la misión es rechazada por sobrepeso o fallo de despacho.
        """
        if not id_pedido and id_dron:
            for p in self.centro.pedidos:
                if p.dron_asignado and p.dron_asignado.id_dron == id_dron and p.estado == "ASIGNADO":
                    pedido = p
                    id_pedido = p.id_pedido
                    break

        pedido = self._buscar_pedido(id_pedido)
        if pedido.estado != "ASIGNADO" or pedido.dron_asignado is None:
            raise ValueError(
                f"El pedido '{pedido.id_pedido}' debe estar en estado ASIGNADO con un dron reservado."
            )

        dron = pedido.dron_asignado

        if actualizar_clima:
            clima = self.servicio_clima.obtener_condiciones(self._nodo_clima_activo)
            clima["consultado_en_vivo"] = not bool(clima.get("fallback", False))
            self._clima_actual = clima

        if modo_despacho.strip().upper() == "INSTANTANEO":
            if isinstance(dron, DronEntregaLigera) and not dron.es_apto_carga(pedido.peso_carga_kg):
                dron.en_mision = False
                dron.disponible = True
                pedido.actualizar_estado("CANCELADO")
                raise ActualizarEstadoDronError(
                    dron.id_dron,
                    f"Misión rechazada por sobrepeso: {pedido.peso_carga_kg:.1f} kg excede {dron.capacidad_carga_kg:.1f} kg.",
                )
            exito = self.centro.despachar_mision(pedido.id_pedido)
            if not exito:
                raise ActualizarEstadoDronError(
                    dron.id_dron,
                    f"El centro de control rechazó el despacho instantáneo del pedido {pedido.id_pedido}.",
                )
            dist_ret = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
            sesion = self._sesiones_vuelo.setdefault(dron.id_dron, {})
            sesion.update(
                crear_sesion_base(
                    id_dron=dron.id_dron,
                    id_pedido=pedido.id_pedido,
                    categoria=pedido.categoria_requerida,
                    direccion_destino=pedido.direccion_destino or f"{pedido.coordenada_destino}",
                    coordenadas_origen=self.centro.coordenadas_base,
                    coordenadas_destino=pedido.coordenada_destino,
                    distancia_ida_km=dist_ret,
                    distancia_retorno_km=dist_ret,
                    ultimo_estado_pulso="RETORNANDO_A_BASE",
                    ultimo_progreso_pct=50.0,
                    ultima_etapa=2,
                )
            )
            estado = self.obtener_estado_completo()
            estado["mensaje_operacion"] = (
                f"Despacho instantáneo ejecutado para {pedido.id_pedido}; {dron.id_dron} quedó en retorno a base."
            )
            estado["dron_enfocado_id"] = dron.id_dron
            return estado

        self.reloj.obtener_delta()
        dron.coordenadas_base = self.centro.coordenadas_base
        try:
            reporte_despegue = dron.ejecutar_mision(pedido)
        except Exception as exc:
            dron.en_mision = False
            dron.pedido_activo = None
            if dron.telemetria is not None and dron.telemetria.bateria >= 20.0:
                dron.disponible = True
            pedido.actualizar_estado("CANCELADO")
            self.centro.generar_log(
                evento="DESPEGUE_RECHAZADO",
                id_dron=dron.id_dron,
                id_pedido=pedido.id_pedido,
                detalles=f"Despegue cancelado por protocolo de seguridad: {exc}",
            )
            raise

        self.centro.generar_log(
            evento="DESPEGUE_MISION",
            id_dron=dron.id_dron,
            id_pedido=pedido.id_pedido,
            detalles=(
                f"Despegue autorizado y exitoso hacia {pedido.coordenada_destino}. "
                f"Distancia objetivo: {reporte_despegue['distancia_objetivo_km']} km. "
                f"Batería inicial: {dron.telemetria.bateria:.1f}%."
            ),
        )

        dist_ida = float(reporte_despegue.get("distancia_objetivo_km", 0.5))
        dist_ret = self.calculador.calcular_haversine(
            pedido.coordenada_destino, self.centro.coordenadas_base
        )
        reporte_serializado = {
            **reporte_despegue,
            "coordenadas_origen": list(reporte_despegue["coordenadas_origen"]),
            "coordenadas_destino": list(reporte_despegue["coordenadas_destino"]),
        }
        self._sesiones_vuelo[dron.id_dron] = crear_sesion_base(
            id_dron=dron.id_dron,
            id_pedido=pedido.id_pedido,
            categoria=pedido.categoria_requerida,
            direccion_destino=pedido.direccion_destino or f"{pedido.coordenada_destino}",
            coordenadas_origen=dron.telemetria.coordenadas,
            coordenadas_destino=pedido.coordenada_destino,
            distancia_ida_km=dist_ida,
            distancia_retorno_km=dist_ret,
            ultimo_estado_pulso="DESPEGUE_EXITOSO",
            ultimo_progreso_pct=0.0,
            ultima_etapa=1,
            instrumental_activado=reporte_despegue.get("instrumental_activado", "NOMINAL"),
            reporte_despegue=reporte_serializado,
        )

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = (
            f"Despegue exitoso: {dron.id_dron} en el aire a {dron.telemetria.altitud:.0f} m "
            f"(Instrumental: {reporte_despegue.get('instrumental_activado', 'NOMINAL')})."
        )
        estado["dron_enfocado_id"] = dron.id_dron
        estado["reporte_despegue"] = reporte_serializado
        return estado

    def avanzar_simulacion(
        self,
        id_dron: str | None = None,
        delta_t: float = 30.0,
        usar_reloj_real: bool = False,
        escala_tiempo: float = 15.0,
    ) -> dict[str, Any]:
        """
        Avanza un pulso temporal discreto en la simulación física cinemática (RF-13).

        Soporta simulación concurrente multidrón: si `id_dron` es None, avanza todas
        las aeronaves actualmente en vuelo al unísono. Modula la velocidad según el
        clima vigente, interpola coordenadas geodésicas y descuenta batería polimórficamente.

        Args:
            id_dron (str | None, optional): ID de la aeronave a avanzar, o None para toda la flota en vuelo.
            delta_t (float, optional): Delta temporal en segundos para simulación manual o automática. Defaults to 30.0.
            usar_reloj_real (bool, optional): Si True, utiliza el tiempo monotónico medido por `reloj.obtener_delta()`.
            escala_tiempo (float, optional): Factor multiplicador para el reloj en tiempo real. Defaults to 15.0.

        Returns:
            dict[str, Any]: Snapshot del sistema con la lista de pulsos emitidos y posiciones actualizadas.
        """
        delta_reloj = self.reloj.obtener_delta()
        if usar_reloj_real:
            factor_escala = max(0.1, float(escala_tiempo))
            if factor_escala == 1.0:
                paso_seg = max(0.5, min(120.0, delta_reloj))
            else:
                paso_seg = max(1.0, min(120.0, delta_reloj * factor_escala))
        else:
            paso_seg = max(1.0, float(delta_t))

        factor_clima = float(self._clima_actual.get("factor_velocidad", 1.0))

        if id_dron:
            objetivos = [self._buscar_dron(id_dron)]
        else:
            objetivos = [
                d
                for d in self.centro.flota_drones
                if (d.en_mision and d.pedido_activo is not None) or d.retornando_a_base
            ]

        pulsos_emitidos: list[dict[str, Any]] = []
        for dron in objetivos:
            estaba_activo = (dron.en_mision and dron.pedido_activo is not None) or dron.retornando_a_base
            if not estaba_activo:
                continue

            pedido_ref = dron.pedido_activo or getattr(dron, "ultimo_pedido_completado", None)
            reporte = self.simulador.avanzar_paso_tiempo(
                dron=dron,
                delta_t=paso_seg,
                factor_clima=factor_clima,
            )

            if dron.id_dron not in self._sesiones_vuelo:
                self._sesiones_vuelo[dron.id_dron] = crear_sesion_contingencia(
                    dron=dron,
                    pedido_ref=pedido_ref,
                    coordenadas_base=self.centro.coordenadas_base,
                )
            sesion = self._sesiones_vuelo[dron.id_dron]
            pedido_final = pedido_ref or self._buscar_pedido_por_id_seguro(sesion.get("id_pedido"))

            pulso_item = registrar_pulso_en_sesion(
                dron=dron,
                sesion=sesion,
                reporte=reporte,
                paso_seg=paso_seg,
                pedido_final=pedido_final,
            )
            pulsos_emitidos.append(pulso_item)

        estado = self.obtener_estado_completo()
        estado["pulsos_emitidos"] = pulsos_emitidos
        estado["delta_aplicado_seg"] = round(paso_seg, 1)
        if pulsos_emitidos:
            ult = pulsos_emitidos[-1]
            if ult["evento_especial"]:
                estado["mensaje_operacion"] = ult["evento_especial"]
        return estado

    def ordenar_retorno_base(self, id_dron: str) -> dict[str, Any]:
        """
        Emite una orden de retorno obligatorio a la base central para una aeronave en vuelo (RF-09).

        Si el dron transportaba un pedido activo, este se cancela para priorizar la seguridad
        aeronáutica y la aeronave invierte su rumbo hacia Olaya Herrera.

        Args:
            id_dron (str): Identificador único de la aeronave a ordenar.

        Returns:
            dict[str, Any]: Snapshot del sistema con la bandera `retornando_a_base=True`.

        Raises:
            ActualizarEstadoDronError: Si la aeronave no se encuentra en vuelo.
        """
        dron = self._buscar_dron(id_dron)
        pedido_cancelado_id = None
        if dron.pedido_activo is not None and dron.pedido_activo.estado == "EN_TRANSITO":
            pedido_cancelado_id = dron.pedido_activo.id_pedido
            dron.pedido_activo.actualizar_estado("CANCELADO")
            dron.pedido_activo = None

        exito = self.centro.gestionar_retorno_a_base(dron.id_dron)
        if not exito:
            raise ActualizarEstadoDronError(
                dron.id_dron,
                "La aeronave no se encuentra en una misión activa para ordenar retorno a base.",
            )

        dist_base = dron.calcular_distancia_a_destino(self.centro.coordenadas_base)
        sesion = self._sesiones_vuelo.setdefault(dron.id_dron, {})
        sesion["abortado"] = True
        sesion["distancia_retorno_total_km"] = round(max(dist_base, 0.05), 3)
        sesion["ultimo_estado_pulso"] = "RETORNANDO_A_BASE"

        estado = self.obtener_estado_completo()
        sufijo = f" (pedido {pedido_cancelado_id} marcado CANCELADO)" if pedido_cancelado_id else ""
        estado["mensaje_operacion"] = (
            f"Retorno obligatorio a Olaya Herrera activado para {dron.id_dron} "
            f"({dist_base:.2f} km restantes){sufijo}."
        )
        return estado

    def finalizar_retorno_manual(self, id_dron: str) -> dict[str, Any]:
        """
        Valida el aterrizaje manual en el vertipuerto central dentro de la tolerancia de 50 m.

        Apaga los motores a 'STANDBY', fija la altitud en 0.0 m y restaura la disponibilidad
        de la aeronave si conserva al menos 20.0% de batería.

        Args:
            id_dron (str): Identificador único de la aeronave que aterrizó.

        Returns:
            dict[str, Any]: Snapshot actualizado con el dron en plataforma y disponible.
        """
        dron = self._buscar_dron(id_dron)
        dron.finalizar_retorno_en_base()
        if dron.telemetria is not None:
            dron.actualizar_telemetria(
                altitud=0.0,
                estado_motores="STANDBY",
                coordenadas=self.centro.coordenadas_base,
            )
        sesion = self._sesiones_vuelo.get(dron.id_dron)
        if sesion is not None:
            sesion["completada_en_base"] = True
            sesion["ultimo_estado_pulso"] = "LLEGADA_A_BASE"
        self.centro.generar_log(
            evento="ATERRIZAJE_MANUAL_BASE",
            id_dron=dron.id_dron,
            detalles=f"Aterrizaje manual validado en Olaya Herrera para {dron.id_dron}.",
        )
        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = f"Aterrizaje manual completado: {dron.id_dron} disponible en base."
        return estado

    def controlar_reloj(self, accion: str) -> dict[str, Any]:
        """
        Controla el estado operativo del temporizador cinemático del sistema.

        Args:
            accion (str): 'reiniciar' (restablece a 0 s), 'pausar' o 'reanudar'.

        Returns:
            dict[str, Any]: Snapshot del sistema con el estado actualizado del reloj.

        Raises:
            ValueError: Si la acción no es reconocida.
        """
        acc = accion.strip().lower()
        if acc == "reiniciar":
            self.reloj.reiniciar()
            self.reloj.pausado = False
            msg = "Reloj de simulación reiniciado a 0.0 s."
        elif acc == "pausar":
            self.reloj.pausado = True
            msg = "Reloj de simulación en pausa."
        elif acc == "reanudar":
            self.reloj.obtener_delta()
            self.reloj.pausado = False
            msg = "Reloj de simulación reanudado."
        else:
            raise ValueError(f"Acción de reloj no reconocida: '{accion}'.")

        estado = self.obtener_estado_completo()
        estado["mensaje_operacion"] = msg
        return estado

    # ==========================================================================
    # TOUR AUTOMATIZADO END-TO-END (OPCIÓN 7 DE CONSOLASKYROUTE)
    # ==========================================================================

    def preparar_tour_guiado(self) -> dict[str, Any]:
        """
        Ejecuta el protocolo preparatorio para la demostración integral End-to-End.

        1. Realiza mantenimiento preventivo recargando al 100% las aeronaves de Entrega Ligera.
        2. Registra un pedido hacia la dirección urbana 'Parque El Poblado' (1.8 kg).
        3. Asigna la aeronave compatible validando autonomía de ida y vuelta.
        4. Autoriza el despegue e inicia la cinemática temporal con pulsos Delta t sugeridos de 25 s.

        Returns:
            dict[str, Any]: Snapshot con la misión iniciada y la guía paso a paso del tour.
        """
        pasos_tour: list[str] = []

        for d in self.centro.flota_drones:
            if (
                getattr(d, "categoria", None) == "ENTREGA_LIGERA"
                and not d.en_mision
                and not d.retornando_a_base
                and d.telemetria is not None
                and d.telemetria.bateria < 35.0
            ):
                bat_ant = d.telemetria.bateria
                d.recargar_bateria(100.0)
                d.telemetria.coordenadas = self.centro.coordenadas_base
                pasos_tour.append(
                    f"Mantenimiento preventivo en base: {d.id_dron} recargado ({bat_ant:.1f}% -> 100.0%)."
                )

        id_demo = f"DEMO-{int(time.time()) % 10000:04d}-{self._contador_secuencial:02d}"
        self._contador_secuencial += 1
        cliente = self._buscar_usuario("USR-01")

        try:
            detalle = self.geocodificador.obtener_detalle_direccion("Parque El Poblado")
            fuente = str(detalle.get("fuente", type(self.geocodificador).__name__))
        except Exception:
            fuente = type(self.geocodificador).__name__

        pedido = Pedido(
            id_demo,
            cliente,
            "ENTREGA_LIGERA",
            coordenada_destino=None,
            direccion_destino="Parque El Poblado",
            peso_carga_kg=1.8,
        )
        self.centro.registrar_pedido(pedido)
        self._fuentes_geocodificacion[pedido.id_pedido] = fuente
        pasos_tour.append(
            f"Paso 1: Pedido {pedido.id_pedido} geocodificado hacia 'Parque El Poblado' -> {pedido.coordenada_destino} ({fuente})."
        )

        self.asignar_dron_pedido(pedido.id_pedido)
        dron = pedido.dron_asignado
        pasos_tour.append(
            f"Paso 2: Aeronave compatible {dron.id_dron} ({dron.modelo_aeronave}) vinculada tras validar ida y retorno."
        )

        estado_despegue = self.despegar_mision(
            pedido.id_pedido, modo_despacho="TEMPORAL", actualizar_clima=True
        )
        pasos_tour.append(
            "Paso 3: Despegue autorizado a 30 m; iniciando integración cinemática temporal con pulsos Delta t = 25 s."
        )

        estado_despegue["tour_guiado"] = {
            "id_pedido": pedido.id_pedido,
            "id_dron": dron.id_dron,
            "delta_t_sugerido": 25.0,
            "pasos_ejecutados": pasos_tour,
        }
        estado_despegue["mensaje_operacion"] = (
            f"Tour End-to-End iniciado: {pedido.id_pedido} en vuelo con {dron.id_dron} hacia Parque El Poblado."
        )
        return estado_despegue

    # ==========================================================================
    # CLASIFICACIÓN DE EXCEPCIONES DE DOMINIO (RF-02)
    # ==========================================================================

    @staticmethod
    def formatear_excepcion(exc: Exception) -> dict[str, Any]:
        """
        Traduce excepciones del dominio POO a formato estructurado JSON para la interfaz (RF-02).

        Args:
            exc (Exception): Excepción capturada en la capa HTTP.

        Returns:
            dict[str, Any]: Diccionario con `ok: False`, tipo, mensaje y regla de negocio vulnerada.
        """
        return formatear_excepcion_dominio(exc)
