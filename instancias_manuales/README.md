# Editor de Instancias Manuales — Planificador Académico JSON

Este directorio contiene una interfaz web autónoma para crear y editar instancias JSON del planificador académico.

## Archivo principal

- `planificador_academico_json.html`: editor autónomo que se abre directamente en el navegador. No requiere servidor ni dependencias externas.

## Uso

Abre el archivo directamente en el navegador o desde VS Code con Live Server para una experiencia más fluida.

---

## Funcionalidades

### 1. Carga de archivo JSON
- Botón **"Archivo base"**: carga un JSON existente para editarlo.
- Al cargar, se rellenan automáticamente los campos de metadatos, restricciones, maestros y planilla.

### 2. Metadatos e identificación
- **Nombre de salida**: personaliza el nombre del archivo descargado.
- **Semestre**: ej. `2025-1`.
- **Descripción**: opcional, se omite del JSON si queda vacía.
- **Institución**: fija como `PUCV - Escuela de Ingeniería en Informática`.

### 3. Restricciones globales
- **MAX_CARGA_DIARIA**: máximo de horas PUCV de clases por día para un profesor.
- **MAX_CARGA_BLOQUE**: máximo de clases que pueden coincidir en un mismo bloque horario.

### 4. Carga de estudiantes desde CSV
- Botón **"Cargar estudiantes"**: importa una lista de estudiantes desde un archivo CSV.
- Formato esperado (una línea por estudiante):
  ```
  ID_ESTUDIANTE;CODIGO_ASIGNATURA-01,OTRA_ASIGNATURA-02
  ```
- Si no se especifica el paralelo, se asume `"01"`.
- Los datos se almacenan en `recursos.estudiantes`.

### 5. Contadores
- Muestra en tiempo real la cantidad de **Asignaturas**, **Paralelos**, **Clases** y **Maestros** cargados.

### 6. Editor de asignaturas
- **Código**: identificador único de la asignatura (ej. `ICD9999`). Valida duplicados al guardar.
- **Nombre**: nombre completo de la asignatura.
- **Carrera y Semestre de carrera**: datos del curso. Se pueden deshabilitar con el checkbox *"Esta asignatura pertenece a una carrera/semestre"*.
- **Paralelos**: cada paralelo incluye:
  - Código de paralelo (ej. `01`).
  - Maestros del paralelo (separados por coma).
  - **Restricción de clases teóricas**: define cómo se programan las clases teóricas:
    - *Sin restricción*: pueden ir en cualquier día/bloque.
    - *Días distintos*: las teóricas deben ir en días diferentes (pueden ser consecutivos).
    - *Separadas con al menos 1 día*: debe haber al menos un día de por medio entre teóricas.
  - **Clases** (ver sección siguiente).
- Botones del editor:
  - **"Nueva asignatura"**: limpia el formulario para crear una desde cero.
  - **"Plantilla abanico"**: precarga 2 clases de tipo `Cát` y 1 de tipo `Ay.` (sin maestro).
  - **"Agregar paralelo"**: añade un paralelo vacío.
  - **"Guardar asignatura"**: guarda (o actualiza) la asignatura en la planilla. Valida campos obligatorios y duplicados.

### 7. Editor de clases (dentro de cada paralelo)
- **Tipo**: desplegable con los tipos de clase disponibles (ej. `Cát`, `Ay.`, `Lab`, `Tal`).
- **Maestros en clase**: tres modos:
  - *Omitir*: hereda los maestros definidos a nivel de paralelo.
  - *null*: la clase no tiene maestro (se guarda como `null`).
  - *Lista propia*: lista de maestros específica para esta clase (separados por coma).
- **Horario predefinido**: opcional. Al activar el checkbox, se habilitan campos de **día** (ej. `Lu`) y **bloque** (ej. `3-4`).
- **"Plantilla 2 Cát + 1 Ay."**: reemplaza todas las clases del paralelo por 2 Cát y 1 Ay. con maestro `null`.
- **"Agregar clase"**: añade una clase vacía.
- **"Quitar clase"**: elimina la clase del paralelo.

### 8. Planilla en abanico (vista jerárquica)
- Muestra la estructura completa de asignaturas, paralelos y clases en formato colapsable.
- **"Abrir todo"** / **"Cerrar todo"**: expande o contrae todos los niveles.
- Cada asignatura muestra: código, nombre, carrera-semestre y cantidad de paralelos.
- Cada paralelo muestra: código, maestros, cantidad de clases y restricción de teóricas.
- Cada clase muestra: código, nombre, carrera, paralelo, tipo, maestros y horario.
- Botones contextuales:
  - **"Editar asignatura"**: carga los datos de la asignatura en el editor para modificarlos.
  - **"Quitar asignatura"**: elimina la asignatura completa.
  - **"Quitar paralelo"**: elimina el paralelo de la asignatura.
  - **"Quitar clase"**: elimina la clase del paralelo.

### 9. Recursos de maestros
- **"Sincronizar desde planilla"**: detecta automáticamente todos los maestros mencionados en asignaturas, paralelos o clases y los agrega a la lista (evita duplicados).
- **"Agregar maestro"**: añade un maestro manualmente.
- Cada maestro incluye:
  - **Nombre**: editable.
  - **Matriz de disponibilidad**: cuadrícula interactiva de días × bloques. Cada celda se activa/desactiva con clic para indicar disponibilidad.
  - **Restricciones del profesor**:
    - *Respetar carga máxima diaria*: activa/desactiva y define el máximo de clases por día (por defecto `MAX_CARGA_DIARIA / 2`).
    - *Respetar carga máxima semanal*: activa/desactiva y define el máximo de días con clases por semana (por defecto: 3 si horas PUCV ≤ 12, sino 4).
- Botones por maestro:
  - **"Guardar maestro"**: persiste los cambios.
  - **"Quitar maestro"**: elimina el maestro de la lista.

### 10. Vista previa JSON en vivo
- Panel que muestra el JSON completo generado en tiempo real.
- Se actualiza automáticamente con cada cambio en el formulario, editor, maestros o planilla.

### 11. Descarga de JSON
- Botón **"Descargar JSON"**: genera el archivo JSON con el nombre especificado en "Nombre de salida".
- Incluye todos los metadatos, restricciones, asignaturas, paralelos, clases, maestros (con disponibilidad y restricciones) y estudiantes.

## Relación con el proyecto

Esta herramienta complementa al planificador principal y al generador de instancias:

- `UCTPPlanner.py` consume los JSON finales para generar horarios.
- `scripts/generador_instancias.py` crea instancias sintéticas automáticamente.
- `instancias_manuales/planificador_academico_json.html` permite editar instancias a mano con interfaz visual.
