/* La portada de LLACTA: el mapa, la tabla de parroquias y las tarjetas.
 *
 * El mapa son 3.757 trazos SVG que `scripts/escalas.py` ya dejó dibujados y
 * medidos. Aquí no se calcula ni una cifra: se pinta lo que vino, y cambiar de
 * indicador es repintar los mismos trazos con otro número de la misma lista.
 * Por eso no hay espera al cambiar, y por eso la página no necesita servidor.
 */
(function () {
  var D = window.LLACTA;              // los tres indicadores, en el cantón
  var E = window.LLACTA_ESCALAS;      // los mismos, por parroquia
  var M = window.LLACTA_MAPA;         // los trazos
  var C = window.LLACTA_CAPAS;        // el catálogo, solo para el pie de ventana
  var F = window.LL;
  var sello = document.getElementById('sello');

  if (!D || !E || !M) {
    sello.innerHTML = '<span class="gr-chip gr-chip--aviso">Faltan datos: corre ' +
      'scripts/indicadores.py y scripts/escalas.py</span>';
    return;
  }

  var R = window.LLACTA_RED;  // la red vial por cercanía, si está generada
  var escalaSel = 0;          // qué división del territorio se está usando
  var elegido = 0;            // qué indicador se está pintando
  var encuadre = 'ciudad';    // 'ciudad' o 'canton'
  var vista = 'manzanas';     // 'manzanas' (la gente) o 'calles' (la ciudad)

  // La escala de la red es DIVERGENTE y gira en el radio de la ordenanza:
  // azul es «dentro de la norma», ocre es «fuera». No es una rampa de
  // magnitud, es un umbral, y el umbral es el que manda la tabla 3.
  var VIAS = [
    { f: 0.5, rotulo: 'a medio radio o menos', token: '--gr-cerca-2' },
    { f: 1.0, rotulo: 'dentro del radio', token: '--gr-cerca-1' },
    { f: 1.5, rotulo: 'hasta vez y media', token: '--gr-pivote' },
    { f: 3.0, rotulo: 'hasta el triple', token: '--gr-lejos-1' },
    { f: 1e9, rotulo: 'más lejos', token: '--gr-lejos-2' }
  ];
  function tramoVia(metros, radio) {
    for (var i = 0; i < VIAS.length; i++) if (metros <= radio * VIAS[i].f) return i;
    return VIAS.length - 1;
  }

  /* LA RAMPA SE GENERA DEL TONO DEL INDICADOR, no de una lista fija.
   *
   * Antes los tres indicadores se pintaban con el mismo azul y cambiar de uno
   * a otro no cambiaba nada que el ojo notara: solo se movían unos números.
   * Ahora cada uno lleva su tono de la paleta de series del sistema en toda
   * la página —tarjeta, pastilla, mapa, columna de la tabla y panel—, que es
   * la regla de que el color sigue a la entidad.
   *
   * Los seis escalones salen del mismo tono moviendo SOLO la luminosidad, que
   * es lo que pide una rampa secuencial: una escala de magnitud con varios
   * tonos obliga a mirar la leyenda para saber cuál va antes.
   *
   * En tema oscuro la dirección se invierte: sobre fondo negro, «más» tiene
   * que ser «más brillante» o la manzana con menos cobertura acabaría siendo
   * la que más llama.
   */
  var raiz = getComputedStyle(document.documentElement);
  var oscuro = matchMedia('(prefers-color-scheme: dark)').matches;

  function aHsl(css) {
    var d = document.createElement('span');
    d.style.color = css; document.body.appendChild(d);
    var m = getComputedStyle(d).color.match(/\d+/g);
    d.remove();
    var r = m[0] / 255, g = m[1] / 255, b = m[2] / 255;
    var mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, h = 0, s = 0;
    if (mx !== mn) {
      var dd = mx - mn;
      s = l > 0.5 ? dd / (2 - mx - mn) : dd / (mx + mn);
      h = mx === r ? ((g - b) / dd + (g < b ? 6 : 0)) : mx === g ? (b - r) / dd + 2 : (r - g) / dd + 4;
      h *= 60;
    }
    return { h: h, s: s * 100, l: l * 100 };
  }

  var CACHE = {};
  function rampaDe(clave) {
    if (CACHE[clave]) return CACHE[clave];
    var base = aHsl(raiz.getPropertyValue('--gr-' + clave).trim() || '#2C74B0');
    // De claro a oscuro sobre fondo claro; al revés sobre fondo oscuro.
    var luces = oscuro ? [20, 30, 40, 52, 66, 82] : [90, 78, 63, 48, 34, 22];
    var sat = oscuro ? [38, 46, 52, 56, 58, 55] : [34, 42, 50, 56, 60, 62];
    CACHE[clave] = luces.map(function (l, i) {
      return 'hsl(' + Math.round(base.h) + ' ' + Math.round(Math.min(base.s * 1.05, sat[i])) +
        '% ' + l + '%)';
    });
    return CACHE[clave];
  }

  var CORTES = [0, 20, 40, 60, 80, 99, 100];
  var ROTULOS = ['sin cobertura', '1 – 20 %', '21 – 40 %', '41 – 60 %',
                 '61 – 80 %', '81 – 99 %', 'cubierta entera'];
  function tramo(pct) {
    for (var i = 0; i < CORTES.length; i++) if (pct <= CORTES[i]) return i;
    return CORTES.length - 1;
  }
  /** El tono del indicador que se está pintando, como `s1`, `s2`, `s3`. */
  function serie(i) { return 's' + ((i % 8) + 1); }
  /* Los nombres de las parroquias, sobre el mapa, con su punto y su guía.
     Es lo que hace que una lámina se lea sin leyenda: nadie reconoce su
     barrio por la forma, pero todo el mundo reconoce «Lizarzaburu». El ancla
     la calculó el script con un punto que cae dentro de la parroquia, no con
     el centroide, que en Pungalá queda fuera de ella. */
  /** La división que se está mirando: `plataformas` o `parroquias`. */
  function claveEscala() { return E.escalas[escalaSel].clave; }
  function limites() { return M.limites[claveEscala()] || []; }

  /* Los límites y los nombres se dibujan en capas vacías que se rellenan al
     vuelo, y no cosidos al SVG: cambiar de escala tiene que cambiar lo que se
     ve sobre el mapa, no solo la tabla de abajo. Si el mapa siguiera con las
     parroquias mientras la tabla habla de plataformas, serían dos páginas. */
  function pintarLimites() {
    var L = limites();
    var bordes = L.map(function (p) {
      return '<path class="par" d="' + p.d + '"/>';
    }).join('');
    var nombres = L.filter(function (p) { return p.x !== undefined; })
      .map(function (p) {
        return '<circle class="punto-rotulo" cx="' + p.x + '" cy="' + p.y + '" r="3"/>' +
          '<line class="guia" x1="' + p.x + '" y1="' + p.y +
            '" x2="' + (p.x + 16) + '" y2="' + (p.y - 16) + '"/>' +
          '<text class="rotulo" x="' + (p.x + 20) + '" y="' + (p.y - 17) + '">' +
            F.esc(p.n) + '</text>';
      }).join('');
    document.querySelectorAll('.capa-lim').forEach(function (g) { g.innerHTML = bordes; });
    document.querySelectorAll('.rotulos').forEach(function (g) { g.innerHTML = nombres; });
    tallarRotulos();
  }

  /* El tamaño del rótulo va en unidades del viewBox, así que tiene que
     recalcularse al cambiar de encuadre o el nombre saldría del tamaño de
     una parroquia entera en la vista de ciudad. */
  function tallarRotulos() {
    var ancho = (vista === 'calles' ? R : M).viewBox[encuadre][2];
    var cuerpo = Math.max(7, ancho / 52);
    document.querySelectorAll('.rotulos').forEach(function (g) {
      g.style.fontSize = cuerpo + 'px';
      g.querySelectorAll('.punto-rotulo').forEach(function (c) {
        c.setAttribute('r', cuerpo / 4);
      });
      g.querySelectorAll('.guia').forEach(function (l) {
        l.setAttribute('stroke-width', cuerpo / 12);
      });
      g.querySelectorAll('.rotulo').forEach(function (t) {
        t.style.strokeWidth = (cuerpo / 5) + 'px';
      });
    });
  }

  // El tramo 0 se rellena con la trama; los demás, con su tono de la rampa.
  function color(i, cual) {
    return i === 0 ? 'url(#sincob)' : rampaDe(serie(cual === undefined ? elegido : cual))[i - 1];
  }
  function muestra(i, cual) {
    return i === 0 ? 'var(--gr-nada)' : rampaDe(serie(cual === undefined ? elegido : cual))[i - 1];
  }

  /* ------------------------------------------------------------- el sello */
  sello.innerHTML =
    '<span class="gr-chip gr-chip--info">Dato del ' + F.esc(F.fecha(D.generado)) + '</span>' +
    '<span class="gr-chip">Método v' + F.esc(D.version_metodo) + '</span>' +
    '<span class="gr-chip">Censo 2022 · INEC</span>' +
    '<span class="gr-chip">' +
      E.escalas.map(function (s) {
        return s.unidades.length + ' ' + s.nombre.toLowerCase();
      }).join(' · ') + ' · ' + F.N.format(M.manzanas.length) + ' manzanas</span>' +
    '<span class="gr-chip gr-chip--aviso">Prototipo · cifras para revisar</span>';

  if (C && C.capas) {
    var mb = C.capas.reduce(function (s, c) { return s + c.bytes; }, 0) / 1048576;
    document.getElementById('pie-mapoteca').textContent =
      C.capas.length + ' capas · ' + F.N1.format(mb) + ' MB';
  }

  /* -------------------------------------------------------- los mandos */
  var mandos = D.indicadores.map(function (x, i) {
    return '<button class="pastilla" data-ind="' + i + '" aria-pressed="' +
      (i === elegido) + '" style="--acento-sel:var(--gr-' + serie(i) + ')">' +
      ICONOS.svg(ICONOS.deIndicador(x.clave), 17) +
      F.esc(x.nombre.replace('Gente con ', '')) + '</button>';
  }).join('') +
    '<span class="sep"></span>' +
    '<span class="vistas">' +
      E.escalas.map(function (s, i) {
        return '<button class="pastilla" data-escala="' + i + '" aria-pressed="' +
          (i === escalaSel) + '">' + F.esc(s.nombre) + '</button>';
      }).join('') + '</span>' +
    (R ? '<span class="vistas">' +
      '<button class="pastilla" data-vista="manzanas" aria-pressed="true">Manzanas</button>' +
      '<button class="pastilla" data-vista="calles" aria-pressed="false">Calles</button>' +
      '</span>' : '') +
    '<button class="pastilla" data-enc="ciudad" aria-pressed="true">La ciudad</button>' +
    '<button class="pastilla" data-enc="canton" aria-pressed="false">Todo el cantón</button>';
  document.getElementById('mandos').innerHTML = mandos;

  /* ---------------------------------------------------------- el dibujo */
  var vb = M.viewBox[encuadre];
  var svg = '<svg viewBox="' + vb.join(' ') + '" id="svg-mapa" ' +
    'role="img" aria-label="Mapa de Riobamba por manzanas. La tabla de ' +
    'parroquias de abajo dice lo mismo en texto.">' +
    // «Sin cobertura» va con trama además de color. El sistema de diseño pide
    // que nada dependa solo del color, y aquí hay una razón de fondo: esa
    // manzana no tiene un valor bajo de la escala, está fuera de la escala.
    '<defs><pattern id="sincob" width="6" height="6" ' +
      'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
      '<rect width="6" height="6" fill="var(--gr-nada)"/>' +
      '<line x1="0" y1="0" x2="0" y2="6" stroke="var(--gr-fondo)" ' +
      'stroke-width="2" opacity=".55"/></pattern></defs>';
  for (var i = 0; i < M.manzanas.length; i++) {
    svg += '<path class="mz" data-i="' + i + '" d="' + M.manzanas[i].d + '"/>';
  }
  svg += '<g class="capa-lim"></g><g class="rotulos"></g></svg>';
  // La escala y el norte se reponen aquí: `caja-mapa` se reescribe entera al
  // dibujar, y si el aparejo viviera solo en el HTML desaparecería.
  document.getElementById('caja-mapa').innerHTML = svg +
    '<div class="aparejo" id="aparejo" aria-hidden="true"></div>' +
    '<div class="globo" id="globo"></div>';

  var nodos = document.querySelectorAll('#svg-mapa .mz');
  var vias = null;                   // se dibujan la primera vez que se piden
  var globo = document.getElementById('globo');
  var caja = document.getElementById('caja-mapa');
  var lienzo = document.querySelector('.lienzo');

  // Los 16.952 tramos no se dibujan al cargar: quien entra viene a ver la
  // cifra y las manzanas, y meter 17.000 nodos más en el documento retrasa
  // eso para todo el mundo, incluido quien nunca toque el botón.
  function dibujarCalles() {
    if (vias) return;
    var s = '<svg viewBox="' + R.viewBox[encuadre].join(' ') + '" id="svg-red" ' +
      'role="img" aria-label="La red vial de Riobamba coloreada por la ' +
      'distancia al equipamiento más cercano.">';
    for (var i = 0; i < R.tramos.length; i++) {
      s += '<polyline class="tramo-via" data-i="' + i + '" points="' +
        R.tramos[i].p + '"/>';
    }
    s += '<g class="capa-lim"></g><g class="rotulos"></g></svg>';
    caja.insertAdjacentHTML('afterbegin', s);
    vias = caja.querySelectorAll('#svg-red .tramo-via');
  }

  function pintar() {
    var ind = D.indicadores[elegido];
    // El acento del indicador elegido viaja a toda la página de una vez.
    document.documentElement.style.setProperty(
      '--acento-sel', raiz.getPropertyValue('--gr-' + serie(elegido)).trim());
    if (vista === 'calles') {
      dibujarCalles();
      for (var v = 0; v < vias.length; v++) {
        vias[v].setAttribute('stroke',
          'var(' + VIAS[tramoVia(R.tramos[v].d[elegido], ind.radio_m)].token + ')');
      }
    } else {
      for (var k = 0; k < nodos.length; k++) {
        nodos[k].setAttribute('fill', color(tramo(M.manzanas[k].p[elegido])));
      }
    }
    var fuera = ind.denominador - ind.alcanzados;
    document.getElementById('titular-cifra').textContent = F.N.format(fuera);
    document.getElementById('titular-texto').innerHTML =
      '<strong>personas en Riobamba no tienen ' +
      F.esc(ind.nombre.replace('Gente con ', '').replace(' cerca', '')) +
      ' a menos de ' + F.N.format(ind.radio_m) + ' metros.</strong> ' +
      'De las ' + F.N.format(ind.denominador) + ' que viven en alguna manzana ' +
      'del Censo 2022, ' + F.N.format(ind.alcanzados) + ' sí lo tienen: ' +
      F.N1.format(ind.valor_pct) + ' %.';

    document.getElementById('leyenda').innerHTML =
      (vista === 'calles' ? rampaVias(ind) : rampaManzanas()) +
      '<span class="tramo" style="margin-left:auto">' +
      F.esc(ind.norma.simbolo) + ' ' + F.esc(ind.norma.tipologia) +
      ' · radio ' + F.N.format(ind.radio_m) + ' m</span>';

    document.getElementById('figura').innerHTML =
      '<b>Figura ' + (vista === 'calles' ? '2' : '1') + '</b> · ' +
      (vista === 'calles'
        ? 'Red vial de Riobamba por distancia a ' +
          F.esc(corto(ind)) + '. ' + F.N.format(R.tramos.length) +
          ' tramos de la red caminable. OpenStreetMap, ODbL.'
        : 'Manzanas de Riobamba por población alcanzada por ' +
          F.esc(corto(ind)) + '. ' + F.N.format(M.manzanas.length) +
          ' manzanas, Censo 2022 del INEC.') +
      ' Proyección UTM 17S · EPSG:32717.';
  }

  function corto(ind) {
    return ind.nombre.replace('Gente con ', '').replace(' cerca', '');
  }

  /* La leyenda de la red es una rampa continua con marcas de distancia, y
     el radio de la ordenanza señalado encima: es lo que convierte la escala
     en una afirmación —«esto es la norma»— en vez de cinco colores sueltos.
     Las marcas van en metros Y en minutos, a los 75 m/min que el visor usa
     para sus isócronas: nadie piensa su barrio en metros. */
  function rampaVias(ind) {
    var topes = VIAS.map(function (t) { return t.f; });
    var max = 3;                                // el último tramo se corta aquí
    var barra = VIAS.map(function (t) {
      var ancho = (Math.min(t.f, max) - 0) / max;
      return '<i style="background:var(' + t.token + ');flex:' +
        (t.f > max ? 0.5 : ancho) + '"></i>';
    }).join('');
    var marcas = '';
    [0.5, 1, 1.5, 2, 3].forEach(function (f) {
      var m = Math.round(ind.radio_m * f);
      var min = m / (R.velocidad_m_min || 75);
      marcas += '<span class="marca' + (f === 1 ? ' umbral' : '') +
        '" style="left:' + (Math.min(f, max) / max * 100 * (1 / 1.1667)) + '%">' +
        F.N.format(m) + ' m<br>' + F.N1.format(min) + ' min' +
        (f === 1 ? '<br>ordenanza' : '') + '</span>';
    });
    return '<span class="rampa"><span class="titulo">Distancia a ' +
      F.esc(corto(ind)) + '</span><span class="barra-l">' + barra +
      '</span><span class="ejes">' + marcas + '</span></span>' +
      '<span class="aparte">caminando a 4,5 km/h</span>';
  }

  /* La de manzanas es una rampa de 0 a 100 %, y «sin cobertura» va FUERA de
     ella, con su trama: no es el extremo bajo de la escala, es otra cosa. */
  function rampaManzanas() {
    var barra = '';
    for (var n = 1; n < CORTES.length; n++) {
      barra += '<i style="background:' + muestra(n) + '"></i>';
    }
    var marcas = '';
    [0, 20, 40, 60, 80, 100].forEach(function (v) {
      marcas += '<span class="marca" style="left:' + v + '%">' + v + ' %</span>';
    });
    return '<span class="rampa"><span class="titulo">Parte de la manzana ' +
      'cubierta</span><span class="barra-l">' + barra +
      '</span><span class="ejes">' + marcas + '</span></span>' +
      '<span class="aparte"><i class="rayada" style="background-color:' +
      'var(--gr-nada)"></i>sin cobertura</span>';
  }

  /* La barra de escala se calcula con los metros por unidad que traen los
     datos y el ancho real del viewBox. Una barra dibujada «a ojo» en una
     lámina del municipio es una mentira que alguien va a medir con regla. */
  function aparejo() {
    var fuente = vista === 'calles' ? R : M;
    var svgEl = document.getElementById(vista === 'calles' ? 'svg-red' : 'svg-mapa');
    if (!svgEl) return;
    var anchoPx = svgEl.getBoundingClientRect().width;
    if (!anchoPx) return;

    // Metros por píxel DE PANTALLA. Es el único camino honesto: el ancho de la
    // barra en porcentaje se resuelve contra el contenedor, no contra el mapa,
    // y con eso la barra decía 2,0 km midiendo 678 m. Una barra de escala es
    // justo lo que alguien va a medir con una regla sobre el papel.
    var mPorPx = (fuente.viewBox[encuadre][2] * (fuente.m_por_unidad || 1)) / anchoPx;

    // Se elige el número redondo cuya barra quede entre 70 y 170 px.
    var paso = null;
    for (var e = -1; e <= 5 && paso === null; e++) {
      var base = Math.pow(10, e);
      [1, 2, 5].forEach(function (k) {
        var px = k * base / mPorPx;
        if (paso === null && px >= 70 && px <= 170) paso = k * base;
      });
    }
    if (paso === null) paso = Math.round(mPorPx * 110);
    var anchoBarra = paso / mPorPx;
    var rotulo = paso >= 1000 ? F.N1.format(paso / 1000) + ' km' : F.N.format(paso) + ' m';

    document.getElementById('aparejo').innerHTML =
      '<span class="escala-barra" style="width:' + anchoBarra.toFixed(1) + 'px">' +
        '<span class="regla"><span></span><span></span><span></span><span></span></span>' +
        '<span class="cifras"><span>0</span><span>' + rotulo + '</span></span>' +
      '</span>' +
      '<span class="norte"><svg width="17" height="21" viewBox="0 0 17 21" ' +
        'aria-hidden="true"><path d="M8.5 0 L15 21 L8.5 15.5 L2 21 Z" ' +
        'fill="currentColor"/></svg>N</span>';
  }

  function encuadrar() {
    document.getElementById('svg-mapa')
      .setAttribute('viewBox', M.viewBox[encuadre].join(' '));
    var r = document.getElementById('svg-red');
    if (r) r.setAttribute('viewBox', R.viewBox[encuadre].join(' '));
    aparejo();
    tallarRotulos();
  }

  function cambiarVista() {
    var calles = vista === 'calles';
    if (calles) dibujarCalles();
    lienzo.classList.toggle('lienzo--noche', calles);
    var a = document.getElementById('svg-mapa');
    var b = document.getElementById('svg-red');
    a.style.display = calles ? 'none' : 'block';
    if (b) b.style.display = calles ? 'block' : 'none';
    globo.style.display = 'none';
    document.getElementById('nota-vista').innerHTML = calles
      ? 'Los <strong>' + F.N.format(R.tramos.length) + ' tramos</strong> de la ' +
        'red vial, pintados por la ' +
        'distancia en línea recta al equipamiento más cercano. <strong>Aquí no ' +
        'hay población</strong>: una calle larga y vacía pesa lo mismo que una ' +
        'del centro. Sirve para ver la forma de la ciudad, no para sacar una cifra.'
      : 'Cada manzana de Riobamba, pintada por la parte de su gente que vive a ' +
        'la distancia que manda la ordenanza. Las ' + F.N.format(M.manzanas.length) +
        ' del Censo 2022, una por una. <strong>Pasa el cursor o toca</strong> ' +
        'para ver cualquiera de ellas.';
  }

  document.getElementById('mandos').addEventListener('click', function (ev) {
    var b = ev.target.closest('.pastilla');
    if (!b) return;
    if (b.dataset.ind !== undefined) {
      elegido = +b.dataset.ind;
      this.querySelectorAll('[data-ind]').forEach(function (o) {
        o.setAttribute('aria-pressed', String(+o.dataset.ind === elegido));
      });
      pintar();
      tablaEscala();
    } else if (b.dataset.escala !== undefined) {
      escalaSel = +b.dataset.escala;
      pintarLimites();
      tablaEscala();
    } else if (b.dataset.vista !== undefined) {
      vista = b.dataset.vista;
      this.querySelectorAll('[data-vista]').forEach(function (o) {
        o.setAttribute('aria-pressed', String(o.dataset.vista === vista));
      });
      cambiarVista();
      pintar();
      pintarLimites();
      aparejo();
    } else {
      encuadre = b.dataset.enc;
      this.querySelectorAll('[data-enc]').forEach(function (o) {
        o.setAttribute('aria-pressed', String(o.dataset.enc === encuadre));
      });
      encuadrar();
    }
  });

  /* --------------------------------------------------------- el globo */
  function mirar(ev) {
    var p = ev.target.closest('.mz, .tramo-via');
    if (!p) { globo.style.display = 'none'; return; }
    if (p.classList.contains('tramo-via')) {
      var t = R.tramos[+p.dataset.i];
      var m2 = t.d[elegido];
      var ind2 = D.indicadores[elegido];
      globo.innerHTML =
        '<span class="donde">Tramo de vía</span>' +
        (m2 >= R.tope_m ? 'A más de <b>' + F.N.format(R.tope_m) + ' m</b>'
                        : 'A <b>' + F.N.format(m2) + ' m</b>') +
        ' de ' + F.esc(ind2.nombre.replace('Gente con ', '').replace(' cerca', '')) +
        '<br><span style="color:var(--gr-tinta-3)">' +
        (m2 <= ind2.radio_m ? 'Dentro' : 'Fuera') + ' de los ' +
        F.N.format(ind2.radio_m) + ' m de la ordenanza</span>';
    } else {
    var m = M.manzanas[+p.dataset.i];
    var pct = m.p[elegido];
    globo.innerHTML =
      '<span class="donde">' + F.esc((m.u && m.u[escalaSel]) ||
        ('Fuera de ' + E.escalas[escalaSel].nombre.toLowerCase())) + '</span>' +
      '<b>' + F.N.format(m.h) + '</b> habitantes<br>' +
      (pct === 0
        ? 'Sin cobertura'
        : 'Cubierta al <b>' + F.N.format(pct) + ' %</b> · alcanza a <b>' +
          F.N.format(Math.round(m.h * pct / 100)) + '</b>');
    }
    var r = caja.getBoundingClientRect();
    globo.style.display = 'block';
    // Se mantiene dentro del lienzo: pegado al borde derecho, el globo se
    // saldría de la pantalla en un teléfono.
    var x = Math.min(ev.clientX - r.left + 14, r.width - globo.offsetWidth - 8);
    globo.style.left = Math.max(8, x) + 'px';
    globo.style.top = Math.max(8, ev.clientY - r.top - globo.offsetHeight - 12) + 'px';
  }

  // En un teléfono no hay cursor, así que la misma ficha se abre al tocar.
  // Sin esto, media Riobamba —que entra desde el móvil— no vería su manzana.
  caja.addEventListener('mousemove', mirar);
  caja.addEventListener('click', mirar);
  caja.addEventListener('mouseleave', function () { globo.style.display = 'none'; });

  /* ---------------------------------------------------- las parroquias */
  function celda(v) {
    if (v.lectura === 'sin_inventario') {
      return '<td class="n"><span class="sinv">sin inventario</span></td>';
    }
    var pct = v.valor_pct || 0;
    return '<td class="n"><span class="barrita"><i style="width:' + pct + '%"></i></span>' +
      '<span class="lectura' + (v.propio ? '' : ' vecina') + '">' +
      F.N1.format(pct) + ' %</span></td>';
  }

  function tablaEscala() {
    var esc = E.escalas[escalaSel];
    E.indicadores.forEach(function (x, n) {
      var th = document.getElementById('th-' + (n + 1));
      th.style.textAlign = 'right';
      th.innerHTML = F.esc(x.nombre.replace('Gente con ', '')) +
        '<br><span style="font-weight:400">' + F.N.format(x.radio_m) + ' m</span>';
      th.classList.toggle('viva', n === elegido);
    });
    document.getElementById('th-unidad').textContent = esc.nombre.replace(/s$/, '');

    document.getElementById('filas-par').innerHTML = esc.unidades.map(function (p) {
      return '<tr>' +
        '<td><strong>' + F.esc(p.nombre) + '</strong>' +
          '<span class="campos">' + F.esc(p.sub) + ' · ' +
          F.N.format(p.manzanas) + ' manzanas' +
          (p.area_ha ? ' · ' + F.N.format(Math.round(p.area_ha)) + ' ha' : '') +
          '</span></td>' +
        '<td class="n">' + F.N.format(p.poblacion_en_manzana) + '</td>' +
        '<td class="n">' + F.N.format(p.equipamientos) + '</td>' +
        E.indicadores.map(function (x) { return celda(p.indicadores[x.clave]); }).join('') +
        '</tr>';
    }).join('');

    document.getElementById('titulo-escala').innerHTML =
      'Las ' + esc.unidades.length + ' ' + F.esc(esc.nombre.toLowerCase());
    document.getElementById('nota-escala').innerHTML =
      F.esc(esc.nota) + '. Cubre <strong>' +
      F.N.format(esc.poblacion_cubierta) + '</strong> habitantes, el ' +
      F.N1.format(esc.pct_del_total) + ' % de los ' +
      F.N.format(E.poblacion_medida) + ' que este observatorio mide' +
      (esc.sin_manzanas.length
        ? '. Sin ninguna manzana del INEC: ' + F.esc(esc.sin_manzanas.join(', '))
        : '') + '.';

    document.querySelectorAll('[data-escala]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(+b.dataset.escala === escalaSel));
    });
  }

  /* ------------------------------------------------------ las tarjetas */
  document.getElementById('tarjetas').innerHTML = D.indicadores.map(function (x, i) {
    var n = x.norma || {}, sirve = x.sin_contar_en_mal_estado || {};
    return '<article class="ind ind--' + (i + 1) + '">' +
      '<h3><span class="ico-caja">' +
        ICONOS.svg(ICONOS.deIndicador(x.clave), 22) + '</span>' +
        F.esc(x.nombre) + '</h3>' +
      '<div><p class="cifra"><b>' + F.N1.format(x.valor_pct) + '</b><span>%</span></p>' +
      '<p class="gente"><b>' + F.N.format(x.alcanzados) + '</b> de ' +
        F.N.format(x.denominador) + ' habitantes</p></div>' +
      '<div class="barra" role="img" aria-label="' + F.N1.format(x.valor_pct) +
        ' por ciento de la población"><i style="width:' +
        Math.max(0, Math.min(100, x.valor_pct)) + '%"></i></div>' +
      '<dl class="ficha">' +
        '<dt>Radio</dt><dd>' + F.N.format(x.radio_m) + ' m</dd>' +
        '<dt>Norma</dt><dd>' + F.esc(n.simbolo) + ' · ' + F.esc(n.tipologia) + '</dd>' +
        '<dt>Equipamientos</dt><dd>' + F.N.format(x.equipamientos) + '</dd>' +
        '<dt>Solo los que sirven</dt><dd>' + F.N1.format(sirve.valor_pct) + ' %</dd>' +
      '</dl>' +
      '<p class="cita">' + F.esc(n.actividades) + '.</p>' +
      '</article>';
  }).join('');

  /* -------------------------------------------------- fuentes y pie */
  var vistas = [];
  D.indicadores.forEach(function (x) {
    (x.fuentes || []).forEach(function (f) { if (vistas.indexOf(f) < 0) vistas.push(f); });
  });
  document.getElementById('fuentes').innerHTML =
    vistas.map(function (f) { return '<li>' + F.esc(f) + '</li>'; }).join('');

  document.getElementById('pie').textContent =
    'LLACTA · GADM Riobamba · indicadores generados el ' + F.fecha(D.generado) +
    ' con el método v' + D.version_metodo + '. Prototipo: ninguna cifra de aquí ' +
    'se usa en un expediente sin revisarla.';

  // La barra se recalcula al cambiar el ancho de la ventana: está en píxeles
  // medidos, así que si el mapa se estrecha y la barra no, vuelve a mentir.
  var tempo;
  window.addEventListener('resize', function () {
    clearTimeout(tempo);
    tempo = setTimeout(aparejo, 150);
  });

  cambiarVista();
  /* LOS TRES PANELES COMPARADOS.
   *
   * La misma ciudad, los tres indicadores, uno al lado del otro. Alternando
   * con las pastillas no se compara: se recuerda, y mal. Puestos en fila se
   * ve de un golpe que donde sobra escuela falta salud.
   *
   * Cada panel NO dibuja 3.756 trazos: junta los de cada escalón en un solo
   * `path`. Son siete por panel en vez de 3.756, y para una lámina de 300 px
   * sin interacción eso no quita nada y evita meter once mil nodos más en el
   * documento.
   */
  function laminaMini(cual) {
    var cubos = ['', '', '', '', '', '', ''];
    for (var k = 0; k < M.manzanas.length; k++) {
      cubos[tramo(M.manzanas[k].p[cual])] += M.manzanas[k].d;
    }
    var s = '<svg class="lamina" viewBox="' + M.viewBox.ciudad.join(' ') + '" ' +
      'role="img" aria-label="' + F.esc(D.indicadores[cual].nombre) +
      ', por manzana. La tabla de parroquias dice lo mismo en texto.">' +
      '<defs><pattern id="sc' + cual + '" width="6" height="6" ' +
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
        '<rect width="6" height="6" fill="var(--gr-nada)"/>' +
        '<line x1="0" y1="0" x2="0" y2="6" stroke="var(--gr-fondo)" ' +
        'stroke-width="2" opacity=".55"/></pattern></defs>';
    for (var b = 0; b < cubos.length; b++) {
      if (!cubos[b]) continue;
      s += '<path class="mz-l" fill="' +
        (b === 0 ? 'url(#sc' + cual + ')' : muestra(b, cual)) +
        '" d="' + cubos[b] + '"/>';
    }
    for (var q = 0; q < M.limites.parroquias.length; q++) {
      // Los paneles llevan siempre las parroquias: son la única escala que
      // dibuja el cantón entero, y una miniatura necesita el contorno
      // completo para que se reconozca de qué ciudad se habla.
      s += '<path class="par-l" d="' + M.limites.parroquias[q].d + '"/>';
    }
    return s + '</svg>';
  }

  document.getElementById('paneles').innerHTML = D.indicadores.map(function (x, i) {
    return '<article class="panel panel--' + (i + 1) + '">' +
      '<h3>' + ICONOS.svg(ICONOS.deIndicador(x.clave), 19) +
        F.esc(x.nombre.replace('Gente con ', '').replace(/^un /, '').replace(/^una /, '')) +
        '</h3>' + laminaMini(i) +
      '<p class="pie-panel"><b>' + F.N1.format(x.valor_pct) + ' %</b>' +
        '<span>' + F.N.format(x.alcanzados) + ' de ' + F.N.format(x.denominador) +
        ' hab · ' + F.N.format(x.radio_m) + ' m</span></p>' +
      '</article>';
  }).join('');

  cambiarVista();
  pintar();
  pintarLimites();   // dibuja los límites y los nombres de la escala elegida
  aparejo();
  tablaEscala();
})();

