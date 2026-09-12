# Documento 04: Historias de Usuario y Plan de Trabajo (Sprint 1)

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  
**Semestre:** 2026-2  
**Docente:** Mario Alejandro Saldarriaga (Grupo 62)  
**Equipo:** Alejandro García Jiménez, Juan Manuel Pava Higuita, Valery Arboleda Ardila  

---

## 1. Lineamientos Técnicos del Sprint 1: "El Core sin Pilares"

> **RESTRICCIONES OBLIGATORIAS:**  
> En esta primera entrega **NO se permite el uso de los 4 pilares de la Programación Orientada a Objetos**:
> * **Cero Herencia:** No crear jerarquías de clases (`class DronEntrega(Dron)`). Todas las aeronaves se gestionan con una clase concreta `Dron` configurando su tipo mediante un atributo plano (ej. `categoria: str`).
> * **Cero Polimorfismo:** No sobrescribir métodos ni implementar despacho dinámico. Usar bifurcaciones directas (`if/elif/else`) para comportamientos según el tipo.
> * **Cero Encapsulamiento Estricto:** No usar atributos privados con doble guion bajo (`__atributo`) ni decoradores `@property` para getters/setters avanzados. Los atributos se asignan directamente en el constructor `__init__` (`self.atributo = valor`) y se validan con condicionales antes de asignarse.
> * **Cero Abstracción Formal:** No usar el módulo `abc` ni métodos abstractos (`@abstractmethod`).
> * **Lógica Pura entre Clases:** Creación de clases concretas que colaboran pasándose instancias, guardando listas de objetos y ejecutando métodos directos de negocio.

---

## 2. Matriz de Distribución Equitativa del Trabajo

Para garantizar un reparto exactamente equitativo (33.3% por integrante), el sistema se descompone en 3 módulos funcionales con carga de lógica balanceada:

| Integrante | Módulo Asignado | Requisitos Funcionales | Clases y Componentes Clave |
|---|---|---|---|
| **Alejandro García Jiménez** | **Módulo 1:** Núcleo Geodésico, Excepciones y Telemetría | RF-01, RF-02, RF-03, RF-10 | `TelemetriaDrone`, `CalculadorGeodesico`, Excepciones de Dominio |
| **Juan Manuel Pava Higuita** | **Módulo 2:** Entidad Dron, Operación de Flota y Consola | RF-04, RF-05, RF-09 | `Dron`, Ciclo de retorno a base, `__str__` / `__repr__` |
| **Valery Arboleda Ardila** | **Módulo 3:** Usuarios, Pedidos y Orquestación Central | RF-06, RF-07, RF-08 | `Usuario`, `Pedido`, `LogOperacion`, `SistemaCentroControl` |

---

## 3. Historias de Usuario Detalladas y To-Do Lists

---

### Responsable 1: Alejandro García Jiménez
**Módulo:** Núcleo Geodésico, Telemetría y Manejo de Excepciones

#### HU-01: Validación de Datos de Telemetría y Excepciones de Dominio
* **Como:** Operador de seguridad aérea y monitoreo.
* **Quiero:** Que el sistema valide rigurosamente los datos crudos de telemetría (batería, altitud, motores, coordenadas) y emita alertas claras ante anomalías.
* **Para:** Garantizar que ninguna aeronave opere bajo condiciones físicas incoherentes o fuera de la normativa aeronáutica del Valle de Aburrá.
* **RF Vinculados:** `RF-01`, `RF-02`

##### Criterios de Aceptación:
1. Si `bateria` no está en `[0.0, 100.0]`, se interrumpe lanzando `BateriaInvalidaError`.
2. Si `altitud` no está en `[0.0, 120.0]`, se lanza `AltitudInvalidaError`.
3. Si `altitud > 0.0` y `estado_motores != 'EN_VUELO'`, se lanza `EstadoMotorInvalidoError`.
4. Si `altitud == 0.0` y `estado_motores == 'EN_VUELO'`, se lanza `EstadoMotorInvalidoError`.
5. Si `coordenadas` no están en latitud `[-90.0, 90.0]` o longitud `[-180.0, 180.0]`, se lanza `CoordenadaInvalidaError`.

