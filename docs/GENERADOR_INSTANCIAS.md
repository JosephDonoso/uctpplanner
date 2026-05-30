**Generador de instancias — generador_instancias.py**

Descripción breve
- **Script:** generador_instancias.py
- **Propósito:** Genera un JSON de instancia compatible con el cargador del proyecto (formato usado por `UCTPPlanner.py`).

Uso
- Ejecutar desde la raíz del proyecto:

```
python generador_instancias.py --config ruta/al/config.json --output ruta/de/salida.json
```
- El parámetro `--config` es obligatorio; `--output` es opcional (por defecto escribe `instancia_generada.json` junto al `config`).

Estructura del JSON de configuración (resumen)
- `metadatos` (objeto)
  - `institucion` (string)
  - `semestre` (string)
- `cantidades` / `conteos` (objeto)
  - `asignaturas` (int)
  - `paralelos_min`, `paralelos_max` (int)
  - `media_paralelos_por_asignatura` (float)
  - `sesiones_min`, `sesiones_max`, `media_sesiones_por_asignatura`
  - `maestros` (int)
  - `paralelos_min_por_maestro`, `paralelos_max_por_maestro`, `media_paralelos_por_maestro`
  - `prob_disponibilidad_maestro_bloque` (0..1)
  - `estudiantes` (int)
  - `sesiones_min_por_estudiante`, `sesiones_max_por_estudiante`, `media_sesiones_por_estudiante`
  - `cursos` (int)
  - `prob_relacion_asignatura_curso` (0..1)
  - `prob_asignaturas_preasignadas` (0..1) — probabilidad por asignatura de intentar preasignar horarios
  - `prob_asignatura_con_ayudantia` (0..1) — probabilidad de incluir 1 ayudantía en la asignatura
  - `prob_un_maestro_por_paralelo_compartido` (0..1)
- `tiempos` (objeto)
  - `dias` (lista de strings) ejemplo: ["Lu","Ma","Mi","Ju","Vi"]
  - `bloques` (lista) o `bloques_diarios` (int) para generar bloques `1-2,3-4,...`
  - `bloques_totales` (opcional) debe coincidir con `len(dias)*len(bloques)` si se usa
- `restricciones` (objeto)
  - `MAX_CARGA_DIARIA`, `MAX_CARGA_BLOQUE` (int)
  - `prob_restriccion_teorica_dias_distintos` (0..1)
  - `prob_restriccion_teorica_separadas_1_dia` (0..1)
- `nombres` (objeto)
  - `prefijo_asignatura`, `prefijo_maestro`, `prefijo_estudiante` (strings)
- `tipos_clases` (lista) formato: lista de strings o de objetos `{"tipo": "Cát", "peso": 0.45}`
- `bloques_protegidos` (lista) elementos `{"dia":"Ju","bloque":"7-8"}` para bloquear horas específicas
- `seed` (opcional) semilla para reproducibilidad
- `output` (opcional) ruta de salida relativa al `config` si no se pasa `--output`

Semántica y reglas importantes
- Las clases se generan por asignatura y se copian a cada paralelo (paralelos comparten la plantilla de clases).
- `prob_asignaturas_preasignadas` aplica por asignatura: el generador intenta preasignar todas las clases de sus paralelos; si falla, revierte la preasignación para esa asignatura.
- Máximo 1 ayudantía por asignatura cuando se produce (la ayudantía tiene `"maestros": null`).
- Al crear preasignaciones, se respetan las disponibilidades de los profesores y los `bloques_protegidos`.
- El primer pase asigna al menos un profesor por paralelo; luego se añaden profesores extra para acercarse a la carga objetivo por profesor.


Ejemplo mínimo de `config.json`
```
{
  "seed": 42,
  "metadatos": {"institucion":"Mi Uni","semestre":"2025-1"},
  "cantidades": {"asignaturas": 10, "maestros": 8, "estudiantes": 100},
  "tiempos": {"dias": ["Lu","Ma","Mi","Ju","Vi"], "bloques_diarios": 5},
  "nombres": {"prefijo_asignatura":"ASG","prefijo_maestro":"DOC","prefijo_estudiante":"EST"}
}
```

Archivo de ejemplo: `config.ejemplo.json`

Aquí tienes un `config.ejemplo.json` ampliado que puedes copiar directamente junto al script `generador_instancias.py` y usar como punto de partida:

```
{
  "seed": 12345,
  "metadatos": {
    "institucion": "Universidad Ejemplo",
    "semestre": "2025-1"
  },
  "cantidades": {
    "asignaturas": 20,
    "paralelos_min": 1,
    "paralelos_max": 3,
    "media_paralelos_por_asignatura": 1.5,
    "sesiones_min": 2,
    "sesiones_max": 4,
    "media_sesiones_por_asignatura": 2.8,
    "maestros": 12,
    "paralelos_min_por_maestro": 1,
    "paralelos_max_por_maestro": 4,
    "media_paralelos_por_maestro": 2.0,
    "prob_disponibilidad_maestro_bloque": 0.75,
    "estudiantes": 300,
    "sesiones_min_por_estudiante": 1,
    "sesiones_max_por_estudiante": 6,
    "media_sesiones_por_estudiante": 3.0,
    "cursos": 6,
    "prob_relacion_asignatura_curso": 0.9,
    "prob_asignaturas_preasignadas": 0.08,
    "prob_asignatura_con_ayudantia": 0.3,
    "prob_un_maestro_por_paralelo_compartido": 0.7
  },
  "tiempos": {
    "dias": ["Lu", "Ma", "Mi", "Ju", "Vi"],
    "bloques_diarios": 6
  },
  "restricciones": {
    "MAX_CARGA_DIARIA": 8,
    "MAX_CARGA_BLOQUE": 15,
    "prob_restriccion_teorica_dias_distintos": 0.05,
    "prob_restriccion_teorica_separadas_1_dia": 0.02
  },
  "nombres": {
    "prefijo_asignatura": "ASG",
    "prefijo_maestro": "DOC",
    "prefijo_estudiante": "EST"
  },
  "tipos_clases": [
    {"tipo": "Cát", "peso": 0.45},
    {"tipo": "Ay.", "peso": 0.25},
    {"tipo": "Lab", "peso": 0.2}
  ],
  "bloques_protegidos": [
    {"dia": "Ju", "bloque": "5-6"}
  ],
  "output": "instancia_ejemplo_generada.json"
}
```

Coloca este archivo como `config.generador.json` en la misma carpeta que `generador_instancias.py` y ejecútalo con:

```
python generador_instancias.py --config config.generador.json
```

