# Módulo de Servicios Externos y Cartografía Urbana (`src/servicios/`)

Servicios de infraestructura externa para telemetría meteorológica en tiempo real del Valle de Aburrá y resolución geocodificada de direcciones urbanas mediante cadena de contingencia multinivel (ArcGIS, Google Maps, OpenStreetMap Nominatim y Catálogo Local Offline).

* **Responsable de Implementación:** Alejandro García Jiménez (Módulo de Funcionamiento: Reloj, Simulador y Servicios)
* **Historias de Usuario Vinculadas:** HU-05 (Geocodificación de Pedidos), HU-06 (Inyección en Centro de Control), HU-12 (Factor Climático en Simulación)
* **Requisitos Funcionales:** RF-05, RF-07, RF-08, RF-10

---

## 1. Propósito y Alcance

El paquete `src/servicios/` encapsula la interacción con APIs públicas y fuentes cartográficas externas, aislando la lógica de negocio de la torre de control de dependencias volátiles de red. Sus objetivos son:

1. **Resolución Cartográfica de Direcciones Urbanas (`IServicioGeocodificador`):** Convertir direcciones alfanuméricas de clientes (ej. *"Calle 30A # 82A-26"*, *"Universidad de Medellín"*) en coordenadas geodésicas decimales WGS84 dentro del perímetro del Valle de Aburrá.
2. **Arquitectura de Contingencia Multinivel (Fallback):** Implementar un patrón de cadena de proveedores donde fallos de red, límites de cuota o caídas de proveedores comerciales delegan transparentemente en OpenStreetMap y, en última instancia, en un catálogo local offline 100% determinista.
3. **Monitoreo Meteorológico Metropolitano (`ServicioClimaAburra`):** Consultar en tiempo real variables atmosféricas (temperatura, velocidad del viento, ráfagas y precipitación) sin requerir autenticación para 6 nodos clave del Valle de Aburrá.
4. **Modulación de Velocidad de Vuelo y Seguridad:** Calcular el factor de reducción de velocidad efectiva ($0.80$ a $1.0$) y evaluar la condición binaria de vuelo seguro (`vuelo_seguro`).

---

## 2. Arquitectura de Geocodificación y Cadena de Contingencia

```
                           +----------------------------+
                           |  IServicioGeocodificador   | (Protocol)
                           +----------------------------+
                           | + geocodificar_direccion() |
                           | + obtener_detalle_dir()    |
                           +----------------------------+
                                          ^
        +---------------------------------+---------------------------------+
        |                                 |                                 |
+--------------------+           +--------------------+           +--------------------+
| GeocodificadorArcGIS|           |GeocodificadorGoogle|           | GeocodificadorOSM  |
+--------------------+           +--------------------+           +--------------------+
| - Esri World Geocod|           | - Google Maps API  |           | - OSM Nominatim    |
| - Malla vial IGAC  |           | - Bounded viewbox  |           | - Bounded Aburrá   |
| - Score min >= 70% |           | - GOOGLE_MAPS_KEY  |           | - Nomenclatura CO  |
+--------------------+           +--------------------+           +--------------------+
        |                                 |                                 |
        +---------------------------------+---------------------------------+
                                          | (fallback si falla la red)
                                          v
                           +----------------------------+
                           | ServicioGeocodificadorLocal|
                           +----------------------------+
                           | - 22 Puntos de Referencia  |
                           | - 100% Determinista / Test |
                           | - Cero latencia de red     |
                           +----------------------------+
```

### 2.1 Cadena de Proveedores
* **Esri ArcGIS (`ServicioGeocodificadorArcGIS`):** Proveedor principal por defecto en `SistemaCentroControl`. Excelente precisión para la nomenclatura vial colombiana (malla IGAC) sin requerir API key para búsquedas individuales. Filtra candidatos con `Score >= 70.0%`.
* **Google Maps (`ServicioGeocodificadorGoogle`):** Máxima precisión para direcciones comerciales y residenciales con cruces complejos. Carga credenciales desde la variable de entorno `GOOGLE_MAPS_API_KEY` o parámetro directo.
* **OpenStreetMap Nominatim (`ServicioGeocodificadorOSM`):** Proveedor abierto restringido por `viewbox` al Valle de Aburrá. Implementa un motor de expresiones regulares para normalización vial colombiana (`MAPA_PREFIJOS_VIALES` y `PATRON_CUADRICULA`) que genera búsquedas jerárquicas candidatas (dirección exacta, cruce vial, vía principal) y filtra resultados degradados a nivel de ciudad.
* **Catálogo Local Offline (`ServicioGeocodificadorLocal`):** Diccionario en memoria con 22 hitos urbanos y vertipuertos metropolitanos (Parque Berrío, El Poblado, Santa Fe, Universidad de Medellín, Aeropuerto Olaya Herrera, etc.). Garantiza que la suite de pruebas unitarias y entornos sin internet funcionen sin interrupciones.

---

