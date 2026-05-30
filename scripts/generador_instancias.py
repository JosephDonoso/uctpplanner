from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DIAS_DEFECTO = ["Lu", "Ma", "Mi", "Ju", "Vi"]
TIPOS_CLASES_DEFECTO = [
    {"tipo": "Cát", "peso": 0.45},
    {"tipo": "Ay.", "peso": 0.25},
    {"tipo": "Lab", "peso": 0.20},
    {"tipo": "Tal", "peso": 0.10},
]
PROTECCION_DEFECTO = [{"dia": "Ju", "bloque": "7-8"}]


def _leer_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _escalar_texto(valor: Any, default: str) -> str:
    if valor is None:
        return default
    texto = str(valor).strip()
    return texto if texto else default


def _obtener(config: Dict[str, Any], clave: str, default: Any = None) -> Any:
    if clave in config:
        return config[clave]
    for seccion in ("cantidades", "conteos", "parametros", "parámetros", "restricciones", "tiempos", "metadatos", "nombres", "generacion"):
        valor = config.get(seccion)
        if isinstance(valor, dict) and clave in valor:
            return valor[clave]
    return default


def _obtener_dict(config: Dict[str, Any], clave: str) -> Dict[str, Any]:
    valor = _obtener(config, clave, {})
    return valor if isinstance(valor, dict) else {}


def _obtener_lista(config: Dict[str, Any], clave: str, default: Optional[List[Any]] = None) -> List[Any]:
    valor = _obtener(config, clave, default if default is not None else [])
    return list(valor) if isinstance(valor, list) else list(default or [])


def _numero(config: Dict[str, Any], clave: str, default: float) -> float:
    valor = _obtener(config, clave, default)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float(default)


def _entero(config: Dict[str, Any], clave: str, default: int) -> int:
    valor = _obtener(config, clave, default)
    try:
        return int(valor)
    except (TypeError, ValueError):
        return int(default)


def _codigo_seq(prefijo: str, indice: int, ancho: int = 3) -> str:
    return f"{prefijo}{indice:0{ancho}d}"


def _normalizar_total_objetivo(cantidad: int, minimo: int, maximo: int, media: float) -> int:
    objetivo = int(round(cantidad * media))
    return max(cantidad * minimo, min(cantidad * maximo, objetivo))


def _distribuir_enteros(cantidad: int, minimo: int, maximo: int, media: float, rng: random.Random) -> List[int]:
    if cantidad <= 0:
        return []
    minimo = max(0, minimo)
    maximo = max(minimo, maximo)
    objetivo_total = _normalizar_total_objetivo(cantidad, minimo, maximo, media)
    valores = [minimo] * cantidad
    sobrante = objetivo_total - cantidad * minimo

    indices = list(range(cantidad))
    while sobrante > 0:
        rng.shuffle(indices)
        progreso = False
        for idx in indices:
            if sobrante <= 0:
                break
            if valores[idx] < maximo:
                valores[idx] += 1
                sobrante -= 1
                progreso = True
        if not progreso:
            break

    return valores


def _generar_bloques_diarios(cantidad: int) -> List[str]:
    return [f"{idx * 2 + 1}-{idx * 2 + 2}" for idx in range(cantidad)]


def _usar_lista_o_default(config: Dict[str, Any], clave: str, default: List[str]) -> List[str]:
    valor = _obtener_lista(config, clave, default)
    resultado = [_escalar_texto(item, item) for item in valor]
    return resultado if resultado else list(default)


def _normalizar_dias(config: Dict[str, Any]) -> List[str]:
    dias = _usar_lista_o_default(config, "dias", DIAS_DEFECTO)
    return dias if dias else list(DIAS_DEFECTO)


def _normalizar_bloques(config: Dict[str, Any]) -> List[str]:
    bloques = _usar_lista_o_default(config, "bloques", [])
    if bloques:
        return bloques
    bloques_diarios = _entero(config, "bloques_diarios", 7)
    return _generar_bloques_diarios(bloques_diarios)


