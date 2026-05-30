# Guía para leer el “Panel Detalle (última ejecución)”

Este documento explica qué significa cada métrica del panel y cómo se calcula, para interpretar el resultado sin tener que leer el código.

> **Contexto**: el panel se actualiza con cada ejecución de `evaluarFuncionObjetivo()` y se escribe en la hoja **“Evaluación de FO”**.

Nota importante: el script ahora escribe dos paneles en la misma hoja para facilitar la comparación:

- **Panel Detalle (optimizada con búsqueda local)**: resultado de la corrida estándar que incluye la fase de búsqueda local para mejorar ventanas.
- **Panel Detalle (DFS primera factible sin búsqueda local)**: segunda corrida que usa DFS y se detiene en la primera solución factible (sin aplicar búsqueda local). Esta segunda versión se coloca más abajo y está rotulada claramente.

Ambos paneles contienen las mismas secciones y columnas, por lo que puedes comparar directamente métricas (FO, choques, distribuciones y rankings).

---

## 0) Parámetros (hoja “Evaluación de FO”)

Estos parámetros controlan tanto la función objetivo como (opcionalmente) el modo en que se construyen los paralelos por estudiante.

Además, los parámetros se pueden configurar desde el **menú de la planilla** (UI), sin depender de celdas.

- **ALFA** (`I3`): exponente del ratio de desbalance.
- **CV IDEAL** (`I4`): CV objetivo por asignatura para estimar el desbalance “ideal”.
- **VENTANA IDEAL** (`I5`):
  - Se usa como “ventana ideal” al construir el ratio de ventana.
  - También es el **umbral** de penalización cuadrática para ventanas.
- **HOJA MALLA** (`I7`), **HOJA HORARIOS** (`I8`), **HOJA MATRÍCULAS** (`I9`): nombres de hojas de entrada.
- **RESOLVER SEGMENTACIÓN DE ESTUDIANTES** (`I10`, valor `0` o `1`):
  - `0` → **Usa los paralelos tal como vienen en matrícula** (no se re-asigna nada).
  - `1` → **Resuelve segmentación**: desde la lista de asignaturas por estudiante, el script elige un paralelo por asignatura para cada estudiante.

### 0.0 Menú UI (recomendado)

En la planilla, en el menú superior, existe **Evaluación FO** con:

- **Configurar parámetros…**: abre un panel lateral (sidebar) con los parámetros **prellenados**.
- **Restaurar parámetros (usar hoja)**: elimina la configuración guardada por UI y vuelve a leer desde la hoja “Evaluación de FO” (o defaults si esa hoja no existe).

**Dónde se guardan**: al guardar desde el sidebar, los valores quedan persistidos en **Propiedades del documento** (no en celdas). Esto evita estar editando rangos y hace más cómodo cambiar valores.

**Prioridad de lectura**:
1) Si existe configuración guardada desde UI → se usa esa.
2) Si no existe → se leen los parámetros desde la hoja.

> Nota: para compatibilidad, el script también intenta interpretar el valor de segmentación si quedó en otra celda (p.ej. `H11`), pero la vía recomendada es `I10` o el menú.

### 0.1 ¿Qué significa “resolver segmentación” en este contexto?

Cuando `RESOLVER SEGMENTACIÓN DE ESTUDIANTES = 1`, el panel y la FO se calculan sobre una asignación **construida por el solver** (no sobre lo declarado en matrícula).

Cuando `RESOLVER SEGMENTACIÓN DE ESTUDIANTES = 0`, el panel y la FO se calculan usando los **paralelos que vienen en la matrícula** (el script no re-asigna estudiantes).

La idea es: cada estudiante trae una lista de **asignaturas** (siglas), y el solver elige **qué paralelo** de cada asignatura tomará el estudiante, intentando:

1) **Minimizar choques** horarios del estudiante (prioridad #1).
2) **Balancear carga** entre paralelos (preferir paralelos con menor ocupación global al momento de asignar).
3) **Reducir ventanas** (mejora local) sin introducir choques nuevos.

---

## 1) Resumen superior del panel

- **FO**: valor total de la función objetivo que ya usas.
- **Ratio Desbalance**: razón entre el desbalance real y el ideal (con exponente `ALFA`).
- **Ratio Ventana**: razón entre ventanas reales y ventanas ideales.
- **Choques** (en el panel superior): corresponde a **Total Choques** del cálculo original (duplicados).

> Nota: el panel también muestra totales de ventanas/choques calculados “en detalle”. Debieran ser consistentes con los del cálculo original para choques duplicados (mismo concepto) y con ventanas *raw/penalizada* según definición.

---

## 2) Métricas por estudiante (las que se distribuyen)

### 2.1 Ventanas (raw)

