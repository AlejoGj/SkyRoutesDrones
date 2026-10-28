# Documento 02: Requisitos Funcionales y Reglas de Negocio

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  

---

## 1. Reglas de Negocio del Sistema (Restricciones de Dominio)

1. **Identificador Único (`id_dron`):** Cadena alfanumérica no vacía (`str`). No se permiten espacios en blanco puros.
2. **Nivel de Batería (`bateria`):** Número real en porcentaje delimitado estrictamente en `[0.0, 100.0]%`.
3. **Límite de Altitud (`altitud`):** Medida en metros sobre el nivel del suelo en el rango `[0.0, 120.0] m` (techo aeronáutico regulatorio).
4. **Coherencia de Motores vs Altitud:**
   - Si `altitud > 0.0 m`: `estado_motores` debe ser obligatoriamente `'EN_VUELO'`.
   - Si `altitud == 0.0 m` (en tierra): `estado_motores` no puede ser `'EN_VUELO'` (debe ser `'APAGADOS'`, `'STANDBY'` o `'EMERGENCIA'`).
   - El conjunto de estados válidos para los motores es estrictamente: `{'APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA'}`.
5. **Coordenadas Geográficas (`coordenadas`):** Tupla de dos números reales `(latitud, longitud)` delimitada estrictamente por el área operativa del Valle de Aburrá (entre 5°58′ y 6°30′ de latitud norte `[5.9667, 6.5000]` y 75°21′ y 75°43′ de longitud oeste `[-75.7167, -75.3500]`).
6. **Cálculo Geodésico:** La distancia a un destino geográfico se calcula mediante la fórmula de Haversine asumiendo un radio terrestre de 6371.0 km.
7. **Validación de Usuario:** Todo usuario registrado en el sistema debe poseer un identificador único (`id_usuario`), un nombre no vacío y un rol válido dentro de la plataforma (ej. `{'CLIENTE', 'OPERADOR_VUELO', 'ADMINISTRADOR'}`).
8. **Validación de Pedido:** Cada pedido gestionado por el sistema requiere un identificador único (`id_pedido`), un estado inicial válido (ej. `{'PENDIENTE', 'ASIGNADO', 'EN_TRANSITO', 'COMPLETADO', 'CANCELADO'}`), y debe estar asociado obligatoriamente a un usuario existente y a una de las 6 categorías de drones autorizadas.
9. **Cruce de Información (Sistema de Control):** El sistema de control centraliza los registros de la flota de drones, los perfiles de los usuarios y las solicitudes de pedidos, asegurando la consistencia relacional al momento de asignar los recursos.
10. **Autonomía de Circuito Completo:** Ninguna aeronave puede ser asignada ni despachada si su nivel de batería remanente es inferior al consumo estimado requerido para completar tanto el trayecto de ida al destino como el retorno obligatorio hacia la base central ($C_{\text{total}} = C_{\text{ida}} + C_{\text{retorno}}$).
11. **Tolerancia Métrica de Vertipuerto (50 m):** El protocolo de aterrizaje y confirmación de fin de retorno a base solo puede ejecutarse si la aeronave se encuentra a una distancia ortodrómica menor o igual a 50 metros ($\le 0.05\text{ km}$) respecto a las coordenadas oficiales de la base central (Aeropuerto Olaya Herrera).
12. **Aterrizaje de Emergencia por Agotamiento Energético (0.0%):** Si durante la simulación de vuelo la batería de una aeronave alcanza el $0.0\%$, el sistema interrumpe el vuelo de forma inmediata, interpola las coordenadas geográficas exactas del incidente, apaga motores a `'STANDBY'`, fija la altitud en $0.0\text{ m}$, marca la aeronave como no disponible y emite una alerta crítica en la bitácora de auditoría.

---

## 2. Requisitos Funcionales (Formato Oficial UDEM)

### **RF-01: Validar e Instanciar Trama de Telemetría**
*   **Nombre:** Validar e Instanciar Trama de Telemetría
*   **Resumen:** **Actor:** Sensor / Operador de Vuelo. El sistema recibe los datos crudos de telemetría de una aeronave y valida tipos de datos, rangos y coherencia física antes de instanciar el objeto `TelemetriaDrone`.
*   **Entradas:** `id_dron` (str), `bateria` (float), `altitud` (float), `estado_motores` (str), `coordenadas` (tuple[float, float]).
*   **Resultado:** Objeto `TelemetriaDrone` correctamente creado con atributos privados y accesores protegidos.

---