##### To-Do List:
- [ ] Crear el archivo de excepciones con las clases: `BateriaInvalidaError`, `AltitudInvalidaError`, `EstadoMotorInvalidoError`, `CoordenadaInvalidaError` (heredando únicamente de `Exception` nativa de Python).
- [ ] Definir la clase `TelemetriaDrone` con el método `__init__(self, id_dron, bateria, altitud, estado_motores, coordenadas)`.
- [ ] Implementar el método `validar_datos()` dentro de `TelemetriaDrone` aplicando las reglas de negocio con condicionales `if/else`.
- [ ] Implementar el método `actualizar_trama(self, bateria, altitud, estado_motores, coordenadas)` que vuelva a validar antes de actualizar los atributos.

> [!TIP]
> **Guía para Alejandro:**
> * Recuerda: no uses getters/setters ni `@property`. Llama a tu método `self.validar_datos()` directamente en la primera línea de `__init__`.
> * Para verificar motores, define una tupla o lista permitida: `estados_validos = ('APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA')`.
> * Las coordenadas deben recibirse como una tupla `(latitud, longitud)`. Puedes desempaquetarlas fácilmente: `lat, lon = coordenadas`.

---

#### HU-02: Motor de Cálculo Geodésico (Haversine) y Estimador de Tiempo (ETA)
* **Como:** Operador de logística y tráfico de drones.
* **Quiero:** Disponer de una herramienta matemática que calcule distancias ortodrómicas exactas en la Tierra y proyecte tiempos estimados de viaje.
* **Para:** Conocer con precisión la longitud de las rutas sobre Medellín y estimar a qué hora llegará el servicio al cliente.
* **RF Vinculados:** `RF-03`, `RF-10`

##### Criterios de Aceptación:
1. El cálculo de distancia usa la fórmula de Haversine asumiendo un radio terrestre de `6371.0 km`.
2. El resultado se retorna como un número decimal (`float`) que representa kilómetros.
3. El cálculo de ETA recibe la distancia en km y la velocidad promedio en km/h, retornando el tiempo estimado en **minutos**.

##### To-Do List:
- [ ] Crear la clase `CalculadorGeodesico`.
- [ ] Asignar el atributo `radio_tierra_km = 6371.0` en el `__init__`.
- [ ] Implementar el método `calcular_haversine(self, origen, destino)` usando las funciones `math.radians`, `math.sin`, `math.cos`, `math.sqrt` y `math.atan2`.
- [ ] Implementar el método `calcular_tiempo_vuelo_min(self, distancia_km, velocidad_km_h)` mediante la fórmula: `(distancia_km / velocidad_km_h) * 60.0`.

> [!TIP]
> **Guía para Alejandro:**
> * Recuerda importar `import math` al inicio del archivo.
> * Valida que si la `velocidad_km_h <= 0`, el método de tiempo retorne `0.0` o levante un error para evitar división por cero.
> * Comprueba tu fórmula con dos puntos conocidos de Medellín (por ejemplo, Centro Comercial Santafé hacia Parque Berrío).

---

### Responsable 2: Juan Manuel Pava Higuita
**Módulo:** Entidad Dron, Operación de Flota y Visualización en Consola

#### HU-03: Estructura del Dron y Representación Técnica en Consola
* **Como:** Desarrollador y supervisor del centro de monitoreo.
* **Quiero:** Contar con una clase unificada `Dron` capaz de contener la telemetría, sus especificaciones operativas y contar con formatos legibles en texto.
* **Para:** Inspeccionar visualmente el estado del dron en terminal y depurar el sistema de forma rápida y comprensible.
* **RF Vinculados:** `RF-04`, `RF-05`

##### Criterios de Aceptación:
1. La clase `Dron` almacena directamente: `id_dron`, `modelo`, `categoria`, `velocidad_promedio_kmh`, `kilometraje_total`, `disponible`, `en_mision`, `retornando_a_base`, `telemetria` (objeto) y `calculador` (objeto).
2. El método `__str__` muestra una ficha técnica limpia y formateada con el estado actual, batería y ubicación del dron.
3. El método `__repr__` muestra una salida técnica con los valores clave de la instancia para fines de depuración.
4. El método `actualizar_telemetria(nueva_telemetria)` reemplaza el objeto de telemetría asociado y acumula el kilometraje si hubo desplazamiento.

##### To-Do List:
- [ ] Crear la clase `Dron` con sus atributos iniciales en `__init__`.
- [ ] Conectar una instancia de `CalculadorGeodesico` dentro del dron (`self.calculador = CalculadorGeodesico()`).
- [ ] Implementar el método `asignar_telemetria(self, nueva_telemetria)` que verifique que el `id_dron` de la telemetría coincida con el del dron.
- [ ] Implementar el método especial `__str__(self)` con formato legible multilínea (incluyendo indicadores como `[DISPONIBLE]`, porcentaje de batería, etc.).
- [ ] Implementar el método especial `__repr__(self)` devolviendo una cadena con formato: `Dron(id='...', categoria='...', disponible=...)`.

