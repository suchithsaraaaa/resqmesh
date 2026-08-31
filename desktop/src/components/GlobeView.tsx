import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { MapIncidentMarker } from './MapView';
import worldCountriesData from '../assets/world-countries.json';

interface GlobeViewProps {
  incidents: MapIncidentMarker[];
  selectedIncidentId?: string | null;
  onSelectIncident: (id: string) => void;
  onOpenDetailsModal?: (incident: MapIncidentMarker) => void;
}

export const GlobeView: React.FC<GlobeViewProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onOpenDetailsModal,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const markersGroupRef = useRef<THREE.Group | null>(null);
  const pulseRingsGroupRef = useRef<THREE.Group | null>(null);
  const cameraTransitionRef = useRef<{
    isTransitioning: boolean;
    startPos: THREE.Vector3;
    targetPos: THREE.Vector3;
    startTime: number;
    duration: number;
  } | null>(null);
  const [autoRotate, setAutoRotate] = useState<boolean>(true);
  const [hoveredIncident, setHoveredIncident] = useState<MapIncidentMarker | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [showUnmappedDrawer, setShowUnmappedDrawer] = useState<boolean>(false);

  const GLOBE_RADIUS = 100;

  // Convert GPS (latitude, longitude) to 3D Cartesian coordinates on sphere
  const latLonToVector3 = useCallback((lat: number, lon: number, radius: number = GLOBE_RADIUS): THREE.Vector3 => {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    return new THREE.Vector3(x, y, z);
  }, []);

  const flyToIncident = useCallback(
    (lat: number, lon: number, durationMs: number = 900) => {
      const camera = cameraRef.current;
      if (!camera) return;
      const targetPos = latLonToVector3(lat, lon, GLOBE_RADIUS + 130);
      cameraTransitionRef.current = {
        isTransitioning: true,
        startPos: camera.position.clone(),
        targetPos,
        startTime: performance.now(),
        duration: durationMs,
      };
      if (controlsRef.current) {
        controlsRef.current.autoRotate = false;
      }
    },
    [latLonToVector3]
  );

  const resetCamera = useCallback(() => {
    const camera = cameraRef.current;
    if (!camera) return;
    cameraTransitionRef.current = {
      isTransitioning: true,
      startPos: camera.position.clone(),
      targetPos: new THREE.Vector3(0, 40, 260),
      startTime: performance.now(),
      duration: 800,
    };
  }, []);

  // Procedurally generate high-tech dark tactical earth canvas texture with real country boundaries (100% offline)
  const createTacticalGlobeTexture = (): THREE.CanvasTexture => {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');
    if (!ctx) return new THREE.CanvasTexture(canvas);

    // Deep tactical oceanic base
    const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, '#020617');
    grad.addColorStop(0.5, '#040d21');
    grad.addColorStop(1, '#020617');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Render authentic country boundaries and landmass polygons
    if (worldCountriesData && (worldCountriesData as any).features) {
      const features: any[] = (worldCountriesData as any).features;

      features.forEach((feature) => {
        const geom = feature.geometry;
        if (!geom) return;

        const name = (feature.properties?.ADMIN || feature.properties?.name || feature.properties?.NAME || '').toLowerCase();
        const isIndia = name === 'india';

        // Tactical styling per country
        ctx.fillStyle = isIndia ? 'rgba(14, 165, 233, 0.28)' : 'rgba(15, 30, 54, 0.65)';
        ctx.strokeStyle = isIndia ? 'rgba(56, 189, 248, 0.95)' : 'rgba(56, 189, 248, 0.38)';
        ctx.lineWidth = isIndia ? 2.2 : 1.0;

        const drawPolygonRings = (rings: number[][][]) => {
          ctx.beginPath();
          rings.forEach((ring) => {
            ring.forEach(([lon, lat], idx) => {
              const x = ((lon + 180) / 360) * canvas.width;
              const y = ((90 - lat) / 180) * canvas.height;
              if (idx === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            });
            ctx.closePath();
          });
          ctx.fill();
          ctx.stroke();
        };

        if (geom.type === 'Polygon') {
          drawPolygonRings(geom.coordinates);
        } else if (geom.type === 'MultiPolygon') {
          geom.coordinates.forEach((polyRings: number[][][]) => {
            drawPolygonRings(polyRings);
          });
        }
      });

      // Subtle Country Sector Labels for Key Geographic Regions
      const sectorLabels: { name: string; lat: number; lon: number; highlight?: boolean }[] = [
        { name: 'INDIA (HQ)', lat: 21.5, lon: 78.5, highlight: true },
        { name: 'NORTH AMERICA', lat: 45.0, lon: -100.0 },
        { name: 'SOUTH AMERICA', lat: -15.0, lon: -60.0 },
        { name: 'EUROPE', lat: 52.0, lon: 15.0 },
        { name: 'AFRICA', lat: 5.0, lon: 20.0 },
        { name: 'EAST ASIA', lat: 35.0, lon: 105.0 },
        { name: 'AUSTRALIA', lat: -25.0, lon: 133.0 },
      ];

      sectorLabels.forEach((lbl) => {
        const x = ((lbl.lon + 180) / 360) * canvas.width;
        const y = ((90 - lbl.lat) / 180) * canvas.height;
        ctx.fillStyle = lbl.highlight ? '#38bdf8' : 'rgba(148, 163, 184, 0.45)';
        ctx.font = lbl.highlight
          ? 'bold 16px "SF Mono", "Segoe UI", Roboto, monospace'
          : '12px "SF Mono", "Segoe UI", Roboto, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(lbl.name, x, y);
      });
    }

    // Latitude and Longitude Graticule Grid
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
    ctx.lineWidth = 1;

    // Latitudes (every 15 degrees)
    for (let lat = -75; lat <= 75; lat += 15) {
      const y = ((90 - lat) / 180) * canvas.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Longitudes (every 15 degrees)
    for (let lon = -180; lon <= 180; lon += 15) {
      const x = ((lon + 180) / 360) * canvas.width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }

    // Equator & Prime Meridian Highlights
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.28)';
    ctx.lineWidth = 2;
    // Equator
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
    // Prime Meridian
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  };

  // Initialize Three.js scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 450;

    // Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x0a0f1d);

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
    camera.position.set(0, 40, 260);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 130;
    controls.maxDistance = 450;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 0.5;
    controlsRef.current = controls;

    // Globe Mesh
    const globeGeometry = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const globeMaterial = new THREE.MeshStandardMaterial({
      map: createTacticalGlobeTexture(),
      roughness: 0.85,
      metalness: 0.15,
    });
    const globeMesh = new THREE.Mesh(globeGeometry, globeMaterial);
    scene.add(globeMesh);

    // Outer Atmosphere Halo Glow
    const haloGeometry = new THREE.SphereGeometry(GLOBE_RADIUS * 1.025, 48, 48);
    const haloMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.12,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
    });
    const haloMesh = new THREE.Mesh(haloGeometry, haloMaterial);
    scene.add(haloMesh);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x94a3b8, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(200, 150, 250);
    scene.add(dirLight);

    const backLight = new THREE.DirectionalLight(0x38bdf8, 0.4);
    backLight.position.set(-200, -100, -200);
    scene.add(backLight);

    // Groups for markers and animated pulse rings
    const markersGroup = new THREE.Group();
    scene.add(markersGroup);
    markersGroupRef.current = markersGroup;

    const pulseRingsGroup = new THREE.Group();
    scene.add(pulseRingsGroup);
    pulseRingsGroupRef.current = pulseRingsGroup;

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      controls.update();

      // Animate pulsing rings on active markers
      pulseRingsGroup.children.forEach((ring) => {
        const mesh = ring as THREE.Mesh;
        const scale = 1 + (Math.sin(elapsed * 3 + (mesh.userData.phase || 0)) + 1) * 0.4;
        mesh.scale.set(scale, scale, 1);
        if (mesh.material instanceof THREE.MeshBasicMaterial) {
          mesh.material.opacity = 0.8 - (scale - 1) * 0.7;
        }
      });

      // Smooth Camera Transition Flight
      const trans = cameraTransitionRef.current;
      if (trans && trans.isTransitioning && camera) {
        const progress = Math.min(1, (performance.now() - trans.startTime) / trans.duration);
        const ease = progress * progress * (3 - 2 * progress); // smoothstep
        camera.position.lerpVectors(trans.startPos, trans.targetPos, ease);
        camera.lookAt(0, 0, 0);
        controls.target.set(0, 0, 0);
        if (progress >= 1) {
          trans.isTransitioning = false;
        }
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Update controls auto-rotation state
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Update Incident 3D Markers on Globe
  useEffect(() => {
    const markersGroup = markersGroupRef.current;
    const pulseRingsGroup = pulseRingsGroupRef.current;
    if (!markersGroup || !pulseRingsGroup) return;

    // Clear existing markers
    while (markersGroup.children.length > 0) {
      markersGroup.remove(markersGroup.children[0]);
    }
    while (pulseRingsGroup.children.length > 0) {
      pulseRingsGroup.remove(pulseRingsGroup.children[0]);
    }

    const severityColors: Record<string, number> = {
      critical: 0xef4444, // Red
      high: 0xf97316,     // Orange
      medium: 0xf59e0b,   // Yellow
      low: 0x10b981,      // Green
    };

    const severityColorHex: Record<string, string> = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#f59e0b',
      low: '#10b981',
    };

    const createTextSprite = (text: string, colorHex: string): THREE.Sprite => {
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.strokeStyle = colorHex;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.roundRect(6, 6, 244, 52, 8);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 20px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const label = text.length > 18 ? text.slice(0, 17) + '…' : text;
        ctx.fillText(label, 128, 32);
      }
      const texture = new THREE.CanvasTexture(canvas);
      const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
      const sprite = new THREE.Sprite(mat);
      sprite.scale.set(22, 5.5, 1);
      return sprite;
    };

    incidents.forEach((inc, idx) => {
      // Skip incidents without valid coordinates (never plot at 0, 0!)
      if (inc.lat === null || inc.lon === null) return;

      const pos = latLonToVector3(inc.lat, inc.lon, GLOBE_RADIUS + 1.2);
      const sevKey = inc.severity.toLowerCase();
      const color = severityColors[sevKey] || 0x64748b;
      const colorHex = severityColorHex[sevKey] || '#64748b';
      const isSelected = inc.id === selectedIncidentId;

      // 3D Pin Sphere Marker
      const pinRadius = isSelected ? 4.5 : inc.severity === 'critical' ? 3.8 : 3.0;
      const pinGeom = new THREE.SphereGeometry(pinRadius, 16, 16);
      const pinMat = new THREE.MeshBasicMaterial({
        color,
      });
      const pinMesh = new THREE.Mesh(pinGeom, pinMat);
      pinMesh.position.copy(pos);
      pinMesh.userData = { incident: inc };
      markersGroup.add(pinMesh);

      // Vertical Marker Pin Stem
      const normal = pos.clone().normalize();
      const stemLength = isSelected ? 12 : 7;
      const stemGeom = new THREE.CylinderGeometry(0.6, 0.6, stemLength, 8);
      const stemMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 });
      const stemMesh = new THREE.Mesh(stemGeom, stemMat);
      stemMesh.position.copy(pos.clone().add(normal.clone().multiplyScalar(stemLength / 2)));
      stemMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
      stemMesh.userData = { incident: inc };
      markersGroup.add(stemMesh);

      // Billboard Text Label Sprite floating above the pin
      const sprite = createTextSprite(inc.title, colorHex);
      const labelPos = pos.clone().add(normal.clone().multiplyScalar(stemLength + 6));
      sprite.position.copy(labelPos);
      sprite.userData = { incident: inc };
      markersGroup.add(sprite);

      // Vertical Beacon Light Beam for Critical/High Emergencies
      if (inc.severity === 'critical' || inc.severity === 'high' || isSelected) {
        const beamHeight = isSelected ? 35 : 22;
        const beamGeom = new THREE.CylinderGeometry(0.2, 1.8, beamHeight, 8);
        const beamMat = new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.35,
        });
        const beamMesh = new THREE.Mesh(beamGeom, beamMat);
        beamMesh.position.copy(pos.clone().add(normal.clone().multiplyScalar(beamHeight / 2)));
        beamMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
        pulseRingsGroup.add(beamMesh);

        // Concentric Expanding Pulse Rings
        const ringGeom = new THREE.RingGeometry(3.5, 5.0, 24);
        const ringMat = new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.7,
          side: THREE.DoubleSide,
        });
        const ringMesh = new THREE.Mesh(ringGeom, ringMat);
        ringMesh.position.copy(pos.clone().add(normal.clone().multiplyScalar(0.2)));
        ringMesh.lookAt(pos.clone().add(normal));
        ringMesh.userData = { phase: idx * 0.8 };
        pulseRingsGroup.add(ringMesh);
      }
    });
  }, [incidents, selectedIncidentId, latLonToVector3]);

  // Synchronize outer incident selection with camera flight
  useEffect(() => {
    if (!selectedIncidentId) return;
    const target = incidents.find((i) => i.id === selectedIncidentId);
    if (target && target.lat !== null && target.lon !== null) {
      flyToIncident(target.lat, target.lon, 900);
    }
  }, [selectedIncidentId, incidents, flyToIncident]);

  // Raycasting for Mouse Interaction (Click & Hover)
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    const camera = cameraRef.current;
    const markersGroup = markersGroupRef.current;
    if (!container || !camera || !markersGroup) return;

    const rect = container.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(markersGroup.children);

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      const inc: MapIncidentMarker = hit.userData.incident;
      if (inc) {
        if (inc.lat !== null && inc.lon !== null) {
          flyToIncident(inc.lat, inc.lon, 800);
        }
        onSelectIncident(inc.id);
        if (onOpenDetailsModal) {
          onOpenDetailsModal(inc);
        }
      }
    }
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    const camera = cameraRef.current;
    const markersGroup = markersGroupRef.current;
    if (!container || !camera || !markersGroup) return;

    const rect = container.getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });

    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(markersGroup.children);

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      const inc: MapIncidentMarker = hit.userData.incident;
      if (inc) {
        setHoveredIncident(inc);
        container.style.cursor = 'pointer';
        return;
      }
    }

    setHoveredIncident(null);
    container.style.cursor = 'grab';
  };

  const incidentsWithoutCoords = incidents.filter((i) => i.lat === null || i.lon === null);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '440px', overflow: 'hidden', borderRadius: '8px' }}>
      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        style={{ width: '100%', height: '100%', minHeight: '440px' }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      />

      {/* Tactical HUD Header Controls */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(15, 23, 42, 0.82)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '6px 12px',
          color: '#f8fafc',
          fontSize: '0.8rem',
          zIndex: 10,
        }}
      >
        <span style={{ fontWeight: '700', color: '#38bdf8' }}>🌍 3D Tactical Mesh Globe</span>
        <span style={{ color: '#64748b' }}>|</span>
        <span style={{ color: '#94a3b8' }}>
          Active: <strong>{incidents.length - incidentsWithoutCoords.length}</strong>
        </span>
        <button
          type="button"
          onClick={() => setAutoRotate((prev) => !prev)}
          style={{
            background: autoRotate ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            border: '1px solid #334155',
            color: autoRotate ? '#38bdf8' : '#94a3b8',
            borderRadius: '4px',
            padding: '2px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '600',
          }}
        >
          {autoRotate ? '↺ Auto-Rotate: ON' : '⏸ Auto-Rotate: OFF'}
        </button>
        <button
          type="button"
          onClick={resetCamera}
          title="Reset camera view to center"
          style={{
            background: 'transparent',
            border: '1px solid #334155',
            color: '#94a3b8',
            borderRadius: '4px',
            padding: '2px 8px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            fontWeight: '600',
          }}
        >
          🎯 Reset View
        </button>
      </div>

      {/* Offline Hardware Notice Pill */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(15, 23, 42, 0.82)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '6px 10px',
          color: '#10b981',
          fontSize: '0.72rem',
          fontWeight: '600',
          zIndex: 10,
        }}
      >
        <span>●</span> Offline Mesh Mode (100% On-Device)
      </div>

      {/* Warning indicator for incidents with missing coordinates */}
      {incidentsWithoutCoords.length > 0 && (
        <div style={{ position: 'absolute', bottom: '12px', left: '14px', zIndex: 15 }}>
          <button
            type="button"
            onClick={() => setShowUnmappedDrawer((prev) => !prev)}
            style={{
              background: 'rgba(245, 158, 11, 0.2)',
              border: '1px solid rgba(245, 158, 11, 0.5)',
              backdropFilter: 'blur(8px)',
              borderRadius: '6px',
              padding: '6px 12px',
              color: '#f59e0b',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>⚠</span>
            <span>{incidentsWithoutCoords.length} incident{incidentsWithoutCoords.length > 1 ? 's' : ''} location unavailable</span>
            <span style={{ fontSize: '0.7rem', color: '#cbd5e1' }}>({showUnmappedDrawer ? 'Hide ▲' : 'View ▼'})</span>
          </button>

          {showUnmappedDrawer && (
            <div
              style={{
                position: 'absolute',
                bottom: '36px',
                left: '0',
                width: '280px',
                maxHeight: '200px',
                overflowY: 'auto',
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid #475569',
                borderRadius: '8px',
                padding: '10px',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#cbd5e1', marginBottom: '8px' }}>
                Unmapped Mesh Incidents:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {incidentsWithoutCoords.map((inc) => (
                  <div
                    key={inc.id}
                    onClick={() => {
                      onSelectIncident(inc.id);
                      if (onOpenDetailsModal) {
                        onOpenDetailsModal(inc);
                      }
                    }}
                    style={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '4px',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                    }}
                  >
                    <div style={{ fontWeight: '700', color: '#f8fafc', marginBottom: '2px' }}>{inc.title}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.7rem' }}>
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

      {/* Interactive Marker Tooltip Hover Card */}
      {hoveredIncident && (
        <div
          style={{
            position: 'absolute',
            left: `${mousePos.x + 15}px`,
            top: `${mousePos.y - 45}px`,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #38bdf8',
            borderRadius: '6px',
            padding: '8px 12px',
            color: '#f8fafc',
            pointerEvents: 'none',
            fontSize: '0.78rem',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.6)',
            zIndex: 20,
            minWidth: '160px',
          }}
        >
          <div style={{ fontWeight: '800', marginBottom: '2px', color: '#f8fafc' }}>
            {hoveredIncident.title}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', color: '#94a3b8', fontSize: '0.72rem' }}>
            <span style={{ textTransform: 'uppercase', fontWeight: '700', color: hoveredIncident.severity === 'critical' ? '#ef4444' : hoveredIncident.severity === 'high' ? '#f97316' : '#10b981' }}>
              {hoveredIncident.severity}
            </span>
            <span>📍 {hoveredIncident.lat?.toFixed(2)}, {hoveredIncident.lon?.toFixed(2)}</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: '#38bdf8', marginTop: '4px' }}>
            Click to inspect incident details ↗
          </div>
        </div>
      )}
    </div>
  );
};