def _cargar_tipos_clase(config: Dict[str, Any]) -> List[Tuple[str, float]]:
    raw = _obtener_lista(config, "tipos_clases", TIPOS_CLASES_DEFECTO)
    tipos: List[Tuple[str, float]] = []
    for item in raw:
        if isinstance(item, dict):
            tipo = _escalar_texto(item.get("tipo"), "")
            peso = item.get("peso", 1)
        else:
            tipo = _escalar_texto(item, "")
            peso = 1
        if not tipo:
            continue
        try:
            peso_num = float(peso)
        except (TypeError, ValueError):
            peso_num = 1.0
        if peso_num <= 0:
            peso_num = 1.0
        tipos.append((tipo, peso_num))
    if not tipos:
        tipos = [(item["tipo"], float(item["peso"])) for item in TIPOS_CLASES_DEFECTO]
    return tipos


def _seleccionar_tipos_clase(tipos: Sequence[Tuple[str, float]], cantidad: int, rng: random.Random) -> List[str]:
    if cantidad <= 0:
        return []
    disponibles = list(tipos)
    seleccionados: List[str] = []
    while cantidad > 0:
        if not disponibles:
            disponibles = list(tipos)
        if not disponibles:
            break
        total = sum(peso for _, peso in disponibles)
        if total <= 0:
            tipo, _ = disponibles.pop(0)
            seleccionados.append(tipo)
            cantidad -= 1
            continue
        r = rng.random() * total
        acumulado = 0.0
        indice = 0
        for idx, (_, peso) in enumerate(disponibles):
            acumulado += peso
            if r <= acumulado:
                indice = idx
                break
        tipo, _ = disponibles.pop(indice)
        seleccionados.append(tipo)
        cantidad -= 1
    return seleccionados


def _generar_clases_base_asignatura(
    cantidad_clases: int,
    tipos_clase: Sequence[Tuple[str, float]],
    rng: random.Random,
    prob_asignatura_con_ayudantia: float,
) -> List[Dict[str, Any]]:
    if cantidad_clases <= 0:
        return []

    tipos_sin_ay = [(tipo, peso) for tipo, peso in tipos_clase if tipo != "Ay."]
    if not tipos_sin_ay:
        tipos_sin_ay = list(tipos_clase)

    clases = [{"tipo": _seleccionar_tipos_clase(tipos_sin_ay, 1, rng)[0]} for _ in range(cantidad_clases)]

    if cantidad_clases >= 2 and rng.random() < prob_asignatura_con_ayudantia:
        idx_ay = rng.randrange(cantidad_clases)
        clases[idx_ay]["tipo"] = "Ay."

    if cantidad_clases == 1 and clases[0]["tipo"] == "Ay.":
        clases[0]["tipo"] = _seleccionar_tipos_clase(tipos_sin_ay, 1, rng)[0]

    return clases


def _construir_catalogo_cursos(cantidad_cursos: int) -> List[Dict[str, str]]:
    return [{"carrera": f"CUR{idx:02d}", "semestre": "01"} for idx in range(1, cantidad_cursos + 1)]


def _repartir_asignaturas_en_cursos(cantidad_asignaturas: int, cantidad_cursos: int, rng: random.Random) -> List[int]:
    if cantidad_cursos <= 0:
        return [0] * cantidad_asignaturas
    asignaturas_por_curso = cantidad_asignaturas // cantidad_cursos
    resto = cantidad_asignaturas % cantidad_cursos
    indices = list(range(cantidad_cursos))
    rng.shuffle(indices)
    resultado: List[int] = []
    for idx in indices:
        resultado.extend([idx] * asignaturas_por_curso)
    resultado.extend(indices[:resto])
    rng.shuffle(resultado)
    return resultado


def _crear_disponibilidad_maestro(
    dias: Sequence[str],
    bloques: Sequence[str],
    probabilidad: float,
    rng: random.Random,
) -> List[Dict[str, List[int]]]:
    disponibilidad: List[Dict[str, List[int]]] = []
    for dia in dias:
        fila = [1 if rng.random() < probabilidad else 0 for _ in bloques]
        if not any(fila):
            fila[rng.randrange(len(fila))] = 1
        disponibilidad.append({dia: fila})
    return disponibilidad


