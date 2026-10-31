document.addEventListener("DOMContentLoaded", () => {
  const mapNode = document.getElementById("agro-map");
  const status = document.getElementById("mapStatus");
  const startButton = document.getElementById("startDrawing");
  const undoButton = document.getElementById("undoPoint");
  const clearButton = document.getElementById("clearDrawing");
  const saveButton = document.getElementById("saveField");
  const coordinatesInput = document.getElementById("fieldCoordinates");
  const propertySelect = document.getElementById("fieldProperty");
  const nameInput = document.getElementById("fieldName");
  const areaPreview = document.getElementById("areaPreview");
  const locateButton = document.getElementById("locateMe");
  const placeSearchForm = document.getElementById("placeSearchForm");
  const placeSearchInput = document.getElementById("placeSearchInput");
  const placeSearchButton = document.getElementById("placeSearchButton");
  const showWorldButton = document.getElementById("showWorld");

  if (!mapNode || !status) return;
  if (!window.L) {
    status.textContent = "O mapa não carregou. Verifique a conexão com a internet e atualize a página.";
    status.classList.add("map-status-error");
    return;
  }

  const map = window.L.map(mapNode, {
    minZoom: 0,
    maxZoom: 19,
    scrollWheelZoom: true,
    worldCopyJump: true,
  }).setView([-13.85, -40.08], 14);
  const tileLayer = window.L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a> '
        + '— Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
    },
  );
  const streetLayer = window.L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>',
    },
  );
  let activeBaseLayer = tileLayer;
  const readyMessage = !propertySelect || propertySelect.disabled
    ? "Mapa pronto. Cadastre uma propriedade para começar a desenhar talhões."
    : "Mapa pronto. Selecione uma propriedade para desenhar um talhão.";
  const watchTileLayer = (layer, errorMessage) => {
    let layerHasLoaded = false;
    layer.on("tileload", () => {
      layerHasLoaded = true;
      if (activeBaseLayer !== layer) return;
      status.textContent = readyMessage;
      status.classList.remove("map-status-error");
    });
    layer.on("tileerror", () => {
      if (activeBaseLayer !== layer || layerHasLoaded) return;
      status.textContent = errorMessage;
      status.classList.add("map-status-error");
    });
  };
  watchTileLayer(
    tileLayer,
    "As imagens de satélite não carregaram. Verifique a conexão ou escolha o mapa de ruas.",
  );
  watchTileLayer(
    streetLayer,
    "O mapa de ruas não carregou. Verifique a conexão ou escolha o mapa de satélite.",
  );
  tileLayer.addTo(map);
  const layerControl = window.L.control.layers(
    { "Satélite": tileLayer, "Ruas": streetLayer },
    null,
    { position: "topright", collapsed: true },
  ).addTo(map);
  const layerControlButton = layerControl
    .getContainer()
    .querySelector(".leaflet-control-layers-toggle");
  layerControlButton?.setAttribute("title", "Alterar visualização do mapa");
  layerControlButton?.setAttribute("aria-label", "Alterar visualização do mapa");
  map.on("baselayerchange", event => {
    activeBaseLayer = event.layer;
    status.textContent = `Visualização de ${event.name.toLowerCase()} ativada.`;
    status.classList.remove("map-status-error");
  });

  const savedFieldsNode = document.getElementById("saved-fields-data");
  let savedFields = [];
  try {
    savedFields = JSON.parse(savedFieldsNode?.textContent || "[]");
  } catch {
    status.textContent = "Não foi possível carregar os talhões salvos.";
    status.classList.add("map-status-error");
  }

  const savedLayers = [];
  savedFields.forEach(field => {
    if (!Array.isArray(field.coordinates) || field.coordinates.length < 3) return;
    const polygon = window.L.polygon(field.coordinates, {
      color: "#35d184",
      fillColor: "#20a960",
      fillOpacity: 0.35,
      weight: 3,
    }).addTo(map);
    polygon.bindPopup(
      `<strong>${escapeHtml(field.name)}</strong><br>${escapeHtml(field.property)}`
      + `<br>${escapeHtml(field.culture || "Cultura não informada")}`
      + `<br>${escapeHtml(field.area)} ha`,
    );
    savedLayers.push(polygon);
  });

  if (savedLayers.length) {
    const group = window.L.featureGroup(savedLayers);
    map.fitBounds(group.getBounds().pad(0.2), { maxZoom: 16 });
  }
  window.setTimeout(() => map.invalidateSize(), 100);

  let drawing = false;
  let points = [];
  let markers = [];
  let previewPolygon = null;

  const approximateAreaHectares = coordinates => {
    const earthRadiusMeters = 6378137;
    let ringSum = 0;
    coordinates.forEach((point, index) => {
      const next = coordinates[(index + 1) % coordinates.length];
      ringSum += (next.lng - point.lng) * Math.PI / 180 * (
        2
        + Math.sin(point.lat * Math.PI / 180)
        + Math.sin(next.lat * Math.PI / 180)
      );
    });
    return Math.abs(ringSum) * earthRadiusMeters ** 2 / 2 / 10000;
  };

  const updateFormState = () => {
    if (
      !undoButton
      || !clearButton
      || !saveButton
      || !coordinatesInput
      || !propertySelect
      || !nameInput
      || !areaPreview
    ) return;
    const hasValidPolygon = points.length >= 3;
    undoButton.disabled = points.length === 0;
    clearButton.disabled = points.length === 0;
    saveButton.disabled = !hasValidPolygon
      || !propertySelect.value
      || !nameInput.value.trim();
    coordinatesInput.value = hasValidPolygon
      ? JSON.stringify(points.map(point => [point.lat, point.lng]))
      : "";
    areaPreview.textContent = hasValidPolygon
      ? `Área aproximada: ${approximateAreaHectares(points).toFixed(2)} ha`
      : `${points.length}/3 pontos marcados para formar o limite.`;
  };

  const redrawPreview = () => {
    markers.forEach(marker => marker.remove());
    markers = points.map((point, index) => window.L.circleMarker(point, {
      radius: index === 0 ? 7 : 5,
      color: "#041a10",
      weight: 2,
      fillColor: index === 0 ? "#ffc85a" : "#51ed9a",
      fillOpacity: 1,
    }).addTo(map));

    if (previewPolygon) previewPolygon.remove();
    previewPolygon = points.length >= 3
      ? window.L.polygon(points, {
        color: "#ffc85a",
        fillColor: "#e5a82f",
        fillOpacity: 0.3,
        dashArray: "7 5",
        weight: 3,
      }).addTo(map)
      : null;

    updateFormState();
  };

  const resetDrawing = () => {
    drawing = false;
    points = [];
    redrawPreview();
    startButton.innerHTML = '<svg class="ico ico-lead" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>Desenhar talhão';
    map.getContainer().style.cursor = "";
    status.textContent = "Desenho apagado. Inicie novamente ou escolha um talhão salvo.";
  };

  const addDrawingPoint = event => {
    if (!drawing) return;
    points.push(event.latlng);
    redrawPreview();
    status.textContent = points.length >= 3
      ? "Limite desenhado. Confira o nome e a propriedade antes de salvar."
      : `${points.length} ponto(s) marcado(s). Continue clicando para fechar o limite.`;
  };

  startButton?.addEventListener("click", () => {
    if (!propertySelect?.value) {
      status.textContent = "Selecione uma propriedade antes de desenhar o talhão.";
      propertySelect.focus();
      return;
    }
    points = [];
    drawing = true;
    redrawPreview();
    startButton.textContent = "Marque os pontos no mapa";
    status.textContent = map.getZoom() < 12
      ? "Aproxime o mapa da área da fazenda antes de marcar os vértices. São necessários pelo menos 3 pontos."
      : "Clique no mapa para marcar os vértices. São necessários pelo menos 3 pontos.";
    map.getContainer().style.cursor = "crosshair";
  });

  map.on("click", addDrawingPoint);
  savedLayers.forEach(layer => {
    layer.on("click", event => {
      if (!drawing) return;
      event.target.closePopup();
      window.L.DomEvent.stopPropagation(event);
      addDrawingPoint(event);
    });
  });

  undoButton?.addEventListener("click", () => {
    points.pop();
    redrawPreview();
    status.textContent = "Último ponto removido.";
  });
  clearButton?.addEventListener("click", resetDrawing);
  propertySelect?.addEventListener("change", updateFormState);
  nameInput?.addEventListener("input", updateFormState);

  let lastPlaceSearchAt = 0;
  let searchMarker = null;
  placeSearchForm?.addEventListener("submit", async event => {
    event.preventDefault();
    const query = placeSearchInput.value.trim();
    if (!query || placeSearchButton.disabled) return;

    placeSearchButton.disabled = true;
    placeSearchButton.textContent = "Buscando...";
    status.classList.remove("map-status-error");
    status.textContent = `Buscando “${query}” no mapa...`;

    try {
      const wait = Math.max(0, 1000 - (Date.now() - lastPlaceSearchAt));
      if (wait) await new Promise(resolve => window.setTimeout(resolve, wait));
      lastPlaceSearchAt = Date.now();

      const params = new URLSearchParams({
        format: "jsonv2",
        limit: "1",
        q: query,
      });
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params}`,
        { headers: { "Accept-Language": "pt-BR" } },
      );
      if (!response.ok) {
        throw new Error(`O serviço de busca respondeu com erro (${response.status}).`);
      }

      const [place] = await response.json();
      const latitude = Number(place?.lat);
      const longitude = Number(place?.lon);
      if (
        !place
        || !Number.isFinite(latitude)
        || !Number.isFinite(longitude)
        || Math.abs(latitude) > 90
        || Math.abs(longitude) > 180
      ) {
        status.textContent = "Local não encontrado. Tente informar cidade, estado e país.";
        return;
      }

      const bounds = place.boundingbox?.map(Number);
      if (
        bounds?.length === 4
        && bounds.every(Number.isFinite)
        && bounds[0] <= bounds[1]
        && bounds[2] <= bounds[3]
      ) {
        map.fitBounds(
          [[bounds[0], bounds[2]], [bounds[1], bounds[3]]],
          { maxZoom: 15 },
        );
      } else {
        map.setView([latitude, longitude], 14);
      }

      searchMarker?.remove();
      searchMarker = window.L.marker([latitude, longitude]).addTo(map);
      const placeLabel = document.createElement("span");
      placeLabel.textContent = place.display_name;
      searchMarker.bindPopup(placeLabel).openPopup();
      status.textContent = `Mapa centralizado em ${place.display_name}. Aproxime para marcar o talhão.`;
    } catch (error) {
      status.textContent = "Não foi possível buscar esse local. Verifique a conexão e tente novamente.";
      status.classList.add("map-status-error");
      console.error("Erro ao buscar localização no mapa:", error);
    } finally {
      placeSearchButton.disabled = false;
      placeSearchButton.textContent = "Buscar local";
    }
  });

  showWorldButton?.addEventListener("click", () => {
    map.setView([0, 0], 0);
    status.classList.remove("map-status-error");
    status.textContent = "Visão mundial. Busque uma cidade ou aproxime e arraste o mapa até a área desejada.";
  });

  locateButton?.addEventListener("click", () => {
    status.textContent = "Solicitando acesso à sua localização...";
    map.locate({ setView: true, maxZoom: 16, enableHighAccuracy: true });
  });
  map.on("locationfound", event => {
    window.L.circleMarker(event.latlng, {
      radius: 8,
      color: "#071a10",
      fillColor: "#51ed9a",
      fillOpacity: 1,
      weight: 3,
    }).addTo(map).bindPopup("Sua localização aproximada").openPopup();
    status.textContent = "Mapa centralizado na sua localização.";
  });
  map.on("locationerror", () => {
    status.textContent = "Não foi possível acessar a localização. Confira a permissão do navegador.";
    status.classList.add("map-status-error");
  });

  document.getElementById("fieldForm")?.addEventListener("submit", event => {
    updateFormState();
    if (saveButton.disabled) {
      event.preventDefault();
      status.textContent = "Escolha a propriedade, informe o nome e desenhe um limite com pelo menos 3 pontos.";
      status.classList.add("map-status-error");
      return;
    }
    saveButton.disabled = true;
    saveButton.textContent = "Salvando...";
  });

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, character => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[character]);
  }

  updateFormState();
});
