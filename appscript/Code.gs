function onOpenPlanificacionDocente_(e) {
  SpreadsheetApp.getUi()
    .createMenu('Planificación docente')
    .addItem('Cargar horario (JSON) desde PC…', 'showJsonUploadDialog')
    .addToUi();
}

function showJsonUploadDialog() {
  const html = HtmlService.createHtmlOutputFromFile('Upload')
    .setWidth(520)
    .setHeight(420);
  SpreadsheetApp.getUi().showModalDialog(html, 'Cargar JSON');
}

function writeAsignaturasFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');
    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    writeAsignaturasSheet_(ss, baseName, data);
  });

  return { ok: true, count: files.length };
}

function writeProfesoresFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');
    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    writeProfesoresSheet_(ss, baseName, data);
  });

  return { ok: true, count: files.length };
}

function writeAlumnosFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');
    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    writeAlumnosSheet_(ss, baseName, data);
  });

  return { ok: true, count: files.length };
}

function writeAvailabilityFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');

    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    const sheetName = sanitizeSheetName(`${baseName}-DisponibilidadDocente`);
    let sheet = ss.getSheetByName(sheetName);
    if (sheet) ss.deleteSheet(sheet);
    sheet = ss.insertSheet(sheetName);

    const bloques = safeArray_(data?.tiempos?.bloques).length ? data.tiempos.bloques : ['1-2','3-4','5-6','7-8','9-10','11-12','13-14'];
    const dias = safeArray_(data?.tiempos?.dias).length ? data.tiempos.dias : ['Lu','Ma','Mi','Ju','Vi'];

    const dayLabels = {
      Lu: 'Lunes',
      Ma: 'Martes',
      Mi: 'Miércoles',
      Ju: 'Jueves',
      Vi: 'Viernes'
    };

    const maestros = safeArray_(data?.recursos?.maestros);

    const BLUE = '#93C5FD'; // disponible
    const RED  = '#FCA5A5'; // no disponible

    let row = 1;

    maestros.forEach((m) => {
      const nombre = String(m?.nombre || '').trim() || '(Sin nombre)';

      // Fila 1 del bloque del profe
      sheet.getRange(row, 1).setValue('Profesor:').setFontWeight('bold');
      sheet.getRange(row, 2).setValue(nombre);
      sheet.getRange(row, 1, 1, 2).setBackground('#F9FAFB');

      // Header tabla (fila row+1)
      const headerRow = row + 1;
      sheet.getRange(headerRow, 1).setValue('Bloque').setFontWeight('bold');

      // Días como headers desde col 2
      dias.forEach((d, i) => {
        sheet.getRange(headerRow, 2 + i).setValue(dayLabels[d] || d).setFontWeight('bold');
      });

      // Normalizar disponibilidad a mapa día -> array 0/1 por bloque
      const dispMap = buildAvailabilityMap_(m?.disponibilidad, dias, bloques.length);

      // Evitar que claves como "7-8" se interpreten como fecha
      sheet.getRange(headerRow + 1, 1, bloques.length, 1).setNumberFormat('@');

      // Rellenar filas de bloques
      bloques.forEach((bloque, bIndex) => {
        const r = headerRow + 1 + bIndex;
        sheet.getRange(r, 1).setValue(bloque);

        dias.forEach((d, i) => {
          const v = Number(dispMap[d]?.[bIndex]) === 1 ? 1 : 0;
          const cell = sheet.getRange(r, 2 + i);
          cell.setValue(''); // por ahora solo color
          cell.setBackground(v === 1 ? BLUE : RED);
        });
      });

      // Ajustes visuales rápidos
      const tableRange = sheet.getRange(headerRow, 1, 1 + bloques.length, 1 + dias.length);
      tableRange.setHorizontalAlignment('center');
      tableRange.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
      sheet.getRange(headerRow, 1, 1, 1 + dias.length)
        .setBackground('#E5E7EB')
        .setFontWeight('bold')
        .setVerticalAlignment('middle');
      sheet.getRange(headerRow + 1, 1, bloques.length, 1)
        .setBackground('#F3F4F6')
        .setFontWeight('bold');

      sheet.setColumnWidth(1, 80);
      for (let c = 0; c < dias.length; c++) sheet.setColumnWidth(2 + c, 110);

      // Espacio entre profesores
      row = headerRow + 1 + bloques.length + 2;
    });
  });

  return { ok: true, count: files.length };
}

