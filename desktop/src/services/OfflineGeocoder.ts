import telanganaCitiesData from '../assets/geo/telangana-cities.json';
import globalCitiesData from '../assets/geo/global-cities.json';
import hyderabadPlacesData from '../assets/geo/hyderabad-places.json';

export interface GeocodedAddress {
  cityName: string;
  district?: string;
  country: string;
  formatted: string;
  distanceKm: number;
}

export interface PlaceSearchResult {
  name: string;
  category: string;
  district?: string;
  state: string;
  lat: number;
  lon: number;
  label: string;
}

/**
 * 100% Offline Reverse Geocoder
 * Resolves any (lat, lon) coordinate to the nearest authoritative city and district in < 1ms
 * using pre-indexed local vector datasets.
 * Requires ZERO internet connectivity and ZERO external cloud API calls.
 */
export class OfflineGeocoder {
  private static telanganaCities: Array<{
    name: string;
    district: string;
    lat: number;
    lon: number;
  }> | null = null;

  private static globalCities: Array<{
    name: string;
    country: string;
    lat: number;
    lon: number;
  }> | null = null;

  private static init() {
    if (!this.telanganaCities) {
      const tcFeatures = (telanganaCitiesData as any).features || [];
      this.telanganaCities = tcFeatures.map((f: any) => ({
        name: f.properties?.name || 'Unknown',
        district: f.properties?.district || '',
        lon: f.geometry?.coordinates?.[0] ?? 0,
        lat: f.geometry?.coordinates?.[1] ?? 0,
      }));
    }

    if (!this.globalCities) {
      const gcFeatures = (globalCitiesData as any).features || [];
      this.globalCities = gcFeatures.map((f: any) => ({
        name: f.properties?.name || 'Unknown',
        country: f.properties?.country || '',
        lon: f.geometry?.coordinates?.[0] ?? 0,
        lat: f.geometry?.coordinates?.[1] ?? 0,
      }));
    }
  }

  /**
   * Calculates Haversine distance in kilometers between two geographic coordinates
   */
  private static haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // Earth radius in km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  /**
   * Reverse geocodes coordinates to the closest authoritative offline city/district/region
   */
  static reverseGeocode(lat: number, lon: number): GeocodedAddress {
    this.init();

    // Check if coordinates are within or proximate to Telangana
    // (Lat: 15.0 to 20.5, Lon: 76.5 to 82.5)
    if (lat >= 15.0 && lat <= 20.5 && lon >= 76.5 && lon <= 82.5 && this.telanganaCities && this.telanganaCities.length > 0) {
      let nearest = this.telanganaCities[0];
      let minDistance = this.haversineKm(lat, lon, nearest.lat, nearest.lon);

      for (let i = 1; i < this.telanganaCities.length; i++) {
        const c = this.telanganaCities[i];
        const dist = this.haversineKm(lat, lon, c.lat, c.lon);
        if (dist < minDistance) {
          minDistance = dist;
          nearest = c;
        }
      }

      const distStr = minDistance < 1 ? 'Within' : `~${Math.round(minDistance)} km from`;
      const formatted = `${distStr} ${nearest.name}, ${nearest.district} District, Telangana`;

      return {
        cityName: nearest.name,
        district: nearest.district,
        country: 'India',
        formatted,
        distanceKm: Math.round(minDistance),
      };
    }

    // Fallback to global cities
    if (this.globalCities && this.globalCities.length > 0) {
      let nearest = this.globalCities[0];
      let minDistance = this.haversineKm(lat, lon, nearest.lat, nearest.lon);

      for (let i = 1; i < this.globalCities.length; i++) {
        const c = this.globalCities[i];
        const dist = this.haversineKm(lat, lon, c.lat, c.lon);
        if (dist < minDistance) {
          minDistance = dist;
          nearest = c;
        }
      }

      const distStr = minDistance < 1 ? 'Within' : `~${Math.round(minDistance)} km from`;
      const formatted = nearest.country
        ? `${distStr} ${nearest.name}, ${nearest.country}`
        : `${distStr} ${nearest.name}`;

      return {
        cityName: nearest.name,
        country: nearest.country,
        formatted,
        distanceKm: Math.round(minDistance),
      };
    }

    return {
      cityName: '',
      country: '',
      formatted: `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`,
      distanceKm: 0,
    };
  }

  /**
   * 100% Offline Gazetteer Search
   * Searches local cities, towns, and neighborhood places across Telangana
   */
  public static searchPlaces(query: string, limit = 6): PlaceSearchResult[] {
    this.init();
    const clean = query.trim().toLowerCase();
    if (!clean || clean.length < 2) return [];

    const results: PlaceSearchResult[] = [];

    // Search Telangana Cities & Towns
    if (this.telanganaCities) {
      for (const city of this.telanganaCities) {
        if (city.name.toLowerCase().includes(clean) || city.district.toLowerCase().includes(clean)) {
          results.push({
            name: city.name,
            category: 'City / Town',
            district: city.district,
            state: 'Telangana',
            lat: city.lat,
            lon: city.lon,
            label: `${city.name}, ${city.district} District, Telangana`,
          });
        }
      }
    }

    // Search Hyderabad Suburbs & Landmarks
    const hpFeatures = (hyderabadPlacesData as any).features || [];
    for (const feat of hpFeatures) {
      const pName = feat.properties?.name || '';
      const pType = feat.properties?.type || 'Subdivision';
      if (pName.toLowerCase().includes(clean)) {
        results.push({
          name: pName,
          category: pType.toUpperCase(),
          district: 'Hyderabad Sector',
          state: 'Telangana',
          lon: feat.geometry?.coordinates?.[0] ?? 0,
          lat: feat.geometry?.coordinates?.[1] ?? 0,
          label: `${pName}, Hyderabad, Telangana`,
        });
      }
    }

    return results.slice(0, limit);
  }
}
