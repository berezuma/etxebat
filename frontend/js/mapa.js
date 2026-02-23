/**
 * Etxebat - Euskadiko Higiezinen Mapa Estrategikoa
 * Leaflet.js mapa koropletikoa: udalerrien higiezin-datuak bistaratzeko.
 */

(function () {
  "use strict";

  // Euskadiko erdigunea eta zoom maila
  var EUSKADI_ERDIGUNEA = [43.0, -2.5];
  var HASIERAKO_ZOOM = 9;

  // Kolore-eskala (prezio baxutik alturaino)
  var KOLOREAK = ["#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#0c2c84"];
  var MUGAK_EURO_M2 = [0, 1000, 1500, 2000, 2500, 3000, 4000];

  // Geruza motak
  var GERUZA_MOTAK = {
    salmenta_euro_m2: {
      izena: "Salmenta (€/m²)",
      eremua: "salmenta_euro_m2",
      formatua: function (b) { return b ? b.toLocaleString("eu") + " €/m²" : "—"; },
      mugak: MUGAK_EURO_M2,
      koloreak: KOLOREAK,
    },
    salmenta_prezioa: {
      izena: "Salmenta prezioa (€)",
      eremua: "salmenta_prezioa",
      formatua: function (b) { return b ? b.toLocaleString("eu") + " €" : "—"; },
      mugak: [0, 100000, 150000, 200000, 250000, 300000, 400000],
      koloreak: KOLOREAK,
    },
    alokairu_errenta: {
      izena: "Alokairua (€/hil)",
      eremua: "alokairu_errenta",
      formatua: function (b) { return b ? b.toLocaleString("eu") + " €/hil" : "—"; },
      mugak: [0, 400, 600, 800, 1000, 1200, 1500],
      koloreak: KOLOREAK,
    },
    salmenta_aldakuntza_pct: {
      izena: "Salmenta Δ%",
      eremua: "salmenta_aldakuntza_pct",
      formatua: function (b) { return b !== null && b !== undefined ? b.toFixed(1) + " %" : "—"; },
      mugak: [-10, -5, -2, 0, 2, 5, 10],
      koloreak: ["#d73027", "#fc8d59", "#fee08b", "#ffffbf", "#d9ef8b", "#91cf60", "#1a9850"],
    },
  };

  var unekoa = "salmenta_euro_m2";
  var mapa, geojsonGeruza, legenda, infoPanela, geruzaKontrola;
  var geojsonDatuak = null;

  // Mapa sortu
  function mapaHasieratu() {
    mapa = L.map("mapa", {
      center: EUSKADI_ERDIGUNEA,
      zoom: HASIERAKO_ZOOM,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 18,
    }).addTo(mapa);

    legendaSortu();
    infoPanelaSortu();
    geruzaKontrolaSortu();
    datuakKargatu();
  }

  // Kolore-funtzioa
  function koloreaBalioarekin(balioa, conf) {
    if (balioa === null || balioa === undefined || isNaN(balioa)) return "#cccccc";
    var mugak = conf.mugak;
    var koloreak = conf.koloreak;
    for (var i = mugak.length - 1; i >= 0; i--) {
      if (balioa >= mugak[i]) return koloreak[i];
    }
    return koloreak[0];
  }

  // Estiloa
  function estiloaLortu(feature) {
    var conf = GERUZA_MOTAK[unekoa];
    var balioa = feature.properties[conf.eremua];
    return {
      fillColor: koloreaBalioarekin(balioa, conf),
      weight: 1,
      opacity: 1,
      color: "#666",
      fillOpacity: 0.7,
    };
  }

  // Feature bakoitzeko interakzioa
  function interakzioaGehitu(feature, layer) {
    layer.on({
      mouseover: function (e) {
        var geruza = e.target;
        geruza.setStyle({ weight: 3, color: "#333", fillOpacity: 0.85 });
        geruza.bringToFront();
        infoPanelaEguneratu(feature.properties);
      },
      mouseout: function (e) {
        geojsonGeruza.resetStyle(e.target);
        infoPanelaGarbitu();
      },
      click: function (e) {
        mapa.fitBounds(e.target.getBounds());
        popupErakutsi(e.target, feature.properties);
      },
    });
  }

  // Popup edukia sortu
  function popupErakutsi(layer, props) {
    var izena = props.iz_ofizial || props.udalerri_normalizatua || props.NOMBRE_MUNICIPIO || props.nombre || "Ezezaguna";

    var html = '<h3>' + eskatu(izena) + '</h3>';
    html += '<div class="popup-datuak">';

    // Salmenta sekzioa
    if (props.salmenta_prezioa || props.salmenta_euro_m2) {
      html += '<div class="popup-sekzioa"><h4>Salmenta</h4>';
      if (props.salmenta_euro_m2) {
        html += lerroa("€/m²", props.salmenta_euro_m2.toLocaleString("eu") + " €");
      }
      if (props.salmenta_prezioa) {
        html += lerroa("Batez bestekoa", props.salmenta_prezioa.toLocaleString("eu") + " €");
      }
      if (props.salmenta_aldakuntza_pct !== null && props.salmenta_aldakuntza_pct !== undefined) {
        var klaseaS = props.salmenta_aldakuntza_pct >= 0 ? "gorantz" : "beherantz";
        html += lerroa("Δ urtekoa", '<span class="' + klaseaS + '">' + props.salmenta_aldakuntza_pct.toFixed(1) + " %</span>");
      }
      html += "</div>";
    }

    // Alokairu sekzioa
    if (props.alokairu_errenta) {
      html += '<div class="popup-sekzioa"><h4>Alokairua</h4>';
      html += lerroa("Errenta", props.alokairu_errenta.toLocaleString("eu") + " €/hil");
      if (props.alokairu_aldakuntza_pct !== null && props.alokairu_aldakuntza_pct !== undefined) {
        var klaseaA = props.alokairu_aldakuntza_pct >= 0 ? "gorantz" : "beherantz";
        html += lerroa("Δ urtekoa", '<span class="' + klaseaA + '">' + props.alokairu_aldakuntza_pct.toFixed(1) + " %</span>");
      }
      html += "</div>";
    }

    // Daturik ez bada
    if (!props.salmenta_prezioa && !props.salmenta_euro_m2 && !props.alokairu_errenta) {
      html += '<div style="color:#999;font-style:italic;">Daturik ez</div>';
    }

    html += "</div>";
    layer.bindPopup(html, { maxWidth: 280 }).openPopup();
  }

  function lerroa(etiketa, balioa) {
    return '<div class="lerroa"><span class="etiketa">' + etiketa + '</span><span class="balioa">' + balioa + "</span></div>";
  }

  function eskatu(testua) {
    var div = document.createElement("div");
    div.textContent = testua;
    return div.innerHTML;
  }

  // Legenda
  function legendaSortu() {
    legenda = L.control({ position: "bottomright" });
    legenda.onAdd = function () {
      var div = L.DomUtil.create("div", "legenda");
      legendaEguneratu(div);
      return div;
    };
    legenda.addTo(mapa);
  }

  function legendaEguneratu(container) {
    var conf = GERUZA_MOTAK[unekoa];
    if (!container) container = document.querySelector(".legenda");
    if (!container) return;

    var html = "<h4>" + conf.izena + "</h4>";
    for (var i = 0; i < conf.mugak.length; i++) {
      var hurrengoMuga = conf.mugak[i + 1];
      var etiketa = conf.mugak[i].toLocaleString("eu");
      if (hurrengoMuga !== undefined) {
        etiketa += " – " + hurrengoMuga.toLocaleString("eu");
      } else {
        etiketa += "+";
      }
      html += '<div><i style="background:' + conf.koloreak[i] + '"></i> ' + etiketa + "</div>";
    }
    html += '<div><i style="background:#cccccc"></i> Daturik ez</div>';
    container.innerHTML = html;
  }

  // Informazio panela (hover)
  function infoPanelaSortu() {
    infoPanela = L.control({ position: "topright" });
    infoPanela.onAdd = function () {
      var div = L.DomUtil.create("div", "info-panela");
      div.innerHTML = "<h4>Udalerria hautatu</h4><span>Pasatu sagua udalerri baten gainetik</span>";
      return div;
    };
    infoPanela.addTo(mapa);
  }

  function infoPanelaEguneratu(props) {
    var container = document.querySelector(".info-panela");
    if (!container) return;

    var conf = GERUZA_MOTAK[unekoa];
    var izena = props.iz_ofizial || props.udalerri_normalizatua || props.NOMBRE_MUNICIPIO || props.nombre || "—";
    var balioa = props[conf.eremua];

    var html = "<h4>" + eskatu(izena) + "</h4>";
    html += '<div><span class="etiketa">' + conf.izena + ": </span>";
    html += '<span class="balioa">' + conf.formatua(balioa) + "</span></div>";

    container.innerHTML = html;
  }

  function infoPanelaGarbitu() {
    var container = document.querySelector(".info-panela");
    if (container) {
      container.innerHTML = "<h4>Udalerria hautatu</h4><span>Pasatu sagua udalerri baten gainetik</span>";
    }
  }

  // Geruza kontrola (radio botoiak)
  function geruzaKontrolaSortu() {
    geruzaKontrola = L.control({ position: "topleft" });
    geruzaKontrola.onAdd = function () {
      var div = L.DomUtil.create("div", "geruza-kontrola");
      L.DomEvent.disableClickPropagation(div);

      var html = "";
      var gakoak = Object.keys(GERUZA_MOTAK);
      for (var i = 0; i < gakoak.length; i++) {
        var gakoa = gakoak[i];
        var conf = GERUZA_MOTAK[gakoa];
        var hautatua = gakoa === unekoa ? " checked" : "";
        html += '<label><input type="radio" name="geruza" value="' + gakoa + '"' + hautatua + "> " + conf.izena + "</label>";
      }
      div.innerHTML = html;

      div.addEventListener("change", function (e) {
        if (e.target.name === "geruza") {
          unekoa = e.target.value;
          geruzaEguneratu();
        }
      });

      return div;
    };
    geruzaKontrola.addTo(mapa);
  }

  // Geruza eguneratu (mota aldatzean)
  function geruzaEguneratu() {
    if (geojsonGeruza) {
      geojsonGeruza.setStyle(estiloaLortu);
    }
    legendaEguneratu();
    infoPanelaGarbitu();
  }

  // Datuak kargatu (fitxategi estatikotik edo API-tik)
  function datuakKargatu() {
    // GitHub Pages-en bide erlatiboa erabili; bestela API-a
    var script = document.currentScript || document.querySelector('script[src*="mapa.js"]');
    var basePath = "";
    if (script && script.src) {
      // mapa.js frontend/js/ karpetan dago; datuak/ erroan dago
      basePath = script.src.replace(/frontend\/js\/mapa\.js.*$/, "");
    }
    var url = basePath + "datuak/udalerri_datuak.geojson";
    fetch(url)
      .then(function (erantzuna) {
        if (!erantzuna.ok) throw new Error("GeoJSON kargatzean errorea: " + erantzuna.status);
        return erantzuna.json();
      })
      .then(function (geojson) {
        geojsonDatuak = geojson;
        geojsonGeruza = L.geoJSON(geojson, {
          style: estiloaLortu,
          onEachFeature: interakzioaGehitu,
        }).addTo(mapa);

        // Mugak egokitu datuetara
        if (geojsonGeruza.getBounds().isValid()) {
          mapa.fitBounds(geojsonGeruza.getBounds(), { padding: [20, 20] });
        }

        kargaPantailaEzkutatu();
      })
      .catch(function (errorea) {
        console.error("Errorea datuak kargatzen:", errorea);
        kargaPantailaErrorea(errorea.message);
      });
  }

  // Karga pantaila kudeatu
  function kargaPantailaEzkutatu() {
    var pantaila = document.getElementById("karga-pantaila");
    if (pantaila) {
      pantaila.classList.add("ezkutatua");
      setTimeout(function () {
        pantaila.style.display = "none";
      }, 500);
    }
  }

  function kargaPantailaErrorea(mezua) {
    var pantaila = document.getElementById("karga-pantaila");
    if (pantaila) {
      pantaila.innerHTML =
        '<div style="text-align:center;max-width:400px;padding:20px;">' +
        "<h3>Datuak ez daude eskuragarri</h3>" +
        "<p>ETL prozesua exekutatu behar da datuak kargatzeko.</p>" +
        '<p style="font-size:0.8em;color:#a0a0c0;">' + eskatu(mezua) + "</p>" +
        "</div>";
    }
  }

  // Hasieratu dokumentua prest dagoenean
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mapaHasieratu);
  } else {
    mapaHasieratu();
  }
})();
