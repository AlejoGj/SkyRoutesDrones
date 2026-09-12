# Documento 03: Modelo del Mundo y Diseño de Clases

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  

---

## Tabla de Contenidos
- [1. Modelo del Mundo (Conceptualización de Flota)](#1-modelo-del-mundo-conceptualización-de-flota)
  - [1.1 Cuadro Comparativo de Especializaciones](#11-cuadro-comparativo-de-especializaciones)
  - [1.2 Descripción Detallada de los Drones](#12-descripción-detallada-de-los-drones)
- [2. Modelo de Clases UML (Diagrama Mermaid)](#2-modelo-de-clases-uml-diagrama-mermaid)
  - [2.1 Recurso Gráfico Editable](#21-recurso-gráfico-editable)
  - [2.2 Especificación Mermaid](#22-especificación-mermaid)

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

## 2. Modelo de Clases UML (Diagrama Mermaid)

### 2.1 Enlace Drawio

> **Diagrama en Draw.io:**  
https://drive.google.com/file/d/1L1QFliRs5vp0Q_SnUW9ahnXzg7J49c-M/view?usp=sharing

### 2.2 Especificación Mermaid

```mermaid
classDiagram
    %% ==========================================
    %% 1. ORQUESTADOR CENTRAL
    %% ==========================================
    
    class SistemaCentroControl {
        -flotaDrones: list~Dron~
        -usuariosRegistrados: list~Usuario~
        -pedidos: list~Pedido~
        -historialLogs: list~LogOperacion~
        -coordenadasBase: tuple~float, float~
        +refrescarDatosFlota()
        +registrarUsuario(idUsuario: str, nombre: str, rol: str) Usuario
        +registrarPedido(usuario: Usuario, categoria: str, destino: tuple) Pedido
        +asignarDronAPedido(idPedido: str) bool
        +obtenerDronesDisponibles() list~Dron~
        +gestionarRetornoABase(idDron: str)
        +generarLog(evento: str, idDron: str, idPedido: str) LogOperacion
    }

    %% ==========================================
    %% 2. GESTIÓN DE USUARIOS, PEDIDOS Y LOGS
    %% ==========================================
    class Usuario {
        -idUsuario: str
        -nombre: str
        -rol: str
        +validarRol() bool
    }

    class Pedido {
        -idPedido: str
        -usuarioSolicitante: Usuario
        -categoriaRequerida: str
        -coordenadaDestino: tuple~float, float~
        -pesoCargaKg: float
        -estado: str
        -dronAsignado: Dron
        +actualizarEstado(nuevoEstado: str)
        +vincularDron(dron: Dron)
    }

    class LogOperacion {
        -idLog: str
        -fechaHora: str
        -tipoEvento: str
        -idDron: str
        -idPedido: str
        -detalles: str
        +formatearRegistro() str
    }

    %% ==========================================
    %% 3. TELEMETRÍA Y CÁLCULO
    %% ==========================================
    class CalculadorGeodesico {
        -radioTierraKm: float
        +calcularHaversine(origen: tuple, destino: tuple) float
        +calcularTiempoVueloMin(distanciaKm: float, velocidadKmH: float) float
    }

    class TelemetriaDrone {
        -idDron: str
        -bateria: float
        -altitud: float
        -estadoMotores: str
        -latitud: float
        -longitud: float
        +validarRangos() bool
        +_validarCoherenciaVuelo() bool
        +actualizarTrama(bateria: float, altitud: float, motores: str, lat: float, lon: float)
    }

    %% ==========================================
    %% 4. CLASE BASE DE FLOTA
    %% ==========================================
    class Dron {
        -idDron: str
        -modeloAeronave: str
        -velocidadPromedioKmH: float
        -kilometrajeTotal: float
        -disponible: bool
        -enMision: bool
        -retornandoABase: bool
        -telemetria: TelemetriaDrone
        -calculador: CalculadorGeodesico
        +asignarNuevaTelemetria(nuevaTelemetria: TelemetriaDrone)
        +calcularDistanciaADestino(destino: tuple) float
        +estimarTiempoLlegadaMin(destino: tuple) float
        +iniciarRetornoBase(coordenadasBase: tuple)
        +cambiarDisponibilidad(estado: bool)
    }

    %% ==========================================
    %% 5. SUBCLASES ESPECIALIZADAS (6 TIPOS)
    %% ==========================================
    class DronEntregaLigera {
        -pesoMaximoPaqueteKg: float
        -compartimentoRefrigerado: bool
        -mecanismoSueltaRapida: bool
    }

    class DronCargaPesada {
        -volumenCargaM3: float
        -numeroRotores: int
        -potenciaRemolqueW: float
    }

    class DronVigilancia {
        -resolucionCamaraMp: int
        -visionNocturna: bool
        -frecuenciaTransmisionGhz: float
    }

    class DronMapeo {
        -tieneSensorLidar: bool
        -precisionGpsCm: float
        -capacidadAlmacenamientoTb: float
    }

    class DronInspeccion {
        -zoomOpticoX: int
        -rangoSensorUltrasonicoM: float
    }

    class DronRescate {
        -camaraTermica: bool
        -kitAuxiliosEquipado: bool
        -potenciaAltavozDb: int
    }

    %% ==========================================
    %% RELACIONES DEL SISTEMA
    %% ==========================================
    %% Orquestador
    SistemaCentroControl "1" *-- "*" Dron : administra
    SistemaCentroControl "1" *-- "*" Usuario : registra
    SistemaCentroControl "1" *-- "*" Pedido : procesa
    SistemaCentroControl "1" *-- "*" LogOperacion : genera y audita

    %% Flujo de Pedidos y Usuarios
    Pedido "*" --> "1" Usuario : solicitado por
    Pedido "0..1" --> "0..1" Dron : atendido por

    %% Componentes del Dron
    Dron "1" *-- "1" TelemetriaDrone : monitoriza estado
    Dron "1" o-- "1" CalculadorGeodesico : usa para cálculos

    %% Especialización de Drones (Herencia)
    Dron <|-- DronEntregaLigera
    Dron <|-- DronCargaPesada
    Dron <|-- DronVigilancia
    Dron <|-- DronMapeo
    Dron <|-- DronInspeccion
    Dron <|-- DronRescate
```