function sanitizeSheetName(name) {
  let s = String(name || 'Hoja').trim();
  s = s.replace(/[\[\]\:\*\?\/\\]/g, '-');
  if (s.length > 100) s = s.slice(0, 100);
  if (!s) s = 'Hoja';
  return s;
}

function safeArray_(v) {
  return Array.isArray(v) ? v : [];
}

function applyAlternatingRowBackground_(sheet, startRow, startCol, numRows, numCols, colorA, colorB) {
  if (!sheet || numRows <= 0 || numCols <= 0) return;
  const a = colorA || '#FFFFFF';
  const b = colorB || '#F9FAFB';

  const backgrounds = [];
  for (let r = 0; r < numRows; r++) {
    const rowColor = (r % 2 === 0) ? a : b;
    const row = new Array(numCols);
    row.fill(rowColor);
    backgrounds.push(row);
  }

  sheet.getRange(startRow, startCol, numRows, numCols).setBackgrounds(backgrounds);
}

function writeSubjectsAndProfessorsSheets_(ss, baseName, data) {
  writeAsignaturasSheet_(ss, baseName, data);
  writeProfesoresSheet_(ss, baseName, data);
  writeAlumnosSheet_(ss, baseName, data);
}

function writeAlumnosSheet_(ss, baseName, data) {
  const sheetName = sanitizeSheetName(`${baseName}-Alumnos`);
  let sheet = ss.getSheetByName(sheetName);
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet(sheetName);

  const header = ['ID', 'Asignaturas'];
  const rows = [header];

  const estudiantes = safeArray_(data?.recursos?.estudiantes);
  for (const est of estudiantes) {
    const id = String(est?.id || '').trim();
    if (!id) continue;

    const inscripciones = safeArray_(est?.asignaturas).map((x) => {
      const cod = String(x?.codigo || '').trim();
      const par = String(x?.paralelo || '').trim();
      if (!cod && !par) return '';
      if (cod && par) return `${cod}-${par}`;
      return cod || par;
    }).filter(Boolean);

    rows.push([id, inscripciones.join(', ')]);
  }

  const range = sheet.getRange(1, 1, rows.length, rows[0].length);
  range.setNumberFormat('@');
  range.setValues(rows);

  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, rows[0].length)
    .setFontWeight('bold')
    .setBackground('#E5E7EB')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  range.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
  if (rows.length > 1) applyAlternatingRowBackground_(sheet, 2, 1, rows.length - 1, rows[0].length);

  sheet.getRange(2, 1, Math.max(rows.length - 1, 1), rows[0].length)
    .setHorizontalAlignment('left')
    .setVerticalAlignment('top')
    .setWrap(true);

  sheet.setColumnWidth(1, 240); // ID
  sheet.setColumnWidth(2, 520); // Asignaturas
}

