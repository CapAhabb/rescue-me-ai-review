const layerButtons = Array.from(document.querySelectorAll("[data-layer]"));
const mission = document.querySelector("#mission");
const assessment = document.querySelector("#assessment");
const statusText = document.querySelector("#status");
const waterMetric = document.querySelector("#waterMetric");
const windMetric = document.querySelector("#windMetric");
const depthMetric = document.querySelector("#depthMetric");
const map = document.querySelector("#map");
const bathymetryLayer = document.querySelector("#bathymetryLayer");
const bathymetryStatus = document.querySelector("#bathymetryStatus");

const bathymetrySources = {
  contours: "./data/noaa_lake_michigan_bathymetry_contours.geojson",
  shoreline: "./data/lake_michigan_shoreline.geojson"
};

const chartViewport = {
  width: 1000,
  height: 620
};

const missionCopy = {
  shoreline: {
    status: "Guarded",
    severity: "guarded",
    summary: "Prioritize shoreline sweep lanes and recent sighting points.",
    actions: ["Assign nearshore grid teams", "Mark last-known point", "Keep weather and water layers active"]
  },
  vessel: {
    status: "Elevated",
    severity: "elevated",
    summary: "Use wind, wave, and current drift assumptions before widening search.",
    actions: ["Plot likely drift corridor", "Stage asset handoff point", "Refresh buoy observations"]
  },
  weather: {
    status: "Elevated",
    severity: "elevated",
    summary: "Weather movement can close safe operating windows quickly.",
    actions: ["Set time checkpoints", "Identify shelter locations", "Keep wind and weather layers active"]
  },
  exposure: {
    status: "Critical",
    severity: "critical",
    summary: "Cold-water exposure risk is time sensitive and should drive routing.",
    actions: ["Shorten search intervals", "Prioritize thermal risk zones", "Prepare medical handoff"]
  }
};

function activeLayers() {
  return layerButtons
    .filter((button) => button.classList.contains("active"))
    .map((button) => button.dataset.layer);
}

async function renderAssessment() {
  const active = activeLayers();
  const copy = missionCopy[mission.value];
  const supportingSignals = active.length ? active.join(", ") : "none selected";

  statusText.textContent = copy.status;
  waterMetric.textContent = "N/A";
  windMetric.textContent = "N/A";
  assessment.innerHTML = `
    <strong>${copy.severity.toUpperCase()}</strong>
    <span>${copy.summary}</span>
    <span>Actions: ${copy.actions.join("; ")}.</span>
    <span>Supporting signals: ${supportingSignals}.</span>
    <span>Weather, water, wind, and drift feeds are not connected in this static console.</span>
    <span>Bathymetry uses local NOAA Lake Michigan contour and shoreline GeoJSON.</span>
  `;
}

function syncMapLayers() {
  const active = new Set(activeLayers());
  ["assets", "weather", "water", "wind", "currents", "notes", "bathymetry"].forEach((layer) => {
    map.classList.toggle(`hide-${layer}`, !active.has(layer));
  });
}