**Qué es**: una medida de “huecos” dentro de un día, basada en los bloques ocupados por el estudiante.

**Cómo se calcula (por día)**:
1. Se listan los índices de bloque ocupados en ese día (0 a 6).
2. Por cada par consecutivo de bloques ocupados, se suma el **gap**:

   - `gap = bloque_siguiente - bloque_actual - 1`
   - si `gap > 0`, se suma tal cual.

3. **Regla de almuerzo**: si el estudiante tiene al menos un bloque en la mañana (`<= 3`) y otro en la tarde (`>= 4`) ese día, se suma **+1** adicional.

**Importante**:
- **Sí incluye la regla de almuerzo** (ese +1 por día cuando cruza de mañana a tarde).
- **No incluye choques** directamente (los choques son otra métrica).

### 2.2 Ventanas (penalizadas)

**Qué es**: una versión que castiga mucho cuando las ventanas superan un umbral.

**Cómo se calcula**:
- Si `ventanas_raw <= umbral` → `ventanas_penalizadas = ventanas_raw`
- Si `ventanas_raw > umbral` → `ventanas_penalizadas = umbral + (ventanas_raw - umbral)^2`

Donde **umbral = Ventana ideal** (configurable en `Evaluación de FO!I5`). Esto hace que pasar del umbral “cueste” cuadráticamente.

### 2.3 Choques (duplicados)

**Qué es**: cuántas clases se “pisan” en el mismo bloque horario, contado como **duplicados**.

**Interpretación**:
- Si en un mismo bloque el estudiante tiene `k` eventos (por ejemplo, 2 ramos a la vez), entonces aporta `k - 1` choques duplicados.

**Ejemplos**:
- 2 clases simultáneas en un bloque → `1` choque duplicado.
- 3 clases simultáneas en un bloque → `2` choques duplicados.

Este concepto coincide con el que usabas en el cálculo original:

- `choques_duplicados = (#eventos totales) - (#bloques únicos)`

**Importante (doble sala, no es choque real)**:
- Si un **mismo paralelo** aparece repetido en el mismo bloque por tener **2 salas** para la misma clase, **NO se considera choque**.
- En términos prácticos, esos duplicados se **colapsan** antes de contar choques.

Ejemplo: si para un solo paralelo se obtienen bloques `[1,4,5,5,9,9]`, entonces los duplicados en `5` y `9` **no cuentan como choques** (se interpreta como una sola clase con dos salas).

### 2.4 Choques (grupos)

**Qué es**: cantidad de **bloques horarios** que presentan al menos un choque.

**Interpretación**:
- Si en un bloque hay 2 o 3 clases simultáneas, igualmente cuenta como **1** choque de tipo “grupo” (porque es 1 slot con colisión).

---

## 3) Distribuciones

En el panel aparecen dos tablas de distribución:

- **Distribución Ventanas**: muestra el valor exacto de ventanas por estudiante, el acumulado `<= raw` y su porcentaje sobre el total con carga.
- **Distribución Choques (duplicados)**: para cada valor `y`, cuántos estudiantes tienen `choques_duplicados = y`.

Ambas tablas muestran además el **% de alumnos sobre el total con carga**.

Estas distribuciones ayudan a ver si el problema está concentrado (pocos estudiantes muy afectados) o disperso.

---

## 4) Rankings (Top) por asignatura / paralelo

Antes de los rankings, el panel incluye una sección de **Matrícula por asignatura / por paralelo**:
- **Matrícula por asignatura**: cuántos estudiantes (con carga) cursan cada asignatura.
- **Matrícula por paralelo**: cuántos estudiantes (con carga) están asignados a cada paralelo.

Estas tablas también muestran el **% de alumnos sobre el total con carga** para leerlas más rápido.

La lista se ordena de mayor a menor y puede recortarse para no ocupar todo el panel.

### 4.1 “Top … por ventanas (estimado)”

Estas tablas responden a: “¿Qué cursos/paralelos aparecen más asociados a ventanas?”

**Ojo**: es una **atribución estimada**, porque las ventanas emergen de la combinación de ramos:
- Para un gap entre dos bloques del día, el gap se atribuye al/los paralelo(s) del bloque “anterior”.
- El +1 de almuerzo se atribuye al/los paralelo(s) del último bloque de la mañana.

### 4.2 “Top … por choques (dup)”

Para choques la atribución es más directa:
- En un bloque con choque (k eventos), el total `k-1` se reparte entre los paralelos involucrados.
- Esto evita sobrecontar cuando hay varios ramos chocando simultáneamente.