function writeAsignaturasSheet_(ss, baseName, data) {
  const sheetName = sanitizeSheetName(`${baseName}-Asignaturas`);
  let sheet = ss.getSheetByName(sheetName);
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet(sheetName);

  const header = ['Código', 'Carrera', 'Semestre', 'Nombre', 'Profesores', 'Horario'];
  const rows = [header];

  const asignaturas = safeArray_(data?.eventos?.asignaturas);
  for (const subj of asignaturas) {
    const codAsig = String(subj?.codigo || '').trim();
    const nombre = String(subj?.nombre || '').trim();
    const carrera = String(subj?.curso?.carrera || '').trim();
    const semestre = String(subj?.curso?.semestre || '').trim();

    for (const par of safeArray_(subj?.paralelos)) {
      const codPar = String(par?.codigo || '').trim();
      const cod = [codAsig, codPar].filter(Boolean).join('-');

      const profesores = listTeachersForParallel_(par);
      const horario = buildHorarioStringForParallel_(par);

      rows.push([
        cod,
        carrera,
        semestre,
        nombre,
        profesores.join(', '),
        horario
      ]);
    }
  }

  const range = sheet.getRange(1, 1, rows.length, rows[0].length);
  range.setNumberFormat('@');
  range.setValues(rows);

  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, rows[0].length)
    .setFontWeight('bold')
    .setBackground('#E5E7EB')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  range.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
  if (rows.length > 1) applyAlternatingRowBackground_(sheet, 2, 1, rows.length - 1, rows[0].length);

  sheet.getRange(2, 1, Math.max(rows.length - 1, 1), rows[0].length)
    .setHorizontalAlignment('left')
    .setVerticalAlignment('top')
    .setWrap(true);

  // Column widths
  sheet.setColumnWidth(1, 165); // Cod
  sheet.setColumnWidth(2, 80);  // Carrera
  sheet.setColumnWidth(3, 85);  // Semestre
  sheet.setColumnWidth(4, 340); // Nombre
  sheet.setColumnWidth(5, 280); // Profesores
  sheet.setColumnWidth(6, 420); // Horario
}

function writeProfesoresSheet_(ss, baseName, data) {
  const sheetName = sanitizeSheetName(`${baseName}-Profesores`);
  let sheet = ss.getSheetByName(sheetName);
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet(sheetName);

  const header = ['Nombre', 'Asignaturas'];
  const rows = [header];

  const teacherNames = getAllTeacherNames_(data);
  const assignments = new Map();
  for (const t of teacherNames) assignments.set(t, new Set());

  const asignaturas = safeArray_(data?.eventos?.asignaturas);
  for (const subj of asignaturas) {
    const codAsig = String(subj?.codigo || '').trim();
    for (const par of safeArray_(subj?.paralelos)) {
      const codPar = String(par?.codigo || '').trim();
      const cod = [codAsig, codPar].filter(Boolean).join('-');
      if (!cod) continue;

      const teachersForPar = listTeachersForParallel_(par);
      for (const t of teachersForPar) {
        if (!assignments.has(t)) assignments.set(t, new Set());
        assignments.get(t).add(cod);
      }
    }
  }

  for (const t of teacherNames) {
    const set = assignments.get(t) || new Set();
    rows.push([t, Array.from(set).join(', ')]);
  }

  const range = sheet.getRange(1, 1, rows.length, rows[0].length);
  range.setNumberFormat('@');
  range.setValues(rows);

  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, rows[0].length)
    .setFontWeight('bold')
    .setBackground('#E5E7EB')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  range.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
  if (rows.length > 1) applyAlternatingRowBackground_(sheet, 2, 1, rows.length - 1, rows[0].length);

  sheet.getRange(2, 1, Math.max(rows.length - 1, 1), rows[0].length)
    .setHorizontalAlignment('left')
    .setVerticalAlignment('top')
    .setWrap(true);

  sheet.setColumnWidth(1, 240); // Nombre
  sheet.setColumnWidth(2, 520); // Asignaturas
}

function listTeachersForParallel_(par) {
  const out = [];
  const seen = new Set();
  const add = (name) => {
    const n = normalizeTeacherName_(name);
    if (!n) return;
    const key = n.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    out.push(n);
  };

  // Primero maestros del paralelo
  safeArray_(par?.maestros).forEach(add);

  // Luego maestros específicos de clases (si existen)
  for (const cls of safeArray_(par?.clases)) {
    if (Array.isArray(cls?.maestros)) {
      cls.maestros.forEach(add);
    }
  }

  return out;
}

