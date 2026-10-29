# Módulo de Geodesia y Navegación Espacial (`src/geodesia/`)

Núcleo matemático para el cálculo de distancias ortodrómicas, validación de geocercas operativas del Valle de Aburrá, estimación de tiempos de vuelo (ETA) e interpolación de posiciones intermedias para la flota de aeronaves SkyRoute.

* **Responsable de Implementación:** Alejandro García Jiménez
* **Historias de Usuario Vinculadas:** HU-01, HU-02
* **Requisitos Funcionales:** RF-01, RF-02, RF-03, RF-10

---

## 1. Propósito y Alcance

El módulo centraliza las operaciones geográficas y trigonométricas del sistema, garantizando que:
1. Ninguna aeronave opere o planifique misiones fuera del espacio aéreo autorizado del Valle de Aburrá.
2. Todas las mediciones métricas utilicen la formulación esférica de Haversine con un radio terrestre nominal uniforme de **6371.0 km**.
3. El motor de simulación temporal disponga de funciones de interpolación continua de waypoints para modelar el desplazamiento en vuelo y georreferenciar aterrizajes de emergencia.

---

## 2. Delimitación Geográfica Oficial (Geocerca)

Las operaciones del sistema están estrictamente enclavadas en las coordenadas del Área Metropolitana del Valle de Aburrá:

| Parámetro | Límite Mínimo | Límite Máximo | Notación Geográfica |
| :--- | :--- | :--- | :--- |
| **Latitud Norte** | `5.9667` | `6.5000` | 5°58' N a 6°30' N (Caldas a Barbosa) |
| **Longitud Oeste** | `-75.7167` | `-75.3500` | 75°43' W a 75°21' W |

Cualquier coordenada que viole este cuadrante es rechazada lanzando la excepción de dominio `CoordenadaInvalidaError`.

---

## 3. Arquitectura y Contratos de Código

El módulo implementa un diseño basado en contratos desacoplados mediante `typing.Protocol`:

```
src/geodesia/
├── __init__.py           # Exporta ICalculadorGeodesico y CalculadorGeodesico
├── calculador.py         # Definición del Protocolo, constantes de geocerca e implementación
└── test_calculador.py    # Suite de pruebas unitarias sobre corredores viales reales
```

### Protocolo `ICalculadorGeodesico`

Define la interfaz estructural para cualquier motor de navegación o cálculo espacial:

```python
class ICalculadorGeodesico(Protocol):
    LAT_MIN_ABURRA: float = 5.9667
    LAT_MAX_ABURRA: float = 6.5000
    LON_MIN_ABURRA: float = -75.7167
    LON_MAX_ABURRA: float = -75.3500
    radio_tierra_km: float

    def validar_coordenada(self, coordenada: tuple[float, float]) -> None: ...
    def calcular_haversine(self, origen: tuple[float, float], destino: tuple[float, float]) -> float: ...
    def calcular_tiempo_vuelo_min(self, distancia_km: float, velocidad_km_h: float) -> float: ...
    def calcular_punto_intermedio(self, origen: tuple[float, float], destino: tuple[float, float], fraccion: float) -> tuple[float, float]: ...
```

---

## 4. Evolución de Diseño y Decisiones Técnicas

Durante la integración con los módulos de simulación física y telemetría, se incorporaron decisiones de ingeniería que refinaron los requerimientos iniciales de las HU:

### A. Desacoplamiento de Geocerca (Principio de Responsabilidad Única - SRP)
* **Requerimiento inicial en HU-01:** Proponía que `TelemetriaDrone.validar_datos()` validara directamente la geocerca metropolitana del Valle de Aburrá.
* **Implementación real:** `TelemetriaDrone` se mantuvo agnóstico a jurisdicciones operativas locales, validando únicamente límites geométricos físicos WGS84 (`[-90.0, 90.0]`, `[-180.0, 180.0]`). La validación del perímetro del Valle de Aburrá fue centralizada en `CalculadorGeodesico.validar_coordenada()`, evitando acoplar una entidad de sensor/hardware a un área territorial específica.