async function loadBathymetry() {
  try {
    const [contours, shoreline] = await Promise.all([
      fetchJson(bathymetrySources.contours),
      fetchJson(bathymetrySources.shoreline)
    ]);
    renderBathymetry(contours, shoreline);
  } catch (error) {
    bathymetryStatus.textContent = "Bathymetry file load failed";
    depthMetric.textContent = "ERR";
    console.error(error);
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Unable to load ${url}: ${response.status}`);
  }

  return response.json();
}

function renderBathymetry(contours, shoreline) {
  const features = [
    ...validFeatures(contours),
    ...validFeatures(shoreline)
  ];
  const bounds = coordinateBounds(features);
  const fragment = document.createDocumentFragment();

  validFeatures(shoreline).forEach((feature) => {
    pathsForGeometry(feature.geometry, bounds).forEach((pathData) => {
      const path = svgPath(pathData, "bathy-shoreline");
      fragment.append(path);
    });
  });

  validFeatures(contours)
    .slice()
    .sort((a, b) => Number(a.properties?.depth ?? 0) - Number(b.properties?.depth ?? 0))
    .forEach((feature) => {
      const depth = Number(feature.properties?.depth ?? 0);
      const classes = ["bathy-contour"];
      if (depth % 50 === 0) classes.push("major");
      if (depth >= 150) classes.push("deep");

      pathsForGeometry(feature.geometry, bounds).forEach((pathData) => {
        const path = svgPath(pathData, classes.join(" "));
        path.dataset.depthMeters = String(depth);
        fragment.append(path);
      });
    });

  bathymetryLayer.replaceChildren(fragment);

  const depths = validFeatures(contours)
    .map((feature) => Number(feature.properties?.depth))
    .filter((depth) => Number.isFinite(depth));
  const minDepth = Math.min(...depths);
  const maxDepth = Math.max(...depths);

  depthMetric.textContent = `${minDepth}-${maxDepth} m`;
  bathymetryStatus.textContent =
    `NOAA Lake Michigan bathymetry: ${validFeatures(contours).length.toLocaleString()} contours, ${minDepth}-${maxDepth} m`;
}

function validFeatures(collection) {
  return Array.isArray(collection?.features)
    ? collection.features.filter((feature) => feature?.geometry)
    : [];
}

function coordinateBounds(features) {
  const bounds = {
    minLon: Infinity,
    minLat: Infinity,
    maxLon: -Infinity,
    maxLat: -Infinity
  };

  features.forEach((feature) => {
    walkCoordinates(feature.geometry.coordinates, (coordinate) => {
      const [lon, lat] = coordinate;
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) return;
      bounds.minLon = Math.min(bounds.minLon, lon);
      bounds.minLat = Math.min(bounds.minLat, lat);
      bounds.maxLon = Math.max(bounds.maxLon, lon);
      bounds.maxLat = Math.max(bounds.maxLat, lat);
    });
  });

  if (!Number.isFinite(bounds.minLon)) {
    throw new Error("Bathymetry files contain no usable coordinates");
  }

  return bounds;
}

function walkCoordinates(coordinates, visitor) {
  if (!Array.isArray(coordinates)) return;

  if (typeof coordinates[0] === "number" && typeof coordinates[1] === "number") {
    visitor(coordinates);
    return;
  }

  coordinates.forEach((child) => walkCoordinates(child, visitor));
}

function pathsForGeometry(geometry, bounds) {
  if (geometry.type === "LineString") {
    return [linePath(geometry.coordinates, bounds)];
  }

  if (geometry.type === "MultiLineString") {
    return geometry.coordinates.map((line) => linePath(line, bounds));
  }

  if (geometry.type === "Polygon") {
    return [polygonPath(geometry.coordinates, bounds)];
  }

  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.map((polygon) => polygonPath(polygon, bounds));
  }

  return [];
}

function linePath(line, bounds) {
  return line
    .map((coordinate, index) => {
      const point = projectCoordinate(coordinate, bounds);
      return `${index === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
    })
    .join(" ");
}

function polygonPath(rings, bounds) {
  return rings
    .map((ring) => `${linePath(ring, bounds)} Z`)
    .join(" ");
}

function projectCoordinate(coordinate, bounds) {
  const [lon, lat] = coordinate;
  const x = ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * chartViewport.width;
  const y = chartViewport.height -
    ((lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * chartViewport.height;

  return { x, y };
}

function svgPath(pathData, className) {
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathData);
  path.setAttribute("class", className);
  return path;
}

layerButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.disabled) return;
    button.classList.toggle("active");
    syncMapLayers();
    renderAssessment();
  });
});

mission.addEventListener("change", renderAssessment);

syncMapLayers();
renderAssessment();
loadBathymetry();
