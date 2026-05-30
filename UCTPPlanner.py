# -*- coding: utf-8 -*-

"""UCTPPlanner: punto de entrada principal del flujo de horarios."""

import argparse
import random as rd
import time
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from src.dominio import Dominio
from src.solver import Greedy, Modelo, SSP, UCTP, mejores_resultados, resultados
from src.uctp_utils import (
  configuracion_por_defecto,
  leer_json,
  mezclar_configuraciones,
  ruta_json_salida_por_defecto,
)


def main(configuracion: Optional[Dict[str, Any]] = None):
  """Punto de entrada del flujo completo.

  Construye Dominio/Modelo, genera X con Greedy, asigna Y con SSP y mejora X con
  UCTP (Tabu Search). Devuelve el modelo final y trazas de FO.
  """
  tiempo_inicio = time.time()
  resultados.clear()
  mejores_resultados.clear()
  configuracion_final = mezclar_configuraciones(configuracion_por_defecto(), configuracion)
  dominio_cfg = configuracion_final.get('dominio', {})
  greedy_cfg = configuracion_final.get('greedy', {})
  ssp_cfg = configuracion_final.get('ssp', {})
  uctp_cfg = configuracion_final.get('uctp', {})
  flujo_cfg = configuracion_final.get('flujo', {})
  salida_cfg = configuracion_final.get('salida', {})
  ejecucion_cfg = configuracion_final.get('ejecucion', {})

  semilla = ejecucion_cfg.get('seed')
  if semilla is not None:
    try:
      semilla_int = int(semilla)
      rd.seed(semilla_int)
      np.random.seed(semilla_int)
    except Exception:
      pass

  MAX_ITERACIONES = int(flujo_cfg.get('max_iteraciones', 1))
  resultados_main = []
  mejores_resultados_main = []
  json_path = str(dominio_cfg.get('json_path', 'test.json'))
  dom = Dominio(json_path=json_path)
  dom.MAX_CARGA_DIARIA = int(dominio_cfg.get('max_carga_diaria', dom.MAX_CARGA_DIARIA))
  dom.MAX_CARGA_BLOQUE = int(dominio_cfg.get('max_carga_bloque', dom.MAX_CARGA_BLOQUE))
  modelo = Modelo(dom)
  modelo.resumen()
  greedy = Greedy(
    modelo,
    umbral_varianza_aceptable=float(greedy_cfg.get('umbral_varianza_aceptable', 0.05)),
    umbral_compatibilidad_intercurso=float(greedy_cfg.get('umbral_compatibilidad_intercurso', 0.25)),
    asignacion_inteligente=bool(greedy_cfg.get('asignacion_inteligente', True)),
    max_reintentos=int(greedy_cfg.get('max_reintentos', 100)),
  )
  ssp = SSP(
    modelo,
    alfa=ssp_cfg.get('alfa', 1),
    cv_ideal=ssp_cfg.get('cv_ideal', 0.1),
    ventana_ideal=ssp_cfg.get('ventana_ideal', 4),
  )
  uctp = UCTP(
    modelo,
    ssp,
    max_iteraciones=int(uctp_cfg.get('max_iteraciones', 100)),
    max_iteraciones_sin_mejora=int(uctp_cfg.get('max_iteraciones_sin_mejora', 50)),
    tamaño_lista_tabu=int(uctp_cfg.get('tamaño_lista_tabu', uctp_cfg.get('tamano_lista_tabu', 20))),
    tamaño_vecindario=int(uctp_cfg.get('tamaño_vecindario', uctp_cfg.get('tamano_vecindario', 50))),
    resolver_ssp=bool(uctp_cfg.get('resolver_ssp', True)),
  )

  print("\n--- INICIO DEL FLUJO PRINCIPAL ---")
  try:
    greedy.solve()
  except RuntimeError as e:
    print(str(e))
    print("Error: Greedy no pudo construir un horario factible dentro del limite de reintentos.")
    return None, resultados_main, mejores_resultados_main
  if not modelo.validar_restricciones_duras():
    print("Error: El horario generado por Greedy no es factible. Terminando ejecución.")
  if not modelo.hc_5():
    print("Error: El horario generado por Greedy no cumple con la restricción hc_5. Terminando ejecución.")

  mejor_solucion_X = modelo.X.copy()
  mejor_solucion_Y = modelo.Y.copy()
  mejor_fo_global = 10000
  solucion_X_mejor_balanceada = modelo.X.copy()
  fo_mejor_balanceada = 10000
  iteracion = 0

  while iteracion < MAX_ITERACIONES:
    print(f"\n--- ITERACIÓN DEL FLUJO PRINCIPAL {iteracion + 1} ---")
    print("--------------------------------------------------------")
    ssp.solve()
    F_actual = modelo.calc_fo_new(ssp.alfa, ssp.cv_ideal, ssp.ventana_ideal)
    _, _, fo_actual, _ = F_actual
    if float(fo_actual) < fo_mejor_balanceada:
      fo_mejor_balanceada = float(fo_actual)
      solucion_X_mejor_balanceada = modelo.X.copy()

    _best_ts = uctp.solve()
    F_prima = modelo.calc_fo_new(ssp.alfa, ssp.cv_ideal, ssp.ventana_ideal)
    print(f"F_actual = {F_actual[2]:.4f}, F_nueva = {F_prima[2]:.4f}")
    resultados_main.append(F_prima)

    _, _, fo_prima, _ = F_prima
    if float(fo_prima) < mejor_fo_global:
      mejor_fo_global = float(fo_prima)
      mejor_solucion_X = modelo.X.copy()
      mejor_solucion_Y = modelo.Y.copy()
      mejores_resultados_main.append(F_prima)

    iteracion += 1

  if iteracion == MAX_ITERACIONES:
    print("\n--- Máximo de iteraciones alcanzado ---")

  modelo.X = mejor_solucion_X
  modelo.Y = mejor_solucion_Y
  print("Resultado Final:")
  print(f"Mejor Solucion Encontrada (F): {mejor_fo_global}")
  print("--- FIN DEL FLUJO PRINCIPAL ---")
  tiempo_fin = time.time()
  tiempo_ejecucion = tiempo_fin - tiempo_inicio

  _postprocesar_y_exportar(
    modelo=modelo,
    salida_cfg=salida_cfg,
    dominio_cfg=dominio_cfg,
    tiempo_ejecucion=tiempo_ejecucion,
  )
  return modelo, resultados_main, mejores_resultados_main


