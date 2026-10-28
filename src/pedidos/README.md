# Módulo de Pedidos y Solicitudes de Servicio (`src/pedidos/`)

Modelado del ciclo de vida de misiones, requerimientos de transporte, destino geográfico dual (coordenadas geodésicas directas / dirección urbana textual) y vinculación con la flota aérea de SkyRoute en el Valle de Aburrá.

* **Responsables de Implementación:**
  * **Valery Arboleda Ardila:** Estructura de la Entidad `Pedido`, Control de Estados y Vinculación de Flota (HU-05).
  * **Alejandro García Jiménez:** Integración con Geocodificación Desacoplada y Normalización con Capas Superiores (HU-05, HU-06, HU-12).
* **Historias de Usuario Vinculadas:** HU-05, HU-06, HU-12
* **Requisitos Funcionales:** RF-06, RF-07, RF-08

---

## 1. Propósito y Alcance

El paquete `src/pedidos/` representa la unidad fundamental de demanda comercial y logística del sistema SkyRoute. Sus responsabilidades son:

1. **Modelar la Solicitud de Servicio:** Custodiar los parámetros requeridos para cada misión: usuario solicitante, categoría de aeronave exigida, masa de la carga útil en kilogramos y punto geográfico de destino.
2. **Soporte de Destino Geográfico Dual:** Permitir la creación de pedidos tanto mediante coordenadas explícitas `(latitud, longitud)` como mediante dirección urbana alfanumérica (`direccion_destino`), desacoplando la captura de pedidos de la resolución cartográfica externa.
3. **Control del Ciclo de Vida Operativo:** Administrar formalmente las transiciones entre los 5 estados del servicio: `'PENDIENTE'`, `'ASIGNADO'`, `'EN_TRANSITO'`, `'COMPLETADO'` y `'CANCELADO'`.
4. **Vinculación Atómica de Aeronave:** Enlazar la referencia del objeto `Dron` asignado por el centro de control, impidiendo la asignación de objetos incompatibles.
5. **Normalización Defensiva:** Validar que las categorías solicitadas pertenezcan estrictamente al catálogo oficial de las 6 subclases autorizadas y proteger los datos numéricos de carga útil.

---

## 2. Arquitectura y Relaciones del Modelo

```
+------------------------------------+
|              Usuario               |
+------------------------------------+
| - id_usuario: str                  |
| - nombre: str                      |
| - rol: str                         |
+------------------------------------+
                  ^
                  | 1 (solicitante)
                  |
+------------------------------------+              +------------------------------------+
|               Pedido               |              |                Dron                |
+------------------------------------+              +------------------------------------+
| - id_pedido: str                   |              | - id_dron: str                     |
| - usuario_solicitante: Usuario     |              | - modelo_aeronave: str             |
| - categoria_requerida: str         | 1          1 | - telemetria: TelemetriaDrone      |
| - categoria: str (alias)           |------------->| - pedido_activo: Pedido            |
| - coordenada_destino: tuple | None | (asignado)   | - coordenadas_base: tuple          |
| - direccion_destino: str | None    |              +------------------------------------+
| - peso_carga_kg: float             |
| - estado: str                      |
| - dron_asignado: Dron | None       |
+------------------------------------+
```

---

## 3. Catálogo de Atributos y Constantes de Clase

### 3.1 Constantes de Clase
* `categorias_permitidas: list[str]`:
  * `'ENTREGA_LIGERA'`
  * `'CARGA_PESADA'`
  * `'VIGILANCIA'`
  * `'MAPEO_TOPOGRAFICO'`
  * `'INSPECCION_INFRAESTRUCTURA'`
  * `'BUSQUEDA_RESCATE'`
* `estados_permitidos: list[str]`:
  * `'PENDIENTE'`: Pedido registrado en el sistema a la espera de una aeronave compatible y con batería suficiente.
  * `'ASIGNADO'`: Aeronave enlazada exitosamente por el centro de control; pedido reservado para despegue.
  * `'EN_TRANSITO'`: Aeronave en vuelo hacia las coordenadas de destino.
  * `'COMPLETADO'`: Misión técnica o entrega de carga finalizada exitosamente en el punto de destino.
  * `'CANCELADO'`: Misión abortada por contingencia climática, solicitud del usuario o inviabilidad técnica.

### 3.2 Atributos de Instancia

