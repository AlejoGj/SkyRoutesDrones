# Módulo de Centro de Control y Simulación Cinemática (`src/control/`)

Orquestación operativa, asignación de misiones por autonomía de circuito completo, auditoría formal de eventos, catálogo extensible de aeronaves, cinemática de vuelo discreta multi-fase y control de tiempo no bloqueante para el sistema SkyRoute en el Valle de Aburrá.

* **Responsables de Implementación:**
  * **Valery Arboleda Ardila:** Orquestador del Centro de Control, Registro de Usuarios, Pedidos, Auditoría y Despacho Polimórfico (HU-05, HU-06, HU-12).
  * **Alejandro García Jiménez:** Módulo de Funcionamiento: Reloj de Simulación Monotónico (`reloj.py`), Motor de Simulación Cinemática (`simulador.py`), Servicios y Pruebas Unitarias (HU-12).
* **Historias de Usuario Vinculadas:** HU-05, HU-06, HU-12
* **Requisitos Funcionales:** RF-05, RF-06, RF-07, RF-08, RF-09, RF-10

---

## 1. Propósito y Alcance

El paquete `src/control/` constituye el núcleo neurálgico y operativo de la plataforma SkyRoute. Sus responsabilidades comprenden:

1. **Torre de Control Centralizada (`SistemaCentroControl`):** Gestionar las flotas activas, usuarios registrados, solicitudes de servicio y bitácora histórica desde la base aeroportuaria central (Aeropuerto Olaya Herrera).
2. **Asignación Inteligente por Autonomía de Circuito:** Asignar aeronaves a pedidos verificando no solo la categoría, sino la viabilidad energética de completar el circuito total (**ida al destino + retorno a la base**), previniendo incidentes operacionales por agotamiento de batería.
3. **Despacho Polimórfico y Ciclo de Retorno:** Despachar misiones delegando la ejecución en el método polimórfico `dron.ejecutar_mision(pedido)` y enlazando automáticamente la orden de retorno a base.
4. **Fábrica Dinámica de Flota (`FABRICA_DRONES`):** Proveer un registro extensible desacoplado para instanciar subclases especializadas a partir de cadenas de categoría.
5. **Auditoría e Inmutabilidad de Bitácora (`LogOperacion`):** Generar registros estructurados con marcas temporales automáticas y formateo estructurado para fiscalización de aviación civil.
6. **Medición de Tiempo Monotónico No Bloqueante (`RelojSimulacion`):** Medir intervalos temporales reales ($\Delta t$) basados en hardware (`time.monotonic()`), inmunes a desvíos de sincronización horaria del sistema operativo.
7. **Simulación Cinemática y Física de Vuelo (`SimuladorVuelo`):** Integrar el avance físico discreto de la flota activa, interpolar coordenadas intermedias con cálculo geodésico, modular la velocidad por factores climáticos (viento y lluvia), descontar batería polimórficamente y gestionar aterrizajes de emergencia ante batería 0.0%.

---

## 2. Arquitectura y Colaboración de Componentes

```
+-----------------------------------------------------------------------------------+
|                            SistemaCentroControl                                   |
|                                                                                   |
|  - flota_drones: list[Dron]                  - coordenadas_base: (6.2196, -75.5867)|
|  - pedidos: list[Pedido]                     - geocodificador: IServicioGeocod... |
|  - usuarios: list[Usuario]                   - reloj: RelojSimulacion             |
|  - historial_logs: list[LogOperacion]        - simulador: SimuladorVuelo          |
+-----------------------------------------------------------------------------------+
        |                           |                           |
        | 1. Consulta reloj         | 2. Avanza fisica          | 3. Registra eventos
        v                           v                           v
+------------------+       +-------------------+       +--------------------+
| RelojSimulacion  |       |  SimuladorVuelo   |       |    LogOperacion    |
+------------------+       +-------------------+       +--------------------+
| - tiempo_inicio  |       | - calculador:     |       | - id_log: str      |
| - time.monotonic |       |   ICalculadorGeod |       | - fecha_hora: str  |
| - obtener_delta()|       | - avanzar_paso_   |       | - tipo_evento: str |
+------------------+       |   tiempo()        |       | - formatear_reg()  |
                           +-------------------+       +--------------------+
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
       +--------------------+               +--------------------+
       |  ICalculadorGeod   |               |     Dron (ABC)     |
       +--------------------+               +--------------------+
       | calcular_punto_    |               | actualizar_tele... |
       | intermedio()       |               | calcular_consumo.. |
       | calcular_haversine |               | telemetria.bateria |
       +--------------------+               +--------------------+
```

