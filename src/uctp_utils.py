# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def normalizar_id_estudiante(value) -> str:
  """Normaliza un identificador a string."""
  if value is None:
    return ""

  if isinstance(value, bool):
    return str(value)

  if isinstance(value, int):
    return str(value)

  if isinstance(value, float):
    if value.is_integer():
      return str(int(value))
    return str(value)

  s = str(value).strip()
  if s.endswith('.0'):
    head = s[:-2]
    if head.isdigit():
      return head
  return s


_normalizar_id_estudiante = normalizar_id_estudiante


def leer_json(ruta: str | Path) -> Dict[str, Any]:
  with open(ruta, 'r', encoding='utf-8-sig') as f:
    return json.load(f)


def mezclar_configuraciones(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
  resultado = copy.deepcopy(base)
  if not isinstance(override, dict):
    return resultado

  for clave, valor in override.items():
    if isinstance(valor, dict) and isinstance(resultado.get(clave), dict):
      resultado[clave] = mezclar_configuraciones(resultado[clave], valor)
    else:
      resultado[clave] = copy.deepcopy(valor)
  return resultado


def configuracion_por_defecto() -> Dict[str, Any]:
  return {
    "dominio": {
      "json_path": "data/input/test.json",
      "institucion": "PUCV - Escuela de Ingeniería en Informática",
      "semestre": "2025-1",
      "max_carga_diaria": 8,
      "max_carga_bloque": 15,
    },
    "greedy": {
      "umbral_varianza_aceptable": 0.05,
      "umbral_compatibilidad_intercurso": 0.25,
      "asignacion_inteligente": True,
      "max_reintentos": 100,
    },
    "ssp": {
      "alfa": 1,
      "cv_ideal": 0.1,
      "ventana_ideal": 4,
    },
    "uctp": {
      "max_iteraciones": 100,
      "max_iteraciones_sin_mejora": 50,
      "tamaño_lista_tabu": 20,
      "tamaño_vecindario": 50,
      "resolver_ssp": True,
    },
    "flujo": {
      "max_iteraciones": 1,
    },
    "salida": {
      "ruta_json": None,
      "ruta_graficos": "data/output/graficos_optimizacion.png",
      "ruta_resultados": "data/output/results.txt",
      "guardar_graficos": True,
      "guardar_resultados": True,
    },
    "ejecucion": {
      "seed": None,
    },
  }


def ruta_json_salida_por_defecto(ruta_entrada_json: str) -> str:
  """Construye la salida por defecto como <entrada>.generado.json."""
  ruta = Path(ruta_entrada_json)
  if ruta.suffix.lower() == '.json':
    if ruta.parent.name == 'input' and ruta.parent.parent.name == 'data':
      return str(ruta.parent.parent / 'output' / f'{ruta.stem}.generado.json')
    return str(ruta.with_suffix('.generado.json'))
  return f"{ruta_entrada_json}.generado.json"


def registrar_warning_log(mensaje: str, ruta_log: str = 'warnings_logs.txt') -> None:
  """Agrega un warning al archivo de logs sin interrumpir el flujo."""
  try:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    Path(ruta_log).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_log, 'a', encoding='utf-8') as f:
      f.write(f'[{timestamp}] {mensaje}\n')
  except Exception:
    pass


_registrar_warning_log = registrar_warning_log
