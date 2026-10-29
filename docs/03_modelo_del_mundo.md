# Documento 03: Modelo del Mundo y Diseño de Clases

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  

---

## Tabla de Contenidos
- [1. Modelo del Mundo (Conceptualización de Flota)](#1-modelo-del-mundo-conceptualización-de-flota)
  - [1.1 Cuadro Comparativo de Especializaciones](#11-cuadro-comparativo-de-especializaciones)
  - [1.2 Descripción Detallada de los Drones](#12-descripción-detallada-de-los-drones)
- [2. Asignación de Responsabilidades por Entidad del Dominio](#2-asignación-de-responsabilidades-por-entidad-del-dominio)
  - [2.1 Entidades del Núcleo Operativo y Logístico](#21-entidades-del-núcleo-operativo-y-logístico)
  - [2.2 Entidades de Gestión Comercial y Trazabilidad](#22-entidades-de-gestión-comercial-y-trazabilidad)
  - [2.3 Clases de Especialización de Flota](#23-clases-de-especialización-de-flota)
- [3. Modelo de Clases UML (Diagrama Mermaid)](#3-modelo-de-clases-uml-diagrama-mermaid)
  - [3.1 Enlace Drawio](#31-enlace-drawio)
  - [3.2 Especificación Mermaid](#32-especificación-mermaid)

---

## 1. Modelo del Mundo (Conceptualización de Flota)

El sistema **SkyRoute** contempla una arquitectura modular de drones diferenciados por su propósito operativo en entornos urbanos y suburbanos. A continuación, se detallan los 6 tipos de aeronaves no tripuladas que componen la flota:

### 1.1 Cuadro Comparativo de Especializaciones

| # | Tipo de Dron | Categoría Operativa | Caso de Uso Principal | Atributos Específicos UML |
|---|---|---|---|---|
| 1 | **Dron de Entrega Ligera** | Última Milla | Paquetes livianos, medicamentos urgentes, comida en zonas urbanas densas (El Poblado, Laureles). | `pesoMaximoPaqueteKg`, `compartimentoRefrigerado`, `mecanismoSueltaRapida` |
| 2 | **Dron de Carga Pesada** | Transporte Logístico | Mover mercancía industrial o médica entre nodos logísticos (Sabaneta - Bello). | `volumenCargaM3`, `numeroRotores`, `potenciaRemolqueW` |
| 3 | **Dron de Vigilancia** | Monitoreo y Seguridad | Escolta de flota de carga, patrullaje de acopios y verificación pre-aterrizaje. | `resolucionCamaraMp`, `visionNocturna`, `frecuenciaTransmisionGhz` |
| 4 | **Dron de Mapeo** | Cartografía y Topografía | Recopilación geoespacial 3D para cálculo de rutas ortodrómicas en terreno montañoso. | `tieneSensorLidar`, `precisionGpsCm`, `capacidadAlmacenamientoTb` |
| 5 | **Dron de Inspección** | Mantenimiento | Vuelos estacionarios para evaluar infraestructura (vertipuertos, antenas, recarga). | `zoomOpticoX`, `rangoSensorUltrasonicoM` |
| 6 | **Dron de Rescate** | Asistencia de Flota | Respuesta rápida ante descensos forzosos o contingencias (Santa Elena, Nutibara). | `camaraTermica`, `kitAuxiliosEquipado`, `potenciaAltavozDb` |

---

### 1.2 Descripción Detallada de los Drones

#### 1. Dron de Entrega Ligera (Última Milla)
* **Funcionalidad principal:** Está diseñado para el transporte rápido de paquetes pequeños y livianos, como medicamentos urgentes, documentos importantes o comida.
* **Contexto operativo:** Su objetivo es evadir el pesado tráfico vehicular de la ciudad, navegando rápidamente por zonas residenciales o comerciales densas (como El Poblado o Laureles) para entregar el producto directamente al usuario final. Requiere mucha agilidad y sensores de evasión de obstáculos.

#### 2. Dron de Carga Pesada (Transporte Logístico)
* **Funcionalidad principal:** Mover suministros de gran volumen o peso (repuestos, suministros médicos al por mayor, mercancía industrial) entre los diferentes centros de distribución o bodegas de la empresa.
* **Contexto operativo:** En lugar de ir a casas, este dron hace rutas fijas entre puntos logísticos clave (por ejemplo, desde una bodega en el sur en Sabaneta hasta un punto en el norte en Bello). Son más lentos, requieren mucha más batería y vuelan a altitudes más controladas.

#### 3. Dron de Vigilancia y Seguridad (Monitoreo de Rutas)
* **Funcionalidad principal:** Su trabajo no es transportar paquetes, sino escoltar a los drones de carga o patrullar los centros de acopio.
* **Contexto operativo:** Proporciona transmisión de video para asegurar que la mercancía valiosa llegue a su destino sin ser interceptada. También verifica que las zonas de aterrizaje estén despejadas de personas o animales antes de que llegue un dron de entrega.

#### 4. Dron de Mapeo Topográfico
* **Funcionalidad principal:** Recopilar información del terreno y actualizar constantemente los mapas tridimensionales por donde vuela la flota.
* **Contexto operativo:** Debido a la geografía escarpada de las laderas y a la constante construcción de nuevos edificios o instalación de cables, este dron vuela recopilando datos geoespaciales para calcular rutas ortodrómicas seguras y actualizar las bases de datos de altitudes permitidas.

#### 5. Dron de Inspección de Infraestructura
* **Funcionalidad principal:** Revisar el estado técnico de las instalaciones logísticas de la empresa (antenas de comunicación, estaciones de recarga, plataformas de aterrizaje o "vertipuertos").
* **Contexto operativo:** Equipado con cámaras de alta precisión, se encarga de hacer vuelos estacionarios cerca de estructuras clave de la empresa logística para buscar daños, desgaste o fallas, garantizando que el resto de los drones tengan donde aterrizar y comunicarse sin peligro.

#### 6. Dron de Búsqueda y Rescate (Asistencia de Flota)
* **Funcionalidad principal:** Actuar como un equipo de respuesta rápida ante contingencias o emergencias operativas.
* **Contexto operativo:** Si un dron de entrega o carga reporta un error grave (por ejemplo, estado de motores en 'EMERGENCIA' y un descenso forzoso en una zona boscosa o montañosa como Santa Elena o el Cerro Nutibara), este dron se despliega rápidamente a las últimas coordenadas conocidas. Posee cámaras térmicas y de largo alcance para localizar el equipo perdido o la carga.

---

## 2. Asignación de Responsabilidades por Entidad del Dominio

Para que el sistema funcione de manera coordinada y ordenada, cada clase del modelo cumple un rol específico y bien definido. A continuación se desglosa cada entidad del dominio detallando sus **atributos**, **responsabilidades**, **colaboradores**, **requisitos que soporta** e **información que administra**:

---

### 2.1 Entidades del Núcleo Operativo y Logístico

#### 2.1.1 `SistemaCentroControl`
* **Atributos:**
  * `flotaDrones: list[Dron]`: Lista de aeronaves que componen la flota activa.
  * `usuariosRegistrados: list[Usuario]`: Catálogo de usuarios habilitados en la plataforma.
  * `pedidos: list[Pedido]`: Registro general de solicitudes de servicio ingresadas.
  * `historialLogs: list[LogOperacion]`: Bitácora cronológica de eventos y auditoría.
  * `coordenadasBase: tuple[float, float]`: Ubicación geográfica fija de la sede central de operaciones en Medellín.
* **Responsabilidades:**
  * Actuar como la torre de control y centro de comando virtual para toda la operación en el Valle de Aburrá.
  * Dar de alta nuevos usuarios y registrar aeronaves en la flota.
  * Recibir pedidos, cruzando en tiempo real las solicitudes pendientes con los drones disponibles para asignar automáticamente el recurso idóneo según la categoría solicitada.
  * Exigir y coordinar el retorno obligatorio a base una vez concluida una misión, impidiendo que el dron vuelva a estar disponible antes de llegar físicamente a la sede.
  * Generar y almacenar registros de auditoría ante cada evento relevante del sistema.
* **Colaboradores:**
  * `Dron`: Administra la flota, consulta su disponibilidad y activa su retorno a base.
  * `Usuario`: Registra y valida a los usuarios solicitantes.
  * `Pedido`: Centraliza los pedidos y les vincula el dron asignado.
  * `LogOperacion`: Instancia y archiva cada evento del sistema.
* **Requisitos que soporta:**
  * `RF-05` (Actualizar telemetría de flota bajo demanda).
  * `RF-06` (Registrar nuevo usuario en el sistema).
  * `RF-07` (Registrar solicitud de servicio).
  * `RF-08` (Cruzar información y asignar dron).
  * `RF-09` (Gestionar retorno obligatorio a base post-misión).
  * Regla de Negocio 9 (Cruce y consistencia relacional de información).
* **Información que administra:**
  * El inventario global de la flota, el registro de clientes y operadores, el estado de todos los pedidos y la memoria histórica de eventos operacionales.

---

#### 2.1.2 `Dron`
* **Atributos:**
  * `idDron: str`: Identificador alfanumérico único de la aeronave.
  * `modeloAeronave: str`: Referencia técnica o comercial del modelo.
  * `velocidadPromedioKmH: float`: Velocidad de crucero para traslados en km/h.
  * `kilometrajeTotal: float`: Odómetro de vuelo acumulado a lo largo de sus misiones.
  * `disponible: bool`: Bandera lógica que indica si está libre para recibir un nuevo encargo.
  * `enMision: bool`: Bandera que señala si se encuentra en vuelo realizando un servicio.
  * `retornandoABase: bool`: Bandera que indica si está en tránsito de regreso a la sede central.
  * `telemetria: TelemetriaDrone`: Instancia con los datos sensoriales en tiempo real.
  * `calculador: CalculadorGeodesico`: Herramienta matemática asociada para cálculos de navegación.
* **Responsabilidades:**
  * Modelar el comportamiento y el estado físico-operativo de cada aeronave de la empresa.
  * Vincular y actualizar su estado sensorial mediante su objeto de telemetría.
  * Calcular distancias hacia destinos geográficos y proyectar el tiempo estimado de llegada (ETA) en minutos delegando en su calculador.
  * Controlar su propio ciclo de misión, pasando de disponible a ocupado, y luego a estado de retorno obligatorio a base.
  * Proporcionar formatos de texto legibles para operadores (`__str__`) y fichas técnicas de inspección para desarrolladores (`__repr__`).
* **Colaboradores:**
  * `TelemetriaDrone`: Contiene sus mediciones físicas de batería, altitud, coordenadas y motores.
  * `CalculadorGeodesico`: Realiza los cálculos trigonométricos de distancia y tiempo.
  * `Pedido`: Aeronave asignada para ejecutar la orden de servicio.
  * `SistemaCentroControl`: Responde a las órdenes de asignación y retorno.
* **Requisitos que soporta:**
  * `RF-03` (Calcular distancia ortodrómica a destino).
  * `RF-04` (Consultar formato de consola e inspección técnica).
  * `RF-05` (Actualizar telemetría de flota).
  * `RF-09` (Gestionar retorno obligatorio a base).
  * `RF-10` (Calcular tiempo estimado de vuelo - ETA).
  * Regla de Negocio 1 (Identificador único no vacío).
* **Información que administra:**
  * Su ficha técnica de identificación, odómetro acumulado, estados operacionales (disponible, misión, retorno), lectura sensorial actual y herramienta de navegación.

---

#### 2.1.3 `TelemetriaDrone`
* **Atributos:**
  * `idDron: str`: Identificador del dron al que pertenecen las lecturas.
  * `bateria: float`: Porcentaje de carga restante de la batería (`[0.0, 100.0]%`).
  * `altitud: float`: Altura de vuelo sobre el nivel del suelo en metros (`[0.0, 120.0] m`).
  * `estadoMotores: str`: Estado de la planta motriz (`'APAGADOS'`, `'STANDBY'`, `'EN_VUELO'`, `'EMERGENCIA'`).
  * `latitud: float`: Coordenada de latitud en grados decimales acotada al Valle de Aburrá (`[5.9667, 6.5000]`, 5°58′ a 6°30′ N).
  * `longitud: float`: Coordenada de longitud en grados decimales acotada al Valle de Aburrá (`[-75.7167, -75.3500]`, 75°43′ a 75°21′ W).
* **Responsabilidades:**
  * Empaquetar y custodiar los datos sensoriales transmitidos por la aeronave en cada instante.
  * Validar estrictamente las reglas de dominio físico y regulatorio antes de aceptar cualquier valor.
  * Verificar la coherencia física entre altitud y motores (motores obligatoriamente `'EN_VUELO'` si `altitud > 0.0 m`; prohibido `'EN_VUELO'` si `altitud == 0.0 m`).
  * Disparar excepciones de dominio específicas (`BateriaInvalidaError`, `AltitudInvalidaError`, etc.) cuando se detecte una anomalía.
  * Permitir la actualización de la trama de datos bajo demanda del operador.
* **Colaboradores:**
  * `Dron`: Le provee su información sensorial y de ubicación en todo momento.
  * Excepciones de dominio: Dispara las clases de error correspondientes ante fallas de validación.
* **Requisitos que soporta:**
  * `RF-01` (Validar e instanciar trama de telemetría).
  * `RF-02` (Notificar excepciones de dominio específicas).
  * `RF-05` (Actualizar telemetría de la flota bajo demanda).
  * Reglas de Negocio 2, 3, 4 y 5.
* **Información que administra:**
  * Mediciones físicas y espaciales del dron: energía restante, cota altimétrica, condición motriz y posicionamiento global por GPS.

---

#### 2.1.4 `CalculadorGeodesico`
* **Atributos:**
  * `radioTierraKm: float`: Constante que define el radio medio terrestre (fijada en `6371.0 km`).
* **Responsabilidades:**
  * Realizar cálculos de trigonometría esférica para determinar la distancia ortodrómica en kilómetros entre dos coordenadas geográficas mediante la fórmula de Haversine.
  * Calcular el tiempo estimado de viaje (ETA) en minutos relacionando la distancia calculada con la velocidad promedio de vuelo.
* **Colaboradores:**
  * `Dron`: Utiliza sus métodos para conocer distancias a destinos y a la base central.
* **Requisitos que soporta:**
  * `RF-03` (Calcular distancia ortodrómica a destino).
  * `RF-10` (Calcular tiempo estimado de vuelo - ETA).
  * Regla de Negocio 6 (Cálculo geodésico Haversine).
* **Información que administra:**
  * Parámetros matemáticos y constante del radio de la Tierra.

---

### 2.2 Entidades de Gestión Comercial y Trazabilidad

#### 2.2.1 `Usuario`
* **Atributos:**
  * `idUsuario: str`: Identificador alfanumérico único de la persona o entidad.
  * `nombre: str`: Nombre completo o razón social del usuario registrado.
  * `rol: str`: Nivel de permisos dentro de la plataforma (`'CLIENTE'`, `'OPERADOR_VUELO'`, `'ADMINISTRADOR'`).
* **Responsabilidades:**
  * Identificar formalmente a los actores que interactúan con el sistema SkyRoute.
  * Validar que el identificador no sea vacío y que el rol asignado sea válido dentro de las políticas de la empresa.
* **Colaboradores:**
  * `SistemaCentroControl`: Registra y custodia a los usuarios autorizados.
  * `Pedido`: Aparece vinculado como el usuario solicitante de la orden de servicio.
* **Requisitos que soporta:**
  * `RF-06` (Registrar nuevo usuario en el sistema).
  * Regla de Negocio 7 (Validación de usuario y roles).
* **Información que administra:**
  * Identificador, nombre de usuario y perfil de privilegios en el sistema.

---

#### 2.2.2 `Pedido`
* **Atributos:**
  * `idPedido: str`: Código alfanumérico único de la solicitud de servicio.
  * `usuarioSolicitante: Usuario`: Instancia del usuario que solicita la misión.
  * `categoriaRequerida: str`: Categoría del dron requerido (ej. `'ENTREGA_LIGERA'`, `'CARGA_PESADA'`, etc.).
  * `coordenadaDestino: tuple[float, float]`: Coordenadas `(latitud, longitud)` donde se debe ejecutar la entrega o servicio.
  * `pesoCargaKg: float`: Masa de la mercancía en kilogramos (cuando la misión involucra transporte físico).
  * `estado: str`: Estado del ciclo de vida del pedido (`'PENDIENTE'`, `'ASIGNADO'`, `'EN_TRANSITO'`, `'COMPLETADO'`, `'CANCELADO'`).
  * `dronAsignado: Dron`: Referencia a la aeronave vinculada para cumplir la misión.
* **Responsabilidades:**
  * Modelar y estructurar el encargo de servicio solicitado por un cliente u operador.
  * Custodiar los requerimientos específicos de la misión (coordenadas objetivo, peso a transportar y categoría necesaria).
  * Administrar la transición de sus estados operativos a medida que avanza el servicio.
  * Enlazar formalmente la aeronave física asignada por el centro de control.
* **Colaboradores:**
  * `Usuario`: Usuario que solicita la orden.
  * `Dron`: Aeronave asignada para ejecutar la misión.
  * `SistemaCentroControl`: Orquesta la creación y asignación del pedido.
* **Requisitos que soporta:**
  * `RF-07` (Registrar solicitud de servicio).
  * `RF-08` (Cruzar información y asignar dron).
  * Regla de Negocio 8 (Validación y consistencia de pedido).
* **Información que administra:**
  * Identificador del encargo, cliente solicitante, especificaciones de la misión (categoría, destino, peso), estado del pedido y dron adjudicado.

---

#### 2.2.3 `LogOperacion`
* **Atributos:**
  * `idLog: str`: Código único del registro de auditoría.
  * `fechaHora: str`: Marca temporal con fecha y hora exacta del evento.
  * `tipoEvento: str`: Categoría o nombre del acontecimiento (ej. `'CREACION_PEDIDO'`, `'ASIGNACION_DRON'`, `'INICIO_RETORNO'`).
  * `idDron: str`: Identificador del dron involucrado en el suceso (si aplica).
  * `idPedido: str`: Identificador del pedido relacionado (si aplica).
  * `detalles: str`: Texto explicativo con detalles operacionales del evento.
* **Responsabilidades:**
  * Preservar la trazabilidad histórica de todas las acciones y decisiones tomadas en el sistema.
  * Garantizar la inmutabilidad de los registros operacionales.
  * Formatear líneas de auditoría estandarizadas para inspección y reportes en consola.
* **Colaboradores:**
  * `SistemaCentroControl`: Encargado de instanciar y recopilar cada log.
* **Requisitos que soporta:**
  * Trazabilidad transversal y auditoría de `RF-06`, `RF-07`, `RF-08` y `RF-09`.
* **Información que administra:**
  * Registro de auditoría con sello de tiempo, clasificación de evento, entidades asociadas y descripción técnica.

---

### 2.3 Clases de Especialización de Flota (Subtipos de Drones)

#### 2.3.1 `DronEntregaLigera` (Última Milla)
* **Atributos:**
  * `pesoMaximoPaqueteKg: float`: Capacidad máxima de carga en kilogramos.
  * `compartimentoRefrigerado: bool`: Indicador de compartimento térmico para medicamentos/comida.
  * `mecanismoSueltaRapida: bool`: Indicador de gancho o escotilla de liberación automática.
* **Responsabilidades:**
  * Gestionar la entrega ágil de paquetes pequeños en zonas urbanas densas, controlando límites de peso liviano y operando mecanismos de descarga rápida o aislamiento térmico.
* **Colaboradores:**
  * Especializa a la clase `Dron` (hereda todos sus atributos y métodos generales).
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Límite de carga en kg, habilitación de refrigeración y estado del mecanismo de suelta.

---

#### 2.3.2 `DronCargaPesada` (Transporte Logístico)
* **Atributos:**
  * `volumenCargaM3: float`: Capacidad volumétrica cúbica de la bodega interna.
  * `numeroRotores: int`: Cantidad de rotores dedicados a sustentación y empuje.
  * `potenciaRemolqueW: float`: Potencia en vatios de arrastre industrial.
* **Responsabilidades:**
  * Administrar traslados de gran volumen o suministros al por mayor entre bodegas logísticas, gestionando la tracción de múltiples rotores y la potencia de arrastre.
* **Colaboradores:**
  * Especializa a la clase `Dron`.
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Capacidad volumétrica en metros cúbicos, número de rotores instalados y potencia de empuje en vatios.

---

#### 2.3.3 `DronVigilancia` (Seguridad y Monitoreo)
* **Atributos:**
  * `resolucionCamaraMp: int`: Resolución del sensor óptico principal en megapíxeles.
  * `visionNocturna: bool`: Indicador de visión infrarroja nocturna.
  * `frecuenciaTransmisionGhz: float`: Frecuencia en GHz para el enlace de video en vivo.
* **Responsabilidades:**
  * Escolta aérea de drones de carga, patrullaje de perímetros de vertipuertos y transmisión de video de alta definición tanto diurna como nocturna.
* **Colaboradores:**
  * Especializa a la clase `Dron`.
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Megapíxeles de cámara, disponibilidad de visión nocturna y frecuencia en GHz del canal de transmisión.

---

#### 2.3.4 `DronMapeo` (Cartografía y Topografía)
* **Atributos:**
  * `tieneSensorLidar: bool`: Indicador de escáner láser de teledetección óptica.
  * `precisionGpsCm: float`: Margen de precisión del posicionamiento satelital en centímetros.
  * `capacidadAlmacenamientoTb: float`: Capacidad del disco de almacenamiento de nubes de puntos 3D.
* **Responsabilidades:**
  * Recopilar datos geoespaciales 3D mediante pulsos láser LiDAR y GPS de alta precisión en laderas y zonas montañosas para mantener actualizadas las rutas de vuelo seguras.
* **Colaboradores:**
  * Especializa a la clase `Dron`.
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Estado de sensor LiDAR, margen de error del GPS en centímetros y espacio de almacenamiento para escaneos 3D.

---

#### 2.3.5 `DronInspeccion` (Mantenimiento de Infraestructura)
* **Atributos:**
  * `zoomOpticoX: int`: Factor de aumentos del zoom óptico mecánico.
  * `rangoSensorUltrasonicoM: float`: Rango máximo en metros del sensor de proximidad.
* **Responsabilidades:**
  * Realizar vuelo estacionario cercano para inspeccionar fisuras, desgastes o averías técnicas en antenas, vertipuertos y estaciones de recarga sin riesgo de colisión.
* **Colaboradores:**
  * Especializa a la clase `Dron`.
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Factor de zoom óptico y distancia mínima de seguridad de sensores ultrasónicos.

---

#### 2.3.6 `DronRescate` (Asistencia y Búsqueda Operativa)
* **Atributos:**
  * `camaraTermica: bool`: Indicador de sensor térmico FLIR para detección por calor.
  * `kitAuxiliosEquipado: bool`: Indicador de botiquín o kit de herramientas de emergencia.
  * `potenciaAltavozDb: int`: Nivel de presión sonora del megáfono/altavoz en decibelios.
* **Responsabilidades:**
  * Responder con inmediatez ante descensos forzosos de aeronaves de la flota en zonas de difícil acceso, localizándolas mediante calor, emitiendo mensajes acústicos y transportando suministros de rescate.
* **Colaboradores:**
  * Especializa a la clase `Dron`.
* **Requisitos que soporta:** `RF-07`, `RF-08`.
* **Información que administra:** Disponibilidad de sensor térmico, presencia de botiquín/kit de auxilio y potencia sonora del altavoz en decibelios.

---

## 3. Modelo de Clases UML (Diagrama Mermaid)

### 3.1 Enlace Drawio

> **Diagrama en Draw.io:**  
https://drive.google.com/file/d/1L1QFliRs5vp0Q_SnUW9ahnXzg7J49c-M/view?usp=sharing

### 3.2 Especificación Mermaid

```mermaid
classDiagram
    %% =========================================================================
    %% 1. CAPA DE INTERFAZ GRÁFICA WEB, SERVIDOR HTTP Y CONSOLA INTERACTIVA
    %% =========================================================================

    class InterfazWebSPA {
        <<Frontend_SPA>>
        -snapshot: dict
        -vistaActiva: str
        -dronCabinaId: str
        -dronInspectorId: str
        -modoSimulacion: str
        -simularSoloEnfocado: bool
        -timerAuto: int
        -timerRealtime: int
        -cadenciaRealtimeSeg: int
        -modoDestinoPedido: str
        -filtroPedidos: str
        -distanciaPolimorfismoKm: float
        -datosPolimorfismo: dict
        -selectsInicializados: bool
        +iniciar() None
        +enlazarEventos() None
        +peticionAPI(ruta: str, opciones: dict) Promise~dict~
        +aplicarSnapshot(snapshot: dict, mostrarMensaje: bool) None
        +cambiarVista(nombreVista: str) None
        +cambiarModoSimulacion(modo: str) None
        +inicializarSelectoresEstaticos(snapshot: dict) None
        +renderizarBarraGlobal(snapshot: dict) None
        +renderizarCabinaOperaciones(snapshot: dict) None
        +renderizarFlotaEInspector(snapshot: dict) None
        +renderizarCamposDinamicosFabrica(categoria: str) None
        +renderizarDespachoYUsuarios(snapshot: dict) None
        +cargarComparativaPolimorfica(distanciaKm: float, sincronizarControles: bool) Promise~None~
        +renderizarBitacora(snapshot: dict) None
        +ejecutarPulsoSimulacion(deltaSeg: float, silencioso: bool) Promise~None~
        +iniciarAutoSimulacion() None
        +detenerAutoSimulacion() None
        +ejecutarPulsoTiempoReal(silencioso: bool) Promise~None~
        +iniciarSimulacionTiempoReal() None
        +detenerSimulacionTiempoReal() None
        +lanzarTourGuiado() Promise~None~
        +mostrarNotificacion(config: dict) None
    }

    class BaseHTTPRequestHandler {
        <<Standard_Library>>
        +path: str
        +headers: Message
        +rfile: BufferedReader
        +wfile: BufferedWriter
        +send_response(code: int) None
        +send_header(keyword: str, value: str) None
        +end_headers() None
    }

    class ManejadorSkyRouteHTTP {
        +DIRECTORIO_ESTATICOS: Path$
        +TIPOS_MIME: dict~str, str~$
        +controlador: ControladorSkyRoute$
        +candado: RLock$
        +log_message(format: str, args: Any) None
        -_enviar_json(payload: dict, codigo_http: int) None
        -_servir_archivo_estatico(nombre_relativo: str) None
        -_leer_cuerpo_json() dict
        +do_GET() None
        +do_POST() None
        +crear_servidor(host: str, puerto_inicial: int, controlador: ControladorSkyRoute)$ tuple~ThreadingHTTPServer, int~
        +iniciar_aplicacion(host: str, puerto: int, abrir_navegador: bool)$ None
    }

    class ControladorSkyRoute {
        +ETIQUETAS_CATEGORIA: dict~str, str~$
        +ESQUEMA_FABRICA: dict~str, dict~$
        +SUGERENCIAS_DIRECCIONES: list~dict~$
        +calculador: CalculadorGeodesico
        +geocodificador: IServicioGeocodificador
        +servicio_clima: ServicioClimaAburra
        +centro: SistemaCentroControl
        +simulador: SimuladorVuelo
        +reloj: RelojSimulacion
        -_usuario_activo_id: str
        -_nodo_clima_activo: str
        -_clima_actual: dict~str, Any~
        -_sesiones_vuelo: dict~str, dict~
        -_fuentes_geocodificacion: dict~str, str~
        -_contador_secuencial: int
        -_inicializar_entorno_base() None
        -_buscar_dron(id_dron: str) Dron
        -_buscar_pedido(id_pedido: str) Pedido
        -_buscar_usuario(id_usuario: str) Usuario
        -_buscar_pedido_por_id_seguro(id_pedido: str) Pedido
        -_pedido_reservado_para_dron(dron: Dron) Pedido
        -_extraer_atributos_especializados(dron: Dron) list~dict~
        -_calcular_progreso_lineal(dron: Dron, sesion: dict, distancia_a_base_km: float) dict
        -_serializar_dron(dron: Dron) dict
        -_diagnosticar_candidatos_pedido(pedido: Pedido) dict
        -_serializar_pedido(pedido: Pedido) dict
        +obtener_estado_completo() dict
        +consultar_clima_nodo(nodo: str) dict
        +previsualizar_geocodificacion(direccion: str) dict
        +comparar_viabilidad_polimorfica(distancia_km: float) dict
        +gestionar_usuario(datos: dict) dict
        +crear_dron_desde_fabrica(datos: dict) dict
        +recargar_bateria_dron(id_dron: str, porcentaje: float) dict
        +gestionar_telemetria_dron(datos: dict) dict
        +registrar_nuevo_pedido(datos: dict) dict
        +asignar_dron_pedido(id_pedido: str) dict
        +cancelar_pedido(id_pedido: str) dict
        +despegar_mision(id_pedido: str, modo_despacho: str, actualizar_clima: bool, id_dron: str) dict
        +avanzar_simulacion(id_dron: str, delta_t: float, usar_reloj_real: bool, escala_tiempo: float) dict
        +ordenar_retorno_base(id_dron: str) dict
        +finalizar_retorno_manual(id_dron: str) dict
        +controlar_reloj(accion: str) dict
        +preparar_tour_guiado() dict
        +formatear_excepcion(exc: Exception)$ dict
    }

    class ConsolaSkyRoute {
        +LINEA_DOBLE: str$
        +LINEA_SIMPLE: str$
        +calculador: CalculadorGeodesico
        +servicio_clima: ServicioClimaAburra
        +geocodificador: ServicioGeocodificadorArcGIS
        +centro: SistemaCentroControl
        +simulador: SimuladorVuelo
        +reloj: RelojSimulacion
        +cliente: Usuario
        +operador: Usuario
        -_inicializar_entorno_base() None
        +barra_bateria(porcentaje: float, ancho: int) str
        +encabezado(titulo: str) None
        +pausar() None
        +ver_estado_flota() None
        +registrar_pedido_interactivo() Pedido
        +asignar_dron_interactivo() None
        +simular_vuelo_interactivo() None
        +comparar_consumo_polimorfico() None
        +ver_bitacora_auditoria() None
        +ejecutar_demo_guiada() None
        +ejecutar() None
    }

    %% =========================================================================
    %% 2. ORQUESTADOR CENTRAL, SIMULACIÓN CINEMÁTICA Y RELOJ TEMPORAL
    %% =========================================================================

    class ResumenRefrescoFlota {
        <<dict>>
        +__int__() int
        +__index__() int
    }

    class SistemaCentroControl {
        +LAT_BASE: float$
        +LON_BASE: float$
        +COORDENADAS_BASE: tuple~float, float~$
        +FABRICA_DRONES: dict~str, TypeDron~$
        +flota_drones: list~Dron~
        +usuarios_registrados: list~Usuario~
        +pedidos: list~Pedido~
        +historial_logs: list~LogOperacion~
        +coordenadas_base: tuple~float, float~
        +geocodificador: IServicioGeocodificador
        +reloj: RelojSimulacion
        +servicio_clima: ServicioClimaAburra
        +simulador: SimuladorVuelo
        -_cache_clima: dict~str, Any~
        -_nodo_cache_clima: str
        -_ts_cache_clima: float
        +registrar_subclase_en_fabrica(categoria: str, clase_dron: TypeDron)$ None
        +instanciar_dron_desde_fabrica(categoria: str, args: Any, kwargs: Any)$ Dron
        -_obtener_clima_con_cache(nombre_nodo: str, ttl_segundos: float) dict
        +agregar_dron(dron: Dron) Dron
        +registrar_usuario(usuario: Usuario) Usuario
        +registrar_pedido(pedido: Pedido) Pedido
        +obtener_drones_disponibles() list~Dron~
        +asignar_dron_a_pedido(id_pedido: str) bool
        +despachar_mision(id_pedido: str) bool
        +gestionar_retorno_a_base(id_dron: str) bool
        +generar_log(evento: str, id_dron: str, id_pedido: str, detalles: str, tipo_evento: str) LogOperacion
        +refrescar_datos_flota(nombre_nodo: str, delta_t: float, factor_clima: float) ResumenRefrescoFlota
        +__str__() str
        +__repr__() str
    }

    class SimuladorVuelo {
        +calculador: ICalculadorGeodesico
        +centro_control: SistemaCentroControl
        +avanzar_paso_tiempo(dron: Dron, delta_t: float, factor_clima: float, coordenada_objetivo: tuple) dict
        +avanzar_flota(flota: list~Dron~, delta_t: float, factor_clima: float) list~dict~
    }

    class RelojSimulacion {
        +tiempo_inicio: float
        +ultima_actualizacion: float
        +pausado: bool
        +obtener_tiempo_total_seg() float
        +obtener_delta() float
        +reiniciar() None
    }

    class LogOperacion {
        +id_log: str
        +fecha_hora: str
        +tipo_evento: str
        +id_dron: str
        +id_pedido: str
        +detalles: str
        +formatear_registro() str
        +__str__() str
        +__repr__() str
    }

    %% =========================================================================
    %% 3. SERVICIOS DE GEODESIA, GEOCODIFICACIÓN Y METEOROLOGÍA
    %% =========================================================================

    class ICalculadorGeodesico {
        <<interface>>
        +LAT_MIN_ABURRA: float$
        +LAT_MAX_ABURRA: float$
        +LON_MIN_ABURRA: float$
        +LON_MAX_ABURRA: float$
        +radio_tierra_km: float
        +validar_coordenada(coordenada: tuple~float, float~)* None
        +calcular_haversine(origen: tuple, destino: tuple)* float
        +calcular_tiempo_vuelo_min(distancia_km: float, velocidad_km_h: float)* float
        +calcular_punto_intermedio(origen: tuple, destino: tuple, fraccion: float)* tuple~float, float~
    }

    class CalculadorGeodesico {
        +radio_tierra_km: float
        +validar_coordenada(coordenada: tuple~float, float~) None
        +calcular_haversine(origen: tuple, destino: tuple) float
        +calcular_tiempo_vuelo_min(distancia_km: float, velocidad_km_h: float) float
        +calcular_punto_intermedio(origen: tuple, destino: tuple, fraccion: float) tuple~float, float~
    }

    class IServicioGeocodificador {
        <<interface>>
        +geocodificar_direccion(direccion: str)* tuple~float, float~
        +obtener_detalle_direccion(direccion: str)* dict
    }

    class ServicioGeocodificadorArcGIS {
        +URL_ARCGIS: str$
        +SCORE_MINIMO: float$
        +calculador: ICalculadorGeodesico
        +proveedor_fallback: IServicioGeocodificador
        +score_minimo: float
        +normalizar_consulta(direccion: str) str
        +geocodificar_direccion(direccion: str) tuple~float, float~
        +obtener_detalle_direccion(direccion: str) dict
    }

    class ServicioGeocodificadorGoogle {
        +URL_GOOGLE: str$
        +calculador: ICalculadorGeodesico
        +api_key: str
        +proveedor_fallback: IServicioGeocodificador
        +normalizar_consulta(direccion: str) str
        +geocodificar_direccion(direccion: str) tuple~float, float~
        +obtener_detalle_direccion(direccion: str) dict
    }

    class ServicioGeocodificadorOSM {
        +URL_NOMINATIM: str$
        +USER_AGENT: str$
        +MAPA_PREFIJOS_VIALES: list~tuple~$
        +PATRON_CUADRICULA: Pattern$
        +CRUCES_COMPLEMENTARIOS: dict~str, str~$
        +TIPOS_NO_DESEADOS_SI_BUSCA_VIA: set~str~$
        +calculador: ICalculadorGeodesico
        +proveedor_fallback: IServicioGeocodificador
        +normalizar_consulta(direccion: str) str
        +generar_consultas_candidatas(direccion: str) list~str~
        -_es_resultado_valido(item: dict, requiere_nivel_via: bool) bool
        +geocodificar_direccion(direccion: str) tuple~float, float~
        +obtener_detalle_direccion(direccion: str) dict
    }

    class ServicioGeocodificadorLocal {
        +PUNTOS_REFERENCIA_ABURRA: dict~str, tuple~$
        +calculador: ICalculadorGeodesico
        +geocodificar_direccion(direccion: str) tuple~float, float~
        +obtener_detalle_direccion(direccion: str) dict
    }

    class ServicioClimaAburra {
        +NODOS_ABURRA: dict~str, dict~$
        +url_base: str
        +obtener_condiciones(nombre_nodo: str) dict
    }

    %% =========================================================================
    %% 4. GESTIÓN COMERCIAL Y TELEMETRÍA SENSORIAL
    %% =========================================================================

    class Usuario {
        +ROLES_PERMITIDOS: list~str~$
        +id_usuario: str
        +nombre: str
        +rol: str
        +validar_rol() bool
        +validar_usuario() bool
        +__str__() str
        +__repr__() str
    }

    class Pedido {
        +categorias_permitidas: list~str~$
        +estados_permitidos: list~str~$
        +id_pedido: str
        +usuario_solicitante: Usuario
        +categoria_requerida: str
        +categoria: str
        +coordenada_destino: tuple~float, float~
        +direccion_destino: str
        +peso_carga_kg: float
        +estado: str
        +dron_asignado: Dron
        +actualizar_estado(nuevo_estado: str) None
        +vincular_dron(dron: Dron) None
        +__str__() str
        +__repr__() str
    }

    class TelemetriaDrone {
        +id_dron: str
        +bateria: float
        +altitud: float
        +estado_motores: str
        +coordenadas: tuple~float, float~
        +latitud: float
        +longitud: float
        +validar_datos(id_dron: str, bateria: float, altitud: float, estado_motores: str, coordenadas: tuple) bool
        +actualizar_trama(bateria: float, altitud: float, estado_motores: str, coordenadas: tuple) None
        +__str__() str
        +__repr__() str
    }

    %% =========================================================================
    %% 5. CLASE ABSTRACTA BASE DE FLOTA Y 6 SUBCLASES ESPECIALIZADAS
    %% =========================================================================

    class Dron {
        <<abstract>>
        +id_dron: str
        +modelo_aeronave: str
        +velocidad_promedio_kmh: float
        +kilometraje_total_km: float
        +disponible: bool
        +en_mision: bool
        +retornando_a_base: bool
        +coordenadas_base: tuple~float, float~
        +pedido_activo: Pedido
        +ultimo_pedido_completado: Pedido
        +telemetria: TelemetriaDrone
        +calculador: ICalculadorGeodesico
        -_historial_telemetria: list~str~
        +historial_telemetria: tuple~str~
        -__post_init__() None
        +ejecutar_mision(pedido: Pedido)* dict
        +calcular_consumo_estimado(distancia_km: float)* float
        +inspeccionar_sistemas_especializados()* str
        +predecir_viabilidad_mision(distancia_km: float) dict
        +actualizar_estado_disponibilidad(disponible: bool) None
        +asignar_telemetria(nueva_telemetria: TelemetriaDrone) None
        +actualizar_telemetria(bateria_o_telemetria: float, altitud: float, estado_motores: str, coordenadas: tuple) None
        +recargar_bateria(porcentaje: float) None
        +calcular_distancia_a_destino(destino: tuple) float
        +estimar_tiempo_llegada_min(destino: tuple) float
        +iniciar_retorno_base(coordenadas_base: tuple) None
        +finalizar_retorno_en_base() None
        +finalizar_mision_en_destino() dict
        +__str__() str
        +__repr__() str
    }

    class DronEntregaLigera {
        +CATEGORIA_ESPECIALIZADA: str$
        +CAPACIDAD_CARGA_DEFAULT_KG: float$
        +categoria: str
        #_capacidad_carga_kg: float
        #_compartimento_refrigerado: bool
        #_mecanismo_suelta_rapida: bool
        +es_apto_carga(peso_carga_kg: float) bool
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +__str__() str
        +__repr__() str
    }

    class DronCargaPesada {
        +CATEGORIA_ESPECIALIZADA: str$
        +VOLUMEN_DEFAULT_M3: float$
        +ROTORES_DEFAULT: int$
        +POTENCIA_REMOLQUE_DEFAULT_W: float$
        +categoria: str
        #_volumen_carga_m3: float
        #_numero_rotores: int
        #_potencia_remolque_w: float
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +__str__() str
        +__repr__() str
    }

    class DronVigilancia {
        +CATEGORIA_ESPECIALIZADA: str$
        +RESOLUCION_DEFAULT_MP: int$
        +VISION_NOCTURNA_DEFAULT: bool$
        +FRECUENCIA_DEFAULT_GHZ: float$
        +categoria: str
        #_resolucion_camara_mp: int
        #_vision_nocturna: bool
        #_frecuencia_transmision_ghz: float
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +predecir_viabilidad_mision(distancia_km: float) dict
        +__str__() str
        +__repr__() str
    }

    class DronMapeo {
        +CATEGORIA_ESPECIALIZADA: str$
        +LIDAR_DEFAULT: bool$
        +PRECISION_GPS_DEFAULT_CM: float$
        +ALMACENAMIENTO_DEFAULT_TB: float$
        +categoria: str
        #_tiene_sensor_lidar: bool
        #_precision_gps_cm: float
        #_capacidad_almacenamiento_tb: float
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +__str__() str
        +__repr__() str
    }

    class DronInspeccion {
        +CATEGORIA_ESPECIALIZADA: str$
        +ZOOM_DEFAULT_X: int$
        +ULTRASONICO_DEFAULT_M: float$
        +categoria: str
        #_zoom_optico_x: int
        #_rango_sensor_ultrasonico_m: float
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +predecir_viabilidad_mision(distancia_km: float) dict
        +__str__() str
        +__repr__() str
    }

    class DronRescate {
        +CATEGORIA_ESPECIALIZADA: str$
        +CAMARA_TERMICA_DEFAULT: bool$
        +KIT_AUXILIOS_DEFAULT: bool$
        +POTENCIA_ALTAVOZ_DEFAULT_DB: int$
        +categoria: str
        #_camara_termica: bool
        #_kit_auxilios_equipado: bool
        #_potencia_altavoz_db: int
        +potenciaAltavozDb: int
        +ejecutar_mision(pedido: Pedido) dict
        +calcular_consumo_estimado(distancia_km: float) float
        +inspeccionar_sistemas_especializados() str
        +predecir_viabilidad_mision(distancia_km: float) dict
        +__str__() str
        +__repr__() str
    }

    %% =========================================================================
    %% 6. JERARQUÍA DE EXCEPCIONES DE DOMINIO AERONÁUTICO
    %% =========================================================================

    class Exception {
        <<builtin>>
    }

    class BateriaInvalidaError {
        +bateria_invalida: float
    }

    class AltitudInvalidaError {
        +altitud_invalida: float
    }

    class EstadoMotorInvalidoError {
        +estado_motor_invalido: str
    }

    class CoordenadaInvalidaError {
        +coordenada_invalida: Any
    }

    class GeocodificacionError {
        +direccion: str
    }

    class DronError {
        +id_dron: str
        +message: str
    }

    class ActualizarEstadoDronError {
        +parametro: str
    }

    class EstadoDronDuplicadoError {
        +estado_actual: bool
    }

    class AsignarTelemetriaError {
        +objeto_invalido: Any
    }

    class TelemetriaNoAsignadaError {
    }

    class DestinoInvalidoError {
        +destino: Any
    }

    class CategoriaDronInvalidoError {
        +categoria: str
        +categorias_permitidas: tuple
    }

    %% =========================================================================
    %% RELACIONES ARQUITECTÓNICAS DEL SISTEMA
    %% =========================================================================

    %% 1. Capa de Interfaz Gráfica Web, Servidor HTTP y Consola CLI
    InterfazWebSPA ..> ManejadorSkyRouteHTTP : consume API REST JSON
    BaseHTTPRequestHandler <|-- ManejadorSkyRouteHTTP
    ManejadorSkyRouteHTTP "1" --> "1" ControladorSkyRoute : delega peticiones HTTP
    ControladorSkyRoute "1" *-- "1" SistemaCentroControl : adapta y controla
    ControladorSkyRoute "1" *-- "1" SimuladorVuelo : ejecuta pulsos cinemáticos
    ControladorSkyRoute "1" *-- "1" RelojSimulacion : gestiona tiempo UI
    ControladorSkyRoute "1" o-- "1" IServicioGeocodificador : previsualiza direcciones
    ControladorSkyRoute "1" o-- "1" ServicioClimaAburra : consulta clima por nodo
    ControladorSkyRoute "1" o-- "1" CalculadorGeodesico : calcula distancias y viabilidad

    ConsolaSkyRoute "1" *-- "1" SistemaCentroControl : orquesta por CLI
    ConsolaSkyRoute "1" *-- "1" SimuladorVuelo : simula vuelo en consola
    ConsolaSkyRoute "1" *-- "1" RelojSimulacion : controla reloj
    ConsolaSkyRoute "1" o-- "1" ServicioGeocodificadorArcGIS : geocodifica pedidos
    ConsolaSkyRoute "1" o-- "1" ServicioClimaAburra : consulta meteorología

    %% 2. Orquestador Central y Motor de Simulación
    SistemaCentroControl "1" *-- "*" Dron : administra flota
    SistemaCentroControl "1" *-- "*" Usuario : registra usuarios
    SistemaCentroControl "1" *-- "*" Pedido : procesa pedidos
    SistemaCentroControl "1" *-- "*" LogOperacion : genera y audita
    SistemaCentroControl "1" o-- "1" IServicioGeocodificador : resuelve direcciones
    SistemaCentroControl "1" o-- "1" ServicioClimaAburra : consulta clima con caché
    SistemaCentroControl "1" *-- "1" RelojSimulacion : mide delta t
    SistemaCentroControl "1" *-- "1" SimuladorVuelo : avanza física de flota
    SistemaCentroControl ..> ResumenRefrescoFlota : retorna en refresco
    SimuladorVuelo "1" o-- "1" ICalculadorGeodesico : interpola waypoints y ETA
    SimuladorVuelo "0..1" --> "0..1" SistemaCentroControl : registra logs de arribo y emergencia
    SimuladorVuelo ..> Dron : integra cinemática y batería

    %% 3. Geodesia y Cadena de Contingencia en Geocodificación
    ICalculadorGeodesico <|.. CalculadorGeodesico
    IServicioGeocodificador <|.. ServicioGeocodificadorArcGIS
    IServicioGeocodificador <|.. ServicioGeocodificadorGoogle
    IServicioGeocodificador <|.. ServicioGeocodificadorOSM
    IServicioGeocodificador <|.. ServicioGeocodificadorLocal
    ServicioGeocodificadorArcGIS "1" o-- "1" ICalculadorGeodesico : valida geocerca Aburrá
    ServicioGeocodificadorArcGIS "1" --> "1" IServicioGeocodificador : fallback hacia OSM
    ServicioGeocodificadorGoogle "1" o-- "1" ICalculadorGeodesico : valida geocerca Aburrá
    ServicioGeocodificadorGoogle "1" --> "1" IServicioGeocodificador : fallback hacia OSM
    ServicioGeocodificadorOSM "1" o-- "1" ICalculadorGeodesico : valida geocerca Aburrá
    ServicioGeocodificadorOSM "1" --> "1" IServicioGeocodificador : fallback hacia Catálogo Local
    ServicioGeocodificadorLocal "1" o-- "1" ICalculadorGeodesico : valida geocerca Aburrá

    %% 4. Flujo de Pedidos, Usuarios y Componentes del Dron
    Pedido "*" --> "1" Usuario : solicitado por
    Pedido "0..1" --> "0..1" Dron : atendido por
    Dron "0..1" --> "0..1" Pedido : ejecuta pedido_activo
    Dron "1" *-- "0..1" TelemetriaDrone : monitoriza estado físico
    Dron "1" o-- "1" ICalculadorGeodesico : usa para navegación

    %% 5. Especialización Polimórfica de Flota (Herencia)
    Dron <|-- DronEntregaLigera
    Dron <|-- DronCargaPesada
    Dron <|-- DronVigilancia
    Dron <|-- DronMapeo
    Dron <|-- DronInspeccion
    Dron <|-- DronRescate

    %% 6. Jerarquía de Excepciones de Dominio
    Exception <|-- BateriaInvalidaError
    Exception <|-- AltitudInvalidaError
    Exception <|-- EstadoMotorInvalidoError
    Exception <|-- CoordenadaInvalidaError
    Exception <|-- GeocodificacionError
    Exception <|-- DronError
    DronError <|-- ActualizarEstadoDronError
    DronError <|-- EstadoDronDuplicadoError
    DronError <|-- AsignarTelemetriaError
    DronError <|-- TelemetriaNoAsignadaError
    DronError <|-- DestinoInvalidoError
    DronError <|-- CategoriaDronInvalidoError

    TelemetriaDrone ..> BateriaInvalidaError : dispara
    TelemetriaDrone ..> AltitudInvalidaError : dispara
    TelemetriaDrone ..> EstadoMotorInvalidoError : dispara
    TelemetriaDrone ..> CoordenadaInvalidaError : dispara
    CalculadorGeodesico ..> CoordenadaInvalidaError : dispara
    IServicioGeocodificador ..> GeocodificacionError : dispara
    Dron ..> DronError : dispara subclases
```