| Atributo | Tipo | Descripción |
|---|---|---|
| `id_pedido` | `str` | Identificador único alfanumérico no vacío del encargo. |
| `usuario_solicitante` | `Usuario` | Objeto válido de la clase `Usuario` que originó la petición. |
| `categoria_requerida` | `str` | Categoría en mayúsculas de la aeronave requerida. |
| `categoria` | `str` | Alias directo de `categoria_requerida` para interoperabilidad de pruebas y flota. |
| `coordenada_destino` | `tuple[float, float] \| None` | Tupla `(latitud, longitud)` en grados decimales WGS84. |
| `direccion_destino` | `str \| None` | Dirección urbana textual en el Valle de Aburrá (ej. *"Calle 30A # 82A-26"*). |
| `peso_carga_kg` | `float` | Masa de la carga a transportar (mínimo `0.0 kg`). |
| `estado` | `str` | Estado actual del pedido dentro del ciclo de vida permitido. |
| `dron_asignado` | `Dron \| None` | Instancia de la aeronave adjudicada para la operación (o `None`). |

---

## 4. Evolución Técnica frente al Diseño Original de la HU-05

| Elemento | Especificación Original (Sprint 1) | Implementación Real en Producción | Justificación de Ingeniería |
|---|---|---|---|
| **Punto de Destino** | Parámetro obligatorio `coordenada_destino` tipo tupla. | Destino dual: admite `coordenada_destino` o `direccion_destino`. | Los usuarios reales ingresan direcciones alfanuméricas. Se desacopla la creación del pedido de la geocodificación. |
| **Alias de Categoría** | Solo existía `categoria_requerida`. | Soporta tanto `categoria_requerida` como `categoria`. | Garantiza compatibilidad retroactiva con algoritmos de asignación y pruebas unitarias heterogéneas. |
| **Protección Booleana en Peso** | Validación numérica simple. | `if isinstance(peso_carga_kg, bool) ... raise TypeError`. | En Python `bool` hereda de `int` (`isinstance(True, int) == True`). La comprobación explícita previene pasar flags lógicas como peso. |
| **Validación de Tupla Geodésica** | Se asumía tupla válida. | Valida tamaño exacto de 2 elementos y tipos numéricos `(int, float)`. | Previene fallos en tiempo de ejecución al invocar el motor trigonométrico Haversine. |
| **Ciclo de Vida** | Estados `'PENDIENTE'` y `'ASIGNADO'`. | 5 estados formales (`PENDIENTE`, `ASIGNADO`, `EN_TRANSITO`, `COMPLETADO`, `CANCELADO`). | Requerido para soportar la simulación física multi-fase y el monitoreo en tiempo real de la UI web. |
| **Representaciones** | No especificadas. | Sobrescritura de `__str__` y `__repr__` informando dron y estado de geocodificación. | Facilita la auditoría en consola, registros de bitácora y depuración de pruebas. |

---

## 5. Guía de Uso

### 5.1 Creación con Coordenadas Geodésicas Directas
```python
from src.usuarios.usuario import Usuario
from src.pedidos.pedido import Pedido

cliente = Usuario(id_usuario="USR-01", nombre="Hospital General", rol="CLIENTE")

pedido_coordenadas = Pedido(
    id_pedido="PED-001",
    usuario_solicitante=cliente,
    categoria_requerida="ENTREGA_LIGERA",
    coordenada_destino=(6.2341, -75.5682),
    peso_carga_kg=1.5
)
print(pedido_coordenadas)
# Pedido [PED-001] - Cat: ENTREGA_LIGERA - Estado: PENDIENTE - Dron: Sin asignar - Destino: (6.2341, -75.5682)
```

### 5.2 Creación con Dirección Textual (Geocodificación Diferida)
```python
pedido_direccion = Pedido(
    id_pedido="PED-002",
    usuario_solicitante=cliente,
    categoria_requerida="BUSQUEDA_RESCATE",
    direccion_destino="Universidad de Medellin, Belen",
    peso_carga_kg=0.0
)
print(pedido_direccion)
# Pedido [PED-002] - Cat: BUSQUEDA_RESCATE - Estado: PENDIENTE - Dron: Sin asignar - Destino: 'Universidad de Medellin, Belen' (Pendiente Geocodificación)
```

---

## 6. Pruebas Unitarias y Cobertura

La entidad `Pedido` se valida en múltiples suites del proyecto:
* `src/servicios/test_geocodificador.py`: Valida el flujo de pedidos creados con dirección textual y resueltos por la torre de control.
* `src/flota/test_drones_transporte.py`: Valida el rechazo por sobrepeso en `DronEntregaLigera` según el `peso_carga_kg` del pedido.
* `src/control/test_simulador.py`: Valida las transiciones de estado de `Pedido` durante el despacho, vuelo y finalización de misión.

Para ejecutar todas las pruebas unitarias:
```bash
python -m unittest discover -s src -p "test*.py"
```
