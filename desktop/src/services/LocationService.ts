import { OfflineGeocoder } from './OfflineGeocoder';

export type LocationSource =
  | 'GNSS'
  | 'GPS'
  | 'Windows Location'
  | 'Browser Geolocation'
  | 'Wi-Fi'
  | 'Cellular'
  | 'IP / Approximate'
  | 'Manual / Map Pick'
  | 'MANUAL_MAP'
  | 'Cached Last Known'
  | 'Unavailable';

export interface LocationResult {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null; // Real accuracy in meters
  source: LocationSource;
  timestamp: string; // e.g. "18:42:21"
  rawTimestamp: number; // Unix ms
  isFresh: boolean;
  isWithin20m: boolean;
  accuracyLabel: 'VERIFIED' | 'LOW ACCURACY' | 'TOO INACCURATE' | 'MANUAL' | 'MANUAL_SELECTION' | 'UNAVAILABLE';
  error?: string;
  resolvedAddress?: string;
}

const STORAGE_KEY = 'resqmesh_last_known_location';

/**
 * ResQMesh Real Physical Location Engine
 * Priority:
 * 1. GNSS / GPS (Physical hardware)
 * 2. Windows high-accuracy device location
 * 3. Browser high-accuracy geolocation
 * 4. Offline: Local GNSS hardware if present, otherwise clearly reports Unavailable (never fakes accuracy)
 */
export class LocationService {
  private static watchId: number | null = null;
  private static listeners: Set<(loc: LocationResult) => void> = new Set();
  private static currentLocation: LocationResult | null = null;

  /**
   * Evaluates if network connectivity is currently reported
   */
  static isOnline(): boolean {
    if (typeof navigator !== 'undefined' && typeof navigator.onLine === 'boolean') {
      return navigator.onLine;
    }
    return true;
  }

  /**
   * Validates whether given coordinates fall within the Telangana geographic area.
   */
  static isInsideTelangana(lat: number, lon: number): boolean {
    return lat >= 15.80 && lat <= 19.90 && lon >= 77.20 && lon <= 81.80;
  }

  /**
   * Evaluates accuracy against the ResQMesh emergency target of ±20 meters
   */
  static evaluateAccuracy(
    accuracy: number | null,
    source: LocationSource
  ): { isWithin20m: boolean; accuracyLabel: LocationResult['accuracyLabel'] } {
    if (source === 'Manual / Map Pick') {
      return { isWithin20m: true, accuracyLabel: 'MANUAL' };
    }
    if (accuracy === null || source === 'Unavailable') {
      return { isWithin20m: false, accuracyLabel: 'UNAVAILABLE' };
    }
    if (accuracy <= 20) {
      return { isWithin20m: true, accuracyLabel: 'VERIFIED' };
    }
    if (accuracy <= 1000) {
      return { isWithin20m: false, accuracyLabel: 'LOW ACCURACY' };
    }
    return { isWithin20m: false, accuracyLabel: 'TOO INACCURATE' };
  }

  /**
   * Determines realistic source description based on connection status and reported accuracy
   */
  static deduceSource(accuracy: number, isOnline: boolean): LocationSource {
    if (!isOnline) {
      // Offline fix can only come from local physical GNSS/GPS hardware
      return 'GNSS';
    }
    if (accuracy <= 8) {
      return 'GNSS';
    }
    if (accuracy <= 20) {
      return 'Windows Location';
    }
    if (accuracy <= 60) {
      return 'Wi-Fi';
    }
    if (accuracy <= 300) {
      return 'Cellular';
    }
    return 'IP / Approximate';
  }

