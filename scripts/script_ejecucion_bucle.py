
import subprocess, random, sys, os

if len(sys.argv) > 3 or len(sys.argv) < 2:
    print("Uso: python scripts/script_ejecucion_bucle.py <num_iteraciones> <semilla_inicial>")
    sys.exit(1)

if len(sys.argv) == 3:
    try:
        num_iteraciones = int(sys.argv[1])
        semilla_inicial = int(sys.argv[2])
    except ValueError:
        print("Error: Ambos argumentos deben ser enteros.")
        sys.exit(1)

if len(sys.argv) == 2:
    try:
        num_iteraciones = int(sys.argv[1])
        semilla_inicial = 999999
    except ValueError:
        print("Error: El argumento debe ser un entero.")
        sys.exit(1)

random.seed(semilla_inicial)
seeds = [random.randint(1,999999) for _ in range(num_iteraciones)]
for s in seeds:
    print(f'\n=== Seed {s} ===')
    subprocess.run([sys.executable, 'scripts/generador_instancias.py', '--config', 'config/config.generador.json', '--seed', str(s)])
    subprocess.run([sys.executable, 'UCTPPlanner.py', '--seed', str(s), '--no-plot'])