# Uso de `UCTPPlanner.py`

Este archivo ejecuta el flujo completo de planificación:

1. Carga el dominio desde un JSON UCTP.
2. Construye el modelo.
3. Genera un horario inicial con `Greedy`.
4. Asigna estudiantes con `SSP`.
5. Mejora el horario con `UCTP`.
6. Exporta el resultado final a JSON.

## Ejecución rápida

Desde la raíz del proyecto:

```bash
python UCTPPlanner.py
```

Si quieres usar un archivo de configuración:

```bash
python UCTPPlanner.py --config config.modelo.json
```

## Argumentos disponibles

- `--config`: ruta a un JSON con secciones de configuración.
- `--json-path`: sobrescribe el JSON de dominio que se carga.
- `--output-json`: sobrescribe la ruta del JSON exportado.
- `--max-iteraciones`: sobrescribe las iteraciones del flujo principal.
- `--seed`: fija la semilla para `random` y `numpy`.
- `--no-plot`: desactiva la generación del gráfico final.

Los argumentos de línea de comandos tienen prioridad sobre el archivo `config`.

## Estructura del archivo de configuración

El archivo `config.modelo.json` separa los valores modificables por sección:

- `dominio`
  - `json_path`: JSON UCTP de entrada que se usará como base del dominio.
  - `institucion`, `semestre`: metadatos que quedan escritos en el JSON exportado.
  - `max_carga_diaria`: tope global de clases por día para un profesor.
  - `max_carga_bloque`: tope global de clases por bloque horario.
- `greedy`
  - `umbral_varianza_aceptable`: controla cuánto desbalance entre paralelos se tolera al armar compatibilidades.
  - `umbral_compatibilidad_intercurso`: define desde qué porcentaje de alumnos compartidos dos cursos se consideran compatibles.
  - `asignacion_inteligente`: activa o desactiva la heurística que balancea paralelos según carga esperada.
  - `max_reintentos`: cantidad máxima de reinicios del `Greedy` antes de abortar.
- `ssp`
  - `alfa`: exponente aplicado al ratio de desbalance dentro de la función objetivo.
  - `cv_ideal`: coeficiente de variación objetivo para la distribución de inscritos por paralelo.
  - `ventana_ideal`: umbral base para penalizar ventanas/huecos en la función objetivo y en la búsqueda local.
- `uctp`
  - `max_iteraciones`: número máximo de iteraciones del Tabu Search.
  - `max_iteraciones_sin_mejora`: cuántas iteraciones sin mejora se toleran antes de detener la búsqueda.
  - `tamano_lista_tabu`: largo de la lista Tabu para evitar repetir movimientos recientes.
  - `tamano_vecindario`: cantidad de vecinos generados por iteración.
  - `resolver_ssp`: si `true`, `UCTP` vuelve a resolver `SSP` al evaluar cada vecino; si `false`, solo recalcula la FO con el `Y` actual.
  - `busqueda_guiada`: si `true`, cada iteración decide entre priorizar desbalance o ventana según cuál esté peor y sesga la selección de clases a mover hacia los paralelos más problemáticos. Si `false`, la generación de vecinos es completamente aleatoria (comportamiento original).
  - `proporcion_guiada`: fracción de vecinos (0.0–1.0) que usan selección guiada cuando `busqueda_guiada=true`. El resto se genera aleatoriamente para mantener diversidad.
- `flujo`
  - `max_iteraciones`: cantidad de ciclos Greedy + SSP + UCTP.
- `salida`
  - `ruta_json`: archivo exportado final. Si se deja `null`, la salida por defecto será `<json_origen>.generado.json`.
  - `ruta_graficos`: archivo donde se guarda la figura de evolución de métricas.
  - `ruta_resultados`: archivo donde se van acumulando los tuplos de la mejor solución encontrada por ejecución (formato `(desbalance, insatisfaccion, fo, choques, tiempo_ejecucion)`).
  - `ruta_valores_graficos`: archivo TSV (tab-separated) con los valores de cada iteración usados para generar el gráfico de evolución: `iteracion`, `desbalance`, `insatisfaccion`, `fo`, `choques`.
  - `ruta_warnings`: archivo donde se exportan las advertencias de reintentos de asignación del componente `Greedy`.
  - `guardar_graficos`: activa o desactiva el guardado del gráfico final.
  - `guardar_resultados`: activa o desactiva el guardado en `ruta_resultados`.
- `ejecucion`
  - `seed`: semilla para reproducibilidad de `random` y `numpy`.

## Warnings

- Los detalles internos de reintento de `Greedy` se escriben por defecto en `data\output\warnings_logs.txt`.
- En consola solo queda el aviso de reintento y el mensaje cuando se alcanza el límite.

## Ejemplo de uso recomendado

```bash
python UCTPPlanner.py --config config.modelo.json --no-plot
```

Eso carga el dominio desde `test.json` (si no se especifica otro), usa los parámetros del config y exporta el resultado en la ruta definida en `salida.ruta_json` o, si es `null`, en `<json_origen>.generado.json`.

## Notas

- Si no pasas `--config`, el script usa valores por defecto internos.
- Si no pasas `--json-path`, se usa `dominio.json_path` del config o `test.json` por defecto.
- El archivo `config.modelo.json` está pensado como punto de partida para ajustar los parámetros del flujo sin tocar el código.
- `ruta_resultados` guarda la **mejor** FO global, no la última. Escanea todos los resultados de la ejecución y escribe el tuplo con FO mínima.
- `ruta_valores_graficos` se sobreescribe en cada ejecución (contiene los datos del último flujo). El gráfico y `ruta_resultados` son acumulativos.