function buildHorarioStringForParallel_(par) {
  const parts = [];
  for (const cls of safeArray_(par?.clases)) {
    const horario = cls?.horario_predefinido;
    if (!horario) continue;

    const dia = String(horario?.dia || '').trim();
    const bloque = String(horario?.bloque || '').trim();
    const tipo = String(cls?.tipo || '').trim();

    if (!dia || !bloque || !tipo) continue;
    parts.push(`${dia} ${bloque} ${tipo}`);
  }
  return parts.join(', ');
}

// Soporta formato: [{"Lu":[...]},{"Ma":[...]}...] (como tu gestor)
function buildAvailabilityMap_(disponibilidad, dias, blockLen) {
  const map = {};
  dias.forEach((d) => { map[d] = new Array(blockLen).fill(0); });

  if (!Array.isArray(disponibilidad)) return map;

  disponibilidad.forEach((entry) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return;
    const keys = Object.keys(entry);
    if (keys.length !== 1) return;
    const day = keys[0];
    if (!map[day]) return;

    const arr = Array.isArray(entry[day]) ? entry[day] : [];
    for (let i = 0; i < blockLen; i++) {
      map[day][i] = Number(arr[i]) === 1 ? 1 : 0;
    }
  });

  return map;
}

function writeScheduleFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');
    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    const sheetName = sanitizeSheetName(`${baseName}-HorarioDocente`);

    let sheet = ss.getSheetByName(sheetName);
    if (sheet) ss.deleteSheet(sheet);
    sheet = ss.insertSheet(sheetName);

    const bloques = safeArray_(data?.tiempos?.bloques).length
      ? data.tiempos.bloques
      : ['1-2','3-4','5-6','7-8','9-10','11-12','13-14'];

    const dias = safeArray_(data?.tiempos?.dias).length
      ? data.tiempos.dias
      : ['Lu','Ma','Mi','Ju','Vi'];

    const dayLabels = { Lu: 'Lunes', Ma: 'Martes', Mi: 'Miércoles', Ju: 'Jueves', Vi: 'Viernes' };

    // Lista de profesores: recursos.maestros + detectados desde planilla
    const teacherNames = getAllTeacherNames_(data);
    if (teacherNames.length === 0) {
      sheet.getRange(1, 1).setValue('No hay maestros en el JSON.');
      return;
    }

    // Construir mapa: teacher -> (day|block) -> [entries...]
    const byTeacher = buildTeacherSchedule_(data, dias, bloques);

    let row = 1;

    teacherNames.forEach((teacherName) => {
      // Fila 1: "Profesor:" + nombre
      sheet.getRange(row, 1).setValue('Profesor:').setFontWeight('bold');
      sheet.getRange(row, 2).setValue(teacherName);
      sheet.getRange(row, 1, 1, 2).setBackground('#F9FAFB');

      // Fila 2: headers
      const headerRow = row + 1;
      sheet.getRange(headerRow, 1).setValue('Bloque').setFontWeight('bold');
      dias.forEach((d, i) => {
        sheet.getRange(headerRow, 2 + i).setValue(dayLabels[d] || d).setFontWeight('bold');
      });

      // Filas de bloques
      const teacherMap = byTeacher.get(teacherName) || new Map();

      // Evitar que claves como "7-8" se interpreten como fecha
      sheet.getRange(headerRow + 1, 1, bloques.length, 1).setNumberFormat('@');

      bloques.forEach((bloque, bIndex) => {
        const r = headerRow + 1 + bIndex;
        sheet.getRange(r, 1).setValue(bloque);

        dias.forEach((d, i) => {
          const key = `${d}|${bloque}`;
          const items = teacherMap.get(key) || [];

          // Texto multilinea (si hay varias clases, se concatenan una debajo de otra)
          const cellText = items.join('\n');
          const cell = sheet.getRange(r, 2 + i);
          cell.setValue(cellText);
          cell.setWrap(true);
          cell.setVerticalAlignment('top');
        });
      });

      // Formato básico para legibilidad
      const tableRange = sheet.getRange(headerRow, 1, 1 + bloques.length, 1 + dias.length);
      tableRange.setHorizontalAlignment('left');
      tableRange.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
      sheet.getRange(headerRow, 1, 1, 1 + dias.length)
        .setBackground('#E5E7EB')
        .setFontWeight('bold')
        .setVerticalAlignment('middle');
      sheet.getRange(headerRow + 1, 1, bloques.length, 1)
        .setBackground('#F3F4F6')
        .setFontWeight('bold')
        .setHorizontalAlignment('center');
      applyAlternatingRowBackground_(sheet, headerRow + 1, 2, bloques.length, dias.length);

      sheet.setColumnWidth(1, 80);
      for (let c = 0; c < dias.length; c++) sheet.setColumnWidth(2 + c, 240);

      // Espacio entre profesores
      row = headerRow + 1 + bloques.length + 2;
    });
  });

  return { ok: true, count: files.length };
}