---

## 3. Catálogo de Componentes y Clases

### 3.1 `SistemaCentroControl` (`centro_control.py`)
Clase orquestadora principal que administra los recursos de vuelo, la interacción con servicios externos y el despacho de servicios.

* **Base Central de Operaciones:**
  * `LAT_BASE = 6.219603`
  * `LON_BASE = -75.586792`
  * `COORDENADAS_BASE = (6.219603, -75.586792)` (Aeropuerto Olaya Herrera de Medellín).
* **Inyección de Dependencias:** El constructor acepta instancias desacopladas de:
  * `geocodificador: IServicioGeocodificador` (por omisión: `ServicioGeocodificadorArcGIS`).
  * `reloj: RelojSimulacion`.
  * `servicio_clima: ServicioClimaAburra`.
  * `simulador: SimuladorVuelo`.
* **Caché Meteorológico en Memoria (`_obtener_clima_con_cache`):** Reduce la latencia de red en las consultas climáticas del Valle de Aburrá mediante un TTL de 60 segundos con fallback defensivo local en caso de cortes de servicio.
* **Geocodificación Automática en `registrar_pedido()`:** Si un pedido incluye una dirección textual (`direccion_destino`) sin coordenadas, el centro de control delega la resolución al geocodificador inyectado y genera los eventos de auditoría correspondientes (`GEOCODIFICACION_EXITOSA` o `PEDIDO_RECHAZADO_DIRECCION_INVALIDA`).
* **Algoritmo de Asignación con Autonomía de Circuito Completo (`asignar_dron_a_pedido`):**
  1. Identifica el pedido en estado `'PENDIENTE'` y consulta la clase requerida en `FABRICA_DRONES`.
  2. Filtra aeronaves disponibles con coincidencia de categoría.
  3. Descarta drones con batería agotada (`bateria <= 0.0%`).
  4. Calcula la distancia de ida al destino: $d_{\text{ida}} = \text{haversine}(\text{origen}, \text{destino})$.
  5. Calcula la distancia de regreso a la base: $d_{\text{retorno}} = \text{haversine}(\text{destino}, \text{base})$.
  6. Calcula el consumo energético requerido: $C_{\text{req}} = \text{dron.calcular\_consumo\_estimado}(d_{\text{ida}} + d_{\text{retorno}})$.
  7. Si $\text{bateria} < C_{\text{req}}$, rechaza la aeronave informativamente y evalúa la siguiente opción.
  8. Si cumple con la autonomía requerida, vincula el pedido (`'ASIGNADO'`), marca el dron (`en_mision = True`, `disponible = False`) y audita el evento `ASIGNACION_DRON`.
* **Despacho Polimórfico (`despachar_mision`):**
  1. Localiza el pedido en estado `'ASIGNADO'`.
  2. Cambia el estado del pedido a `'EN_TRANSITO'`.
  3. Si la aeronave carece de telemetría nominal previa, inicializa sus sensores en base a 0 m de altitud y 100% de batería.
  4. Invoca polimórficamente `dron.ejecutar_mision(pedido)` (que eleva la aeronave a 30 m de crucero).
  5. Actualiza el estado a `'COMPLETADO'`.
  6. Registra los detalles técnicos de la misión en `LogOperacion` (`MISION_COMPLETADA`).
  7. Dispara de forma obligatoria `gestionar_retorno_a_base(id_dron)`.
