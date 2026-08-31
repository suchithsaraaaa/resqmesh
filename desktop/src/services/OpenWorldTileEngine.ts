import spatialIndexData from '../assets/geo/sectors/spatial-index.json';

export interface SectorMeta {
  id: string;
  name: string;
  center: [number, number];
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  file: string;
  featureCount: number;
}

/**
 * Open-World Dynamic Spatial Tile Engine
 * Dynamically streams and loads vector road sector tiles based on camera viewport bounds.
 * Mimics open-world game chunk streaming: only loads and renders geometries required
 * for the current camera view, preventing memory bloat and maintaining 60 FPS.
 */
export class OpenWorldTileEngine {
  private static sectors: SectorMeta[] = spatialIndexData as SectorMeta[];
  private static sectorCache = new Map<string, any>();
  private static activeSectorIds = new Set<string>();

  /**
   * Evaluates whether two 2D bounding boxes intersect
   */
  private static bboxesIntersect(
    b1: [number, number, number, number],
    b2: [number, number, number, number]
  ): boolean {
    return !(b2[0] > b1[2] || b2[2] < b1[0] || b2[1] > b1[3] || b2[3] < b1[1]);
  }

  /**
   * Lazily loads a sector GeoJSON by ID
   */
  private static async loadSector(sector: SectorMeta): Promise<any> {
    if (this.sectorCache.has(sector.id)) {
      return this.sectorCache.get(sector.id);
    }

    try {
      let module: any;
      if (sector.id === 'hyderabad') {
        module = await import('../assets/geo/hyderabad-roads.json');
      } else {
        // Dynamic import of sector chunk with explicit extension for Vite
        module = await import(`../assets/geo/sectors/${sector.id}-roads.json`);
      }
      const data = module.default || module;
      this.sectorCache.set(sector.id, data);
      return data;
    } catch (err) {
      console.warn(`[OpenWorld] Failed to load road sector ${sector.id}:`, err);
      return null;
    }
  }

  /**
   * Updates visible sectors based on active camera bounding box and zoom level.
   * Returns a merged GeoJSON FeatureCollection containing all visible road geometries.
   */
  static async getVisibleRoads(
    bounds: { getWest: () => number; getSouth: () => number; getEast: () => number; getNorth: () => number },
    zoom: number
  ): Promise<{ data: any; changed: boolean }> {
    // Only load detailed urban sectors at zoom >= 8.5
    if (zoom < 8.5) {
      if (this.activeSectorIds.size === 0) {
        return { data: { type: 'FeatureCollection', features: [] }, changed: false };
      }
      this.activeSectorIds.clear();
      return { data: { type: 'FeatureCollection', features: [] }, changed: true };
    }

    const viewBbox: [number, number, number, number] = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];

    const matchingSectors = this.sectors.filter((sec) => this.bboxesIntersect(viewBbox, sec.bbox));

    const newSectorIds = new Set(matchingSectors.map((s) => s.id));
    
    // Check if active sectors changed
    let hasChanged = false;
    if (newSectorIds.size !== this.activeSectorIds.size) {
      hasChanged = true;
    } else {
      for (const id of newSectorIds) {
        if (!this.activeSectorIds.has(id)) {
          hasChanged = true;
          break;
        }
      }
    }

    if (!hasChanged) {
      return { data: null, changed: false };
    }

    this.activeSectorIds = newSectorIds;

    // Load and combine features from all visible sectors
    const loadedDataList = await Promise.all(matchingSectors.map((s) => this.loadSector(s)));
    const allFeatures: any[] = [];

    for (const d of loadedDataList) {
      if (d && Array.isArray(d.features)) {
        allFeatures.push(...d.features);
      }
    }

    return {
      data: {
        type: 'FeatureCollection',
        features: allFeatures,
      },
      changed: true,
    };
  }

  /**
   * Preloads common strategic hubs in the background
   */
  static preloadCommonHubs() {
    setTimeout(async () => {
      const topHubs = ['delhi', 'mumbai', 'bengaluru', 'hyderabad'];
      for (const id of topHubs) {
        const sec = this.sectors.find((s) => s.id === id);
        if (sec) {
          await this.loadSector(sec);
        }
      }
    }, 2000);
  }
}
