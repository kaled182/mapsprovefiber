// Reutilizável para embutir mapa de fibras em qualquer página
(function(global){
  const STATUS_COLORS = {
    up: '#16a34a',
    down: '#dc2626',
    degraded: '#f59e0b',
    unknown: '#6b7280'
  };
  function loadJSON(url){ return fetch(url, {headers:{'X-Requested-With':'XMLHttpRequest'}}).then(r=>r.json()); }

  function initFiberMap(opts){
    const el = document.getElementById(opts.elementId || 'fiberMap');
    if(!el){ console.warn('Elemento mapa não encontrado'); return; }
    const map = new google.maps.Map(el, {center: {lat: -16.6869, lng: -49.2648}, zoom: 6, mapTypeId:'terrain'});

    const legend = document.createElement('div');
    legend.className='bg-white rounded shadow text-xs p-2 space-y-1';
    legend.innerHTML = Object.entries(STATUS_COLORS).map(([k,v]) => `<div class='flex items-center gap-2'><span style='background:${v};width:18px;height:4px;border-radius:2px;display:inline-block'></span>${k}</div>`).join('');
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);

    Promise.all([
      loadJSON(opts.fibersUrl),
      loadJSON(opts.sitesUrl)
    ]).then(([fibersResp, sitesResp]) => {
      // Sites
      sitesResp.sites.forEach(s => {
        if(s.lat == null) return;
        const marker = new google.maps.Marker({position:{lat:s.lat,lng:s.lng}, map, title:s.name});
        const iw = new google.maps.InfoWindow({content:`<strong>${s.name}</strong><br>${s.city||''}`});
        marker.addListener('click',()=> iw.open(map, marker));
      });
      // Fibras
      fibersResp.cables.forEach(c => {
        let path = [];
        if(c.path && c.path.length){ path = c.path.map(p=>({lat:p.lat,lng:p.lng})); }
        else if(c.origin.lat!=null && c.destination.lat!=null){
          path = [{lat:c.origin.lat,lng:c.origin.lng},{lat:c.destination.lat,lng:c.destination.lng}];
        }
        if(!path.length) return;
        const poly = new google.maps.Polyline({path, map, strokeColor: STATUS_COLORS[c.status]||STATUS_COLORS.unknown, strokeWeight: 4, strokeOpacity:.85});
        const info = new google.maps.InfoWindow({content:`<strong>${c.name}</strong><br>Status: ${c.status}<br>${c.origin.site} (${c.origin.port}) ➜ ${c.destination.site} (${c.destination.port})`});
        poly.addListener('click', e => { info.setPosition(e.latLng); info.open(map); });
      });
    }).catch(err => console.error('Erro carregando dados do mapa:', err));
  }
  global.FiberMapEmbed = { initFiberMap };
})(window);
