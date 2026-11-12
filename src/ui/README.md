# Módulo de Interfaz Gráfica y Servidor HTTP (`src/ui/`)

Servidor web HTTP nativo sin dependencias externas (`http.server`), adaptador MVC (Patrón Fachada), gestión cinemática de sesiones de vuelo y puente de comunicación JSON con el dashboard web interactivo de SkyRoute en el Valle de Aburrá.

* **Responsables de Implementación:**
  * **Alejandro García Jiménez:** Servidor HTTP multi-hilo, sincronización de concurrencia (`threading.RLock`), integración cinemática en tiempo real y adaptador MVC.
  * **Valery Arboleda Ardila:** Mapeo de reglas de negocio para auditoría (RF-02) y serializadores de pedidos/usuarios.
  * **Juan Manuel Pava Higuita:** Serialización polimórfica de la flota y extracción de atributos de hardware especializado.
* **Historias de Usuario Vinculadas:** HU-01 a HU-12
* **Requisitos Funcionales:** RF-01, RF-02, RF-05, RF-06, RF-07, RF-08, RF-09, RF-10, RF-11, RF-12, RF-13, RF-14

---

## 1. Propósito y Alcance

El paquete `src/ui/` proporciona la capa de presentación y el puente HTTP entre el navegador web y el núcleo de dominio orientado a objetos de SkyRoute. Sus responsabilidades comprenden:

1. **Servidor HTTP Multi-hilo Nativo (`servidor.py`):** Instanciar un `ThreadingHTTPServer` sobre la biblioteca estándar de Python sin frameworks externos (Flask, FastAPI o Django), sirviendo recursos estáticos locales (`index.html`, `estilos.css`, `app.js`, Leaflet.js) y despachando la API REST JSON.
2. **Control Concurrente Reentrante (`threading.RLock`):** Proteger las mutaciones del modelo de simulación y del centro de control ante colisiones entre pulsos automáticos de fondo e interacciones manuales del operador en el navegador.
3. **Fachada Orquestadora (`controlador.py`):** Exponer al servidor web una interfaz unificada de alto nivel (`ControladorSkyRoute`) que desacopla el transporte HTTP de las clases de dominio (`SistemaCentroControl`, `SimuladorVuelo`, `RelojSimulacion`).
4. **Catálogos y Semilla Base (`catalogos.py`):** Centralizar metadatos de presentación, esquemas dinámicos de formularios de fábrica y el protocolo de arranque con los 3 usuarios oficiales y las 6 aeronaves base en Olaya Herrera.
5. **Máquina de Estados de Sesiones de Vuelo (`sesiones_vuelo.py`):** Rastrear el progreso cinemático lineal de 3 etapas (0% Base -> 50% Destino -> 100% Retorno), la bitácora de pulsos en vuelo y las certificaciones finales de misión.
6. **Serializadores DTO (`serializadores.py`):** Convertir las entidades POO (`Dron`, `Pedido`, `Usuario`, `LogOperacion`) a diccionarios JSON inmutables para el consumo reactivo del frontend (`app.js`).
7. **Traductor de Excepciones a Reglas de Negocio (`manejador_errores.py`):** Capturar excepciones del dominio aeronáutico y clasificarlas hacia las Reglas de Negocio normativas (#1 a #12) con código `HTTP 400 Bad Request`.

---

## 2. Arquitectura Interna del Paquete

```
+---------------------------------------------------------------------------------------------------+
|                                       NAVEGADOR WEB (CLIENTE)                                     |
|   - Leaflet.js (Cartografía Aburrá)                - app.js (peticionAPI / aplicarSnapshot)       |
|   - index.html (5 Espacios de Trabajo)             - estilos.css (Diseño Aeronáutico)             |
+---------------------------------------------------------------------------------------------------+
                                                  |  HTTP / REST (JSON)
                                                  v
+---------------------------------------------------------------------------------------------------+
|                               servidor.py (ThreadingHTTPServer)                                   |
|   - ManejadorSkyRouteHTTP (do_GET / do_POST)       - Concurrencia segura: threading.RLock         |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                            controlador.py (ControladorSkyRoute · Fachada)                         |
+---------------------------------------------------------------------------------------------------+
         |                           |                           |                           |
         v                           v                           v                           v
+------------------+       +-------------------+       +--------------------+      +----------------+
|   catalogos.py   |       | sesiones_vuelo.py |       | serializadores.py  |      |  manejador_    |
+------------------+       +-------------------+       +--------------------+      |   errores.py   |
| - ESQUEMA_FABRICA|       | - calcular_progre-|       | - serializar_dron  |      +----------------+
| - ETIQUETAS_CAT  |       |   so_lineal()     |       | - serializar_pedido|      | - MAPA_REGLAS  |
| - semilla_base() |       | - crear_sesion_   |       | - diagnosticar_    |      | - formatear_   |
| - extraer_param_ |       |   base()          |       |   candidatos()     |      |   excepcion_   |
|   fabrica()      |       | - registrar_pulso |       | - construir_       |      |   dominio()    |
+------------------+       +-------------------+       |   snapshot()       |      +----------------+
                                                       +--------------------+
```

---

## 3. Catálogo de Funciones y Módulos

### 3.1 `src/ui/controlador.py` (`ControladorSkyRoute`)

* **`obtener_estado_completo() -> dict[str, Any]`:** Construye el snapshot atómico y completo del sistema con métricas, flota, pedidos y bitácora.
* **`consultar_clima_nodo(nodo: str | None) -> dict[str, Any]`:** Actualiza el reporte meteorológico en vivo para un sector del Valle de Aburrá y modula la velocidad de vuelo.
* **`previsualizar_geocodificacion(direccion: str) -> dict[str, Any]`:** Resuelve una dirección urbana cartográficamente y calcula distancias sin persistir un pedido.
* **`comparar_viabilidad_polimorfica(distancia_km: float) -> dict[str, Any]`:** Evalúa cuantitativamente el consumo y aptitud de las 6 subclases de drones ante una distancia dada.
* **`gestionar_usuario(datos: dict[str, Any]) -> dict[str, Any]`:** Registra un nuevo usuario con rol RBAC o conmuta la sesión activa en cabina.
* **`crear_dron_desde_fabrica(datos: dict[str, Any]) -> dict[str, Any]`:** Instancia dinámicamente una nueva aeronave validando que su batería inicial sea $\ge 20.0\%$.
* **`recargar_bateria_dron(id_dron: str, porcentaje: float) -> dict[str, Any]`:** Aplica mantenimiento energético en base; si estaba en 0.0% lo reposiciona en plataforma.
* **`gestionar_telemetria_dron(datos: dict[str, Any]) -> dict[str, Any]`:** Refresca la flota bajo demanda o inyecta tramas sensoriales manuales validadas.
* **`registrar_nuevo_pedido(datos: dict[str, Any]) -> dict[str, Any]`:** Da de alta solicitudes comerciales con destino dual (coordenadas o texto).
* **`asignar_dron_pedido(id_pedido: str) -> dict[str, Any]`:** Asigna aeronaves verificando disponibilidad y autonomía de circuito completo (ida + retorno).
* **`cancelar_pedido(id_pedido: str) -> dict[str, Any]`:** Cancela pedidos no despachados y libera la reserva de la aeronave.
* **`despegar_mision(id_pedido, modo_despacho, ...) -> dict[str, Any]`:** Autoriza el despegue físico a 30 m de crucero e inicia la cinemática de vuelo.
* **`avanzar_simulacion(id_dron, delta_t, ...) -> dict[str, Any]`:** Avanza la integración discreta temporal en un dron o en toda la flota concurrente.
* **`ordenar_retorno_base(id_dron: str) -> dict[str, Any]`:** Cancela el pedido en tránsito si existía y fuerza el regreso inmediato al vertipuerto.
* **`finalizar_retorno_manual(id_dron: str) -> dict[str, Any]`:** Aterriza la aeronave dentro de la tolerancia de 50 m y apaga motores a `STANDBY`.
* **`controlar_reloj(accion: str) -> dict[str, Any]`:** Reinicia, pausa o reanuda el reloj monotónico del sistema.
* **`preparar_tour_guiado() -> dict[str, Any]`:** Ejecuta de forma automática los preparativos del Tour Guiado End-to-End.

### 3.2 `src/ui/sesiones_vuelo.py`

* **`calcular_progreso_lineal(dron, sesion, distancia_a_base_km) -> dict[str, Any]`:** Modela el indicador visual en 3 etapas:
  * **Etapa 0 (0%):** En plataforma de despegue.
  * **Etapa 1 (0% a 50%):** Vuelo de ida hacia el destino.
  * **Etapa 2 (50% a 100%):** Vuelo de regreso a Olaya Herrera.
  * **Etapa 3 (100%):** Aterrizaje confirmado y motores en `STANDBY`.
  * **Emergencia 0.0%:** Fase `EMERGENCIA_BATERIA` por agotamiento crítico.
* **`crear_sesion_base(...) -> dict[str, Any]`:** Inicializa la estructura con las 17 propiedades requeridas por el frontend.
* **`crear_sesion_contingencia(dron, pedido_ref, base) -> dict[str, Any]`:** Inicialización defensiva de sesión ante drones en vuelo no registrados previamente.
* **`registrar_pulso_en_sesion(dron, sesion, reporte, paso_seg, pedido_final) -> dict[str, Any]`:** Incorpora la cinemática del pulso discreto y emite la certificación terminal (`EXITO` o `EMERGENCIA_BATERIA`).

### 3.3 `src/ui/serializadores.py`

* **`pedido_reservado_para_dron(dron, pedidos) -> Pedido | None`:** Identifica el pedido activo o reservado para una aeronave.
* **`extraer_atributos_especializados(dron) -> list[dict[str, str]]`:** Extrae dinámicamente especificaciones de hardware (cámaras, sensores, tolvas, FLIR).
* **`diagnosticar_candidatos_pedido(pedido, flota, base, calculador) -> dict[str, Any]`:** Computa el consumo energético ida + vuelta para cada dron candidato.
* **`serializar_dron(dron, centro, calculador, clima, sesiones) -> dict[str, Any]`:** Transforma el estado del dron a DTO con odómetro, velocidad efectiva y ETA.
* **`serializar_pedido(pedido, centro, calculador, fuentes) -> dict[str, Any]`:** Transforma pedidos con análisis de elegibilidad y geocodificación.
* **`construir_snapshot_estado(...) -> dict[str, Any]`:** Ensambla el estado atómico global del sistema.

### 3.4 `src/ui/catalogos.py`

* **`crear_clima_inicial_default() -> dict[str, Any]`:** Provee condiciones nominales seguras (22 °C, 11.5 km/h viento, factor 1.0) para el arranque.
* **`inicializar_semilla_sistema(centro, reloj) -> None`:** Registra a los 3 integrantes con los 3 roles y las 6 aeronaves al 100% en Olaya Herrera.
* **`extraer_parametros_fabrica(datos, total_flota) -> tuple`:** Normaliza y castea tipos de datos para dar de alta aeronaves en `FABRICA_DRONES`.

### 3.5 `src/ui/manejador_errores.py`

* **`formatear_excepcion_dominio(exc: Exception) -> dict[str, Any]`:** Traduce excepciones de dominio a JSON con la Regla de Negocio infringida (RF-02):
  * `BateriaInvalidaError` $\rightarrow$ Regla de Negocio #2 (Batería [0.0, 100.0]%).
  * `AltitudInvalidaError` $\rightarrow$ Regla de Negocio #3 (Techo UAEAC [0.0, 120.0] m).
  * `EstadoMotorInvalidoError` $\rightarrow$ Regla de Negocio #4 (Coherencia Motores vs Altitud).
  * `CoordenadaInvalidaError` $\rightarrow$ Regla de Negocio #5 (Polígono Valle de Aburrá).
  * `GeocodificacionError` $\rightarrow$ Regla de Negocio #5 (Geocodificación Aburrá).
  * `CategoriaDronInvalidoError` $\rightarrow$ Regla de Negocio #8 (Categorías Autorizadas).
  * `ActualizarEstadoDronError` $\rightarrow$ Regla de Negocio #9 (Control Operacional y Autonomía).

---

## 4. Ejecución y Verificación

### Arranque del Servidor Web
```bash
python -m src.ui
```
Por defecto el servidor se enlaza en `http://127.0.0.1:8000` y abre automáticamente el navegador web predeterminado.

### Ejecución de Pruebas Unitarias del Servidor
```bash
python -m unittest src.ui.test_ui_servidor -v
```
Verifica la entrega de recursos estáticos, ausencia total de emojis, transacciones de despacho, integración cinemática y control de tiempo real 1:1.