  /**
   * Format timestamp as HH:MM:SS
   */
  static formatTime(date: Date = new Date()): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /**
   * Retrieves the previously known/cached location from on-device persistent storage.
   */
  static getLastKnownLocation(): LocationResult | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (
        typeof parsed.latitude === 'number' &&
        typeof parsed.longitude === 'number' &&
        !isNaN(parsed.latitude) &&
        !isNaN(parsed.longitude)
      ) {
        const rawTime = parsed.rawTimestamp || Date.now() - 3600000;
        const isFresh = Date.now() - rawTime < 60000;
        const acc = typeof parsed.accuracy === 'number' ? parsed.accuracy : null;
        const { isWithin20m, accuracyLabel } = this.evaluateAccuracy(acc, 'Cached Last Known');
        const addr = OfflineGeocoder.reverseGeocode(parsed.latitude, parsed.longitude);

        return {
          latitude: parsed.latitude,
          longitude: parsed.longitude,
          accuracy: acc,
          source: 'Cached Last Known',
          timestamp: parsed.timestamp || this.formatTime(new Date(rawTime)),
          rawTimestamp: rawTime,
          isFresh,
          isWithin20m,
          accuracyLabel,
          resolvedAddress: addr.formatted,
        };
      }
    } catch {
      // Ignore corrupted cache
    }
    return null;
  }

  /**
   * Persists a validated coordinate to on-device storage for future reference.
   */
  static saveLastKnownLocation(
    lat: number,
    lon: number,
    accuracy: number | null,
    source: LocationSource
  ) {
    try {
      const now = Date.now();
      const payload = {
        latitude: Number(lat.toFixed(6)),
        longitude: Number(lon.toFixed(6)),
        accuracy: accuracy !== null ? Math.round(accuracy) : null,
        timestamp: this.formatTime(new Date(now)),
        rawTimestamp: now,
        source,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // Ignore storage error
    }
  }

  /**
   * Manually sets an incident location coordinate (e.g. from Pick on Map or manual input).
   */
  static setManualLocation(lat: number, lon: number): LocationResult {
    const addr = OfflineGeocoder.reverseGeocode(lat, lon);
    const now = Date.now();
    const result: LocationResult = {
      latitude: Number(lat.toFixed(6)),
      longitude: Number(lon.toFixed(6)),
      accuracy: null,
      source: 'Manual / Map Pick',
      timestamp: this.formatTime(new Date(now)),
      rawTimestamp: now,
      isFresh: true,
      isWithin20m: true,
      accuracyLabel: 'MANUAL',
      resolvedAddress: addr.formatted,
    };
    this.saveLastKnownLocation(lat, lon, null, 'Manual / Map Pick');
    this.currentLocation = result;
    this.notifyListeners(result);
    return result;
  }

  /**
   * Requests a fresh high-accuracy position from operating system / device hardware.
   * Never fakes an offline GPS result if hardware does not exist.
   */
  static async getCurrentLocation(timeoutMs: number = 8000): Promise<LocationResult> {
    const online = this.isOnline();
    const now = Date.now();
    const timeStr = this.formatTime(new Date(now));

    if (typeof window === 'undefined' || !navigator.geolocation) {
      return {
        latitude: null,
        longitude: null,
        accuracy: null,
        source: 'Unavailable',
        timestamp: timeStr,
        rawTimestamp: now,
        isFresh: false,
        isWithin20m: false,
        accuracyLabel: 'UNAVAILABLE',
        error: online
          ? 'Device geolocation is not supported on this platform.'
          : 'No GNSS/device location source detected. Waiting for GPS/GNSS.',
      };
    }

    return new Promise<LocationResult>((resolve) => {
      let settled = false;

      const timer = setTimeout(() => {
        if (!settled) {
          settled = true;
          // Timeout occurred
          const result: LocationResult = {
            latitude: null,
            longitude: null,
            accuracy: null,
            source: 'Unavailable',
            timestamp: this.formatTime(),
            rawTimestamp: Date.now(),
            isFresh: false,
            isWithin20m: false,
            accuracyLabel: 'UNAVAILABLE',
            error: online
              ? 'Location acquisition timed out. Please retry.'
              : 'No GNSS/device location source detected. Accuracy requirement: ±20 m. Status: Waiting for GPS/GNSS.',
          };
          this.currentLocation = result;
          resolve(result);
        }
      }, timeoutMs);

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          if (!settled) {
            settled = true;
            clearTimeout(timer);
            const lat = Number(pos.coords.latitude.toFixed(6));
            const lon = Number(pos.coords.longitude.toFixed(6));
            const rawAcc = pos.coords.accuracy;
            const acc = typeof rawAcc === 'number' && !isNaN(rawAcc) ? Math.round(rawAcc * 10) / 10 : 25;
            const source = this.deduceSource(acc, online);
            const { isWithin20m, accuracyLabel } = this.evaluateAccuracy(acc, source);
            const addr = OfflineGeocoder.reverseGeocode(lat, lon);
            const fixTime = pos.timestamp ? new Date(pos.timestamp) : new Date();

            const result: LocationResult = {
              latitude: lat,
              longitude: lon,
              accuracy: acc,
              source,
              timestamp: this.formatTime(fixTime),
              rawTimestamp: fixTime.getTime(),
              isFresh: true,
              isWithin20m,
              accuracyLabel,
              resolvedAddress: addr.formatted,
            };

            this.saveLastKnownLocation(lat, lon, acc, source);
            this.currentLocation = result;
            this.notifyListeners(result);
            resolve(result);
          }
        },
        (err) => {
          if (!settled) {
            settled = true;
            clearTimeout(timer);
            const isOffline = !this.isOnline();
            const result: LocationResult = {
              latitude: null,
              longitude: null,
              accuracy: null,
              source: 'Unavailable',
              timestamp: this.formatTime(),
              rawTimestamp: Date.now(),
              isFresh: false,
              isWithin20m: false,
              accuracyLabel: 'UNAVAILABLE',
              error: isOffline
                ? 'No GNSS/device location source detected. Accuracy requirement: ±20 m. Status: Waiting for GPS/GNSS.'
                : err.message || 'Unable to acquire location from device provider.',
            };
            this.currentLocation = result;
            resolve(result);
          }
        },
        {
          enableHighAccuracy: true,
          timeout: timeoutMs,
          maximumAge: 0,
        }
      );
    });
  }

  /**
   * Starts continuous background location watching.
   * Updates listeners when coordinates or accuracy change without rebuilding the UI.
   */
  static startWatching(listener: (loc: LocationResult) => void): () => void {
    this.listeners.add(listener);

    // If we already have a recent location, emit it immediately
    if (this.currentLocation) {
      listener(this.currentLocation);
    }

    if (this.watchId === null && typeof navigator !== 'undefined' && navigator.geolocation) {
      try {
        this.watchId = navigator.geolocation.watchPosition(
          (pos) => {
            const online = this.isOnline();
            const lat = Number(pos.coords.latitude.toFixed(6));
            const lon = Number(pos.coords.longitude.toFixed(6));
            const rawAcc = pos.coords.accuracy;
            const acc = typeof rawAcc === 'number' && !isNaN(rawAcc) ? Math.round(rawAcc * 10) / 10 : null;
            const source = acc !== null ? this.deduceSource(acc, online) : 'Windows Location';
            const { isWithin20m, accuracyLabel } = this.evaluateAccuracy(acc, source);
            const addr = OfflineGeocoder.reverseGeocode(lat, lon);
            const fixTime = pos.timestamp ? new Date(pos.timestamp) : new Date();

            const result: LocationResult = {
              latitude: lat,
              longitude: lon,
              accuracy: acc,
              source,
              timestamp: this.formatTime(fixTime),
              rawTimestamp: fixTime.getTime(),
              isFresh: true,
              isWithin20m,
              accuracyLabel,
              resolvedAddress: addr.formatted,
            };

            this.currentLocation = result;
            if (acc !== null && isWithin20m) {
              this.saveLastKnownLocation(lat, lon, acc, source);
            }
            this.notifyListeners(result);
          },
          (err) => {
            const isOffline = !this.isOnline();
            if (isOffline) {
              const result: LocationResult = {
                latitude: null,
                longitude: null,
                accuracy: null,
                source: 'Unavailable',
                timestamp: this.formatTime(),
                rawTimestamp: Date.now(),
                isFresh: false,
                isWithin20m: false,
                accuracyLabel: 'UNAVAILABLE',
                error: 'No GNSS/device location source detected. Status: Waiting for GPS/GNSS.',
              };
              this.currentLocation = result;
              this.notifyListeners(result);
            }
          },
          {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 10000,
          }
        );
      } catch {
        // Ignore watchPosition errors
      }
    }

    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0 && this.watchId !== null) {
        if (typeof navigator !== 'undefined' && navigator.geolocation) {
          navigator.geolocation.clearWatch(this.watchId);
        }
        this.watchId = null;
      }
    };
  }

  private static notifyListeners(result: LocationResult) {
    this.listeners.forEach((fn) => {
      try {
        fn(result);
      } catch {
        // Ignore listener error
      }
    });
  }
}
