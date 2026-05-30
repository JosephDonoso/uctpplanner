/**
 * Constantes de configuración global
 */
const DIAS_INDICE = { "Lu": 0, "Ma": 1, "Mi": 2, "Ju": 3, "Vi": 4, "lu": 0, "ma": 1, "mi": 2, "ju": 3, "vi": 4 };
const DIAS_TEXTO = ["Lu", "Ma", "Mi", "Ju", "Vi"];
const BLOQUES_INDICE = {
  "1 - 2": 0, "3 - 4": 1, "5 - 6": 2, "7 - 8": 3,
  "9 - 10": 4, "11 - 12": 5, "13 - 14": 6,
  "1-2": 0, "3-4": 1, "5-6": 2, "7-8": 3,
  "9-10": 4, "11-12": 5, "13-14": 6
};
const BLOQUES_TEXTO = ["1 - 2", "3 - 4", "5 - 6", "7 - 8", "9 - 10", "11 - 12", "13 - 14"];
const TOTAL_DIAS = 5;
const BLOQUES_POR_DIA = 7;

function _pairKey_(a, b) {
  const sa = String(a);
  const sb = String(b);
  return sa < sb ? `${sa}||${sb}` : `${sb}||${sa}`;
}

function _splitPairKey_(key) {
  const parts = String(key || "").split("||");
  return { a: parts[0] || "", b: parts[1] || "" };
}

function _acumularMapaDeMapasNumericos_(target, source) {
  if (!source) return;
  for (const k in source) {
    if (!target[k]) target[k] = {};
    const inner = source[k] || {};
    for (const kk in inner) {
      target[k][kk] = (target[k][kk] || 0) + (inner[kk] || 0);
    }
  }
}

function _topBlocksSummary_(blockMap, topK) {
  const top = _topFromMap(blockMap || {}, topK || 3);
  return top.map(x => `${x.key}`).join(", ");
}

function _pct_(num, den, decimals) {
  const d = Number(den) || 0;
  if (d <= 0) return "";
  const n = Number(num) || 0;
  return `${_round((n / d) * 100, (decimals == null ? 1 : decimals))}%`;
}

function _topPairs_(countsMap, blocksByPairMap, topN) {
  const keys = Object.keys(countsMap || {});
  const arr = keys.map((k) => ({
    key: k,
    count: countsMap[k] || 0,
    blocks: (blocksByPairMap && blocksByPairMap[k]) ? blocksByPairMap[k] : {}
  }));

  arr.sort((x, y) => (y.count || 0) - (x.count || 0));
  const sliced = arr.slice(0, topN || 15);

  return sliced.map((it) => {
    const p = _splitPairKey_(it.key);
    return {
      a: p.a,
      b: p.b,
      count: it.count,
      top_bloques: _topBlocksSummary_(it.blocks, 3)
    };
  });
}

function _topPairsWithRates_(ctx) {
  const {
    occMap,
    blocksByPair,
    sharedStudentsByPair,
    impactedStudentsByPair,
    studentsByA,
    topN,
    sortByRate
  } = ctx;

  const keys = Object.keys(occMap || {});
  const arr = keys.map((k) => {
    const p = _splitPairKey_(k);
    const a = p.a;
    const b = p.b;
    const occ = occMap[k] || 0;
    const shared = (sharedStudentsByPair && sharedStudentsByPair[k]) ? sharedStudentsByPair[k] : 0;
    const impacted = (impactedStudentsByPair && impactedStudentsByPair[k]) ? impactedStudentsByPair[k] : 0;
    const aCount = (studentsByA && a) ? (studentsByA[a] || 0) : 0;
    const bCount = (studentsByA && b) ? (studentsByA[b] || 0) : 0;
    const rateShared = shared > 0 ? (impacted / shared) : 0;

    return {
      key: k,
      a,
      b,
      ocurrencias: occ,
      alumnos_comparten: shared,
      alumnos_afectados: impacted,
      pct_afectados_sobre_comparten: _pct_(impacted, shared, 1),
      pct_afectados_sobre_total_a: _pct_(impacted, aCount, 1),
      pct_afectados_sobre_total_b: _pct_(impacted, bCount, 1),
      top_bloques: _topBlocksSummary_((blocksByPair && blocksByPair[k]) ? blocksByPair[k] : {}, 3),
      _rate_shared: rateShared
    };
  });

  arr.sort((x, y) => {
    if (sortByRate) {
      const dr = (y._rate_shared || 0) - (x._rate_shared || 0);
      if (dr !== 0) return dr;
    }
    return (y.ocurrencias || 0) - (x.ocurrencias || 0);
  });

  return arr.slice(0, topN || 20).map((it) => {
    delete it._rate_shared;
    return it;
  });
}

const _FO_CONFIG_PROP_KEY_ = "FO_CONFIG_JSON";

/**
 * Agrega un menú personalizado al abrir la planilla.
 */
function onOpenEvaluacionFO_(e) {
  SpreadsheetApp.getUi()
    .createMenu("Evaluación FO")
    .addItem("Ejecutar evaluación", "evaluarFuncionObjetivo")
    .addSeparator()
    .addItem("Configurar parámetros…", "mostrarConfiguracionFO_")
    .addItem("Restaurar parámetros (usar hoja)", "restaurarConfiguracionFO_")
    .addToUi();
}

function _defaultConfigEvaluacion_() {
  return {
    alfa: 1,
    cv_ideal: 0.1,
    ventana_ideal: 4,
    resolver_segmentacion: 0,
    hoja_malla: "MALLAS",
    hoja_horarios: "HorariosYSalas",
    hoja_matriculas: "Matrículas2025-1"
  };
}

function _getUIConfigOverride_() {
  const props = PropertiesService.getDocumentProperties();
  const raw = props.getProperty(_FO_CONFIG_PROP_KEY_);
  if (!raw) return null;
  try {
    const obj = JSON.parse(raw);
    return obj && typeof obj === "object" ? obj : null;
  } catch (e) {
    return null;
  }
}

function _setUIConfigOverride_(cfg) {
  const props = PropertiesService.getDocumentProperties();
  props.setProperty(_FO_CONFIG_PROP_KEY_, JSON.stringify(cfg || {}));
}

function mostrarConfiguracionFO_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = _leerConfigEvaluacion_(ss);
  const tpl = HtmlService.createTemplateFromFile("ConfiguracionFO");
  tpl.config = config;
  const html = tpl.evaluate().setTitle("Parámetros Evaluación FO");
  try {
    html.setSandboxMode(HtmlService.SandboxMode.IFRAME);
  } catch (e) {
    // no-op
  }
  SpreadsheetApp.getUi().showSidebar(html);
}

function guardarConfiguracionFO_(payload) {
  try {
    const defaults = _defaultConfigEvaluacion_();
    const cfg = {
      alfa: _numOrDefault_(payload && payload.alfa, defaults.alfa),
      cv_ideal: _numOrDefault_(payload && payload.cv_ideal, defaults.cv_ideal),
      ventana_ideal: _numOrDefault_(payload && payload.ventana_ideal, defaults.ventana_ideal),
      resolver_segmentacion: _bool01OrDefault_(payload && payload.resolver_segmentacion, defaults.resolver_segmentacion),
      hoja_malla: _textOrDefault_(payload && payload.hoja_malla, defaults.hoja_malla),
      hoja_horarios: _textOrDefault_(payload && payload.hoja_horarios, defaults.hoja_horarios),
      hoja_matriculas: _textOrDefault_(payload && payload.hoja_matriculas, defaults.hoja_matriculas)
    };
    _setUIConfigOverride_(cfg);
    console.log("Configuración FO guardada (UI override)", cfg);
    return { ok: true, savedAt: new Date().toISOString(), cfg: cfg };
  } catch (e) {
    console.error("Error guardando configuración FO:", e);
    throw new Error("No se pudo guardar la configuración: " + (e && e.message ? e.message : String(e)));
  }
}

// Alias público para llamadas desde sidebar (más compatible que el sufijo `_`).
function guardarConfiguracionFO(payload) {
  return guardarConfiguracionFO_(payload);
}

function restaurarConfiguracionFO_() {
  PropertiesService.getDocumentProperties().deleteProperty(_FO_CONFIG_PROP_KEY_);
  SpreadsheetApp.getUi().alert("Parámetros restaurados. Se usarán los valores de la hoja (o defaults). ");
}

/**
 * Lee configuración desde la hoja "Evaluación de FO" (columna I).
 * Celdas esperadas:
 * - I3: ALFA
 * - I4: CV ideal
 * - I5: Ventana ideal (también es el umbral de penalización cuadrática)
 * - I7: Nombre hoja malla
 * - I8: Nombre hoja horarios
 * - I9: Nombre hoja matrículas
 */
