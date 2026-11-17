/* Los iconos de LLACTA, dibujados aquí.
 *
 * No vienen de una tipografía de iconos ni de un CDN: son trazos sobre una
 * retícula de 24, con el color heredado y el grosor en una sola constante. Hay
 * tres razones y ninguna es estética.
 *
 * 1. Una página del municipio que depende de que el servidor de otro siga en
 *    pie es una página que algún día sale rota, y el aviso llega tarde.
 * 2. Dentro de la red interna puede no haber internet. El visor y CHASKI ya
 *    funcionan sin él; esto también.
 * 3. Un icono traído de fuera lleva su licencia detrás, y este repositorio es
 *    público.
 *
 * Cada icono dice algo del territorio, no de la interfaz: el árbol es el
 * parque barrial, la cruz es el subcentro, la carpeta es la mapoteca. Si un
 * icono no nombra una cosa real, sobra.
 */
window.ICONOS = (function () {
  var T = {
    /* --- los quince indicadores
     *
     * Uno por cada fila de la tabla 3 que fija radio. Eran tres y los doce que
     * llegaron después caían en `lugar`, la chincheta genérica: doce tarjetas
     * con el mismo dibujo no distinguen nada, que es justo lo que un icono
     * tiene que hacer en una rejilla de quince.
     *
     * Cada uno nombra la COSA, no la categoría: el birrete es el colegio, la
     * cancha es la cancha, la lápida es el cementerio. Y se dibujan para
     * leerse a 22 px, que es el tamaño al que salen en la tarjeta: nada de
     * detalles que a ese tamaño se vuelven una mancha. */
    arbol: '<path d="M12 21v-5"/><path d="M12 16c-3.3 0-6-2.4-6-5.5S8.7 5 12 5s6 2.4 6 5.5-2.7 5.5-6 5.5Z"/><path d="M9 21h6"/>',
    escuela: '<path d="M3 10 12 5l9 5"/><path d="M5 11v8h14v-8"/><path d="M10 19v-4h4v4"/>',
    salud: '<path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/><path d="M12 11v5M9.5 13.5h5"/>',
    // Birrete: el colegio y el instituto, frente a la casa con puerta de la
    // escuela barrial. Dos niveles distintos de la norma, dos dibujos.
    colegio: '<path d="m12 4.5 9 4.5-9 4.5-9-4.5z"/><path d="M6.8 11.2V16c0 1.5 2.3 2.7 5.2 2.7s5.2-1.2 5.2-2.7v-4.8"/><path d="M21 9v5"/>',
    // Linea de pulso dentro del edificio: el hospital y el centro de salud.
    // La cruz ya la usa el subcentro barrial y repetirla los confundiria.
    hospital: '<path d="M3.5 6.5h17v13h-17z"/><path d="M6.5 13h2.6l1.4-3 2.2 6 1.3-3h3.5"/>',
    deporte: '<path d="M3 6.5h18v11H3z"/><path d="M12 6.5v11"/><circle cx="12" cy="12" r="2.6"/><path d="M3 9.5h2.5v5H3M21 9.5h-2.5v5H21"/>',
    casa_comunal: '<path d="M12 7.6C10 6.1 7.5 5.6 4 5.6v12c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2v-12c-3.5 0-6 .5-8 2Z"/><path d="M12 7.6v12"/>',
    // Las columnas del museo, el teatro y el auditorio.
    cultura: '<path d="m3 9 9-5 9 5"/><path d="M5.5 9v9M9.8 9v9M14.2 9v9M18.5 9v9"/><path d="M3 20.5h18"/>',
    // Bloques de juego: el centro infantil y la guarderia.
    infantil: '<path d="M4 13.5h6.5V20H4z"/><path d="M13.5 13.5H20V20h-6.5z"/><path d="M8.7 6.5h6.6V13H8.7z"/>',
    albergue: '<path d="M3 19.5V10"/><path d="M3 14.5h18v5"/><circle cx="7" cy="11" r="2.1"/><path d="M10.5 14.5V11h7a3.5 3.5 0 0 1 3.5 3.5"/>',
    upc: '<path d="M12 3.2 20 6v6.2c0 4.6-3.4 7.5-8 9.1-4.6-1.6-8-4.5-8-9.1V6Z"/><path d="m9 12 2.2 2.2L15.2 10"/>',
    transporte: '<path d="M5 4.5h14v11.5H5z"/><path d="M5 10h14"/><circle cx="8.5" cy="18.5" r="1.6"/><circle cx="15.5" cy="18.5" r="1.6"/><path d="M7 16v1M17 16v1"/>',
    // La gota: la bateria sanitaria y la lavanderia publica, que es
    // infraestructura de agua antes que un edificio.
    bateria: '<path d="M12 3.4s6.2 6.7 6.2 10.3a6.2 6.2 0 0 1-12.4 0C5.8 10.1 12 3.4 12 3.4Z"/><path d="M9.3 13.8a2.7 2.7 0 0 0 2.7 2.7"/>',
    iglesia: '<path d="M12 2.4v4.2M10.1 4.5h3.8"/><path d="M12 6.8 4.6 12.4V21h14.8v-8.6Z"/><path d="M10 21v-4.6h4V21"/>',
    cementerio: '<path d="M5 21h14"/><path d="M8 21v-8.6a4 4 0 0 1 8 0V21"/><path d="M12 9.3v5.2M10 11.6h4"/>',

    // --- las cuatro ventanas
    // NAWI es «ojo» en kichwa, asi que el icono es un ojo y no un mapa
    // plegado. El nombre y el dibujo dicen lo mismo o no dicen nada.
    nawi: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    chaski: '<path d="M12 3v3M12 18v3M3 12h3M18 12h3"/><circle cx="12" cy="12" r="4.5"/><path d="m14.5 9.5 3-3M6.5 17.5l3-3"/>',
    mapoteca: '<path d="M4 5h6l2 2h8v12H4z"/><path d="M8 11h8M8 15h5"/>',
    levantamiento: '<path d="M8 4h8v3H8z"/><path d="M6 6h2M16 6h2v14H6V6"/><path d="m9.5 13 2 2 3.5-3.5"/>',

    // --- los objetivos
    gente: '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M16 5.5a3 3 0 0 1 0 5.6M18 20c0-2.6-1-4.4-2.5-5.3"/>',
    serie: '<path d="M3 20h18"/><path d="M3 20V4"/><path d="m6 15 4-4 3 3 5-6"/><circle cx="6" cy="15" r="1.3"/><circle cx="10" cy="11" r="1.3"/><circle cx="13" cy="14" r="1.3"/><circle cx="18" cy="8" r="1.3"/>',
    hueco: '<path d="M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Z" stroke-dasharray="3 3"/><path d="M12 8v5"/><circle cx="12" cy="16.5" r="1" fill="currentColor" stroke="none"/>',
    rehacer: '<path d="M4 12a8 8 0 1 1 2.6 5.9"/><path d="M4 18v-5h5"/><path d="M12 8v4.5l3 1.8"/>',

    // --- señales
    aviso: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4"/><circle cx="12" cy="17.2" r="1" fill="currentColor" stroke="none"/>',
    norma: '<path d="M5 4h11l3 3v13H5z"/><path d="M16 4v3h3"/><path d="M8.5 12h7M8.5 16h4"/>',
    lugar: '<path d="M12 21s6.5-6 6.5-10.5a6.5 6.5 0 1 0-13 0C5.5 15 12 21 12 21Z"/><circle cx="12" cy="10.5" r="2.3"/>'
  };

  var POR_CLAVE = {
    proximidad_area_verde: 'arbol',
    proximidad_escuela: 'escuela',
    proximidad_salud: 'salud',
    proximidad_colegio: 'colegio',
    proximidad_hospital: 'hospital',
    proximidad_deporte: 'deporte',
    proximidad_casa_comunal: 'casa_comunal',
    proximidad_cultura: 'cultura',
    proximidad_infantil: 'infantil',
    proximidad_albergue: 'albergue',
    proximidad_upc: 'upc',
    proximidad_transporte: 'transporte',
    proximidad_bateria: 'bateria',
    proximidad_iglesia: 'iglesia',
    proximidad_cementerio: 'cementerio'
  };

  return {
    /** El icono como SVG, con el tamaño pedido y el color del texto. */
    svg: function (nombre, lado, clase) {
      var d = T[nombre];
      if (!d) return '';
      return '<svg class="ico ' + (clase || '') + '" width="' + (lado || 24) +
        '" height="' + (lado || 24) + '" viewBox="0 0 24 24" fill="none" ' +
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" ' +
        'stroke-linejoin="round" aria-hidden="true" focusable="false">' + d + '</svg>';
    },
    /** Qué icono le toca a cada indicador, por su clave.
     *
     * Un mapa y no una pila de `indexOf`. Aquello encontraba «salud» dentro de
     * `proximidad_salud` pero también la habría encontrado en cualquier clave
     * nueva que llevara esa palabra, y daba el mismo icono a dos indicadores
     * distintos sin avisar. Aquí una clave tiene su icono o no lo tiene.
     *
     * Lo que no esté listado cae en la chincheta: si la norma añade una fila,
     * la tarjeta sale igual y con un dibujo que no miente sobre qué es.
     */
    deIndicador: function (clave) {
      return POR_CLAVE[clave] || 'lugar';
    }
  };
})();

/* Los iconos declarados en el marcado con `data-ico` se rellenan aquí mismo.
 *
 * Sin esperar a `DOMContentLoaded`: este archivo se carga al final del cuerpo,
 * así que todo lo que lleva `data-ico` ya existe, y un oyente de evento en
 * otro archivo se queda sin disparar en cuanto el navegador sirve ese otro
 * archivo de la caché —que es justo lo que pasó—.
 *
 * El marcado dice QUÉ icono va; cómo se dibuja vive solo aquí arriba.
 */
document.querySelectorAll('[data-ico]').forEach(function (e) {
  e.insertAdjacentHTML('afterbegin', window.ICONOS.svg(e.dataset.ico, 20));
});