* **Ciclo de Simulación y Telemetría (`refrescar_datos_flota`):**
  1. Obtiene el delta de tiempo real mediante `reloj.obtener_delta()` (o un parámetro explícito).
  2. Consulta el factor climático del Valle de Aburrá (vía `ServicioClimaAburra`).
  3. Itera sobre todas las aeronaves en vuelo o retorno, delegando el avance físico en `simulador.avanzar_paso_tiempo()`.
  4. Genera log periódico `REFRESCO_TELEMETRIA`.
  5. Retorna un objeto `ResumenRefrescoFlota` con acceso a métricas cinemáticas completas y compatibilidad retroactiva con enteros (`int(resumen)`).

---

### 3.2 Fábrica Dinámica de Flota (`FABRICA_DRONES`)
Mecanismo extensible que desacopla la instanciación de aeronaves del orquestador central:

```python
FABRICA_DRONES: dict[str, type[Dron]] = {
    'INSPECCION_INFRAESTRUCTURA': DronInspeccion,
    'BUSQUEDA_RESCATE': DronRescate,
    'VIGILANCIA': DronVigilancia,
    'MAPEO_TOPOGRAFICO': DronMapeo,
    'ENTREGA_LIGERA': DronEntregaLigera,
    'CARGA_PESADA': DronCargaPesada,
}

def registrar_subclase_en_fabrica(categoria: str, clase_dron: type[Dron]) -> None:
    ...

def instanciar_dron_desde_fabrica(categoria: str, *args, **kwargs) -> Dron:
    ...
```

---

### 3.3 `RelojSimulacion` (`reloj.py`)
Controlador temporal no bloqueante para simulación discreta de telemetría y vuelo.

* **Inmunidad ante Cambios de Hora:** Utiliza el reloj monotónico del hardware (`time.monotonic()`), evitando saltos temporales si el sistema operativo ajusta su reloj por NTP o cambio horario.
* **Interfaz de Métodos:**
  * `obtener_tiempo_total_seg() -> float`: Retorna los segundos transcurridos desde la inicialización del sistema.
  * `obtener_delta() -> float`: Retorna el intervalo exacto ($\Delta t \ge 0.0\text{ s}$) transcurrido desde la última consulta y actualiza la marca para el próximo pulso.
  * `reiniciar() -> None`: Restablece el cronómetro a cero.

---

### 3.4 `SimuladorVuelo` (`simulador.py`)
Motor cinemático y físico para la propagación del vuelo en el espacio geográfico del Valle de Aburrá.

* **Simulación Multi-Fase Discreta con Propagación de Tiempo Remanente:**
  * Si una aeronave alcanza las coordenadas de entrega del pedido durante un paso temporal $\Delta t$ y aún queda tiempo sobrante, **inicia inmediatamente la fase de retorno a base dentro del mismo paso**.
  * Si el tiempo remanente cubre también el regreso, el dron aterriza en vertipuerto, apaga motores (`'STANDBY'`) y queda disponible en ese mismo pulso.
* **Modulación por Condiciones Meteorológicas:**
  * La velocidad de crucero nominal es modulada por el factor climático del SIATA/Open-Meteo:
    $$v_{\text{efectiva}} = v_{\text{promedio}} \times \max(0.1, \min(1.0, \text{factor\_clima}))$$
* **Consumo de Batería Polimórfico Continuo:**
  * En cada pulso se deduce la energía consumida: $C = \text{dron.calcular\_consumo\_estimado}(d_{\text{avanzada}})$.
* **Protocolo de Aterrizaje de Emergencia por Agotamiento (0.0%):**
  * Si la batería restante no cubre la etapa, el simulador calcula la distancia exacta alcanzable con la energía residual y utiliza `ICalculadorGeodesico.calcular_punto_intermedio()` para obtener la coordenada intermedia del descenso forzoso.
  * La aeronave apaga motores (`estado_motores = 'STANDBY'`), fija altitud en `0.0 m`, cancela la misión y genera una alerta crítica de auditoría (`ATERRIZAJE_EMERGENCIA_BATERIA`).

---

### 3.5 `LogOperacion` (`log_operacion.py`)
Bitácora de auditoría estandarizada para registro de eventos operacionales.

