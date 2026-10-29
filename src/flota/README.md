# Módulo de Flota y Aeronaves Especializadas (`src/flota/`)

Gestión integral del ciclo de vida de aeronaves, cinemática de despegue y retorno a base, telemetría atómica, herencia jerárquica, abstracción pura (`abc.ABC`) y despacho polimórfico para la flota aérea de SkyRoute en el Valle de Aburrá.

* **Responsables de Implementación:** Juan Manuel Pava Higuita y Valery Arboleda Ardila (Subclases de Flota) / Alejandro García Jiménez (Clase Base Dron y Módulo de Funcionamiento: Reloj, Simulador y Servicios)
* **Historias de Usuario Vinculadas:** HU-03, HU-04, HU-07, HU-08, HU-09, HU-10, HU-11
* **Requisitos Funcionales:** RF-04, RF-05, RF-07, RF-08, RF-09, RF-10

---

## 1. Propósito y Alcance

El paquete `src/flota/` modela la jerarquía técnica de aeronaves no tripuladas (drones). Sus responsabilidades comprenden:
1. Definir el contrato abstracto unificado (`Dron`) que impide la instanciación de aeronaves genéricas incompletas.
2. Implementar las **6 subclases especializadas**, encapsulando sus aditamentos únicos (cámaras térmicas, sensores LiDAR, tolvas refrigeradas, brazos electromecánicos, ultrasonido y altavoces SAR).
3. Gestionar los estados de vuelo y el ciclo de vida operacional sin recurrir a la teletransportación de coordenadas.
4. Evaluar polimórficamente el consumo energético diferenciado y la viabilidad de despegue para el circuito completo (**ida + retorno a base**).
5. Proveer fichas técnicas legibles (`__str__`) y representaciones de depuración técnica (`__repr__`).

---

## 2. Jerarquía de Clases y Arquitectura

```
                        +----------------------------+
                        |         Dron (ABC)         |
                        +----------------------------+
                        | - id_dron: str             |
                        | - modelo_aeronave: str     |
                        | - velocidad_promedio_kmh   |
                        | - kilometraje_total_km     |
                        | - disponible: bool         |
                        | - telemetria: Telemetria   |
                        | - calculador: ICalculador  |
                        +----------------------------+
                                      ^
        +-----------------------------+-----------------------------+
        |                             |                             |
+-------------------+       +-------------------+       +--------------------+
| DronEntregaLigera |       |  DronCargaPesada  |       |   DronVigilancia   |
+-------------------+       +-------------------+       +--------------------+
| tolva refrigerada |       | volumen m3        |       | camara optica MP   |
| suelta rapida     |       | rotores (4 a 16)  |       | vision nocturna    |
| tasa: 1.2% / km   |       | tasa: 2.5 + rot*0.1|      | tasa: 1.3% / km    |
+-------------------+       +-------------------+       +--------------------+
        |                             |                             |
+-------------------+       +-------------------+       +--------------------+
|     DronMapeo     |       |   DronInspeccion  |       |     DronRescate    |
+-------------------+       +-------------------+       +--------------------+
| sensor LiDAR      |       | zoom optico 30x   |       | camara termica FLIR|
| precision RTK cm  |       | sensor ultrasonico|       | altavoz SAR dB     |
| tasa: 1.4% / km   |       | tasa: 1.5% / km   |       | tasa: 2.0% / km    |
+-------------------+       +-------------------+       +--------------------+
```

---

## 3. Pilares de Programación Orientada a Objetos

### A. Herencia
Todas las subclases heredan formalmente de la clase base `Dron(ABC)` e invocan `super().__init__(...)` para inicializar identificador, modelo, cinemática, odómetro y calculador geodésico, evitando duplicación de código.

### B. Abstracción Formal (`abc.ABC`)
`Dron` no puede ser instanciado directamente (`TypeError: Can't instantiate abstract class Dron with abstract methods...`). Define tres métodos abstractos obligatorios:
* `ejecutar_mision(self, pedido) -> dict`: Configuración instrumental y despegue de la misión.
* `calcular_consumo_estimado(self, distancia_km: float) -> float`: Tasa polimórfica de gasto de batería por kilómetro.
* `inspeccionar_sistemas_especializados(self) -> str`: Diagnóstico de instrumental técnico en consola.

### C. Polimorfismo Dinámico
El sistema opera sobre cualquier aeronave a través de la interfaz común `Dron`. El consumo de batería se calcula dinámicamente según la morfología y peso de cada clase:

| Subclase | Categoría Oficial | Fórmula de Consumo (% Batería / km) | Instrumental Especializado |
| :--- | :--- | :--- | :--- |
| `DronEntregaLigera` | `ENTREGA_LIGERA` | $\text{distancia} \times 1.2$ | Tolva refrigerada y desacople electromecánico. |
| `DronCargaPesada` | `CARGA_PESADA` | $\text{distancia} \times (2.5 + (\text{rotores} \times 0.1))$ | Tolva industrial de alto volumen y 8 rotores. |
| `DronVigilancia` | `VIGILANCIA` | $\text{distancia} \times 1.3$ | Cámara de 48 MP, visión nocturna y transmisión a 5.8 GHz. |
| `DronMapeo` | `MAPEO_TOPOGRAFICO` | $\text{distancia} \times 1.4$ | Escáner láser LiDAR, GPS centimétrico RTK y disco SSD. |
| `DronInspeccion` | `INSPECCION_INFRAESTRUCTURA` | $\text{distancia} \times 1.5$ | Zoom óptico 30x y sensor ultrasónico de proximidad. |
| `DronRescate` | `BUSQUEDA_RESCATE` | $\text{distancia} \times 2.0$ | Cámara termográfica FLIR, kit de auxilios y altavoz SAR. |

