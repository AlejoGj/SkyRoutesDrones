# Módulo de Excepciones de Dominio Aeronáutico (`src/excepciones/`)

Taxonomía jerárquica de excepciones personalizadas para blindaje de reglas de negocio aeronáuticas, integridad sensorial de telemetría, control de ciclo de vida de la flota y resolución cartográfica en el Valle de Aburrá.

* **Responsables de Implementación:**
  * **Alejandro García Jiménez:** Excepciones de Telemetría Sensorial, Geodesia y Servicios de Geocodificación (`BateriaInvalidaError`, `AltitudInvalidaError`, `EstadoMotorInvalidoError`, `CoordenadaInvalidaError`, `GeocodificacionError` - HU-01).
  * **Juan Manuel Pava Higuita:** Excepciones del Ciclo de Vida y Flota de Aeronaves (`DronError`, `ActualizarEstadoDronError`, `EstadoDronDuplicadoError`, `AsignarTelemetriaError`, `TelemetriaNoAsignadaError`, `DestinoInvalidoError`, `CategoriaDronInvalidoError` - HU-03).
* **Historias de Usuario Vinculadas:** HU-01, HU-03
* **Requisitos Funcionales:** RF-01, RF-02, RF-03, RF-04, RF-05, RF-07, RF-08, RF-09, RF-10

---

## 1. Propósito y Alcance

El paquete `src/excepciones/` centraliza todos los errores de dominio del sistema SkyRoute bajo un modelo fuertemente tipado. Sus objetivos principales son:

1. **Blindaje de Reglas de Negocio Aeronáuticas:** Evitar que datos físicamente imposibles (batería negativa, altitud por encima del techo legal o motores apagados en vuelo estacionario) corrompan el estado del sistema.
2. **Jerarquización Semántica:** Distinguir entre fallos de hardware sensorial (`TelemetriaDrone`), errores de asignación y despacho en aeronaves (`DronError`) y fallas en servicios de localización (`GeocodificacionError`).
3. **Depuración Forense y Auditoría:** Cada excepción almacena los valores inválidos originales como atributos de instancia (`bateria_invalida`, `altitud_invalida`, `id_dron`, `parametro`, etc.), permitiendo que la torre de control y los logs de auditoría capturen la causa exacta del incidente sin parsear texto.
4. **Resiliencia en Capas Superiores:** Permitir que la interfaz gráfica web (`src/ui/`) y el centro de control (`src/control/`) capturen excepciones específicas para presentar advertencias amigables al usuario sin abortar la ejecución del servidor.

---

## 2. Taxonomía y Jerarquía de Clases

```
                                  +-------------------+
                                  |     Exception     | (Built-in Python)
                                  +-------------------+
                                            |
         +-----------------------+----------+----------+-----------------------+
         |                       |                     |                       |
+----------------------+ +---------------------+ +--------------------+ +--------------------+
| BateriaInvalidaError | | AltitudInvalidaError| |EstadoMotorInvalido | |CoordenadaInvalida  |
+----------------------+ +---------------------+ +--------------------+ +--------------------+
| - bateria_invalida   | | - altitud_invalida  | | - estado_motor_... | | - coordenada_inval |
+----------------------+ +---------------------+ +--------------------+ +--------------------+
         |                       |                     |                       |
+----------------------+         |                     |                       |
| GeocodificacionError |         |                     |                       |
+----------------------+         |                     |                       |
| - direccion          |         |                     |                       |
+----------------------+         |                     |                       |
                                 v                     v                       v
                      +-----------------------------------------------------------------+
                      |                            DronError                            |
                      +-----------------------------------------------------------------+
                      | - id_dron: str                                                  |
                      | - message: str                                                  |
                      | Prefijo formateado: "[Dron <id_dron>]: <message>"               |
                      +-----------------------------------------------------------------+
                                                        |
         +-------------------------+--------------------+-------------------------+
         |                         |                    |                         |
+----------------------+ +--------------------+ +---------------------+ +--------------------+
| ActualizarEstado...  | | EstadoDronDuplicado| | AsignarTelemetria...| | TelemetriaNo...    |
+----------------------+ +--------------------+ +---------------------+ +--------------------+
| - parametro          | | - estado_actual    | | - objeto_invalido   | | (sin telemetria)   |
+----------------------+ +--------------------+ +---------------------+ +--------------------+
         |                         |
+----------------------+ +--------------------+
| DestinoInvalidoError | | CategoriaDron...   |
+----------------------+ +--------------------+
| - destino            | | - categoria        |
|                      | | - categorias_perm. |
+----------------------+ +--------------------+
```

---

## 3. Catálogo Detallado de Excepciones

### 3.1 Excepciones de Telemetría Sensorial (Alejandro García Jiménez - HU-01)

| Excepción | Parámetros del Constructor | Condición de Disparo | Regla de Negocio / Normativa |
|---|---|---|---|
| `BateriaInvalidaError` | `bateria_invalida: float`, `message: str = None` | Carga de batería $< 0.0\%$ o $> 100.0\%$. | Estado químico de celdas LiPo. |
| `AltitudInvalidaError` | `altitud_invalida: float`, `message: str = None` | Altitud $< 0.0\text{ m}$ o $> 120.0\text{ m}$. | Límite máximo UAV de la Aerocivil colombiana (120 m AGL). |
| `EstadoMotorInvalidoError` | `estado_motor_invalido: str`, `message: str = None` | Estado no pertenece a `{'APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA'}` o hay altitud $> 0$ con motores apagados. | Coherencia física de sustentación aerodinámica. |
| `CoordenadaInvalidaError` | `coordenada_invalida: Any`, `message: str = None` | Formato distinto a tupla de 2 flotantes, latitud fuera de $[-90, 90]^\circ$, longitud fuera de $[-180, 180]^\circ$, o punto fuera de la geocerca metropolitana del Valle de Aburrá. | Estándar geodésico WGS84 y perímetro metropolitano. |