function buildTeacherSchedule_(data, dias, bloques) {
  const byTeacher = new Map();

  // Inicializar contenedores para todos los maestros conocidos
  for (const name of getAllTeacherNames_(data)) {
    byTeacher.set(name, new Map());
  }

  const asignaturas = safeArray_(data?.eventos?.asignaturas);

  for (const subj of asignaturas) {
    const codigoAsignatura = String(subj?.codigo || '').trim();
    const paralelos = safeArray_(subj?.paralelos);

    for (const par of paralelos) {
      const codigoParalelo = String(par?.codigo || '').trim();
      const maestrosParalelo = safeArray_(par?.maestros).map(normalizeTeacherName_).filter(Boolean);
      const clases = safeArray_(par?.clases);

      for (const cls of clases) {
        const tipo = String(cls?.tipo || '').trim();
        const horario = cls?.horario_predefinido;
        const dia = String(horario?.dia || '').trim();
        const bloque = String(horario?.bloque || '').trim();

        if (!dia || !bloque) continue; // sin horario, no entra al “HorarioDocente”
        if (dias.indexOf(dia) < 0) continue;
        if (bloques.indexOf(bloque) < 0) continue;

        // Determinar maestros: hereda paralelo si no existe propiedad 'maestros' en cls
        let maestros = [];
        if (Object.prototype.hasOwnProperty.call(cls || {}, 'maestros')) {
          if (cls?.maestros === null) maestros = [];
          else maestros = safeArray_(cls?.maestros).map(normalizeTeacherName_).filter(Boolean);
        } else {
          maestros = maestrosParalelo;
        }

        if (maestros.length === 0) continue;

        const entry = `${codigoAsignatura} - ${codigoParalelo}\n${tipo}`;

        for (const m of maestros) {
          if (!byTeacher.has(m)) byTeacher.set(m, new Map());
          const map = byTeacher.get(m);

          const key = `${dia}|${bloque}`;
          const prev = map.get(key) || [];
          prev.push(entry);
          map.set(key, prev);
        }
      }
    }
  }

  return byTeacher;
}

function getAllTeacherNames_(data) {
  const fromResources = safeArray_(data?.recursos?.maestros)
    .map((m) => normalizeTeacherName_(m?.nombre))
    .filter(Boolean);

  const fromPlanilla = extractTeachersFromPlanilla_(data);

  // mantener orden: primero recursos, luego los que falten
  const seen = new Set();
  const out = [];
  for (const n of [...fromResources, ...fromPlanilla]) {
    const key = n.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(n);
  }
  return out;
}