### D. Encapsulamiento Defensivo
Aunque el lineamiento inicial del Sprint 2 restringía el uso de encapsulamiento, la integridad de dominio requirió la protección de atributos mediante prefijo simple (`_atributo`) y validaciones estrictas con `@property` y `@setter`. Esto previene tipos erróneos (booleanos camuflados como números, valores negativos en capacidad o potencia, y textos vacíos).

---

## 4. Ciclo de Vida Operacional y Métodos de Vuelo

### 1. Despegue y Autonomía de Circuito (`ejecutar_mision`)
A diferencia de un modelo simplificado donde el dron se teletransporta al destino, `Dron.ejecutar_mision` proporciona una lógica base funcional:
1. **Validación de Autonomía Completa:** Calcula la distancia de ida al destino más la distancia de retorno a la base Olaya Herrera (`6.219603, -75.586792`). Si la batería remanente no cubre ambos trayectos, el despegue se rechaza inmediatamente lanzando `ActualizarEstadoDronError`.
2. **Elevación y Motores:** Ajusta la altitud a 30.0 m y los motores a `'EN_VUELO'`.
3. **Conservación de Coordenadas:** La aeronave permanece en su punto de origen geográfico, permitiendo que el motor de simulación temporal desplace la posición progresivamente en pulsos discretos.
4. **Activación de Instrumental:** Las subclases extienden este método mediante `super().ejecutar_mision(pedido)` para registrar la activación de sus sensores particulares.

### 2. Arribo al Objetivo (`finalizar_mision_en_destino`)
Valida que el dron se encuentre en un radio métrico estricto del vertipuerto o cliente ($\le 0.05\text{ km} = 50\text{ m}$). Cambia el estado del pedido a `'COMPLETADO'`, archiva la referencia y activa automáticamente el protocolo de retorno a base.

### 3. Retorno y Aterrizaje en Base (`iniciar_retorno_base` y `finalizar_retorno_en_base`)
* `iniciar_retorno_base(coordenadas_base)`: Activa la bandera `retornando_a_base = True` y fija las coordenadas de la base central.
* `finalizar_retorno_en_base()`: Valida mediante Haversine que la aeronave esté a $\le 50\text{ m}$ de la base. Al confirmar la proximidad, apaga motores (`STANDBY`), fija altitud en `0.0 m` y restaura `disponible = True`.

### 4. Sobrecarga Híbrida en `actualizar_telemetria`
El método `actualizar_telemetria` admite recibir una instancia completa de `TelemetriaDrone` o los argumentos individuales (`bateria_o_telemetria, altitud, estado_motores, coordenadas`). Reutiliza atómicamente el objeto interno mediante `actualizar_trama()`, acumula el odómetro si hubo desplazamiento geodésico y registra una captura inmutable en `historial_telemetria`.

### 5. Estación de Mantenimiento y Recarga (`recargar_bateria`)
Permite reponer la batería de la aeronave cuando se encuentra estacionaria en base. Bloquea cualquier intento de recarga en vuelo y restaura la disponibilidad operativa si el porcentaje supera el umbral del 20.0%.

---

## 5. Prevención de Ciclos de Importación (PEP 563 / PEP 484)

Para resolver la dependencia circular entre `Dron` (que tipa a `Pedido` en `ejecutar_mision`) y `Pedido` (que tipa a `Dron` en `dron_asignado`), el módulo utiliza:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido
```

Esto permite al analizador estático y al IDE interpretar las firmas de métodos sin cargar los módulos en memoria antes de tiempo, eliminando cualquier error de importación circular en tiempo de ejecución.

---

## 6. Ejemplo de Uso

```python
from src.flota import DronEntregaLigera, DronVigilancia

# 1. Instanciar aeronaves especializadas
dron_medico = DronEntregaLigera(
    id_dron="DRON-ENT-01",
    modelo_aeronave="AeroCourier-V3",
    velocidad_promedio_kmh=65.0,
    capacidad_carga_kg=3.5,
    compartimento_refrigerado=True
)

dron_seguridad = DronVigilancia(
    id_dron="DRON-VIG-03",
    modelo_aeronave="SkyGuardian-Pro",
    velocidad_promedio_kmh=58.0,
    resolucion_camara_mp=48,
    vision_nocturna=True,
    frecuencia_transmision_ghz=5.8
)

# 2. Evaluación polimórfica de autonomía para una ruta de 12.5 km
consumo_medico = dron_medico.calcular_consumo_estimado(12.5)      # 12.5 * 1.2 = 15.0%
consumo_seguridad = dron_seguridad.calcular_consumo_estimado(12.5) # 12.5 * 1.3 = 16.25%

print(f"Consumo entrega ligera: {consumo_medico:.2f}%")
print(f"Consumo vigilancia: {consumo_seguridad:.2f}%")

# 3. Diagnóstico técnico en consola
print(dron_seguridad.inspeccionar_sistemas_especializados())
```

---

## 7. Pruebas Unitarias Asociadas

El módulo cuenta con cobertura total de pruebas unitarias en `src/flota/`:
* [`test_drones_transporte.py`](test_drones_transporte.py): Valida `DronEntregaLigera`, límites de sobrepeso y `DronCargaPesada`.
* [`test_dron_vigilancia.py`](test_dron_vigilancia.py): Comprueba resolución óptica, visión nocturna y enlace a 5.8 GHz.
* [`test_dron_mapeo.py`](test_dron_mapeo.py): Verifica sensor LiDAR, georreferenciación RTK y almacenamiento SSD.
* [`test_polimorfismo_consumo.py`](test_polimorfismo_consumo.py): Certifica que un trayecto idéntico genera consumos matemáticamente diferenciados en cada subclase.
