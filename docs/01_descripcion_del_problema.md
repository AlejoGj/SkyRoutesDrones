# Documento 01: Descripción e Historial del Problema

**Proyecto:** SkyRoute - Sistema de Gestión y Telemetría para Drones  
**Asignatura:** Algoritmos de Programación Orientada a Objetos  
**Institución:** Universidad de Medellín (UDEM)  
**Semestre:** 2026-2  
**Docente:** Mario Alejandro Saldarriaga (Grupo 62)  
**Equipo:** Alejandro García Jiménez, Juan Manuel Pava Higuita, Valery Arboleda Ardila  

---

## 1. Contexto del Problema

Una empresa de logística y transporte basada en la ciudad de Medellín requiere un módulo de software inicial para gestionar y validar la telemetría de su flota aérea. La compañía opera 6 tipos distintos de drones (Ej: Entrega Ligera, Carga Pesada, Vigilancia, Mapeo Topográfico, Inspección de Infraestructura y Búsqueda/Rescate).

El sistema debe recibir datos crudos de telemetría, validando que se cumplan estrictas reglas de negocio (niveles de batería, límites de altitud, coherencia del estado de los motores y validez de las coordenadas). Es un requisito fundamental que la información geográfica corresponda a ubicaciones reales del área metropolitana de Medellín (aproximadamente entre las latitudes 6.15 y 6.35, y longitudes -75.65 a -75.50) y que los datos geográficos sean consumidos de forma verídica.

La actualización de la información no será en tiempo real continuo; en su lugar, el sistema permitirá al operador actualizar y validar los datos de los drones bajo demanda a través de un botón de refresco en la futura interfaz gráfica. Si se detectan anomalías en las validaciones, el sistema debe interrumpir la operación con excepciones específicas.

---