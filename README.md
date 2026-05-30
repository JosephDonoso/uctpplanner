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

Ejemplo de uso:

```powershell
python scripts/generador_instancias.py --config config/config.generador.json
```

Si no pasas `--output`, el generador escribe el archivo en `data/input/`.

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