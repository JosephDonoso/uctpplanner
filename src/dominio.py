# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from src.uctp_utils import _normalizar_id_estudiante, normalizar_id_estudiante

if TYPE_CHECKING:
  from src.solver import Modelo
# ----------------------------------------------------------------------
class Dia(Enum):
    LUNES = 1
    MARTES = 2
    MIERCOLES = 3
    JUEVES = 4
    VIERNES = 5

class TipoClase(Enum):
    CATEDRA = 1
    AYUDANTIA = 2
    TALLER = 3
    LABORATORIO = 4

class Sesion:
  """
  Representación de una sesión semanal o clase (a,p,s).

  Atrs:
    tipo: Tipo de clase.
    id_sesion: Número de la clase en la asignatura.
    id_paralelo: Número de paralelo al que pertenece.
    id_asignatura: Código de la asignatura a la que pertenece.
  """
  def __init__(self,
               tipo: TipoClase,
               id_sesion,
               id_paralelo,
               id_asignatura):
    self.tipo_clase = tipo
    self.id_asignatura = id_asignatura
    self.id_paralelo = id_paralelo
    self.id_sesion = id_sesion

class Paralelo:
  """
  Representación de un paralelo (a,p).

  Atrs:
    id_paralelo: Número de paralelo.
    id_asignatura: Código de la asignatura a la que pertenece.
    sesiones: Lista de clases del paralelo.
  """
  def __init__(self, id_paralelo, id_asignatura):
    self.id_paralelo = id_paralelo
    self.id_asignatura = id_asignatura
    self.sesiones: List[Sesion] = []
    # Lista de maestros por defecto del paralelo (export JSON)
    self.maestros: List[str] = []
    self.restriccion_teoricas: str = 'none'

class Asignatura:
  """
  Representación de una asignatura (a).

  Atrs:
    id_asignatura: Código de la asignatura.
    asignatura: Nombre de la asignatura.
    paralelos: Lista de paralelos de la asignatura.
  """
  def __init__(self, id_asignatura, asignatura):
    self.id_asignatura = id_asignatura
    self.asignatura = asignatura
    self.paralelos: List[Paralelo] = []
    # Metadatos de curso (export JSON)
    self.curso_carrera: Optional[str] = None
    self.curso_semestre: Optional[str] = None

# El número máximo de días con clases está dado por la cantidad
# de horas de cátedra que imparte el maestro:
# si horas <= 12 horas PUCV = 3 días máximo de clase
# si no 4 días máximo de clase
class Maestro:
  """
  Representación de un maestro (m).

  Atrs:
    id_maestro: Número de identificación del maestro.
    nombre: Nombre del maestro.
    max_carga_diaria: Número máximo de clases por día que puede impartir.
    max_carga_semanal: Número máximo de días que imparte clases.
    clases: Lista de clases específicas que imparte.
    disponibilidad: Períodos en los cuales está disponible el maestro.
  """
  def __init__(self, id_maestro, nombre):
    self.id_maestro = id_maestro
    self.nombre = nombre
    self.max_carga_diaria: int = 0
    self.max_carga_semanal: int = 0
    self.respeta_max_carga_diaria: bool = True
    self.respeta_max_carga_semanal: bool = True
    self.clases: List[Sesion] = []
    self.disponibilidad: List[Bloque] = []


class Estudiante:
  """
  Representación de un estudiante (e).

  Atrs:
    id_estudiante: Número de identificación del alumno.
    nombre: Nombre del alumno (Default None).
    asignaturas: Lista de asignaturas que puede cursar.
  """
  def __init__(self, id_estudiante, nombre = None):
    self.id_estudiante = id_estudiante
    self.nombre = nombre
    self.asignaturas: List[Asignatura] = []

# No se modela a los estudiantes pertenecientes al curso para
# minimizar redundancias de carga o inconsistencia con alumnos que
# se encuentren en desfase con su período del plan curricular
class Curso:
  """
  Representación de un período académico de un plan de estudios
  que agrupa a un conjunto de estudiantes (e').

  Atrs:
    id_curso: Número de identificación del curso.
    asignaturas: Lista de asignaturas asignadas al curso.
  """
  def __init__(self, id_curso):
    self.id_curso = id_curso
    self.asignaturas: List[Asignatura] = []

