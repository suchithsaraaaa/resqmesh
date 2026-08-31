import React, { useEffect, useRef, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { MapIncidentMarker } from './MapView';
import worldCountriesData from '../assets/world-countries.json';
import { colors, radii, shadows, fonts } from '../styles/designTokens';

export interface GlobeHeroViewRef {
  flyToIncident: (lat: number, lon: number, durationMs?: number) => void;
  resetView: () => void;
}

interface GlobeHeroViewProps {
  incidents: MapIncidentMarker[];
  selectedIncidentId?: string | null;
  onSelectIncident: (id: string) => void;
  onOpenDetailsModal?: (incident: MapIncidentMarker) => void;
  height?: string | number;
}

let cachedGlobeTexture: THREE.CanvasTexture | null = null;

// Procedurally generate tactical earth canvas texture with real country polygons (Cached at module level)
function getTacticalGlobeTexture(): THREE.CanvasTexture {
  if (cachedGlobeTexture) return cachedGlobeTexture;

  const canvas = document.createElement('canvas');
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    cachedGlobeTexture = new THREE.CanvasTexture(canvas);
    return cachedGlobeTexture;
  }

  // Deep oceanic space-navy base
  const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
  grad.addColorStop(0, '#040914');
  grad.addColorStop(0.5, '#071224');
  grad.addColorStop(1, '#040914');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Render authentic country boundaries and landmass polygons
  if (worldCountriesData && (worldCountriesData as any).features) {
    const features: any[] = (worldCountriesData as any).features;

    features.forEach((feature) => {
      const geom = feature.geometry;
      if (!geom) return;

      const name = (
        feature.properties?.ADMIN ||
        feature.properties?.name ||
        feature.properties?.NAME ||
        ''
      ).toLowerCase();
      const isIndia = name === 'india';

      // High-contrast tactical styling
      ctx.fillStyle = isIndia ? 'rgba(56, 189, 248, 0.32)' : 'rgba(17, 34, 60, 0.72)';
      ctx.strokeStyle = isIndia ? 'rgba(56, 189, 248, 0.95)' : 'rgba(56, 189, 248, 0.38)';
      ctx.lineWidth = isIndia ? 2.2 : 0.8;

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

    // Subtle tactical region labels
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
        ? 'bold 15px "SF Mono", "Segoe UI", Roboto, monospace'
        : '11px "SF Mono", "Segoe UI", Roboto, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(lbl.name, x, y);
    });
  }

  // Latitude & Longitude Graticule Grid
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
  ctx.lineWidth = 1;

  for (let lat = -75; lat <= 75; lat += 15) {
    const y = ((90 - lat) / 180) * canvas.height;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }

  for (let lon = -180; lon <= 180; lon += 15) {
    const x = ((lon + 180) / 360) * canvas.width;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }

  // Equator & Prime Meridian Highlights
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(canvas.width / 2, 0);
  ctx.lineTo(canvas.width / 2, canvas.height);
  ctx.stroke();

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  cachedGlobeTexture = texture;
  return cachedGlobeTexture;
}

