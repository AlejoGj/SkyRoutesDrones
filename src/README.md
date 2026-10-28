# Arquitectura de Paquetes - SkyRoute (`src/`)

Estructura modular del código fuente de producción para la plataforma de gestión y simulación cinemática de drones en el Valle de Aburrá (Sprints 1 y 2).

---

## Organización de Módulos y Responsabilidades

### 1. Alejandro García Jiménez
* [`src/geodesia/`](geodesia/README.md): Motor de cálculo trigonométrico Haversine, interpolación de waypoints y estimación de ETA (`HU-02`).
* [`src/telemetria/`](telemetria/README.md): Trama física, coherencia de sustentación y validación sensorial de aeronaves (`HU-01`).
* [`src/excepciones/`](excepciones/README.md): Taxonomía jerárquica de excepciones de dominio aeronáutico y cartográfico (`HU-01`, `HU-03`).
* [`src/servicios/`](servicios/README.md): Cadena de geocodificación urbana multinivel (ArcGIS, Google, OSM, Catálogo Local) y telemetría meteorológica Open-Meteo (`HU-05`, `HU-06`, `HU-12`).
* **Módulo de Funcionamiento y Motor:** Controlador de tiempo no bloqueante (`reloj.py`) y motor cinemático de vuelo físico discreto (`simulador.py`) en [`src/control/`](control/README.md) (`HU-12`).

### 2. Juan Manuel Pava Higuita
* [`src/flota/`](flota/README.md): Jerarquía de aeronaves, modelo abstracto base `Dron(ABC)`, consumo energético polimórfico y ciclo de vida sin teletransportación (`HU-03`, `HU-04`, `HU-07`, `HU-08`, `HU-09`, `HU-10`, `HU-11`).

### 3. Valery Arboleda Ardila
* [`src/usuarios/`](usuarios/README.md): Entidad `Usuario`, control de acceso basado en roles (RBAC) e integridad (`HU-05`).
* [`src/pedidos/`](pedidos/README.md): Entidad `Pedido`, soporte de destino geográfico dual y ciclo de vida de 5 estados (`HU-05`).
* [`src/control/`](control/README.md): Orquestador central `SistemaCentroControl`, fábrica de aeronaves `FABRICA_DRONES`, asignación por autonomía de circuito y bitácora `LogOperacion` (`HU-05`, `HU-06`, `HU-12`).

---

## Puntos de Entrada y Validación

* [`src/main.py`](main.py): Demostración de integración general del sistema.
* [`src/ui/`](ui/): Servidor web HTTP y controlador de la interfaz gráfica interactiva en tiempo real.
* **Suite de Pruebas Automatizadas:**
  ```bash
  python -m unittest discover -s src -p "test*.py"
  ```
