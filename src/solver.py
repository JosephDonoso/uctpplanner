# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import random as rd
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np

from src.dominio import Dia, Dominio, TipoClase
from src.uctp_utils import _registrar_warning_log, registrar_warning_log


resultados = []
mejores_resultados = []
# ----------------------------------------------------------------------
class Modelo:
  """
  Representación del modelo de datos.

  Atrs:
    dominio: Dominio del problema.
    X[(a,p,s,b)]: Diccionario de asignaciones horarias (X).
    Y[(e,a,p)]: Diccionario de asignaciones de estudiantes (Y).
    A: Número de asignaturas.
    P[a]: Número de paralelos por asignatura.
    S[(a,p)]: Número de sesiones por paralelo.
    S_T[(a,p,s)]: Diccionario de sesiones teóricas por paralelo.
    M: Número de maestros.
    DISP[(m,b)]: Diccionario de disponibilidad de maestros.
    I[(m,a,p,s)]: Diccionario de asignaciones de maestros.
    E: Número de estudiantes.
    CE[(e,a)]: Diccionario de asignaciones de estudiantes.
    Q: Número de cursos.
    CQ[(q,a)]: Diccionario de asignaciones de cursos.
    B: Número de bloques.
    Bd: Número de bloques diarios.
    D: Número de días.
    PRE[(a,p,s,b)]: Diccionario de preasignaciones.
    MAX_CARGA_S[m]: Diccionario de carga máxima semanal de maestros.
    MAX_CARGA_D: Número de carga máxima diaria para todos los profesores.
    MAX_CARGA_B: Número de carga máxima de clases por bloque.

    ID[(m,d)]:  Diccionario de si un maestro imparte clase
                en un día específico (Variable auxiliar).
  """

  X = {}
  Y = {}

  def __init__(self, dominio: Dominio):
    """
    Inicializa el modelo de datos a partir del dominio cargado.
    Permite construir las estructuras A, P, S, M, I, E, CE, Q, CQ, B y PRE
    de acuerdo con los objetos definidos en el dominio.
    """
    # -----------------------------------------------------------
    # CONJUNTOS Y VARIABLES DEL DOMINIO
    # -----------------------------------------------------------
    self.dominio = dominio

    # -----------------------------------------------------------
    # Conjunto de asignaturas (A)
    # -----------------------------------------------------------
    self.A = len(dominio.asignaturas)

    # -----------------------------------------------------------
    # Conjunto de paralelos por asignatura (P[a])
    # -----------------------------------------------------------
    self.P = {}
    for idx_a in range(self.A):
      self.P[idx_a] = len(dominio.asignaturas[idx_a].paralelos)

    # -----------------------------------------------------------
    # Conjunto de sesiones por paralelo (S[a,p]),
    # sesiones teóricas S_T[(a,p,s)] = 1 y
    # sesiones prácticas S_T[(a,p,s)] = 0
    # -----------------------------------------------------------
    self.S = {}
    self.S_T = {}
    for idx_a in range(self.A):
      for idx_p in range(self.P[idx_a]):
        sesiones = dominio.asignaturas[idx_a].paralelos[idx_p].sesiones
        self.S[(idx_a, idx_p)] = len(sesiones)
        for idx_s in range(self.S[(idx_a, idx_p)]):
          if sesiones[idx_s].tipo_clase == TipoClase.CATEDRA:
            self.S_T[(idx_a, idx_p, idx_s)] = 1
          else:
            self.S_T[(idx_a, idx_p, idx_s)] = 0

    # -----------------------------------------------------------
    # Conjunto de maestros (M)
    # -----------------------------------------------------------
    self.M = len(dominio.maestros)

    # -----------------------------------------------------------
    # Disponibilidad de maestros DISP[(m,b)]
    # 1 si el maestro m está disponible en el bloque b
    # -----------------------------------------------------------
    self.DISP = {}
    for idx_m, maestro in enumerate(dominio.maestros):
      for idx_b, bloque in enumerate(dominio.bloques):
        self.DISP[(idx_m, idx_b)] = 1 if bloque in maestro.disponibilidad else 0

    # -----------------------------------------------------------
    # Asignación de clases a maestros I[(m,a,p,s)]
    # 1 si el maestro m dicta clase (a,p,s)
    # -----------------------------------------------------------
    # I es *sparse*: sólo guardamos los 1, el resto se asume 0 vía .get()
    self.I = {}
    sesion_to_index = {}
    for idx_a, asignatura in enumerate(dominio.asignaturas):
      for idx_p, paralelo in enumerate(asignatura.paralelos):
        for idx_s, sesion in enumerate(paralelo.sesiones):
          sesion_to_index[id(sesion)] = (idx_a, idx_p, idx_s)

    for idx_m, maestro in enumerate(dominio.maestros):
      for sesion in maestro.clases:
        key = sesion_to_index.get(id(sesion))
        if key is not None:
          idx_a, idx_p, idx_s = key
          self.I[(idx_m, idx_a, idx_p, idx_s)] = 1

    # -----------------------------------------------------------
    # Conjunto de estudiantes (E)
    # -----------------------------------------------------------
    self.E = len(dominio.estudiantes)

    # -----------------------------------------------------------
    # Asignaturas asignadas a cada estudiante CE[(e,a)] = 1
    # si el estudiante e tiene a la asignatura a
    # -----------------------------------------------------------
    # CE sparse: guardamos sólo 1
    self.CE = {}
    asignatura_obj_to_idx = {id(a): idx_a for idx_a, a in enumerate(dominio.asignaturas)}
    for idx_e, estudiante in enumerate(dominio.estudiantes):
      for asignatura in estudiante.asignaturas:
        idx_a = asignatura_obj_to_idx.get(id(asignatura))
        if idx_a is not None:
          self.CE[(idx_e, idx_a)] = 1

    # -----------------------------------------------------------
    # Conjunto de cursos de estudiantes (Q)
    # -----------------------------------------------------------
    self.Q = len(dominio.cursos)

    # -----------------------------------------------------------
    # Asignaturas asignadas a cada curso CQ[(q,a)] = 1
    # si el curso q tiene a la asignatura a
    # -----------------------------------------------------------
    # CQ sparse: guardamos sólo 1
    self.CQ = {}
    for idx_q, curso in enumerate(dominio.cursos):
      for asignatura in curso.asignaturas:
        idx_a = asignatura_obj_to_idx.get(id(asignatura))
        if idx_a is not None:
          self.CQ[(idx_q, idx_a)] = 1

    # -----------------------------------------------------------
    # Bloques horarios (B)
    # -----------------------------------------------------------
    self.B = len(dominio.bloques)
    self.Bd = Dominio.BLOQUES_DIARIOS
    self.D = len(Dia)

    # -----------------------------------------------------------
    # Preasignaciones PRE[(a,p,s,b)] = 1
    # si la clase (a,p,s) está preasignada al bloque b
    # -----------------------------------------------------------
    # PRE sparse: guardamos sólo 1
    self.PRE = {}
    if dominio.preasignaciones:
      bloque_obj_to_idx = {id(b): idx_b for idx_b, b in enumerate(dominio.bloques)}
      for pre in dominio.preasignaciones:
        ses = pre.sesion
        blk = pre.bloque
        ses_idx = sesion_to_index.get(id(ses))
        blk_idx = bloque_obj_to_idx.get(id(blk))
        if ses_idx is not None and blk_idx is not None:
          idx_a, idx_p, idx_s = ses_idx
          self.PRE[(idx_a, idx_p, idx_s, blk_idx)] = 1

    # -----------------------------------------------------------
    # Restricciones teóricas por paralelo
    # -----------------------------------------------------------
    self.CLASES_TEORICAS_DIAS_DISTINTOS = set(getattr(dominio, 'restricciones_clases_teoricas_dias_distintos', set()))
    self.CLASES_TEORICAS_SEPARADAS_1_DIA = set(getattr(dominio, 'restricciones_clases_teoricas_separadas_1_dia', set()))
    self.CLASES_TEORICAS_DIAS_DISTINTOS_POR_PARALELO: Dict[Tuple[int, int], Set[int]] = {}
    self.CLASES_TEORICAS_SEPARADAS_1_DIA_POR_PARALELO: Dict[Tuple[int, int], Set[int]] = {}
    for idx_a, idx_p, idx_s in self.CLASES_TEORICAS_DIAS_DISTINTOS:
      self.CLASES_TEORICAS_DIAS_DISTINTOS_POR_PARALELO.setdefault((idx_a, idx_p), set()).add(idx_s)
    for idx_a, idx_p, idx_s in self.CLASES_TEORICAS_SEPARADAS_1_DIA:
      self.CLASES_TEORICAS_SEPARADAS_1_DIA_POR_PARALELO.setdefault((idx_a, idx_p), set()).add(idx_s)

    # -----------------------------------------------------------
    # Máxima carga semanal para un profesor MAX_CARGA_S[m]
    # -----------------------------------------------------------
    self.MAX_CARGA_S = {}
    for idx_m, maestro in enumerate(dominio.maestros):
      self.MAX_CARGA_S[idx_m] = maestro.max_carga_semanal

    # -----------------------------------------------------------
    # Máxima carga diaria por profesor MAX_CARGA_D[m]
    # -----------------------------------------------------------
    self.MAX_CARGA_D = {}
    for idx_m, maestro in enumerate(dominio.maestros):
      max_diaria = getattr(maestro, 'max_carga_diaria', dominio.MAX_CARGA_DIARIA)
      if not isinstance(max_diaria, int) or max_diaria <= 0:
        max_diaria = dominio.MAX_CARGA_DIARIA
      self.MAX_CARGA_D[idx_m] = max_diaria

    # -----------------------------------------------------------
    # Máxima carga de clases para un mismo bloque MAX_CARGA_B
    # -----------------------------------------------------------
    self.MAX_CARGA_B = dominio.MAX_CARGA_BLOQUE

    # -----------------------------------------------------------
    # HC_8: Bloques protegidos (no se puede asignar ninguna clase)
    # Regla activa: Jueves 7-8
    # -----------------------------------------------------------
    self.BLOQUES_PROTEGIDOS = set()
    for idx_b, bloque in enumerate(dominio.bloques):
      cod = str(getattr(bloque, 'id_bloque', '')).strip().lower().replace(' ', '')
      if cod.startswith('ju') and '7-8' in cod:
        self.BLOQUES_PROTEGIDOS.add(idx_b)

    # -----------------------------------------------------------
    # OPTIMIZACIÓN: Mapeo Inverso Clase -> Maestros
    # -----------------------------------------------------------
    self.mapa_clase_maestros = {}
    for idx_m in range(self.M):
      for idx_a in range(self.A):
        for idx_p in range(self.P[idx_a]):
          for idx_s in range(self.S[(idx_a, idx_p)]):
             # Si la matriz I dice que el maestro da la clase, lo agregamos
             if self.I.get((idx_m, idx_a, idx_p, idx_s), 0) == 1:
                self.mapa_clase_maestros.setdefault((idx_a, idx_p, idx_s), set()).add(idx_m)

    # Backward compatibility: primer maestro de la clase (no usar para validar restricciones).
    self.mapa_clase_maestro = {
      key: min(valores)
      for key, valores in self.mapa_clase_maestros.items()
      if valores
    }

    # -----------------------------------------------------------
    # Reseteo de variables
    # -----------------------------------------------------------
    self.reset_X()
    self.reset_Y()



  # -----------------------------------------------------------
  # RESETEO DE VARIABLES DEL MODELO
  # -----------------------------------------------------------

  def reset_X(self):
    # X sparse: sólo guardamos asignaciones con valor 1
    self.X = {}
    for key, valor in self.PRE.items():
      if valor == 1:
        self.X[key] = 1

  def reset_Y(self):
    # Y sparse: sólo guardamos asignaciones con valor 1
    self.Y = {}

  def _maestros_de_clase(self, idx_a: int, idx_p: int, idx_s: int) -> Set[int]:
    """Retorna todos los maestros asignados a una clase (a,p,s)."""
    return self.mapa_clase_maestros.get((idx_a, idx_p, idx_s), set())

  # -----------------------------------------------------------
  # CÁLCULO DE VARIABLES AUXILIARES
  # -----------------------------------------------------------

  # -----------------------------------------------------------
  # Imparte clases el día ID[(m,d)] = 1
  # si el maestro m imparte al menos una clase en el día d
  # -----------------------------------------------------------
  def calc_ID(self):
    self.ID = {}
    for idx_m in range(self.M):
      for idx_d in range(self.D):
        self.ID[(idx_m, idx_d)] = 0
        for idx_a in range(self.A):
          if self.ID[(idx_m, idx_d)] == 1:
            break
          for idx_p in range(self.P[idx_a]):
            if self.ID[(idx_m, idx_d)] == 1:
              break
            for idx_s in range(self.S[(idx_a, idx_p)]):
              if self.ID[(idx_m, idx_d)] == 1:
                break
              for idx_b in range(idx_d * self.Bd, (idx_d+1) * self.Bd):
                 if (self.I.get((idx_m, idx_a, idx_p, idx_s), 0) == 1 and
                   self.X.get((idx_a, idx_p, idx_s, idx_b), 0) == 1):
                   self.ID[(idx_m, idx_d)] = 1
                   break

  # -----------------------------------------------------------
  # RESTRICCIONES DE FACTIBILIDAD HORARIA
  # -----------------------------------------------------------
  def validar_restricciones_duras(self):
    """
    Verifica HC_1, HC_2, HC_3, HC_4, HC_6, HC_7 y HC_8 en un solo recorrido.
    Retorna True si es factible, False si viola alguna restricción.
    """
    ocupacion_maestro = set()       # Para HC_1
    cargas_diarias = {}             # Para HC_4: {(m, d): cantidad}
    dias_maestro = {}               # Para HC_3: {m: set(dias)}
    conteo_bloques = {}             # Para HC_6: {b: cantidad}
    dias_teoria_distintos = {}      # Para restricciones de días distintos
    dias_teoria_separados = {}      # Para restricciones de separación mínima de 1 día

    # Recorremos X UNA sola vez
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
        if val == 0:
            continue

        # --- HC_8: Bloque protegido ---
        if idx_b in self.BLOQUES_PROTEGIDOS:
          return False

        # --- HC_6: Capacidad del Bloque (Check rápido) ---
        conteo_bloques[idx_b] = conteo_bloques.get(idx_b, 0) + 1
        if conteo_bloques[idx_b] > self.MAX_CARGA_B:
            return False # Excede capacidad del bloque

        idx_d = idx_b // self.Bd

        # --- Nuevas restricciones teóricas por paralelo ---
        clave_clase = (idx_a, idx_p, idx_s)
        if clave_clase in self.CLASES_TEORICAS_DIAS_DISTINTOS:
          clave_paralelo = (idx_a, idx_p)
          dias_usados = dias_teoria_distintos.setdefault(clave_paralelo, set())
          if idx_d in dias_usados:
            return False
          dias_usados.add(idx_d)

        if clave_clase in self.CLASES_TEORICAS_SEPARADAS_1_DIA:
          clave_paralelo = (idx_a, idx_p)
          dias_usados = dias_teoria_separados.setdefault(clave_paralelo, set())
          if idx_d in dias_usados:
            return False
          dias_usados.add(idx_d)

        # Obtenemos todos los maestros de la clase (si aplica).
        maestros = self._maestros_de_clase(idx_a, idx_p, idx_s)

        # Si es una ayudantía u otra clase sin maestro definido en I, saltamos validaciones de maestro
        if not maestros:
            continue

        for idx_m in maestros:
          # --- HC_2: Disponibilidad del Maestro ---
          if self.DISP.get((idx_m, idx_b), 0) == 0:
            return False

          # --- HC_1: Colisión de Horario (Maestro en dos sitios a la vez) ---
          clave_ocupacion = (idx_m, idx_b)
          if clave_ocupacion in ocupacion_maestro:
            return False
          ocupacion_maestro.add(clave_ocupacion)

          # --- HC_4: Carga Diaria Máxima ---
          clave_carga = (idx_m, idx_d)
          cargas_diarias[clave_carga] = cargas_diarias.get(clave_carga, 0) + 1
          if cargas_diarias[clave_carga] > self.MAX_CARGA_D.get(idx_m, self.dominio.MAX_CARGA_DIARIA):
            return False

          # --- Recolección datos para HC_3 (Carga Semanal) ---
          if idx_m not in dias_maestro:
            dias_maestro[idx_m] = set()
          dias_maestro[idx_m].add(idx_d)

    # --- Verificación final de HC_3 (Se hace post-loop) ---
    for idx_m, dias in dias_maestro.items():
        if len(dias) > self.MAX_CARGA_S[idx_m]:
            return False

    # Verificación final de las clases teóricas: días distintos y separación mínima de 1 día.
    for clave_paralelo, dias in dias_teoria_distintos.items():
      if len(dias) != len({dia for dia in dias}):
        return False
    for clave_paralelo, dias in dias_teoria_separados.items():
      dias_ordenados = sorted(dias)
      for idx in range(1, len(dias_ordenados)):
        if dias_ordenados[idx] - dias_ordenados[idx - 1] <= 1:
          return False

    # --- HC_7: Preasignaciones ---
    for key, val in self.PRE.items():
        if val == 1 and self.X.get(key, 0) == 0:
            return False

    return True

  def _hc_1_legacy(self):
    """(Legacy) Restricción dura HC_1.

    Se mantiene sólo como referencia/validación alternativa.
    """
    for idx_m in range(self.M):
      for idx_b in range(self.B):
        sum = 0
        for idx_a in range(self.A):
          for idx_p in range(self.P[idx_a]):
            for idx_s in range(self.S[(idx_a, idx_p)]):
              sum += self.I.get((idx_m, idx_a, idx_p, idx_s), 0) * self.X.get((idx_a, idx_p, idx_s, idx_b), 0)
        if sum > 1:
          return False
    return True

  def hc_1(self):
    ''' 1. Un mismo profesor no puede impartir dos clases al mismo tiempo (Optimizado).'''
    ocupacion = set()
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
        if val == 1:
          for idx_m in self._maestros_de_clase(idx_a, idx_p, idx_s):
            clave_ocupacion = (idx_m, idx_b)
            if clave_ocupacion in ocupacion:
              return False
            ocupacion.add(clave_ocupacion)
    return True

  def _hc_2_legacy(self):
    """(Legacy) Restricción dura HC_2.

    Se mantiene sólo como referencia/validación alternativa.
    """
    for idx_m in range(self.M):
      for idx_b in range(self.B):
        sum = 0
        for idx_a in range(self.A):
          for idx_p in range(self.P[idx_a]):
            for idx_s in range(self.S[(idx_a, idx_p)]):
              sum += self.I.get((idx_m, idx_a, idx_p, idx_s), 0) * self.X.get((idx_a, idx_p, idx_s, idx_b), 0)
        if sum > self.DISP[(idx_m, idx_b)]:
          return False
    return True

  def hc_2(self):
    ''' 2. Un profesor no puede impartir clases en bloques donde no está disponible (Optimizado).'''
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
      if val == 1:
        for idx_m in self._maestros_de_clase(idx_a, idx_p, idx_s):
          if self.DISP.get((idx_m, idx_b), 0) == 0:
            return False
    return True

  def _hc_3_legacy(self):
    """(Legacy) Restricción dura HC_3.

    Se mantiene sólo como referencia/validación alternativa.
    """
    self.calc_ID()
    for idx_m in range(self.M):
      sum = 0
      for idx_d in range(self.D):
        sum += self.ID[(idx_m, idx_d)]
      if sum > self.MAX_CARGA_S[idx_m]:
        return False
    return True
  def hc_3(self):
    ''' 3. Un profesor no puede impartir clases en más días de los permitidos (Optimizado).'''
    dias_maestro = {}
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
      if val == 1:
        for idx_m in self._maestros_de_clase(idx_a, idx_p, idx_s):
          idx_d = idx_b // self.Bd
          if idx_m not in dias_maestro:
            dias_maestro[idx_m] = set()
          dias_maestro[idx_m].add(idx_d)
          if len(dias_maestro[idx_m]) > self.MAX_CARGA_S[idx_m]:
            return False
    return True

  def _hc_4_legacy(self):
    """(Legacy) Restricción dura HC_4.

    Se mantiene sólo como referencia/validación alternativa.
    """
    for idx_m in range(self.M):
      for idx_d in range(self.D):
        sum = 0
        for idx_a in range(self.A):
          for idx_p in range(self.P[idx_a]):
            for idx_s in range(self.S[(idx_a, idx_p)]):
              for idx_b in range(idx_d * self.Bd, (idx_d+1) * self.Bd):
                sum += self.I.get((idx_m, idx_a, idx_p, idx_s), 0) * self.X.get((idx_a, idx_p, idx_s, idx_b), 0)
        if sum > self.MAX_CARGA_D.get(idx_m, self.dominio.MAX_CARGA_DIARIA):
          return False
    return True

  def hc_4(self):
    ''' 4. Un profesor no debe sobrepasar la cantidad máxima de clases por día (Optimizado).'''

    cargas = {}
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
      if val == 1:
        for idx_m in self._maestros_de_clase(idx_a, idx_p, idx_s):
          idx_d = idx_b // self.Bd
          clave = (idx_m, idx_d)
          cargas[clave] = cargas.get(clave, 0) + 1
          if cargas[clave] > self.MAX_CARGA_D.get(idx_m, self.dominio.MAX_CARGA_DIARIA):
            return False
    return True

  def hc_5(self):
    ''' 5. Cada paralelo debe asignar todas las clases semanales de su asignatura.'''
    for idx_a in range(self.A):
      for idx_p in range(self.P[idx_a]):
        for idx_s in range(self.S[(idx_a, idx_p)]):
          sum = 0
          for idx_b in range(self.B):
            sum += self.X.get((idx_a, idx_p, idx_s, idx_b), 0)
          if sum != 1:
            return False, (idx_a, idx_p, idx_s, idx_b)
    return True

  def _hc_6_legacy(self):
    """(Legacy) Restricción dura HC_6.

    Se mantiene sólo como referencia/validación alternativa.
    """
    for idx_b in range(self.B):
      sum = 0
      lista = []
      for idx_a in range(self.A):
        for idx_p in range(self.P[idx_a]):
          for idx_s in range(self.S[(idx_a, idx_p)]):
            sum += self.X.get((idx_a, idx_p, idx_s, idx_b), 0)
            if self.X.get((idx_a, idx_p, idx_s, idx_b), 0) == 1:
              lista.append((self.dominio.asignaturas[idx_a].asignatura, idx_p, idx_s))
      if sum > self.MAX_CARGA_B:
        return False, idx_b, lista
    return True

  def hc_6(self):
    ''' 6. Máxima cantidad de clases por bloque (Optimizada).'''
    conteo_bloques = {}
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
      if val == 1:
        nuevo_total = conteo_bloques.get(idx_b, 0) + 1
        if nuevo_total > self.MAX_CARGA_B:
          return False
        conteo_bloques[idx_b] = nuevo_total
    return True

  def hc_7(self):
    ''' 7. Respetar preasignaciones horarias (PRE sparse).'''
    for key, val in self.PRE.items():
      if val == 1 and self.X.get(key, 0) == 0:
        return False
    return True

  def hc_8(self):
    ''' 8. Bloque protegido: no se pueden asignar clases en Ju 7-8. '''
    for (idx_a, idx_p, idx_s, idx_b), val in self.X.items():
      if val == 1 and idx_b in self.BLOQUES_PROTEGIDOS:
        return False
    return True

  # -----------------------------------------------------------
  # FUNCIÓN OBJETIVO
  # -----------------------------------------------------------
  def calc_fo_new(self, alfa=1, cv_ideal=0.1, ventana_ideal=4):
    # 1. PRE-CÁLCULO LOCAL: Bloques por paralelo
    # Formato: {(id_asignatura, id_paralelo): [id_bloque1, ...]}
    self.bloques_paralelos = {}
    for idx_a in range(self.A):
      for idx_p in range(self.P[idx_a]):
        bloques = []
        for idx_s in range(self.S[(idx_a, idx_p)]):
          for idx_b in range(self.B):
            if self.X.get((idx_a, idx_p, idx_s, idx_b), 0) == 1:
              bloques.append(idx_b)
        self.bloques_paralelos[(idx_a, idx_p)] = bloques

    # Asignaturas que cursa cada estudiante
    # Formato: {id_estudiante: [id_asignatura1, ...]}
    self.asignaturas_estudiantes = {idx_e: [] for idx_e in range(self.E)}
    for (idx_e, idx_a), cursa in self.CE.items():
      if cursa == 1:
        self.asignaturas_estudiantes[idx_e].append(idx_a)

    # Dict para llevar la cuenta rápida de alumnos por paralelo
    # Formato: {(id_asignatura, id_paralelo): cantidad_actual}
    self.ocupacion_actual = {(idx_a, idx_p): 0 for idx_a in range(self.A)
                            for idx_p in range(self.P[idx_a])}
    # Dict para guardar los bloques ocupados por estudiante
    # Formato: {id_estudiante: [id_bloque1, ...]}
    self.bloques_estudiantes = {}
    for idx_e in range(self.E):
      bloques = []
      for idx_a in self.asignaturas_estudiantes[idx_e]:
        for idx_p in range(self.P[idx_a]):
          if self.Y.get((idx_e, idx_a, idx_p), 0) == 1:
            bloques.extend(self.bloques_paralelos[(idx_a, idx_p)])
            self.ocupacion_actual[(idx_a, idx_p)] += 1
      self.bloques_estudiantes[idx_e] = bloques

    suma_desviaciones_reales = 0
    suma_desviaciones_ideales = 0
    total_inscripciones = 0

    for idx_a in range(self.A):
      n_p = self.P[idx_a]
      inscritos = [self.ocupacion_actual[(idx_a, idx_p)] for idx_p in range(n_p)]

      # Solo calculamos para materias con más de 1 paralelo
      if n_p > 1:
        # 1. Datos Reales
        media_a = sum(inscritos) / n_p
        varianza = sum((n - media_a)**2 for n in inscritos) / n_p
        sigma_real = varianza**0.5
        suma_desviaciones_reales += sigma_real

        # 2. Datos Ideales (Basados en el CV por asignatura)
        # La desviación ideal es el X% de la media de esta materia
        sigma_ideal_a = media_a * cv_ideal
        suma_desviaciones_ideales += sigma_ideal_a
      else:
        # Materias con 1 paralelo no aportan al desbalance (desv=0)
        pass

    # Promedios globales de desbalance
    desbalance_real = suma_desviaciones_reales / self.A
    desbalance_ideal = suma_desviaciones_ideales / self.A

    # 3. Ventanas
    ventana_total_real = sum(self.calcular_ventana(self.bloques_estudiantes[e], ventana_ideal) for e in range(self.E))
    estudiantes_con_carga = sum(1 for e in range(self.E) if self.asignaturas_estudiantes[e])
    ventana_total_ideal = estudiantes_con_carga * ventana_ideal

    # Choques
    choques = sum( len(self.bloques_estudiantes[e])-len(set(self.bloques_estudiantes[e])) for e in range(self.E))

    # 4. Función Objetivo Multiplicativa
    ratio_desbalance_crudo = desbalance_real / max(desbalance_ideal, 1e-6)
    ratio_desbalance_fo = ratio_desbalance_crudo**alfa
    ratio_ventana = ventana_total_real / max(ventana_total_ideal, 1e-6)
    return (ratio_desbalance_crudo, ratio_ventana, (ratio_desbalance_fo * ratio_ventana), choques)

  def calcular_ventana(self, bloques_ocupados, ventana_ideal=4):
    """Calcula la ventana para una secuencia de bloques horarios"""
    if not bloques_ocupados: return 0

    # Ordenamos y quitamos duplicados
    bloques_ordenados = sorted(bloques_ocupados)

    # 1. Clasificación por día (0-34 // 7) y posición relativa (0-34 % 7)
    dias = {d: [] for d in range(self.D)}
    for b in bloques_ordenados:
      dias[b // self.Bd].append(b % self.Bd)

    sumatoria_ventanas = 0
    for b_dia in dias.values():
      if len(b_dia) < 2: continue

      # 2. Conteo de ventanas
      for i in range(len(b_dia) - 1):
        ventana = (b_dia[i+1] - b_dia[i] - 1)
        # Penalizar choque
        if ventana < 0:
          ventana = 7
        sumatoria_ventanas += ventana

      # 3. Regla almuerzo: al menos uno en [0,1,2,3] y al menos uno en [4,5,6]
      if b_dia[0] <= 3 and b_dia[-1] >= 4:
        sumatoria_ventanas += 1

    # 4. Penalización cuadrática si supera el umbral configurable (ventana_ideal)
    umbral = max(0, float(ventana_ideal))
    if sumatoria_ventanas > umbral:
      return umbral + (sumatoria_ventanas - umbral)**2

    return sumatoria_ventanas

  # -----------------------------------------------------------
  # SETTERS
  # -----------------------------------------------------------

  # -----------------------------------------------------------
  # Asignación horaria
  # -----------------------------------------------------------
  def set_X(self, X):
    self.X = X

  # -----------------------------------------------------------
  # Asignación de estudiantes
  # -----------------------------------------------------------
  def set_Y(self, Y):
    self.Y = Y

  # -----------------------------------------------------------
  # MÉTODOS UTILITARIOS
  # -----------------------------------------------------------
  def resumen(self):
    """Imprime un resumen del modelo generado."""
    print("=== MODELO DE DATOS ===")
    print(f"Asignaturas (A): {self.A}")
    print(f"Paralelos totales: {sum(self.P.values())}")
    print(f"Sesiones totales: {sum(self.S.values())}")
    print(f"Maestros (M): {self.M}")
    print(f"Estudiantes (E): {self.E}")
    print(f"Cursos (Q): {self.Q}")
    print(f"Preasignaciones (PRE): {sum(self.PRE.values())}")
    print(f"Bloques totales (B): {self.B}")
    print(f"Bloques diarios (Bd): {self.Bd}")
    print(f"Días (D): {self.D}")
    print()
    print("Paralelos por asignatura (P):", self.P)
    print("Sesiones por paralelo (S):", self.S)
    print(f"Total de relaciones maestro-clase: {sum(self.I.values())}")
    print(f"Total de relaciones estudiante-asignatura: {sum(self.CE.values())}")
    print(f"Total de relaciones curso-asignatura: {sum(self.CQ.values())}")


# ----------------------------------------------------------------------
# INICIALIZACIÓN GREEDY
# ----------------------------------------------------------------------
class Greedy:

  """Construye una solución inicial factible para X (horario).

  Estrategia:
  - Respetar preasignaciones (`modelo.PRE`).
  - Agrupar cursos con alta compatibilidad inter-curso (alumnos compartidos).
  - Dentro de cada grupo, ordenar asignaturas y asignar sesiones (a,p,s) a
    bloques b validando restricciones duras (HC_1..HC_4, HC_6, HC_7).
  - Programar también asignaturas “huérfanas” (no presentes en CQ).

  API pública:
  - `solve()` genera (o re-genera) `modelo.X`.

  Notas:
  - Los métodos auxiliares se consideran internos y usan prefijo `_`.
  - Se mantiene el “reintento” por timeout de 10s durante la asignación.
  """

  def __init__(
    self,
    modelo: 'Modelo',
    umbral_varianza_aceptable=0.05,
    umbral_compatibilidad_intercurso=0.25,
    asignacion_inteligente=True,
    max_reintentos=100,
    salida_warnings='data/output/warnings_logs.txt'
  ) -> None:
    self.modelo = modelo
    self.umbral_varianza_aceptable = umbral_varianza_aceptable
    self.umbral_compatibilidad_intercurso = umbral_compatibilidad_intercurso
    self.asignacion_inteligente = asignacion_inteligente
    self.max_reintentos = max(1, int(max_reintentos))
    self._reintentos_actuales = 0
    self.salida_warnings = salida_warnings

    self.asignaturas_asignadas: Dict[int, bool] = {}
    self.asignaturas_por_curso: Dict[int, List[int]] = self._construir_asignaturas_por_curso()
    self.clases_por_asignatura: Dict[int, List[Tuple[int, int]]] = self._construir_clases_por_asignatura()
    self.clases_teoricas_dias_distintos_por_paralelo = getattr(
      self.modelo,
      'CLASES_TEORICAS_DIAS_DISTINTOS_POR_PARALELO',
      {},
    )
    self.clases_teoricas_separadas_1_dia_por_paralelo = getattr(
      self.modelo,
      'CLASES_TEORICAS_SEPARADAS_1_DIA_POR_PARALELO',
      {},
    )
    self.dias_teoricas_dias_distintos_usados: Dict[Tuple[int, int], Set[int]] = {}
    self.dias_teoricas_separados_usados: Dict[Tuple[int, int], Set[int]] = {}

    # Matriz alumnos_compartidos_entre_cursos[i][j] (conteo de estudiantes que
    # toman al menos una asignatura del curso i y al menos una del curso j).
    self.alumnos_compartidos_entre_cursos: List[List[int]] = self._construir_matriz_alumnos_compartidos_entre_cursos()

    # Atributos de apoyo (se recalculan/ordenan en `solve()`)
    self.grupos_cursos_compatibles: List[List[int]] = []
    self.cantidad_clases_por_curso: Dict[int, int] = {}

  def solve(self, reset_reintentos: bool = True) -> None:
    """Genera un horario inicial factible en `self.modelo.X`.

    Efectos:
    - Resetea y modifica `modelo.X` in-place.
    - Marca asignaturas asignadas en `self.asignaturas_asignadas`.
    """
    if reset_reintentos:
      self._reintentos_actuales = 0

    self.modelo.reset_X()
    self.asignaturas_asignadas = {}
    self._cargar_preasignaciones_en_X()
    self._cargar_restricciones_teoricas_desde_X()

    self.grupos_cursos_compatibles = self._construir_grupos_cursos_compatibles()
    self.cantidad_clases_por_curso = self._contar_clases_por_curso()
    self._ordenar_grupos_por_prioridad()

    for cursos in self.grupos_cursos_compatibles:
      asignaturas_a_asignar = self._asignaturas_del_grupo(cursos)
      matriz_compatibilidad, asignaturas_ordenadas = self._generar_compatibilidades(asignaturas_a_asignar)
      self._asignar_horarios_compatibles(matriz_compatibilidad, asignaturas_ordenadas)

    # Programar asignaturas que no pertenecen a ningún curso (CQ)
    restantes = [idx_a for idx_a in range(self.modelo.A) if idx_a not in self.asignaturas_asignadas]
    if restantes:
      matriz_compatibilidad, asignaturas_ordenadas = self._generar_compatibilidades(restantes)
      self._asignar_horarios_compatibles(matriz_compatibilidad, asignaturas_ordenadas)

  # --------------------------------------------------------------------
  # Construcción de insumos
  # --------------------------------------------------------------------
  def _construir_asignaturas_por_curso(self) -> Dict[int, List[int]]:
    asignaturas_por_curso: Dict[int, List[int]] = {}
    for idx_q in range(self.modelo.Q):
      asignaturas_por_curso[idx_q] = [
        idx_a
        for idx_a in range(self.modelo.A)
        if self.modelo.CQ.get((idx_q, idx_a), 0) == 1
      ]
    return asignaturas_por_curso

  def _construir_clases_por_asignatura(self) -> Dict[int, List[Tuple[int, int]]]:
    clases_por_asignatura: Dict[int, List[Tuple[int, int]]] = {}
    for idx_a in range(self.modelo.A):
      clases: List[Tuple[int, int]] = []
      for idx_p in range(self.modelo.P[idx_a]):
        for idx_s in range(self.modelo.S[(idx_a, idx_p)]):
          clases.append((idx_p, idx_s))
      clases_por_asignatura[idx_a] = clases
    return clases_por_asignatura

  def _construir_matriz_alumnos_compartidos_entre_cursos(self) -> List[List[int]]:
    compartidos = [[0 for _ in range(self.modelo.Q)] for _ in range(self.modelo.Q)]

    # student_in_course[e][q] = True si el estudiante e toma al menos una
    # asignatura perteneciente al curso q.
    student_in_course = [[False for _ in range(self.modelo.Q)] for _ in range(self.modelo.E)]
    for idx_e in range(self.modelo.E):
      for idx_q in range(self.modelo.Q):
        for idx_a in self.asignaturas_por_curso[idx_q]:
          if self.modelo.CE.get((idx_e, idx_a), 0) == 1:
            student_in_course[idx_e][idx_q] = True
            break

    # Conteo por pares ordenados (i,j), igual a la implementación original.
    for idx_e in range(self.modelo.E):
      cursos_del_estudiante = [idx_q for idx_q in range(self.modelo.Q) if student_in_course[idx_e][idx_q]]
      for idx_q_i in cursos_del_estudiante:
        for idx_q_j in cursos_del_estudiante:
          compartidos[idx_q_i][idx_q_j] += 1

    return compartidos

  def _cargar_preasignaciones_en_X(self) -> None:
    """Carga `modelo.PRE` en X y marca asignaturas como asignadas.

    Se mantiene el mismo criterio previo: si una asignatura tiene alguna
    preasignación, se marca completa como “asignada” para no re-programarla.
    """
    for (idx_a, idx_p, idx_s, idx_b), valor in self.modelo.PRE.items():
      if valor == 1:
        self.modelo.X[(idx_a, idx_p, idx_s, idx_b)] = 1
        self.asignaturas_asignadas[idx_a] = True

  def _cargar_restricciones_teoricas_desde_X(self) -> None:
    self.dias_teoricas_dias_distintos_usados = {}
    self.dias_teoricas_separados_usados = {}
    for (idx_a, idx_p, idx_s, idx_b), val in self.modelo.X.items():
      if val != 1:
        continue
      idx_d = idx_b // self.modelo.Bd
      clave_paralelo = (idx_a, idx_p)
      if (idx_a, idx_p, idx_s) in self.modelo.CLASES_TEORICAS_DIAS_DISTINTOS:
        self.dias_teoricas_dias_distintos_usados.setdefault(clave_paralelo, set()).add(idx_d)
      if (idx_a, idx_p, idx_s) in self.modelo.CLASES_TEORICAS_SEPARADAS_1_DIA:
        self.dias_teoricas_separados_usados.setdefault(clave_paralelo, set()).add(idx_d)

  # --------------------------------------------------------------------
  # Agrupación y prioridades de cursos
  # --------------------------------------------------------------------
  def _construir_grupos_cursos_compatibles(self) -> List[List[int]]:
    """Agrupa cursos a programar juntos según ratio de alumnos compartidos."""
    lista_compatibilidad: List[Tuple[int, int, float]] = []
    for idx_q_i in range(len(self.alumnos_compartidos_entre_cursos)):
      diagonal = self.alumnos_compartidos_entre_cursos[idx_q_i][idx_q_i]
      if diagonal > 0:
        for idx_q_j in range(idx_q_i + 1, len(self.alumnos_compartidos_entre_cursos)):
          ratio = self.alumnos_compartidos_entre_cursos[idx_q_i][idx_q_j] / diagonal
          lista_compatibilidad.append((idx_q_i, idx_q_j, ratio))
      else:
        lista_compatibilidad.append((idx_q_i, idx_q_i, 0))

    lista_compatibilidad.sort(key=lambda x: x[2], reverse=True)

    cursos_vistos: Dict[int, bool] = {}
    grupos: List[List[int]] = []
    for curso_1, curso_2, ratio_compartidos in lista_compatibilidad:
      if curso_1 in cursos_vistos:
        continue
      cursos_vistos[curso_1] = True
      if ratio_compartidos >= self.umbral_compatibilidad_intercurso:
        grupos.append([curso_1, curso_2])
      else:
        grupos.append([curso_1])
    return grupos

  def _contar_clases_por_curso(self) -> Dict[int, int]:
    cantidad: Dict[int, int] = {}
    for idx_q in range(self.modelo.Q):
      total = 0
      for idx_a in range(self.modelo.A):
        if self.modelo.CQ.get((idx_q, idx_a), 0) == 1:
          for idx_p in range(self.modelo.P[idx_a]):
            total += self.modelo.S[(idx_a, idx_p)]
      cantidad[idx_q] = total
    return cantidad

  def _ordenar_grupos_por_prioridad(self) -> None:
    self.grupos_cursos_compatibles.sort(
      key=lambda x: (
        self.cantidad_clases_por_curso[x[0]] + self.cantidad_clases_por_curso[x[1]]
        if len(x) == 2
        else self.cantidad_clases_por_curso[x[0]]
      ),
      reverse=True,
    )

  def _asignaturas_del_grupo(self, cursos: List[int]) -> List[int]:
    if len(cursos) == 2:
      return self.asignaturas_por_curso[cursos[0]] + self.asignaturas_por_curso[cursos[1]]
    return self.asignaturas_por_curso[cursos[0]]

  # --------------------------------------------------------------------
  # Asignación horaria (misma lógica original)
  # --------------------------------------------------------------------
  def _asignar_horarios_compatibles(self, matriz_compatibilidad, asignaturas_ordenadas) -> None:
    for i, idx_a_i in enumerate(asignaturas_ordenadas):
      if idx_a_i in self.asignaturas_asignadas:
        continue

      self.asignaturas_asignadas[idx_a_i] = True
      asignaturas_restricciones = [asignaturas_ordenadas[j] for j in range(i - 1, -1, -1)]

      for idx_p_i in range(self.modelo.P[idx_a_i]):
        restriccion_no_solapamiento: List[Tuple[int, int, int]] = []
        restriccion_solapamiento: List[Tuple[int, int, int]] = []

        for idx_a_j in asignaturas_restricciones:
          submatriz = matriz_compatibilidad[(idx_a_j, idx_a_i)]
          for idx_p_j in range(self.modelo.P[idx_a_j]):
            # 1|0|-1: No Solapa|Sin Restricción|Si Solapa
            compatible = submatriz[idx_p_j][idx_p_i]
            for idx_s_j in range(self.modelo.S[(idx_a_j, idx_p_j)]):
              if compatible == 1:
                restriccion_no_solapamiento.append((idx_a_j, idx_p_j, idx_s_j))
              elif compatible == -1:
                restriccion_solapamiento.append((idx_a_j, idx_p_j, idx_s_j))

        for idx_s_i in range(self.modelo.S[(idx_a_i, idx_p_i)]):
          bloques_prohibidos = self._buscar_bloques_de_clases(restriccion_no_solapamiento)
          bloques_ideales = self._buscar_bloques_de_clases(restriccion_solapamiento)
          self._asignar_clase_a_bloque_con_reintento(
            idx_a_i,
            idx_p_i,
            idx_s_i,
            bloques_prohibidos,
            bloques_ideales,
          )

  def _buscar_bloques_de_clases(self, clases: List[Tuple[int, int, int]]) -> List[int]:
    bloques: List[int] = []
    for idx_a, idx_p, idx_s in clases:
      for idx_b in range(self.modelo.B):
        if self.modelo.X.get((idx_a, idx_p, idx_s, idx_b), 0) == 1:
          bloques.append(idx_b)
    return bloques

  def _bloque_viola_restriccion_teorica(self, idx_a: int, idx_p: int, idx_s: int, idx_b: int) -> bool:
    idx_d = idx_b // self.modelo.Bd
    clave_paralelo = (idx_a, idx_p)
    clave_clase = (idx_a, idx_p, idx_s)

    if clave_clase in self.modelo.CLASES_TEORICAS_DIAS_DISTINTOS:
      dias_usados = self.dias_teoricas_dias_distintos_usados.get(clave_paralelo, set())
      if idx_d in dias_usados:
        return True

    if clave_clase in self.modelo.CLASES_TEORICAS_SEPARADAS_1_DIA:
      dias_usados = self.dias_teoricas_separados_usados.get(clave_paralelo, set())
      for dia_prev in dias_usados:
        if abs(idx_d - dia_prev) <= 1:
          return True

    return False

  def _registrar_restriccion_teorica(self, idx_a: int, idx_p: int, idx_s: int, idx_b: int) -> None:
    idx_d = idx_b // self.modelo.Bd
    clave_paralelo = (idx_a, idx_p)
    clave_clase = (idx_a, idx_p, idx_s)

    if clave_clase in self.modelo.CLASES_TEORICAS_DIAS_DISTINTOS:
      self.dias_teoricas_dias_distintos_usados.setdefault(clave_paralelo, set()).add(idx_d)
    if clave_clase in self.modelo.CLASES_TEORICAS_SEPARADAS_1_DIA:
      self.dias_teoricas_separados_usados.setdefault(clave_paralelo, set()).add(idx_d)

  def _etiqueta_clase(self, idx_a: int, idx_p: int, idx_s: int) -> str:
    asig = self.modelo.dominio.asignaturas[idx_a]
    paralelo = asig.paralelos[idx_p]
    return f"{asig.id_asignatura}-{paralelo.id_paralelo}-s{idx_s + 1}"

  def _etiqueta_bloque(self, idx_b: int) -> str:
    return str(self.modelo.dominio.bloques[idx_b].id_bloque)

  def _diagnostico_reintento(
    self,
    idx_a: int,
    idx_p: int,
    idx_s: int,
    bloques_prohibidos: List[int],
    restriccion_bloque_prohibido_activa: bool,
    bloques_revisados: List[int],
    contador: int,
  ) -> None:
    maestros_objetivo = sorted(list(self.modelo._maestros_de_clase(idx_a, idx_p, idx_s)))

    clases_en_bloque: Dict[int, List[Tuple[int, int, int]]] = {}
    ocupacion_bloque: Dict[int, int] = {}
    ocupacion_maestro_bloque: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
    dias_por_maestro: Dict[int, Set[int]] = {}
    carga_dia_maestro: Dict[Tuple[int, int], int] = {}

    for (a2, p2, s2, b2), val in self.modelo.X.items():
      if val != 1:
        continue
      clases_en_bloque.setdefault(b2, []).append((a2, p2, s2))
      ocupacion_bloque[b2] = ocupacion_bloque.get(b2, 0) + 1
      d2 = b2 // self.modelo.Bd
      for m2 in self.modelo._maestros_de_clase(a2, p2, s2):
        ocupacion_maestro_bloque.setdefault((m2, b2), []).append((a2, p2, s2))
        dias_por_maestro.setdefault(m2, set()).add(d2)
        key_md = (m2, d2)
        carga_dia_maestro[key_md] = carga_dia_maestro.get(key_md, 0) + 1

    contadores: Dict[str, int] = {
      'RESTR_COMPAT': 0,
      'RESTR_TEO': 0,
      'HC_8': 0,
      'HC_1': 0,
      'HC_2': 0,
      'HC_3': 0,
      'HC_4': 0,
      'HC_6': 0,
    }
    ejemplos: Dict[str, str] = {}

    for idx_b in range(self.modelo.B):
      if idx_b in getattr(self.modelo, 'BLOQUES_PROTEGIDOS', set()):
        contadores['HC_8'] += 1
        if 'HC_8' not in ejemplos:
          ejemplos['HC_8'] = f"bloque protegido {self._etiqueta_bloque(idx_b)}"
        continue

      if restriccion_bloque_prohibido_activa and idx_b in bloques_prohibidos:
        contadores['RESTR_COMPAT'] += 1
        if 'RESTR_COMPAT' not in ejemplos:
          ejemplos['RESTR_COMPAT'] = f"bloque {self._etiqueta_bloque(idx_b)} prohibido por compatibilidad entre eventos"
        continue

      if self._bloque_viola_restriccion_teorica(idx_a, idx_p, idx_s, idx_b):
        contadores['RESTR_TEO'] += 1
        if 'RESTR_TEO' not in ejemplos:
          ejemplos['RESTR_TEO'] = f"bloque {self._etiqueta_bloque(idx_b)} viola restriccion teorica del paralelo"
        continue

      if ocupacion_bloque.get(idx_b, 0) >= self.modelo.MAX_CARGA_B:
        contadores['HC_6'] += 1
        if 'HC_6' not in ejemplos:
          conflictos = [self._etiqueta_clase(a3, p3, s3) for (a3, p3, s3) in clases_en_bloque.get(idx_b, [])[:3]]
          ejemplos['HC_6'] = f"bloque {self._etiqueta_bloque(idx_b)} lleno (clases: {', '.join(conflictos)})"
        continue

      d = idx_b // self.modelo.Bd
      bloque_invalido = False
      for idx_m in maestros_objetivo:
        nombre_m = self.modelo.dominio.maestros[idx_m].nombre

        if ocupacion_maestro_bloque.get((idx_m, idx_b)):
          contadores['HC_1'] += 1
          if 'HC_1' not in ejemplos:
            conflicto = ocupacion_maestro_bloque[(idx_m, idx_b)][0]
            ejemplos['HC_1'] = (
              f"maestro {nombre_m} ya ocupa {self._etiqueta_bloque(idx_b)} "
              f"con {self._etiqueta_clase(conflicto[0], conflicto[1], conflicto[2])}"
            )
          bloque_invalido = True
          break

        if self.modelo.DISP.get((idx_m, idx_b), 0) == 0:
          contadores['HC_2'] += 1
          if 'HC_2' not in ejemplos:
            ejemplos['HC_2'] = f"maestro {nombre_m} no disponible en {self._etiqueta_bloque(idx_b)}"
          bloque_invalido = True
          break

        dias_m = dias_por_maestro.get(idx_m, set())
        if d not in dias_m and len(dias_m) + 1 > self.modelo.MAX_CARGA_S[idx_m]:
          contadores['HC_3'] += 1
          if 'HC_3' not in ejemplos:
            ejemplos['HC_3'] = (
              f"maestro {nombre_m} excede max_carga_semanal={self.modelo.MAX_CARGA_S[idx_m]} "
              f"al usar dia {d + 1}"
            )
          bloque_invalido = True
          break

        carga_dia = carga_dia_maestro.get((idx_m, d), 0)
        max_diaria = self.modelo.MAX_CARGA_D.get(idx_m, self.modelo.dominio.MAX_CARGA_DIARIA)
        if carga_dia + 1 > max_diaria:
          contadores['HC_4'] += 1
          if 'HC_4' not in ejemplos:
            ejemplos['HC_4'] = (
              f"maestro {nombre_m} excede max_carga_diaria={max_diaria} "
              f"en dia {d + 1}"
            )
          bloque_invalido = True
          break

      if bloque_invalido:
        continue

    revisados = sum(bloques_revisados)
    clase = self._etiqueta_clase(idx_a, idx_p, idx_s)
    nombres_maestros = [self.modelo.dominio.maestros[m].nombre for m in maestros_objetivo]
    _registrar_warning_log(
      f"[GREEDY_REINTENTO] Clase {clase} no pudo asignarse. "
      f"Intentos={contador}, bloques_revisados={revisados}/{self.modelo.B}, "
      f"maestros={nombres_maestros}", self.salida_warnings
    )

    claves_orden = ['HC_8', 'RESTR_COMPAT', 'RESTR_TEO', 'HC_1', 'HC_2', 'HC_3', 'HC_4', 'HC_6']
    for k in claves_orden:
      if contadores.get(k, 0) <= 0:
        continue
      msg = ejemplos.get(k, 'sin detalle adicional')
      _registrar_warning_log(f"  - [{k}] bloqueado en {contadores[k]} bloques. Ejemplo: {msg}", self.salida_warnings)

  def _siguiente_bloque_no_revisado(
    self,
    bloques_ideales: List[int],
    contador: int,
    bloques_revisados: List[int],
  ) -> Tuple[Optional[int], int]:
    # Prioriza bloques ideales aún no revisados
    while contador < len(bloques_ideales):
      idx_b = bloques_ideales[contador]
      contador += 1
      if 0 <= idx_b < self.modelo.B and bloques_revisados[idx_b] == 0:
        return idx_b, contador

    # Si no quedan ideales, toma cualquier bloque no revisado
    no_revisados = [i for i, v in enumerate(bloques_revisados) if v == 0]
    if not no_revisados:
      return None, contador
    return rd.choice(no_revisados), contador

  def _asignar_clase_a_bloque_con_reintento(
    self,
    idx_a: int,
    idx_p: int,
    idx_s: int,
    bloques_prohibidos: List[int],
    bloques_ideales: List[int],
  ) -> None:
    restriccion_bloque_prohibido = True
    bloques_revisados = [0 for _ in range(self.modelo.B)]
    contador = 0

    bloque_no_asignado = True
    while bloque_no_asignado:
      idx_b, contador = self._siguiente_bloque_no_revisado(bloques_ideales, contador, bloques_revisados)
      if idx_b is None:
        if restriccion_bloque_prohibido:
          # Segunda pasada: relajar solo restricción de compatibilidad y volver a barrer todos los bloques
          restriccion_bloque_prohibido = False
          bloques_revisados = [0 for _ in range(self.modelo.B)]
          continue

        # Si ya se revisaron todos los bloques con y sin restricción de compatibilidad, reintentar greedy completo
        self._diagnostico_reintento(
          idx_a,
          idx_p,
          idx_s,
          bloques_prohibidos,
          restriccion_bloque_prohibido,
          bloques_revisados,
          contador,
        )
        if self._reintentos_actuales >= self.max_reintentos:
          clase = self._etiqueta_clase(idx_a, idx_p, idx_s)
          _registrar_warning_log(
            f"[GREEDY_REINTENTO] Límite alcanzado ({self.max_reintentos}) al intentar asignar {clase}."
          )
          raise RuntimeError(
            f"[ERROR][GREEDY_REINTENTO] Maximo de reintentos alcanzado "
            f"({self.max_reintentos}) al intentar asignar {clase}."
          )

        self._reintentos_actuales += 1
        if self._reintentos_actuales % 10 == 0 or self._reintentos_actuales == self.max_reintentos:
          print(f"[WARN][GREEDY_REINTENTO] Reintentando greedy.solve() ({self._reintentos_actuales}/{self.max_reintentos}).")
        self.solve(reset_reintentos=False)
        return

      bloques_revisados[idx_b] = 1

      if idx_b in getattr(self.modelo, 'BLOQUES_PROTEGIDOS', set()):
        continue

      if restriccion_bloque_prohibido and idx_b in bloques_prohibidos:
        continue

      if self._bloque_viola_restriccion_teorica(idx_a, idx_p, idx_s, idx_b):
        continue

      self.modelo.X[(idx_a, idx_p, idx_s, idx_b)] = 1
      if (
        self.modelo.hc_1()
        and self.modelo.hc_2()
        and self.modelo.hc_3()
        and self.modelo.hc_4()
        and self.modelo.hc_8()
        and self.modelo.hc_6()
        and self.modelo.hc_7()
      ):
        self._registrar_restriccion_teorica(idx_a, idx_p, idx_s, idx_b)
        bloque_no_asignado = False
      else:
        self.modelo.X.pop((idx_a, idx_p, idx_s, idx_b), None)

  # --------------------------------------------------------------------
  # Generación de compatibilidades entre asignaturas
  # --------------------------------------------------------------------
  def _generar_compatibilidades(self, lista_asignaturas: List[int]):
    asignaturas_ordenadas = lista_asignaturas.copy()
    asignaturas_ordenadas.sort(key=lambda x: self.modelo.P[x], reverse=True)

    matriz_compatibilidad: Dict[Tuple[int, int], List[List[int]]] = {}
    for i in range(len(asignaturas_ordenadas)):
      for j in range(i + 1, len(asignaturas_ordenadas)):
        idx_a_i = asignaturas_ordenadas[i]
        idx_a_j = asignaturas_ordenadas[j]
        paralelos_i = self.modelo.P[idx_a_i]
        paralelos_j = self.modelo.P[idx_a_j]

        if self.asignacion_inteligente:
          alumnos_i, alumnos_j, alumnos_compartidos = self._contar_estudiantes_asignaturas(idx_a_i, idx_a_j)
          submatriz = self._generar_matriz_compatibilidad(
            paralelos_i,
            alumnos_i,
            paralelos_j,
            alumnos_j,
            alumnos_compartidos,
          )
        else:
          submatriz = [[0 for _ in range(paralelos_j)] for _ in range(paralelos_i)]

        matriz_compatibilidad[(idx_a_i, idx_a_j)] = submatriz

    return matriz_compatibilidad, asignaturas_ordenadas

  def _contar_estudiantes_asignaturas(self, idx_a_i: int, idx_a_j: int) -> Tuple[int, int, int]:
    alumnos_i = 0
    alumnos_j = 0
    alumnos_compartidos = 0
    for idx_e in range(self.modelo.E):
      toma_i = self.modelo.CE.get((idx_e, idx_a_i), 0) == 1
      toma_j = self.modelo.CE.get((idx_e, idx_a_j), 0) == 1
      if toma_i and toma_j:
        alumnos_compartidos += 1
      if toma_i:
        alumnos_i += 1
      if toma_j:
        alumnos_j += 1
    return alumnos_i, alumnos_j, alumnos_compartidos

  # --------------------------------------------------------------------
  # Heurística de matriz de compatibilidad (balanceo de carga)
  # --------------------------------------------------------------------
  def _calculo_varianza_normalizada(self, lista: List[float]) -> float:
    lista_np = np.array(lista)
    varianza = np.var(lista_np)
    total = np.sum(lista_np)
    if len(lista_np) - 1 != 0:
      varianza_max = ((total / len(lista_np)) ** 2) * (len(lista_np) - 1)
    else:
      varianza_max = 0

    if varianza_max == 0:
      return 0
    return float(varianza / varianza_max)

  def _simulacion_carga(self, matriz_compatibilidad, stu_A1, stu_A2, stu_C):
    cargaA1 = []
    cargaA2 = []
    stu_A1_NC = stu_A1 - stu_C
    stu_A2_NC = stu_A2 - stu_C

    opciones_C_A1 = []
    for i in range(len(matriz_compatibilidad)):
      sum_fila = 0
      for j in range(len(matriz_compatibilidad[i])):
        sum_fila += matriz_compatibilidad[i][j]
      if sum_fila > 0:
        opciones_C_A1.append(1)
      else:
        opciones_C_A1.append(0)

    cant_opciones_C_A1 = sum(opciones_C_A1)
    carga_por_opcion_C_A1 = stu_C / cant_opciones_C_A1
    carga_por_opcion_NC_A1 = stu_A1_NC / len(matriz_compatibilidad)
    for i in range(len(matriz_compatibilidad)):
      cargaA1.append(carga_por_opcion_NC_A1 + (carga_por_opcion_C_A1 if opciones_C_A1[i] else 0))

    carga_por_opcion_NC_A2 = stu_A2_NC / len(matriz_compatibilidad[0])
    for j in range(len(matriz_compatibilidad[0])):
      cargaA2.append(carga_por_opcion_NC_A2)
      for i in range(len(matriz_compatibilidad)):
        if matriz_compatibilidad[i][j] == 1:
          sum_col = 0
          for k in range(len(matriz_compatibilidad[0])):
            sum_col += matriz_compatibilidad[i][k] if matriz_compatibilidad[i][k] == 1 else 0
          cargaA2[j] += (cargaA1[i] - carga_por_opcion_NC_A1) / sum_col

    return cargaA1, cargaA2

  def _generar_nuevas_compatibilidades(self, matriz_compatibilidad, estudiantes_A1, estudiantes_A2, estudiantes_compartidos):
    nuevas_compatibilidades = []
    for i in range(len(matriz_compatibilidad)):
      for j in range(len(matriz_compatibilidad[i])):
        if matriz_compatibilidad[i][j] == 0:
          matriz_compatibilidad[i][j] = 1
          cargaA1, cargaA2 = self._simulacion_carga(
            matriz_compatibilidad,
            estudiantes_A1,
            estudiantes_A2,
            estudiantes_compartidos,
          )
          varianza_norm_A1 = self._calculo_varianza_normalizada(cargaA1)
          varianza_norm_A2 = self._calculo_varianza_normalizada(cargaA2)
          matriz_compatibilidad[i][j] = 0
          nuevas_compatibilidades.append((i, j, varianza_norm_A1, varianza_norm_A2))

    nuevas_compatibilidades.sort(key=lambda x: x[2] + x[3])
    return nuevas_compatibilidades

  def _generar_matriz_compatibilidad(self, paralelos_A1, estudiantes_A1, paralelos_A2, estudiantes_A2, estudiantes_compartidos):
    matriz_compatibilidad = [[0 for _ in range(paralelos_A2)] for _ in range(paralelos_A1)]
    matriz_compatibilidad[0][0] = 1
    cargaA1, cargaA2 = self._simulacion_carga(
      matriz_compatibilidad,
      estudiantes_A1,
      estudiantes_A2,
      estudiantes_compartidos,
    )
    varianza_norm_A1 = self._calculo_varianza_normalizada(cargaA1)
    varianza_norm_A2 = self._calculo_varianza_normalizada(cargaA2)

    while varianza_norm_A1 > self.umbral_varianza_aceptable or varianza_norm_A2 > self.umbral_varianza_aceptable:
      nuevas_compatibilidades = self._generar_nuevas_compatibilidades(
        matriz_compatibilidad,
        estudiantes_A1,
        estudiantes_A2,
        estudiantes_compartidos,
      )

      matriz_compatibilidad[nuevas_compatibilidades[0][0]][nuevas_compatibilidades[0][1]] = 1
      varianza_norm_A1 = nuevas_compatibilidades[0][2]
      varianza_norm_A2 = nuevas_compatibilidades[0][3]

    nuevas_compatibilidades = self._generar_nuevas_compatibilidades(
      matriz_compatibilidad,
      estudiantes_A1,
      estudiantes_A2,
      estudiantes_compartidos,
    )

    index = len(nuevas_compatibilidades) - 1
    while index >= 0:
      varianza_norm_A1 = nuevas_compatibilidades[index][2]
      varianza_norm_A2 = nuevas_compatibilidades[index][3]
      if varianza_norm_A1 > self.umbral_varianza_aceptable or varianza_norm_A2 > self.umbral_varianza_aceptable:
        i = nuevas_compatibilidades[index][0]
        j = nuevas_compatibilidades[index][1]
        matriz_compatibilidad[i][j] = -1
      index -= 1

    return matriz_compatibilidad


# ----------------------------------------------------------------------
# PROGRAMACIÓN ENTERA (SSP) - Con Balanceo de Carga
# ----------------------------------------------------------------------
class SSP:
  """Asigna estudiantes a paralelos (variable Y) dado un horario X.

  Estrategia:
  - Para cada estudiante, se intenta construir un path de asignación minimizando
    choques de bloques (backtracking con poda).
  - Luego se realiza una búsqueda local para reducir la "ventana" (huecos entre
    clases) sin introducir choques.

  API pública:
  - `solve()` genera (o re-genera) `modelo.Y` para el X actual.

  El resto de métodos se consideran internos y se nombran con prefijo `_`.
  """

  def __init__(self, modelo, alfa=1, cv_ideal=0.1, ventana_ideal=4) -> None:
    self.modelo = modelo
    self.alfa = alfa
    self.cv_ideal = cv_ideal
    self.ventana_ideal = ventana_ideal

    # OPTIMIZACIÓN FIJA: asignaturas que cursa cada estudiante
    # Formato: {id_estudiante: [id_asignatura1, ...]}
    self.asignaturas_estudiantes = {idx_e: [] for idx_e in range(self.modelo.E)}
    for (idx_e, idx_a), cursa in self.modelo.CE.items():
      if cursa == 1:
        self.asignaturas_estudiantes[idx_e].append(idx_a)

  def solve(self):
    """Calcula una asignación de estudiantes a paralelos (`modelo.Y`) para el X actual.

    Retorna una tupla con métricas (desbalance, ventana, FO, choques) calculadas
    con la evaluación interna del SSP.
    """
    self.modelo.reset_Y()
    # 1. PRE-CÁLCULO LOCAL: Bloques por paralelo
    # Formato: {(id_asignatura, id_paralelo): [id_bloque1, ...]}
    self.bloques_por_paralelo = {}
    for idx_a in range(self.modelo.A):
      for idx_p in range(self.modelo.P[idx_a]):
        bloques = []
        for idx_s in range(self.modelo.S[(idx_a, idx_p)]):
          for idx_b in range(self.modelo.B):
            if self.modelo.X.get((idx_a, idx_p, idx_s, idx_b), 0) == 1:
              bloques.append(idx_b)
        self.bloques_por_paralelo[(idx_a, idx_p)] = bloques

    # 2. Estructuras auxiliares
    # Dict para llevar la cuenta rápida de alumnos por paralelo
    # Formato: {(id_asignatura, id_paralelo): cantidad_actual}
    self.ocupacion_por_paralelo = {(idx_a, idx_p): 0 for idx_a in range(self.modelo.A)
                            for idx_p in range(self.modelo.P[idx_a])}

    # Dict para guardar los bloques ocupados por estudiante (se llena conforme asignamos)
    # Formato: {id_estudiante: [id_bloque1, ...]}
    self.bloques_por_estudiante = {idx_e: [] for idx_e in range(self.modelo.E)}

    # 3. Generación de asignaciones
    for idx_e in range(self.modelo.E):
      asignaturas = self.asignaturas_estudiantes[idx_e]
      if not asignaturas:
        continue

      # 3.1. Ordenar por oferta (Variable más restringida)
      asignaturas_ordenadas = sorted(asignaturas, key=lambda a: self.modelo.P[a])

      # 3.2. Inicializar récords para el Estudiante E
      self.min_choques_estudiante = float('inf')
      self.mejor_asignacion_estudiante = {}
      bloques_rama = []
      choques_rama = 0
      path_rama = {}

      # 3.3. Llamada recursiva
      self._asignar_asignaturas(idx_e, asignaturas_ordenadas,
                bloques_rama, choques_rama, path_rama)

      # 3.4. Aplicar el ganador global al modelo real (Solo aquí cambia la ocupación)
      for idx_a, idx_p in self.mejor_asignacion_estudiante.items():
        self.modelo.Y[(idx_e, idx_a, idx_p)] = 1
        self.ocupacion_por_paralelo[(idx_a, idx_p)] += 1
        self.bloques_por_estudiante[idx_e].extend(self.bloques_por_paralelo[(idx_a, idx_p)])

      # Realizamos una búsqueda local minimizando ventanas
      self._busqueda_local(idx_e, asignaturas[:])

    return self._evaluar_fo(self.alfa, self.cv_ideal, self.ventana_ideal)

  def _asignar_asignaturas(self, estudiante, asignaturas_pendientes,
                           bloques_rama, choques_rama, path_rama):

    # CASO BASE: Éxito total en la rama
    if not asignaturas_pendientes:
      self.min_choques_estudiante = choques_rama
      self.mejor_asignacion_estudiante = path_rama
      return

    # Selección de asignatura actual
    restantes = asignaturas_pendientes[:]
    idx_a = restantes.pop(0)

    # Ordenar paralelos por ocupación (Heurística de valor menos restrictivo)
    # Al estar ordenados, la primera rama de X choques será la de mejor ocupación
    paralelos_por_ocupacion = sorted(range(self.modelo.P[idx_a]),
                                     key=lambda p: self.ocupacion_por_paralelo[(idx_a, p)])

    for idx_p in paralelos_por_ocupacion:
      bloques_paralelo = self.bloques_por_paralelo[(idx_a, idx_p)]
      choques_paralelo = sum(1 for b in bloques_paralelo if b in bloques_rama)

      # PODA: Si ya igualamos o superamos el récord, descartamos la rama entera
      if choques_rama + choques_paralelo >= self.min_choques_estudiante:
        continue

      # Clonar estructuras para la siguiente profundidad (evitar enlaces de referencia)
      nuevo_path = path_rama.copy()
      nuevo_path[idx_a] = idx_p
      nuevos_bloques = bloques_rama + bloques_paralelo

      self._asignar_asignaturas(estudiante, restantes, nuevos_bloques,
                                choques_rama + choques_paralelo, nuevo_path)

  def _busqueda_local(self, estudiante, asignaturas):
    """
    Para un estudiante específico, intenta mejorar su ventana
    moviendo sus asignaturas a otros paralelos.
    """
    bloques_ocupados = self.bloques_por_estudiante[estudiante]
    # Estocástico (intencional): el orden afecta el óptimo local encontrado.
    rd.shuffle(asignaturas)
    mejora = True
    while mejora:
      mejora = False
      for idx_a in asignaturas:
        # Encontrar el paralelo asignado actualmente
        idx_p_actual = next((p for p in range(self.modelo.P[idx_a])
                         if self.modelo.Y.get((estudiante, idx_a, p), 0) == 1), None)
        if idx_p_actual is None:
          continue
        v_actual = self._calcular_ventana(bloques_ocupados, self.ventana_ideal)
        b_actuales = self.bloques_por_paralelo[(idx_a, idx_p_actual)]

        for idx_p_nuevo in range(self.modelo.P[idx_a]):
          if idx_p_nuevo == idx_p_actual: continue
          b_nuevos = self.bloques_por_paralelo[(idx_a, idx_p_nuevo)]

          # Paso A: Quitar bloques del paralelo actual de la lista de referencia
          # Usamos remove para quitar solo una instancia de cada bloque
          for b in b_actuales: bloques_ocupados.remove(b)

          # Paso B: Evaluar si el nuevo paralelo no causa choques con el resto
          if sum(1 for b in b_nuevos if b in bloques_ocupados) == 0:
            # Paso C: Insertar los bloques nuevos para calcular la ventana resultante
            bloques_ocupados.extend(b_nuevos)
            v_nueva = self._calcular_ventana(bloques_ocupados, self.ventana_ideal)

            if v_nueva < v_actual:
              # Confirmar cambio en el modelo y en la ocupación
              self.modelo.Y.pop((estudiante, idx_a, idx_p_actual), None)
              self.modelo.Y[(estudiante, idx_a, idx_p_nuevo)] = 1
              self.ocupacion_por_paralelo[(idx_a, idx_p_actual)] -= 1
              self.ocupacion_por_paralelo[(idx_a, idx_p_nuevo)] += 1
              mejora = True

              break # Salir del loop de paralelos para pasar a la siguiente asignatura
            else:
              # Deshacer: No mejoró la ventana, quitamos los nuevos y restauramos viejos
              for b in b_nuevos: bloques_ocupados.remove(b)
              bloques_ocupados.extend(b_actuales)
          else:
            # Deshacer: Generaba choques, restauramos bloques originales
            bloques_ocupados.extend(b_actuales)

  def _calcular_ventana(self, bloques_ocupados, ventana_ideal=4):
    """Calcula la ventana para una secuencia de bloques horarios"""
    if not bloques_ocupados: return 0

    # Ordenamos y -------------------------------------------------------------------------quitamos duplicados (Ya no)
    #bloques_unicos = sorted(list(set(bloques_ocupados)))
    bloques_ordenados = sorted(bloques_ocupados)

    # 1. Clasificación por día (0-34 // 7) y posición relativa (0-34 % 7)
    dias = {d: [] for d in range(self.modelo.D)}
    for b in bloques_ordenados:
      dias[b // self.modelo.Bd].append(b % self.modelo.Bd)

    sumatoria_ventanas = 0
    for b_dia in dias.values():
      if len(b_dia) < 2: continue

      # 2. Conteo de ventanas
      for i in range(len(b_dia) - 1):
        ventana = (b_dia[i+1] - b_dia[i] - 1)
        # Penalizar choque
        if ventana < 0:
          ventana = 7
        sumatoria_ventanas += ventana

      # 3. Regla almuerzo: al menos uno en [0,1,2,3] y al menos uno en [4,5,6]
      if b_dia[0] <= 3 and b_dia[-1] >= 4:
        sumatoria_ventanas += 1

    # 4. Penalización cuadrática si supera el umbral configurable (ventana_ideal)
    umbral = max(0, float(ventana_ideal))
    if sumatoria_ventanas > umbral:
      return umbral + (sumatoria_ventanas - umbral)**2

    return sumatoria_ventanas

  def _evaluar_fo(self, alfa=1, cv_ideal=0.1, ventana_ideal=4):
    """
    Calcula la función objetivo: (Desbalance/Desbalance_Ideal)^alfa * (Ventana/Ventana_Ideal)
    """
    suma_desviaciones_reales = 0
    suma_desviaciones_ideales = 0
    total_inscripciones = 0

    for idx_a in range(self.modelo.A):
      n_p = self.modelo.P[idx_a]
      inscritos = [self.ocupacion_por_paralelo[(idx_a, idx_p)] for idx_p in range(n_p)]

      # Solo calculamos para materias con más de 1 paralelo
      if n_p > 1:
        # 1. Datos Reales
        media_a = sum(inscritos) / n_p
        varianza = sum((n - media_a)**2 for n in inscritos) / n_p
        sigma_real = varianza**0.5
        suma_desviaciones_reales += sigma_real

        # 2. Datos Ideales (Basados en el CV por asignatura)
        # La desviación ideal es el X% de la media de esta materia
        sigma_ideal_a = media_a * cv_ideal
        suma_desviaciones_ideales += sigma_ideal_a
      else:
        # Materias con 1 paralelo no aportan al desbalance (desv=0)
        # pero sumamos 0 para mantener el promedio sobre el total de A
        pass

    # Promedios globales de desbalance
    desbalance_real = suma_desviaciones_reales / self.modelo.A
    desbalance_ideal = suma_desviaciones_ideales / self.modelo.A

    # 3. Ventanas
    ventana_total_real = sum(self._calcular_ventana(self.bloques_por_estudiante[e], ventana_ideal) for e in range(self.modelo.E))
    estudiantes_con_carga = sum(1 for e in range(self.modelo.E) if self.asignaturas_estudiantes[e])
    ventana_total_ideal = estudiantes_con_carga * ventana_ideal

    # Choques
    choques = sum(len(self.bloques_por_estudiante[e]) - len(set(self.bloques_por_estudiante[e])) for e in range(self.modelo.E))

    # 4. Función Objetivo Multiplicativa
    ratio_desbalance_crudo = desbalance_real / max(desbalance_ideal, 1e-6)
    ratio_desbalance_fo = ratio_desbalance_crudo**alfa
    ratio_ventana = ventana_total_real / max(ventana_total_ideal, 1e-6)
    return (ratio_desbalance_crudo, ratio_ventana, (ratio_desbalance_fo * ratio_ventana), choques)

class Nodo:
  """Nodo de Tabu Search.

  Guarda una solución candidata y el movimiento (move/swap) que la generó.
  """
  def __init__(self,
               id,
               X: dict,
               Y: dict,
               move: tuple,
               fo: float,
               tupla_fo: tuple) -> None:
    self.id = id
    self.X = X
    self.Y = Y
    self.move = move
    self.fo = fo
    self.tupla_fo = tupla_fo

class UCTP:
  """Tabu Search (UCTP) sobre la variable de horario X.

  El vecindario se genera perturbando X (move/swap) y, según `resolver_ssp`,
  puede re-optimizar Y con `SSP.solve()` o evaluar la FO con el Y actual.
  """
  def __init__(self,
               modelo,
               ssp,
               max_iteraciones = 100,
               max_iteraciones_sin_mejora = 25,
               tamaño_lista_tabu = 20,
               tamaño_vecindario = 50,
               resolver_ssp: bool = True) -> None:
    self.modelo = modelo
    self.ssp = ssp
    self.lista_tabu = []
    self.max_iteraciones = max_iteraciones
    self.max_iteraciones_sin_mejora = max_iteraciones_sin_mejora # Guardar parámetro
    self.tamaño_lista_tabu = tamaño_lista_tabu
    self.tamaño_vecindario = tamaño_vecindario
    self.resolver_ssp = bool(resolver_ssp)

  def solve(self):
    lista_tabu = []

    # Estado inicial
    tupla_fo = self.modelo.calc_fo_new(self.ssp.alfa, self.ssp.cv_ideal, self.ssp.ventana_ideal)
    X = Nodo(None, self.modelo.X.copy(), self.modelo.Y.copy(), None, tupla_fo[2], tupla_fo)
    X_prime = copy.deepcopy(X)

    iteracion_actual = 0
    contador_sin_mejora = 0            # <--- Contador para Criterio 1
    intentos_fallidos_consecutivos = 0 # <--- Seguridad para Criterio 2

    print(f"--- Inicio Tabu Search (FO Inicial: {X.fo}) ---")
    print("Desbalance:", X.tupla_fo[0])
    print("Insatisfacción:", X.tupla_fo[1])

    resultados.append(X.tupla_fo)
    mejores_resultados.append(X.tupla_fo)
    while True:
      print(f"\nIteración TS: {iteracion_actual + 1} | Mejor FO Global: {X_prime.fo} | Sin Mejora: {contador_sin_mejora}")

      # 1. Generación de vecindario
      vecindario = self._generar_vecindario(X)

      X_actual = None
      movimiento_valido = False

      # 2. Selección del mejor vecino no tabú (o aspiración)
      while not movimiento_valido and vecindario:
        X_actual = self._obtener_mejor_vecino(vecindario)
        es_movimiento_tabu = self._es_tabu(X_actual)

        if not es_movimiento_tabu:
          movimiento_valido = True
        else:
          # Criterio de aspiración: si es tabú pero mejora el global, se permite
          if self._cumple_criterio_aspiracion(X_actual, X_prime):
            print("  -> Movimiento Tabú aceptado por Criterio de Aspiración")
            movimiento_valido = True
          else:
            self._remover_vecino(vecindario, X_actual)
            X_actual = None # Resetear si fue removido

      # 3. Manejo de "Callejón sin salida" (MEJORA 2: Reintento)
      if not X_actual or not movimiento_valido:
        intentos_fallidos_consecutivos += 1
        print(f"  <!> No se encontraron movimientos válidos. Reintentando generación estocástica ({intentos_fallidos_consecutivos}/10)...")

        # Si fallamos 10 veces seguidas en la misma iteración, asumimos bloqueo real
        if intentos_fallidos_consecutivos >= 10:
             print("  <!> Se alcanzó el límite de reintentos estocásticos. Terminando búsqueda.")
             break

        # 'continue' salta al inicio del 'while True' SIN incrementar iteracion_actual,
        # forzando a _generar_vecindario a probar nuevos randoms.
        continue

      # Si encontramos movimiento, reseteamos el contador de fallos consecutivos
      intentos_fallidos_consecutivos = 0

      # 4. Actualizar Tabú y solución actual
      self._actualizar_lista_tabu(X_actual)
      X = X_actual
      resultados.append(X.tupla_fo)
      print(f"  -> Nuevo vecino aceptado. FO: {X.fo}")

      # 5. Actualizar Mejor Solución Global (MEJORA 1: Contador sin mejora)
      if X.fo < X_prime.fo:
        print(f"  * ¡MEJORA ENCONTRADA! {X_prime.fo} -> {X.fo}")
        mejores_resultados.append(X.tupla_fo)
        X_prime = copy.deepcopy(X)
        contador_sin_mejora = 0 # Reseteamos contador porque hubo mejora
      else:
        contador_sin_mejora += 1 # Incrementamos contador

      # 6. Criterios de Parada
      iteracion_actual += 1

      # A. Parada por iteraciones máximas
      if self._criterio_parada(iteracion_actual):
        print("--- Fin: Máximo de iteraciones alcanzado ---")
        break

      # B. Parada por estancamiento (MEJORA 1)
      if contador_sin_mejora >= self.max_iteraciones_sin_mejora:
        print(f"--- Fin: Se alcanzaron {self.max_iteraciones_sin_mejora} iteraciones sin mejora sustancial ---")
        break

    # Al final, aplicamos EXACTAMENTE la mejor solución encontrada (X,Y,FO)
    # tal como fue evaluada durante la búsqueda (sin re-optimizar Y).
    self.modelo.set_X(X_prime.X)
    self.modelo.set_Y(X_prime.Y)
    print(f"--- Solución Final TS: {X_prime.fo} ---")

    return X_prime

  # -----------------------------------------------------------------------
  # Métodos Auxiliares (Sin cambios lógicos mayores, solo el que ya tenías)
  # -----------------------------------------------------------------------
  def _generar_vecindario(self, X_nodo: Nodo):
    vecindario = []

    # Identificar sesiones asignadas (valor 1)
    asignaciones_activas = [k for k, v in X_nodo.X.items() if v == 1]

    if not asignaciones_activas:
        return []

    for _ in range(self.tamaño_vecindario):
      nueva_X = X_nodo.X.copy()
      movimiento = None
      operador = rd.choice(['swap', 'move'])

      # --- OPERADOR MOVE ---
      if operador == 'move':
        clase_random = rd.choice(asignaciones_activas)
        idx_a, idx_p, idx_s, b_actual = clase_random

        b_nuevo = rd.randint(0, self.modelo.B - 1)
        while b_nuevo == b_actual:
            b_nuevo = rd.randint(0, self.modelo.B - 1)

        nueva_X[(idx_a, idx_p, idx_s, b_actual)] = 0
        nueva_X[(idx_a, idx_p, idx_s, b_nuevo)] = 1

        movimiento = ('move', idx_a, idx_p, idx_s, b_actual, b_nuevo)

      # --- OPERADOR SWAP ---
      elif operador == 'swap':
        if len(asignaciones_activas) < 2:
            continue

        idx1 = rd.randint(0, len(asignaciones_activas) - 1)
        idx2 = rd.randint(0, len(asignaciones_activas) - 1)
        while idx1 == idx2:
             idx2 = rd.randint(0, len(asignaciones_activas) - 1)

        c1 = asignaciones_activas[idx1]
        c2 = asignaciones_activas[idx2]

        if c1[3] == c2[3]:
             continue

        nueva_X[(c1[0], c1[1], c1[2], c1[3])] = 0
        nueva_X[(c1[0], c1[1], c1[2], c2[3])] = 1
        nueva_X[(c2[0], c2[1], c2[2], c2[3])] = 0
        nueva_X[(c2[0], c2[1], c2[2], c1[3])] = 1

        movimiento = ('swap', c1, c2)

      # --- VALIDACIÓN Y CÁLCULO FO ---
      self.modelo.set_X(nueva_X)

      # Usando la validación optimizada que definimos previamente
      es_factible = True
      if hasattr(self.modelo, 'validar_restricciones_duras'):
          es_factible = self.modelo.validar_restricciones_duras()
      else:
          # Fallback por si no se ha definido la función maestra aún
          if not self.modelo.hc_1() or not self.modelo.hc_2() or \
           not self.modelo.hc_3() or not self.modelo.hc_4() or \
           not self.modelo.hc_8() or \
             not self.modelo.hc_7():
              es_factible = False
          if es_factible:
             res_hc6 = self.modelo.hc_6()
             if res_hc6 is not True:
               es_factible = False

      if es_factible:
          if self.resolver_ssp:
            resultado_fo = self.ssp.solve()
          else:
            resultado_fo = self.modelo.calc_fo_new(self.ssp.alfa, self.ssp.cv_ideal, self.ssp.ventana_ideal)

          fo_valor = resultado_fo[2]

          # Congelar la solución completa (X,Y) que produjo esta FO
          nuevo_nodo = Nodo(id=None, X=nueva_X, Y=self.modelo.Y.copy(), move=movimiento, fo=fo_valor, tupla_fo=resultado_fo)
          vecindario.append(nuevo_nodo)


    # Restaurar
    self.modelo.set_X(X_nodo.X)
    self.modelo.set_Y(X_nodo.Y)
    return vecindario

  def _obtener_mejor_vecino(self, vecindario: List):
    vecindario.sort(key=lambda x: x.fo)
    return vecindario[0]

  def _es_tabu(self, X: Nodo):
    for i in self.lista_tabu:
      if i.move == X.move:
        return True
    return False

  def _remover_vecino(self, vecindario: List, X: Nodo):
    if X in vecindario:
        vecindario.remove(X)

  def _actualizar_lista_tabu(self, X: Nodo):
    if len(self.lista_tabu) >= self.tamaño_lista_tabu:
      self.lista_tabu.pop(0)
    self.lista_tabu.append(X)

  def _cumple_criterio_aspiracion(self, X: Nodo, X_prime: Nodo):
    if X.fo < X_prime.fo:
      return True
    return False

  def _criterio_parada(self, iteracion_actual: int):
    if iteracion_actual >= self.max_iteraciones:
      return True
    return False

# ----------------------------------------------------------------------