function _leerConfigEvaluacion_(ss) {
  const defaults = _defaultConfigEvaluacion_();

  // 0) Si hay override por UI, tiene prioridad y no requiere hoja.
  const uiCfg = _getUIConfigOverride_();
  if (uiCfg) {
    return {
      alfa: _numOrDefault_(uiCfg.alfa, defaults.alfa),
      cv_ideal: _numOrDefault_(uiCfg.cv_ideal, defaults.cv_ideal),
      ventana_ideal: _numOrDefault_(uiCfg.ventana_ideal, defaults.ventana_ideal),
      resolver_segmentacion: _bool01OrDefault_(uiCfg.resolver_segmentacion, defaults.resolver_segmentacion),
      hoja_malla: _textOrDefault_(uiCfg.hoja_malla, defaults.hoja_malla),
      hoja_horarios: _textOrDefault_(uiCfg.hoja_horarios, defaults.hoja_horarios),
      hoja_matriculas: _textOrDefault_(uiCfg.hoja_matriculas, defaults.hoja_matriculas)
    };
  }

  const sh = ss.getSheetByName("Evaluación de FO");
  if (!sh) return defaults;

  const getI = (row) => sh.getRange(row, 9).getValue(); // Columna I
  const getA1 = (a1) => sh.getRange(a1).getValue();

  // Compatibilidad: el valor puede estar en I10 (convención H/I)
  // o en H11 (según layout personalizado del usuario).
  const rawResolver = (() => {
    const vI10 = getI(10);
    if (String(vI10 || "").trim() !== "") return vI10;
    const vH11 = getA1("H11");
    if (String(vH11 || "").trim() !== "") return vH11;
    const vI11 = getA1("I11");
    if (String(vI11 || "").trim() !== "") return vI11;
    return "";
  })();

  return {
    alfa: _numOrDefault_(getI(3), defaults.alfa),
    cv_ideal: _numOrDefault_(getI(4), defaults.cv_ideal),
    ventana_ideal: _numOrDefault_(getI(5), defaults.ventana_ideal),
    resolver_segmentacion: _bool01OrDefault_(rawResolver, defaults.resolver_segmentacion),
    hoja_malla: _textOrDefault_(getI(7), defaults.hoja_malla),
    hoja_horarios: _textOrDefault_(getI(8), defaults.hoja_horarios),
    hoja_matriculas: _textOrDefault_(getI(9), defaults.hoja_matriculas)
  };
}

function _numOrDefault_(value, def) {
  const n = Number(value);
  return Number.isFinite(n) ? n : def;
}

function _textOrDefault_(value, def) {
  const t = String(value == null ? "" : value).trim();
  return t ? t : def;
}

function _bool01OrDefault_(value, def) {
  if (value === true) return 1;
  if (value === false) return 0;
  const n = Number(value);
  if (!Number.isFinite(n)) return def;
  return n ? 1 : 0;
}

/**
 * Asegura que existan los títulos de parámetros en la hoja "Evaluación de FO".
 * No borra nada y solo rellena celdas vacías.
 *
 * Sección esperada:
 * - H1:I2 (combinado): "Parámetros para Ejecutar Evaluación"
 * - H3/H4/H5: ALFA, CV IDEAL, VENTANA IDEAL
 * - H7/H8/H9: HOJA MALLA, HOJA HORARIOS, HOJA MATRÍCULAS
 * - I3/I4/I5/I7/I8/I9: valores
 */
function _asegurarPlantillaConfigEvaluacion_(ss, config) {
  const sh = ss.getSheetByName("Evaluación de FO");
  if (!sh) return;

  const header = sh.getRange("H1:I2");
  try {
    header.merge();
  } catch (e) {
    // no-op
  }

  const headerValue = String(sh.getRange("H1").getValue() || "").trim();
  if (!headerValue) {
    sh.getRange("H1").setValue("Parámetros para Ejecutar Evaluación");
    header.setFontWeight("bold").setBackground("#f3f3f3").setHorizontalAlignment("center");
  }

  const items = [
    { labelCell: "H3", label: "ALFA", valueCell: "I3", def: config.alfa },
    { labelCell: "H4", label: "CV IDEAL", valueCell: "I4", def: config.cv_ideal },
    { labelCell: "H5", label: "VENTANA IDEAL", valueCell: "I5", def: config.ventana_ideal },
    { labelCell: "H7", label: "HOJA MALLA", valueCell: "I7", def: config.hoja_malla },
    { labelCell: "H8", label: "HOJA HORARIOS", valueCell: "I8", def: config.hoja_horarios },
    { labelCell: "H9", label: "HOJA MATRÍCULAS", valueCell: "I9", def: config.hoja_matriculas },
    // Flag: 0 = usar paralelos desde matrícula, 1 = resolver segmentación
    { labelCell: "H10", label: "RESOLVER SEGMENTACIÓN DE ESTUDIANTES", valueCell: "I10", def: config.resolver_segmentacion }
  ];

  for (const it of items) {
    const lc = sh.getRange(it.labelCell);
    if (!String(lc.getValue() || "").trim()) {
      lc.setValue(it.label).setFontWeight("bold");
    }
    const vc = sh.getRange(it.valueCell);
    if (!String(vc.getValue() || "").trim()) {
      vc.setValue(it.def);
    }
  }

  try {
    sh.setColumnWidths(8, 2, 220); // H:I
  } catch (e) {
    // no-op
  }
}

/**
 * Calcula la penalización por "ventanas" (bloques libres entre clases) y choques.
 * @param {number[]} bloquesOcupados - Array con los IDs numéricos de los bloques del estudiante.
 * @param {number} ventanaIdeal - Umbral tolerable de ventanas (se usa en la penalización cuadrática).
 * @returns {number} Valor total de la penalización por ventanas.
 */
function _calcularVentana(bloquesOcupados, ventanaIdeal) {
  if (!bloquesOcupados || bloquesOcupados.length === 0) return 0;

  const umbralVentana = (Number.isFinite(Number(ventanaIdeal)) && Number(ventanaIdeal) > 0)
    ? Number(ventanaIdeal)
    : 4;

  const bloquesOrdenados = [...bloquesOcupados].sort((a, b) => a - b);

  // 1. Clasificación por día (0-4 para Lu-Vi)
  const bloquesPorDia = { 0: [], 1: [], 2: [], 3: [], 4: [] };
  for (let b of bloquesOrdenados) {
    const dia = Math.floor(b / BLOQUES_POR_DIA);
    if (bloquesPorDia[dia]) {
      bloquesPorDia[dia].push(b % BLOQUES_POR_DIA);
    }
  }

  let totalVentanas = 0;

  for (let d = 0; d < TOTAL_DIAS; d++) {
    const bloquesDia = bloquesPorDia[d];
    if (bloquesDia.length < 2) continue;

    // 2. Conteo de ventanas
    for (let i = 0; i < bloquesDia.length - 1; i++) {
      let ventana = (bloquesDia[i + 1] - bloquesDia[i] - 1);
      
      // Penalizar choque horario
      if (ventana < 0) ventana = BLOQUES_POR_DIA;
      totalVentanas += ventana;
    }

    // 3. Regla almuerzo: al menos uno en la mañana [<=3] y otro en la tarde [>=4]
    if (bloquesDia[0] <= 3 && bloquesDia[bloquesDia.length - 1] >= 4) {
      totalVentanas += 1;
    }
  }

  // 4. Penalización cuadrática si supera el umbral tolerable (ventana ideal)
  if (totalVentanas > umbralVentana) {
    return umbralVentana + Math.pow((totalVentanas - umbralVentana), 2);
  }

  return totalVentanas;
}

/**
 * Busca y retorna los bloques horarios asignados a un paralelo específico.
 * @param {any[][]} datosHorario - Matriz de datos de la hoja de horarios.
 * @param {string} curso - Sigla del curso.
 * @param {number} numParalelo - Número del paralelo a buscar.
 * @returns {number[]} Array con los IDs numéricos de los bloques.
 */
function _obtenerBloquesDeParalelo(datosHorario, curso, numParalelo) {
  // Un mismo paralelo puede aparecer repetido en el mismo bloque
  // (p.ej. dos salas para la misma clase). Eso NO debe contar como choque.
  // Por eso deduplicamos los IDs de bloque por paralelo.
  const bloquesSet = new Set();

  for (let i = 1; i < datosHorario.length; i++) {
    const fila = datosHorario[i];
    const dia = _normalizarDiaClaveADia_(fila[0]);
    const bloqueTexto = fila[1];

    // Los bloques empiezan en la columna C (índice 2), cada iteración salta 5 columnas
    for (let c = 2; c < fila.length; c += 5) {
      const celdaCurso = _normalizarMateriaAParalelo_(fila[c]);
      if (!celdaCurso) continue;

      const siglaCurso = celdaCurso.slice(0, -3);
      const paraleloCurso = parseInt(celdaCurso.slice(-2), 10);

      if (siglaCurso === curso && paraleloCurso === numParalelo) {
        const idBloque = (DIAS_INDICE[dia] * BLOQUES_POR_DIA) + BLOQUES_INDICE[bloqueTexto];
        bloquesSet.add(idBloque);
      }
    }
  }

  return Array.from(bloquesSet).sort((a, b) => a - b);
}

