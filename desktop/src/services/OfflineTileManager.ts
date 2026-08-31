/**
 * ResQMesh AI — High-Performance Offline Vector Tile Manager
 * Viewport-based on-demand tile streaming with LRU in-memory cache & neighbor prefetching.
 * Replaces monolithic 37MB GeoJSON loading with tiny ~200KB spatial grid tiles.
 */

interface TileManifestItem {
  count: number;
  bounds: [number, number, number, number]; // [w, s, e, n]
}

interface TileManifest {
  zoom: number;
  tiles: Record<string, TileManifestItem>;
}

export class OfflineTileManager {
  private static manifest: TileManifest | null = null;
  private static tileCache = new Map<string, any>(); // key -> FeatureCollection
  private static pendingLoads = new Map<string, Promise<any>>();
  private static readonly MAX_CACHE_TILES = 60;

  /**
   * Initializes manifest once
   */
  public static async initManifest(): Promise<TileManifest | null> {
    if (this.manifest) return this.manifest;
    try {
      let data: any = null;
      if ((window as any).resqmeshAPI?.loadGeoJson) {
        data = await (window as any).resqmeshAPI.loadGeoJson('geo/tiles/manifest.json');
      }
      if (!data) {
        try {
          const resp = await fetch('./geo/tiles/manifest.json');
          if (resp.ok) data = await resp.json();
        } catch {}
      }
      if (!data) {
        try {
          const resp = await fetch('/geo/tiles/manifest.json');
          if (resp.ok) data = await resp.json();
        } catch {}
      }
      if (data && data.tiles) {
        this.manifest = data as TileManifest;
        return this.manifest;
      }
    } catch (err) {
      console.warn('[OfflineTileManager] Could not load tile manifest:', err);
    }
    return null;
  }

  /**
   * Converts lat/lon to Zoom-13 tile coordinate
   */
  public static deg2num(lat: number, lon: number, zoom = 13): [number, number] {
    const latRad = (lat * Math.PI) / 180;
    const n = Math.pow(2, zoom);
    const xtile = Math.floor(((lon + 180) / 360) * n);
    const ytile = Math.floor(((1 - Math.asinh(Math.tan(latRad)) / Math.PI) / 2) * n);
    return [xtile, ytile];
  }

  /**
   * Loads a single tile by key (e.g. '5881_3695') using LRU memory cache
   */
  public static async loadTile(key: string): Promise<any | null> {
    // Check in-memory LRU cache
    if (this.tileCache.has(key)) {
      const cached = this.tileCache.get(key);
      // Re-insert to mark as recently used
      this.tileCache.delete(key);
      this.tileCache.set(key, cached);
      return cached;
    }

    // Check if already in-flight
    if (this.pendingLoads.has(key)) {
      return this.pendingLoads.get(key);
    }

    const loadPromise = (async () => {
      try {
        const relPath = `geo/tiles/13/${key}.json`;
        let data: any = null;
        if ((window as any).resqmeshAPI?.loadGeoJson) {
          data = await (window as any).resqmeshAPI.loadGeoJson(relPath);
        }
        if (!data) {
          try {
            const resp = await fetch(`./${relPath}`);
            if (resp.ok) data = await resp.json();
          } catch {}
        }
        if (!data) {
          try {
            const resp = await fetch(`/${relPath}`);
            if (resp.ok) data = await resp.json();
          } catch {}
        }

        if (data && data.features) {
          // Store in LRU cache
          if (this.tileCache.size >= this.MAX_CACHE_TILES) {
            const oldestKey = this.tileCache.keys().next().value;
            if (oldestKey) this.tileCache.delete(oldestKey);
          }
          this.tileCache.set(key, data);
          return data;
        }
      } catch (err) {
        console.warn(`[OfflineTileManager] Error loading tile ${key}:`, err);
      } finally {
        this.pendingLoads.delete(key);
      }
      return null;
    })();

    this.pendingLoads.set(key, loadPromise);
    return loadPromise;
  }

  /**
   * Computes visible tile keys for current viewport bounding box
   */
  public static getVisibleTileKeys(
    west: number,
    south: number,
    east: number,
    north: number,
    zoom: number
  ): string[] {
    // Only stream local residential streets at zoom >= 12.0
    if (zoom < 12.0) return [];

    const [minX, minY] = this.deg2num(north, west, 13);
    const [maxX, maxY] = this.deg2num(south, east, 13);

    const keys: string[] = [];
    const clampedMinX = Math.min(minX, maxX);
    const clampedMaxX = Math.max(minX, maxX);
    const clampedMinY = Math.min(minY, maxY);
    const clampedMaxY = Math.max(minY, maxY);

    for (let x = clampedMinX; x <= clampedMaxX; x++) {
      for (let y = clampedMinY; y <= clampedMaxY; y++) {
        const k = `${x}_${y}`;
        if (!this.manifest || this.manifest.tiles[k]) {
          keys.push(k);
        }
      }
    }
    return keys;
  }

  /**
   * Loads all features for current visible viewport and prefetches 1-ring neighbors
   */
  public static async getViewportFeatures(
    west: number,
    south: number,
    east: number,
    north: number,
    zoom: number
  ): Promise<any[]> {
    await this.initManifest();
    const visibleKeys = this.getVisibleTileKeys(west, south, east, north, zoom);
    if (visibleKeys.length === 0) return [];

    // Load visible tiles concurrently
    const loadedTiles = await Promise.all(visibleKeys.map((k) => this.loadTile(k)));
    const mergedFeatures: any[] = [];
    for (const tile of loadedTiles) {
      if (tile && Array.isArray(tile.features)) {
        for (let i = 0; i < tile.features.length; i++) {
          mergedFeatures.push(tile.features[i]);
        }
      }
    }

    // Prefetch surrounding 1-ring neighbor tiles in background
    setTimeout(() => {
      this.prefetchNeighbors(visibleKeys);
    }, 150);

    return mergedFeatures;
  }

  /**
   * Background prefetch of adjacent neighboring tiles
   */
  private static prefetchNeighbors(currentKeys: string[]) {
    const currentSet = new Set(currentKeys);
    const neighbors: string[] = [];

    for (const k of currentKeys) {
      const parts = k.split('_');
      const x = parseInt(parts[0], 10);
      const y = parseInt(parts[1], 10);
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          if (dx === 0 && dy === 0) continue;
          const nk = `${x + dx}_${y + dy}`;
          if (!currentSet.has(nk) && !this.tileCache.has(nk)) {
            if (!this.manifest || this.manifest.tiles[nk]) {
              neighbors.push(nk);
            }
          }
        }
      }
    }

    // Preload top 6 neighbor candidates
    neighbors.slice(0, 6).forEach((nk) => this.loadTile(nk));
  }
}