> [!TIP]
> **Guía para Juan Manuel:**
> * Como **no hay herencia**, las 6 categorías se manejan como una cadena en `self.categoria` (ejemplo: `'ENTREGA_LIGERA'`, `'CARGA_PESADA'`, `'VIGILANCIA'`, etc.).
> * Puedes agregar un diccionario de atributos complementarios o atributos simples para los extras de cada dron (como capacidad de carga o cámara) sin crear subclases.
> * En `__str__`, accede a los datos de la telemetría colaborando directamente: `self.telemetria.bateria`, `self.telemetria.altitud`.

---

####  HU-04: Protocolo de Retorno Obligatorio a Base y Cálculo de ETA
* **Como:** Jefe de operaciones de vuelo.
* **Quiero:** Que al terminar una misión el dron entre en un estado de retorno obligatorio a la sede principal y no quede disponible de inmediato.
* **Para:** Garantizar que ninguna aeronave quede desatendida en el mapa y vuelva a base para mantenimiento o recarga de batería.
* **RF Vinculados:** `RF-09`, `RF-10`

##### Criterios de Aceptación:
1. Al invocar `iniciar_retorno(coordenadas_base)`, el dron cambia: `retornando_a_base = True`, `en_mision = False` y `disponible = False`.
2. El método `estimar_tiempo_llegada(destino)` utiliza el `CalculadorGeodesico` asociado para calcular la distancia y dividirla por su velocidad propia.
3. El método `finalizar_retorno()` únicamente marca `disponible = True` y `retornando_a_base = False` cuando el dron esté efectivamente en la base.

##### To-Do List:
- [ ] Implementar el método `iniciar_retorno_base(self, coordenadas_base)` en `Dron`.
- [ ] Implementar el método `calcular_distancia_a_destino(self, coordenada_destino)` llamando al calculador geodesico.
- [ ] Implementar el método `estimar_tiempo_llegada_min(self, coordenada_destino)` invocando el cálculo de ETA.
- [ ] Implementar el método `aterrizar_en_base(self)` que apague motores, reinicie el estado a disponible y confirme el fin del retorno.

> [!TIP]
> **Guía para Juan Manuel:**
> * Para calcular distancias, usa la instancia del calculador que creaste en el dron: `distancia = self.calculador.calcular_haversine(self.telemetria.coordenadas, destino)`.
> * De esta forma pones a colaborar dos clases (`Dron` y `CalculadorGeodesico`) con lógica pura, sin necesidad de herencia.

---

### Responsable 3: Valery Arboleda Ardila
**Módulo:** Usuarios, Pedidos, Auditoría y Orquestador del Centro de Control

#### HU-05: Registro de Usuarios, Solicitudes de Pedido y Logs de Auditoría
* **Como:** Administrador y cliente del sistema.
* **Quiero:** Poder registrar nuevos usuarios con roles válidos y generar solicitudes de servicio asociadas a categorías específicas de drones.
* **Para:** Organizar las peticiones de transporte, vigilancia o inspección antes de que sean despachadas al aire.
* **RF Vinculados:** `RF-06`, `RF-07`

##### Criterios de Aceptación:
1. La clase `Usuario` valida que el `rol` pertenezca a `{'CLIENTE', 'OPERADOR_VUELO', 'ADMINISTRADOR'}`.
2. La clase `Pedido` recibe un objeto `Usuario`, la categoría solicitada, coordenadas de destino y peso de carga (opcional).
3. Todo pedido nuevo nace con estado `'PENDIENTE'` y sin dron asignado (`dron_asignado = None`).
4. La clase `LogOperacion` registra la fecha/hora, el evento, el ID del dron y el ID del pedido.

##### To-Do List:
- [ ] Crear la clase `Usuario` con atributos: `id_usuario`, `nombre`, `rol`.
- [ ] Implementar validación en `Usuario` para asegurar que el nombre no sea vacío y el rol sea válido.
- [ ] Crear la clase `Pedido` con atributos: `id_pedido`, `usuario_solicitante`, `categoria_requerida`, `coordenada_destino`, `peso_carga_kg`, `estado`, `dron_asignado`.
- [ ] Implementar en `Pedido` métodos simples como `actualizar_estado(nuevo_estado)` y `vincular_dron(dron)`.
- [ ] Crear la clase `LogOperacion` con método `formatear_registro()` para imprimir auditorías.