export const GlobeHeroView = React.memo(forwardRef<GlobeHeroViewRef, GlobeHeroViewProps>(({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onOpenDetailsModal,
  height = '100%',
}, ref) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const markersGroupRef = useRef<THREE.Group | null>(null);
  const pulseRingsGroupRef = useRef<THREE.Group | null>(null);
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseVectorRef = useRef<THREE.Vector2>(new THREE.Vector2());

  // Active hover and detail popup states
  const [hoveredIncident, setHoveredIncident] = useState<MapIncidentMarker | null>(null);
  const [activePopupIncident, setActivePopupIncident] = useState<MapIncidentMarker | null>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [autoRotate, setAutoRotate] = useState<boolean>(false);

  // Camera flight interpolation ref
  const cameraTransitionRef = useRef<{
    isTransitioning: boolean;
    startPos: THREE.Vector3;
    targetPos: THREE.Vector3;
    startTime: number;
    duration: number;
  } | null>(null);

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

  // Smooth camera flight transition to a given coordinate
  const flyToIncident = useCallback(
    (lat: number, lon: number, durationMs: number = 1000) => {
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
      targetPos: new THREE.Vector3(0, 45, 260),
      startTime: performance.now(),
      duration: 900,
    };
    setActivePopupIncident(null);
  }, []);

  // Expose imperative methods to parent
  useImperativeHandle(ref, () => ({
    flyToIncident,
    resetView: resetCamera,
  }));

  // ONE-TIME WebGL Initialization (Permanent Lifecycle, Never Resets On Re-renders)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x070b14);

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
    camera.position.set(0, 45, 260);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.65;
    controls.zoomSpeed = 0.85;
    controls.minDistance = 115;
    controls.maxDistance = 450;
    controls.autoRotate = false;
    controls.autoRotateSpeed = 0.4;
    controlsRef.current = controls;

    // Sacred camera state: cancel programmatic flight when user grabs/drags the globe
    controls.addEventListener('start', () => {
      if (cameraTransitionRef.current) {
        cameraTransitionRef.current.isTransitioning = false;
      }
    });

    // 1. Earth Sphere Core
    const globeGeometry = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const globeTexture = getTacticalGlobeTexture();
    const globeMaterial = new THREE.MeshStandardMaterial({
      map: globeTexture,
      roughness: 0.82,
      metalness: 0.12,
      bumpScale: 0.05,
    });
    const globeMesh = new THREE.Mesh(globeGeometry, globeMaterial);
    scene.add(globeMesh);

    // 2. Tactical Fresnel Atmosphere Glow Shell
    const atmosphereGeometry = new THREE.SphereGeometry(GLOBE_RADIUS * 1.025, 64, 64);
    const atmosphereMaterial = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.68 - dot(vNormal, vec3(0, 0, 1.0)), 2.2);
          gl_FragColor = vec4(0.22, 0.74, 0.97, 1.0) * intensity * 0.75;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
    });
    const atmosphereMesh = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphereMesh);

    // 3. Subtle Outer Space Orbital Dust / Stars
    const starsGeometry = new THREE.BufferGeometry();
    const starCount = 350;
    const starCoords = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      const r = 500 + Math.random() * 400;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      starCoords[i] = r * Math.sin(phi) * Math.cos(theta);
      starCoords[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      starCoords[i + 2] = r * Math.cos(phi);
    }
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(starCoords, 3));
    const starsMaterial = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 1.5,
      transparent: true,
      opacity: 0.35,
    });
    const starsMesh = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(starsMesh);

    // 4. Incident Markers & Pulsing Wave Groups
    const markersGroup = new THREE.Group();
    scene.add(markersGroup);
    markersGroupRef.current = markersGroup;

    const pulseRingsGroup = new THREE.Group();
    scene.add(pulseRingsGroup);
    pulseRingsGroupRef.current = pulseRingsGroup;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.15);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0x38bdf8, 1.4);
    directionalLight1.position.set(300, 200, 300);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0x6366f1, 0.85);
    directionalLight2.position.set(-300, -100, -200);
    scene.add(directionalLight2);

    // Animation loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth camera transition if active
      if (cameraTransitionRef.current && cameraTransitionRef.current.isTransitioning) {
        const trans = cameraTransitionRef.current;
        const elapsedMs = performance.now() - trans.startTime;
        const progress = Math.min(elapsedMs / trans.duration, 1.0);
        // Smoothstep interpolation (3t² - 2t³)
        const t = progress * progress * (3 - 2 * progress);
        camera.position.lerpVectors(trans.startPos, trans.targetPos, t);
        camera.lookAt(0, 0, 0);

        if (progress >= 1.0) {
          trans.isTransitioning = false;
        }
      } else {
        controls.update();
      }

      // Dynamic camera distance-aware marker scaling
      // Min distance: 115 (closest zoom), Max distance: 450 (furthest orbital zoom)
      const camDist = camera.position.length();
      const tDist = THREE.MathUtils.clamp((camDist - 115) / (450 - 115), 0, 1);
      // Smooth interpolation: 0.28 (close zoom, elegant pinpoint) -> 1.0 (orbital view)
      const markerScale = 0.28 + tDist * 0.72;

      markersGroup.children.forEach((child) => {
        const u = (child as any).userData;
        if (u && u.surfacePos && u.normal) {
          if (u.type === 'pin') {
            const offset = 5.5 * markerScale;
            child.position.copy(u.surfacePos).addScaledVector(u.normal, offset);
            child.scale.setScalar(markerScale);
          } else if (u.type === 'beam') {
            const offset = (u.baseHeight * markerScale) / 2;
            child.position.copy(u.surfacePos).addScaledVector(u.normal, offset);
            child.scale.set(markerScale, markerScale, markerScale);
          }
        }
      });

      // Animate pulsing wave rings around incidents (smoothly scaled with zoom)
      pulseRingsGroup.children.forEach((child, idx) => {
        const phase = (elapsedTime * 1.5 + idx * 0.4) % 1.0;
        const scale = (1.0 + phase * 2.2) * markerScale;
        child.scale.set(scale, scale, scale);
        const mat = (child as THREE.Mesh).material as THREE.MeshBasicMaterial;
        if (mat) {
          mat.opacity = Math.max(0, (1.0 - phase) * 0.65);
        }
      });

      renderer.render(scene, camera);
    };
    animate();

    // Resize observer
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
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      controls.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []); // Empty dependency array ensures permanent WebGL lifecycle that never recreates or resets camera

  // Synchronize autoRotate setting with OrbitControls
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Update 3D Incident Markers dynamically (Zero WebGL recreation!)
  useEffect(() => {
    const markersGroup = markersGroupRef.current;
    const pulseRingsGroup = pulseRingsGroupRef.current;
    if (!markersGroup || !pulseRingsGroup) return;

    // Clear existing marker meshes cleanly
    while (markersGroup.children.length > 0) {
      const obj = markersGroup.children[0];
      markersGroup.remove(obj);
    }
    while (pulseRingsGroup.children.length > 0) {
      const obj = pulseRingsGroup.children[0];
      pulseRingsGroup.remove(obj);
    }

    const mapped = incidents.filter(
      (inc) => inc.lat !== null && inc.lon !== null && !isNaN(inc.lat) && !isNaN(inc.lon)
    );

    const getHexColor = (sev: string): number => {
      switch (sev.toLowerCase()) {
        case 'critical':
          return 0xef4444;
        case 'high':
          return 0xf97316;
        case 'medium':
          return 0xeab308;
        default:
          return 0x10b981;
      }
    };

    mapped.forEach((inc) => {
      const lat = inc.lat!;
      const lon = inc.lon!;
      const hexColor = getHexColor(inc.severity);
      const isSelected = selectedIncidentId === inc.id;

      const surfacePos = latLonToVector3(lat, lon, GLOBE_RADIUS);
      const normal = surfacePos.clone().normalize();

      // 1. Interactive Pin Head Sphere
      const pinRadius = isSelected ? 3.4 : 2.5;
      const sphereGeo = new THREE.SphereGeometry(pinRadius, 16, 16);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: hexColor,
        emissive: hexColor,
        emissiveIntensity: isSelected ? 1.5 : 0.8,
        roughness: 0.2,
      });
      const pinSphere = new THREE.Mesh(sphereGeo, sphereMat);
      pinSphere.position.copy(surfacePos.clone().add(normal.clone().multiplyScalar(5.5)));
      (pinSphere as any).userData = {
        incident: inc,
        type: 'pin',
        surfacePos,
        normal,
        baseRadius: pinRadius,
      };
      markersGroup.add(pinSphere);

      // 2. Vertical Radial Beacon Beam
      const beamHeight = isSelected ? 18 : 12;
      const beamGeo = new THREE.CylinderGeometry(0.3, 0.7, beamHeight, 8);
      const beamMat = new THREE.MeshBasicMaterial({
        color: hexColor,
        transparent: true,
        opacity: isSelected ? 0.9 : 0.65,
      });
      const beamMesh = new THREE.Mesh(beamGeo, beamMat);
      beamMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
      beamMesh.position.copy(surfacePos.clone().add(normal.clone().multiplyScalar(beamHeight / 2)));
      (beamMesh as any).userData = {
        incident: inc,
        type: 'beam',
        surfacePos,
        normal,
        baseHeight: beamHeight,
      };
      markersGroup.add(beamMesh);

      // 3. Surface Ripple Wave Ring
      const ringGeo = new THREE.RingGeometry(1.2, 2.8, 24);
      const ringMat = new THREE.MeshBasicMaterial({
        color: hexColor,
        transparent: true,
        opacity: 0.6,
        side: THREE.DoubleSide,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      ringMesh.position.copy(surfacePos.clone().add(normal.clone().multiplyScalar(0.2)));
      (ringMesh as any).userData = {
        type: 'ring',
        surfacePos,
        normal,
      };
      pulseRingsGroup.add(ringMesh);
    });
  }, [incidents, selectedIncidentId, latLonToVector3]);

  // Click & Hover raycasting handler
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    const camera = cameraRef.current;
    const markersGroup = markersGroupRef.current;
    if (!container || !camera || !markersGroup) return;

    const rect = container.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    mouseVectorRef.current.set(x, y);
    raycasterRef.current.setFromCamera(mouseVectorRef.current, camera);

    const intersects = raycasterRef.current.intersectObjects(markersGroup.children, false);
    if (intersects.length > 0) {
      const hit = intersects.find((item) => (item.object as any).userData?.incident);
      if (hit) {
        const inc: MapIncidentMarker = (hit.object as any).userData.incident;
        onSelectIncident(inc.id);
        setActivePopupIncident(inc);
        setPopupPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        flyToIncident(inc.lat!, inc.lon!, 900);
      }
    } else {
      // Clicked on empty space
      setActivePopupIncident(null);
    }
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    const camera = cameraRef.current;
    const markersGroup = markersGroupRef.current;
    if (!container || !camera || !markersGroup) return;

    const rect = container.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    mouseVectorRef.current.set(x, y);
    raycasterRef.current.setFromCamera(mouseVectorRef.current, camera);

    const intersects = raycasterRef.current.intersectObjects(markersGroup.children, false);
    if (intersects.length > 0) {
      const hit = intersects.find((item) => (item.object as any).userData?.incident);
      if (hit) {
        container.style.cursor = 'pointer';
        const inc = (hit.object as any).userData.incident;
        setHoveredIncident((prev) => (prev?.id === inc.id ? prev : inc));
        return;
      }
    }
    container.style.cursor = 'grab';
    setHoveredIncident((prev) => (prev === null ? null : null));
  };

  const handleZoom = (delta: number) => {
    const controls = controlsRef.current;
    const camera = cameraRef.current;
    if (!controls || !camera) return;

    const factor = delta > 0 ? 0.85 : 1.18;
    camera.position.multiplyScalar(factor);
    controls.update();
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height,
        minHeight: '460px',
        borderRadius: radii.xl,
        overflow: 'hidden',
        background: 'radial-gradient(ellipse at center, #0a1324 0%, #070b14 100%)',
        border: `1px solid ${colors.borderSubtle}`,
        boxShadow: shadows.elevated,
      }}
      onMouseLeave={() => {
        setHoveredIncident(null);
      }}
    >
      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        style={{
          width: '100%',
          height: '100%',
          touchAction: 'none',
        }}
      />

      {/* Floating Tactical Overlay HUD (Top Left) */}
      <div
        style={{
          position: 'absolute',
          top: '18px',
          left: '20px',
          pointerEvents: 'none',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: colors.accentElectric,
              boxShadow: shadows.glowCyan,
              display: 'inline-block',
            }}
          />
          <span
            style={{
              color: colors.textPrimary,
              fontFamily: fonts.sans,
              fontSize: '0.85rem',
              fontWeight: '700',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
            }}
          >
            3D Planetary Situation
          </span>
        </div>
        <span
          style={{
            color: colors.textMuted,
            fontFamily: fonts.sans,
            fontSize: '0.74rem',
          }}
        >
          {incidents.filter((i) => i.lat !== null).length} active emergency coordinates mapped
        </span>
      </div>

      {/* Minimal Floating Controls (Top Right) */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          zIndex: 10,
        }}
      >
        <button
          type="button"
          onClick={() => handleZoom(1)}
          title="Zoom In"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: radii.sm,
            background: colors.bgGlassElevated,
            border: `1px solid ${colors.borderMedium}`,
            color: colors.textPrimary,
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.15s ease',
          }}
        >
          +
        </button>

        <button
          type="button"
          onClick={() => handleZoom(-1)}
          title="Zoom Out"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: radii.sm,
            background: colors.bgGlassElevated,
            border: `1px solid ${colors.borderMedium}`,
            color: colors.textPrimary,
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.15s ease',
          }}
        >
          −
        </button>

        <button
          type="button"
          onClick={resetCamera}
          title="Reset Earth Orbit View"
          style={{
            padding: '0 10px',
            height: '32px',
            borderRadius: radii.sm,
            background: colors.bgGlassElevated,
            border: `1px solid ${colors.borderMedium}`,
            color: colors.textSecondary,
            fontSize: '0.74rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🎯</span> Reset
        </button>

        <button
          type="button"
          onClick={() => setAutoRotate(!autoRotate)}
          title={autoRotate ? 'Pause Rotation' : 'Enable Orbit Rotation'}
          style={{
            padding: '0 10px',
            height: '32px',
            borderRadius: radii.sm,
            background: autoRotate ? 'rgba(56, 189, 248, 0.18)' : colors.bgGlassElevated,
            border: `1px solid ${autoRotate ? colors.accentElectric : colors.borderMedium}`,
            color: autoRotate ? colors.accentElectric : colors.textSecondary,
            fontSize: '0.74rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🔄</span> {autoRotate ? 'Rotating' : 'Static'}
        </button>
      </div>

      {/* Hover Tooltip (Transient) */}
      {hoveredIncident && !activePopupIncident && (
        <div
          style={{
            position: 'absolute',
            bottom: '20px',
            left: '20px',
            background: colors.bgGlassElevated,
            backdropFilter: 'blur(16px)',
            border: `1px solid ${colors.borderMedium}`,
            borderRadius: radii.md,
            padding: '8px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: shadows.card,
            pointerEvents: 'none',
            zIndex: 15,
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background:
                hoveredIncident.severity.toLowerCase() === 'critical'
                  ? colors.critical
                  : hoveredIncident.severity.toLowerCase() === 'high'
                  ? colors.high
                  : hoveredIncident.severity.toLowerCase() === 'medium'
                  ? colors.medium
                  : colors.low,
            }}
          />
          <div>
            <div style={{ color: colors.textPrimary, fontSize: '0.82rem', fontWeight: '700' }}>
              {hoveredIncident.title}
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.72rem' }}>
              {hoveredIncident.lat?.toFixed(4)}, {hoveredIncident.lon?.toFixed(4)}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Incident Detail Card Popup */}
      {activePopupIncident && (
        <div
          style={{
            position: 'absolute',
            bottom: '24px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: colors.bgGlassElevated,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.borderMedium}`,
            borderRadius: radii.lg,
            padding: '16px 20px',
            minWidth: '320px',
            maxWidth: '420px',
            boxShadow: shadows.elevated,
            zIndex: 25,
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: radii.full,
                  fontSize: '0.68rem',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  background:
                    activePopupIncident.severity.toLowerCase() === 'critical'
                      ? colors.criticalBg
                      : activePopupIncident.severity.toLowerCase() === 'high'
                      ? colors.highBg
                      : activePopupIncident.severity.toLowerCase() === 'medium'
                      ? colors.mediumBg
                      : colors.lowBg,
                  color:
                    activePopupIncident.severity.toLowerCase() === 'critical'
                      ? colors.critical
                      : activePopupIncident.severity.toLowerCase() === 'high'
                      ? colors.high
                      : activePopupIncident.severity.toLowerCase() === 'medium'
                      ? colors.medium
                      : colors.low,
                  border: `1px solid ${
                    activePopupIncident.severity.toLowerCase() === 'critical'
                      ? colors.criticalBorder
                      : activePopupIncident.severity.toLowerCase() === 'high'
                      ? colors.highBorder
                      : activePopupIncident.severity.toLowerCase() === 'medium'
                      ? colors.mediumBorder
                      : colors.lowBorder
                  }`,
                }}
              >
                ● {activePopupIncident.severity}
              </span>
              <span style={{ color: colors.textMuted, fontSize: '0.74rem' }}>
                {activePopupIncident.category || 'Incident'}
              </span>
            </div>

            <button
              type="button"
              onClick={() => setActivePopupIncident(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: colors.textMuted,
                fontSize: '1.1rem',
                cursor: 'pointer',
                padding: '0 4px',
              }}
            >
              ×
            </button>
          </div>

          <div>
            <h4
              style={{
                margin: 0,
                color: colors.textPrimary,
                fontSize: '1rem',
                fontWeight: '700',
              }}
            >
              {activePopupIncident.title}
            </h4>
            <div style={{ color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
              📍 {activePopupIncident.lat?.toFixed(5)}°N, {activePopupIncident.lon?.toFixed(5)}°E
            </div>
          </div>

          {activePopupIncident.summary && (
            <p
              style={{
                margin: 0,
                color: colors.textSecondary,
                fontSize: '0.78rem',
                lineHeight: 1.4,
              }}
            >
              {activePopupIncident.summary.slice(0, 130)}
              {activePopupIncident.summary.length > 130 ? '...' : ''}
            </p>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '4px' }}>
            {onOpenDetailsModal && (
              <button
                type="button"
                onClick={() => onOpenDetailsModal(activePopupIncident)}
                style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: `1px solid ${colors.accentElectric}`,
                  color: colors.accentElectric,
                  padding: '6px 14px',
                  borderRadius: radii.sm,
                  fontSize: '0.76rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                View Incident Brief
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}));

GlobeHeroView.displayName = 'GlobeHeroView';