def _bloques_protegidos(config: Dict[str, Any]) -> List[Tuple[str, str]]:
    raw = _obtener_lista(config, "bloques_protegidos", PROTECCION_DEFECTO)
    resultado: List[Tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        dia = _escalar_texto(item.get("dia"), "")
        bloque = _escalar_texto(item.get("bloque"), "")
        if dia and bloque:
            resultado.append((dia, bloque))
    return resultado


def _dias_validos_por_restriccion(restriccion: str, dias: Sequence[str], dias_usados: Sequence[str]) -> List[str]:
    if restriccion == "days_distinct":
        return [dia for dia in dias if dia not in dias_usados]
    if restriccion == "days_gap_1":
        indices_usados = {dias.index(dia) for dia in dias_usados if dia in dias}
        bloqueados = set(indices_usados)
        for idx in indices_usados:
            if idx - 1 >= 0:
                bloqueados.add(idx - 1)
            if idx + 1 < len(dias):
                bloqueados.add(idx + 1)
        return [dia for idx, dia in enumerate(dias) if idx not in bloqueados]
    return list(dias)


def _feasible_blocks_for_teacher(
    dias: Sequence[str],
    bloques: Sequence[str],
    maestros: Sequence[str],
    disponibilidad_maestros: Dict[str, Dict[str, List[int]]],
    ocupacion_maestros: Dict[str, set],
    ocupacion_paralelo: set,
    dias_protegidos: set,
    restriccion: str,
) -> Dict[str, List[Tuple[str, str]]]:
    dias_validos = _dias_validos_por_restriccion(restriccion, dias, [dia for dia, _ in ocupacion_paralelo])
    resultado: Dict[str, List[Tuple[str, str]]] = {maestro: [] for maestro in maestros}
    for maestro in maestros:
        disp = disponibilidad_maestros.get(maestro, {})
        for dia in dias_validos:
            if dia not in disp:
                continue
            for idx_bloque, bloque in enumerate(bloques):
                if (dia, bloque) in dias_protegidos:
                    continue
                if (dia, bloque) in ocupacion_paralelo:
                    continue
                if (dia, bloque) in ocupacion_maestros.get(maestro, set()):
                    continue
                if idx_bloque >= len(disp[dia]) or disp[dia][idx_bloque] != 1:
                    continue
                resultado[maestro].append((dia, bloque))
    return resultado


def _elegir_maestro_balanceado(candidatos: Iterable[str], carga_por_maestro: Dict[str, int], rng: random.Random) -> str:
    candidatos_limpios = [c for c in candidatos if c]
    if not candidatos_limpios:
        raise ValueError("No hay maestros candidatos disponibles")
    rng.shuffle(candidatos_limpios)
    candidatos_limpios.sort(key=lambda nombre: (carga_por_maestro.get(nombre, 0), nombre))
    return candidatos_limpios[0]


def _elegir_bloque(
    opciones: Dict[str, List[Tuple[str, str]]],
    maestros: Sequence[str],
    carga_por_maestro: Dict[str, int],
    rng: random.Random,
) -> Optional[Tuple[str, str, str]]:
    candidatos: List[Tuple[int, int, str, str, str]] = []
    for maestro in maestros:
        for dia, bloque in opciones.get(maestro, []):
            candidatos.append((len(opciones.get(maestro, [])), carga_por_maestro.get(maestro, 0), maestro, dia, bloque))
    if not candidatos:
        return None
    rng.shuffle(candidatos)
    candidatos.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]))
    _, _, maestro, dia, bloque = candidatos[0]
    return maestro, dia, bloque