function _normalizarDiaClaveADia_(dia) {
  const raw = String(dia == null ? "" : dia).trim();
  if (raw.trim().length >= 3){
    return raw.trim().slice(0,2);
  }
  return raw;
}

function _normalizarMateriaACurso_(materia) {
  const raw = String(materia == null ? "" : materia).trim();
  if (!raw) return "";

  // Si viene con guion: "CURSO-01" o "CURSO-1" -> "CURSO"
  if (raw.includes("-")) {
    const parts = raw.split("-");
    return String(parts[0] || "").trim();
  }

  // Si viene raw: "CURSO" 
  if (raw.length <= 7) {
    return raw.trim();
  }

  // Si viene pegado: "CURSO01" -> quitar los 2 últimos dígitos
  if (raw.length >= 3) {
    const last2 = raw.slice(-2);
    if (/^\d{2}$/.test(last2)) return raw.slice(0, -2).trim();
  }

  // Fallback: asumir que ya es el curso
  return raw;
}

function _normalizarMateriaAParalelo_(materia) {
  const raw = String(materia == null ? "" : materia).trim();
  if (!raw) return "";

  // Esperables: "CURSO-01", no convencional: "CURSO01", "CURSO-1"
  if (!raw.includes("-")) {
    if (raw.length < 3) return raw;
    return `${raw.slice(0, -2)}-${raw.slice(-2)}`;
  }

  const parts = raw.split("-");
  const curso = String(parts[0] || "").trim();
  const p = String(parts[1] || "").trim();
  if (!curso) return raw;
  if (!p) return curso;
  const paraleloNum = String(p).padStart(2, "0");
  return `${curso}-${paraleloNum}`;
}

function _buildParalelosDesdeMatricula_(datosEstudiantes, listaParalelos) {
  const setParalelos = {};
  for (let i = 0; i < (listaParalelos || []).length; i++) setParalelos[listaParalelos[i]] = true;

  const paralelosPorEstudiante = [];
  for (let i = 1; i < (datosEstudiantes || []).length; i++) {
    const materiasInscritas = String((datosEstudiantes[i] && datosEstudiantes[i][1]) || "").split(",");
    const paralelosValidos = [];
    const vistos = new Set();
    for (let j = 0; j < materiasInscritas.length; j++) {
      const idParalelo = _normalizarMateriaAParalelo_(materiasInscritas[j]);
      if (setParalelos[idParalelo] && !vistos.has(idParalelo)) {
        vistos.add(idParalelo);
        paralelosValidos.push(idParalelo);
      }
    }
    paralelosPorEstudiante.push(paralelosValidos);
  }
  return paralelosPorEstudiante;
}

function _buildBloquesYOcupacionDesdeParalelos_(paralelosPorEstudiante, bloquesPorParalelo, ocupacionActual) {
  const bloquesPorEstudiante = [];
  for (let i = 0; i < (paralelosPorEstudiante || []).length; i++) {
    const paralelos = paralelosPorEstudiante[i] || [];
    let bloquesEstudiante = [];
    for (let j = 0; j < paralelos.length; j++) {
      const paralelo = paralelos[j];
      const bloques = bloquesPorParalelo[paralelo];
      if (!bloques || bloques.length === 0) continue;
      bloquesEstudiante = bloquesEstudiante.concat(bloques);
      ocupacionActual[paralelo] = (ocupacionActual[paralelo] || 0) + 1;
    }
    bloquesPorEstudiante.push(bloquesEstudiante);
  }
  return bloquesPorEstudiante;
}

function _buildCursoParalelosMap_(listaParalelos) {
  const map = {};
  for (let i = 0; i < (listaParalelos || []).length; i++) {
    const idParalelo = listaParalelos[i];
    const curso = _cursoDesdeParalelo(idParalelo);
    if (!curso) continue;
    if (!map[curso]) map[curso] = [];
    map[curso].push(idParalelo);
  }
  return map;
}

function _shuffleInPlace_(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
  }
  return arr;
}

function _bloquesDesdeConteos_(counts) {
  const res = [];
  for (let b = 0; b < counts.length; b++) {
    const k = counts[b] || 0;
    for (let i = 0; i < k; i++) res.push(b);
  }
  return res;
}

function _resolverSegmentacionEstudiantes_(asignaturasPorEstudiante, cursoParalelos, bloquesPorParalelo, ocupacionActual, ventanaIdeal, opciones) {
  const usarBusquedaLocal = !(opciones && opciones.usarBusquedaLocal === false);
  const pararEnPrimeraFactible = !!(opciones && opciones.pararEnPrimeraFactible);
  const E = (asignaturasPorEstudiante || []).length;
  const paralelosPorEstudiante = new Array(E);
  const bloquesPorEstudiante = new Array(E);
  const totalBloques = TOTAL_DIAS * BLOQUES_POR_DIA;

  for (let idxE = 0; idxE < E; idxE++) {
    const cursosRaw = asignaturasPorEstudiante[idxE] || [];
    const cursos = cursosRaw.filter(c => c && cursoParalelos[c] && cursoParalelos[c].length > 0);
    if (cursos.length === 0) {
      paralelosPorEstudiante[idxE] = [];
      bloquesPorEstudiante[idxE] = [];
      continue;
    }

    // Variable más restringida primero (menos paralelos)
    const cursosOrdenados = [...cursos].sort((a, b) => (cursoParalelos[a].length - cursoParalelos[b].length));

    let bestChoques = Number.POSITIVE_INFINITY;
    let bestPath = null; // { curso: idParalelo }

    let foundSolution = false;

    const backtrack = (pos, blocksState, choques, path) => {
      if (pararEnPrimeraFactible && foundSolution) return true;
      if (pos >= cursosOrdenados.length) {
        bestChoques = choques;
        bestPath = path;
        foundSolution = true;
        return true;
      }

      const curso = cursosOrdenados[pos];
      const paralelos = cursoParalelos[curso] || [];

      // Valor menos restrictivo: paralelos con menor ocupación actual primero
      const paralelosOrdenados = [...paralelos].sort((p1, p2) => {
        const o1 = ocupacionActual[p1] || 0;
        const o2 = ocupacionActual[p2] || 0;
        return o1 - o2;
      });

      for (let i = 0; i < paralelosOrdenados.length; i++) {
        const idParalelo = paralelosOrdenados[i];
        const bloques = bloquesPorParalelo[idParalelo] || [];
        let choquesParalelo = 0;
        for (let j = 0; j < bloques.length; j++) {
          const b = bloques[j];
          if (blocksState[b]) choquesParalelo += 1;
        }

        if (!pararEnPrimeraFactible && choques + choquesParalelo >= bestChoques) continue;

        const nextState = blocksState.slice();
        for (let j = 0; j < bloques.length; j++) {
          const b = bloques[j];
          if (b >= 0 && b < totalBloques) nextState[b] = true;
        }

        const nextPath = Object.assign({}, path);
        nextPath[curso] = idParalelo;
        const solved = backtrack(pos + 1, nextState, choques + choquesParalelo, nextPath);
        if (solved && pararEnPrimeraFactible) return true;
      }

      return false;
    };

    backtrack(0, new Array(totalBloques).fill(false), 0, {});
    if (!bestPath) bestPath = {};

    // Aplicar solución al estado global (ocupación + bloques del estudiante)
    const asignacionPorCurso = {};
    const counts = new Array(totalBloques).fill(0);
    const paralelosElegidos = [];

    for (let i = 0; i < cursosOrdenados.length; i++) {
      const curso = cursosOrdenados[i];
      const idParalelo = bestPath[curso];
      if (!idParalelo) continue;
      asignacionPorCurso[curso] = idParalelo;
      paralelosElegidos.push(idParalelo);
      ocupacionActual[idParalelo] = (ocupacionActual[idParalelo] || 0) + 1;
      const bloques = bloquesPorParalelo[idParalelo] || [];
      for (let j = 0; j < bloques.length; j++) {
        const b = bloques[j];
        if (b >= 0 && b < totalBloques) counts[b] += 1;
      }
    }

    if (usarBusquedaLocal) {
      // Búsqueda local: mejorar ventanas del estudiante (sin generar choques nuevos)
      const cursosShuffle = [...cursosOrdenados];
      _shuffleInPlace_(cursosShuffle);
      let mejora = true;
      while (mejora) {
        mejora = false;
        for (let i = 0; i < cursosShuffle.length; i++) {
          const curso = cursosShuffle[i];
          const idActual = asignacionPorCurso[curso];
          if (!idActual) continue;

          const vActual = _calcularVentana(_bloquesDesdeConteos_(counts), ventanaIdeal);
          const bloquesActuales = bloquesPorParalelo[idActual] || [];

          // Quitar bloques del paralelo actual
          for (let j = 0; j < bloquesActuales.length; j++) {
            const b = bloquesActuales[j];
            if (b >= 0 && b < totalBloques) counts[b] -= 1;
          }

          const candidatos = cursoParalelos[curso] || [];
          let aceptado = false;
          for (let k = 0; k < candidatos.length; k++) {
            const idNuevo = candidatos[k];
            if (idNuevo === idActual) continue;
            const bloquesNuevos = bloquesPorParalelo[idNuevo] || [];

            // No permitir choques con el resto
            let choca = false;
            for (let j = 0; j < bloquesNuevos.length; j++) {
              const b = bloquesNuevos[j];
              if (b >= 0 && b < totalBloques && counts[b] > 0) {
                choca = true;
                break;
              }
            }
            if (choca) continue;

            // Probar
            for (let j = 0; j < bloquesNuevos.length; j++) {
              const b = bloquesNuevos[j];
              if (b >= 0 && b < totalBloques) counts[b] += 1;
            }

            const vNueva = _calcularVentana(_bloquesDesdeConteos_(counts), ventanaIdeal);
            if (vNueva < vActual) {
              // Confirmar
              asignacionPorCurso[curso] = idNuevo;
              ocupacionActual[idActual] = (ocupacionActual[idActual] || 0) - 1;
              ocupacionActual[idNuevo] = (ocupacionActual[idNuevo] || 0) + 1;
              mejora = true;
              aceptado = true;
              break;
            }

            // Deshacer
            for (let j = 0; j < bloquesNuevos.length; j++) {
              const b = bloquesNuevos[j];
              if (b >= 0 && b < totalBloques) counts[b] -= 1;
            }
          }

          if (!aceptado) {
            // Restaurar original
            for (let j = 0; j < bloquesActuales.length; j++) {
              const b = bloquesActuales[j];
              if (b >= 0 && b < totalBloques) counts[b] += 1;
            }
          }
        }
      }
    }

    // Reconstruir paralelos y bloques finales del estudiante
    const paralelosFinal = [];
    for (let i = 0; i < cursosOrdenados.length; i++) {
      const curso = cursosOrdenados[i];
      const idPar = asignacionPorCurso[curso];
      if (idPar) paralelosFinal.push(idPar);
    }

    paralelosPorEstudiante[idxE] = paralelosFinal;
    bloquesPorEstudiante[idxE] = _bloquesDesdeConteos_(counts);
  }

  return { paralelosPorEstudiante, bloquesPorEstudiante };
}

