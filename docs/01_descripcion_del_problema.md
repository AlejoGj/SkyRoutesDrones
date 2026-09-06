# Documento 01: Descripción e Historial del Problema

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  
**Semestre:** 2026-2  
**Docente:** Mario Alejandro Saldarriaga (Grupo 62)  
**Equipo:** Alejandro García Jiménez, Juan Manuel Pava Higuita, Valery Arboleda Ardila  

---

## 1. Contexto del Problema

¡Bienvenido al proyecto SkyRoutes!

En esta ocasión, nos acompañarás a descubrir qué hay detrás de la tecnología de Mario, líder de una innovadora empresa de logística y servicios aéreos en Medellín. Su compañía opera una variada flota distribuida en 6 categorías especializadas: Entrega Ligera, Carga Pesada, Vigilancia, Mapeo Topográfico, Inspección de Infraestructura y Búsqueda/Rescate.

Para escalar sus operaciones en el Valle de Aburrá, se nos encomendó el desarrollo de un módulo de software enfocado en dos pilares fundamentales:

1. Gestión Inteligente de Pedidos: Una minibase de datos encargada de procesar las solicitudes de los clientes y asignar automáticamente el dron idóneo según la categoría y los requerimientos de la misión.

2. Monitoreo de Telemetría y Mapa en Vivo: Un panel interactivo que consume datos geográficos reales de Medellín (latitudes 6.15 a 6.35 y longitudes -75.65 a -75.50) para ubicar cada aeronave sobre el mapa. Los datos se actualizan bajo demanda cada vez que el operador presiona el botón de refresco.

Para garantizar operaciones seguras, el módulo valida en cada actualización que la batería, la altitud, el estado de los motores y las coordenadas cumplan con esstrictas reglas de negocio. Ante cualquier anomalía, el sistema interrumpe el proceso emitiendo excepciones específicas para alertar al operador.

¿Estás listo para conocer la arquitectura y el código detrás de esta solución? ¡Acompáñanos a explorar el  mundo de esté proyecto!

---