def _preasignar_paralelo(
    paralelo: Dict[str, Any],
    dias: Sequence[str],
    bloques: Sequence[str],
    disponibilidad_maestros: Dict[str, Dict[str, List[int]]],
    ocupacion_maestros: Dict[str, set],
    dias_protegidos: set,
    rng: random.Random,
) -> bool:
    clases = paralelo.get("clases", [])
    ocupacion_paralelo: set = set()
    asignaciones: List[Tuple[Dict[str, Any], Tuple[str, str]]] = []

    clases_ordenadas = sorted(
        [clase for clase in clases if isinstance(clase, dict)],
        key=lambda clase: 0 if clase.get("tipo") != "Ay." else 1,
    )

    for clase in clases_ordenadas:
        tipo = clase.get("tipo")
        maestros_clase = clase.get("maestros")
        if tipo == "Ay.":
            candidatos = []
        else:
            if isinstance(maestros_clase, list) and maestros_clase:
                candidatos = [str(nombre) for nombre in maestros_clase if str(nombre).strip()]
            else:
                candidatos = [str(nombre) for nombre in paralelo.get("maestros", []) if str(nombre).strip()]

        candidatos = candidatos or [str(nombre) for nombre in paralelo.get("maestros", []) if str(nombre).strip()]
        if not candidatos:
            if tipo == "Ay.":
                candidatos = ["__SIN_MAESTRO__"]
            else:
                return False

        if tipo == "Ay.":
            opciones: List[Tuple[str, str]] = []
            for dia in dias:
                for bloque in bloques:
                    if (dia, bloque) in dias_protegidos:
                        continue
                    if (dia, bloque) in ocupacion_paralelo:
                        continue
                    opciones.append((dia, bloque))
            if not opciones:
                for clase_asignada, _ in asignaciones:
                    clase_asignada.pop("horario_predefinido", None)
                return False
            dia, bloque = rng.choice(opciones)
            clase["maestros"] = None
            clase["horario_predefinido"] = {"dia": dia, "bloque": bloque}
            ocupacion_paralelo.add((dia, bloque))
            asignaciones.append((clase, (dia, bloque)))
            continue

        opciones_por_maestro = _feasible_blocks_for_teacher(
            dias=dias,
            bloques=bloques,
            maestros=candidatos,
            disponibilidad_maestros=disponibilidad_maestros,
            ocupacion_maestros=ocupacion_maestros,
            ocupacion_paralelo=ocupacion_paralelo,
            dias_protegidos=dias_protegidos,
            restriccion=paralelo.get("restriccion_teoricas", "none"),
        )
        elegido = _elegir_bloque(opciones_por_maestro, candidatos, {nombre: 0 for nombre in candidatos}, rng)
        if elegido is None:
            for clase_asignada, _ in asignaciones:
                clase_asignada.pop("horario_predefinido", None)
            return False

        maestro_elegido, dia, bloque = elegido
        clase["maestros"] = [maestro_elegido]
        clase["horario_predefinido"] = {"dia": dia, "bloque": bloque}
        ocupacion_paralelo.add((dia, bloque))
        ocupacion_maestros.setdefault(maestro_elegido, set()).add((dia, bloque))
        asignaciones.append((clase, (dia, bloque)))

    return True


