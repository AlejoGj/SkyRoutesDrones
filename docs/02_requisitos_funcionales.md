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
5. **Coordenadas Geográficas (`coordenadas`):** Tupla de dos números reales `(latitud, longitud)` con latitud en `[-90.0, 90.0]` y longitud en `[-180.0, 180.0]`.
6. **Cálculo Geodésico:** La distancia a un destino geográfico se calcula mediante la fórmula de Haversine asumiendo un radio terrestre de 6371.0 km.

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