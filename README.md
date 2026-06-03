# UCTPPlanner

Planificador académico para construir y optimizar horarios tipo UCTP desde un JSON de dominio. El flujo principal sigue estando en `UCTPPlanner.py`, que carga el dominio, genera un horario inicial con Greedy, asigna estudiantes con SSP y mejora la solución con UCTP/Tabu Search.

## Estructura del proyecto

- `UCTPPlanner.py`: punto de entrada principal.
- `src/`: módulos Python del planificador.
- `config/`: archivos de configuración del flujo principal y del generador de instancias.
- `data/input/`: JSON de entrada del dominio.
- `data/output/`: resultados, gráficos, logs y JSON generados.
- `docs/`: documentación técnica y de uso.
- `scripts/`: utilidades auxiliares.
- `appscript/`: interfaz y scripts para Google Apps Script / HTML.
- `index.html`: redirección directa al editor manual.
- `instancias_manuales/`: editor web autónomo para crear o ajustar instancias manualmente desde `planificador_academico_json.html`.
 - `docs/`: documentación técnica y de uso.
 - `scripts/`: utilidades auxiliares.
 - `appscript/`: colección de scripts y recursos para Google Apps Script. Contiene los archivos `.gs` (p. ej. `Code.gs`, `evaluar_fo.gs`, `Bootstrap.gs`) y HTML (p. ej. `Upload.html`, `ConfiguracionFO.html`) que permiten generar hojas en Google Sheets, subir JSONs de instancias desde la interfaz y ejecutar la evaluación de la función objetivo desde la hoja. También incluye un `README.md` con pasos para desplegar.
 - `index.html`: redirección directa al editor manual.
 - `instancias_manuales/`: editor web autónomo para crear o ajustar instancias manualmente.
	 - `planificador_academico_json.html`: editor visual que permite construir o editar el JSON de dominio (asignaturas, paralelos, clases, maestros, estudiantes, horarios) desde el navegador, validar la estructura y descargar el JSON resultante. Es especialmente útil para generar casos de prueba rápidos sin escribir JSON a mano.

## Requisitos

- Python 3.12 o compatible.
- Entorno virtual local en `.venv`.
- Dependencias principales: `numpy` y `matplotlib`.
- Instálalas con `pip install -r requirements.txt` dentro del entorno virtual.

## Ejecución en Windows

Desde la raíz del proyecto:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& "c:\Users\Joseph Donoso\Desktop\MEJORA\.venv\Scripts\Activate.ps1")
python UCTPPlanner.py --config config/config.modelo.json
```

Si quieres ejecutar sin gráfico final:

```powershell
python UCTPPlanner.py --config config/config.modelo.json --no-plot
```

También puedes sobrescribir parámetros desde la línea de comandos con `--json-path`, `--output-json`, `--max-iteraciones` y `--seed`.

## Generador de instancias

El generador de instancias quedó en `scripts/generador_instancias.py`. Sirve para crear un JSON compatible con el cargador de `UCTPPlanner.py` a partir de un archivo de configuración.
Complementa a `scripts/generador_instancias.py` la herramienta visual `instancias_manuales/planificador_academico_json.html`, que permite crear y exportar JSONs desde una interfaz web si prefieres no usar el generador por línea de comandos.

Ejemplo de uso:

```powershell
python scripts/generador_instancias.py --config config/config.generador.json --output ../data/input/test.json
```

Si no pasas `--output`, el generador escribe el archivo en `data/input/`.

## AppScript (Google Sheets)

En la carpeta `appscript/` hay un conjunto de scripts de Google Apps Script que facilitan integrar las instancias JSON con una Google Spreadsheet:

- Archivos `.gs`: implementan funciones para crear hojas derivadas del JSON (`-HorarioMaestro`, `-HorarioDocente`, `-Alumnos`, etc.), menús `onOpen` y la evaluación de la función objetivo (`evaluar_fo`).
- Archivos `.html`: `Upload.html` proporciona una interfaz para subir archivos JSON desde la PC hacia la hoja; `ConfiguracionFO.html` permite ajustar parámetros de evaluación desde la hoja.
- `appscript/README.md` contiene instrucciones de despliegue y sincronización con `clasp`.

Uso rápido:
- Abrir la Spreadsheet → `Extensiones` → `Apps Script` y pegar los archivos.
- Desde la hoja, usar el menú `Planificación docente` → `Cargar horario (JSON) desde PC…` para subir JSONs y generar automáticamente las hojas.

## Editor visual: `planificador_academico_json.html`

Dentro de `instancias_manuales/` existe una herramienta web (`planificador_academico_json.html`) que sirve como editor visual del JSON de dominio. Características principales:

- Construcción interactiva de la estructura del dominio: asignaturas, paralelos, clases, horarios, maestros y estudiantes.
- Validación básica de la estructura del JSON antes de descargar/exportar.
- Exportación directa de un JSON listo para usar con `UCTPPlanner.py` o para subir desde `appscript/Upload.html`.

Este editor es útil para generar casos de prueba rápidamente sin escribir JSON a mano o para enseñar la estructura de datos a usuarios no técnicos.

## Entradas y salidas

- Entrada por defecto del dominio: `data/input/test.json`
- JSON generado por defecto: `data/output/<nombre>.generado.json`
- Resultados: `data/output/results.txt`
- Gráficos: `data/output/graficos_optimizacion.png`
- Warnings de Greedy: `data/output/warnings_logs.txt`

## Documentación

- `docs/USO_CODIGO_PRINCIPAL.md`
- `docs/ESTRUCTURA_JSON_UCTP.md`
- `docs/GENERADOR_INSTANCIAS.md`
- `instancias_manuales/README.md`

## Notas

- El proyecto está pensado para ejecutarse en Windows con Python y un entorno virtual local.
- Si cambias el JSON de entrada, revisa también la sección `dominio` del archivo de configuración.
- Los archivos generados se mantienen fuera del control de versiones gracias a `.gitignore`.