function onOpen(e) {
  // Un solo onOpen por proyecto. Aquí se invocan los inicializadores de menús
  // definidos en otros archivos .gs para evitar sobreescrituras.

  try {
    if (typeof onOpenPlanificacionDocente_ === 'function') {
      onOpenPlanificacionDocente_(e);
    }
  } catch (err) {
    console.error('Error inicializando menú Planificación docente:', err);
  }

  try {
    if (typeof onOpenEvaluacionFO_ === 'function') {
      onOpenEvaluacionFO_(e);
    }
  } catch (err) {
    console.error('Error inicializando menú Evaluación FO:', err);
  }
}