function extractTeachersFromPlanilla_(data) {
  const names = [];
  const asignaturas = safeArray_(data?.eventos?.asignaturas);

  for (const subj of asignaturas) {
    // si existiera subj.maestros
    if (Array.isArray(subj?.maestros)) names.push(...subj.maestros);

    for (const par of safeArray_(subj?.paralelos)) {
      names.push(...safeArray_(par?.maestros));
      for (const cls of safeArray_(par?.clases)) {
        if (Array.isArray(cls?.maestros)) names.push(...cls.maestros);
      }
    }
  }

  const cleaned = names.map(normalizeTeacherName_).filter(Boolean);
  return Array.from(new Set(cleaned.map((n) => n.toLowerCase()))).map((k) => {
    // recuperar casing original (primera ocurrencia)
    return cleaned.find((n) => n.toLowerCase() === k) || k;
  });
}

function normalizeTeacherName_(v) {
  return String(v || '').trim().replace(/\s+/g, ' ');
}

function writePeriodScheduleFromJsonFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('No se recibieron archivos.');
  }

  const ss = SpreadsheetApp.getActive();

  files.forEach((f) => {
    const fileName = String(f && f.name ? f.name : 'Horario.json');
    const jsonText = String(f && f.text ? f.text : '');
    if (!jsonText.trim()) throw new Error(`Archivo vacío: ${fileName}`);

    let data;
    try {
      data = JSON.parse(jsonText);
    } catch (e) {
      throw new Error(`JSON inválido (${fileName}): ${e && e.message ? e.message : e}`);
    }

    const baseName = fileName.replace(/\.json$/i, '');
    const sheetName = sanitizeSheetName(`${baseName}-HorarioMaestro`);

    let sheet = ss.getSheetByName(sheetName);
    if (sheet) ss.deleteSheet(sheet);
    sheet = ss.insertSheet(sheetName);

    const dias = safeArray_(data?.tiempos?.dias).length ? data.tiempos.dias : ['Lu','Ma','Mi','Ju','Vi'];
    const bloques = safeArray_(data?.tiempos?.bloques).length ? data.tiempos.bloques : ['1-2','3-4','5-6','7-8','9-10','11-12','13-14'];

    // key = "Lu|1-2" => [{curso, actividad, profesores}, ...]
    const periodMap = new Map();
    const pushToPeriod = (dia, bloque, item) => {
      const key = `${dia}|${bloque}`;
      const arr = periodMap.get(key) || [];
      arr.push(item);
      periodMap.set(key, arr);
    };

    const asignaturas = safeArray_(data?.eventos?.asignaturas);

    for (const subj of asignaturas) {
      const codAsig = String(subj?.codigo || '').trim();
      for (const par of safeArray_(subj?.paralelos)) {
        const codPar = String(par?.codigo || '').trim();
        const maestrosParalelo = safeArray_(par?.maestros).map(normalizeTeacherName_).filter(Boolean);

        for (const cls of safeArray_(par?.clases)) {
          const horario = cls?.horario_predefinido;
          if (!horario) continue; // SOLO con horario_predefinido

          const dia = String(horario?.dia || '').trim();
          const bloque = String(horario?.bloque || '').trim();
          if (!dia || !bloque) continue;
          if (dias.indexOf(dia) < 0) continue;
          if (bloques.indexOf(bloque) < 0) continue;

          const tipo = String(cls?.tipo || '').trim();

          // Profesores: hereda paralelo si cls no tiene propiedad 'maestros'
          let maestros = [];
          if (Object.prototype.hasOwnProperty.call(cls || {}, 'maestros')) {
            if (cls?.maestros === null) maestros = [];
            else maestros = safeArray_(cls?.maestros).map(normalizeTeacherName_).filter(Boolean);
          } else {
            maestros = maestrosParalelo;
          }

          const item = {
            curso: `${codAsig}-${codPar}`,
            actividad: tipo,
            profesores: maestros.join(', ')
          };

          pushToPeriod(dia, bloque, item);
        }
      }
    }

    // Máxima concurrencia para repetir C..G hacia la derecha
    let maxConcurrent = 0;
    for (const arr of periodMap.values()) maxConcurrent = Math.max(maxConcurrent, arr.length);
    if (maxConcurrent < 1) maxConcurrent = 1;

    // Header
    const header = ['Día', 'Bloque'];
    for (let i = 0; i < maxConcurrent; i++) {
      header.push('Curso', 'Actividad', 'Profesores', 'Sala', 'Estudiantes');
    }

    const rows = [];
    rows.push(header);

    // Filas: todos los días x todos los bloques (aunque no haya clases)
    for (const dia of dias) {
      for (const bloque of bloques) {
        const key = `${dia}|${bloque}`;
        const items = periodMap.get(key) || [];

        const row = [dia, bloque];
        for (let i = 0; i < maxConcurrent; i++) {
          const it = items[i];
          if (it) {
            row.push(it.curso || '', it.actividad || '', it.profesores || '', '', '');
          } else {
            row.push('', '', '', '', '');
          }
        }
        rows.push(row);
      }
    }

    // Escribir todo de una vez
    const range = sheet.getRange(1, 1, rows.length, rows[0].length);
    // Evitar auto-parseo a fecha (por ejemplo "7-8") en toda la tabla
    range.setNumberFormat('@');
    range.setValues(rows);

    // Formato mínimo
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, rows[0].length).setFontWeight('bold');
    range.setWrap(true);
    sheet.getRange(2, 1, rows.length - 1, 2).setWrap(false);

    // Estilo tabla
    range.setBorder(true, true, true, true, true, true, '#D1D5DB', SpreadsheetApp.BorderStyle.SOLID);
    sheet.getRange(1, 1, 1, rows[0].length)
      .setBackground('#E5E7EB')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle');
    if (rows.length > 1) {
      sheet.getRange(2, 1, rows.length - 1, 2)
        .setBackground('#F3F4F6')
        .setFontWeight('bold')
        .setHorizontalAlignment('center');
      const extraCols = rows[0].length - 2;
      if (extraCols > 0) {
        applyAlternatingRowBackground_(sheet, 2, 3, rows.length - 1, extraCols);
      }
    }

    // Divisor más notorio entre grupos (…Estudiantes | Curso…)
    // Pone un borde derecho más grueso en cada columna "Estudiantes" salvo la última.
    const dividerColor = '#6B7280';
    for (let g = 0; g < maxConcurrent - 1; g++) {
      const estudiantesCol = 3 + g * 5 + 4;
      sheet
        .getRange(1, estudiantesCol, rows.length, 1)
        .setBorder(null, null, null, true, null, null, dividerColor, SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    }

    // Anchos (opcionales, pero ayuda)
    sheet.setColumnWidth(1, 55);  // Día
    sheet.setColumnWidth(2, 65);  // Bloque
    for (let g = 0; g < maxConcurrent; g++) {
      const baseCol = 3 + g * 5;
      sheet.setColumnWidth(baseCol + 0, 140); // Curso
      sheet.setColumnWidth(baseCol + 1, 95);  // Actividad
      sheet.setColumnWidth(baseCol + 2, 240); // Profesores
      sheet.setColumnWidth(baseCol + 3, 90);  // Sala
      sheet.setColumnWidth(baseCol + 4, 120); // Estudiantes
    }
  });

  return { ok: true, count: files.length };
}

function writeAllFromJsonFiles(files) {
  // Genera las 6 hojas con los mismos archivos
  writeAvailabilityFromJsonFiles(files);
  writeScheduleFromJsonFiles(files);
  writePeriodScheduleFromJsonFiles(files);
  writeAsignaturasFromJsonFiles(files);
  writeProfesoresFromJsonFiles(files);
  writeAlumnosFromJsonFiles(files);
  return { ok: true, count: Array.isArray(files) ? files.length : 0 };
}
