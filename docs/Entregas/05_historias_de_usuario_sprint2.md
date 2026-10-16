# Documento 05: Historias de Usuario y Plan de Trabajo (Sprint 2)

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  
**Semestre:** 2026-2  
**Docente:** Mario Alejandro Saldarriaga (Grupo 62)  
**Equipo:** Alejandro García Jiménez, Juan Manuel Pava Higuita, Valery Arboleda Ardila  

---

## 1. Lineamientos Técnicos del Sprint 2: "Herencia, Polimorfismo y Abstracción"

> **REGLAS DE ARQUITECTURA PARA LA ENTREGA #2:**  
> En esta segunda entrega se habilita formalmente la aplicación de **tres de los cuatro pilares de la POO**, manteniendo una restricción explícita:
>
> * ✔️ **Herencia:** Implementación de la jerarquía completa del modelo del mundo. La clase `Dron` pasa a ser la clase base común, y de ella heredan las 6 subclases especializadas reutilizando atributos y métodos generales mediante `super().__init__(...)`.
> * ✔️ **Abstracción Formal:** Uso obligatorio del módulo estándar `abc` (`from abc import ABC, abstractmethod`). La clase `Dron` se declara como clase abstracta base y define métodos abstractos que obligan a cada subclase a implementar su propia lógica. Queda prohibido instanciar directamente la clase abstracta `Dron`.
> * ✔️ **Polimorfismo:** Despacho dinámico y sobrescritura de métodos. Cada tipo de dron implementará con comportamiento propio los métodos abstractos (`ejecutar_mision`, `calcular_consumo_estimado`, `inspeccionar_sistemas_especializados`). El `SistemaCentroControl` y `Pedido` interactúan polimórficamente con cualquier aeronave sin necesidad de validar cadenas de texto con `if/elif`.
> * ❌ **EXCEPCIÓN - Cero Encapsulamiento:** En esta entrega **NO** se utilizará encapsulamiento; los atributos se gestionan directamente (`self.atributo = valor`) sin atributos privados (`__`) ni getters o setters (`@property`).

---

## 2. Matriz de Distribución Equitativa del Trabajo (Sprint 2)

Para mantener el reparto del 33.3% por integrante, las 6 subclases especializadas y los componentes de abstracción y polimorfismo se distribuyen equitativamente (2 subclases de drones por colaborador):

| Integrante | Módulo Asignado | Subclases y Componentes Clave | Responsabilidad Técnica |
|---|---|---|---|
| **Alejandro García Jiménez** | **Módulo 1:** Abstracción Base y Drones de Monitoreo | `Dron(ABC)` (Base Abstracta), `DronVigilancia`, `DronMapeo` | Definir el contrato abstracto de la flota y construir las aeronaves sensoriales y cartográficas. |
| **Juan Manuel Pava Higuita** | **Módulo 2:** Drones de Transporte y Consumo Polimórfico | `DronEntregaLigera`, `DronCargaPesada`, Consumo Energético | Implementar la logística de carga, límites de peso/volumen y despacho dinámico de consumo. |
| **Valery Arboleda Ardila** | **Módulo 3:** Drones de Asistencia y Orquestador Polimórfico | `DronInspeccion`, `DronRescate`, Fábrica y Despacho en `SistemaCentroControl` | Desarrollar aeronaves técnicas/rescate y actualizar el centro de control para operar polimórficamente. |

---

## 3. Metodología de Trabajo

---

El equipo mantendrá el mismo flujo disciplinado de trabajo en Git acordado en el Sprint 1:

### 3.1 Creación de Ramas por Historia de Usuario (HU)
* Cada integrante trabajará en una **rama independiente** creada a partir de la rama principal (`main`).
* **Regla estricta:** Prohibido realizar commits directos sobre `main`.
* **Nomenclatura estándar de ramas para el Sprint 2:**
  * `feature/HU-07-dron-abstracto` (Alejandro)
  * `feature/HU-08-drones-vigilancia-mapeo` (Alejandro)
  * `feature/HU-09-drones-transporte-carga` (Juan Manuel)
  * `feature/HU-10-polimorfismo-consumo-str` (Juan Manuel)
  * `feature/HU-11-drones-inspeccion-rescate` (Valery)
  * `feature/HU-12-orquestacion-polimorfica-centro-control` (Valery)

### 3.2 Commits Atómicos y Testeo Previo
* **Commits por funcionalidad:** Realizar commits pequeños y específicos tras implementar cada clase, método abstracto o prueba unitaria.
* **Testeo sencillo previo:** Antes de hacer cada `git commit`, verificar localmente (mediante pruebas o scripts de consola) que las instancias de las subclases hereden correctamente y que los métodos abstractos se ejecuten sin romper el sistema.
* **Mensajes descriptivos:** Redactar mensajes en formato semántico (ej. `feat(flota): implementar DronVigilancia con sobrescritura de ejecutar_mision`).