* **Validación Defensiva:** Control estricto de tipos (`TypeError`) y cadenas no vacías (`ValueError`) en `id_log` y `tipo_evento`.
* **Timestamp Automático:** Asigna automáticamente la fecha y hora actual en formato `YYYY-MM-DD HH:MM:SS` si no se provee un timestamp manual.
* **Visualización Estructurada:** Provee `formatear_registro()`, `__str__()` y `__repr__()` con delimitadores ASCII limpios para fácil lectura en consola y archivo de registros.

---

## 4. Principios de Diseño y Patrones Aplicados

| Principio / Patrón | Aplicación en el Módulo de Control |
|---|---|
| **Inversión de Dependencias (DIP)** | `SistemaCentroControl` y `SimuladorVuelo` dependen de interfaces abstractas (`IServicioGeocodificador`, `ICalculadorGeodesico`), permitiendo inyectar implementaciones alternativas o mocks para testing sin alterar la lógica de negocio. |
| **Responsabilidad Única (SRP)** | Desacoplamiento funcional: `SistemaCentroControl` orquesta pedidos y flota; `RelojSimulacion` contabiliza tiempo monotónico; `SimuladorVuelo` ejecuta física e interpolación; `LogOperacion` formatea auditoría. |
| **Abierto / Cerrado (OCP)** | La `FABRICA_DRONES` permite registrar dinámicamente nuevas subclases de drones mediante `registrar_subclase_en_fabrica` sin tener que modificar el archivo fuente del orquestador. |
| **Polimorfismo Dinámico** | El método `despachar_mision` invoca `dron.ejecutar_mision(pedido)` y el simulador calcula `dron.calcular_consumo_estimado(distancia)` sin inspeccionar tipos concretos de aeronave mediante estructuras `if/elif`. |

---

## 5. Guía de Uso

```python
from src.control.centro_control import SistemaCentroControl
from src.control.reloj import RelojSimulacion
from src.control.simulador import SimuladorVuelo
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido
from src.flota.dron_entrega_ligera import DronEntregaLigera

# 1. Instanciación del centro de control con inyección de servicios
centro = SistemaCentroControl()

# 2. Registro de aeronave en base Olaya Herrera
dron_entrega = DronEntregaLigera(
    id_dron="DRON-LOG-01",
    modelo_aeronave="AeroCourier-V3",
    velocidad_promedio_kmh=60.0,
    peso_maximo_paquete_kg=3.5,
    compartimento_refrigerado=True,
    mecanismo_suelta_rapida=True,
)
centro.agregar_dron(dron_entrega)

# 3. Registro de usuario y solicitud de pedido
cliente = Usuario(id_usuario="USR-01", nombre="Hospital San Vicente", rol="CLIENTE")
centro.registrar_usuario(cliente)

pedido = Pedido(
    id_pedido="PED-MED-01",
    usuario_solicitante=cliente,
    categoria_requerida="ENTREGA_LIGERA",
    coordenada_destino=(6.2625, -75.5681),  # Vertipuerto San Vicente
    peso_carga_kg=1.8,
)
centro.registrar_pedido(pedido)

# 4. Asignación con verificación de autonomía de circuito
if centro.asignar_dron_a_pedido("PED-MED-01"):
    # 5. Despacho polimórfico y despegue a 30 m de altitud
    centro.despachar_mision("PED-MED-01")

    # 6. Avance de la simulación cinemática (pulso de 15 segundos)
    resumen = centro.refrescar_datos_flota(delta_t=15.0)
    print(f"Paso completado: {resumen['delta_segundos']}s | Activos: {resumen['drones_activos']}")
```

---

## 6. Pruebas Unitarias y Verificación

El módulo cuenta con suite de pruebas unitarias automatizadas:
* `src/control/test_reloj.py`: Valida monotonicidad de hardware, medición de delta temporal y precisión no bloqueante.
* `src/control/test_simulador.py`: Valida simulación multi-fase, propagación de tiempo remanente, aterrizajes de emergencia ante batería 0.0%, interpolación geodésica de waypoints y modulación por viento/lluvia.

Para ejecutar la verificación:
```bash
python -m unittest discover -s src -p "test*.py"
```
