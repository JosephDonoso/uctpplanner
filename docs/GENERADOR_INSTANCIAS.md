**Generador de instancias — `generador_instancias.py`**

## Qué hace

Genera un JSON de instancia compatible con el cargador del proyecto y con el formato usado por `UCTPPlanner.py`.

## Uso

Ejecutar desde la raíz del proyecto:

```bash
python scripts/generador_instancias.py --config config/config.generador.json --output ../data/input/test.json
```

## Estructura del config

### `seed`

Semilla opcional para reproducibilidad. Si existe, el generador produce siempre la misma instancia para ese config.

### `output`

Ruta de salida por defecto del JSON generado. Si se usa `--output`, ese valor tiene prioridad.

### `metadatos`

- `institucion`: nombre de la institución que aparecerá en el JSON de salida.
- `semestre`: período académico que se propagará al JSON de salida.

### `restricciones`

- `MAX_CARGA_DIARIA`: máximo de carga por día para profesores.
- `MAX_CARGA_BLOQUE`: máximo de carga por bloque.
- `prob_restriccion_teorica_dias_distintos`: probabilidad de imponer que las clases teóricas caigan en días distintos.
- `prob_restriccion_teorica_separadas_1_dia`: probabilidad de imponer una separación de un día entre clases teóricas.
- `bloques_protegidos`: lista de bloques que no pueden asignarse. Cada elemento usa `dia` y `bloque`.

### `tiempos`

- `dias`: lista de días lectivos. Ejemplo: `["Lu", "Ma", "Mi", "Ju", "Vi"]`.
- `bloques_diarios`: cantidad de bloques por día si no se entrega una lista explícita en `bloques`.
- `bloques_totales`: validación opcional. Debe coincidir con `len(dias) * len(bloques)` cuando se declara.
- `bloques`: lista opcional de bloques explícitos. Si existe, tiene prioridad sobre `bloques_diarios`.

### `cantidades`

- `asignaturas`: cantidad de asignaturas distintas a generar.
- `paralelos_min`, `paralelos_max`: mínimo y máximo de paralelos por asignatura.
- `media_paralelos_por_asignatura`: media objetivo usada para distribuir paralelos entre asignaturas.
- `sesiones_min`, `sesiones_max`: mínimo y máximo de clases por asignatura.
- `media_sesiones_por_asignatura`: media objetivo de clases por asignatura.
- `maestros`: cantidad de profesores a generar.
- `paralelos_min_por_maestro`, `paralelos_max_por_maestro`: rango de carga por maestro.
- `media_paralelos_por_maestro`: media objetivo de carga por maestro.
- `prob_disponibilidad_maestro_bloque`: probabilidad de que un maestro esté disponible en un bloque dado.
- `estudiantes`: cantidad de estudiantes a generar.
- `asignaturas_min_por_estudiante`, `asignaturas_max_por_estudiante`: mínimo y máximo de asignaturas por estudiante.
- `media_asignaturas_por_estudiante`: media objetivo de asignaturas por estudiante.
- `carreras`: cantidad de carreras a generar.
- `semestre_min_por_carrera`: mínimo de semestres por carrera.
- `semestre_max_por_carrera`: máximo de semestres por carrera.
- `media_semestres_por_carrera`: media objetivo de semestres por carrera.
- `prob_relacion_asignatura_curso`: probabilidad de que una asignatura de estudiante provenga de su curso base.
- `prob_curso_base_para_estudiante`: probabilidad de que una asignatura salga sin curso asociado.
- `prob_asignaturas_preasignadas`: probabilidad de intentar preasignar horarios de una asignatura.
- `prob_asignatura_con_ayudantia`: probabilidad de incluir una ayudantía en la asignatura.
- `prob_un_maestro_por_paralelo_compartido`: probabilidad de que un paralelo con más de un maestro pase a modo compartido; en ese caso, todas sus clases se co-imparten por todos esos maestros.
- `max_maestros_por_asignatura`: máximo de maestros que puede tener una asignatura/paralelo. Valor recomendado: `2`.

### `nombres`