/**
 * Función Principal: Evalúa la Función Objetivo del modelo.
 */
function evaluarFuncionObjetivo() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 0. Configuración desde "Evaluación de FO" (columna I)
  const hasUIOverride = !!_getUIConfigOverride_();
  const config = _leerConfigEvaluacion_(ss);
  // Si la configuración viene desde la UI, no escribimos plantilla en la hoja.
  if (!hasUIOverride) {
    _asegurarPlantillaConfigEvaluacion_(ss, config);
  }
  const ALFA = config.alfa;
  const CV_IDEAL = config.cv_ideal;
  const VENTANA_IDEAL = config.ventana_ideal;
  const RESOLVER_SEGMENTACION = config.resolver_segmentacion;

  // 1. Carga de Datos (nombres de hojas configurables)
  const hojaMallas = ss.getSheetByName(config.hoja_malla);
  const hojaHorarios = ss.getSheetByName(config.hoja_horarios);
  const hojaMatriculas = ss.getSheetByName(config.hoja_matriculas);
  if (!hojaMallas) throw new Error(`No se encontró la hoja de malla: '${config.hoja_malla}' (config en Evaluación de FO!I7)`);
  if (!hojaHorarios) throw new Error(`No se encontró la hoja de horarios: '${config.hoja_horarios}' (config en Evaluación de FO!I8)`);
  if (!hojaMatriculas) throw new Error(`No se encontró la hoja de matrículas: '${config.hoja_matriculas}' (config en Evaluación de FO!I9)`);

  const datosMallas = hojaMallas.getDataRange().getValues();
  const datosHorarios = hojaHorarios.getDataRange().getValues();
  const datosEstudiantes = hojaMatriculas.getDataRange().getValues();

  const listaAsignaturas = [];
  const listaParalelos = [];
  const bloquesPorParalelo = {};
  const ocupacionActual = {};
  const asignaturasSet = {};

  // 2. Procesamiento de Mallas (Asignaturas y Paralelos)
  for (let i = 1; i < datosMallas.length; i++) {
    const curso = datosMallas[i][0];
    let asignaturaRegistrada = false;
    let numParalelo = 1;

    while (true) {
      const bloques = _obtenerBloquesDeParalelo(datosHorarios, curso, numParalelo);
      
      // Rompe el ciclo si ya no encuentra más paralelos para este curso
      if (bloques.length === 0) break;

      if (!asignaturaRegistrada) {
        listaAsignaturas.push(curso);
        asignaturasSet[curso] = true;
        asignaturaRegistrada = true;
      }

      // Formato: "CURSO-01"
      const idParalelo = `${curso}-${String(numParalelo).padStart(2, '0')}`;
      
      bloquesPorParalelo[idParalelo] = bloques;
      listaParalelos.push(idParalelo);
      ocupacionActual[idParalelo] = 0; // Inicializar contador de ocupación
      
      numParalelo++;
    }
  }

  const corridaOptimizada = _ejecutarCorridaEvaluacion_({
    listaAsignaturas,
    listaParalelos,
    bloquesPorParalelo,
    datosEstudiantes,
    ocupacionBase: ocupacionActual,
    ventanaIdeal: VENTANA_IDEAL,
    cvIdeal: CV_IDEAL,
    alfa: ALFA,
    resolverSegmentacion: RESOLVER_SEGMENTACION
  }, "optimizada");

  const corridaDfsPura = _ejecutarCorridaEvaluacion_({
    listaAsignaturas,
    listaParalelos,
    bloquesPorParalelo,
    datosEstudiantes,
    ocupacionBase: ocupacionActual,
    ventanaIdeal: VENTANA_IDEAL,
    cvIdeal: CV_IDEAL,
    alfa: ALFA,
    resolverSegmentacion: RESOLVER_SEGMENTACION
  }, "dfs_puro_sin_local");

  // 8. Escritura de resultados en la hoja "Evaluación de FO"
  const hojaSalida = ss.getSheetByName("Evaluación de FO");
  
  if (hojaSalida) {
    try {
      const fecha = new Date();
      const filasPrimerPanel = _escribirPanelAnaliticas(hojaSalida, fecha, corridaOptimizada.resultadoFinal, corridaOptimizada.detalle, {
        startRow: 1,
        titulo: "Panel Detalle (optimizada con búsqueda local)"
      });
      const margenEntrePaneles = 4;
      const filasSegundoPanel = _escribirPanelAnaliticas(hojaSalida, fecha, corridaDfsPura.resultadoFinal, corridaDfsPura.detalle, {
        startRow: 1 + filasPrimerPanel + margenEntrePaneles,
        titulo: "Panel Detalle (DFS puro sin búsqueda local)"
      });
      const margenComparativa = 2;
      _escribirComparativaTierDesbalance_(hojaSalida, 1 + filasPrimerPanel + margenEntrePaneles + filasSegundoPanel + margenComparativa, corridaOptimizada.detalle, corridaDfsPura.detalle);
    } catch (e) {
      console.error("Error al calcular/escribir analíticas adicionales:", e);
    }
    
  } else {
    console.error("No se encontró la hoja 'Evaluación de FO'. Los resultados no se guardaron.");
  }

  return corridaOptimizada.resultadoFinal;
}