---

### 3.2 Jerarquía de Errores de Flota y Ciclo de Vuelo (Juan Manuel Pava Higuita - HU-03)

Todas las excepciones de aeronaves heredan de `DronError`, estandarizando los mensajes en consola y logs bajo el formato: `[Dron <id_dron>]: <mensaje_detallado>`.

| Excepción | Parámetros del Constructor | Atributos Propios | Condición de Disparo |
|---|---|---|---|
| `DronError` | `id_dron: str`, `message: str` | `id_dron`, `message` | Clase base abstracta/general para incidentes de aeronaves. |
| `ActualizarEstadoDronError` | `id_dron: str`, `parametro: str` | `parametro` | Intento de forzar un estado no permitido (ej. marcar fin de retorno cuando el dron aún se encuentra a $> 50\text{ m}$ de la base). |
| `EstadoDronDuplicadoError` | `id_dron: str`, `estado_actual: bool` | `estado_actual` | Llamada redundante para cambiar a un estado que ya está activo. |
| `AsignarTelemetriaError` | `id_dron: str`, `objeto_invalido: Any` | `objeto_invalido` | Se intenta vincular a la aeronave un objeto que no es una instancia de `TelemetriaDrone`. |
| `TelemetriaNoAsignadaError` | `id_dron: str` | `id_dron` | Se solicita cálculo de distancias, ETA o simulación cinemática sobre un dron sin enlace sensorial inicializado. |
| `DestinoInvalidoError` | `id_dron: str`, `destino: Any` | `destino` | El punto de destino suministrado al dron no corresponde a una tupla de coordenadas válida. |
| `CategoriaDronInvalidoError` | `id_dron: str`, `categoria: str`, `categorias_permitidas: tuple` | `categoria`, `categorias_permitidas` | La aeronave se registra con una categoría ajena al catálogo oficial de las 6 subclases autorizadas. |

---

### 3.3 Excepciones de Servicios Cartográficos (Alejandro García Jiménez)

| Excepción | Parámetros del Constructor | Atributos Propios | Condición de Disparo |
|---|---|---|---|
| `GeocodificacionError` | `direccion: str`, `message: str = None` | `direccion` | Fallo de conexión, dirección no encontrada o coordenadas resultantes fuera del perímetro metropolitano del Valle de Aburrá. |

---

## 4. Buenas Prácticas y Patrones de Captura

### 4.1 Captura Selectiva frente a Captura Genérica
Se prohíbe el uso de `except Exception:` sin propagación o registro en módulos de negocio. Se debe capturar siempre la excepción más específica:

```python
from src.excepciones.errores import (
    CoordenadaInvalidaError,
    BateriaInvalidaError,
    AltitudInvalidaError,
    EstadoMotorInvalidoError,
)
from src.telemetria.telemetria import TelemetriaDrone

try:
    telemetria = TelemetriaDrone(
        id_dron="DRON-TEST-01",
        bateria=105.0,  # Valor ilegal
        altitud=50.0,
        estado_motores="EN_VUELO",
        coordenadas=(6.2442, -75.5812)
    )
except BateriaInvalidaError as e:
    print(f"Alerta: Nivel de carga inválido detectado: {e.bateria_invalida}%")
except AltitudInvalidaError as e:
    print(f"Alerta: Altitud de vuelo prohibida: {e.altitud_invalida} m")
except CoordenadaInvalidaError as e:
    print(f"Alerta: Coordenada fuera de la geocerca metropolitana: {e.coordenada_invalida}")
```

### 4.2 Inspección Polimórfica mediante `DronError`
Dado que todos los errores de aeronaves heredan de `DronError`, los orquestadores pueden capturar la jerarquía completa extrayendo automáticamente el ID de la aeronave comprometida:

```python
from src.excepciones.errores import DronError

try:
    dron.finalizar_retorno_en_base()
except DronError as e:
    # Captura ActualizarEstadoDronError, EstadoDronDuplicadoError, etc.
    logger.error("Fallo operacional en aeronave %s: %s", e.id_dron, e)
```

---

## 5. Pruebas Unitarias y Cobertura

Las excepciones de este módulo son validadas exhaustivamente en toda la suite de pruebas del sistema:
* `src/telemetria/test_telemetria.py`: Valida `BateriaInvalidaError`, `AltitudInvalidaError`, `EstadoMotorInvalidoError` y `CoordenadaInvalidaError`.
* `src/geodesia/test_calculador.py`: Valida `CoordenadaInvalidaError` ante puntos fuera del Valle de Aburrá.
* `src/servicios/test_geocodificador.py`: Valida `GeocodificacionError` ante direcciones inexistentes o fuera de geocerca.
* `src/control/test_simulador.py`: Valida `TelemetriaNoAsignadaError` en el motor de cinemática de vuelo.

Para ejecutar todas las pruebas que verifican estas excepciones:
```bash
python -m unittest discover -s src -p "test*.py"
```
