/* Lo que comparten las páginas de LLACTA: formato es-EC y escape.
 *
 * Va en un archivo y no copiado en cada página porque el formato de las
 * cifras es una decisión del sistema de diseño —punto de miles, coma decimal,
 * cifras tabulares—, y una página que lo haga distinto se nota en seguida y
 * hace dudar del dato. */
window.LL = (function () {
  var N = new Intl.NumberFormat('es-EC');
  var N1 = new Intl.NumberFormat('es-EC', {
    minimumFractionDigits: 1, maximumFractionDigits: 1
  });
  var FECHA = new Intl.DateTimeFormat('es-EC', {
    day: 'numeric', month: 'long', year: 'numeric'
  });

  return {
    N: N,
    N1: N1,

    /** Una fecha ISO leída como fecha local, no como UTC.
     *  `new Date('2026-11-04')` se interpreta en UTC y en Ecuador —UTC-5—
     *  retrocede un día: el dato del 4 saldría fechado el 3. */
    fecha: function (iso) {
      var p = String(iso).split('-');
      return FECHA.format(new Date(+p[0], +p[1] - 1, +p[2]));
    },

    /** Peso de archivo en la unidad que se lee de un vistazo. */
    peso: function (bytes) {
      if (bytes >= 1048576) return N1.format(bytes / 1048576) + ' MB';
      return N.format(Math.round(bytes / 1024)) + ' KB';
    },

    /** Todo lo que viene del dato pasa por aquí antes de entrar al HTML. */
    esc: function (s) {
      return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }
  };
})();
