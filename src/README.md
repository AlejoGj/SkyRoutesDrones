# Arquitectura de Paquetes - SkyRoute (`src/`)

Estructura modular del código fuente para el **Sprint 1 (Core sin Pilares de POO)**.

---

## Organización por Responsable

### 1. Alejandro García Jiménez (Módulo 1)
* [`src/excepciones/`](excepciones/): Excepciones de dominio personalizadas (`RF-02`, `HU-01`).
* [`src/telemetria/`](telemetria/): Trama y validación de datos de telemetría física (`RF-01`, `HU-01`).
* [`src/geodesia/`](geodesia/): Motor de cálculo Haversine y tiempos de viaje ETA (`RF-03`, `RF-10`, `HU-02`).

### 2. Juan Manuel Pava Higuita (Módulo 2)
* [`src/flota/`](flota/): Entidad `Dron`, ciclo de vida de vuelo y formatos en consola (`RF-04`, `RF-05`, `RF-09`, `HU-03`, `HU-04`).

### 3. Valery Arboleda Ardila (Módulo 3)
* [`src/usuarios/`](usuarios/): Entidad `Usuario` y validación de roles (`RF-06`, `HU-05`).
* [`src/pedidos/`](pedidos/): Entidad `Pedido` y estados de solicitud (`RF-07`, `HU-05`).
* [`src/control/`](control/): Orquestador central `SistemaCentroControl` y registros de auditoría `LogOperacion` (`RF-08`, `RF-09`, `HU-05`, `HU-06`).

---

## Punto de Entrada
* [`src/main.py`](main.py): Script de integración general y prueba de humo para la entrega #1.