> [!TIP]
> **Guía para Valery:**
> * El atributo `usuario_solicitante` en `Pedido` debe ser directamente el objeto `Usuario`, no solo su nombre o ID.
> * Las 6 categorías autorizadas de drones son:
>   `'ENTREGA_LIGERA'`, `'CARGA_PESADA'`, `'VIGILANCIA'`, `'MAPEO_TOPOGRAFICO'`, `'INSPECCION_INFRAESTRUCTURA'`, `'BUSQUEDA_RESCATE'`. Valida que la categoría solicitada esté en esta lista.

---

#### HU-06: Asignación Inteligente de Drones en el Sistema de Centro de Control
* **Como:** Orquestador central del sistema SkyRoute.
* **Quiero:** Gestionar la flota global, registrar los pedidos y cruzar la información para asignar automáticamente el dron idóneo disponible.
* **Para:** Automatizar el despacho de servicios sin intervención manual propensa a errores.
* **RF Vinculados:** `RF-08`, `RF-09`

##### Criterios de Aceptación:
1. `SistemaCentroControl` mantiene listas internas: `flota_drones`, `usuarios_registrados`, `pedidos` e `historial_logs`.
2. El método `asignar_dron_a_pedido(id_pedido)` busca el pedido por su ID, filtra drones disponibles cuya categoría coincida exactamente con la requerida, y realiza la vinculación.
3. Si la asignación tiene éxito, el pedido pasa a `'ASIGNADO'`, el dron pasa a `disponible = False`, `en_mision = True`, y se genera un `LogOperacion`.
4. Si no hay drones compatibles o disponibles, retorna `False` o lanza un aviso informativo sin que el programa se caiga.

##### To-Do List:
- [ ] Crear la clase `SistemaCentroControl` inicializando las listas vacías y las `coordenadas_base = (6.2089, -75.5684)` (Medellín).
- [ ] Implementar métodos de administración: `registrar_usuario(usuario)` y `agregar_dron(dron)`.
- [ ] Implementar `crear_pedido(id_pedido, usuario, categoria, destino, peso)` y añadirlo a la lista.
- [ ] Implementar el algoritmo de asignación en `asignar_dron_a_pedido(id_pedido)`.
- [ ] Implementar `gestionar_retorno_a_base(id_dron)` que busque el dron en la lista y dispare su protocolo de retorno hacia las coordenadas base.

> [!TIP]
> **Guía para Valery:**
> * Para buscar el dron disponible, usa un simple ciclo `for dron in self.flota_drones:` con una condición:  
>   `if dron.disponible and dron.categoria == pedido.categoria_requerida:`.
> * Al encontrarlo, vincula: `pedido.vincular_dron(dron)` y cambia el estado del dron. Luego usa `break` para no seguir buscando.

---

## 4. Plan de Integración y Validación Conjunta (Fin del Sprint 1)

Una vez que cada integrante termine su módulo individual, se realizará una sesión de integración en un archivo ejecutable (ej. `main.py` o `demo_sprint1.py`).

### Checklist de Prueba Conjunta:
- [ ] **Paso 1 (Alejandro & Juan Manuel):** Instanciar un `Dron`, asignarle una `TelemetriaDrone` con coordenadas de Medellín y verificar que disparos con batería negativa o altitud excesiva eleven las excepciones esperadas.
- [ ] **Paso 2 (Alejandro & Juan Manuel):** Calcular la distancia entre el dron y un destino de prueba mediante `CalculadorGeodesico`, verificando el ETA en minutos.
- [ ] **Paso 3 (Valery & Juan Manuel):** Crear un `SistemaCentroControl`, añadir 2 drones de categorías distintas a la flota y registrar un usuario cliente.
- [ ] **Paso 4 (Integración Total):** Crear un pedido para una categoría en específico, ejecutar `asignar_dron_a_pedido`, y constatar que:
  * El pedido quedó con estado `'ASIGNADO'` y referencia al dron.
  * El dron quedó como no disponible.
  * Se generó un registro en `historial_logs`.
- [ ] **Paso 5 (Cierre de Vuelo):** Invocar `gestionar_retorno_a_base` para comprobar el cambio de estado a retorno hacia la base de Medellín.