/* El seguidor de la cinta: marca en qué sección estás mientras bajas.
 *
 * Poder saltar no es navegar. Un documento largo se vuelve navegable cuando
 * además sabes dónde estás parado, y eso en una página de scroll solo lo
 * puede decir la propia página.
 *
 * Con IntersectionObserver y no escuchando el scroll: el oyente de scroll se
 * dispara decenas de veces por segundo y hace trabajo en cada una; esto solo
 * avisa cuando una sección cruza la línea.
 */
(function () {
  var saltos = [].slice.call(document.querySelectorAll('.cinta a.salto'));
  if (!saltos.length || !window.IntersectionObserver) return;

  var secciones = saltos.map(function (a) {
    return document.getElementById(a.getAttribute('href').slice(1));
  }).filter(Boolean);

  var visibles = new Set();
  function marcar() {
    var activa = null;
    for (var i = 0; i < secciones.length; i++) {
      if (visibles.has(secciones[i].id)) { activa = secciones[i].id; break; }
    }
    saltos.forEach(function (a) {
      var suya = a.getAttribute('href').slice(1) === activa;
      if (suya) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  var vigia = new IntersectionObserver(function (entradas) {
    entradas.forEach(function (e) {
      if (e.isIntersecting) visibles.add(e.target.id);
      else visibles.delete(e.target.id);
    });
    marcar();
  }, {
    // La franja útil es la mitad de arriba de la pantalla: una sección se
    // considera «donde estás» cuando su título ya pasó la barra y todavía no
    // se fue por abajo.
    rootMargin: '-62px 0px -55% 0px',
    threshold: 0
  });
  secciones.forEach(function (s) { vigia.observe(s); });
})();
