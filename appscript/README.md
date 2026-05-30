# AppScript — Cómo crear y ejecutar

Este directorio contiene los archivos de Google Apps Script usados por el proyecto MEJORA.

Archivos principales
- `Bootstrap.gs` — utilidades de arranque.
- `Code.gs` — funciones para crear hojas (HorarioMaestro, HorarioDocente, Matrículas, etc.) y la UI de carga.
- `evaluar_fo.gs` — evaluación de la función objetivo y generación de analíticas.
- `ConfiguracionFO.html`, `Upload.html` — plantillas HTML usadas por la interfaz en la hoja.

Objetivo del README
- Explicar cómo crear un proyecto de Apps Script con estos archivos y cómo ejecutarlo.

   1. Abre `CARGAR HORARIOS PUCV.xlsx` con Google Spreadsheet.
   2. Ve a `Extensiones` → `Apps Script`.
   3. En el editor de Apps Script crea un nuevo proyecto (o usa el proyecto vinculado si ya existe).
   4. Por cada archivo en este directorio crea un archivo nuevo en el editor con el mismo nombre y extensión (`.gs` o `.html`) y pega el contenido correspondiente.
   5. Guarda el proyecto.
   6. Autoriza: al ejecutar por primera vez cualquier función (por ejemplo `writeAllFromJsonFiles` o `evaluarFuncionObjetivo`) se solicitarán permisos; sigue los pasos para concederlos.
   7. Vuelve a la hoja y recarga la página para que se ejecuten los `onOpen` y aparezcan los menús (p. ej. `Planificación docente`).
   8. Usa `Planificación docente` → `Cargar horario (JSON) desde PC…` para abrir la interfaz y subir los JSON que generarán las hojas automáticamente.

Ejemplo rápido

- Crea un archivo JSON de prueba con la estructura esperada (usa `instancias_manuales/planificador_academico_json.html` o `scripts/generador_instancias.py` para ejemplos).
- En la Spreadsheet: `Planificación docente` → `Cargar horario (JSON) desde PC…` → subir JSON → verificar que se crean las hojas `-HorarioMaestro`, `-HorarioDocente`, `-Alumnos`, etc.