### **RF-02: Notificar Excepciones de Dominio Específicas**
*   **Nombre:** Notificar Excepciones de Dominio
*   **Resumen:** **Actor:** Sistema / Operador. Al detectar cualquier violación a las reglas de negocio, el sistema interrumpe la operación de forma controlada y dispara la excepción correspondiente con un mensaje descriptivo del fallo.
*   **Entradas:** Parámetros inválidos pasados durante la creación o modificación de atributos.
*   **Resultado:** Disparo de `BateriaInvalidaError`, `AltitudInvalidaError`, `EstadoMotorInvalidoError` o `CoordenadaInvalidaError`.

---

### **RF-03: Calcular Distancia Ortodrómica a Destino**
*   **Nombre:** Calcular Distancia Ortodrómica a Destino
*   **Resumen:** **Actor:** Operador de Vuelo. Calcula la distancia geodésica en kilómetros entre la ubicación actual del dron y una coordenada objetivo utilizando la fórmula de Haversine.
*   **Entradas:** Coordenada objetivo `destino` como `(latitud, longitud)` (tuple[float, float]).
*   **Resultado:** Número flotante (`float`) representando la distancia estimada en kilómetros (km).

---

### **RF-04: Consultar Formato de Consola e Inspección Técnica**
*   **Nombre:** Consultar Formato de Consola e Inspección Técnica
*   **Resumen:** **Actor:** Operador de Monitoreo / Desarrollador. Proporciona representaciones formateadas legibles para la consola de operaciones (`__str__`) o representaciones técnicas precisas para depuración (`__repr__`).
*   **Entradas:** Ninguna (invocado sobre la instancia).
*   **Resultado:** Cadena de texto formateada con los datos consolidados del dron.

---

### **RF-05: Actualizar Datos de Flota bajo Demanda**
*   **Nombre:** Actualizar Telemetría de la Flota
*   **Resumen**: Permite al usuario consumir los datos reales de ubicación y estado de los 6 tipos de   drones al presionar un botón, actualizando la información del sistema sin ser en tiempo real continuo.
*   **Entradas**: Señal de clic del operador / Invocación del método de actualización.  
*   **Resultado**: Consumo de datos externos y actualización de los atributos de las instancias de los drones.

---

### **RF-06: Registrar Nuevo Usuario en el Sistema**
*   **Nombre** Registrar Nuevo Usuario
*   **Resumen**: Actor: Administrador / Sistema. Permite dar de alta a un nuevo usuario (cliente u operador) validando sus datos básicos y rol dentro de la plataforma.
*   **Entradas**: `id_usuario` (str), `nombre` (str), `rol` (str).
*   **Resultado**: Creación y almacenamiento de la entidad de usuario en el registro general, o disparo de excepción si el rol es inválido o el ID ya existe.

---

### **RF-07: Registrar Solicitud de Servicio**
*   **Nombre** Registrar Solicitud de Servicio
*   **Resumen**: Actor: Cliente / Operador. Permite ingresar una nueva solicitud de servicio al sistema especificando la categoría especializada requerida (Entrega Ligera, Carga Pesada, Vigilancia, Mapeo Topográfico, Inspección de Infraestructura o Búsqueda/Rescate) y los requerimientos geográficos o de carga de la misión.
*   **Entradas**: `id_solicitud` (str), `id_usuario` (str), `categoria_requerida` (str), `coordenada_destino` (tuple[float, float]), `peso_carga` (float, opcional según la categoría del dron).
*   **Resultado**: Almacenamiento de la solicitud en la base de datos interna con estado "PENDIENTE", adaptándose a si requiere transporte físico o procesamiento operativo.

---

### **RF-08: Cruzar Información y Asignar Dron (Sistema de Control)**
*   **Nombre** Cruzar Información y Asignar Dron
*   **Resumen**: Actor: Sistema de Control. Cruza de forma automatizada los datos del pedido pendiente, la disponibilidad de la flota y las 6 categorías especializadas para asignar el dron idóneo.
*   **Entradas**: `id_pedido` (str).
*   **Resultado**: Actualización del estado del pedido a ASIGNADO y enlace del id_dron correspondiente mediante la centralización del sistema de control, o disparo de excepción si no hay recursos disponibles.

---

### **RF-09: Gestionar Retorno obligatorio a la sede de la empresa Post-Misión**
*   **Nombre** Gestionar Retorno Obligatorio a Base
*   **Resumen**: Actor: Sistema de Control / Operador. Al finalizar o abortar una misión, el dron no se marca como disponible de inmediato; el sistema calcula la ruta y la distancia geodésica de retorno hacia las coordenadas fijas de la base central de la empresa en Medellín, bloqueando su disponibilidad hasta que la aeronave aterrice físicamente en la base.
*   **Entradas**: `id_dron` (str), `coordenadas_base_empresa` (tuple[float, float]).
*   **Resultado**: Cambio temporal del estado del dron a RETORNANDO, cálculo continuo de la distancia a la base, y cambio definitivo a STANDBY (disponible) únicamente cuando la aeronave alcance las coordenadas de la empresa.

