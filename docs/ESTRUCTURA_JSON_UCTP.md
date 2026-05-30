# Estructura del JSON (UCTP / Planificación Docente)

Este documento describe la estructura del archivo JSON usado en este proyecto (por ejemplo: `Semestre 2025-1.editado.json`).

## Vista general

El JSON está organizado en 4 secciones principales:

- `metadatos`: información del dataset (institución, semestre, etc.).
- `restricciones`: parámetros/restricciones del problema (por ejemplo cargas máximas).
- `tiempos`: definición del eje temporal (días y bloques).
- `eventos`: definición académica (asignaturas → paralelos → clases).
- `recursos`: recursos humanos y demanda (maestros con disponibilidad, estudiantes con ramos inscritos).

En términos de relaciones:

- Una **asignatura** (`eventos.asignaturas[]`) tiene varios **paralelos**.
- Un **paralelo** tiene una lista de **maestros** (profesores asociados al paralelo) y varias **clases**.
- Una **clase** representa una sesión/tipo (Cát, Ay., Lab, etc.) y opcionalmente puede traer:
  - `maestros` específicos para esa clase (si no existe, se entiende que hereda los del paralelo).
  - `horario_predefinido` con `dia` y `bloque` (si no existe / es `null`, la clase no tiene horario fijo).

---

## Esquema (pseudo-schema)

```json
{
  "metadatos": {
    "institucion": "string",
    "semestre": "string"
  },
  "restricciones": {
    "MAX_CARGA_DIARIA": 8,
    "MAX_CARGA_BLOQUE": 15,
    "CLASES_TEORICAS_DIAS_DISTINTOS": [ /* lista de {codigo_asignatura, paralelo} */ ],
    "CLASES_TEORICAS_SEPARADAS_1_DIA": [ /* lista de {codigo_asignatura, paralelo} */ ],
    "PROFESORES": [ /* metadatos por profesor (ver más abajo) */ ]
  },
  "tiempos": {
    "dias": ["Lu", "Ma", "Mi", "Ju", "Vi"],
    "bloques": ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14"]
  },
  "eventos": {
    "tipo_clases": ["Cát", "Ay.", "Lab", "Tal"],
    "asignaturas": [
      {
        "codigo": "string",
        "nombre": "string",
        "curso": { "carrera": "string", "semestre": "string" },
        "paralelos": [
          {
            "codigo": "string",
            "maestros": ["string"],
            "restriccion_teoricas": "none|days_distinct|days_gap_1",
            "clases": [
              {
                "tipo": "string",
                "maestros": ["string"] | null | (no existe),
                "horario_predefinido": {
                  "dia": "Lu|Ma|Mi|Ju|Vi",
                  "bloque": "1-2|3-4|..."
                } | null | (no existe)
              }
            ]
          }
        ]
      }
    ]
  },
  "recursos": {
    "maestros": [
      {
        "nombre": "string",
        "disponibilidad": [
          { "Lu": [0|1, 0|1, ...] },
          { "Ma": [0|1, 0|1, ...] },
          { "Mi": [0|1, 0|1, ...] },
          { "Ju": [0|1, 0|1, ...] },
          { "Vi": [0|1, 0|1, ...] }
        ],
        /* Nota: además de `recursos.maestros`, el proyecto puede incluir
           metadatos por profesor dentro de `restricciones.PROFESORES`,
           p. ej.: */
        /* "respeta_max_carga_diaria": true,
           "max_carga_diaria": 8,
           "respeta_max_carga_semanal": true,
           "max_carga_semanal": "default" */
      }
    ],
    "estudiantes": [
      {
        "id": "string",
        "asignaturas": [
          { "codigo": "string", "paralelo": "string" }
        ]
      }
    ]
  }
}
```

---

## Sección por sección

## 1) `metadatos`

Objeto con información general.

Campos observados:
- `metadatos.institucion` (string): nombre de la institución/unidad.
- `metadatos.semestre` (string): identificador de semestre (por ejemplo `"2025-1"`).

## 2) `restricciones`

Objeto para guardar restricciones/parámetros del problema.

Campos soportados por el proyecto:
- `restricciones.MAX_CARGA_DIARIA` (int): máximo de horas PUCV de clases por día para un profesor.
- `restricciones.MAX_CARGA_BLOQUE` (int): máximo de clases por bloque.

Notas:
- Si faltan estas claves, el código usa valores por defecto (actualmente 8 y 15).

## 3) `tiempos`

Define los ejes temporales válidos:

- `tiempos.dias` (array de string): códigos de días.
  - En los datasets del proyecto se usan `Lu`, `Ma`, `Mi`, `Ju`, `Vi`.
- `tiempos.bloques` (array de string): claves de bloques.
  - Ejemplos: `"1-2"`, `"7-8"`, etc.

Recomendaciones:
- El orden de `dias` y `bloques` define el orden en tablas/horarios.
- Estos valores son los que se usan para validar `horario_predefinido`.

## 4) `eventos`

