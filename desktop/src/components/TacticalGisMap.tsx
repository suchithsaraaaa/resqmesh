import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapIncidentMarker } from './MapView';
import worldCountriesData from '../assets/world-countries.json';
import telanganaBoundaryData from '../assets/geo/telangana-boundary.json';
import telanganaDistrictsData from '../assets/geo/telangana-districts.json';
import telanganaHighwaysData from '../assets/geo/telangana-highways.json';
import telanganaRoadsData from '../assets/geo/telangana-roads.json';
import telanganaCitiesData from '../assets/geo/telangana-cities.json';
import hyderabadRoadsData from '../assets/geo/hyderabad-roads.json';
import hyderabadWaterData from '../assets/geo/hyderabad-water.json';
import hyderabadPlacesData from '../assets/geo/hyderabad-places.json';
import { LocationService } from '../services/LocationService';

interface TacticalGisMapProps {
  incidents: MapIncidentMarker[];
  selectedIncidentId?: string | null;
  onSelectIncident: (id: string) => void;
  onOpenDetailsModal?: (incident: MapIncidentMarker) => void;
  // Interactive Location Acquisition Mode ("Pick on Map")
  isPickingLocation?: boolean;
  onLocationPicked?: (coords: { lat: number; lon: number }) => void;
  pickedCoords?: { lat: number; lon: number } | null;
  onCancelPickLocation?: () => void;
  userLocation?: { lat: number; lon: number } | null;
}