function _escribirComparativaTierDesbalance_(hojaSalida, startRow, detalleOpt, detalleDfs) {
  const startCol = 1;
  const maxCols = 7;
  const maxRows = 260;

  hojaSalida.getRange(startRow, startCol, maxRows, maxCols).clearContent();

  const rows = [];
  const pushRow = (cols) => {
    const r = new Array(maxCols).fill("");
    for (let i = 0; i < Math.min(cols.length, maxCols); i++) r[i] = cols[i];
    rows.push(r);
  };

  const mapOpt = {};
  const mapDfs = {};
  const tierOpt = (detalleOpt && detalleOpt.tier_desbalance) ? detalleOpt.tier_desbalance : [];
  const tierDfs = (detalleDfs && detalleDfs.tier_desbalance) ? detalleDfs.tier_desbalance : [];

  for (let i = 0; i < tierOpt.length; i++) mapOpt[tierOpt[i].asignatura] = tierOpt[i];
  for (let i = 0; i < tierDfs.length; i++) mapDfs[tierDfs[i].asignatura] = tierDfs[i];

  const asignaturas = Array.from(new Set(Object.keys(mapOpt).concat(Object.keys(mapDfs)))).sort((a, b) => String(a).localeCompare(String(b)));

  pushRow(["Comparativa Tierlist Desbalance", "", "", "", "", "", ""]);
  pushRow(["Asignatura", "#Par", "Total", "CV (optimizada)", "ocupación (optimizada)", "CV (solo DFS)", "ocupación (solo DFS)"]);

  for (let i = 0; i < asignaturas.length; i++) {
    const asignatura = asignaturas[i];
    const o = mapOpt[asignatura] || {};
    const d = mapDfs[asignatura] || {};
    pushRow([
      asignatura,
      o.num_paralelos != null ? o.num_paralelos : (d.num_paralelos != null ? d.num_paralelos : ""),
      o.total_inscritos != null ? o.total_inscritos : (d.total_inscritos != null ? d.total_inscritos : ""),
      o.cv != null ? _round(o.cv, 3) : "",
      o.detalle_paralelos || "",
      d.cv != null ? _round(d.cv, 3) : "",
      d.detalle_paralelos || ""
    ]);
  }

  const writeRows = Math.min(rows.length, maxRows);
  const data = rows.slice(0, writeRows);
  hojaSalida.getRange(startRow, startCol, data.length, maxCols).setValues(data);
  return data.length;
}

function _ejecutarCorridaEvaluacion_(ctx, modoSegmentacion) {
  const {
    listaAsignaturas,
    listaParalelos,
    bloquesPorParalelo,
    datosEstudiantes,
    ocupacionBase,
    ventanaIdeal,
    cvIdeal,
    alfa,
    resolverSegmentacion
  } = ctx;

  const ocupacionActual = {};
  for (let i = 0; i < listaParalelos.length; i++) {
    ocupacionActual[listaParalelos[i]] = (ocupacionBase && Number.isFinite(Number(ocupacionBase[listaParalelos[i]]))) ? Number(ocupacionBase[listaParalelos[i]]) : 0;
  }

  let paralelosPorEstudiante;
  let bloquesPorEstudiante;
  if (resolverSegmentacion === 1) {
    const asignaturasPorEstudiante = [];
    const asignaturasSet = {};
    for (let i = 0; i < listaAsignaturas.length; i++) asignaturasSet[listaAsignaturas[i]] = true;
    for (let i = 1; i < datosEstudiantes.length; i++) {
      const materiasInscritas = String(datosEstudiantes[i][1] || "").split(",");
      const cursosSet = {};
      for (let j = 0; j < materiasInscritas.length; j++) {
        const curso = _normalizarMateriaACurso_(materiasInscritas[j]);
        if (!curso) continue;
        if (asignaturasSet[curso]) cursosSet[curso] = true;
      }
      asignaturasPorEstudiante.push(Object.keys(cursosSet));
    }

    const cursoParalelos = _buildCursoParalelosMap_(listaParalelos);
    const seg = _resolverSegmentacionEstudiantes_(
      asignaturasPorEstudiante,
      cursoParalelos,
      bloquesPorParalelo,
      ocupacionActual,
      ventanaIdeal,
      {
        usarBusquedaLocal: modoSegmentacion !== "dfs_puro_sin_local",
        pararEnPrimeraFactible: false
      }
    );
    paralelosPorEstudiante = seg.paralelosPorEstudiante;
    bloquesPorEstudiante = seg.bloquesPorEstudiante;
  } else {
    paralelosPorEstudiante = _buildParalelosDesdeMatricula_(datosEstudiantes, listaParalelos);
    bloquesPorEstudiante = _buildBloquesYOcupacionDesdeParalelos_(paralelosPorEstudiante, bloquesPorParalelo, ocupacionActual);
  }

  let sumaDesviacionesReales = 0;
  let sumaDesviacionesIdeales = 0;
  for (let asignatura of listaAsignaturas) {
    const paralelosDeAsignatura = listaParalelos.filter(p => p.startsWith(`${asignatura}-`));
    const numP = paralelosDeAsignatura.length;
    if (numP > 1) {
      const inscritos = paralelosDeAsignatura.map(p => ocupacionActual[p]);
      const totalInscritos = inscritos.reduce((a, b) => a + b, 0);
      const media = totalInscritos / numP;
      const varianza = inscritos.reduce((acc, val) => acc + Math.pow(val - media, 2), 0) / numP;
      const sigmaReal = Math.sqrt(varianza);
      sumaDesviacionesReales += sigmaReal;
      sumaDesviacionesIdeales += (media * cvIdeal);
    }
  }

  const desbalanceReal = sumaDesviacionesReales / listaAsignaturas.length;
  const desbalanceIdeal = sumaDesviacionesIdeales / listaAsignaturas.length;

  let ventanaTotalReal = 0;
  let estudiantesConCarga = 0;
  let totalChoques = 0;
  for (let bloques of bloquesPorEstudiante) {
    ventanaTotalReal += _calcularVentana(bloques, ventanaIdeal);
    if (bloques.length > 0) estudiantesConCarga += 1;
    const bloquesUnicos = new Set(bloques);
    totalChoques += (bloques.length - bloquesUnicos.size);
  }

  const ventanaTotalIdeal = estudiantesConCarga * ventanaIdeal;
  const ratioDesbalance = Math.pow((desbalanceReal / Math.max(desbalanceIdeal, 1e-6)), alfa);
  const ratioVentana = ventanaTotalReal / Math.max(ventanaTotalIdeal, 1e-6);
  const resultadoFinal = {
    ratio_desbalance: ratioDesbalance,
    ratio_ventana: ratioVentana,
    fo_total: ratioDesbalance * ratioVentana,
    choques: totalChoques
  };

  const detalle = _calcularAnaliticasAdicionales({
    listaAsignaturas,
    listaParalelos,
    ocupacionActual,
    paralelosPorEstudiante,
    bloquesPorParalelo,
    ventanaIdeal
  });

  return { resultadoFinal, detalle };
}

/**
 * Calcula métricas adicionales para análisis y toma de decisiones.
 * Nota: algunas atribuciones (p.ej. ventanas por curso) son estimaciones,
 * porque las ventanas se generan por la combinación de cursos en el horario.
 */