### 4.1) `eventos.tipo_clases`

- Array de strings que define los tipos de clases esperados.
- Ejemplo: `"Cát"`, `"Ay."`, `"Lab"`, `"Tal"`.

### 4.2) `eventos.asignaturas[]`

Cada asignatura tiene:

- `codigo` (string): código de asignatura (ej: `ICD1140`).
- `nombre` (string): nombre completo.
- `curso` (objeto): metadatos académicos.
  - `curso.carrera` (string): sigla de carrera (ej: `ICD`, `ICI`).
  - `curso.semestre` (string): semestre/nivel (en el JSON aparece como string, ej: `"01"`, `"05"`).
- `paralelos[]` (array): lista de paralelos.

#### 4.2.1) `paralelos[]`

Cada paralelo tiene:

- `codigo` (string): identificador del paralelo (ej: `"01"`).
- `maestros` (array de string): profesores “por defecto” asociados al paralelo.
- `clases[]` (array): clases/actividades (Cát, Ay., etc.).

#### 4.2.2) `clases[]`

Cada clase típicamente tiene:

- `tipo` (string): debe ser consistente con `eventos.tipo_clases`.

Opcionales:
- `maestros`:
  - Si **no existe** la propiedad `maestros`: la clase **hereda** los maestros del paralelo.
  - Si existe y es `null`: se interpreta como “sin maestros” para esa clase (no hereda).
  - Si existe y es array: lista de maestros específica de esa clase.
- `horario_predefinido`:
  - Si es un objeto: la clase tiene un horario fijo.
  - Si es `null` o no existe: la clase no tiene horario fijo.

Formato observado:

```json
"horario_predefinido": { "dia": "Lu", "bloque": "1-2" }
```

Notas:
- `dia` debe existir en `tiempos.dias`.
- `bloque` debe existir en `tiempos.bloques`.

---

## 5) `recursos`

### 5.1) `recursos.maestros[]`

Lista de maestros disponibles para planificación.

Campos:
- `nombre` (string)
- `disponibilidad` (array): disponibilidad semanal.

Formato observado de disponibilidad:

- `disponibilidad` es una lista de objetos, donde cada objeto tiene **una sola clave** de día.
- Cada día apunta a un arreglo de `0/1` con largo igual a la cantidad de bloques.

Ejemplo:

```json
"disponibilidad": [
  { "Lu": [1,1,1,1,1,1,1] },
  { "Ma": [1,1,1,1,1,1,1] },
  { "Mi": [1,1,1,1,1,1,1] },
  { "Ju": [1,1,1,0,1,1,1] },
  { "Vi": [1,1,1,1,1,1,1] }
]
```

Semántica:
- `1` = disponible
- `0` = no disponible

### 5.2) `recursos.estudiantes[]`

Representa demanda/inscripción.

Campos:
- `id` (string): identificador del estudiante.
- `asignaturas` (array): lista de inscripciones.

Cada inscripción:
- `codigo` (string): código de asignatura.
- `paralelo` (string): código del paralelo.

Ejemplo:

```json
{ "id": "0-0", "asignaturas": [ { "codigo": "ICI1001", "paralelo": "01" } ] }
```

---

## Convenciones y observaciones prácticas

- En el archivo editado aparecen asignaturas “placeholder” con `codigo`/`nombre` vacíos. Eso es válido como JSON, pero normalmente conviene eliminarlas si no deben participar en exportación/planificación.
- Las claves de bloque como `"7-8"` son strings: al exportar a Google Sheets conviene forzar formato de texto para que no se interpreten como fecha.
- Para generar horarios:
  - Un `horario_predefinido` define ubicación (día + bloque).
  - Los profesores de una clase se determinan así:
    1) Si la clase trae propiedad `maestros`: usarla (si es `null`, queda vacío).
    2) Si no trae `maestros`: hereda los del paralelo.

---

## Ejemplo mínimo completo

```json
{
  "metadatos": { "institucion": "X", "semestre": "2025-1" },
  "restricciones": {},
  "tiempos": { "dias": ["Lu","Ma"], "bloques": ["1-2","3-4"] },
  "eventos": {
    "tipo_clases": ["Cát"],
    "asignaturas": [
      {
        "codigo": "ABC123",
        "nombre": "EJEMPLO",
        "curso": { "carrera": "ICI", "semestre": "01" },
        "paralelos": [
          {
            "codigo": "01",
            "maestros": ["PROF X"],
            "clases": [
              { "tipo": "Cát", "horario_predefinido": { "dia": "Lu", "bloque": "1-2" } }
            ]
          }
        ]
      }
    ]
  },
  "recursos": {
    "maestros": [
      { "nombre": "PROF X", "disponibilidad": [ {"Lu":[1,1]}, {"Ma":[1,1]} ] }
    ],
    "estudiantes": [
      { "id": "0-0", "asignaturas": [ { "codigo": "ABC123", "paralelo": "01" } ] }
    ]
  }
}
```