class Bloque:
  """
  Representación de un bloque horario en el que se puede
  dictar una clase (b).

  Atrs:
    id_bloque: Número de identificación del bloque.
    dia: Día de la semana en el que se programa el bloque.
  """
  def __init__(self, id_bloque, dia: Dia):
    self.id_bloque = id_bloque
    self.dia = dia

class Preasignacion:
  """
  Representación de una preasignación (a,p,s,b)

  Atrs:
    sesion: Clase preasignada (a,p,s).
    bloque: Bloque en el que se programa la clase (b).
  """
  def __init__(self, sesion: Sesion, bloque: Bloque):
    self.sesion = sesion
    self.bloque = bloque

# ----------------------------------------------------------------------
# DOMINIO DEL PROBLEMA
# ----------------------------------------------------------------------
class Dominio:
  """
  Representación del dominio del problema.

  Atrs:
    MAX_CARGA_DIARIA: Número máximo de horas PUCV de clases por día para un profesor.
    MAX_CARGA_BLOQUE: Número máximo de clases por bloque.
    BLOQUES_DIARIOS: Número de bloques por día.
    asignaturas: Lista de asignaturas.
    estudiantes: Lista de estudiantes.
    cursos: Lista de cursos.
    maestros: Lista de maestros.
    bloques: Lista de bloques.
    preasignaciones: Lista de preasignaciones.
  """
  MAX_CARGA_DIARIA = 8
  MAX_CARGA_BLOQUE = 15
  BLOQUES_DIARIOS = 7
  asignaturas: List[Asignatura] = []
  estudiantes: List[Estudiante] = []
  cursos: List[Curso] = []
  cursos_optimos: List[Curso] = []
  maestros: List[Maestro] = []
  bloques: List[Bloque] = []
  preasignaciones: List[Preasignacion] = []

  _X = {}


  def __init__(self, json_path: str = "Semestre 2025-1.editado.json"):
    self.MAX_CARGA_DIARIA = 8
    self.MAX_CARGA_BLOQUE = 15
    self.BLOQUES_DIARIOS = 7
    self.asignaturas: List[Asignatura] = []
    self.estudiantes: List[Estudiante] = []
    self.cursos: List[Curso] = []
    self.maestros: List[Maestro] = []
    self.bloques: List[Bloque] = []
    self.preasignaciones: List[Preasignacion] = []
    self.restricciones_clases_teoricas_dias_distintos_json: List = []
    self.restricciones_clases_teoricas_separadas_1_dia_json: List = []
    self.restricciones_clases_teoricas_dias_distintos: Set[Tuple[int, int, int]] = set()
    self.restricciones_clases_teoricas_separadas_1_dia: Set[Tuple[int, int, int]] = set()

    self._X = {}

    self.cargar_desde_json(json_path)

  def cargar_desde_json(self, json_path: str) -> None:
    """Carga el dominio desde un JSON UCTP (ver ESTRUCTURA_JSON_UCTP.md)."""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
      data = json.load(f)

    # Restricciones (parámetros de dominio)
    restricciones = data.get('restricciones', {})
    if not isinstance(restricciones, dict):
      restricciones = {}

    def _as_int(value, default: int) -> int:
      try:
        if value is None or value == "":
          return default
        return int(value)
      except Exception:
        return default

    def _as_bool(value, default: bool) -> bool:
      if isinstance(value, bool):
        return value
      if value is None:
        return default
      s = str(value).strip().lower()
      if s in ("1", "true", "t", "si", "sí", "yes", "y"):
        return True
      if s in ("0", "false", "f", "no", "n"):
        return False
      return default

    def _as_int_opt(value):
      try:
        if value is None or value == "":
          return None
        return int(value)
      except Exception:
        return None

    def _extraer_restricciones_teoricas(item, base_codigo: str = "", base_paralelo: str = "") -> List[Tuple[str, str, int]]:
      if item is None:
        return []

      if isinstance(item, dict):
        codigo_asignatura = str(
          item.get('codigo_asignatura')
          or item.get('id_asignatura')
          or item.get('asignatura')
          or item.get('codigo')
          or base_codigo
          or ''
        ).strip()
        codigo_paralelo = str(
          item.get('codigo_paralelo')
          or item.get('id_paralelo')
          or item.get('paralelo')
          or base_paralelo
          or ''
        ).strip()

        if 'clases' in item or 'sesiones' in item:
          resultado: List[Tuple[str, str, int]] = []
          for subitem in (item.get('clases') or item.get('sesiones') or []):
            resultado.extend(_extraer_restricciones_teoricas(subitem, codigo_asignatura, codigo_paralelo))
          return resultado

        idx_sesion = _as_int_opt(
          item.get('clase')
          or item.get('sesion')
          or item.get('id_sesion')
          or item.get('indice')
          or item.get('numero')
        )
        if codigo_asignatura and codigo_paralelo and idx_sesion is not None:
          return [(codigo_asignatura, codigo_paralelo, idx_sesion)]
        return []

      if isinstance(item, (list, tuple)):
        if len(item) >= 3:
          codigo_asignatura = str(item[0]).strip()
          codigo_paralelo = str(item[1]).strip()
          idx_sesion = _as_int_opt(item[2])
          if codigo_asignatura and codigo_paralelo and idx_sesion is not None:
            return [(codigo_asignatura, codigo_paralelo, idx_sesion)]
        return []

      if isinstance(item, (int, float)) and base_codigo and base_paralelo:
        idx_sesion = _as_int_opt(item)
        if idx_sesion is not None:
          return [(base_codigo, base_paralelo, idx_sesion)]

      if isinstance(item, str):
        raw = item.strip()
        if not raw:
          return []
        for sep in ('|', ';', ',', '/'):
          parts = [part.strip() for part in raw.split(sep)]
          if len(parts) >= 3:
            idx_sesion = _as_int_opt(parts[2])
            if parts[0] and parts[1] and idx_sesion is not None:
              return [(parts[0], parts[1], idx_sesion)]
        return []

      return []

    self.MAX_CARGA_DIARIA = _as_int(restricciones.get('MAX_CARGA_DIARIA'), self.MAX_CARGA_DIARIA)
    self.MAX_CARGA_BLOQUE = _as_int(restricciones.get('MAX_CARGA_BLOQUE'), self.MAX_CARGA_BLOQUE)
    self.restricciones_clases_teoricas_dias_distintos_json = list(restricciones.get('CLASES_TEORICAS_DIAS_DISTINTOS', []) or [])
    self.restricciones_clases_teoricas_separadas_1_dia_json = list(restricciones.get('CLASES_TEORICAS_SEPARADAS_1_DIA', []) or [])

    # Restricciones por profesor (si existen). Formato esperado:
    # restricciones.PROFESORES = [{nombre, max_carga_diaria, ...}, ...]
    profesores_restricciones: Dict[str, Dict] = {}
    for item in (restricciones.get('PROFESORES', []) or []):
      if not isinstance(item, dict):
        continue
      nombre_prof = str(item.get('nombre') or '').strip()
      if not nombre_prof:
        continue
      profesores_restricciones[nombre_prof.lower()] = item

    def _max_carga_diaria_maestro(nombre_maestro: str) -> int:
      item = profesores_restricciones.get(str(nombre_maestro).lower())
      if isinstance(item, dict):
        # Si explícitamente no respeta la carga diaria, mantenemos fallback global.
        if _as_bool(item.get('respeta_max_carga_diaria'), True) is False:
          return self.MAX_CARGA_DIARIA
        valor = _as_int(item.get('max_carga_diaria'), self.MAX_CARGA_DIARIA)
        if valor > 0:
          return valor
      return self.MAX_CARGA_DIARIA

    def _max_carga_semanal_maestro(nombre_maestro: str, carga_auto: int) -> int:
      item = profesores_restricciones.get(str(nombre_maestro).lower())
      if isinstance(item, dict):
        # Si no respeta carga semanal o viene en default, mantenemos fallback automático.
        if _as_bool(item.get('respeta_max_carga_semanal'), True) is False:
          return carga_auto
        valor = _as_int(item.get('max_carga_semanal'), carga_auto)
        if valor > 0:
          return valor
      return carga_auto

    tiempos = data.get('tiempos', {})
    dias = tiempos.get('dias', ["Lu", "Ma", "Mi", "Ju", "Vi"])
    bloques = tiempos.get('bloques', ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14"])

    # Mantener coherencia con la definición de tiempos del JSON
    self.BLOQUES_DIARIOS = len(bloques)

    dia_enum = {
      "Lu": Dia.LUNES,
      "Ma": Dia.MARTES,
      "Mi": Dia.MIERCOLES,
      "Ju": Dia.JUEVES,
      "Vi": Dia.VIERNES,
    }

    # Bloques horarios
    self.bloques = []
    bloque_por_clave: Dict[Tuple[str, str], Bloque] = {}
    for d in dias:
      d_enum = dia_enum.get(d)
      if d_enum is None:
        continue
      for b in bloques:
        b_str = str(b).replace('-', ' - ')
        cod = f"{d} {b_str}"
        obj = Bloque(cod, d_enum)
        self.bloques.append(obj)
        bloque_por_clave[(d, str(b))] = obj

    # Maestros
    self.maestros = []
    maestros_unicos: Dict[str, Maestro] = {}
    recursos = data.get('recursos', {})
    for m in recursos.get('maestros', []) or []:
      nombre = (m or {}).get('nombre')
      if not nombre:
        continue
      nombre = str(nombre)
      maestro = Maestro(nombre, nombre)
      maestro.max_carga_diaria = _max_carga_diaria_maestro(nombre)
      maestro.respeta_max_carga_diaria = _as_bool((profesores_restricciones.get(nombre.lower()) or {}).get('respeta_max_carga_diaria'), True)
      maestros_unicos[nombre] = maestro
      self.maestros.append(maestro)

      # Disponibilidad: lista de {"Lu": [0/1,...]}
      for dia_obj in (m or {}).get('disponibilidad', []) or []:
        if not isinstance(dia_obj, dict) or not dia_obj:
          continue
        d, arr = next(iter(dia_obj.items()))
        if d is None:
          continue
        d = str(d)
        if not isinstance(arr, list):
          continue
        for i, val in enumerate(arr):
          if i >= len(bloques):
            break
          if int(val) == 1:
            blk = bloque_por_clave.get((d, str(bloques[i])))
            if blk is not None:
              maestro.disponibilidad.append(blk)

    # Asignaturas / cursos / paralelos / clases
    self.asignaturas = []
    self.cursos = []
    asignaturas_unicas: Dict[str, Asignatura] = {}
    cursos_unicos: Dict[str, Curso] = {}
    sesion_por_clave: Dict[Tuple[str, str, int], Sesion] = {}

    tipo_map = {
      "Cát": TipoClase.CATEDRA,
      "Cat": TipoClase.CATEDRA,
      "Ay.": TipoClase.AYUDANTIA,
      "Ay": TipoClase.AYUDANTIA,
      "Lab": TipoClase.LABORATORIO,
      "Tal": TipoClase.TALLER,
    }

    for a in (data.get('eventos', {}) or {}).get('asignaturas', []) or []:
      if not isinstance(a, dict):
        continue
      cod_a = a.get('codigo')
      nombre_a = a.get('nombre')
      if not cod_a:
        continue
      cod_a = str(cod_a)
      asignatura = Asignatura(cod_a, "" if nombre_a is None else str(nombre_a))
      curso = a.get('curso') or {}
      asignatura.curso_carrera = None if curso.get('carrera') in (None, "") else str(curso.get('carrera'))
      asignatura.curso_semestre = None if curso.get('semestre') in (None, "") else str(curso.get('semestre'))
      self.asignaturas.append(asignatura)
      asignaturas_unicas[cod_a] = asignatura

      # Cursos (solo si hay semestre definido en el JSON)
      carrera = asignatura.curso_carrera
      sem = asignatura.curso_semestre
      if carrera and sem and str(sem).isdigit():
        cod_curso = f"{carrera}-{int(sem)}"
        if cod_curso not in cursos_unicos:
          c = Curso(cod_curso)
          cursos_unicos[cod_curso] = c
          self.cursos.append(c)
        cursos_unicos[cod_curso].asignaturas.append(asignatura)

      for p in a.get('paralelos', []) or []:
        if not isinstance(p, dict) or not p.get('codigo'):
          continue
        cod_p = str(p.get('codigo'))
        paralelo = Paralelo(cod_p, cod_a)
        paralelo.maestros = [str(x) for x in (p.get('maestros', []) or []) if str(x).strip()]
        restriccion_teorica = str(p.get('restriccion_teoricas') or 'none').strip().lower()
        if restriccion_teorica in ('days_distinct', 'days_gap_1', 'none'):
          paralelo.restriccion_teoricas = restriccion_teorica

        clases = p.get('clases', []) or []
        for idx_s, c_json in enumerate(clases, start=1):
          if not isinstance(c_json, dict):
            continue
          tipo_str = c_json.get('tipo')
          if not tipo_str:
            continue
          tipo_enum_val = tipo_map.get(str(tipo_str), None)
          if tipo_enum_val is None:
            continue
          sesion = Sesion(tipo_enum_val, idx_s, cod_p, cod_a)
          paralelo.sesiones.append(sesion)
          sesion_por_clave[(cod_a, cod_p, idx_s)] = sesion

          # Maestros para esta clase
          if 'maestros' in c_json:
            maestros_clase = [] if c_json.get('maestros') is None else list(c_json.get('maestros') or [])
          else:
            maestros_clase = list(paralelo.maestros)

          for nombre_m in [str(x) for x in maestros_clase if str(x).strip()]:
            maestro = maestros_unicos.get(nombre_m)
            if maestro is None:
              maestro = Maestro(nombre_m, nombre_m)
              maestro.max_carga_diaria = _max_carga_diaria_maestro(nombre_m)
              maestro.respeta_max_carga_diaria = _as_bool((profesores_restricciones.get(nombre_m.lower()) or {}).get('respeta_max_carga_diaria'), True)
              # Si no viene en recursos, asumimos disponibilidad total
              maestro.disponibilidad = list(self.bloques)
              maestros_unicos[nombre_m] = maestro
              self.maestros.append(maestro)
            if sesion.tipo_clase != TipoClase.AYUDANTIA:
              maestro.clases.append(sesion)

          # Preasignación si el JSON trae horario_predefinido
          hp = c_json.get('horario_predefinido')
          if isinstance(hp, dict):
            d_hp = hp.get('dia')
            b_hp = hp.get('bloque')
            if d_hp is not None and b_hp is not None:
              blk = bloque_por_clave.get((str(d_hp), str(b_hp)))
              if blk is not None:
                self.preasignaciones.append(Preasignacion(sesion, blk))

        asignatura.paralelos.append(paralelo)

    def _resolver_restricciones_teoricas(raw_items: List) -> Set[Tuple[int, int, int]]:
      resultado: Set[Tuple[int, int, int]] = set()
      for item in raw_items or []:
        if isinstance(item, dict):
          cod_a = str(
            item.get('codigo_asignatura')
            or item.get('id_asignatura')
            or item.get('asignatura')
            or item.get('codigo')
            or ''
          ).strip()
          cod_p = str(
            item.get('codigo_paralelo')
            or item.get('id_paralelo')
            or item.get('paralelo')
            or ''
          ).strip()
          idx_s = _as_int_opt(
            item.get('clase')
            or item.get('sesion')
            or item.get('id_sesion')
            or item.get('indice')
            or item.get('numero')
          )
          if cod_a and cod_p and idx_s is None:
            for idx_a, asignatura in enumerate(self.asignaturas):
              if str(asignatura.id_asignatura) != cod_a:
                continue
              for idx_p, paralelo in enumerate(asignatura.paralelos):
                if str(paralelo.id_paralelo) != cod_p:
                  continue
                for idx_s_real in range(len(paralelo.sesiones)):
                  resultado.add((idx_a, idx_p, idx_s_real))
                break
              break

        for cod_a, cod_p, idx_s in _extraer_restricciones_teoricas(item):
          sesion = sesion_por_clave.get((cod_a, cod_p, idx_s))
          if sesion is None:
            continue
          for idx_a, asignatura in enumerate(self.asignaturas):
            if str(asignatura.id_asignatura) != str(cod_a):
              continue
            for idx_p, paralelo in enumerate(asignatura.paralelos):
              if str(paralelo.id_paralelo) != str(cod_p):
                continue
              for idx_s_real, sesion_real in enumerate(paralelo.sesiones):
                if sesion_real is sesion and sesion_real.id_sesion == idx_s:
                  resultado.add((idx_a, idx_p, idx_s_real))
                  break
      return resultado

    self.restricciones_clases_teoricas_dias_distintos = _resolver_restricciones_teoricas(self.restricciones_clases_teoricas_dias_distintos_json)
    self.restricciones_clases_teoricas_separadas_1_dia = _resolver_restricciones_teoricas(self.restricciones_clases_teoricas_separadas_1_dia_json)

    for idx_a, asignatura in enumerate(self.asignaturas):
      for idx_p, paralelo in enumerate(asignatura.paralelos):
        if getattr(paralelo, 'restriccion_teoricas', 'none') not in ('days_distinct', 'days_gap_1', 'none'):
          paralelo.restriccion_teoricas = 'none'
        if paralelo.restriccion_teoricas == 'none':
          if any((idx_a, idx_p, idx_s) in self.restricciones_clases_teoricas_separadas_1_dia for idx_s in range(len(paralelo.sesiones))):
            paralelo.restriccion_teoricas = 'days_gap_1'
          elif any((idx_a, idx_p, idx_s) in self.restricciones_clases_teoricas_dias_distintos for idx_s in range(len(paralelo.sesiones))):
            paralelo.restriccion_teoricas = 'days_distinct'

    # Estudiantes
    self.estudiantes = []
    estudiantes_unicos: Dict[str, Estudiante] = {}
    for e in (recursos.get('estudiantes', []) or []):
      if not isinstance(e, dict) or e.get('id') is None:
        continue
      id_e = _normalizar_id_estudiante(e.get('id'))
      if not id_e:
        continue
      estudiante = estudiantes_unicos.get(id_e)
      if estudiante is None:
        estudiante = Estudiante(id_e)
        estudiantes_unicos[id_e] = estudiante
        self.estudiantes.append(estudiante)

      for a_insc in e.get('asignaturas', []) or []:
        if not isinstance(a_insc, dict):
          continue
        cod = a_insc.get('codigo')
        if not cod:
          continue
        asignatura = asignaturas_unicas.get(str(cod))
        if asignatura is not None and asignatura not in estudiante.asignaturas:
          estudiante.asignaturas.append(asignatura)

    # Máxima carga semanal
    for maestro in self.maestros:
      carga_auto = 3 if len(maestro.clases) <= 6 else 4
      maestro.max_carga_semanal = _max_carga_semanal_maestro(maestro.nombre, carga_auto)
      maestro.respeta_max_carga_semanal = _as_bool((profesores_restricciones.get(maestro.nombre.lower()) or {}).get('respeta_max_carga_semanal'), True)

    # Si algún maestro quedó sin disponibilidad, asumimos total
    for maestro in self.maestros:
      if not maestro.disponibilidad:
        maestro.disponibilidad = list(self.bloques)

  #Setters
  def set_asignaturas(self, asignaturas):
    self.asignaturas = asignaturas

  def set_estudiantes(self, estudiantes):
    self.estudiantes = estudiantes

  def set_cursos(self, cursos):
    self.cursos = cursos

  def set_maestros(self, maestros):
    self.maestros = maestros

  def set_bloques(self, bloques):
    self.bloques = bloques

  def set_preasignaciones(self, preasignaciones):
    self.preasignaciones = preasignaciones

  # --------------------------------------------------------------------
  # EXPORTACIÓN JSON (UCTP)
  # --------------------------------------------------------------------
  def to_json_dict(self,
                   modelo: 'Modelo',
                   institucion: str = "PUCV - Escuela de Ingeniería en Informática",
                   semestre: str = "2025-1") -> Dict:
    """Serializa el dominio + solución (X,Y) al esquema definido en ESTRUCTURA_JSON_UCTP.md."""

    dias = ["Lu", "Ma", "Mi", "Ju", "Vi"]
    bloques = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14"]

    tipo_map = {
      TipoClase.CATEDRA: "Cát",
      TipoClase.AYUDANTIA: "Ay.",
      TipoClase.LABORATORIO: "Lab",
      TipoClase.TALLER: "Tal",
    }

    # Mapa rápido: (a,p,s) -> b (bloque asignado en el horario final)
    clase_a_bloque: Dict[Tuple[int, int, int], int] = {}
    for (idx_a, idx_p, idx_s, idx_b), val in modelo.X.items():
      if val == 1 and (idx_a, idx_p, idx_s) not in clase_a_bloque:
        clase_a_bloque[(idx_a, idx_p, idx_s)] = idx_b

    # Eventos (asignaturas/paralelos/clases)
    asignaturas_json: List[Dict] = []
    for idx_a, asignatura in enumerate(self.asignaturas):
      paralelos_json: List[Dict] = []
      for idx_p, paralelo in enumerate(asignatura.paralelos):
        clases_json: List[Dict] = []
        for idx_s, sesion in enumerate(paralelo.sesiones):
          clase_dict: Dict = {
            "tipo": tipo_map.get(sesion.tipo_clase, str(sesion.tipo_clase)),
          }

          # Horario (exportamos el horario generado como horario_predefinido)
          idx_b = clase_a_bloque.get((idx_a, idx_p, idx_s))
          if idx_b is not None:
            dia = dias[idx_b // modelo.Bd] if (idx_b // modelo.Bd) < len(dias) else None
            bloque = bloques[idx_b % modelo.Bd] if (idx_b % modelo.Bd) < len(bloques) else None
            if dia is not None and bloque is not None:
              clase_dict["horario_predefinido"] = {"dia": dia, "bloque": bloque}

          # Exportamos maestros por clase para evitar ambigüedad cuando hay más de uno.
          if sesion.tipo_clase == TipoClase.AYUDANTIA:
            clase_dict["maestros"] = None
          else:
            idxs_m = sorted(list(getattr(modelo, 'mapa_clase_maestros', {}).get((idx_a, idx_p, idx_s), set())))
            clase_dict["maestros"] = [
              str(self.maestros[idx_m].nombre)
              for idx_m in idxs_m
              if 0 <= idx_m < len(self.maestros)
            ]

          clases_json.append(clase_dict)

        paralelos_json.append({
          "codigo": str(paralelo.id_paralelo),
          "maestros": list(getattr(paralelo, "maestros", [])),
          "restriccion_teoricas": str(getattr(paralelo, "restriccion_teoricas", "none") or "none"),
          "clases": clases_json,
        })

      asignaturas_json.append({
        "codigo": str(asignatura.id_asignatura),
        "nombre": str(asignatura.asignatura),
        "curso": {
          "carrera": "" if asignatura.curso_carrera is None else str(asignatura.curso_carrera),
          "semestre": "" if asignatura.curso_semestre is None else str(asignatura.curso_semestre),
        },
        "paralelos": paralelos_json,
      })

    # Recursos: maestros (con disponibilidad)
    bloque_id_to_idx = {b.id_bloque: idx_b for idx_b, b in enumerate(self.bloques)}
    maestros_json: List[Dict] = []
    for maestro in self.maestros:
      disponible_por_bloque = [0] * (len(dias) * len(bloques))
      for b in maestro.disponibilidad:
        idx_b = bloque_id_to_idx.get(b.id_bloque)
        if idx_b is not None and 0 <= idx_b < len(disponible_por_bloque):
          disponible_por_bloque[idx_b] = 1

      disponibilidad = []
      for idx_d, dia in enumerate(dias):
        start = idx_d * len(bloques)
        end = start + len(bloques)
        disponibilidad.append({dia: disponible_por_bloque[start:end]})

      maestros_json.append({
        "nombre": str(maestro.nombre),
        "disponibilidad": disponibilidad,
      })

    profesores_json: List[Dict] = []
    for maestro in self.maestros:
      carga_semanal_default = 3 if len(maestro.clases) <= 6 else 4
      carga_diaria_default = max(1, int(self.MAX_CARGA_DIARIA) // 2)
      carga_diaria_export = int(getattr(maestro, 'max_carga_diaria', carga_diaria_default))
      if bool(getattr(maestro, 'respeta_max_carga_diaria', True)) and carga_diaria_export == int(self.MAX_CARGA_DIARIA):
        carga_diaria_export = carga_diaria_default
      if getattr(maestro, 'respeta_max_carga_semanal', True) and int(maestro.max_carga_semanal) == carga_semanal_default:
        max_carga_semanal = "default"
      else:
        max_carga_semanal = int(maestro.max_carga_semanal)

      profesores_json.append({
        "nombre": str(maestro.nombre),
        "respeta_max_carga_diaria": bool(getattr(maestro, 'respeta_max_carga_diaria', True)),
        "max_carga_diaria": carga_diaria_export,
        "respeta_max_carga_semanal": bool(getattr(maestro, 'respeta_max_carga_semanal', True)),
        "max_carga_semanal": max_carga_semanal,
      })

    # Recursos: estudiantes (exportamos asignación final por paralelo desde Y)
    asignaciones_por_estudiante: Dict[int, List[Tuple[int, int]]] = {}
    for (idx_e, idx_a, idx_p), val in modelo.Y.items():
      if val == 1:
        asignaciones_por_estudiante.setdefault(idx_e, []).append((idx_a, idx_p))

    estudiantes_json: List[Dict] = []
    for idx_e, estudiante in enumerate(self.estudiantes):
      asignaturas_est = []
      for (idx_a, idx_p) in sorted(asignaciones_por_estudiante.get(idx_e, [])):
        try:
          cod_a = self.asignaturas[idx_a].id_asignatura
          cod_p = self.asignaturas[idx_a].paralelos[idx_p].id_paralelo
        except Exception:
          continue
        asignaturas_est.append({"codigo": str(cod_a), "paralelo": str(cod_p)})
      estudiantes_json.append({
        "id": _normalizar_id_estudiante(estudiante.id_estudiante),
        "asignaturas": asignaturas_est,
      })

    def _exportar_restricciones_teoricas(conjunto: Set[Tuple[int, int, int]]) -> List[Dict[str, str]]:
      resultado: List[Dict[str, str]] = []
      vistos: Set[Tuple[str, str]] = set()
      for idx_a, idx_p, _ in sorted(conjunto):
        try:
          codigo_asignatura = str(self.asignaturas[idx_a].id_asignatura)
          paralelo = str(self.asignaturas[idx_a].paralelos[idx_p].id_paralelo)
        except Exception:
          continue
        clave = (codigo_asignatura, paralelo)
        if clave in vistos:
          continue
        vistos.add(clave)
        resultado.append({
          "codigo_asignatura": codigo_asignatura,
          "paralelo": paralelo,
        })
      return resultado

    return {
      "metadatos": {
        "institucion": institucion,
        "semestre": semestre,
      },
      "restricciones": {
        "MAX_CARGA_DIARIA": int(self.MAX_CARGA_DIARIA),
        "MAX_CARGA_BLOQUE": int(self.MAX_CARGA_BLOQUE),
        "CLASES_TEORICAS_DIAS_DISTINTOS": _exportar_restricciones_teoricas(getattr(self, 'restricciones_clases_teoricas_dias_distintos', set())),
        "CLASES_TEORICAS_SEPARADAS_1_DIA": _exportar_restricciones_teoricas(getattr(self, 'restricciones_clases_teoricas_separadas_1_dia', set())),
        "PROFESORES": profesores_json,
      },
      "tiempos": {
        "dias": dias,
        "bloques": bloques,
      },
      "eventos": {
        "tipo_clases": list(tipo_map.values()),
        "asignaturas": asignaturas_json,
      },
      "recursos": {
        "maestros": maestros_json,
        "estudiantes": estudiantes_json,
      },
    }

  def exportar_json(self,
                    modelo: 'Modelo',
                    ruta_json: str,
                    institucion: str = "PUCV - Escuela de Ingeniería en Informática",
                    semestre: str = "2025-1") -> None:
    """Escribe a disco la exportación JSON (UTF-8, pretty)."""
    data = self.to_json_dict(modelo=modelo, institucion=institucion, semestre=semestre)
    Path(ruta_json).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_json, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

# Nota (optimización): evitamos construir el dominio al importar el módulo.
# Se construye dentro de main().

# ----------------------------------------------------------------------
