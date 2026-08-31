import React, { useState, useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { colors, radii, shadows, fonts } from '../styles/designTokens';
import { OfflineGeocoder, PlaceSearchResult } from '../services/OfflineGeocoder';
import { OfflineTileManager } from '../services/OfflineTileManager';

// Bundled lightweight authoritative geospatial vector datasets (< 1.9MB combined)
import telanganaBoundaryData from '../assets/geo/telangana-boundary.json';
import telanganaDistrictsData from '../assets/geo/telangana-districts.json';
import telanganaHighwaysData from '../assets/geo/telangana-highways.json';
import telanganaRoadsData from '../assets/geo/telangana-roads.json';
import telanganaCitiesData from '../assets/geo/telangana-cities.json';
import hyderabadWaterData from '../assets/geo/hyderabad-water.json';
import hyderabadArterialsData from '../assets/geo/hyderabad-primary-roads.json';
import hyderabadPlacesData from '../assets/geo/hyderabad-places.json';

interface LocationPickerModalProps {
  isOpen: boolean;
  initialLat?: number | null;
  initialLon?: number | null;
  userLocation?: { lat: number; lon: number } | null;
  onConfirm: (coords: { lat: number; lon: number; address?: string }) => void;
  onCancel: () => void;
}

export const LocationPickerModal: React.FC<LocationPickerModalProps> = ({
  isOpen,
  initialLat,
  initialLon,
  userLocation,
  onConfirm,
  onCancel,
}) => {
  // Determine initial coordinates: prefer valid initial coords, then userLocation, then Hyderabad central
  const defaultLat = initialLat ?? (userLocation?.lat ?? 17.385044);
  const defaultLon = initialLon ?? (userLocation?.lon ?? 78.486671);

  const [lat, setLat] = useState<number>(defaultLat);
  const [lon, setLon] = useState<number>(defaultLon);
  const [currentZoom, setCurrentZoom] = useState<number>(initialLat && initialLon ? 13 : 11.5);
  const [resolvedAddress, setResolvedAddress] = useState<string>('');
  const [isTilesLoading, setIsTilesLoading] = useState<boolean>(false);

  // Offline search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<PlaceSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const isMapLoadedRef = useRef<boolean>(false);
  const geocodeTimeoutRef = useRef<any>(null);
  const tileLoadTimeoutRef = useRef<any>(null);
  const openTimeRef = useRef<number>(0);

  // Asynchronous debounced reverse geocoding to prevent UI stalls
  const scheduleReverseGeocode = useCallback((newLat: number, newLon: number) => {
    if (geocodeTimeoutRef.current) clearTimeout(geocodeTimeoutRef.current);
    geocodeTimeoutRef.current = setTimeout(() => {
      try {
        const rev = OfflineGeocoder.reverseGeocode(newLat, newLon);
        setResolvedAddress(rev?.formatted || `${newLat.toFixed(6)}°, ${newLon.toFixed(6)}°`);
      } catch {
        setResolvedAddress(`${newLat.toFixed(6)}°, ${newLon.toFixed(6)}°`);
      }
    }, 250);
  }, []);

  // Update viewport road tiles progressively on move or zoom
  const updateViewportTiles = useCallback(async () => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    const zoom = map.getZoom();
    if (zoom < 11.8) {
      const src = map.getSource('urban-local-streets') as maplibregl.GeoJSONSource;
      if (src) src.setData({ type: 'FeatureCollection', features: [] });
      setIsTilesLoading(false);
      return;
    }

    const bounds = map.getBounds();
    const west = bounds.getWest();
    const south = bounds.getSouth();
    const east = bounds.getEast();
    const north = bounds.getNorth();

    setIsTilesLoading(true);
    try {
      const tStart = performance.now();
      const features = await OfflineTileManager.getViewportFeatures(west, south, east, north, zoom);
      const src = map.getSource('urban-local-streets') as maplibregl.GeoJSONSource;
      if (src && mapRef.current) {
        src.setData({
          type: 'FeatureCollection',
          features,
        });
      }
      console.log(`[MapPicker Profiler] VIEWPORT TILES LOADED: ${Math.round(performance.now() - openTimeRef.current)}ms (${features.length} local streets in ${Math.round(performance.now() - tStart)}ms)`);
    } catch (err) {
      console.warn('[LocationPickerModal] Viewport tile streaming notice:', err);
    } finally {
      setIsTilesLoading(false);
    }
  }, []);

  // Handle local offline gazetteer search
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }
    const matches = OfflineGeocoder.searchPlaces(searchQuery, 6);
    setSearchResults(matches);
    setIsSearching(true);
  }, [searchQuery]);

  // Initialize MapLibre GL Map
  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return;

    openTimeRef.current = performance.now();
    console.log('[MapPicker Profiler] MAP PICKER OPEN: 0ms');

    setLat(defaultLat);
    setLon(defaultLon);
    scheduleReverseGeocode(defaultLat, defaultLon);

    // If map instance already exists, reuse it instantly without recreating
    if (mapRef.current) {
      const map = mapRef.current;
      map.resize();
      map.jumpTo({
        center: [defaultLon, defaultLat],
        zoom: initialLat && initialLon ? 13 : 11.5,
      });
      if (markerRef.current) {
        markerRef.current.setLngLat([defaultLon, defaultLat]);
      }
      console.log(`[MapPicker Profiler] WARM START MAP READY: ${Math.round(performance.now() - openTimeRef.current)}ms`);
      updateViewportTiles();
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          'telangana-boundary': {
            type: 'geojson',
            data: telanganaBoundaryData as any,
          },
          'telangana-districts': {
            type: 'geojson',
            data: telanganaDistrictsData as any,
          },
          'hyderabad-water': {
            type: 'geojson',
            data: hyderabadWaterData as any,
          },
          'telangana-highways': {
            type: 'geojson',
            data: telanganaHighwaysData as any,
          },
          'telangana-roads': {
            type: 'geojson',
            data: telanganaRoadsData as any,
          },
          'urban-arterials': {
            type: 'geojson',
            data: hyderabadArterialsData as any,
          },
          'urban-local-streets': {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] } as any,
          },
          'telangana-cities': {
            type: 'geojson',
            data: telanganaCitiesData as any,
          },
          'hyderabad-places': {
            type: 'geojson',
            data: hyderabadPlacesData as any,
          },
        },
        layers: [
          // 1. Dark Base Canvas
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#060a12',
            },
          },
          // 2. Authentic Telangana State Boundary Casing
          {
            id: 'telangana-boundary-casing',
            type: 'line',
            source: 'telangana-boundary',
            paint: {
              'line-color': '#011d33',
              'line-width': ['interpolate', ['linear'], ['zoom'], 4, 3.0, 8, 5.0, 14, 8.0],
              'line-opacity': 0.8,
            },
          },
          // 3. Authentic Telangana State Boundary Line (Crisp Cyan)
          {
            id: 'telangana-boundary-line',
            type: 'line',
            source: 'telangana-boundary',
            paint: {
              'line-color': '#0284c7',
              'line-width': ['interpolate', ['linear'], ['zoom'], 4, 1.8, 8, 3.2, 14, 5.0],
              'line-opacity': 0.95,
            },
          },
          // 4. Authentic Telangana Districts Fill (visible at regional zoom, subtle at street zoom)
          {
            id: 'telangana-districts-fill',
            type: 'fill',
            source: 'telangana-districts',
            minzoom: 5.0,
            paint: {
              'fill-color': '#0e2b4d',
              'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.22, 8, 0.28, 11, 0.1, 13, 0.0],
            },
          },
          // 5. Authentic Telangana Districts Boundary Lines (Survey of India)
          {
            id: 'telangana-districts-line',
            type: 'line',
            source: 'telangana-districts',
            minzoom: 5.0,
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 8, 1.3, 11, 0.6, 13, 0.2],
              'line-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.7, 8, 0.55, 11, 0.25, 13, 0.05],
            },
          },
          // 6. Water Bodies (Hussain Sagar, Osman Sagar, Himayat Sagar, etc.)
          {
            id: 'hyderabad-water-fill',
            type: 'fill',
            source: 'hyderabad-water',
            minzoom: 7.0,
            paint: {
              'fill-color': '#0369a1',
              'fill-opacity': ['interpolate', ['linear'], ['zoom'], 7, 0.45, 10, 0.65, 14, 0.85],
            },
          },
          {
            id: 'hyderabad-water-line',
            type: 'line',
            source: 'hyderabad-water',
            minzoom: 7.0,
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 7, 0.8, 11, 1.8, 14, 2.8],
              'line-opacity': 0.9,
            },
          },
          // 7. State Highways & Connecting Corridors
          {
            id: 'telangana-roads-casing',
            type: 'line',
            source: 'telangana-roads',
            minzoom: 6.0,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.5, 9, 3.0, 14, 5.0],
            },
          },
          {
            id: 'telangana-roads-line',
            type: 'line',
            source: 'telangana-roads',
            minzoom: 6.0,
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.0, 9, 2.0, 14, 3.5],
              'line-opacity': 0.9,
            },
          },
          // 8. National Highways (NH 44, NH 65, NH 163, NH 765, ORR)
          {
            id: 'telangana-highways-casing',
            type: 'line',
            source: 'telangana-highways',
            minzoom: 4.5,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 4.5, 2.0, 8, 4.0, 14, 6.5],
            },
          },
          {
            id: 'telangana-highways-line',
            type: 'line',
            source: 'telangana-highways',
            minzoom: 4.5,
            paint: {
              'line-color': '#f59e0b',
              'line-width': ['interpolate', ['linear'], ['zoom'], 4.5, 1.2, 8, 2.8, 14, 4.8],
              'line-opacity': 0.95,
            },
          },
          // 9. Fast Regional Arterials (Motorways, Trunks, Primaries, Expressways)
          {
            id: 'urban-arterials-casing',
            type: 'line',
            source: 'urban-arterials',
            minzoom: 8.0,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 8, 1.2, 10, 2.2, 13, 4.0, 16, 7.5],
            },
          },
          {
            id: 'urban-arterials-primary',
            type: 'line',
            source: 'urban-arterials',
            minzoom: 8.0,
            filter: ['in', ['get', 'highway'], ['literal', ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link']]],
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 8, 1.0, 10, 2.0, 13, 3.4, 16, 6.0],
              'line-opacity': 0.95,
            },
          },
          {
            id: 'urban-arterials-secondary',
            type: 'line',
            source: 'urban-arterials',
            minzoom: 9.5,
            filter: ['in', ['get', 'highway'], ['literal', ['secondary', 'secondary_link', 'tertiary', 'tertiary_link']]],
            paint: {
              'line-color': '#60a5fa',
              'line-width': ['interpolate', ['linear'], ['zoom'], 9.5, 0.8, 11, 1.6, 14, 2.6, 16, 4.5],
              'line-opacity': 0.9,
            },
          },
          // 10. Viewport-Streamed Local Residential Streets & Intersections (Zoom >= 11.5)
          {
            id: 'urban-local-streets-casing',
            type: 'line',
            source: 'urban-local-streets',
            minzoom: 11.5,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 11.5, 0.8, 13, 1.8, 16, 4.5],
            },
          },
          {
            id: 'urban-local-streets-line',
            type: 'line',
            source: 'urban-local-streets',
            minzoom: 11.5,
            paint: {
              'line-color': '#94a3b8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 11.5, 0.5, 13, 1.1, 16, 3.0],
              'line-opacity': ['interpolate', ['linear'], ['zoom'], 11.5, 0.55, 13, 0.8, 16, 0.95],
            },
          },
          // 11. Cities & Towns Center Markers
          {
            id: 'telangana-cities-circle',
            type: 'circle',
            source: 'telangana-cities',
            minzoom: 5.0,
            paint: {
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 3.0, 8, 4.5, 12, 6.0],
              'circle-color': '#38bdf8',
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 1.5,
              'circle-opacity': 0.9,
            },
          },
          // 12. Strategic Neighborhood Landmarks
          {
            id: 'hyderabad-places-circle',
            type: 'circle',
            source: 'hyderabad-places',
            minzoom: 11.0,
            paint: {
              'circle-radius': 3.5,
              'circle-color': '#a855f7',
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 1.0,
              'circle-opacity': 0.85,
            },
          },
        ],
      },
      center: [defaultLon, defaultLat],
      zoom: initialLat && initialLon ? 13 : 11.5,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
    });

    mapRef.current = map;
    console.log(`[MapPicker Profiler] MAP ENGINE INITIALIZED: ${Math.round(performance.now() - openTimeRef.current)}ms`);

    // Create Custom Tactical Red/Orange Pin Marker Element
    const pinEl = document.createElement('div');
    pinEl.className = 'tactical-maplibre-pin';
    pinEl.style.width = '36px';
    pinEl.style.height = '48px';
    pinEl.style.cursor = 'grab';
    pinEl.style.display = 'flex';
    pinEl.style.flexDirection = 'column';
    pinEl.style.alignItems = 'center';
    pinEl.style.filter = 'drop-shadow(0 4px 10px rgba(0,0,0,0.7))';
    pinEl.innerHTML = `
      <div style="width: 32px; height: 32px; border-radius: 50% 50% 50% 0; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border: 2.5px solid #ffffff; transform: rotate(-45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 14px #ef4444;">
        <div style="width: 10px; height: 10px; background: #ffffff; border-radius: 50%; transform: rotate(45deg);"></div>
      </div>
      <div style="width: 10px; height: 10px; border-radius: 50%; background: rgba(239, 68, 68, 0.4); margin-top: 4px; box-shadow: 0 0 8px #ef4444;"></div>
    `;

    // Instantiate Draggable MapLibre Marker strictly anchored to [lon, lat]
    const marker = new maplibregl.Marker({
      element: pinEl,
      draggable: true,
      anchor: 'bottom',
    })
      .setLngLat([defaultLon, defaultLat])
      .addTo(map);

    markerRef.current = marker;

    // Listen to live marker dragging (instant coordinate update without reverse-geocoding stall)
    marker.on('drag', () => {
      const lngLat = marker.getLngLat();
      setLat(lngLat.lat);
      setLon(lngLat.lng);
    });

    marker.on('dragend', () => {
      const lngLat = marker.getLngLat();
      setLat(lngLat.lat);
      setLon(lngLat.lng);
      scheduleReverseGeocode(lngLat.lat, lngLat.lng);
    });

    // Listen to map click to place/move the pin to the EXACT clicked coordinate
    map.on('click', (e) => {
      const clickedLng = e.lngLat.lng;
      const clickedLat = e.lngLat.lat;
      marker.setLngLat([clickedLng, clickedLat]);
      setLat(clickedLat);
      setLon(clickedLng);
      scheduleReverseGeocode(clickedLat, clickedLng);
    });

    // Track live zoom level
    map.on('zoom', () => {
      setCurrentZoom(map.getZoom());
    });

    // Progressive on-demand viewport tile stream trigger
    map.on('moveend', () => {
      if (tileLoadTimeoutRef.current) clearTimeout(tileLoadTimeoutRef.current);
      tileLoadTimeoutRef.current = setTimeout(() => {
        updateViewportTiles();
      }, 100);
    });

    // Map loaded event
    map.on('load', () => {
      isMapLoadedRef.current = true;
      map.resize();
      console.log(`[MapPicker Profiler] BASE GEOMETRY READY: ${Math.round(performance.now() - openTimeRef.current)}ms`);
      console.log(`[MapPicker Profiler] MAP INTERACTIVE: ${Math.round(performance.now() - openTimeRef.current)}ms`);
      updateViewportTiles();
    });

    return () => {
      // Map instance is kept alive in ref for warm start; only clear timers on unmount
      if (geocodeTimeoutRef.current) clearTimeout(geocodeTimeoutRef.current);
      if (tileLoadTimeoutRef.current) clearTimeout(tileLoadTimeoutRef.current);
    };
  }, [isOpen, defaultLat, defaultLon, initialLat, initialLon, scheduleReverseGeocode, updateViewportTiles]);

  // Navigate map to coordinate programmatically
  const flyToCoord = (targetLon: number, targetLat: number, targetZoom: number) => {
    if (!mapRef.current || !markerRef.current) return;
    mapRef.current.flyTo({
      center: [targetLon, targetLat],
      zoom: targetZoom,
      essential: true,
    });
    markerRef.current.setLngLat([targetLon, targetLat]);
    setLat(targetLat);
    setLon(targetLon);
    scheduleReverseGeocode(targetLat, targetLon);
    setSearchQuery('');
    setSearchResults([]);
    setIsSearching(false);
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 10001,
        background: 'rgba(2, 6, 23, 0.88)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        fontFamily: fonts.body,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div
        style={{
          background: '#0a0f1d',
          border: '1px solid #1e293b',
          borderRadius: radii.xl,
          width: '100%',
          maxWidth: '920px',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: shadows.elevated,
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 20px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(90deg, #0f172a, #0a0f1d)',
          }}
        >
          <div>
            <div style={{ color: colors.textPrimary, fontSize: '0.96rem', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📍</span> SELECT INCIDENT LOCATION
              <span
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid #10b981',
                  color: '#34d399',
                  padding: '2px 8px',
                  borderRadius: radii.full,
                  fontSize: '0.66rem',
                  fontWeight: '700',
                  letterSpacing: '0.04em',
                }}
              >
                ● 100% OFFLINE GEOSPATIAL MAP (TELANGANA)
              </span>
              {isTilesLoading && (
                <span
                  style={{
                    background: 'rgba(56, 189, 248, 0.12)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    color: colors.accent,
                    padding: '2px 8px',
                    borderRadius: radii.full,
                    fontSize: '0.66rem',
                    fontWeight: '600',
                  }}
                >
                  ● Streaming Sector Roads...
                </span>
              )}
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.74rem', marginTop: '2px' }}>
              Click anywhere to place the pin or drag it to the exact incident position • WGS84 Geographic Coordinate System
            </div>
          </div>
          <button
            onClick={onCancel}
            style={{
              background: 'none',
              border: 'none',
              color: colors.textMuted,
              fontSize: '1.2rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Tactical Search & Quick Sector Bar */}
        <div
          style={{
            padding: '10px 20px',
            background: 'rgba(15, 23, 42, 0.95)',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            gap: '10px',
            alignItems: 'center',
            flexWrap: 'wrap',
            fontSize: '0.74rem',
            position: 'relative',
          }}
        >
          {/* Offline Local Gazetteer Search */}
          <div style={{ position: 'relative', flex: '1 1 240px', minWidth: '220px' }}>
            <input
              type="text"
              placeholder="🔍 Search place (e.g. Charminar, Warangal, Gachibowli)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                background: '#070b14',
                border: '1px solid #334155',
                borderRadius: radii.sm,
                color: '#f8fafc',
                padding: '6px 10px',
                fontSize: '0.74rem',
                outline: 'none',
              }}
            />
            {isSearching && searchResults.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: '4px',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: radii.sm,
                  boxShadow: shadows.elevated,
                  zIndex: 10002,
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              >
                {searchResults.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => flyToCoord(item.lon, item.lat, item.category === 'City / Town' ? 12 : 14)}
                    style={{
                      padding: '8px 12px',
                      borderBottom: '1px solid #1e293b',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#1e293b')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <div>
                      <div style={{ color: '#f8fafc', fontWeight: '700', fontSize: '0.76rem' }}>{item.name}</div>
                      <div style={{ color: '#94a3b8', fontSize: '0.68rem' }}>{item.label}</div>
                    </div>
                    <span
                      style={{
                        fontSize: '0.62rem',
                        background: 'rgba(56, 189, 248, 0.15)',
                        color: colors.accent,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: '700',
                      }}
                    >
                      {item.category}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Focus Sector Buttons */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: colors.textMuted, fontSize: '0.70rem' }}>Sectors:</span>
            <button
              type="button"
              onClick={() => flyToCoord(78.4867, 17.3850, 13)}
              style={{
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                color: colors.accent,
                borderRadius: radii.sm,
                padding: '4px 8px',
                fontSize: '0.70rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              📍 Hyderabad
            </button>
            <button
              type="button"
              onClick={() => flyToCoord(79.6000, 17.9500, 11.5)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid #334155',
                color: colors.textPrimary,
                borderRadius: radii.sm,
                padding: '4px 8px',
                fontSize: '0.70rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              📍 Warangal
            </button>
            <button
              type="button"
              onClick={() => flyToCoord(78.1000, 18.6725, 11.5)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid #334155',
                color: colors.textPrimary,
                borderRadius: radii.sm,
                padding: '4px 8px',
                fontSize: '0.70rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              📍 Nizamabad
            </button>
            <button
              type="button"
              onClick={() => flyToCoord(79.1333, 18.4333, 11.5)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid #334155',
                color: colors.textPrimary,
                borderRadius: radii.sm,
                padding: '4px 8px',
                fontSize: '0.70rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              📍 Karimnagar
            </button>
            <button
              type="button"
              onClick={() => flyToCoord(79.0, 17.8, 7.2)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid #334155',
                color: colors.textMuted,
                borderRadius: radii.sm,
                padding: '4px 8px',
                fontSize: '0.70rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              🌍 Telangana Regional
            </button>
            {userLocation && (
              <button
                type="button"
                onClick={() => flyToCoord(userLocation.lon, userLocation.lat, 13)}
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid #10b981',
                  color: '#34d399',
                  borderRadius: radii.sm,
                  padding: '4px 8px',
                  fontSize: '0.70rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                🎯 My Location
              </button>
            )}
          </div>
        </div>

        {/* Map Container Area */}
        <div style={{ position: 'relative', width: '100%', height: '480px', background: '#060a12' }}>
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

          {/* Floating Zoom & Map Controls */}
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              zIndex: 10,
            }}
          >
            <button
              type="button"
              onClick={() => mapRef.current?.zoomIn()}
              title="Zoom In"
              style={{
                width: '32px',
                height: '32px',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                borderRadius: radii.sm,
                fontSize: '1.1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              +
            </button>
            <button
              type="button"
              onClick={() => mapRef.current?.zoomOut()}
              title="Zoom Out"
              style={{
                width: '32px',
                height: '32px',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                borderRadius: radii.sm,
                fontSize: '1.1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              −
            </button>
            <button
              type="button"
              onClick={() => flyToCoord(79.0, 17.8, 7.2)}
              title="Reset View"
              style={{
                width: '32px',
                height: '32px',
                background: '#0f172a',
                border: '1px solid #334155',
                color: colors.accent,
                borderRadius: radii.sm,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              ↺
            </button>
          </div>

          {/* Floating Cartographic Legend & Zoom Level */}
          <div
            style={{
              position: 'absolute',
              bottom: '10px',
              left: '12px',
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(6px)',
              border: '1px solid #334155',
              borderRadius: radii.sm,
              padding: '6px 10px',
              fontSize: '0.68rem',
              color: '#94a3b8',
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              zIndex: 10,
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '12px', height: '3px', background: '#f59e0b', display: 'inline-block' }} /> National Highway
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '12px', height: '2px', background: '#38bdf8', display: 'inline-block' }} /> Primary / Arterial
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '12px', height: '2px', background: '#94a3b8', display: 'inline-block' }} /> Local Street
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', background: '#0369a1', border: '1px solid #38bdf8', display: 'inline-block' }} /> Water Body
            </span>
            <span style={{ color: '#f8fafc', fontWeight: 'bold', fontFamily: fonts.mono, marginLeft: '6px' }}>
              Zoom: {currentZoom.toFixed(1)}
            </span>
          </div>
        </div>

        {/* Live Coordinate Status & Confirmation Footer */}
        <div
          style={{
            padding: '14px 20px',
            borderTop: '1px solid #1e293b',
            background: 'rgba(0, 0, 0, 0.35)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: colors.accent, fontSize: '0.76rem', fontWeight: '800' }}>
                SELECTED COORDINATES:
              </span>
              <span style={{ color: colors.textPrimary, fontSize: '0.86rem', fontWeight: '700', fontFamily: fonts.mono }}>
                {lat.toFixed(6)}°, {lon.toFixed(6)}°
              </span>
              <span
                style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  color: colors.accent,
                  padding: '1px 6px',
                  borderRadius: radii.sm,
                  fontSize: '0.66rem',
                  fontWeight: '700',
                }}
              >
                MANUAL MAP PIN
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: colors.textMuted }}>
              Source: <strong style={{ color: colors.textPrimary }}>MANUAL MAP SELECTION</strong> • Accuracy:{' '}
              <strong style={{ color: '#fbbf24' }}>USER SELECTED / NOT GNSS VERIFIED</strong>
            </div>
            {resolvedAddress && (
              <div style={{ fontSize: '0.72rem', color: colors.accent, fontWeight: '600' }}>
                📍 {resolvedAddress}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: '1px solid #334155',
                color: colors.textSecondary,
                borderRadius: radii.md,
                fontSize: '0.80rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => onConfirm({ lat, lon, address: resolvedAddress })}
              style={{
                padding: '8px 20px',
                background: colors.accent,
                border: 'none',
                color: '#070B14',
                borderRadius: radii.md,
                fontSize: '0.82rem',
                fontWeight: '800',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: shadows.glowCyan,
              }}
            >
              <span>✓</span> Use This Location
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