**Por qué a veces aparecen decimales**:
- El **choque duplicado por estudiante** (sección 2.3) y su **distribución** (sección 3) siempre son **enteros**, porque cuentan eventos repetidos por bloque.
- En cambio, en los rankings “Top … por choques (dup)” el panel muestra una **atribución estimada por paralelo/asignatura** que **prorratea** el choque cuando participan varios paralelos en el mismo bloque.

**Regla de prorrateo usada** (por cada bloque con choque):
- Si en un bloque coinciden `k` eventos (paralelos) distintos, el choque total del bloque es `k - 1`.
- A cada paralelo involucrado se le asigna una fracción:

  - `shareDup = (k - 1) / k`

**Ejemplos**:
- Si chocan 2 paralelos en el mismo bloque: choque total `= 1`, cada paralelo recibe `1/2 = 0.5`.
- Si chocan 3 paralelos: choque total `= 2`, cada paralelo recibe `2/3 ≈ 0.6667`.

Luego, al sumar estas fracciones a lo largo de todos los estudiantes y bloques (y al agregar por asignatura), es normal que el “Top … por choques (dup)” muestre valores con decimales.

### 4.3 “Top pares de choque (… )”

Estas secciones responden a: **“¿Qué dos clases chocan directamente, y en qué bloque ocurre más?”**

Se muestran dos variantes:
- **Top pares de choque (paralelos)**: el par es del tipo `CURSO-01 vs OTRO-02`.
- **Top pares de choque (asignaturas)**: el par es del tipo `CURSO vs OTRO` (se ignora el número de paralelo).

**Cómo se contabiliza**:
- Se usa la colisión real observada en horarios de estudiantes: si en un mismo bloque el estudiante tiene más de una clase, se generan todas las combinaciones de pares.
- En un bloque con `k` eventos simultáneos, se suman `C(k,2)` pares (por ejemplo, si chocan A, B y C, se registran A–B, A–C y B–C).

**Bloques**:
- Para cada par, el panel lista los 3 bloques donde más se repite el choque, como lista de bloques: `Lu 5 - 6, Mi 9 - 10, ...`.

#### Nuevas columnas (priorización)

Además de **Ocurr** (ocurrencias) y **Bloques**, se muestran columnas para priorizar si conviene reajustar horarios:

- **Alum ambos**: cantidad de alumnos que **cursan ambos** elementos del par.
  - En pares de **asignaturas**, es: alumnos que toman `CURSO` y `OTRO` (independiente de paralelos).
  - En pares de **paralelos**, es: alumnos que toman `CURSO-01` y `OTRO-02`.

- **% afec/total izq** y **% afec/total der**:
  - Usan como denominador el total de alumnos matriculados en el elemento izquierdo/derecho (incluye a quienes también toman el otro).
  - Definición: `alumnos_afectados / alumnos_total_izq` y `alumnos_afectados / alumnos_total_der`.
  - Ayudan a ver “qué tan grande” es el choque respecto a la matrícula de cada lado.

**Nota importante sobre “alumnos afectados”**:
- Se cuenta por alumno (0/1) por par: si un alumno tiene 2 choques del mismo par en dos bloques distintos, sigue contando como **1 alumno afectado**.
- En cambio, **Ocurr** sí puede sumar 2 (porque cuenta ocurrencias por bloque).

---

## 5) Tierlist desbalance (CV desc)

Esta sección ordena asignaturas por **coeficiente de variación** (CV) de sus paralelos.

Para cada asignatura:
- Se toma la ocupación por paralelo (cantidad de alumnos asignados a cada paralelo).
- Se calcula:
  - `media = promedio(inscritos)`
  - `sigma = desviación estándar(inscritos)`
  - `cv = sigma / media`

**Cómo leerlo**:
- CV alto → paralelos muy desbalanceados (uno muy lleno y otro muy vacío, etc.).
- Se muestra además “Paralelos (ocupación)” como una lista tipo `CURSO-01:34, CURSO-02:12, ...`.

---

## 6) Recomendación práctica (cómo usarlo para decidir)

- Si tu objetivo es **reducir choques**, mira primero:
  - Distribución de choques (duplicados)
  - Top asignaturas/paralelos por choques

- Si tu objetivo es **mejorar calidad de vida (ventanas)**, mira:
  - Distribución de ventanas (raw)
  - Top asignaturas/paralelos por ventanas (estimado)

- Si tu objetivo es **equidad entre paralelos**, mira:
  - Tierlist desbalance (CV)

---

## 7) Glosario rápido

- **Bloque**: ranura horaria discretizada (por día hay 7 índices: 0..6).
- **Ventana**: hueco (bloque libre) entre dos clases del mismo día.
- **Almuerzo**: penalización +1 si hay clases en mañana y tarde el mismo día.
- **Choque duplicado**: exceso de clases simultáneas medido como `k-1`.
- **Choque grupo**: número de ranuras con colisión (independiente de k).
