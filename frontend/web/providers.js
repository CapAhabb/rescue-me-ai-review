/**
 * EnvironmentalProvider contract.
 *
 * Implementations must return normalized EnvironmentalState records. The
 * prediction core must not depend on NOAA, NWS, USGS, hosted ERDDAP, or local
 * sensor response details.
 */
export class EnvironmentalProvider {
  async getWind() {
    throw new Error("getWind() is not implemented");
  }

  async getCurrent() {
    throw new Error("getCurrent() is not implemented");
  }

  async getWaveHeight() {
    throw new Error("getWaveHeight() is not implemented");
  }

  async getWaveDirection() {
    throw new Error("getWaveDirection() is not implemented");
  }

  async getWaterTemperature() {
    throw new Error("getWaterTemperature() is not implemented");
  }

  async getRiverDischarge() {
    throw new Error("getRiverDischarge() is not implemented");
  }

  async getVisibility() {
    throw new Error("getVisibility() is not implemented");
  }

  async getForecast() {
    throw new Error("getForecast() is not implemented");
  }
}

export class MockEnvironmentalProvider extends EnvironmentalProvider {
  constructor(fixtureUrl = "./fixtures/signals.mock.json") {
    super();
    this.fixtureUrl = fixtureUrl;
  }

  async getWind() {
    const points = await this.loadPoints();
    return stateFromPoints("mock-erddap", "wind", points, "wind_speed");
  }

  async getWaveHeight() {
    const points = await this.loadPoints();
    return stateFromPoints("mock-erddap", "wave-height", points, "wave_height");
  }

  async getWaterTemperature() {
    const points = await this.loadPoints();
    return stateFromPoints("mock-erddap", "water-temperature", points, "water_temperature");
  }

  async getCurrent() {
    const points = await this.loadPoints();
    return stateFromPoints("mock-erddap", "current", points, "wind_speed");
  }

  async getWaveDirection() {
    return emptyState("mock-erddap", "wave-direction");
  }

  async getRiverDischarge() {
    return emptyState("mock-erddap", "river-discharge");
  }

  async getVisibility() {
    return emptyState("mock-erddap", "visibility");
  }

  async getForecast() {
    return emptyState("mock-erddap", "forecast");
  }

  async loadPoints() {
    const response = await fetch(this.fixtureUrl);
    const erddapTable = await response.json();
    return normalizeErddapTable(erddapTable, "mock-erddap");
  }
}

export class PublicErddapProvider extends EnvironmentalProvider {
  constructor(config) {
    super();
    this.config = config;
  }
}

export class HostedErddapProvider extends EnvironmentalProvider {
  constructor(config) {
    super();
    this.config = config;
  }
}

export function normalizeErddapTable(payload, source) {
  const table = payload.table;
  const names = table.columnNames;
  const units = table.columnUnits;

  return table.rows.map((row, index) => {
    const values = Object.fromEntries(names.map((name, columnIndex) => [name, row[columnIndex]]));
    const unitMap = Object.fromEntries(names.map((name, columnIndex) => [name, units[columnIndex] || ""]));

    return {
      id: `${source}-${index}`,
      source,
      observedAt: values.time,
      latitude: values.latitude,
      longitude: values.longitude,
      values,
      units: unitMap
    };
  });
}

function stateFromPoints(source, kind, points, valueKey) {
  const values = points
    .map((point) => Number(point.values[valueKey]))
    .filter((value) => Number.isFinite(value));
  const average = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;

  return {
    source,
    kind,
    points,
    average,
    updatedAt: points[0]?.observedAt || null
  };
}

function emptyState(source, kind) {
  return {
    source,
    kind,
    points: [],
    average: null,
    updatedAt: null
  };
}

