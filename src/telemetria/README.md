# Módulo de Telemetría Sensorial (`src/telemetria/`)

Empaquetamiento de tramas sensoriales en tiempo real, verificación de reglas físicas de sustentación aerodinámica, validación de rangos planetarios WGS84 y actualización atómica para aeronaves en SkyRoute.

* **Responsable de Implementación:** Alejandro García Jiménez (Sprint 1 - HU-01)
* **Historia de Usuario Vinculada:** HU-01
* **Requisitos Funcionales:** RF-01, RF-02, RF-05

---

## 1. Propósito y Alcance

El paquete `src/telemetria/` modela la capa de instrumentación física y sensorial de las aeronaves. Sus responsabilidades comprenden:

1. **Custodia de Tramas Físicas:** Almacenar de manera estructurada los parámetros de vuelo transmitidos por el hardware: carga de batería, altitud sobre el suelo (AGL), estado de la planta motriz y coordenadas GPS.
2. **Coherencia Física de Sustentación:** Garantizar que los estados del motor y la altitud mantengan consistencia aeronáutica (los motores no pueden estar apagados mientras el dron se encuentra en sustentación altimétrica).
3. **Validación Defensiva Planetaria:** Validar que los valores sensoriales cumplan con los límites físicos y geométricos antes de ser admitidos en la memoria del sistema.
4. **Actualización Atómica y Parcial de Datos:** Proveer el método `actualizar_trama(...)` para refrescar variables individuales conservando el resto de las lecturas intactas.
5. **Formateo Estandarizado:** Proporcionar representaciones de consola legibles (`__str__`) y representaciones de depuración para desarrollo (`__repr__`).

---

## 2. Arquitectura de la Clase `TelemetriaDrone`

```
+---------------------------------------------------------------------------------+
|                                 TelemetriaDrone                                 |
+---------------------------------------------------------------------------------+
| - id_dron: str                                                                  |
| - bateria: float           [0.0, 100.0]%                                        |
| - altitud: float           [0.0, 120.0] m (Límite Aerocivil UAEAC)              |
| - estado_motores: str      {'APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA'}    |
| - coordenadas: tuple       (latitud, longitud) WGS84                            |
| - latitud: float           [-90.0, 90.0]°                                       |
| - longitud: float          [-180.0, 180.0]°                                     |
+---------------------------------------------------------------------------------+
| + validar_datos(id_dron, bateria, altitud, estado_motores, coordenadas) -> bool |
| + actualizar_trama(bateria, altitud, estado_motores, coordenadas) -> None       |
| + __str__() -> str                                                              |
| + __repr__() -> str                                                             |
+---------------------------------------------------------------------------------+
```

---

## 3. Reglas de Negocio y Coherencia Física

| Parámetro | Rango / Catálogo Permitido | Excepción Disparada | Regla Aeronáutica Asociada |
|---|---|---|---|
| `id_dron` | `str` no vacía | `ValueError` | Identificador único de fuselaje de la aeronave. |
| `bateria` | `[0.0, 100.0]%` (numérico) | `BateriaInvalidaError` | Límites físicos de las celdas químicas LiPo/Li-Ion. |
| `altitud` | `[0.0, 120.0] m` (numérico) | `AltitudInvalidaError` | Techo legal para operaciones no tripuladas urbanas en Colombia. |
| `estado_motores` | `{'APAGADOS', 'STANDBY', 'EN_VUELO', 'EMERGENCIA'}` | `EstadoMotorInvalidoError` | Catálogo oficial de modos motrices. |
| `coordenadas` | Tupla de 2 reales en `[-90, 90]` y `[-180, 180]` | `CoordenadaInvalidaError` | Estándar geodésico planetario WGS84. |
| **Coherencia Motriz** | `altitud > 0` exige `EN_VUELO`<br>`altitud == 0` prohíbe `EN_VUELO` | `EstadoMotorInvalidoError` | Si la aeronave está en el aire sus hélices deben estar girando en régimen de vuelo; si está en tierra no puede figurar en vuelo. |

---

## 4. Evolución Técnica frente al Diseño Original de la HU-01

| Elemento | Especificación Original (Sprint 1) | Implementación Real en Producción | Justificación de Ingeniería |
|---|---|---|---|
| **Validación de Geocerca** | `validar_datos()` verificaba límites del Valle de Aburrá (`[5.9667, 6.5000]`, `[-75.7167, -75.3500]`). | `validar_datos()` valida geometría planetaria WGS84 (`[-90, 90]`, `[-180, 180]`). La geocerca se delega a `CalculadorGeodesico`. | **Principio de Responsabilidad Única (SRP):** El sensor GPS no debe estar rígidamente acoplado a un valle o ciudad específica; la delimitación metropolitana pertenece a la capa de navegación. |
| **Sobrecarga de `validar_datos()`** | Método sin argumentos que leía directamente `self`. | Admite parámetros opcionales con fallback a `self`: `validar_datos(self, id_dron=None, bateria=None, ...)` | Permite prevalidar tramas parciales en `actualizar_trama(...)` sin instanciar objetos intermedios ni mutar el estado antes de confirmar validez. |
| **Desempaquetado Atómico** | Asignación manual o no descrita. | Desempaquetado automático `self.latitud, self.longitud = self.coordenadas` al validar con éxito. | Facilita el acceso directo a los componentes geográficos sin romper la tupla atómica. |
| **Representaciones** | No especificadas formalmente. | Sobrescritura de `__str__` y `__repr__` con formato legible de telemetría. | Facilita la depuración en tiempo de ejecución, logs de auditoría y pruebas unitarias. |

---

## 5. Guía de Uso

```python
from src.telemetria.telemetria import TelemetriaDrone

# 1. Instanciación nominal en base
telemetria = TelemetriaDrone(
    id_dron="DRON-MED-01",
    bateria=100.0,
    altitud=0.0,
    estado_motores="APAGADOS",
    coordenadas=(6.219603, -75.586792)  # Base Olaya Herrera
)
print(telemetria)
# [Telemetría DRON-MED-01] Batería: 100.0% | Altitud: 0.0 m | Motores: APAGADOS | GPS: (6.219603, -75.586792)

# 2. Despegue a altitud de crucero (actualización parcial atómica)
telemetria.actualizar_trama(
    altitud=30.0,
    estado_motores="EN_VUELO",
    bateria=98.5
)
print(f"Altitud: {telemetria.altitud} m, Motores: {telemetria.estado_motores}")
```

---

## 6. Pruebas Unitarias y Cobertura

El comportamiento de este módulo está respaldado por la suite de pruebas dedicada en:
* [`src/telemetria/test_telemetria.py`](file:///c:/Users/Alejo/Desktop/SkyRoutesDrones/src/telemetria/test_telemetria.py)

Valida límites de batería, techo altimétrico, coherencia motriz-altitud, formato de coordenadas y actualización atómica de tramas.

Para ejecutar las pruebas:
```bash
python -m unittest src/telemetria/test_telemetria.py
```