### B. Blindaje de Estabilidad en Punto Flotante IEEE 754
En la fórmula de Haversine:
$$\Delta\sigma = 2 \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
Donde $a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$.
* Para evitar que imprecisiones de redondeo computacional causen $a > 1.0$ (lo que produciría `ValueError: math domain error` al evaluar $\sqrt{1 - a}$ ante coordenadas idénticas o extremadamente cercanas), se implementó un enclavamiento estricto:
  ```python
  a = max(0.0, min(1.0, a))
  ```

### C. Incorporación de Interpolación de Posición (`calcular_punto_intermedio`)
* **Necesidad:** El motor de simulación temporal (`SimuladorVuelo`) requería actualizar de forma continua y suave la posición GPS de las aeronaves a lo largo de cada pulso temporal, así como determinar el punto exacto de aterrizaje forzoso si la batería llegaba a `0.0%`.
* **Solución:** Se implementó `calcular_punto_intermedio(origen, destino, fraccion)` con verificación de geocerca en el punto resultante y redondeo a 6 decimales.

### D. Protección Defensiva en Estimador de Tiempo (ETA)
* La función `calcular_tiempo_vuelo_min()` retorna `0.0` min si `velocidad_km_h <= 0.0` o `distancia_km <= 0.0`, protegiendo el sistema contra divisiones por cero o velocidades regresivas.

---

## 5. API y Métodos Principales

| Método | Entrada | Salida | Excepciones | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `validar_coordenada(coordenada)` | `tuple[float, float]` | `None` | `CoordenadaInvalidaError` | Valida tipo, tupla de 2 elementos numéricos y límites del Valle de Aburrá. |
| `calcular_haversine(origen, destino)` | `tuple[float, float]`, `tuple[float, float]` | `float` (km) | `CoordenadaInvalidaError` | Pre-valida ambos puntos y calcula la distancia ortodrómica real en kilómetros. |
| `calcular_tiempo_vuelo_min(distancia_km, velocidad_km_h)` | `float`, `float` | `float` (min) | Ninguna | Proyecta el tiempo estimado en minutos con protección contra división por cero. |
| `calcular_punto_intermedio(origen, destino, fraccion)` | `tuple, tuple, float` (`[0.0, 1.0]`) | `tuple[float, float]` | `CoordenadaInvalidaError` | Interpola la coordenada geográfica tras recorrer una fracción lineal de la ruta. |

---

## 6. Ejemplo de Uso

```python
from src.geodesia import CalculadorGeodesico

calculador = CalculadorGeodesico()

# 1. Definir coordenadas en el Valle de Aburrá
base_olaya = (6.219603, -75.586792)
parque_berrio = (6.250500, -75.568100)

# 2. Calcular distancia ortodrómica
distancia_km = calculador.calcular_haversine(base_olaya, parque_berrio)
print(f"Distancia: {distancia_km:.3f} km")

# 3. Proyectar tiempo de vuelo a 60 km/h
tiempo_min = calculador.calcular_tiempo_vuelo_min(distancia_km, velocidad_km_h=60.0)
print(f"ETA estimado: {tiempo_min:.2f} minutos")

# 4. Obtener posición intermedia al 50% de la ruta
punto_medio = calculador.calcular_punto_intermedio(base_olaya, parque_berrio, fraccion=0.5)
print(f"Waypoint al 50%: {punto_medio}")
```

---

## 7. Dependencias e Integración en el Ecosistema

* **Consumidores Directos:**
  * [`src/control/simulador.py`](../control/simulador.py): Utilizado en cada iteración de `avanzar_paso_tiempo()` para desplazar drones y calcular coordenadas de impacto por batería.
  * [`src/servicios/geocodificador.py`](../servicios/geocodificador.py): Empleado para verificar la viabilidad de destinos de pedidos y calcular kilometrajes de ida y vuelta.
  * [`src/ui/controlador.py`](../ui/controlador.py): Utilizado para telemetría en cabina y comparativas polimórficas de consumo.
* **Dependencias de Excepciones:**
  * [`src/excepciones/errores.py`](../excepciones/errores.py): `CoordenadaInvalidaError`.
* **Pruebas Automatizadas:**
  * [`src/geodesia/test_calculador.py`](test_calculador.py): Suite unitaria con 100% de aserciones aprobadas sobre rutas urbanas reales (Santafé, Parque Berrío, Sabaneta, Bello, Caldas, Barbosa).