## 3. Telemetría Meteorológica en Tiempo Real (`clima.py`)

La clase `ServicioClimaAburra` interactúa con el endpoint abierto de Open-Meteo (`https://api.open-meteo.com/v1/forecast`), parametrizado para la zona horaria `America/Bogota`.

### 3.1 Nodos Metropolitanos Monitoreados
```python
NODOS_ABURRA = {
    "Medellin_Centro": {"lat": 6.2442, "lon": -75.5812},
    "El_Poblado":      {"lat": 6.2089, "lon": -75.5684},
    "Belen":           {"lat": 6.2319, "lon": -75.6105},
    "Envigado":        {"lat": 6.1759, "lon": -75.5917},
    "Bello":           {"lat": 6.3373, "lon": -75.5579},
    "Sabaneta":        {"lat": 6.1515, "lon": -75.6166}
}
```

### 3.2 Lógica de Modulación y Criterio de Seguridad
* **Factor de Reducción de Velocidad (`factor_velocidad`):**
  * Si $\text{viento} > 25.0\text{ km/h}$: Factor $0.80$ (reducción del 20%).
  * Si $\text{viento} > 15.0\text{ km/h}$: Factor $0.90$ (reducción del 10%).
  * En condiciones moderadas: Factor $1.00$ (sin penalización).
* **Condición de Vuelo Seguro (`vuelo_seguro`):**
  $$\text{vuelo\_seguro} = (\text{lluvia} < 2.0\text{ mm}) \land (\text{viento} < 35.0\text{ km/h})$$
* **Resiliencia ante Fallos (`fallback`):** Si la solicitud expira (`timeout = 4 s`) o no hay conexión, retorna valores nominales seguros ($22^\circ\text{C}$, $0\text{ mm}$ lluvia, $12\text{ km/h}$ viento, factor $1.0$).

---

## 4. Decisiones Técnicas y Patrones de Diseño

| Principio / Decisión | Justificación Técnica |
|---|---|
| **Inversión de Dependencias (DIP)** | `SistemaCentroControl` no depende de ArcGIS ni de OSM, sino del protocolo `IServicioGeocodificador`. Esto permite intercambiar proveedores o usar mocks en tests unitarios sin tocar una sola línea de lógica de negocio. |
| **Cadena de Contingencia (Fallback)** | Previene que el rechazo de una petición HTTP por parte de una API pública detenga el registro de pedidos de los clientes. Cada proveedor delega en el siguiente nivel si no halla resultados o sufre errores de red. |
| **Normalización Regex Colombiana** | La nomenclatura colombiana mezcla abreviaturas heterogéneas (`cll`, `cra`, `diag`, `#`, `-`, `con`). El motor de OSM expande prefijos y descompone cuadrículas para consultar candidatos viales estructurados. |
| **Caché en Centro de Control** | Para evitar llamadas HTTP repetitivas en cada ciclo cinemático de `refrescar_datos_flota()`, el centro de control cachea los reportes climáticos con un TTL de 60 segundos. |

---

## 5. Guía de Uso

### 5.1 Geocodificación con ArcGIS (Proveedor Predeterminado)
```python
from src.servicios.geocodificador import ServicioGeocodificadorArcGIS

geocodificador = ServicioGeocodificadorArcGIS()
coords = geocodificador.geocodificar_direccion("Universidad de Medellín, Belén")
print(f"Coordenadas resueltas: {coords}")
# Coordenadas resueltas: (6.2319, -75.6105)

detalle = geocodificador.obtener_detalle_direccion("Parque de Envigado")
print(f"Fuente: {detalle['fuente']} | Coordenadas: {detalle['coordenadas']}")
```

### 5.2 Consulta Climática y Factor de Velocidad
```python
from src.servicios.clima import ServicioClimaAburra

servicio_clima = ServicioClimaAburra()
reporte = servicio_clima.obtener_condiciones("Belen")

print(f"Nodo: {reporte['nodo']}")
print(f"Temperatura: {reporte['temperatura_c']} °C | Viento: {reporte['viento_kmh']} km/h")
print(f"Factor de velocidad aplicable: {reporte['factor_velocidad']}")
print(f"¿Vuelo seguro?: {reporte['vuelo_seguro']}")
```

---

## 6. Pruebas Unitarias y Cobertura

La suite dedicada [`src/servicios/test_geocodificador.py`](file:///c:/Users/Alejo/Desktop/SkyRoutesDrones/src/servicios/test_geocodificador.py) valida:
* Geocodificación offline determinista de los 22 puntos de referencia.
* Manejo de direcciones con nomenclatura abreviada y cuadrícula vial.
* Invocación de fallbacks multinivel ante errores de red simulados.
* Rechazo y disparo de `CoordenadaInvalidaError` ante puntos fuera del Valle de Aburrá.
* Disparo de `GeocodificacionError` ante direcciones no encontradas.

Para ejecutar las pruebas:
```bash
python -m unittest src/servicios/test_geocodificador.py
```