---

### **RF-10: Calcular Tiempo Estimado de Vuelo (ETA)**
*   **Nombre** Nombre: Calcular Tiempo Estimado de Vuelo (ETA)
*   **Resumen**: Actor: Operador / Sistema de Control. Calcula el tiempo estimado en minutos que tardará una aeronave en llegar a su coordenada de destino, combinando la distancia ortodrómica (Fórmula de Haversine) y la velocidad promedio de crucero propia de la categoría del dron.
*   **Entradas**: `id_dron` (str), `coordenada_destino` (tuple[float, float]).
*   **Resultado**: Número flotante (float) que representa el tiempo estimado de llegada en minutos

---

### **RF-11: Geocodificar y Resolver Cartográficamente Direcciones Urbanas**
*   **Nombre:** Geocodificar y Resolver Cartográficamente Direcciones Urbanas
*   **Resumen:** **Actor:** Cliente / Sistema de Control. Permite ingresar solicitudes de servicio utilizando direcciones textuales de nomenclatura urbana convencional (calles, carreras, diagonales, transversales y cruces viales en el Valle de Aburrá) y resolverlas en coordenadas geodésicas `(latitud, longitud)` WGS84 mediante una cadena de contingencia multinivel (Esri ArcGIS, Google Maps, OpenStreetMap Nominatim y Catálogo Local Offline).
*   **Entradas:** `direccion` (str).
*   **Resultado:** Tupla `(latitud, longitud)` de coordenadas geodésicas validadas dentro del perímetro operativo del Valle de Aburrá, o disparo de `GeocodificacionError` / `CoordenadaInvalidaError`.

---

### **RF-12: Despachar Misiones y Ejecutar Comportamientos Polimórficos de Flota**
*   **Nombre:** Despachar Misiones y Ejecutar Comportamientos Polimórficos
*   **Resumen:** **Actor:** Operador de Torre de Control / Sistema de Control. Despacha una misión técnica o logística asociada a un pedido en estado `'ASIGNADO'`, inicializando telemetría nominal de despegue si se requiere, elevando la aeronave a 30 metros de altitud de crucero (`'EN_VUELO'`), invocando polimórficamente `dron.ejecutar_mision(pedido)` para que responda según sus aditamentos especializados, registrando el resultado técnico en la bitácora de auditoría y ordenando el retorno automático a la base central.
*   **Entradas:** `id_pedido` (str).
*   **Resultado:** Transición del pedido a `'EN_TRANSITO'` y posteriormente a `'COMPLETADO'`, emisión de registro `LogOperacion(MISION_COMPLETADA)` e inicio automático de retorno a base.

---

### **RF-13: Simular Cinemática de Vuelo Multi-Fase con Modulación Meteorológica**
*   **Nombre:** Simular Cinemática de Vuelo Multi-Fase con Modulación Meteorológica
*   **Resumen:** **Actor:** Simulador de Vuelo / Operador de Torre de Control. Integra temporalmente el avance físico continuo de la flota en vuelo sobre el espacio aéreo del Valle de Aburrá a partir de intervalos de tiempo discretos ($\Delta t$ medido mediante reloj monotónico de hardware `time.monotonic()`), modulando la velocidad según el viento y la lluvia obtenidos en tiempo real (Open-Meteo), interpolando waypoints geodésicos proporcionales, deduciendo batería polimórficamente y ejecutando aterrizaje forzoso inmediato en caso de descarga total ($0.0\%$).
*   **Entradas:** `delta_t` (float, opcional), `nombre_nodo` (str, opcional).
*   **Resultado:** Objeto estructurado `ResumenRefrescoFlota` con coordenadas intermedias actualizadas, odómetro acumulado, porcentaje de batería remanente, métricas climáticas vigentes y evento de auditoría.

---

### **RF-14: Monitorear Telemetría y Cartografía en Interfaz Gráfica Web Interactiva**
*   **Nombre:** Monitorear Telemetría y Cartografía en Interfaz Gráfica Web
*   **Resumen:** **Actor:** Operador de Vuelo / Administrador. Provee una interfaz web gráfica interactiva servida localmente vía HTTP y API REST, que renderiza la cartografía del Valle de Aburrá mediante Leaflet.js, representa la ubicación y estado de cada aeronave con simbología diferenciada por categoría, visualiza nodos climáticos, permite registrar pedidos con geocodificación automática y avanzar la simulación temporal bajo demanda.
*   **Entradas:** Peticiones HTTP del navegador web (`GET /`, `GET /api/estado`, `POST /api/pedidos`, `POST /api/refrescar`).
*   **Resultado:** Renderizado cartográfico interactivo, actualización visual del avance de la flota y paneles de telemetría y auditoría en tiempo real.