def _postprocesar_y_exportar(
  modelo: Modelo,
  salida_cfg: Dict[str, Any],
  dominio_cfg: Dict[str, Any],
  tiempo_ejecucion: float,
) -> None:
  """Genera gráficos, guarda resultados y exporta el JSON final."""
  if resultados:
    resultados_plt = resultados[:100]
    mejores = []
    min_fo = float('inf')
    for r in resultados_plt:
      if r[2] < min_fo:
        min_fo = r[2]
        mejores.append(r)

    iteraciones = range(len(resultados_plt))
    desbalance = [r[0] for r in resultados_plt]
    insatisfaccion = [r[1] for r in resultados_plt]
    fo = [r[2] for r in resultados_plt]
    choques = [r[3] for r in resultados_plt]

    idx_mejores = []
    current_min = float('inf')
    for i, val in enumerate(fo):
      if val < current_min:
        current_min = val
        idx_mejores.append(i)

    best_desbalance = [desbalance[i] for i in idx_mejores]
    best_insatisfaccion = [insatisfaccion[i] for i in idx_mejores]
    best_fo = [fo[i] for i in idx_mejores]
    best_choques = [choques[i] for i in idx_mejores]

    fig, axs = plt.subplots(4, 1, figsize=(10, 15))
    axs[0].plot(iteraciones, desbalance, label='Desbalance', color='blue', alpha=0.6)
    axs[0].scatter(idx_mejores, best_desbalance, color='red', label='Mejora Global (Best FO)', zorder=5, s=50)
    axs[0].set_title('Evolución del Desbalance')
    axs[0].set_xlabel('Iteración')
    axs[0].set_ylabel('Valor Desbalance')
    axs[0].legend()
    axs[0].grid(True, linestyle='--', alpha=0.7)

    axs[1].plot(iteraciones, insatisfaccion, label='Insatisfacción', color='orange', alpha=0.6)
    axs[1].scatter(idx_mejores, best_insatisfaccion, color='red', label='Mejora Global (Best FO)', zorder=5, s=50)
    axs[1].set_title('Evolución de la Insatisfacción')
    axs[1].set_xlabel('Iteración')
    axs[1].set_ylabel('Valor Insatisfacción')
    axs[1].legend()
    axs[1].grid(True, linestyle='--', alpha=0.7)

    axs[2].plot(iteraciones, fo, label='Función Objetivo (FO)', color='green', alpha=0.6)
    axs[2].scatter(idx_mejores, best_fo, color='red', label='Mejora Global', zorder=5, s=50)
    axs[2].set_title('Evolución de la Función Objetivo')
    axs[2].set_xlabel('Iteración')
    axs[2].set_ylabel('Valor FO')
    axs[2].legend()
    axs[2].grid(True, linestyle='--', alpha=0.7)

    axs[3].plot(iteraciones, choques, label='Choques', color='purple', alpha=0.6)
    axs[3].scatter(idx_mejores, best_choques, color='red', label='Mejora Global (Best FO)', zorder=5, s=50)
    axs[3].set_title('Evolución de los Choques')
    axs[3].set_xlabel('Iteración')
    axs[3].set_ylabel('Cantidad Choques')
    axs[3].legend()
    axs[3].grid(True, linestyle='--', alpha=0.7)

    if bool(salida_cfg.get('guardar_graficos', True)):
      ruta_graficos = str(salida_cfg.get('ruta_graficos', 'graficos_optimizacion.png'))
      plt.tight_layout()
      plt.savefig(ruta_graficos)

    if mejores and bool(salida_cfg.get('guardar_resultados', True)):
      ruta = str(salida_cfg.get('ruta_resultados', 'results.txt'))
      with open(ruta, 'a', encoding='utf-8') as f:
        f.write(str((*(mejores[-1]), tiempo_ejecucion)) + "\n")

  try:
    ruta_json_cfg = salida_cfg.get('ruta_json')
    if ruta_json_cfg in (None, ''):
      ruta_json = ruta_json_salida_por_defecto(str(dominio_cfg.get('json_path', 'test.json')))
    else:
      ruta_json = str(ruta_json_cfg)
    modelo.dominio.exportar_json(
      modelo,
      ruta_json,
      institucion=str(dominio_cfg.get('institucion', 'PUCV - Escuela de Ingeniería en Informática')),
      semestre=str(dominio_cfg.get('semestre', '2025-1')),
    )
    print(f"Export JSON generado: {ruta_json}")
  except Exception as e:
    print(f"[WARN] No se pudo exportar JSON: {e}")