### 3.3 Creación de Pull Request (PR) con Descripción Relevante
* Al finalizar el To-Do list de la HU, el desarrollador subirá su rama remota (`git push origin <rama>`) y creará el Pull Request hacia `main`.
* El PR debe detallar:
  1. Qué HU y subclases atiende.
  2. Qué métodos abstractos fueron implementados y cómo responden polimórficamente.
  3. Pruebas ejecutadas que demuestran la herencia funcional.

### 3.4 Revisión y Aceptación Obligatoria del PR por parte de Alejandro
* Ningún colaborador fusiona su propio código a `main`.
* **Alejandro García Jiménez** revisa el PR verificando:
  * Cumplimiento estricto de **Herencia, Polimorfismo y Abstracción**.
  * Invocación correcta de `super().__init__(...)` en los constructores hijos.
  * Aprobación formal y merge hacia `main`.

---

## 4. Historias de Usuario Detalladas y To-Do Lists (Sprint 2)

---

### Responsable 1: Alejandro García Jiménez
**Módulo:** Abstracción Base y Drones de Monitoreo / Cartografía

#### HU-07: Transformación de Dron en Clase Abstracta Base (ABC)
* **Como:** Arquitecto de software del sistema SkyRoute.
* **Quiero:** Convertir la clase `Dron` en una clase abstracta pura mediante el módulo `abc` y definir los métodos abstractos obligatorios para la flota.
* **Para:** Impedir que se instancien drones genéricos sin especialización y garantizar un contrato uniforme para el polimorfismo del sistema.
* **RF Vinculados:** `RF-03`, `RF-04`, `RF-09`, `RF-10`

##### Criterios de Aceptación:
1. La clase `Dron` hereda formalmente de `abc.ABC`.
2. Intentar hacer `Dron(...)` directamente dispara obligatoriamente `TypeError: Can't instantiate abstract class Dron with abstract methods...`.
3. Se definen formalmente los siguientes métodos decorados con `@abstractmethod`:
   * `ejecutar_mision(self, pedido) -> dict`: Define cómo la aeronave lleva a cabo el encargo según su equipamiento.
   * `calcular_consumo_estimado(self, distancia_km: float) -> float`: Retorna el porcentaje de batería que consumirá según su peso y diseño.
   * `inspeccionar_sistemas_especializados(self) -> str`: Retorna el diagnóstico técnico del instrumental propio de la aeronave.
4. Mantiene los métodos comunes no abstractos (`iniciar_retorno_base`, `calcular_distancia_a_destino`, `estimar_tiempo_llegada_min`, `asignar_telemetria`).

##### To-Do List:
- [ ] Modificar `src/flota/dron.py` importando `from abc import ABC, abstractmethod`.
- [ ] Declarar `class Dron(ABC):`.
- [ ] Declarar los métodos abstractos `@abstractmethod` para `ejecutar_mision`, `calcular_consumo_estimado` e `inspeccionar_sistemas_especializados`.
- [ ] Validar que las funciones comunes sigan disponibles para todas las futuras subclases.

---

#### HU-08: Implementación de Subclases de Monitoreo y Cartografía (`DronVigilancia` y `DronMapeo`)
* **Como:** Operador de seguridad y topografía urbana.
* **Quiero:** Contar con las subclases `DronVigilancia` y `DronMapeo` que hereden de `Dron` e incorporen su instrumental técnico específico.
* **Para:** Realizar misiones de escolta de cargamentos y levantamiento tridimensional de laderas y vertipuertos en Medellín.
* **RF Vinculados:** `RF-07`, `RF-08`

##### Criterios de Aceptación:
1. `DronVigilancia` hereda de `Dron`.
   * Atributos propios: `resolucion_camara_mp: int`, `vision_nocturna: bool`, `frecuencia_transmision_ghz: float`.
   * Invoca `super().__init__(...)` asignando su categoría fija `'VIGILANCIA'`.
   * Implementa `ejecutar_mision`: Simula transmisión de video cifrado y escolta aérea.
   * Implementa `inspeccionar_sistemas_especializados`: Reporta estado de cámaras y visión nocturna.
2. `DronMapeo` hereda de `Dron`.
   * Atributos propios: `tiene_sensor_lidar: bool`, `precision_gps_cm: float`, `capacidad_almacenamiento_tb: float`.
   * Invoca `super().__init__(...)` asignando su categoría fija `'MAPEO_TOPOGRAFICO'`.
   * Implementa `ejecutar_mision`: Simula escaneo de nubes de puntos 3D.
   * Implementa `inspeccionar_sistemas_especializados`: Reporta estado del sensor LiDAR y disco de memoria.

