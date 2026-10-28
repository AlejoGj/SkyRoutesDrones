# Módulo de Gestión de Usuarios y Roles (`src/usuarios/`)

Administración de identidades, perfiles de acceso autorizados y validación estricta de usuarios dentro de la plataforma SkyRoute.

* **Responsable de Implementación:** Valery Arboleda Ardila (Sprint 1 - HU-05)
* **Historia de Usuario Vinculada:** HU-05
* **Requisitos Funcionales:** RF-06

---

## 1. Propósito y Alcance

El paquete `src/usuarios/` modela la identidad y facultades de los actores que interactúan con el centro de control y la flota aérea. Sus responsabilidades son:

1. **Gestión de Identidad de Actores:** Registrar a los usuarios del sistema bajo un identificador alfanumérico único (`id_usuario`) y un nombre o razón social (`nombre`).
2. **Control de Acceso Basado en Roles (RBAC):** Garantizar que cada usuario posea un rol autorizado dentro del catálogo corporativo (`CLIENTE`, `OPERADOR_VUELO`, `ADMINISTRADOR`).
3. **Validación Defensiva Estricta:** Comprobar mediante `TypeError` y `ValueError` que ningún atributo contenga tipos ilegales o cadenas de texto vacías.
4. **Verificación de Integridad:** Proveer el método `validar_usuario()` para comprobar que todos los campos requeridos estén presentes y sean consistentes antes de autorizar solicitudes de servicio en el centro de control.
5. **Representación Canónica:** Sobrescribir `__str__` y `__repr__` para visualización limpia en consola, bitácoras de auditoría y depuración.

---

## 2. Arquitectura de la Clase `Usuario`

```
+-------------------------------------------------------------+
|                           Usuario                           |
+-------------------------------------------------------------+
| + ROLES_PERMITIDOS: list[str] =                             |
|   ['CLIENTE', 'OPERADOR_VUELO', 'ADMINISTRADOR']            |
+-------------------------------------------------------------+
| - id_usuario: str                                           |
| - nombre: str                                               |
| - rol: str                                                  |
+-------------------------------------------------------------+
| + __init__(id_usuario: str, nombre: str, rol: str) -> None  |
| + validar_rol() -> bool                                     |
| + validar_usuario() -> bool                                 |
| + __str__() -> str                                          |
| + __repr__() -> str                                         |
+-------------------------------------------------------------+
```

---

## 3. Catálogo de Roles y Privilegios

| Rol | Descripción Operativa | Capacidades en el Sistema |
|---|---|---|
| `CLIENTE` | Usuario comercial, hospital o empresa solicitante de servicios logísticos. | Generar solicitudes de pedido (`Pedido`) para entrega o transporte. |
| `OPERADOR_VUELO` | Técnico o piloto de torre de control de SkyRoute. | Supervisar telemetría, autorizar despegues y gestionar retornos a base. |
| `ADMINISTRADOR` | Responsable global de la plataforma aeronáutica. | Registrar nuevas aeronaves, gestionar usuarios y fiscalizar auditorías. |

---

## 4. Evolución Técnica frente al Diseño Original de la HU-05

| Elemento | Especificación Original (Sprint 1) | Implementación Real en Producción | Justificación de Ingeniería |
|---|---|---|---|
| **Constante de Roles** | Validación contra conjunto no encapsulado. | Constante formal de clase `ROLES_PERMITIDOS: list[str]`. | Estandariza la fuente de verdad de roles, permitiendo consultas desacopladas sin instanciar la clase. |
| **Validación de Tipos** | Asumía tipos correctos (`str`). | Validación explícita `if not isinstance(..., str) raise TypeError`. | Impide que enteros, diccionarios o valores nulos ingresen a la base de datos de usuarios. |
| **Normalización** | Lectura directa de la cadena. | Aplicación de `.strip().upper()` en rol y `.strip()` en identificador y nombre. | Tolera variaciones de digitación en interfaces de consola y formularios web. |
| **Verificación de Integridad** | No contemplada. | Método dedicado `validar_usuario() -> bool`. | Permite a `SistemaCentroControl.registrar_usuario()` validar atómicamente el estado del usuario antes de agregarlo al inventario activo. |
| **Representaciones** | No especificadas. | Sobrescritura de `__str__` y `__repr__`. | Presenta información clara del rol y nombre en los registros de auditoría (`LogOperacion`). |

---

## 5. Guía de Uso

```python
from src.usuarios.usuario import Usuario

# 1. Creación de usuario cliente
cliente = Usuario(
    id_usuario="USR-CLI-01",
    nombre="Clínica Las Américas",
    rol="cliente"  # Se normaliza a "CLIENTE"
)
print(cliente)
# Usuario: Clínica Las Américas (ID: USR-CLI-01) - Rol: [CLIENTE]

# 2. Verificación de integridad
if cliente.validar_usuario():
    print(f"Usuario {cliente.nombre} verificado y apto para solicitar pedidos.")

# 3. Manejo de error ante rol no autorizado
try:
    usuario_invalido = Usuario("USR-99", "Tester", "SUPERVISOR")
except ValueError as e:
    print(f"Error esperado: {e}")
```

---

## 6. Pruebas Unitarias y Cobertura

La clase `Usuario` es testeada transversalmente en el proyecto:
* Pruebas de integración del centro de control (`SistemaCentroControl.registrar_usuario`).
* Pruebas de enlace de pedidos (`Pedido.usuario_solicitante`).
* Validación de rechazo ante roles inválidos o tipos no permitidos.

Para ejecutar las pruebas:
```bash
python -m unittest discover -s src -p "test*.py"
```