def construir_configuracion_desde_args(args: argparse.Namespace) -> Dict[str, Any]:
  configuracion = configuracion_por_defecto()

  if args.config:
    ruta_config = Path(args.config).expanduser().resolve()
    if not ruta_config.exists():
      raise SystemExit(f"No existe el config: {ruta_config}")
    configuracion = mezclar_configuraciones(configuracion, leer_json(ruta_config))

  if args.json_path:
    configuracion.setdefault('dominio', {})['json_path'] = args.json_path
  if args.output_json:
    configuracion.setdefault('salida', {})['ruta_json'] = args.output_json
  if args.max_iteraciones is not None:
    configuracion.setdefault('flujo', {})['max_iteraciones'] = args.max_iteraciones
  if args.seed is not None:
    configuracion.setdefault('ejecucion', {})['seed'] = args.seed
  if args.no_plot:
    configuracion.setdefault('salida', {})['guardar_graficos'] = False

  return configuracion


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Genera, evalúa y optimiza un horario UCTP a partir de un JSON de dominio.",
  )
  parser.add_argument("--config", help="Ruta a un JSON con secciones dominio/greedy/ssp/uctp/flujo/salida.")
  parser.add_argument("--json-path", help="Sobrescribe la ruta del JSON de dominio.")
  parser.add_argument("--output-json", help="Sobrescribe la ruta del JSON exportado.")
  parser.add_argument("--max-iteraciones", type=int, help="Sobrescribe las iteraciones del flujo principal.")
  parser.add_argument("--seed", type=int, help="Semilla para `random` y `numpy`.")
  parser.add_argument("--no-plot", action="store_true", help="Desactiva la generación del gráfico final.")
  args = parser.parse_args()

  configuracion = construir_configuracion_desde_args(args)
  modelo, resultados_main, mejores_resultados_main = main(configuracion)