##### To-Do List:
- [ ] Crear el módulo o clases para `DronVigilancia` y `DronMapeo` en el paquete de flota.
- [ ] Implementar constructor con `super().__init__(...)` y atributos específicos.
- [ ] Implementar sobrescritura concreta de los 3 métodos abstractos en ambas clases.
- [ ] Escribir prueba unitaria que valide que ambas clases se puedan instanciar sin error de abstracción.

---

### Responsable 2: Juan Manuel Pava Higuita
**Módulo:** Drones de Transporte y Consumo Polimórfico

#### HU-09: Implementación de Subclases de Transporte (`DronEntregaLigera` y `DronCargaPesada`)
* **Como:** Coordinador de despachos logísticos.
* **Quiero:** Desarrollar las clases `DronEntregaLigera` y `DronCargaPesada` heredando de `Dron`, gestionando límites físicos de carga y mecanismos de transporte.
* **Para:** Despachar medicamentos urgentes de última milla y suministros industriales entre bodegas del Valle de Aburrá.
* **RF Vinculados:** `RF-07`, `RF-08`

##### Criterios de Aceptación:
1. `DronEntregaLigera` hereda de `Dron`.
   * Atributos propios: `peso_maximo_paquete_kg: float`, `compartimento_refrigerado: bool`, `mecanismo_suelta_rapida: bool`.
   * Invoca `super().__init__(...)` con categoría fija `'ENTREGA_LIGERA'`.
   * Valida que si el pedido excede `peso_maximo_paquete_kg`, la misión sea rechazada con advertencia controlada.
   * Implementa `ejecutar_mision`: Simula apertura de compartimento térmico y entrega al cliente.
2. `DronCargaPesada` hereda de `Dron`.
   * Atributos propios: `volumen_carga_m3: float`, `numero_rotores: int`, `potencia_remolque_w: float`.
   * Invoca `super().__init__(...)` con categoría fija `'CARGA_PESADA'`.
   * Implementa `ejecutar_mision`: Simula enganche de contenedor pesado y traslado inter-bodegas.

##### To-Do List:
- [ ] Crear las clases `DronEntregaLigera` y `DronCargaPesada` heredando de `Dron`.
- [ ] Invocar constructores padre con `super().__init__(...)`.
- [ ] Implementar la sobrescritura de `ejecutar_mision` y `inspeccionar_sistemas_especializados`.
- [ ] Agregar validación de sobrepeso en `DronEntregaLigera` basada en el peso del pedido.

---

#### HU-10: Polimorfismo en Consumo Energético y Fichas Técnicas Multilínea
* **Como:** Jefe de mantenimiento y telemetría de flota.
* **Quiero:** Que cada dron calcule su consumo de batería de forma diferenciada según su morfología y que la ficha técnica (`__str__`) muestre sus aditamentos únicos.
* **Para:** Predecir con precisión si la batería soportará la misión antes de despegar y visualizar claramente las especificaciones en consola.
* **RF Vinculados:** `RF-04`, `RF-10`

##### Criterios de Aceptación:
1. Sobrescribir `calcular_consumo_estimado(distancia_km)` en `DronEntregaLigera`:
   * Fórmula polimórfica liviana: `consumo = distancia_km * 1.2` (% de batería por km).
2. Sobrescribir `calcular_consumo_estimado(distancia_km)` en `DronCargaPesada`:
   * Fórmula polimórfica pesada: `consumo = distancia_km * (2.5 + (numero_rotores * 0.1))` (% mayor por arrastre y rotores).
3. Sobrescribir `__str__` en las subclases:
   * Aprovecha `super().__str__()` y anexa en formato limpio las características especializadas (volumen, refrigeración, cámaras, etc.).

##### To-Do List:
- [ ] Implementar la lógica matemática diferenciada de consumo en `DronEntregaLigera` y `DronCargaPesada`.
- [ ] Extender `__str__` y `__repr__` en las subclases usando `super()`.
- [ ] Validar que un mismo viaje de 10 km calcule consumos notablemente distintos entre el dron de carga y el dron ligero demostrando polimorfismo.

---

### Responsable 3: Valery Arboleda Ardila
**Módulo:** Drones de Asistencia y Orquestador Polimórfico

#### HU-11: Implementación de Subclases de Infraestructura y Rescate (`DronInspeccion` y `DronRescate`)
* **Como:** Jefe de contingencias y soporte de vertipuertos.
* **Quiero:** Construir las subclases `DronInspeccion` y `DronRescate` con equipamiento para mantenimiento técnico y respuesta inmediata ante fallas.
* **Para:** Diagnosticar plataformas de aterrizaje y acudir a coordenadas de emergencia donde un dron haya realizado un aterrizaje forzoso.
* **RF Vinculados:** `RF-07`, `RF-08`, `RF-09`

