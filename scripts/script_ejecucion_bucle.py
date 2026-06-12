
import subprocess, random, sys
random.seed(9999)
seeds = [random.randint(1,999999) for _ in range(2)]
for s in seeds:
    print(f'\n=== Seed {s} ===')
    subprocess.run([sys.executable, 'scripts/generador_instancias.py', '--config', 'config/config.generador.json', '--seed', str(s)])
    subprocess.run([sys.executable, 'UCTPPlanner.py', '--seed', str(s), '--no-plot'])