- `prefijo_asignatura`: prefijo para los códigos de asignatura.
- `prefijo_maestro`: prefijo para los códigos de maestro.
- `prefijo_estudiante`: prefijo para los códigos de estudiante.
- `prefijo_carrera`: prefijo para los códigos de carrera que agrupan asignaturas por semestre.

### `tipos_clases`

Lista de tipos de clase. Cada elemento puede ser un string o un objeto con `tipo` y `peso`.

Ejemplos válidos:

```json
["Cát", "Ay.", "Lab"]
```

```json
[
  {"tipo": "Cát", "peso": 0.45},
  {"tipo": "Ay.", "peso": 0.25}
]
```

El peso controla la probabilidad relativa de que ese tipo aparezca al construir las clases base.

## Reglas de generación

- Las clases se generan por asignatura y se copian a cada paralelo.
- `prob_asignaturas_preasignadas` aplica por asignatura completa: el generador intenta fijar horarios para todas las clases de esa asignatura; si falla, revierte la preasignación de esa asignatura.
- La ayudantía, cuando aparece, se marca con `"maestros": null`.
- El generador respeta `bloques_protegidos` y la disponibilidad de los profesores al preasignar.
- Si una asignatura tiene más de un maestro y se activa `prob_un_maestro_por_paralelo_compartido`, sus clases se co-imparten por todos los maestros de ese paralelo.
- Primero asigna al menos un maestro por paralelo; después agrega maestros extra para acercarse a la carga objetivo.

## Estructura del JSON generado

El archivo de salida contiene cuatro bloques principales:

- `metadatos`: institución y semestre.
- `restricciones`: carga máxima y restricciones teóricas, además del listado `PROFESORES`.
- `tiempos`: días y bloques usados.
- `eventos`:
  - `tipo_clases`: tipos de clase que se usaron.
  - `asignaturas`: catálogo de asignaturas con su curso y paralelos.
- `recursos`:
  - `maestros`: disponibilidad por día y bloque.
  - `estudiantes`: lista de asignaturas inscritas por estudiante.

En el JSON de salida, cada asignatura tiene esta forma general:

```json
{
  "codigo": "ASG001",
  "nombre": "Asignatura ASG001",
  "curso": {
    "carrera": "CAR001",
    "semestre": "01"
  },
  "paralelos": [ ... ]
}
```

Si una asignatura sale sin curso, el generador deja `curso` en `null`.

## Ejemplo mínimo de config

```json
{
  "seed": 42,
  "metadatos": {
    "institucion": "Mi Uni",
    "semestre": "2025-1"
  },
  "cantidades": {
    "asignaturas": 10,
    "maestros": 8,
    "estudiantes": 100
  },
  "tiempos": {
    "dias": ["Lu", "Ma", "Mi", "Ju", "Vi"],
    "bloques_diarios": 5
  },
  "nombres": {
    "prefijo_asignatura": "ASG",
    "prefijo_maestro": "DOC",
    "prefijo_estudiante": "EST",
    "prefijo_carrera": "CAR"
  }
}
```

## Ejemplo ampliado

```json
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
    "asignaturas_min_por_estudiante": 1,
    "asignaturas_max_por_estudiante": 6,
    "media_asignaturas_por_estudiante": 3.0,
    "carreras": 3,
    "semestre_min_por_carrera": 8,
    "semestre_max_por_carrera": 12,
    "media_semestres_por_carrera": 9.5,
    "prob_relacion_asignatura_curso": 0.9,
    "prob_asignatura_sin_curso": 0.1,
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
    "prob_restriccion_teorica_separadas_1_dia": 0.02,
    "bloques_protegidos": [
      {"dia": "Ju", "bloque": "5-6"}
    ]
  },
  "nombres": {
    "prefijo_asignatura": "ASG",
    "prefijo_maestro": "DOC",
    "prefijo_estudiante": "EST",
    "prefijo_carrera": "CAR"
  },
  "tipos_clases": [
    {"tipo": "Cát", "peso": 0.45},
    {"tipo": "Ay.", "peso": 0.25},
    {"tipo": "Lab", "peso": 0.2}
  ],
  "output": "instancia_ejemplo_generada.json"
}
```

## Nota

El generador mantiene compatibilidad con varias claves antiguas, pero la documentación de referencia es la de este archivo y la estructura que hoy produce el script.

