# Documento 06: Historial de Cambios y Reconciliación de Historias de Usuario

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Institución:** Universidad de Medellín (UDEM)  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Semestre:** 2026-2  
**Equipo de Desarrollo:** Alejandro García Jiménez, Juan Manuel Pava Higuita, Valery Arboleda Ardila  
**Propósito:** Registro técnico formal y trazabilidad de los cambios arquitectónicos implementados en el código de producción frente a la especificación académica original (Sprints 1 y 2).

---

## 1. Introducción y Marco de Gobernanza

Durante las fases de integración del sistema, acoplamiento con la interfaz gráfica web y pruebas con simuladores de vuelo físico en tiempo real, ciertas decisiones de diseño requerían evolucionar para cumplir con buenas prácticas de ingeniería de software (principios SOLID, estabilidad numérica IEEE 754, prevención de importaciones circulares y simulación física paso a paso).

Este documento compila de forma transparente el **Historial de Cambios** de cada Historia de Usuario (HU), detallando la discrepancia entre el estado original y el estado implementado, la justificación de ingeniería y los archivos afectados.

---

## 2. Índice de Historias de Usuario Reconciliadas

* **Sprint 1 (Núcleo Geodésico, Flota Base y Control Operativo):**
  * [HU-01: Validación de Datos de Telemetría y Excepciones de Dominio](#hu-01-validación-de-datos-de-telemetría-y-excepciones-de-dominio)
  * [HU-02: Motor de Cálculo Geodésico (Haversine) y Estimador de Tiempo (ETA)](#hu-02-motor-de-cálculo-geodésico-haversine-y-estimador-de-tiempo-eta)
  * [HU-03: Estructura del Dron y Representación Técnica en Consola](#hu-03-estructura-del-dron-y-representación-técnica-en-consola)
  * [HU-04: Protocolo de Retorno Obligatorio a Base y Cálculo de ETA](#hu-04-protocolo-de-retorno-obligatorio-a-base-y-cálculo-de-eta)
  * [HU-05: Registro de Usuarios, Solicitudes de Pedido y Logs de Auditoría](#hu-05-registro-de-usuarios-solicitudes-de-pedido-y-logs-de-auditoría)
  * [HU-06: Asignación Inteligente de Drones en el Sistema de Centro de Control](#hu-06-asignación-inteligente-de-drones-en-el-sistema-de-centro-de-control)
* **Sprint 2 (Herencia, Abstracción, Polimorfismo y Simulación):**
  * [HU-07: Transformación de Dron en Clase Abstracta Base (ABC)](#hu-07-transformación-de-dron-en-clase-abstracta-base-abc)
  * [HU-08: Subclases de Monitoreo y Cartografía (`DronVigilancia` y `DronMapeo`)](#hu-08-subclases-de-monitoreo-y-cartografía-dronvigilancia-y-dronmapeo)
  * [HU-09: Subclases de Transporte y Carga (`DronEntregaLigera` y `DronCargaPesada`)](#hu-09-subclases-de-transporte-y-carga-dronentregaligera-y-droncargapesada)
  * [HU-10: Polimorfismo en Consumo Energético y Fichas Técnicas Multilínea](#hu-10-polimorfismo-en-consumo-energético-y-fichas-técnicas-multilínea)
  * [HU-11: Subclases de Infraestructura y Rescate (`DronInspeccion` y `DronRescate`)](#hu-11-subclases-de-infraestructura-y-rescate-droninspeccion-y-dronrescate)
  * [HU-12: Orquestación Polimórfica, Despacho y Simulación en Centro de Control](#hu-12-orquestación-polimórfica-despacho-y-simulación-en-centro-de-control)

---

## 3. Reconciliación Detallada por Historia de Usuario

---

### HU-01: Validación de Datos de Telemetría y Excepciones de Dominio
* **Módulo:** [`src/telemetria/`](../src/telemetria/) y [`src/excepciones/`](../src/excepciones/)
* **Responsable:** Alejandro García Jiménez

#### 1. Estado Original vs. Estado Actual
* **Original:**
  - El Criterio de Aceptación 5 exigía que `TelemetriaDrone.validar_datos()` verificara si las coordenadas estaban dentro de los límites metropolitanos del Valle de Aburrá (`[5.9667, 6.5000]`, `[-75.7167, -75.3500]`), lanzando `CoordenadaInvalidaError`.
  - Método `validar_datos()` sin parámetros que leía únicamente el estado interno del objeto instanciado.
* **Actual:**
  1. **Desacoplamiento de la Geocerca (SRP):** `TelemetriaDrone.validar_datos()` valida rangos geométricos planetarios WGS84 (`[-90.0, 90.0]` y `[-180.0, 180.0]`). La validación estricta de la geocerca metropolitana del Valle de Aburrá se desacopló y trasladó a `CalculadorGeodesico.validar_coordenada()`.
  2. **Sobrecarga Flexible de Validación:** `validar_datos(self, id_dron=None, bateria=None, altitud=None, estado_motores=None, coordenadas=None)` admite parámetros opcionales con fallback a los atributos de la instancia. Esto permite a `actualizar_trama(...)` validar pre-condiciones de forma atómica antes de alterar las propiedades internas.
  3. **Desempaquetado Atómico de Coordenadas:** Al superar la validación, la tupla se desempaqueta automáticamente en `self.latitud` y `self.longitud` para facilitar consultas directas.
  4. **Representaciones Canónicas:** Sobrescritura de `__str__` y `__repr__` para visualización legible y concisa en consola y bitácora.

#### 2. Justificación Técnica
* **Principio de Responsabilidad Única (SRP):** La entidad `TelemetriaDrone` modela los sensores físicos y las tramas de hardware de la aeronave; acoplar el sensor a una jurisdicción geográfica metropolitana impedía la reutilización de aeronaves en otras áreas. La validación territorial pertenece al dominio de navegación y geodesia.
* **Atomicidad y Robustez en Actualización:** La sobrecarga de `validar_datos` permite validar una nueva trama completa o parcial antes de aplicar cambios sobre `self`, garantizando que un dato corrupto en vuelo no deje la telemetría en un estado inconsistente a medio actualizar.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Desacoplamiento de Geocerca y Validación Atómica en Telemetría):**
  * **Modificación en Criterio 5:** Se ajustó la responsabilidad de validación. `TelemetriaDrone.validar_datos()` valida rangos geométricos planetarios válidos `[-90.0, 90.0]` y `[-180.0, 180.0]`. La verificación estricta de la geocerca del Valle de Aburrá (`[5.9667, 6.5000]`, `[-75.7167, -75.3500]`) se delega al componente `CalculadorGeodesico.validar_coordenada()`.
  * **Firma Flexible de Validación:** `validar_datos()` acepta argumentos opcionales para prevalidar tramas antes de aplicar mutaciones en `actualizar_trama()`.
  * **Desempaquetado Automático:** Asignación directa de `latitud` y `longitud` al validar las coordenadas.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/telemetria/telemetria.py`](../src/telemetria/telemetria.py), [`src/telemetria/__init__.py`](../src/telemetria/__init__.py), [`src/geodesia/calculador.py`](../src/geodesia/calculador.py), [`src/telemetria/test_telemetria.py`](../src/telemetria/test_telemetria.py).
* **Dependencias:** [`src/excepciones/errores.py`](../src/excepciones/errores.py).
* **Documentación Técnica del Módulo:** [`src/telemetria/README.md`](../src/telemetria/README.md).

---

### HU-02: Motor de Cálculo Geodésico (Haversine) y Estimador de Tiempo (ETA)
* **Módulo:** `src/geodesia/`
* **Responsable:** Alejandro García Jiménez

#### 1. Estado Original vs. Estado Actual
* **Original:** Clase concreta `CalculadorGeodesico` con radio 6371.0 km, método Haversine y cálculo básico de ETA.
* **Actual:**
  1. Abstracción formal mediante el protocolo `ICalculadorGeodesico(Protocol)`.
  2. `calcular_haversine()` valida obligatoriamente que origen y destino pertenezcan al Valle de Aburrá antes de calcular distancias.
  3. Enclavamiento numérico de seguridad: `a = max(0.0, min(1.0, a))`.
  4. Nuevo método de interpolación geodésica lineal: `calcular_punto_intermedio(origen, destino, fraccion)`.
  5. Protección en ETA: retorna `0.0` min ante distancias o velocidades `<= 0.0`.

#### 2. Justificación Técnica
* **Estabilidad Numérica IEEE 754:** En puntos coincidentes o con distancias infinitesimales, el redondeo de punto flotante puede provocar $a > 1.0$, lo que dispara una excepción matemática de dominio en `math.sqrt(1 - a)`. El enclavamiento evita caídas del sistema.
* **Requerimiento del Simulador de Vuelo:** El cálculo dinámico paso a paso y la determinación del punto geográfico exacto de aterrizaje forzoso ante agotamiento de batería exigían interpolar coordenadas intermedias progresivas.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Ampliación del Motor Geodésico y Blindaje Numérico):**
  * **Abstracción Formal:** Se implementó `ICalculadorGeodesico(Protocol)` definiendo los límites de operación metropolitana como constantes de clase (`LAT_MIN_ABURRA`, `LAT_MAX_ABURRA`, `LON_MIN_ABURRA`, `LON_MAX_ABURRA`).
  * **Prevalidación en Haversine:** `calcular_haversine()` ahora valida previamente que ambos puntos pertenezcan al Valle de Aburrá, lanzando `CoordenadaInvalidaError` si alguno está fuera de zona.
  * **Enclavamiento Numérico:** Se incorporó `a = max(0.0, min(1.0, a))` para evitar errores de dominio matemático en `math.sqrt(1 - a)` causados por imprecisión de punto flotante en distancias nulas o submilimétricas.
  * **Nuevo Método `calcular_punto_intermedio()`:** Se añadió soporte para interpolación geográfica lineal `(origen, destino, fraccion) -> (lat, lon)` con redondeo a 6 decimales y revalidación de geocerca, requerido por el simulador de vuelo para calcular waypoints y coordenadas de aterrizaje de emergencia.
  * **Manejo Defensivo en ETA:** `calcular_tiempo_vuelo_min()` retorna `0.0` ante distancias o velocidades `<= 0.0`.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/geodesia/calculador.py`](../src/geodesia/calculador.py), [`src/control/simulador.py`](../src/control/simulador.py), [`src/geodesia/test_calculador.py`](../src/geodesia/test_calculador.py).

---

### HU-03: Estructura del Dron y Representación Técnica en Consola
* **Módulo:** `src/flota/`
* **Responsable:** Juan Manuel Pava Higuita (Sprint 1) / Alejandro García Jiménez (Sprint 2)

#### 1. Estado Original vs. Estado Actual
* **Original:** Entidad `Dron` concreta con atributos públicos sin validación inicial en constructor. `actualizar_telemetria()` solo admitía un objeto completo `TelemetriaDrone`.
* **Actual:**
  1. `Dron` evolucionó a clase base abstracta (`ABC`).
  2. Implementación de `__post_init__()` manual para validaciones estrictas de tipos (rechazando booleanos en campos numéricos y strings vacíos).
  3. `actualizar_telemetria` admite firma híbrida (objeto o parámetros atómicos desglosados), reutilizando la trama existente in-place y acumulando odómetro si hubo desplazamiento.
  4. Incorporación del historial inmutable congelado: `historial_telemetria -> tuple[str, ...]`.
  5. Implementación de `actualizar_estado_disponibilidad(disponible)` con excepciones `ActualizarEstadoDronError` y `EstadoDronDuplicadoError`.

#### 2. Justificación Técnica
* **Integridad de Datos:** Evitar que valores erróneos en tiempo de ejecución corrompan el odómetro o el estado del motor.
* **Inmutabilidad:** Garantizar que la bitácora técnica de telemetría de la aeronave no pueda ser borrada ni truncada desde el exterior.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Validación Defensiva, Sobrecarga de Telemetría e Historial Inmutable):**
  * **Constructor Seguro:** Se implementó `__post_init__()` manual para validar que `id_dron` y `modelo_aeronave` no sean vacíos y que `velocidad_promedio_kmh` y `kilometraje_total_km` sean números estrictamente positivos (rechazando booleanos).
  * **Firma Híbrida en `actualizar_telemetria`:** Soporta recibir una instancia de `TelemetriaDrone` o los parámetros desglosados (`bateria_o_telemetria`, `altitud`, `estado_motores`, `coordenadas`), reutilizando el objeto interno vía `actualizar_trama()` y acumulando odómetro si hubo desplazamiento.
  * **Bitácora Inmutable:** Se añadió la propiedad `historial_telemetria -> tuple[str, ...]`, impidiendo la alteración externa del registro cronológico de estados de la aeronave.
  * **Control de Disponibilidad:** Se añadió `actualizar_estado_disponibilidad(disponible)` con las excepciones `ActualizarEstadoDronError` y `EstadoDronDuplicadoError`.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/flota/dron.py`](../src/flota/dron.py), [`src/excepciones/errores.py`](../src/excepciones/errores.py).

---

### HU-04: Protocolo de Retorno Obligatorio a Base y Cálculo de ETA
* **Módulo:** `src/flota/`
* **Responsable:** Juan Manuel Pava Higuita

#### 1. Estado Original vs. Estado Actual
* **Original:** `iniciar_retorno()` requería coordenadas explícitas; `finalizar_retorno()` se ejecutaba sin validar proximidad física.
* **Actual:**
  1. `iniciar_retorno_base()` asigna por defecto las coordenadas de la Base Central Olaya Herrera `(6.219603, -75.586792)` si el parámetro es nulo.
  2. `finalizar_retorno_en_base()` valida mediante Haversine que la aeronave esté a una distancia métrica menor o igual a 50 metros ($\le 0.05\text{ km}$) de la plataforma. Si está en ruta, aborta el aterrizaje con `ActualizarEstadoDronError`.
  3. Creación de `finalizar_mision_en_destino()` para gestionar el arribo al cliente con tolerancia de 50 metros, marcar el pedido como completado e iniciar automáticamente el retorno a base.

#### 2. Justificación Técnica
* **Seguridad Operacional:** Impedir que una aeronave en vuelo activo sea marcada artificialmente como "disponible en base" por un operador mientras se encuentra en el aire.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Tolerancia de Aterrizaje y Protocolo de Finalización en Destino):**
  * **Base por Defecto:** `iniciar_retorno_base()` adopta por defecto las coordenadas de la Base Olaya Herrera `(6.219603, -75.586792)` si no se suministra un destino explícito.
  * **Tolerancia de Vertipuerto (50 m):** `finalizar_retorno_en_base()` valida mediante Haversine que la aeronave esté a una distancia `<= 0.05 km` de la plataforma antes de apagar motores y declararla disponible.
  * **Nuevo Método `finalizar_mision_en_destino()`:** Gestiona el arribo al cliente con tolerancia de `<= 0.05 km`, cambia el pedido a `'COMPLETADO'`, archiva el pedido y activa de inmediato el retorno a base.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/flota/dron.py`](../src/flota/dron.py).

---

### HU-05: Registro de Usuarios, Solicitudes de Pedido y Logs de Auditoría
* **Módulo:** [`src/usuarios/`](../src/usuarios/), [`src/pedidos/`](../src/pedidos/), [`src/control/log_operacion.py`](../src/control/log_operacion.py)
* **Responsable Original:** Valery Arboleda Ardila (Sprint 1) / Extensión e Integración: Alejandro García Jiménez

#### 1. Estado Original vs. Estado Actual
* **Original:**
  - La historia requería que `Pedido` recibiera obligatoriamente una tupla de coordenadas de destino `coordenada_destino: tuple[float, float]`.
  - Solo se contemplaba el atributo `categoria_requerida`.
  - Los pedidos nacían en estado `'PENDIENTE'` con métodos simples `actualizar_estado(nuevo_estado)` y `vincular_dron(dron)`.
  - No se preveía soporte para direcciones urbanas alfanuméricas, alias de compatibilidad, validación anti-booleanos ni representaciones formales multilínea.
* **Actual:**
  1. **Destino Geográfico Dual y Geocodificación Desacoplada (`Pedido`):** El constructor admite indistintamente coordenadas geodésicas directas (`coordenada_destino: tuple | None = None`) o una dirección urbana alfanumérica (`direccion_destino: str | None = None`). Si no se suministra al menos una de las dos opciones, dispara `ValueError`. Si se proporcionan coordenadas, valida tipo tupla, longitud exacta de 2 elementos y valores numéricos reales `(int, float)`. Si se proporciona dirección textual, las coordenadas nacen en `None` y son resueltas de forma diferida en `SistemaCentroControl.registrar_pedido()`.
  2. **Alias de Interoperabilidad `self.categoria` (`Pedido`):** Se introduce `self.categoria = self.categoria_requerida` para compatibilidad transparente con algoritmos de asignación, contratos de la flota y suites de pruebas unitarias.
  3. **Blindaje Defensivo Anti-Booleanos en Carga (`Pedido`):** Debido a que en Python `bool` es subclase de `int` (`isinstance(True, int) == True`), se incorporó la validación explícita `if isinstance(peso_carga_kg, bool) ... raise TypeError`, previniendo que flags lógicas sean admitidas como masa. Además, se restringe `peso_carga_kg >= 0.0`.
  4. **Ciclo de Vida de 5 Estados Operativos (`Pedido`):** La constante de clase `estados_permitidos` se amplía formalmente a `['PENDIENTE', 'ASIGNADO', 'EN_TRANSITO', 'COMPLETADO', 'CANCELADO']`, normalizando entradas con `.strip().upper()`.
  5. **Representaciones Canónicas (`Pedido`):** Sobrescritura de `__str__` y `__repr__` indicando la aeronave asignada y si la coordenada está fijada o pendiente de geocodificación.
  6. **Auditoría e Inmutabilidad (`LogOperacion`):** Generación automática de timestamps con `datetime.now()` si `fecha_hora` es omitido, enclavamiento contra cadenas vacías o tipos inválidos, valores predeterminados seguros (`"No aplica"`, `"No hay detalles adicionales"`), formateo multilínea y métodos `__str__` y `__repr__`.
  7. **Gestión de Identidad (`Usuario`):** Constante de clase `ROLES_PERMITIDOS`, método de verificación `validar_usuario()` y validaciones de tipos estrictas.

#### 2. Justificación Técnica
* **Interoperabilidad Logística y UX:** En el entorno urbano del Valle de Aburrá, los usuarios solicitan servicios ingresando direcciones de calle/carrera, no coordenadas geodésicas. Habilitar `direccion_destino` desacopla la creación del pedido de los servicios cartográficos externos (ArcGIS / OSM / Catálogo Local).
* **Integridad Numérica en Carga Útil:** La masa del paquete determina si aeronaves como `DronEntregaLigera` rechazan el despacho por sobrepeso. Filtrar tipos booleanos previene inconsistencias en los cálculos de sustentación y consumo energético.
* **Sincronización con la Simulación Cinemática:** La ampliación a 5 estados formales (`PENDIENTE` $\to$ `ASIGNADO` $\to$ `EN_TRANSITO` $\to$ `COMPLETADO` / `CANCELADO`) es obligatoria para que el `SimuladorVuelo` y la interfaz gráfica web puedan reflejar el estado real del vuelo en tiempo real.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Destino Dual en Pedidos, Blindaje Anti-Booleanos y Ciclo de 5 Estados):**
  * **Destino Geográfico Dual:** `Pedido.__init__()` permite registrar pedidos mediante tupla directa de coordenadas `coordenada_destino` o mediante dirección textual `direccion_destino`, exigiendo al menos uno de los dos campos y validando tipos estrictos.
  * **Geocodificación Diferida:** Los pedidos con dirección textual nacen con `coordenada_destino = None` y son geocodificados automáticamente al ingresar a la torre de control.
  * **Alias `categoria`:** Se incorporó `self.categoria` como espejo de `self.categoria_requerida` para interoperabilidad con los contratos de la flota y el centro de control.
  * **Ciclo de Estados Ampliado:** Estandarización de 5 estados operativos (`'PENDIENTE'`, `'ASIGNADO'`, `'EN_TRANSITO'`, `'COMPLETADO'`, `'CANCELADO'`).
  * **Filtro Anti-Booleanos en Carga:** Validación explícita de `isinstance(peso_carga_kg, bool)` para evitar que valores de bandera lógica sean admitidos como masa en kilogramos.
  * **Generación Automática de Timestamps:** `LogOperacion` genera automáticamente la marca temporal con `datetime.now()` cuando `fecha_hora` es omitido, estandarizando el formato `YYYY-MM-DD HH:MM:SS`.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/pedidos/pedido.py`](../src/pedidos/pedido.py), [`src/pedidos/__init__.py`](../src/pedidos/__init__.py), [`src/usuarios/usuario.py`](../src/usuarios/usuario.py), [`src/control/log_operacion.py`](../src/control/log_operacion.py), [`src/control/centro_control.py`](../src/control/centro_control.py).
* **Dependencias:** Módulo estándar `datetime`, [`src/servicios/geocodificador.py`](../src/servicios/geocodificador.py).
* **Documentación Técnica del Módulo:** [`src/pedidos/README.md`](../src/pedidos/README.md), [`src/usuarios/README.md`](../src/usuarios/README.md).

---

### HU-06: Asignación Inteligente de Drones en el Sistema de Centro de Control
* **Módulo:** `src/control/centro_control.py`
* **Responsable:** Valery Arboleda Ardila (Sprint 1) / Alejandro García Jiménez (Motor y Servicios)

#### 1. Estado Original vs. Estado Actual
* **Original:**
  - Base central en Medellín con coordenadas arbitrarias `(6.2089, -75.5684)` (El Poblado).
  - Algoritmo de asignación (`asignar_dron_a_pedido`) básico por coincidencia de categoría disponible, sin validar batería ni viabilidad de regreso.
  - Centro de control acoplado directamente sin inyección de dependencias.
* **Actual:**
  1. Base central establecida formalmente en el Aeropuerto Olaya Herrera: `LAT_BASE = 6.219603`, `LON_BASE = -75.586792` (`COORDENADAS_BASE`).
  2. Inyección de dependencias en `SistemaCentroControl.__init__`: geocodificador (`IServicioGeocodificador`), reloj monotónico (`RelojSimulacion`), servicio climático (`ServicioClimaAburra`) y simulador físico (`SimuladorVuelo`).
  3. Geocodificación transparente en `registrar_pedido()`: Si el pedido posee dirección textual pero carece de coordenadas, se invoca al servicio geocodificador inyectado y se generan logs de auditoría de resolución geográfica (`GEOCODIFICACION_EXITOSA` o `PEDIDO_RECHAZADO_DIRECCION_INVALIDA`).
  4. **Asignación con Autonomía de Circuito Completo (Ida + Retorno):**
     - Descarte inmediato de aeronaves con batería `0.0%`.
     - Cálculo de la distancia de ida (base/posición actual a destino) y de la distancia de retorno (destino a base central).
     - Validación del consumo polimórfico del trayecto total: `dron.calcular_consumo_estimado(distancia_ida + distancia_retorno)`.
     - Si la batería es insuficiente para el circuito completo, el dron es rechazado de forma no bloqueante y el orquestador continúa evaluando otras aeronaves disponibles.

#### 2. Justificación Técnica
* **Seguridad Aeronáutica:** En aeronaves no tripuladas es inadmisible despachar una misión que no cuente con reserva de energía suficiente para retornar a la base. La validación del circuito completo evita pérdidas de aeronaves en áreas urbanas.
* **Inversión de Dependencias (DIP):** La inyección de servicios externos desacopla la lógica de control del hardware o APIs de terceros, garantizando pruebas unitarias deterministas y mockeables.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Base Operativa Olaya Herrera, Inyección de Dependencias y Validación de Autonomía de Circuito):**
  * **Relocalización de Base:** Coordenadas fijadas en el Aeropuerto Olaya Herrera `(6.219603, -75.586792)` como centro de operaciones y vertipuerto principal.
  * **Inyección de Dependencias:** El constructor de `SistemaCentroControl` recibe instancias desacopladas de geocodificador, reloj, servicio de clima y simulador cinemático.
  * **Geocodificación Automática:** `registrar_pedido()` resuelve direcciones textuales en coordenadas geodésicas mediante el servicio geocodificador inyectado.
  * **Validación de Autonomía de Circuito Completo:** `asignar_dron_a_pedido()` calcula la distancia y consumo energético tanto de ida como de retorno a la base antes de confirmar la asignación.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/control/centro_control.py`](../src/control/centro_control.py), [`src/control/log_operacion.py`](../src/control/log_operacion.py).
* **Dependencias:** [`src/servicios/geocodificador.py`](../src/servicios/geocodificador.py), [`src/servicios/clima.py`](../src/servicios/clima.py).
* **Documentación Técnica del Módulo:** [`src/control/README.md`](../src/control/README.md), [`src/servicios/README.md`](../src/servicios/README.md).

---

### HU-07: Transformación de Dron en Clase Abstracta Base (ABC)
* **Módulo:** `src/flota/`
* **Responsable:** Alejandro García Jiménez

#### 1. Estado Original vs. Estado Actual
* **Original:** `Dron` como clase abstracta pura con métodos abstractos vacíos.
* **Actual:** `Dron.ejecutar_mision` proporciona una implementación base concreta funcional (`super().ejecutar_mision(pedido)`) que:
  - Valida disponibilidad y batería no nula.
  - Calcula la distancia de ida y de retorno a la base.
  - Verifica autonomía pre-vuelo para el circuito completo (**ida + vuelta**).
  - Eleva el dron a 30 m con motores `EN_VUELO` y pasa el pedido a `EN_TRANSITO`.
  - Preserva las coordenadas iniciales sin teletransportación.

#### 2. Justificación Técnica
* **Eliminación de Código Duplicado:** Las validaciones de despegue y autonomía son comunes a todas las aeronaves. Reutilizarlas mediante `super()` evita que cada subclase reescriba la lógica aeronáutica básica.
* **Modelo No Instantáneo:** La simulación requería separar el "despegue" (inicio de vuelo) de la "entrega" (fin de vuelo).

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Lógica Base Concreta en Método Abstracto `ejecutar_mision`):**
  * **Implementación Reutilizable:** Aunque `ejecutar_mision` está decorado con `@abstractmethod`, `Dron` proporciona una implementación base invocada mediante `super().ejecutar_mision(pedido)` para que las subclases no dupliquen validaciones comunes.
  * **Validación de Autonomía de Circuito Completo:** Valida que `bateria >= calcular_consumo_estimado(distancia_ida + distancia_retorno)`. Si la batería es insuficiente para el viaje completo, el despegue se aborta con `ActualizarEstadoDronError`.
  * **Transición de Despegue sin Teletransportación:** Configura altitud a 30.0 m, motores a `'EN_VUELO'`, bandera `en_mision = True` y pedido en `'EN_TRANSITO'`, conservando las coordenadas de origen para integración paso a paso.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/flota/dron.py`](../src/flota/dron.py), todas las subclases en `src/flota/`.

---

### HU-08: Subclases de Monitoreo y Cartografía (`DronVigilancia` y `DronMapeo`)
* **Módulo:** `src/flota/`
* **Responsable Original en Especificación:** Alejandro García Jiménez
* **Responsables de Implementación y Mantenimiento:** Juan Manuel Pava Higuita y Valery Arboleda Ardila

#### 1. Estado Original vs. Estado Actual
* **Original:**
  - Asignada a Alejandro García Jiménez dentro del reparto equitativo del Sprint 2 (2 subclases por desarrollador).
  - Clases concebidas con atributos directos públicos y sin tasa de consumo energético especificada en la historia de usuario.
* **Actual:**
  - **Reasignación de Responsabilidad:** La construcción de `DronVigilancia` y `DronMapeo` fue asumida y culminada conjuntamente por **Juan Manuel Pava Higuita** y **Valery Arboleda Ardila**.
  - **Reasignación Estratégica de Alejandro García Jiménez:** Pasó a asumir la arquitectura y desarrollo del **Módulo de Funcionamiento y Servicios**:
    - Motor de tiempo y reloj de simulación (`src/control/reloj.py` - `RelojSimulacion`).
    - Simulador cinemático de vuelo multi-etapa (`src/control/simulador.py` - `SimuladorVuelo`).
    - Capa de servicios e integración externa (`src/servicios/`: `ServicioClima` con caché de 30s, `ServicioGeocodificadorLocal` con catálogo metropolitano y `ServicioGeocodificadorArcGIS`).
  - Encapsulamiento defensivo con `@property` y setters para resolución de cámara, visión nocturna, sensor LiDAR y memoria SSD.
  - Constructor adaptable que admite variación en el orden de argumentos posicionales.
  - Tasas métricas fijadas: `1.3% / km` (Vigilancia) y `1.4% / km` (Mapeo).
  - Implementación de `predecir_viabilidad_mision(distancia_km)`.

#### 2. Justificación Técnica
* **Equilibrio de Carga Arquitectónica:** El desarrollo del motor de simulación temporal continua (`SimuladorVuelo`), la integración del reloj del sistema y el subsistema de geocodificación espacial en `src/servicios/` representaban una carga de ingeniería de infraestructura crítica. Para no desbalancear el esfuerzo del equipo ni comprometer la calidad del simulador, las dos subclases sensoriales (`DronVigilancia` y `DronMapeo`) se transfirieron a Juan Manuel y Valery, liberando a Alejandro para consolidar el núcleo de funcionamiento dinámico.
* **Integridad de Sensores:** El encapsulamiento en las subclases previene estados corruptos en hardware simulado (cámaras de 0 MP, discos negativos o frecuencias nulas).

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Reasignación de Responsables y Módulo de Funcionamiento):**
  * **Cambio de Responsable:** La implementación de `DronVigilancia` y `DronMapeo` fue transferida a Juan Manuel Pava Higuita y Valery Arboleda Ardila. Alejandro García Jiménez asumió la responsabilidad técnica del módulo de funcionamiento (`RelojSimulacion`, `SimuladorVuelo`) y la infraestructura de servicios (`src/servicios/`).
  * **Tasas de Consumo:** Se definieron las tasas métricas: `1.3% / km` para `DronVigilancia` y `1.4% / km` para `DronMapeo`.
  * **Constructor Flexible:** Se implementó detección automática del orden de parámetros posicionales en constructores para admitir scripts y pruebas heredadas sin romper firmas.
  * **Predicción de Autonomía:** Se incorporó `predecir_viabilidad_mision(distancia_km)` retornando diagnósticos de viabilidad pre-despegue.
```

#### 4. Impacto Técnico
* **Archivos Afectados:**
  - [`src/flota/dron_vigilancia.py`](../src/flota/dron_vigilancia.py), [`src/flota/dron_mapeo.py`](../src/flota/dron_mapeo.py) (Asumidos por Juan Manuel y Valery).
  - [`src/control/reloj.py`](../src/control/reloj.py), [`src/control/simulador.py`](../src/control/simulador.py) (Asumidos por Alejandro).
  - [`src/servicios/clima.py`](../src/servicios/clima.py), [`src/servicios/geocodificador.py`](../src/servicios/geocodificador.py) (Asumidos por Alejandro).

---

### HU-09: Subclases de Transporte y Carga (`DronEntregaLigera` y `DronCargaPesada`)
* **Módulo:** `src/flota/`
* **Responsable:** Juan Manuel Pava Higuita

#### 1. Estado Original vs. Estado Actual
* **Original:** Reglas de carga básicas sin límite programático rígido en despacho.
* **Actual:**
  - `DronEntregaLigera.ejecutar_mision(pedido)` verifica que `pedido.peso_carga_kg <= self.capacidad_carga_kg`. Si excede la capacidad de la tolva (default 5.0 kg), el despegue se deniega lanzando `ActualizarEstadoDronError`.
  - `DronCargaPesada` restringe la cantidad de rotores a números enteros pares entre 4 y 16, y potencia de tracción estrictamente positiva.

#### 2. Justificación Técnica
* Simular con precisión los límites de masa física de las aeronaves y evitar la sobrecarga de rotores en entregas logísticas.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Validación de Sobrecarga y Restricciones Industriales):**
  * **Defensa de Carga:** `DronEntregaLigera.ejecutar_mision()` verifica que `pedido.peso_carga_kg <= self.capacidad_carga_kg`, rechazando el despegue con `ActualizarEstadoDronError` ante sobrecargas.
  * **Validación de Rotores Industriales:** `DronCargaPesada` restringe `numero_rotores` a enteros pares entre 4 y 16, y potencia de remolque a valores mayores a 0 W.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/flota/dron_entrega_ligera.py`](../src/flota/dron_entrega_ligera.py), [`src/flota/dron_carga_pesada.py`](../src/flota/dron_carga_pesada.py).

---

### HU-10: Polimorfismo en Consumo Energético y Fichas Técnicas Multilínea
* **Módulo:** `src/flota/`
* **Responsable:** Juan Manuel Pava Higuita

#### 1. Estado Original vs. Estado Actual
* **Original:** Fórmulas para dos tipos de dron y salida básica en `__str__`.
* **Actual:**
  - Matriz homogénea de consumo polimórfico extendida a las 6 subclases de la flota con validación de distancia positiva (`distancia <= 0` retorna `0.0`).
  - Representación técnica `__str__` implementada en cascada: recorta la línea de cierre de `super().__str__()` y concatena las especificaciones y aditamentos exclusivos de cada subclase.

#### 2. Justificación Técnica
* Brindar transparencia diagnóstica completa en terminal y garantizar que el consumo de batería responda directamente al modelo aerodinámico de cada aeronave.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Matriz Homogénea de Consumo y Fichas Especializadas):**
  * **Protección Numérica:** Las fórmulas de consumo validan `distancia_km <= 0`, retornando `0.0%` en lugar de valores negativos o indefinidos.
  * **Fichas Técnicas Multilínea:** Sobrescritura de `__str__` en las 6 subclases reutilizando la base de `Dron` y anexando ordenadamente los atributos técnicos específicos.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** Todas las clases de `src/flota/`.

---

### HU-11: Subclases de Infraestructura y Rescate (`DronInspeccion` y `DronRescate`)
* **Módulo:** `src/flota/`
* **Responsable:** Valery Arboleda Ardila

#### 1. Estado Original vs. Estado Actual
* **Original:** Atributo de potencia de altavoz definido en camelCase (`potenciaAltavozDb`).
* **Actual:**
  - `DronRescate` soporta tanto el estándar Python snake_case (`potencia_altavoz_db`) como el alias camelCase (`potenciaAltavozDb`), garantizando interoperabilidad sin inconsistencias de estilo.
  - Tasas de consumo fijadas en `1.5% / km` (Inspección) y `2.0% / km` (Rescate).
  - Simulación de barrido térmico, entrega de kit de auxilios y vuelo estacionario por ultrasonido en `ejecutar_mision`.

#### 2. Justificación Técnica
* Cumplir con las convenciones de código PEP 8 sin romper compatibilidad con pruebas o enunciados académicos que invoquen el atributo en camelCase.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Drones de Emergencia y Compatibilidad de Nomenclatura):**
  * **Soporte de Nomenclatura Dual:** `DronRescate` define `potencia_altavoz_db` y el alias `potenciaAltavozDb` para interoperar con la especificación de la historia de usuario sin inconsistencias de estilo.
  * **Tasas Operacionales:** Fijadas en `1.5% / km` para `DronInspeccion` y `2.0% / km` para `DronRescate`.
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/flota/dron_inspeccion.py`](../src/flota/dron_inspeccion.py), [`src/flota/dron_rescate.py`](../src/flota/dron_rescate.py).

---

### HU-12: Orquestación Polimórfica, Despacho y Simulación en Centro de Control
* **Módulo:** `src/control/centro_control.py`, `src/control/reloj.py`, `src/control/simulador.py`
* **Responsable:** Valery Arboleda Ardila (Sprint 2 - HU-12) / Alejandro García Jiménez (Motor de Reloj y Simulación Cinemática)

#### 1. Estado Original vs. Estado Actual
* **Original:**
  - `despachar_mision()` pasaba de forma instantánea de `'EN_TRANSITO'` a `'COMPLETADO'`.
  - Catálogo de fábrica estático `FABRICA_DRONES` solo con referencias hardcodeadas.
  - Sin integración con simulación temporal ni cinemática de vuelo continua.
* **Actual:**
  1. **Fábrica Dinámica y Extensible:** Registro dinámico `FABRICA_DRONES` con funciones de extensión en tiempo de ejecución (`registrar_subclase_en_fabrica`, `instanciar_dron_desde_fabrica`) e importaciones tolerantes a fallos para facilitar el desarrollo distribuido.
  2. **Protocolo de Despacho sin Teletransportación:**
     - Si la aeronave carece de telemetría, se le inicializa telemetría nominal de despegue en la base `(LAT_BASE, LON_BASE, altitud=0.0, bateria=100.0, motores='APAGADOS')`.
     - `despachar_mision()` ejecuta polimórficamente `dron.ejecutar_mision(pedido)`, elevando la aeronave a 30 m de altitud con motores `'EN_VUELO'`.
     - Genera log de auditoría con la información técnica especializada de la misión e invoca automáticamente `gestionar_retorno_a_base()`.
  3. **Motor de Integración Cinemática (`refrescar_datos_flota`):**
     - Desacoplamiento de `RelojSimulacion`: Mide delta temporal mediante `time.monotonic()` (reloj monotónico de hardware), inmune a cambios del reloj del sistema operativo.
     - Simulación multi-fase discreta con `SimuladorVuelo`: Soporta propagación de tiempo remanente en el mismo ciclo temporal (si el dron llega al destino y aún queda tiempo del delta, inicia el retorno a base en ese mismo instante).
     - Modulación de velocidad por clima: Aplica el factor climático de viento y lluvia (`ServicioClimaAburra` con caché TTL de 60s), enclavado de forma segura en `[0.1, 1.0]`.
     - Deducción polimórfica continua de batería en cada pulso de vuelo.
     - **Protocolo de Emergencia por Batería Agotada (0.0%):** Si la batería llega a 0% durante el vuelo, el simulador calcula el punto geográfico exacto de agotamiento vía `calcular_punto_intermedio`, fuerza altitud a `0.0 m`, motores a `'STANDBY'`, desactiva el dron y registra una alerta crítica de auditoría (`ATERRIZAJE_EMERGENCIA_BATERIA`).
     - **Estructura de Retorno `ResumenRefrescoFlota(dict)`:** Proporciona un diccionario enriquecido con telemetría de toda la flota activa, manteniendo total compatibilidad retroactiva con llamadas o aserciones de tests que esperen un entero (`__int__`, `__index__`).

#### 2. Justificación Técnica
* **Abstracción Formal y Principio Abierto/Cerrado (OCP):** El centro de control despacha cualquier aeronave sin consultar su tipo concreto mediante `if/elif`. La fábrica dinámica permite añadir nuevas aeronaves sin modificar `centro_control.py`.
* **Fidelidad Física y Cinemática:** Descartar la teletransportación instantánea permite que la interfaz gráfica web y los paneles de control observen el avance gradual de la flota en el Valle de Aburrá, reflejando el impacto de vientos, lluvia y autonomía energética real.

#### 3. Registro para Historial de Cambios de la HU
```markdown
##### Historial de Cambios y Ajustes de Arquitectura:
* **2026-10-27 (Despacho Polimórfico, Fábrica Extensible y Motor de Simulación Cinemática):**
  * **Fábrica Dinámica:** Implementación de `FABRICA_DRONES` con `registrar_subclase_en_fabrica()` e `instanciar_dron_desde_fabrica()` para desacoplamiento total en la creación de aeronaves.
  * **Despacho Polimórfico:** `despachar_mision()` inicializa telemetría nominal si es requerida, invoca `dron.ejecutar_mision(pedido)` elevando la aeronave a 30 m de altitud, audita los resultados y enlaza el retorno automático a la base.
  * **Motor de Simulación Cinemática (`refrescar_datos_flota`):** Integración no bloqueante con `RelojSimulacion` (`time.monotonic()`), modulación por factor climático del Valle de Aburrá (con caché TTL de 60s) y avance cinemático multi-fase en `SimuladorVuelo`.
  * **Protocolo de Aterrizaje de Emergencia:** Aterrizaje forzoso en coordenadas interpoladas ante batería 0.0% con registro en bitácora (`ATERRIZAJE_EMERGENCIA_BATERIA`).
  * **Objeto `ResumenRefrescoFlota`:** Retorno estructurado que encapsula telemetría y preserva compatibilidad con enteros (`__int__`).
```

#### 4. Impacto Técnico
* **Archivos Afectados:** [`src/control/centro_control.py`](../src/control/centro_control.py), [`src/control/reloj.py`](../src/control/reloj.py), [`src/control/simulador.py`](../src/control/simulador.py), [`src/control/test_reloj.py`](../src/control/test_reloj.py), [`src/control/test_simulador.py`](../src/control/test_simulador.py).
* **Dependencias:** [`src/servicios/clima.py`](../src/servicios/clima.py), [`src/geodesia/calculador.py`](../src/geodesia/calculador.py).
* **Documentación Técnica del Módulo:** [`src/control/README.md`](../src/control/README.md), [`src/servicios/README.md`](../src/servicios/README.md).

---

## 4. Conclusión y Resumen de Trazabilidad

Con la adopción de estas decisiones de ingeniería, el repositorio `SkyRoutesDrones` mantiene un alineamiento total entre la documentación metodológica y el código ejecutable:

1. **Abstracción Pura:** Garantizada mediante `Dron(ABC)` e imposibilidad de instanciación genérica.
2. **Polimorfismo Dinámico:** Homogeneizado a través de contratos en consumo, diagnóstico y ejecución de misión para 6 categorías especializadas.
3. **Simulación Física Fiel:** Reemplazo de la teletransportación por un modelo de despegue y cinemática continua validada en el perímetro del Valle de Aburrá.