def generar_instancia(config: Dict[str, Any]) -> Dict[str, Any]:
    semilla = _obtener(config, "seed", None)
    rng = random.Random(semilla)

    metadatos = _obtener_dict(config, "metadatos")
    restricciones_cfg = _obtener_dict(config, "restricciones")
    tiempos_cfg = _obtener_dict(config, "tiempos")
    cantidades_cfg = _obtener_dict(config, "cantidades") or _obtener_dict(config, "conteos")
    nombres_cfg = _obtener_dict(config, "nombres")

    institucion = _escalar_texto(metadatos.get("institucion"), "PUCV - Escuela de Ingeniería en Informática")
    semestre = _escalar_texto(metadatos.get("semestre"), "2025-1")

    dias = _normalizar_dias(tiempos_cfg)
    bloques = _normalizar_bloques(tiempos_cfg)
    bloques_totales = _entero(tiempos_cfg, "bloques_totales", _entero(config, "bloques_totales", len(dias) * len(bloques)))
    if bloques_totales != len(dias) * len(bloques):
        raise ValueError(
            f"Los bloques declarados no calzan: bloques_totales={bloques_totales}, "
            f"dias*bloques_diarios={len(dias) * len(bloques)}"
        )

    max_carga_diaria = _entero(restricciones_cfg, "MAX_CARGA_DIARIA", 8)
    max_carga_bloque = _entero(restricciones_cfg, "MAX_CARGA_BLOQUE", 15)

    n_asignaturas = _entero(cantidades_cfg, "asignaturas", 70)
    min_paralelos = _entero(cantidades_cfg, "paralelos_min", 1)
    max_paralelos = _entero(cantidades_cfg, "paralelos_max", 4)
    media_paralelos = _numero(cantidades_cfg, "media_paralelos_por_asignatura", 1.48)
    min_sesiones = _entero(cantidades_cfg, "sesiones_min", 2)
    max_sesiones = _entero(cantidades_cfg, "sesiones_max", 4)
    media_sesiones = _numero(cantidades_cfg, "media_sesiones_por_asignatura", 2.7)

    n_maestros = _entero(cantidades_cfg, "maestros", 50)
    min_paralelos_maestro = _entero(cantidades_cfg, "paralelos_min_por_maestro", 1)
    max_paralelos_maestro = _entero(cantidades_cfg, "paralelos_max_por_maestro", 4)
    media_paralelos_maestro = _numero(cantidades_cfg, "media_paralelos_por_maestro", 2.3)
    prob_disponibilidad_maestro_bloque = _numero(cantidades_cfg, "prob_disponibilidad_maestro_bloque", 0.7)

    n_estudiantes = _entero(cantidades_cfg, "estudiantes", 1200)
    min_sesiones_estudiante = _entero(cantidades_cfg, "sesiones_min_por_estudiante", 0)
    max_sesiones_estudiante = _entero(cantidades_cfg, "sesiones_max_por_estudiante", 7)
    media_sesiones_estudiante = _numero(cantidades_cfg, "media_sesiones_por_estudiante", 3.2)

    n_cursos = _entero(cantidades_cfg, "cursos", 15)
    prob_relacion_asignatura_curso = _numero(cantidades_cfg, "prob_relacion_asignatura_curso", 0.88)
    prob_asignaturas_preasignadas = _numero(cantidades_cfg, "prob_asignaturas_preasignadas", 0.05)
    prob_asignatura_con_ayudantia = _numero(cantidades_cfg, "prob_asignatura_con_ayudantia", 0.35)
    prob_un_maestro_por_paralelo_compartido = _numero(cantidades_cfg, "prob_un_maestro_por_paralelo_compartido", 0.7)

    prob_restriccion_dias_distintos = _numero(restricciones_cfg, "prob_restriccion_teorica_dias_distintos", 0.0)
    prob_restriccion_1_dia = _numero(restricciones_cfg, "prob_restriccion_teorica_separadas_1_dia", 0.0)

    prefijo_asignatura = _escalar_texto(nombres_cfg.get("prefijo_asignatura"), "ASG")
    prefijo_maestro = _escalar_texto(nombres_cfg.get("prefijo_maestro"), "DOC")
    prefijo_estudiante = _escalar_texto(nombres_cfg.get("prefijo_estudiante"), "EST")

    tipos_clase = _cargar_tipos_clase(config)
    cursos_catalogo = _construir_catalogo_cursos(n_cursos)
    curso_por_asignatura = _repartir_asignaturas_en_cursos(n_asignaturas, n_cursos, rng)
    paralelos_por_asignatura = _distribuir_enteros(n_asignaturas, min_paralelos, max_paralelos, media_paralelos, rng)
    sesiones_por_asignatura = _distribuir_enteros(n_asignaturas, min_sesiones, max_sesiones, media_sesiones, rng)

    total_paralelos = sum(paralelos_por_asignatura)
    objetivo_asignaciones_maestro = _normalizar_total_objetivo(n_maestros, min_paralelos_maestro, max_paralelos_maestro, media_paralelos_maestro)
    objetivo_asignaciones_maestro = max(objetivo_asignaciones_maestro, total_paralelos)

    maestros: List[Dict[str, Any]] = []
    for idx_m in range(1, n_maestros + 1):
        maestros.append(
            {
                "nombre": _codigo_seq(prefijo_maestro, idx_m),
                "disponibilidad": _crear_disponibilidad_maestro(dias, bloques, prob_disponibilidad_maestro_bloque, rng),
            }
        )

    carga_por_maestro = {maestro["nombre"]: 0 for maestro in maestros}
    asignaturas: List[Dict[str, Any]] = []
    paralelos_flat: List[Dict[str, Any]] = []
    paralelos_por_asignatura_dict: Dict[int, List[Dict[str, Any]]] = {}

    for idx_a in range(n_asignaturas):
        codigo_asignatura = _codigo_seq(prefijo_asignatura, idx_a + 1)
        curso = cursos_catalogo[curso_por_asignatura[idx_a]]
        clases_base = _generar_clases_base_asignatura(
            sesiones_por_asignatura[idx_a],
            tipos_clase,
            rng,
            prob_asignatura_con_ayudantia,
        )
        paralelos_asignatura: List[Dict[str, Any]] = []
        for idx_p in range(1, paralelos_por_asignatura[idx_a] + 1):
            paralelo = {
                "codigo": f"{idx_p:02d}",
                "maestros": [],
                "restriccion_teoricas": "none",
                "clases": copy.deepcopy(clases_base),
            }
            paralelos_asignatura.append(paralelo)
            paralelos_flat.append(
                {
                    "codigo_asignatura": codigo_asignatura,
                    "paralelo": paralelo,
                    "indice_asignatura": idx_a,
                    "indice_paralelo": idx_p - 1,
                    "sesiones": sesiones_por_asignatura[idx_a],
                }
            )
            paralelos_por_asignatura_dict.setdefault(idx_a, []).append(paralelos_flat[-1])
        asignaturas.append(
            {
                "codigo": codigo_asignatura,
                "nombre": f"Asignatura {codigo_asignatura}",
                "curso": curso,
                "paralelos": paralelos_asignatura,
            }
        )

    # Primer pase: un maestro por paralelo.
    for entry in paralelos_flat:
        paralelo = entry["paralelo"]
        candidatos = [maestro["nombre"] for maestro in maestros if carga_por_maestro[maestro["nombre"]] < max_paralelos_maestro]
        if not candidatos:
            candidatos = [maestro["nombre"] for maestro in maestros]
        maestro_base = _elegir_maestro_balanceado(candidatos, carga_por_maestro, rng)
        paralelo["maestros"].append(maestro_base)
        carga_por_maestro[maestro_base] += 1

    # Segundo pase: agregar maestros extra para compartir paralelos.
    extra_restantes = objetivo_asignaciones_maestro - total_paralelos
    while extra_restantes > 0:
        candidatos_paralelo = [entry for entry in paralelos_flat if len(entry["paralelo"]["maestros"]) < min(4, len(maestros))]
        if not candidatos_paralelo:
            break
        rng.shuffle(candidatos_paralelo)
        if rng.random() < prob_un_maestro_por_paralelo_compartido:
            candidatos_paralelo.sort(key=lambda entry: (len(entry["paralelo"]["maestros"]), entry["codigo_asignatura"], entry["indice_paralelo"]))
        else:
            candidatos_paralelo.sort(key=lambda entry: (entry["codigo_asignatura"], entry["indice_paralelo"]))
        entrada = candidatos_paralelo[0]
        paralelo = entrada["paralelo"]
        candidatos_maestro = [maestro["nombre"] for maestro in maestros if maestro["nombre"] not in paralelo["maestros"] and carga_por_maestro[maestro["nombre"]] < max_paralelos_maestro]
        if not candidatos_maestro:
            candidatos_maestro = [maestro["nombre"] for maestro in maestros if maestro["nombre"] not in paralelo["maestros"]]
        if not candidatos_maestro:
            break
        maestro_extra = _elegir_maestro_balanceado(candidatos_maestro, carga_por_maestro, rng)
        paralelo["maestros"].append(maestro_extra)
        carga_por_maestro[maestro_extra] += 1
        extra_restantes -= 1

    # Restricciones teoricas por paralelo.
    restricciones_dias_distintos: List[Dict[str, str]] = []
    restricciones_1_dia: List[Dict[str, str]] = []
    for entry in paralelos_flat:
        paralelo = entry["paralelo"]
        r = rng.random()
        if r < prob_restriccion_dias_distintos:
            paralelo["restriccion_teoricas"] = "days_distinct"
            restricciones_dias_distintos.append({"codigo_asignatura": entry["codigo_asignatura"], "paralelo": paralelo["codigo"]})
        elif r < prob_restriccion_dias_distintos + prob_restriccion_1_dia:
            paralelo["restriccion_teoricas"] = "days_gap_1"
            restricciones_1_dia.append({"codigo_asignatura": entry["codigo_asignatura"], "paralelo": paralelo["codigo"]})

    disponibilidad_maestros = {
        maestro["nombre"]: {list(dia_obj.keys())[0]: list(dia_obj.values())[0] for dia_obj in maestro["disponibilidad"]}
        for maestro in maestros
    }
    ocupacion_maestros: Dict[str, set] = {maestro["nombre"]: set() for maestro in maestros}
    dias_protegidos = set(_bloques_protegidos(config))

    # Construccion de clases y preasignaciones factibles.
    for entry in paralelos_flat:
        paralelo = entry["paralelo"]
        maestros_paralelo = list(paralelo["maestros"])
        carga_clases_por_maestro = {maestro: 0 for maestro in maestros_paralelo}
        clases = paralelo.get("clases", [])
        for clase in clases:
            if not isinstance(clase, dict):
                continue
            tipo = clase.get("tipo")
            if tipo == "Ay.":
                clase["maestros"] = None
                continue

            if not maestros_paralelo:
                clase["maestros"] = None if tipo == "Ay." else []
                continue

            maestro_clase = min(
                maestros_paralelo,
                key=lambda nombre: (
                    carga_clases_por_maestro.get(nombre, 0),
                    carga_por_maestro.get(nombre, 0),
                    nombre,
                ),
            )
            clase["maestros"] = [maestro_clase]
            carga_clases_por_maestro[maestro_clase] += 1

    for idx_a, entries in paralelos_por_asignatura_dict.items():
        if idx_a >= len(asignaturas):
            continue
        if rng.random() >= prob_asignaturas_preasignadas:
            continue
        snapshot_ocupacion_maestros = {nombre: set(ocupadas) for nombre, ocupadas in ocupacion_maestros.items()}
        exito_asignatura = True
        for entry in entries:
            paralelo = entry["paralelo"]
            ok = _preasignar_paralelo(
                paralelo=paralelo,
                dias=dias,
                bloques=bloques,
                disponibilidad_maestros=disponibilidad_maestros,
                ocupacion_maestros=ocupacion_maestros,
                dias_protegidos=dias_protegidos,
                rng=rng,
            )
            if not ok:
                exito_asignatura = False
                break
        if not exito_asignatura:
            ocupacion_maestros = snapshot_ocupacion_maestros
            for entry in entries:
                for clase in entry["paralelo"].get("clases", []):
                    if isinstance(clase, dict):
                        clase.pop("horario_predefinido", None)

    # Estudiantes.
    sesiones_por_estudiante = _distribuir_enteros(n_estudiantes, min_sesiones_estudiante, max_sesiones_estudiante, media_sesiones_estudiante, rng)
    curso_a_asignaturas: Dict[int, List[int]] = {idx: [] for idx in range(n_cursos)}
    for idx_a, curso_idx in enumerate(curso_por_asignatura):
        curso_a_asignaturas[curso_idx].append(idx_a)
    cursos_con_ramos = [idx for idx, lista in curso_a_asignaturas.items() if lista]
    if not cursos_con_ramos:
        cursos_con_ramos = list(range(n_cursos))

    estudiantes: List[Dict[str, Any]] = []
    for idx_e in range(n_estudiantes):
        cantidad = sesiones_por_estudiante[idx_e]
        curso_base = rng.choice(cursos_con_ramos)
        materias: List[Dict[str, str]] = []
        elegidas: set = set()
        for _ in range(cantidad):
            if rng.random() < prob_relacion_asignatura_curso:
                pool = [idx for idx in curso_a_asignaturas.get(curso_base, []) if idx not in elegidas]
            else:
                pool = [idx for idx in range(len(asignaturas)) if idx not in elegidas and idx not in curso_a_asignaturas.get(curso_base, [])]
            if not pool:
                pool = [idx for idx in range(len(asignaturas)) if idx not in elegidas]
            if not pool:
                break
            idx_asignatura = rng.choice(pool)
            elegidas.add(idx_asignatura)
            materias.append(
                {
                    "codigo": asignaturas[idx_asignatura]["codigo"],
                    "paralelo": asignaturas[idx_asignatura]["paralelos"][0]["codigo"],
                }
            )
        estudiantes.append({"id": _codigo_seq(prefijo_estudiante, idx_e + 1, ancho=4), "asignaturas": materias})

    profesores_json: List[Dict[str, Any]] = []
    for maestro in maestros:
        profesores_json.append(
            {
                "nombre": maestro["nombre"],
                "respeta_max_carga_diaria": True,
                "max_carga_diaria": max_carga_diaria,
                "respeta_max_carga_semanal": True,
                "max_carga_semanal": "default",
            }
        )

    return {
        "metadatos": {
            "institucion": institucion,
            "semestre": semestre,
        },
        "restricciones": {
            "MAX_CARGA_DIARIA": max_carga_diaria,
            "MAX_CARGA_BLOQUE": max_carga_bloque,
            "CLASES_TEORICAS_DIAS_DISTINTOS": restricciones_dias_distintos,
            "CLASES_TEORICAS_SEPARADAS_1_DIA": restricciones_1_dia,
            "PROFESORES": profesores_json,
        },
        "tiempos": {
            "dias": dias,
            "bloques": bloques,
        },
        "eventos": {
            "tipo_clases": [tipo for tipo, _peso in tipos_clase],
            "asignaturas": asignaturas,
        },
        "recursos": {
            "maestros": maestros,
            "estudiantes": estudiantes,
        },
    }