##### Criterios de Aceptación:
1. `DronInspeccion` hereda de `Dron`.
   * Atributos propios: `zoom_optico_x: int`, `rango_sensor_ultrasonico_m: float`.
   * Invoca `super().__init__(...)` con categoría fija `'INSPECCION_INFRAESTRUCTURA'`.
   * Implementa `ejecutar_mision`: Simula vuelo estacionario a distancia segura por ultrasonido escaneando antenas o vertipuertos.
2. `DronRescate` hereda de `Dron`.
   * Atributos propios: `camara_termica: bool`, `kit_auxilios_equipado: bool`, `potenciaAltavozDb: int`.
   * Invoca `super().__init__(...)` con categoría fija `'BUSQUEDA_RESCATE'`.
   * Implementa `ejecutar_mision`: Simula barrido térmico y activación de altavoz acústico en coordenadas de emergencia.

##### To-Do List:
- [ ] Crear las clases `DronInspeccion` y `DronRescate` heredando de `Dron`.
- [ ] Implementar `super().__init__(...)` y atributos especializados.
- [ ] Sobrescribir `ejecutar_mision`, `calcular_consumo_estimado` y `inspeccionar_sistemas_especializados`.
- [ ] Crear pruebas de instanciación y ejecución de misiones de inspección y rescate.

---

#### HU-12: Orquestación Polimórfica y Despacho de Misiones en Centro de Control
* **Como:** Operador principal de la Torre de Control SkyRoute.
* **Quiero:** Que el `SistemaCentroControl` asigne y despache misiones de manera polimórfica tratando a cualquier aeronave a través de su interfaz común `Dron`.
* **Para:** Eliminar bifurcaciones rígidas (`if/elif`) por modelo de dron y permitir que el sistema ejecute misiones de cualquier categoría transparentemente.
* **RF Vinculados:** `RF-05`, `RF-08`, `RF-09`

##### Criterios de Aceptación:
1. Incorporar el método `despachar_mision(id_pedido: str) -> bool` en `SistemaCentroControl`:
   * Localiza el pedido en estado `'ASIGNADO'`.
   * Invoca polimórficamente `resultado = pedido.dron_asignado.ejecutar_mision(pedido)`.
   * Cambia el estado del pedido a `'EN_TRANSITO'` y luego a `'COMPLETADO'`.
   * Registra el resultado de la misión especializada en `historial_logs`.
2. Actualizar la verificación en `asignar_dron_a_pedido` para comprobar compatibilidad mediante un método polimórfico de dron (ej. `dron.puede_atender_pedido(pedido)`) o compatibilidad de subclase.
3. Crear un registro de fábrica (`FABRICA_DRONES`) para instanciar subclases a partir de un identificador o solicitud.

##### To-Do List:
- [ ] Implementar el método `despachar_mision(id_pedido)` en `SistemaCentroControl`.
- [ ] Integrar el llamado dinámico a `ejecutar_mision(...)` sin importar qué subclase de dron esté asignada.
- [ ] Registrar log de auditoría con los detalles técnicos devueltos por la misión polimórfica.
- [ ] Actualizar el ciclo de retorno post-despacho vinculando el fin de la misión con `gestionar_retorno_a_base`.

---

## 5. Plan de Integración y Validación Conjunta (Fin del Sprint 2)

Al finalizar el Sprint 2, el equipo integrará las 6 subclases en `src/main.py` para una demostración integral de los pilares de POO aplicados:

### Checklist de Prueba Conjunta:
- [ ] **Paso 1 (Comprobación de Abstracción):** Verificar que intentar instanciar `Dron(...)` directamente lance `TypeError`, confirmando que la clase base es estrictamente abstracta.
- [ ] **Paso 2 (Instanciación de la Flota Completa):** Instanciar al menos una aeronave de cada una de las 6 subclases especializadas con sus respectivos atributos propios.
- [ ] **Paso 3 (Registro en Torre de Control):** Agregar los 6 drones a una instancia de `SistemaCentroControl` y verificar que la lista polimórfica `self.flota_drones: list[Dron]` acepte a todas las subclases transparentemente.
- [ ] **Paso 4 (Demostración de Polimorfismo en Consumo):** Calcular el consumo estimado de un trayecto idéntico (ej. 15 km) para cada dron y comprobar que cada clase arroje resultados diferentes según su diseño.
- [ ] **Paso 5 (Despacho Polimórfico de Misiones):** Crear pedidos de distintas categorías (un paquete médico urgente, una inspección de antena y un rescate térmico), asignarlos y despacharlos mediante `centro_control.despachar_mision()`, constatando que cada uno ejecute su comportamiento especializado y genere su log de auditoría.
- [ ] **Paso 6 (Inspección de Fichas Técnicas):** Imprimir con `print(dron)` cada aeronave y comprobar que la representación `__str__` muestre ordenadamente los aditamentos especializados de cada clase.