function _calcularAnaliticasAdicionales(ctx) {
  const {
    listaAsignaturas,
    listaParalelos,
    ocupacionActual,
    paralelosPorEstudiante,
    bloquesPorParalelo,
    ventanaIdeal
  } = ctx;

  const ventanasPorParalelo = {};
  const ventanasPorAsignatura = {};
  const choquesGruposPorParalelo = {};
  const choquesDuplicadosPorParalelo = {};
  const choquesGruposPorAsignatura = {};
  const choquesDuplicadosPorAsignatura = {};

  const histVentanasRaw = {};
  const histVentanasPenalizadas = {};
  const histChoquesDuplicados = {};
  const histChoquesGrupos = {};

  const choquesParesParaleloCounts = {};
  const choquesParesParaleloBloques = {}; // pairKey -> { "Lu 5 - 6": n, ... }
  const choquesParesAsignaturaCounts = {};
  const choquesParesAsignaturaBloques = {};

  // Denominadores para porcentajes
  const alumnosPorParalelo = {};
  const alumnosPorAsignatura = {};
  const alumnosCompartenParaleloPair = {};
  const alumnosCompartenAsignaturaPair = {};
  const alumnosAfectadosParaleloPair = {};
  const alumnosAfectadosAsignaturaPair = {};

  let totalVentanasRaw = 0;
  let totalVentanasPenalizadas = 0;
  let totalChoquesDuplicados = 0;
  let totalChoquesGrupos = 0;
  let estudiantesConCarga = 0;

  for (let i = 0; i < paralelosPorEstudiante.length; i++) {
    const paralelos = paralelosPorEstudiante[i] || [];
    if (paralelos.length === 0) continue;
    estudiantesConCarga += 1;

    // Sets para denominadores por alumno
    const setPar = Array.from(new Set(paralelos));
    const setCur = Array.from(new Set(setPar.map(p => _cursoDesdeParalelo(p)).filter(Boolean)));

    for (let a = 0; a < setPar.length; a++) alumnosPorParalelo[setPar[a]] = (alumnosPorParalelo[setPar[a]] || 0) + 1;
    for (let a = 0; a < setCur.length; a++) alumnosPorAsignatura[setCur[a]] = (alumnosPorAsignatura[setCur[a]] || 0) + 1;

    for (let a = 0; a < setPar.length; a++) {
      for (let b = a + 1; b < setPar.length; b++) {
        const k = _pairKey_(setPar[a], setPar[b]);
        alumnosCompartenParaleloPair[k] = (alumnosCompartenParaleloPair[k] || 0) + 1;
      }
    }
    for (let a = 0; a < setCur.length; a++) {
      for (let b = a + 1; b < setCur.length; b++) {
        const k = _pairKey_(setCur[a], setCur[b]);
        alumnosCompartenAsignaturaPair[k] = (alumnosCompartenAsignaturaPair[k] || 0) + 1;
      }
    }

    const met = _calcularMetricasEstudianteDetalladas(paralelos, bloquesPorParalelo, ventanaIdeal);

    totalVentanasRaw += met.ventanas_raw;
    totalVentanasPenalizadas += met.ventanas_penalizadas;
    totalChoquesDuplicados += met.choques_duplicados;
    totalChoquesGrupos += met.choques_grupos;

    histVentanasRaw[met.ventanas_raw] = (histVentanasRaw[met.ventanas_raw] || 0) + 1;
    histVentanasPenalizadas[met.ventanas_penalizadas] = (histVentanasPenalizadas[met.ventanas_penalizadas] || 0) + 1;
    histChoquesDuplicados[met.choques_duplicados] = (histChoquesDuplicados[met.choques_duplicados] || 0) + 1;
    histChoquesGrupos[met.choques_grupos] = (histChoquesGrupos[met.choques_grupos] || 0) + 1;

    // Acumular atribuciones estimadas
    _acumularMapaNumerico(ventanasPorParalelo, met.ventanas_por_paralelo);
    _acumularMapaNumerico(choquesGruposPorParalelo, met.choques_grupos_por_paralelo);
    _acumularMapaNumerico(choquesDuplicadosPorParalelo, met.choques_duplicados_por_paralelo);

    // Acumular choques directos por par (paralelo/asignatura) con bloque
    _acumularMapaNumerico(choquesParesParaleloCounts, met.choques_pares_paralelo_counts);
    _acumularMapaDeMapasNumericos_(choquesParesParaleloBloques, met.choques_pares_paralelo_bloques);
    _acumularMapaNumerico(choquesParesAsignaturaCounts, met.choques_pares_asignatura_counts);
    _acumularMapaDeMapasNumericos_(choquesParesAsignaturaBloques, met.choques_pares_asignatura_bloques);

    // Alumnos afectados (por par) = conteo por alumno (0/1) acumulado
    _acumularMapaNumerico(alumnosAfectadosParaleloPair, met.choques_pares_paralelo_alumnos);
    _acumularMapaNumerico(alumnosAfectadosAsignaturaPair, met.choques_pares_asignatura_alumnos);
  }

  // Agregar por asignatura (sigla), a partir de paralelo "CURSO-01"
  for (const paralelo in ventanasPorParalelo) {
    const curso = _cursoDesdeParalelo(paralelo);
    ventanasPorAsignatura[curso] = (ventanasPorAsignatura[curso] || 0) + ventanasPorParalelo[paralelo];
  }
  for (const paralelo in choquesGruposPorParalelo) {
    const curso = _cursoDesdeParalelo(paralelo);
    choquesGruposPorAsignatura[curso] = (choquesGruposPorAsignatura[curso] || 0) + choquesGruposPorParalelo[paralelo];
  }
  for (const paralelo in choquesDuplicadosPorParalelo) {
    const curso = _cursoDesdeParalelo(paralelo);
    choquesDuplicadosPorAsignatura[curso] = (choquesDuplicadosPorAsignatura[curso] || 0) + choquesDuplicadosPorParalelo[paralelo];
  }

  // Tierlist desbalance: por asignatura, mostrando alumnos por paralelo
  const tierDesbalance = [];
  for (let idx = 0; idx < listaAsignaturas.length; idx++) {
    const asignatura = listaAsignaturas[idx];
    const paralelosDeAsignatura = listaParalelos.filter(p => p.startsWith(`${asignatura}-`));
    const numP = paralelosDeAsignatura.length;
    if (numP <= 1) continue;

    const inscritos = paralelosDeAsignatura.map(p => ocupacionActual[p] || 0);
    const totalInscritos = inscritos.reduce((a, b) => a + b, 0);
    const media = totalInscritos / Math.max(numP, 1);
    const varianza = inscritos.reduce((acc, val) => acc + Math.pow(val - media, 2), 0) / Math.max(numP, 1);
    const sigma = Math.sqrt(varianza);
    const cv = sigma / Math.max(media, 1e-6);

    const detalleParalelos = paralelosDeAsignatura
      .map((p, j) => `${p}:${inscritos[j]}`)
      .join(", ");

    tierDesbalance.push({
      asignatura,
      num_paralelos: numP,
      total_inscritos: totalInscritos,
      media,
      sigma,
      cv,
      detalle_paralelos: detalleParalelos
    });
  }
  tierDesbalance.sort((a, b) => b.cv - a.cv);

  // Rankings (Top) por asignatura
  const rankingVentanasAsignatura = _topFromMap(ventanasPorAsignatura, 15);
  const rankingChoquesAsignatura = _topFromMap(choquesDuplicadosPorAsignatura, 15);
  const rankingVentanasParalelo = _topFromMap(ventanasPorParalelo, 15);
  const rankingChoquesParalelo = _topFromMap(choquesDuplicadosPorParalelo, 15);
  const rankingChoquesParesParalelo = _topPairsWithRates_({
    occMap: choquesParesParaleloCounts,
    blocksByPair: choquesParesParaleloBloques,
    sharedStudentsByPair: alumnosCompartenParaleloPair,
    impactedStudentsByPair: alumnosAfectadosParaleloPair,
    studentsByA: alumnosPorParalelo,
    topN: 20,
    sortByRate: false
  });
  const rankingChoquesParesAsignatura = _topPairsWithRates_({
    occMap: choquesParesAsignaturaCounts,
    blocksByPair: choquesParesAsignaturaBloques,
    sharedStudentsByPair: alumnosCompartenAsignaturaPair,
    impactedStudentsByPair: alumnosAfectadosAsignaturaPair,
    studentsByA: alumnosPorAsignatura,
    topN: 20,
    sortByRate: false
  });


  return {
    estudiantes_con_carga: estudiantesConCarga,
    matricula: {
      asignaturas: alumnosPorAsignatura,
      paralelos: alumnosPorParalelo
    },
    totales: {
      ventanas_raw: totalVentanasRaw,
      ventanas_penalizadas: totalVentanasPenalizadas,
      choques_duplicados: totalChoquesDuplicados,
      choques_grupos: totalChoquesGrupos
    },
    distribuciones: {
      ventanas_raw: histVentanasRaw,
      ventanas_penalizadas: histVentanasPenalizadas,
      choques_duplicados: histChoquesDuplicados,
      choques_grupos: histChoquesGrupos
    },
    rankings: {
      ventanas_asignatura: rankingVentanasAsignatura,
      choques_asignatura: rankingChoquesAsignatura,
      ventanas_paralelo: rankingVentanasParalelo,
      choques_paralelo: rankingChoquesParalelo,
      choques_pares_paralelo: rankingChoquesParesParalelo,
      choques_pares_asignatura: rankingChoquesParesAsignatura
    },
    tier_desbalance: tierDesbalance
  };
}

/**
 * Calcula métricas de un estudiante a partir de sus paralelos:
 * - Ventanas raw (gaps + almuerzo), y penalización (misma regla que _calcularVentana)
 * - Choques duplicados (como en el cálculo original) y choques por grupos (slots con colisión)
 * - Atribuciones estimadas de ventanas/choques por paralelo
 */