export const TacticalGisMap: React.FC<TacticalGisMapProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onOpenDetailsModal,
  isPickingLocation = false,
  onLocationPicked,
  pickedCoords,
  onCancelPickLocation,
  userLocation,
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const isMapLoadedRef = useRef<boolean>(false);
  const clusterMarkersRef = useRef<maplibregl.Marker[]>([]);
  const autoRotateIntervalRef = useRef<number | null>(null);
  const prevSelectedIncidentIdRef = useRef<string | null>(null);

  // Direct DOM refs for HUD to prevent ANY React re-render during zoom/pan
  const hudZoomRef = useRef<HTMLElement | null>(null);
  const hudCoordsRef = useRef<HTMLElement | null>(null);
  const hudDepthRef = useRef<HTMLElement | null>(null);

  // Stable callback refs so they never trigger effect dependencies
  const onSelectIncidentRef = useRef(onSelectIncident);
  onSelectIncidentRef.current = onSelectIncident;

  const onOpenDetailsModalRef = useRef(onOpenDetailsModal);
  onOpenDetailsModalRef.current = onOpenDetailsModal;

  const onLocationPickedRef = useRef(onLocationPicked);
  onLocationPickedRef.current = onLocationPicked;

  const incidentsRef = useRef(incidents);
  incidentsRef.current = incidents;

  const isPickingRef = useRef(isPickingLocation);
  isPickingRef.current = isPickingLocation;

  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [view3D, setView3D] = useState<boolean>(false);
  const [showUnmappedDrawer, setShowUnmappedDrawer] = useState<boolean>(false);
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  // Prepare GeoJSON for incidents with micro-radial separation for co-located points
  const incidentsGeoJson = useMemo(() => {
    const validIncidents = incidents.filter(
      (inc) => inc.lat !== null && inc.lon !== null && !isNaN(inc.lat) && !isNaN(inc.lon)
    );

    const coordCounts: Record<string, number> = {};

    const features = validIncidents.map((inc) => {
      const baseKey = `${inc.lat!.toFixed(4)}_${inc.lon!.toFixed(4)}`;
      const indexAtCoord = coordCounts[baseKey] || 0;
      coordCounts[baseKey] = indexAtCoord + 1;

      let lon = inc.lon!;
      let lat = inc.lat!;
      if (indexAtCoord > 0) {
        const angle = ((indexAtCoord * 75) * Math.PI) / 180;
        const offsetDeg = 0.00018; // ~18 meters visual separation
        lon = lon + offsetDeg * Math.cos(angle);
        lat = lat + offsetDeg * Math.sin(angle);
      }

      return {
        type: 'Feature' as const,
        id: inc.id,
        properties: {
          id: inc.id,
          title: inc.title,
          category: inc.category,
          severity: inc.severity,
          reportCount: inc.reportCount,
          broadcasterName: inc.broadcasterName || 'Commander',
          summary: inc.summary || '',
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [lon, lat], // GeoJSON format: [longitude, latitude]
        },
      };
    });

    return {
      type: 'FeatureCollection' as const,
      features,
    };
  }, [incidents]);

  const incidentsWithoutCoords = useMemo(() => {
    return incidents.filter((i) => i.lat === null || i.lon === null || isNaN(i.lat) || isNaN(i.lon));
  }, [incidents]);

  // Clean cluster badges
  const clearClusterMarkers = () => {
    clusterMarkersRef.current.forEach((m) => m.remove());
    clusterMarkersRef.current = [];
  };

  // Update cluster number badges on map canvas
  const updateClusterBadges = () => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    clearClusterMarkers();

    try {
      const features = map.queryRenderedFeatures({ layers: ['incident-clusters'] });
      const processedIds = new Set<string>();

      features.forEach((feature) => {
        const clusterId = feature.properties?.cluster_id;
        const pointCount = feature.properties?.point_count;
        if (!clusterId || !pointCount || processedIds.has(clusterId)) return;
        processedIds.add(clusterId);

        const coords = (feature.geometry as any).coordinates;
        if (!coords || coords.length < 2) return;

        const el = document.createElement('div');
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.color = '#ffffff';
        el.style.fontWeight = '900';
        el.style.fontSize = pointCount > 99 ? '10px' : '11px';
        el.style.pointerEvents = 'none';
        el.style.textShadow = '0 1px 3px rgba(0,0,0,0.9)';
        el.innerText = String(pointCount);

        const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
          .setLngLat(coords as [number, number])
          .addTo(map);

        clusterMarkersRef.current.push(marker);
      });
    } catch {
      // Ignore during transitions
    }
  };

  // Helper to determine depth label for HUD
  const getDepthLabel = (z: number) => {
    if (z < 5.0) return '🌍 3D Global Earth (Overview)';
    if (z < 7.5) return '🏛️ Telangana State Overview (33 Districts)';
    if (z < 9.5) return '🛣️ Hyderabad Metro Outer Ring & Major Arterials';
    if (z < 12.5) return '🏙️ Hyderabad Urban Grid & Secondary Avenues';
    return '🏘️ Hyderabad Street-Level Network & Lanes (100% Offline)';
  };

  // =========================================================================
  // ONE-TIME MAP INITIALIZATION (LIFECYCLE STRICTLY SEPARATED FROM STATE)
  // =========================================================================
  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        name: 'ResQMesh Telangana Tactical GIS',
        sources: {
          'world-countries': {
            type: 'geojson',
            data: worldCountriesData as any,
          },
          'telangana-boundary': {
            type: 'geojson',
            data: telanganaBoundaryData as any,
          },
          'telangana-districts': {
            type: 'geojson',
            data: telanganaDistrictsData as any,
          },
          'telangana-highways': {
            type: 'geojson',
            data: telanganaHighwaysData as any,
          },
          'telangana-roads': {
            type: 'geojson',
            data: telanganaRoadsData as any,
          },
          'telangana-cities': {
            type: 'geojson',
            data: telanganaCitiesData as any,
          },
          'urban-streets': {
            type: 'geojson',
            data: hyderabadRoadsData as any,
          },
          'hyderabad-water': {
            type: 'geojson',
            data: hyderabadWaterData as any,
          },
          'hyderabad-places': {
            type: 'geojson',
            data: hyderabadPlacesData as any,
          },
          'incidents': {
            type: 'geojson',
            data: incidentsGeoJson as any,
            cluster: true,
            clusterMaxZoom: 11, // Past zoom 11, clusters decompose into individual pins
            clusterRadius: 40,
          },
          'target-pick': {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: [],
            },
          },
          'user-location': {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: [],
            },
          },
        },
        layers: [
          // 1. Deep Space Cosmic Background
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#020617',
            },
          },
          // 2. Global Ocean Base
          {
            id: 'world-ocean-glow',
            type: 'background',
            paint: {
              'background-color': '#040b17',
            },
          },
          // 3. Global Landmass Fill (CONTINUOUS AT ALL ZOOMS — NEVER TERMINATES INTO BLACK VOID)
          {
            id: 'world-countries-fill',
            type: 'fill',
            source: 'world-countries',
            paint: {
              'fill-color': '#0c1e33',
              'fill-opacity': 0.96,
            },
          },
          // 4. Sovereign International & Regional Boundaries
          {
            id: 'world-countries-line',
            type: 'line',
            source: 'world-countries',
            paint: {
              'line-color': '#1d4ed8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 1, 0.8, 6, 1.8, 12, 3.0],
              'line-opacity': 0.85,
            },
          },
          // 5. Telangana State Boundary Fill (Subtle Area Highlight)
          {
            id: 'telangana-boundary-fill',
            type: 'fill',
            source: 'telangana-boundary',
            paint: {
              'fill-color': '#0e2b4d',
              'fill-opacity': 0.35,
            },
          },
          // 6. Telangana State Outer Boundary Line
          {
            id: 'telangana-boundary-line',
            type: 'line',
            source: 'telangana-boundary',
            paint: {
              'line-color': '#0284c7',
              'line-width': ['interpolate', ['linear'], ['zoom'], 4, 1.5, 8, 3.0, 14, 5.0],
              'line-opacity': 0.95,
            },
          },
          // 7. Telangana 33 Districts Fill
          {
            id: 'telangana-districts-fill',
            type: 'fill',
            source: 'telangana-districts',
            minzoom: 5.0,
            paint: {
              'fill-color': '#0e2b4d',
              'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.25, 8, 0.38, 12, 0.15],
            },
          },
          // 8. Telangana 33 Districts Boundary Lines (Crisp Cyan Grid, subtle at city zoom)
          {
            id: 'telangana-districts-line',
            type: 'line',
            source: 'telangana-districts',
            minzoom: 5.0,
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 8, 1.4, 10, 0.6, 12, 0.2],
              'line-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 8, 0.6, 9.5, 0.15, 11, 0.05],
            },
          },
          // 8b. Hyderabad Iconic Water Bodies (Hussain Sagar, Osman Sagar, Himayat Sagar, Durgam Cheruvu, etc.)
          {
            id: 'hyderabad-water-fill',
            type: 'fill',
            source: 'hyderabad-water',
            minzoom: 7.0,
            paint: {
              'fill-color': '#0369a1',
              'fill-opacity': ['interpolate', ['linear'], ['zoom'], 7, 0.45, 10, 0.65, 14, 0.8],
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
              'line-opacity': 0.85,
            },
          },
          // 9. Continuous State Arterial Roads Casing
          {
            id: 'telangana-roads-casing',
            type: 'line',
            source: 'telangana-roads',
            minzoom: 6.0,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.5, 9, 3.2, 14, 5.5],
            },
          },
          // 10. Continuous State Arterial Roads Line (SH 1, SH 2, SH 4, SH 7, RRR, etc.)
          {
            id: 'telangana-roads-line',
            type: 'line',
            source: 'telangana-roads',
            minzoom: 6.0,
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.0, 9, 2.0, 14, 3.8],
              'line-opacity': 0.9,
            },
          },
          // 11. National Highways Casing
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
          // 12. National Highways Line (Tactical Amber Corridors: NH 44, NH 65, NH 163, NH 765, ORR)
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
          // 13. High-Detail Hyderabad Urban Streets Casing (Zoom >= 8.0: Outer Ring Road, Inner Ring Road, Radial Roads)
          {
            id: 'urban-streets-casing',
            type: 'line',
            source: 'urban-streets',
            minzoom: 8.0,
            paint: {
              'line-color': '#020617',
              'line-width': ['interpolate', ['linear'], ['zoom'], 8, 1.2, 10, 2.2, 13, 4.0, 16, 7.5],
            },
          },
          // 14. High-Detail Hyderabad Urban Streets Primary Arterials (Motorways, Trunks, Primaries, Expressways)
          {
            id: 'urban-streets-primary',
            type: 'line',
            source: 'urban-streets',
            minzoom: 8.0,
            filter: ['in', ['get', 'highway'], ['literal', ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link']]],
            paint: {
              'line-color': '#38bdf8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 8, 1.0, 10, 2.0, 13, 3.4, 16, 6.0],
              'line-opacity': 0.95,
            },
          },
          // 15. High-Detail Hyderabad Urban Streets Secondary & Tertiary
          {
            id: 'urban-streets-secondary',
            type: 'line',
            source: 'urban-streets',
            minzoom: 9.0,
            filter: ['in', ['get', 'highway'], ['literal', ['secondary', 'secondary_link', 'tertiary', 'tertiary_link']]],
            paint: {
              'line-color': '#60a5fa',
              'line-width': ['interpolate', ['linear'], ['zoom'], 9, 0.8, 11, 1.6, 14, 2.6, 16, 4.5],
              'line-opacity': 0.9,
            },
          },
          // 16. High-Detail Hyderabad Urban Streets Local, Residential & Colony Lanes
          {
            id: 'urban-streets-local',
            type: 'line',
            source: 'urban-streets',
            minzoom: 10.2,
            filter: ['!', ['in', ['get', 'highway'], ['literal', ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']]]],
            paint: {
              'line-color': '#94a3b8',
              'line-width': ['interpolate', ['linear'], ['zoom'], 10.2, 0.6, 12, 1.1, 14, 1.8, 16, 3.2],
              'line-opacity': ['interpolate', ['linear'], ['zoom'], 10.2, 0.45, 12, 0.75, 14, 0.92],
            },
          },
          // 17. High-Detail Street Name Labels (Zoom >= 13.0)
          {
            id: 'urban-streets-labels',
            type: 'symbol',
            source: 'urban-streets',
            minzoom: 13.0,
            filter: ['has', 'name'],
            layout: {
              'symbol-placement': 'line',
              'text-field': ['get', 'name'],
              'text-size': ['interpolate', ['linear'], ['zoom'], 13, 9, 15, 11, 17, 13],
              'text-max-angle': 30,
              'text-padding': 3,
            },
            paint: {
              'text-color': '#cbd5e1',
              'text-halo-color': '#020617',
              'text-halo-width': 1.5,
            },
          },
          // 18. Hyderabad Tactical Place / Neighborhood Labels (Charminar, Madhapur, Gachibowli, etc.)
          {
            id: 'hyderabad-places-labels',
            type: 'symbol',
            source: 'hyderabad-places',
            minzoom: 9.0,
            layout: {
              'text-field': ['get', 'name'],
              'text-size': ['interpolate', ['linear'], ['zoom'], 9, 10, 12, 12, 15, 14],
              'text-anchor': 'top',
              'text-offset': [0, 0.5],
            },
            paint: {
              'text-color': '#f8fafc',
              'text-halo-color': '#020617',
              'text-halo-width': 2.0,
              'text-opacity': ['interpolate', ['linear'], ['zoom'], 9, 0.8, 11, 0.95],
            },
          },
          // 17. Strategic Cities Glow
          {
            id: 'cities-glow',
            type: 'circle',
            source: 'telangana-cities',
            minzoom: 5.5,
            paint: {
              'circle-color': '#0284c7',
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 5.5, 4, 8, 7, 13, 11],
              'circle-opacity': 0.35,
            },
          },
          // 18. Strategic Cities Core
          {
            id: 'cities-point',
            type: 'circle',
            source: 'telangana-cities',
            minzoom: 5.5,
            paint: {
              'circle-color': [
                'match',
                ['get', 'tier'],
                1,
                '#38bdf8',
                2,
                '#60a5fa',
                '#94a3b8',
              ],
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 5.5, 2.5, 8, 4.2, 13, 6.0],
              'circle-stroke-width': 1.2,
              'circle-stroke-color': '#ffffff',
            },
          },
          // 19. Incident Clusters (WebGL Circles)
          {
            id: 'incident-clusters',
            type: 'circle',
            source: 'incidents',
            filter: ['has', 'point_count'],
            paint: {
              'circle-color': [
                'step',
                ['get', 'point_count'],
                '#f97316',
                5,
                '#ef4444',
                20,
                '#dc2626',
              ],
              'circle-radius': [
                'step',
                ['get', 'point_count'],
                16,
                5,
                20,
                20,
                26,
              ],
              'circle-stroke-width': 2.5,
              'circle-stroke-color': '#ffffff',
              'circle-opacity': 0.95,
            },
          },
          // 20. Critical Incident Beacon Pulse
          {
            id: 'incident-pulse',
            type: 'circle',
            source: 'incidents',
            filter: ['all', ['!', ['has', 'point_count']], ['==', ['get', 'severity'], 'critical']],
            paint: {
              'circle-color': '#ef4444',
              'circle-radius': 18,
              'circle-opacity': 0.35,
              'circle-stroke-width': 1.2,
              'circle-stroke-color': '#ef4444',
            },
          },
          // 21. REAL Incident Dots
          {
            id: 'incident-unclustered-point',
            type: 'circle',
            source: 'incidents',
            filter: ['!', ['has', 'point_count']],
            paint: {
              'circle-color': [
                'match',
                ['get', 'severity'],
                'critical',
                '#ef4444',
                'high',
                '#f97316',
                'medium',
                '#f59e0b',
                '#10b981', // low
              ],
              'circle-radius': 9,
              'circle-stroke-width': 2.5,
              'circle-stroke-color': '#ffffff',
              'circle-opacity': 1.0,
            },
          },
          // 22. Target Pick Marker (When Pick on Map is active)
          {
            id: 'target-pick-halo',
            type: 'circle',
            source: 'target-pick',
            paint: {
              'circle-color': '#0284c7',
              'circle-radius': 22,
              'circle-opacity': 0.4,
              'circle-stroke-width': 2.0,
              'circle-stroke-color': '#38bdf8',
            },
          },
          {
            id: 'target-pick-point',
            type: 'circle',
            source: 'target-pick',
            paint: {
              'circle-color': '#38bdf8',
              'circle-radius': 7,
              'circle-stroke-width': 2.5,
              'circle-stroke-color': '#ffffff',
            },
          },
          // 23. User / Device Location Beacon
          {
            id: 'user-location-halo',
            type: 'circle',
            source: 'user-location',
            paint: {
              'circle-color': '#10b981',
              'circle-radius': 18,
              'circle-opacity': 0.3,
              'circle-stroke-width': 1.5,
              'circle-stroke-color': '#34d399',
            },
          },
          {
            id: 'user-location-point',
            type: 'circle',
            source: 'user-location',
            paint: {
              'circle-color': '#10b981',
              'circle-radius': 6,
              'circle-stroke-width': 2.0,
              'circle-stroke-color': '#ffffff',
            },
          },
        ],
      },
      center: [79.0000, 17.8000], // Centered directly on Telangana Regional Hub
      zoom: 7.2, // Clean regional overview
      minZoom: 1.5,
      maxZoom: 18.5,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
    });

    mapRef.current = map;

    // Apply native True 3D Globe Projection
    map.on('style.load', () => {
      try {
        if (typeof (map as any).setProjection === 'function') {
          (map as any).setProjection({ type: 'globe' });
        }
      } catch (projErr) {
        console.warn('[TacticalGisMap] Projection set warning:', projErr);
      }
    });

    // Direct HUD DOM updates on zoom and pan (Zero React state updates = Zero resets!)
    map.on('zoom', () => {
      const z = map.getZoom();
      if (hudZoomRef.current) hudZoomRef.current.innerText = z.toFixed(1);
      if (hudDepthRef.current) hudDepthRef.current.innerText = getDepthLabel(z);
    });

    map.on('mousemove', (e) => {
      if (hudCoordsRef.current) {
        hudCoordsRef.current.innerText = `📍 ${e.lngLat.lat.toFixed(4)}°N, ${e.lngLat.lng.toFixed(4)}°E`;
      }
    });

    // Clean cluster badges on camera movement
    map.on('moveend', () => {
      updateClusterBadges();
    });

    // Auto-pause auto-rotation on any user manual interaction
    const pauseRotation = () => {
      setAutoRotate(false);
    };
    map.on('dragstart', pauseRotation);
    map.on('zoomstart', pauseRotation);
    map.on('rotatestart', pauseRotation);
    map.on('pitchstart', pauseRotation);

    map.on('load', () => {
      isMapLoadedRef.current = true;
      updateClusterBadges();

      // Asynchronously load complete continuous Hyderabad roads dataset (175,803 ways)
      const loadRoads = async () => {
        try {
          let data = null;
          if ((window as any).resqmeshAPI?.loadGeoJson) {
            data = await (window as any).resqmeshAPI.loadGeoJson('geo/hyderabad-arterials.json');
          }
          if (!data) {
            try {
              const resp = await fetch('./geo/hyderabad-arterials.json');
              if (resp.ok) data = await resp.json();
            } catch {}
          }
          if (!data) {
            try {
              const resp = await fetch('/geo/hyderabad-arterials.json');
              if (resp.ok) data = await resp.json();
            } catch {}
          }
          if (data && mapRef.current) {
            const src = mapRef.current.getSource('urban-streets') as maplibregl.GeoJSONSource;
            if (src) {
              src.setData(data);
              console.log('[TacticalGisMap] Successfully streamed complete Hyderabad roads dataset (175,803 features)');
            }
          }
        } catch (err) {
          console.warn('[TacticalGisMap] Error loading complete Hyderabad roads:', err);
        }
      };
      loadRoads();
    });

    // Map Click Handler: supports Location Picking mode and Incident clicks
    map.on('click', (e) => {
      if (isPickingRef.current && onLocationPickedRef.current) {
        const lat = Number(e.lngLat.lat.toFixed(6));
        const lon = Number(e.lngLat.lng.toFixed(6));

        // Validate coordinate falls within Telangana bounding area
        if (!LocationService.isInsideTelangana(lat, lon)) {
          alert('Selected location falls outside Telangana. Please select a point within the Telangana operational zone.');
          return;
        }

        onLocationPickedRef.current({ lat, lon });
      }
    });

    // Cluster click: smooth expansion zoom
    map.on('click', 'incident-clusters', async (e) => {
      if (isPickingRef.current) return;
      const features = map.queryRenderedFeatures(e.point, { layers: ['incident-clusters'] });
      if (!features.length) return;
      const clusterId = features[0].properties?.cluster_id;
      const source = map.getSource('incidents') as maplibregl.GeoJSONSource;
      if (source && clusterId) {
        try {
          const zoom = await source.getClusterExpansionZoom(clusterId);
          map.easeTo({
            center: (features[0].geometry as any).coordinates,
            zoom: Math.min(zoom + 0.8, 16.5),
            duration: 600,
          });
        } catch {
          // Ignore
        }
      }
    });

    // Unclustered incident click
    map.on('click', 'incident-unclustered-point', (e) => {
      if (isPickingRef.current) return;
      const feature = e.features?.[0];
      if (feature && feature.properties?.id) {
        const id = feature.properties.id;
        onSelectIncidentRef.current(id);
        const inc = incidentsRef.current.find((i) => i.id === id);
        if (inc && onOpenDetailsModalRef.current) {
          onOpenDetailsModalRef.current(inc);
        }
      }
    });

    // Hover effect over districts
    map.on('mouseenter', 'telangana-districts-fill', (e) => {
      const dist = e.features?.[0]?.properties?.district;
      const hq = e.features?.[0]?.properties?.hq;
      if (dist) setHoveredFeature(`🏛️ ${dist} District (HQ: ${hq || dist})`);
    });
    map.on('mouseleave', 'telangana-districts-fill', () => {
      setHoveredFeature(null);
    });

    // Hover effect over cities
    map.on('mouseenter', 'cities-point', (e) => {
      const name = e.features?.[0]?.properties?.name;
      const district = e.features?.[0]?.properties?.district;
      const pop = e.features?.[0]?.properties?.population;
      if (name) setHoveredFeature(`🏙️ ${name}, ${district} District (Pop: ${pop || 'N/A'})`);
    });
    map.on('mouseleave', 'cities-point', () => {
      setHoveredFeature(null);
    });

    // Hover effect over highways
    map.on('mouseenter', 'telangana-highways-line', (e) => {
      const ref = e.features?.[0]?.properties?.ref;
      const name = e.features?.[0]?.properties?.name;
      if (ref) setHoveredFeature(`🛣️ ${ref}: ${name}`);
    });
    map.on('mouseleave', 'telangana-highways-line', () => {
      setHoveredFeature(null);
    });

    // Hover effect over state roads
    map.on('mouseenter', 'telangana-roads-line', (e) => {
      const ref = e.features?.[0]?.properties?.ref;
      const name = e.features?.[0]?.properties?.name;
      if (ref) setHoveredFeature(`🛣️ ${ref || 'State Route'}: ${name}`);
    });
    map.on('mouseleave', 'telangana-roads-line', () => {
      setHoveredFeature(null);
    });

    // Hover effect over incidents
    map.on('mouseenter', 'incident-unclustered-point', (e) => {
      if (isPickingRef.current) return;
      map.getCanvas().style.cursor = 'pointer';
      const title = e.features?.[0]?.properties?.title;
      const severity = e.features?.[0]?.properties?.severity;
      if (title) setHoveredFeature(`🚨 Incident: ${title} (${(severity || 'medium').toUpperCase()})`);
    });
    map.on('mouseleave', 'incident-unclustered-point', () => {
      map.getCanvas().style.cursor = isPickingRef.current ? 'crosshair' : '';
      setHoveredFeature(null);
    });

    // Hover effect over clusters
    map.on('mouseenter', 'incident-clusters', (e) => {
      if (isPickingRef.current) return;
      map.getCanvas().style.cursor = 'pointer';
      const count = e.features?.[0]?.properties?.point_count;
      if (count) setHoveredFeature(`🚨 Incident Cluster: ${count} incidents (click to expand)`);
    });
    map.on('mouseleave', 'incident-clusters', () => {
      map.getCanvas().style.cursor = isPickingRef.current ? 'crosshair' : '';
      setHoveredFeature(null);
    });

    // Clean up ONLY on component unmount
    return () => {
      clearClusterMarkers();
      if (autoRotateIntervalRef.current) {
        clearInterval(autoRotateIntervalRef.current);
      }
      map.remove();
      mapRef.current = null;
      isMapLoadedRef.current = false;
    };
  }, []); // EMPTY DEPENDENCY ARRAY: INITIALIZED EXACTLY ONCE!

  // =========================================================================
  // DATA-ONLY SYNCHRONIZATION (NEVER RESETS CAMERA, NEVER RECREATES MAP)
  // =========================================================================
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    const source = map.getSource('incidents') as maplibregl.GeoJSONSource;
    if (source) {
      source.setData(incidentsGeoJson as any);
      setTimeout(() => updateClusterBadges(), 60);
    }
  }, [incidentsGeoJson]);

  // Update cursor when picking location
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.getCanvas().style.cursor = isPickingLocation ? 'crosshair' : '';
  }, [isPickingLocation]);

  // Synchronize target-pick marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;
    const source = map.getSource('target-pick') as maplibregl.GeoJSONSource;
    if (!source) return;

    if (pickedCoords && pickedCoords.lat && pickedCoords.lon) {
      source.setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'Point',
              coordinates: [pickedCoords.lon, pickedCoords.lat],
            },
          },
        ],
      });
    } else {
      source.setData({
        type: 'FeatureCollection',
        features: [],
      });
    }
  }, [pickedCoords]);

  // Synchronize user device location marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;
    const source = map.getSource('user-location') as maplibregl.GeoJSONSource;
    if (!source) return;

    if (userLocation && userLocation.lat && userLocation.lon) {
      source.setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'Point',
              coordinates: [userLocation.lon, userLocation.lat],
            },
          },
        ],
      });
    } else {
      source.setData({
        type: 'FeatureCollection',
        features: [],
      });
    }
  }, [userLocation]);

  // =========================================================================
  // USER-INITIATED INCIDENT SELECTION CAMERA ANIMATION
  // =========================================================================
  useEffect(() => {
    if (!selectedIncidentId || !mapRef.current || !isMapLoadedRef.current) return;

    if (prevSelectedIncidentIdRef.current === null) {
      prevSelectedIncidentIdRef.current = selectedIncidentId;
      return;
    }
    if (prevSelectedIncidentIdRef.current === selectedIncidentId) {
      return;
    }
    prevSelectedIncidentIdRef.current = selectedIncidentId;

    const inc = incidents.find((i) => i.id === selectedIncidentId);
    if (inc && inc.lat !== null && inc.lon !== null && !isNaN(inc.lat) && !isNaN(inc.lon)) {
      mapRef.current.easeTo({
        center: [inc.lon, inc.lat],
        duration: 700,
      });
    }
  }, [incidents, selectedIncidentId]);

  // =========================================================================
  // AUTO-ROTATE LOOP (SMOOTH CONTINUOUS BEARING)
  // =========================================================================
  useEffect(() => {
    if (autoRotate) {
      autoRotateIntervalRef.current = window.setInterval(() => {
        const map = mapRef.current;
        if (map) {
          const newBearing = (map.getBearing() + 0.3) % 360;
          map.setBearing(newBearing);
        }
      }, 40);
    } else {
      if (autoRotateIntervalRef.current) {
        clearInterval(autoRotateIntervalRef.current);
        autoRotateIntervalRef.current = null;
      }
    }
    return () => {
      if (autoRotateIntervalRef.current) {
        clearInterval(autoRotateIntervalRef.current);
      }
    };
  }, [autoRotate]);

  // Toggle 3D Perspective Pitch smoothly
  const toggle3DPerspective = () => {
    const map = mapRef.current;
    if (!map) return;
    const targetPitch = view3D ? 0 : 55;
    map.easeTo({ pitch: targetPitch, duration: 800 });
    setView3D(!view3D);
  };

  // Reset View: Returns camera to Telangana 3D regional overview
  const handleResetView = () => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({
      center: [79.0000, 17.8000],
      zoom: 7.2,
      pitch: 0,
      bearing: 0,
      duration: 1100,
    });
  };

  // Fly directly to Telangana Sector
  const handleFlyToTelangana = () => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({
      center: [79.0000, 17.8000],
      zoom: 7.5,
      pitch: view3D ? 45 : 0,
      duration: 1000,
    });
  };

  // Fly directly to Hyderabad Metro City & All Street Grids
  const handleFlyToHyderabad = () => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({
      center: [78.4747, 17.4000],
      zoom: 11.4,
      pitch: view3D ? 45 : 0,
      bearing: 0,
      duration: 1200,
    });
  };

  // Go to Current Location: ONLY executed when the commander explicitly clicks the button
  const handleGoToCurrentLocation = () => {
    const map = mapRef.current;
    if (!map) return;

    if (userLocation && userLocation.lat && userLocation.lon) {
      map.flyTo({
        center: [userLocation.lon, userLocation.lat],
        zoom: 15.0,
        pitch: view3D ? 45 : 0,
        duration: 1000,
      });
      return;
    }

    const cached = LocationService.getLastKnownLocation();
    if (cached && cached.latitude && cached.longitude) {
      map.flyTo({
        center: [cached.longitude, cached.latitude],
        zoom: 15.0,
        pitch: view3D ? 45 : 0,
        duration: 1000,
      });
    }
  };

  // Focus Incidents: Smoothly fit bounds to active incident collection
  const handleFocusIncidents = () => {
    const map = mapRef.current;
    if (!map) return;

    const mapped = incidents.filter(
      (i) => i.lat !== null && i.lon !== null && !isNaN(i.lat) && !isNaN(i.lon)
    );

    if (mapped.length === 0) return;

    if (mapped.length === 1) {
      map.flyTo({
        center: [mapped[0].lon!, mapped[0].lat!],
        zoom: 15.0,
        pitch: view3D ? 45 : 0,
        duration: 1100,
      });
      return;
    }

    const bounds = new maplibregl.LngLatBounds();
    mapped.forEach((inc) => bounds.extend([inc.lon!, inc.lat!]));
    map.fitBounds(bounds, {
      padding: 80,
      maxZoom: 15.2,
      duration: 1200,
    });
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '480px',
        borderRadius: '8px',
        overflow: 'hidden',
        background: '#020617', // Pitch dark tactical canvas container (ZERO WHITE FLASHES)
        border: '1px solid #1e293b',
      }}
    >
      {/* Target Acquisition Banner (Pick on Map Mode) */}
      {isPickingLocation && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(2, 132, 199, 0.95)',
            color: '#ffffff',
            padding: '8px 18px',
            borderRadius: '24px',
            fontSize: '0.82rem',
            fontWeight: '800',
            zIndex: 30,
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.6)',
            border: '1px solid #38bdf8',
          }}
        >
          <span>🎯 TARGET ACQUISITION: Click anywhere inside Telangana to place incident</span>
          {onCancelPickLocation && (
            <button
              type="button"
              onClick={onCancelPickLocation}
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.4)',
                color: '#ffffff',
                borderRadius: '12px',
                padding: '2px 10px',
                fontSize: '0.72rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          )}
        </div>
      )}

      {/* Persistent MapLibre Canvas Container (NEVER REMOUNTED) */}
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '480px',
          background: '#020617',
        }}
      />

      {/* Top Left: Tactical Controls Toolbar */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          display: 'flex',
          gap: '6px',
          flexWrap: 'wrap',
          zIndex: 10,
          background: 'rgba(15, 23, 42, 0.88)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '6px 8px',
        }}
      >
        <button
          type="button"
          onClick={() => setAutoRotate((prev) => !prev)}
          style={{
            background: autoRotate ? '#0284c7' : 'transparent',
            border: `1px solid ${autoRotate ? '#38bdf8' : '#334155'}`,
            color: autoRotate ? '#ffffff' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Toggle Auto-Rotation (automatically pauses upon map drag or zoom)"
        >
          <span>🔄</span> {autoRotate ? 'Rotating' : 'Auto-Rotate'}
        </button>

        <button
          type="button"
          onClick={toggle3DPerspective}
          style={{
            background: view3D ? '#0284c7' : 'transparent',
            border: `1px solid ${view3D ? '#38bdf8' : '#334155'}`,
            color: view3D ? '#ffffff' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Toggle 3D Tactical Perspective Pitch"
        >
          <span>🌐</span> {view3D ? '3D Perspective' : '2D Plan'}
        </button>

        <button
          type="button"
          onClick={handleResetView}
          style={{
            background: 'transparent',
            border: '1px solid #334155',
            color: '#cbd5e1',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Reset Camera to Telangana Regional Overview"
        >
          <span>🎯</span> Reset View
        </button>

        <button
          type="button"
          onClick={handleFlyToTelangana}
          style={{
            background: 'transparent',
            border: '1px solid #334155',
            color: '#38bdf8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Quick Jump to Telangana Regional Sector"
        >
          <span>🏛️</span> Telangana Sector
        </button>

        <button
          type="button"
          onClick={handleFlyToHyderabad}
          style={{
            background: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid #38bdf8',
            color: '#38bdf8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Zoom directly to complete Hyderabad street grid"
        >
          <span>🏙️</span> Hyderabad (All Roads)
        </button>

        <button
          type="button"
          onClick={handleGoToCurrentLocation}
          style={{
            background: 'transparent',
            border: '1px solid #334155',
            color: '#10b981',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Smoothly center map on active device / GPS coordinate"
        >
          <span>📍</span> Go To Current Location
        </button>

        <button
          type="button"
          onClick={handleFocusIncidents}
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            color: '#f87171',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          title="Smoothly fly to active incident area"
        >
          <span>🚨</span> Focus Incidents
        </button>
      </div>

      {/* Top Right: Offline Status Pill */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(15, 23, 42, 0.88)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '6px 10px',
          color: '#10b981',
          fontSize: '0.72rem',
          fontWeight: '700',
          zIndex: 10,
        }}
      >
        <span style={{ animation: 'pulse 1.5s infinite' }}>●</span>
        <span>Telangana Tactical GIS (100% Offline)</span>
      </div>

      {/* Bottom Center: Tactical GIS HUD & Direct DOM Breadcrumb */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'rgba(15, 23, 42, 0.92)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '6px 14px',
          color: '#cbd5e1',
          fontSize: '0.72rem',
          fontWeight: '600',
          zIndex: 10,
          pointerEvents: 'none',
          boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
        }}
      >
        <span ref={hudDepthRef} style={{ color: '#38bdf8', fontWeight: '800' }}>
          🏛️ Telangana State Overview (33 Districts)
        </span>
        <span style={{ color: '#64748b' }}>|</span>
        <span>
          Zoom: <strong ref={hudZoomRef} style={{ color: '#f8fafc' }}>7.2</strong>
        </span>
        <span style={{ color: '#64748b' }}>|</span>
        <span ref={hudCoordsRef}>
          📍 17.8000°N, 79.0000°E
        </span>
      </div>

      {/* Hovered Feature Tooltip Card */}
      {hoveredFeature && (
        <div
          style={{
            position: 'absolute',
            top: '56px',
            left: '12px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #38bdf8',
            borderRadius: '6px',
            padding: '6px 10px',
            color: '#f8fafc',
            fontSize: '0.75rem',
            fontWeight: '700',
            zIndex: 12,
            pointerEvents: 'none',
            boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
          }}
        >
          {hoveredFeature}
        </div>
      )}

      {/* Bottom Left: Warning Pill & Drawer for Unmapped Incidents */}
      {incidentsWithoutCoords.length > 0 && (
        <div style={{ position: 'absolute', bottom: '12px', left: '12px', zIndex: 15 }}>
          <button
            type="button"
            onClick={() => setShowUnmappedDrawer((prev) => !prev)}
            style={{
              background: 'rgba(245, 158, 11, 0.25)',
              border: '1px solid rgba(245, 158, 11, 0.6)',
              backdropFilter: 'blur(8px)',
              borderRadius: '6px',
              padding: '6px 12px',
              color: '#f59e0b',
              fontSize: '0.74rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>⚠</span>
            <span>
              {incidentsWithoutCoords.length} incident{incidentsWithoutCoords.length > 1 ? 's' : ''} unmapped
            </span>
            <span style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
              ({showUnmappedDrawer ? 'Hide ▲' : 'View ▼'})
            </span>
          </button>

          {showUnmappedDrawer && (
            <div
              style={{
                position: 'absolute',
                bottom: '36px',
                left: '0',
                width: '280px',
                maxHeight: '220px',
                overflowY: 'auto',
                background: 'rgba(15, 23, 42, 0.96)',
                border: '1px solid #475569',
                borderRadius: '8px',
                padding: '10px',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: '800', color: '#cbd5e1', marginBottom: '8px' }}>
                Unmapped Mesh Incidents:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {incidentsWithoutCoords.map((inc) => (
                  <div
                    key={inc.id}
                    onClick={() => {
                      onSelectIncidentRef.current(inc.id);
                      if (onOpenDetailsModalRef.current) {
                        onOpenDetailsModalRef.current(inc);
                      }
                    }}
                    style={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '4px',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      fontSize: '0.72rem',
                    }}
                  >
                    <div style={{ fontWeight: '700', color: '#f8fafc', marginBottom: '2px' }}>
                      {inc.title}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.68rem' }}>
                      <span>{inc.broadcasterName || 'Commander'}</span>
                      <span style={{ color: '#38bdf8' }}>Details ↗</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
