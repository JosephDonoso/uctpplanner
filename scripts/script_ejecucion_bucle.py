import json
import random
import sys
import time
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scripts.generador_instancias import _leer_json, generar_instancia
from src.uctp_utils import configuracion_por_defecto, mezclar_configuraciones
from UCTPPlanner import main as solver_main
INSTANCIA_TEMP = RAIZ / "data" / "input" / "_batch_temp.json"
CONFIG_GENERADOR = RAIZ / "config" / "config.generador.json"
RESULTADOS = RAIZ / "data" / "output" / "results.txt"


def main():
    if len(sys.argv) < 2:
        print(f"Uso: python {sys.argv[0]} <num_iteraciones> [semilla_inicial]")
        sys.exit(1)

    num_iteraciones = int(sys.argv[1])
    semilla_inicial = int(sys.argv[2]) if len(sys.argv) >= 3 else 999999

    config_gen = _leer_json(CONFIG_GENERADOR)
    config_solver_base = configuracion_por_defecto()

    random.seed(semilla_inicial)
    seeds = [random.randint(1, 999999) for _ in range(num_iteraciones)]

    print(f"Iniciando batch de {num_iteraciones} ejecuciones (semilla generadora: {semilla_inicial})")
    print(f"Resultados se acumulan en: {RESULTADOS}")
    print()

    for i, s in enumerate(seeds, start=1):
        t_inicio = time.perf_counter()
        print(f"[{i}/{num_iteraciones}] === Seed {s} ===", end=" ", flush=True)

        instancia = generar_instancia(config_gen, semilla_externa=s)
        INSTANCIA_TEMP.parent.mkdir(parents=True, exist_ok=True)
        INSTANCIA_TEMP.write_text(
            json.dumps(instancia, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        config_solver = mezclar_configuraciones(config_solver_base, {
            "dominio": {"json_path": str(INSTANCIA_TEMP)},
            "ejecucion": {"seed": s},
            "salida": {"guardar_graficos": False},
        })
        solver_main(config_solver)

        t_total = time.perf_counter() - t_inicio
        print(f"  ({t_total:.1f}s)")


if __name__ == "__main__":
    main()