function _calcularMetricasEstudianteDetalladas(paralelos, bloquesPorParalelo, ventanaIdeal) {
  const umbralVentana = (Number.isFinite(Number(ventanaIdeal)) && Number(ventanaIdeal) > 0)
    ? Number(ventanaIdeal)
    : 4;
  // Recolectar eventos (paralelo, idBloque)
  const eventos = [];
  for (let i = 0; i < paralelos.length; i++) {
    const paralelo = paralelos[i];
    const bloques = bloquesPorParalelo[paralelo];
    if (!bloques || bloques.length === 0) continue;
    // Seguridad extra: si por algún motivo el paralelo trae IDs repetidos
    // (ej. 2 salas en el mismo bloque), colapsarlos para que no cuente como choque.
    const vistosBloques = new Set();
    for (let j = 0; j < bloques.length; j++) {
      const id = bloques[j];
      if (vistosBloques.has(id)) continue;
      vistosBloques.add(id);
      eventos.push({ paralelo, id });
    }
  }
  if (eventos.length === 0) {
    return {
      ventanas_raw: 0,
      ventanas_penalizadas: 0,
      choques_duplicados: 0,
      choques_grupos: 0,
      ventanas_por_paralelo: {},
      choques_grupos_por_paralelo: {},
      choques_duplicados_por_paralelo: {}
    };
  }

  // Agrupar por día y bloque dentro del día
  const eventosPorDia = { 0: {}, 1: {}, 2: {}, 3: {}, 4: {} }; // day -> blockIdx -> [paralelos]
  for (let e of eventos) {
    const dia = Math.floor(e.id / BLOQUES_POR_DIA);
    const idx = e.id % BLOQUES_POR_DIA;
    if (eventosPorDia[dia]) {
      if (!eventosPorDia[dia][idx]) eventosPorDia[dia][idx] = [];
      eventosPorDia[dia][idx].push(e.paralelo);
    }
  }

  let ventanasRaw = 0;
  let choquesDuplicados = 0;
  let choquesGrupos = 0;
  const ventanasPorParalelo = {};
  const choquesGruposPorParalelo = {};
  const choquesDuplicadosPorParalelo = {};

  const choquesParesParaleloCounts = {};
  const choquesParesParaleloBloques = {}; // pairKey -> { "Lu 5 - 6": n, ... }
  const choquesParesAsignaturaCounts = {};
  const choquesParesAsignaturaBloques = {};
  const choquesParesParaleloAlumnos = {};
  const choquesParesAsignaturaAlumnos = {};

  for (let d = 0; d < TOTAL_DIAS; d++) {
    const mapaIdx = eventosPorDia[d];
    const indices = Object.keys(mapaIdx).map(n => parseInt(n, 10)).sort((a, b) => a - b);
    if (indices.length === 0) continue;

    // Choques por bloque
    for (const idx of indices) {
      // Ignorar repeticiones del MISMO paralelo en el mismo bloque (doble sala)
      const ps = Array.from(new Set(mapaIdx[idx] || []));
      if (ps.length > 1) {
        const bloqueLabel = `${DIAS_TEXTO[d]} ${BLOQUES_TEXTO[idx]}`;

        choquesGrupos += 1;
        choquesDuplicados += (ps.length - 1);
        const shareDup = (ps.length - 1) / ps.length;
        for (const p of ps) {
          choquesGruposPorParalelo[p] = (choquesGruposPorParalelo[p] || 0) + 1;
          choquesDuplicadosPorParalelo[p] = (choquesDuplicadosPorParalelo[p] || 0) + shareDup;
        }

        // Registrar choques directos por par (todas las combinaciones)
        for (let i = 0; i < ps.length; i++) {
          for (let j = i + 1; j < ps.length; j++) {
            const p1 = ps[i];
            const p2 = ps[j];

            const keyP = _pairKey_(p1, p2);
            choquesParesParaleloCounts[keyP] = (choquesParesParaleloCounts[keyP] || 0) + 1;
            if (!choquesParesParaleloBloques[keyP]) choquesParesParaleloBloques[keyP] = {};
            choquesParesParaleloBloques[keyP][bloqueLabel] = (choquesParesParaleloBloques[keyP][bloqueLabel] || 0) + 1;
            choquesParesParaleloAlumnos[keyP] = 1;

            const a1 = _cursoDesdeParalelo(p1);
            const a2 = _cursoDesdeParalelo(p2);
            if (a1 && a2 && a1 !== a2) {
              const keyA = _pairKey_(a1, a2);
              choquesParesAsignaturaCounts[keyA] = (choquesParesAsignaturaCounts[keyA] || 0) + 1;
              if (!choquesParesAsignaturaBloques[keyA]) choquesParesAsignaturaBloques[keyA] = {};
              choquesParesAsignaturaBloques[keyA][bloqueLabel] = (choquesParesAsignaturaBloques[keyA][bloqueLabel] || 0) + 1;
              choquesParesAsignaturaAlumnos[keyA] = 1;
            }
          }
        }
      }
    }

    // Ventanas (gaps) entre bloques ocupados (por índice)
    for (let i = 0; i < indices.length - 1; i++) {
      const a = indices[i];
      const b = indices[i + 1];
      const gap = (b - a - 1);
      if (gap > 0) {
        ventanasRaw += gap;
        const paralelosEnA = mapaIdx[a] || [];
        for (const p of paralelosEnA) {
          ventanasPorParalelo[p] = (ventanasPorParalelo[p] || 0) + gap;
        }
      }
    }

    // Regla almuerzo (misma que _calcularVentana)
    const minIdx = indices[0];
    const maxIdx = indices[indices.length - 1];
    if (minIdx <= 3 && maxIdx >= 4) {
      ventanasRaw += 1;
      // Atribución estimada: al/los cursos del último bloque en la mañana
      const morningIdxs = indices.filter(x => x <= 3);
      const lastMorningIdx = morningIdxs.length ? morningIdxs[morningIdxs.length - 1] : minIdx;
      const paralelosLM = mapaIdx[lastMorningIdx] || [];
      for (const p of paralelosLM) {
        ventanasPorParalelo[p] = (ventanasPorParalelo[p] || 0) + 1;
      }
    }
  }

  // Penalización (umbral = ventana ideal y luego cuadrática)
  const ventanasPenalizadas = (ventanasRaw > umbralVentana)
    ? umbralVentana + Math.pow((ventanasRaw - umbralVentana), 2)
    : ventanasRaw;

  return {
    ventanas_raw: ventanasRaw,
    ventanas_penalizadas: ventanasPenalizadas,
    choques_duplicados: choquesDuplicados,
    choques_grupos: choquesGrupos,
    ventanas_por_paralelo: ventanasPorParalelo,
    choques_grupos_por_paralelo: choquesGruposPorParalelo,
    choques_duplicados_por_paralelo: choquesDuplicadosPorParalelo,
    choques_pares_paralelo_counts: choquesParesParaleloCounts,
    choques_pares_paralelo_bloques: choquesParesParaleloBloques,
    choques_pares_asignatura_counts: choquesParesAsignaturaCounts,
    choques_pares_asignatura_bloques: choquesParesAsignaturaBloques,
    choques_pares_paralelo_alumnos: choquesParesParaleloAlumnos,
    choques_pares_asignatura_alumnos: choquesParesAsignaturaAlumnos
  };
}

function _acumularMapaNumerico(target, source) {
  if (!source) return;
  for (const k in source) {
    target[k] = (target[k] || 0) + (source[k] || 0);
  }
}

function _cursoDesdeParalelo(idParalelo) {
  // Formato esperado: "CURSO-01" (dos dígitos)
  if (!idParalelo) return "";
  return idParalelo.slice(0, -3);
}

function _topFromMap(mapObj, topN) {
  const arr = Object.keys(mapObj || {}).map(k => ({ key: k, value: mapObj[k] }));
  arr.sort((a, b) => (b.value || 0) - (a.value || 0));
  return arr.slice(0, topN);
}

/**
 * Escribe un panel de analíticas en la hoja de salida (a partir de la columna A).
 * Se sobrescribe en cada ejecución para que sirva como "dashboard" del último cálculo.
 */