def _resolver_salida(config_path: Path, config: Dict[str, Any], salida_arg: Optional[str]) -> Path:
    salida = salida_arg or _obtener(config, "output", None) or _obtener(config, "salida", None) or "instancia_generada.json"
    salida_path = Path(str(salida))
    if not salida_path.is_absolute():
        salida_path = (config_path.parent / salida_path).resolve()
    return salida_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera una instancia UCTP desde un config JSON.")
    parser.add_argument("--config", required=True, help="Ruta al config JSON.")
    parser.add_argument("--output", default=None, help="Ruta de salida del JSON generado.")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        raise SystemExit(f"No existe el config: {config_path}")

    config = _leer_json(config_path)
    instancia = generar_instancia(config)
    salida_path = _resolver_salida(config_path, config, args.output)
    salida_path.parent.mkdir(parents=True, exist_ok=True)
    salida_path.write_text(json.dumps(instancia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Instancia generada correctamente")
    print(f"Salida: {salida_path}")
    print(f"Asignaturas: {len(instancia['eventos']['asignaturas'])}")
    print(f"Paralelos: {sum(len(a['paralelos']) for a in instancia['eventos']['asignaturas'])}")
    print(f"Clases: {sum(len(p['clases']) for a in instancia['eventos']['asignaturas'] for p in a['paralelos'])}")
    print(f"Maestros: {len(instancia['recursos']['maestros'])}")
    print(f"Estudiantes: {len(instancia['recursos']['estudiantes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())