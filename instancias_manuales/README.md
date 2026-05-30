# Editor de Instancias Manuales

Este directorio contiene la interfaz web para crear y editar instancias JSON de forma manual.

## Archivo principal

- `planificador_academico_json.html`: editor autónomo que permite cargar un JSON, modificar asignaturas, paralelos, clases y maestros, y descargar el resultado.

## Uso

Abre `planificador_academico_json.html` directamente en el navegador o desde VS Code con Live Server si quieres una experiencia más cómoda.

## Relación con el proyecto

Esta herramienta complementa al planificador principal y al generador de instancias:

- `UCTPPlanner.py` consume los JSON finales.
- `scripts/generador_instancias.py` crea instancias sintéticas.
- `instancias_manuales/planificador_academico_json.html` permite editar instancias a mano.