function _escribirPanelAnaliticas(hojaSalida, fecha, resultadoFinal, detalle, opciones) {
  const startRow = (opciones && Number.isFinite(Number(opciones.startRow))) ? Number(opciones.startRow) : 1;
  const startCol = 1; // Columna A
  const maxRows = (opciones && Number.isFinite(Number(opciones.maxRows))) ? Number(opciones.maxRows) : 260;
  const maxCols = 7; // A-G (no tocar H:I donde van los parámetros)
  const titulo = (opciones && opciones.titulo) ? String(opciones.titulo) : "Panel Detalle (última ejecución)";

  // Limpiar panel anterior (solo el área del panel)
  hojaSalida.getRange(startRow, startCol, maxRows, maxCols).clearContent();

  const rows = [];
  const pushRow = (cols) => {
    const r = new Array(maxCols).fill("");
    for (let i = 0; i < Math.min(cols.length, maxCols); i++) r[i] = cols[i];
    rows.push(r);
  };

  pushRow([titulo, "", "", "", "", "", "", ""]); 
  pushRow(["Fecha", fecha, "FO", resultadoFinal.fo_total, "Choques", resultadoFinal.choques, "", ""]);
  pushRow(["Ratio Desbalance", resultadoFinal.ratio_desbalance, "Ratio Ventana", resultadoFinal.ratio_ventana, "", "", "", ""]);
  pushRow(["Estudiantes con carga", detalle.estudiantes_con_carga, "Ventanas (raw) total", detalle.totales.ventanas_raw, "Choques (dup) total", detalle.totales.choques_duplicados, "", ""]);
  pushRow(["", "", "", "", "", "", "", ""]);

  // Distribuciones
  const totalEstudiantesConCarga = Number(detalle.estudiantes_con_carga) || 0;
  pushRow(["Distribución Ventanas", "Estudiantes con esas ventanas", "Estudiantes (<=raw)", "% Estudiantes (<=raw)", "Distribución Choques (duplicados)", "Estudiantes", "%", ""]);

  const distVentBase = _mapToSortedPairs(detalle.distribuciones.ventanas_raw);
  let acumuladoVentanas = 0;
  const distVent = distVentBase.map((it) => {
    const raw = Number(it.v) || 0;
    acumuladoVentanas += raw;
    return {
      k: it.k,
      raw,
      acumulado: acumuladoVentanas,
      pct: _pct_(acumuladoVentanas, totalEstudiantesConCarga, 1)
    };
  });

  const distChoq = _mapToSortedPairs(detalle.distribuciones.choques_duplicados).map((it) => ({
    k: it.k,
    v: it.v,
    pct: _pct_(it.v, totalEstudiantesConCarga, 1)
  }));
  const maxDist = Math.max(distVent.length, distChoq.length);
  for (let i = 0; i < maxDist; i++) {
    const v = distVent[i] || { k: "", raw: "", acumulado: "", pct: "" };
    const c = distChoq[i] || { k: "", v: "", pct: "" };
    pushRow([v.k, v.raw, v.acumulado, v.pct || "", c.k, c.v, c.pct || ""]);
  }
  pushRow(["", "", "", "", "", "", ""]);

  // Matrícula por asignatura / paralelo
  pushRow(["Matrícula por asignatura", "Alumnos", "%", "", "Matrícula por paralelo", "Alumnos", "%"]);
  const matA = (detalle.matricula && detalle.matricula.asignaturas) ? detalle.matricula.asignaturas : {};
  const matP = (detalle.matricula && detalle.matricula.paralelos) ? detalle.matricula.paralelos : {};
  const listA = _mapToSortedPairsByValueDesc_(matA);
  const listP = _mapToSortedPairsByValueDesc_(matP);
  const maxMat = Math.max(listA.length, listP.length);
  for (let i = 0; i < Math.min(maxMat, 70); i++) {
    const a = listA[i] || { k: "", v: "" };
    const p = listP[i] || { k: "", v: "" };
    pushRow([a.k, a.v, _pct_(a.v, totalEstudiantesConCarga, 1), "", p.k, p.v, _pct_(p.v, totalEstudiantesConCarga, 1)]);
  }
  pushRow(["", "", "", "", "", "", ""]);

  // Choques directos (pares) con bloque + porcentajes
  pushRow(["Top pares de choque (paralelos)", "Ocurr", "Alum ambos (par)", "% afec/total izq", "% afec/total der", "Bloques", "", ""]);
  const topParesParalelo = (detalle.rankings && detalle.rankings.choques_pares_paralelo) ? detalle.rankings.choques_pares_paralelo : [];
  for (let i = 0; i < Math.min(topParesParalelo.length, 20); i++) {
    const t = topParesParalelo[i];
    const label = (t && t.a && t.b) ? `${t.a} vs ${t.b}` : "";
    pushRow([
      label,
      t.ocurrencias || "",
      t.alumnos_comparten || "",
      t.pct_afectados_sobre_total_a || "",
      t.pct_afectados_sobre_total_b || "",
      t.top_bloques || "",
      "",
      ""
    ]);
  }
  pushRow(["", "", "", "", "", "", "", ""]);

  pushRow(["Top pares de choque (asignaturas)", "Ocurr", "Alum ambos (asig)", "% afec/total izq", "% afec/total der", "Bloques", "", ""]);
  const topParesAsignatura = (detalle.rankings && detalle.rankings.choques_pares_asignatura) ? detalle.rankings.choques_pares_asignatura : [];
  for (let i = 0; i < Math.min(topParesAsignatura.length, 20); i++) {
    const t = topParesAsignatura[i];
    const label = (t && t.a && t.b) ? `${t.a} vs ${t.b}` : "";
    pushRow([
      label,
      t.ocurrencias || "",
      t.alumnos_comparten || "",
      t.pct_afectados_sobre_total_a || "",
      t.pct_afectados_sobre_total_b || "",
      t.top_bloques || "",
      "",
      ""
    ]);
  }
  pushRow(["", "", "", "", "", "", "", ""]);

  // Rankings por asignatura
  pushRow(["Top asignaturas por ventanas (estimado)", "Ventanas", "", "", "Top asignaturas por choques (dup)", "Choques", "", ""]);
  const topVentA = detalle.rankings.ventanas_asignatura || [];
  const topChoqA = detalle.rankings.choques_asignatura || [];
  const maxTopA = Math.max(topVentA.length, topChoqA.length);
  for (let i = 0; i < maxTopA; i++) {
    const tv = topVentA[i] || { key: "", value: "" };
    const tc = topChoqA[i] || { key: "", value: "" };
    pushRow([tv.key, tv.value, "", "", tc.key, tc.value, "", ""]);
  }
  pushRow(["", "", "", "", "", "", "", ""]);

  // Rankings por paralelo
  pushRow(["Top paralelos por ventanas (estimado)", "Ventanas", "", "", "Top paralelos por choques (dup)", "Choques", "", ""]);
  const topVentP = detalle.rankings.ventanas_paralelo || [];
  const topChoqP = detalle.rankings.choques_paralelo || [];
  const maxTopP = Math.max(topVentP.length, topChoqP.length);
  for (let i = 0; i < maxTopP; i++) {
    const tv = topVentP[i] || { key: "", value: "" };
    const tc = topChoqP[i] || { key: "", value: "" };
    pushRow([tv.key, tv.value, "", "", tc.key, tc.value, "", ""]);
  }
  pushRow(["", "", "", "", "", "", "", ""]);

  // Tierlist desbalance
  pushRow(["Tierlist desbalance (CV desc)", "#Par", "Total", "Media", "Sigma", "CV", "Paralelos (ocupación)", ""]);
  const tier = detalle.tier_desbalance || [];
  for (let i = 0; i < Math.min(tier.length, 60); i++) {
    const t = tier[i];
    pushRow([
      t.asignatura,
      t.num_paralelos,
      t.total_inscritos,
      _round(t.media, 2),
      _round(t.sigma, 2),
      _round(t.cv, 3),
      t.detalle_paralelos,
      ""
    ]);
  }

  const writeRows = Math.min(rows.length, maxRows);
  const data = rows.slice(0, writeRows);
  hojaSalida.getRange(startRow, startCol, data.length, maxCols).setValues(data);
  return data.length;
}

function _mapToSortedPairs(mapObj) {
  const raw = Object.keys(mapObj || {}).map((key) => {
    const maybeNum = _tryParseNumber(key);
    return {
      sortKey: (typeof maybeNum === "number") ? maybeNum : null,
      displayKey: (typeof maybeNum === "number") ? String(maybeNum) : String(key),
      v: mapObj[key]
    };
  });

  raw.sort((a, b) => {
    if (a.sortKey != null && b.sortKey != null) return a.sortKey - b.sortKey;
    if (a.sortKey != null) return -1;
    if (b.sortKey != null) return 1;
    return a.displayKey.localeCompare(b.displayKey);
  });

  return raw.map(x => ({ k: x.displayKey, v: x.v }));
}

function _mapToCumulativePairsWithPct_(mapObj, total, decimals) {
  const pairs = _mapToSortedPairs(mapObj);
  let acumulado = 0;
  return pairs.map((it) => {
    acumulado += Number(it.v) || 0;
    return {
      k: it.k,
      v: acumulado,
      pct: _pct_(acumulado, total, decimals)
    };
  });
}

function _mapToSortedPairsByValueDesc_(mapObj) {
  const arr = Object.keys(mapObj || {}).map((k) => ({ k, v: mapObj[k] }));
  arr.sort((a, b) => {
    const dv = (b.v || 0) - (a.v || 0);
    if (dv !== 0) return dv;
    return String(a.k).localeCompare(String(b.k));
  });
  return arr;
}

function _tryParseNumber(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : x;
}

function _round(n, decimals) {
  const d = Math.pow(10, decimals || 0);
  return Math.round((Number(n) || 0) * d) / d;
}