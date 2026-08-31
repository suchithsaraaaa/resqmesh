import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LocationService, LocationResult } from '../services/LocationService';
import { OfflineGeocoder } from '../services/OfflineGeocoder';
import { colors, radii, shadows, fonts } from '../styles/designTokens';
import { TacticalEventBus } from '../services/TacticalEventBus';
import { LocationPickerModal } from './LocationPickerModal';

export interface ManualLocationData {
  address: string;
  landmark: string;
  city: string;
  district: string;
  state: string;
  pincode: string;
  additionalDetails?: string;
}

interface CreateIncidentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    title: string;
    category: string;
    severity: string;
    description: string;
    latitude: number | null;
    longitude: number | null;
    accuracy?: number | null;
    location_source?: string;
    captured_at?: string;
    manualLocation?: ManualLocationData;
    files?: File[];
  }) => Promise<void>;
  onStartPickOnMap?: () => void;
  externalPickedCoords?: { lat: number; lon: number } | null;
  onClearPickedCoords?: () => void;
}

export const CreateIncidentModal: React.FC<CreateIncidentModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  onStartPickOnMap,
  externalPickedCoords,
  onClearPickedCoords,
}) => {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('hazmat');
  const [severity, setSeverity] = useState('critical');
  const [description, setDescription] = useState('');

  // Location states
  const [locationResult, setLocationResult] = useState<LocationResult | null>(null);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [activeLat, setActiveLat] = useState<number | null>(null);
  const [activeLon, setActiveLon] = useState<number | null>(null);
  const [activeAccuracy, setActiveAccuracy] = useState<number | null>(null);
  const [resolvedAddress, setResolvedAddress] = useState<string>('');
  const [isMapPickerOpen, setIsMapPickerOpen] = useState<boolean>(false);

  // Manual Location State
  const [showManualSection, setShowManualSection] = useState<boolean>(false);
  const [manualAddress, setManualAddress] = useState<string>('');
  const [manualLandmark, setManualLandmark] = useState<string>('');
  const [manualCity, setManualCity] = useState<string>('Hyderabad');
  const [manualDistrict, setManualDistrict] = useState<string>('Rangareddy');
  const [manualState, setManualState] = useState<string>('Telangana');
  const [manualPincode, setManualPincode] = useState<string>('500001');
  const [manualDetails, setManualDetails] = useState<string>('');

  // Photos State
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [filePreviews, setFilePreviews] = useState<
    { id: string; file: File; previewUrl: string; name: string; size: string }[]
  >([]);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Hidden input refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(LocationService.isOnline());

  // Listen to network status changes (online/offline)
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      detectLocation();
    };
    const handleOffline = () => {
      setIsOnline(false);
      detectLocation();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const resetForm = () => {
    setTitle('');
    setDescription('');
    filePreviews.forEach((p) => URL.revokeObjectURL(p.previewUrl));
    setSelectedFiles([]);
    setFilePreviews([]);
    setError(null);
    setCameraError(null);
    setCategory('hazmat');
    setSeverity('critical');
    setActiveLat(null);
    setActiveLon(null);
    setActiveAccuracy(null);
    setLocationResult(null);
    setIsLocating(false);
    setResolvedAddress('');
    setShowManualSection(false);
    setManualAddress('');
    setManualLandmark('');
    setManualCity('Hyderabad');
    setManualDistrict('Rangareddy');
    setManualState('Telangana');
    setManualPincode('500001');
    setManualDetails('');
    if (onClearPickedCoords) onClearPickedCoords();
  };

  // Attempt real device location detection (priority: GNSS -> Windows Location -> Browser Geolocation)
  const detectLocation = useCallback(async () => {
    setIsLocating(true);
    try {
      const res = await LocationService.getCurrentLocation();
      setLocationResult(res);
      if (res.latitude !== null && res.longitude !== null) {
        setActiveLat(res.latitude);
        setActiveLon(res.longitude);
        setActiveAccuracy(res.accuracy);
        setResolvedAddress(res.resolvedAddress || '');
        if (!res.isWithin20m) {
          setShowManualSection(true);
        }
      } else {
        setShowManualSection(true);
      }
    } catch (err: any) {
      console.warn('[ResQMesh Location] Error acquiring position:', err);
      setLocationResult({
        latitude: null,
        longitude: null,
        accuracy: null,
        source: 'Unavailable',
        timestamp: new Date().toLocaleTimeString(),
        rawTimestamp: Date.now(),
        isFresh: false,
        isWithin20m: false,
        accuracyLabel: 'UNAVAILABLE',
        error: err.message || 'Location unavailable',
      });
      setShowManualSection(true);
    } finally {
      setIsLocating(false);
    }
  }, []);

  // When modal opens, acquire location automatically
  useEffect(() => {
    if (isOpen) {
      detectLocation();
    }
  }, [isOpen, detectLocation]);

  // Handle external picked coordinates from main map
  useEffect(() => {
    if (externalPickedCoords) {
      setActiveLat(externalPickedCoords.lat);
      setActiveLon(externalPickedCoords.lon);
      setActiveAccuracy(5); // Map pin precision
      const rev = OfflineGeocoder.reverseGeocode(externalPickedCoords.lat, externalPickedCoords.lon)?.formatted || '';
      setResolvedAddress(rev);
      setLocationResult({
        latitude: externalPickedCoords.lat,
        longitude: externalPickedCoords.lon,
        accuracy: 5,
        source: 'Manual / Map Pick',
        timestamp: new Date().toLocaleTimeString(),
        rawTimestamp: Date.now(),
        isFresh: true,
        isWithin20m: true,
        accuracyLabel: 'VERIFIED',
        resolvedAddress: rev,
      });
    }
  }, [externalPickedCoords]);

  // File Attachment Handlers
  const handleAddFiles = (files: File[]) => {
    const validFiles = files.filter((f) => {
      const isImg = f.type.startsWith('image/') || /\.(jpg|jpeg|png|webp)$/i.test(f.name);
      const isUnder10MB = f.size <= 10 * 1024 * 1024;
      return isImg && isUnder10MB;
    });

    if (validFiles.length < files.length) {
      setError('Some files were skipped. Only JPG, PNG, and WEBP under 10MB are supported.');
    }

    const newPreviews = validFiles.map((file) => ({
      id: `${file.name}-${file.lastModified}-${Math.random()}`,
      file,
      previewUrl: URL.createObjectURL(file),
      name: file.name,
      size: `${(file.size / 1024).toFixed(0)} KB`,
    }));

    setSelectedFiles((prev) => [...prev, ...validFiles]);
    setFilePreviews((prev) => [...prev, ...newPreviews]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    handleAddFiles(Array.from(e.target.files));
    e.target.value = '';
  };

  const handleCameraCapture = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    handleAddFiles(Array.from(e.target.files));
    e.target.value = '';
  };

  const handleTriggerCamera = async () => {
    setCameraError(null);
    try {
      // Check if mediaDevices is supported
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Test camera access
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true });
          // Stop stream immediately after permission verification
          stream.getTracks().forEach((track) => track.stop());
          cameraInputRef.current?.click();
        } catch (permErr: any) {
          console.warn('[ResQMesh] Camera access check failed:', permErr);
          setCameraError('Camera access unavailable. Use [ Attach Photos ] instead.');
          cameraInputRef.current?.click();
        }
      } else {
        cameraInputRef.current?.click();
      }
    } catch {
      setCameraError('Camera access unavailable. Use [ Attach Photos ] instead.');
      cameraInputRef.current?.click();
    }
  };

  const handleRemoveFile = (previewId: string) => {
    setFilePreviews((prev) => {
      const target = prev.find((p) => p.id === previewId);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }
      const remaining = prev.filter((p) => p.id !== previewId);
      setSelectedFiles(remaining.map((r) => r.file));
      return remaining;
    });
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Please provide an incident title.');
      return;
    }

    // Pincode validation: 6 digits for India if provided
    if (manualPincode.trim() && !/^\d{6}$/.test(manualPincode.trim())) {
      setError('Pincode must be a 6-digit postal code (e.g. 500001).');
      return;
    }

    const hasCoords = activeLat !== null && activeLon !== null && !isNaN(activeLat) && !isNaN(activeLon);
    const hasManual =
      manualAddress.trim().length > 0 ||
      manualLandmark.trim().length > 0 ||
      manualCity.trim().length > 0 ||
      manualDistrict.trim().length > 0;
    const isMapSelected = locationResult?.source === 'MANUAL_MAP';
    const isAccurate = locationResult?.isWithin20m === true;

    // VALIDATION RULES:
    // CASE A: Automatic accuracy <= 20m -> allow broadcast
    // CASE B: Automatic accuracy > 20m + manual location entered -> allow broadcast
    // CASE C: Automatic location unavailable + manual location entered -> allow broadcast
    // CASE D: Manual map selection confirmed -> allow broadcast
    // CASE E: Automatic accuracy > 20m / unavailable and no manual location -> warn user
    if (!isAccurate && !isMapSelected && !hasManual) {
      setError(
        hasCoords
          ? `Location accuracy is low (±${activeAccuracy || 'unknown'}m). Please enter manual location details (street/landmark) or pick a pin on the map.`
          : 'Automatic location is unavailable. Please pick a location on the map or enter manual location details (street/landmark).'
      );
      return;
    }

    setSubmitting(true);

    const sourceTag = isMapSelected ? 'MANUAL_MAP' : hasCoords ? locationResult?.source || 'GNSS' : 'MANUAL';

    const manualPayload: ManualLocationData | undefined = hasManual
      ? {
          address: manualAddress.trim(),
          landmark: manualLandmark.trim(),
          city: manualCity.trim(),
          district: manualDistrict.trim(),
          state: manualState.trim(),
          pincode: manualPincode.trim(),
          additionalDetails: manualDetails.trim(),
        }
      : undefined;

    // Build human-friendly location string
    const manualLocationText = manualPayload
      ? [
          manualPayload.address,
          manualPayload.landmark ? `Near ${manualPayload.landmark}` : '',
          manualPayload.city,
          manualPayload.district,
          manualPayload.state,
          manualPayload.pincode,
          manualPayload.additionalDetails ? `(${manualPayload.additionalDetails})` : '',
        ]
          .filter(Boolean)
          .join(', ')
      : '';

    const finalSummary = description.trim()
      ? manualLocationText
        ? `${description.trim()}\n\nLocation Details: ${manualLocationText}`
        : description.trim()
      : manualLocationText || title.trim();

    try {
      await onSubmit({
        title: title.trim(),
        category,
        severity,
        description: finalSummary,
        latitude: hasCoords ? activeLat : null,
        longitude: hasCoords ? activeLon : null,
        accuracy: hasCoords ? activeAccuracy : null,
        location_source: sourceTag,
        captured_at: new Date().toISOString(),
        manualLocation: manualPayload,
        files: selectedFiles,
      });

      // Publish to central TacticalEventBus
      TacticalEventBus.publish({
        type: 'INCIDENT_REPORTED',
        severity: severity === 'critical' ? 'CRITICAL' : 'WARNING',
        actor: 'Incident Commander',
        title: title.trim(),
        description: finalSummary,
        metadata: {
          category,
          severity,
          latitude: hasCoords ? activeLat : null,
          longitude: hasCoords ? activeLon : null,
          accuracy: hasCoords ? activeAccuracy : null,
          source: sourceTag,
          manualLocation: manualPayload,
          photoCount: selectedFiles.length,
        },
      });

      if (selectedFiles.length > 0) {
        TacticalEventBus.publish({
          type: 'PHOTOS_ATTACHED',
          severity: 'INFO',
          actor: 'Incident Commander',
          title: `Attached ${selectedFiles.length} Incident Photo${selectedFiles.length > 1 ? 's' : ''}`,
          description: `Evidence photos linked to ${title.trim()}`,
          metadata: { count: selectedFiles.length, names: selectedFiles.map((f) => f.name) },
        });
      }

      resetForm();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to broadcast incident.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(3, 7, 18, 0.82)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '16px',
      }}
    >
      <div
        style={{
          background: colors.bgSurface,
          border: `1px solid ${colors.borderMedium}`,
          borderRadius: radii.xl,
          width: '100%',
          maxWidth: '680px',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: shadows.elevated,
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '16px 22px',
            borderBottom: `1px solid ${colors.borderSubtle}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.01)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>🚨</span>
              <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: colors.textPrimary }}>
                REPORT EMERGENCY INCIDENT
              </h2>
            </div>
            <div style={{ fontSize: '0.74rem', color: colors.textMuted, marginTop: '2px' }}>
              Broadcast real-time tactical incident across decentralized P2P mesh network
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: colors.textMuted,
              fontSize: '1.2rem',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form
          onSubmit={handleSubmit}
          style={{
            padding: '20px 22px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            flex: 1,
          }}
        >
          {error && (
            <div
              style={{
                background: colors.criticalBg,
                border: `1px solid ${colors.criticalBorder}`,
                color: '#fca5a5',
                padding: '10px 14px',
                borderRadius: radii.md,
                fontSize: '0.80rem',
                lineHeight: 1.4,
              }}
            >
              ⚠ {error}
            </div>
          )}

          {/* Title */}
          <div>
            <label style={{ display: 'block', fontSize: '0.80rem', fontWeight: 700, color: colors.textPrimary, marginBottom: '6px' }}>
              Incident Title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Chemical Spill near Industrial Area"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                width: '100%',
                background: colors.bgApp,
                border: `1px solid ${colors.borderSubtle}`,
                borderRadius: radii.md,
                padding: '9px 12px',
                color: colors.textPrimary,
                fontSize: '0.86rem',
                fontFamily: fonts.sans,
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Category & Severity Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.80rem', fontWeight: 700, color: colors.textPrimary, marginBottom: '6px' }}>
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: '100%',
                  background: colors.bgApp,
                  border: `1px solid ${colors.borderSubtle}`,
                  borderRadius: radii.md,
                  padding: '9px 12px',
                  color: colors.textPrimary,
                  fontSize: '0.84rem',
                  fontFamily: fonts.sans,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              >
                <option value="hazmat">Hazmat / Chemical</option>
                <option value="collapse">Structural Collapse</option>
                <option value="fire">Fire / Explosion</option>
                <option value="flood">Flood / Water Rescue</option>
                <option value="medical">Medical Mass Casualty</option>
                <option value="search_rescue">Search & Rescue</option>
                <option value="general">General / Other</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.80rem', fontWeight: 700, color: colors.textPrimary, marginBottom: '6px' }}>
                Severity
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                style={{
                  width: '100%',
                  background: colors.bgApp,
                  border: `1px solid ${colors.borderSubtle}`,
                  borderRadius: radii.md,
                  padding: '9px 12px',
                  color: colors.textPrimary,
                  fontSize: '0.84rem',
                  fontFamily: fonts.sans,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              >
                <option value="critical">🔴 Critical (Priority 1)</option>
                <option value="high">🟠 High (Priority 2)</option>
                <option value="medium">🟡 Medium (Priority 3)</option>
                <option value="low">🟢 Low (Priority 4)</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={{ display: 'block', fontSize: '0.80rem', fontWeight: 700, color: colors.textPrimary, marginBottom: '6px' }}>
              Description
            </label>
            <textarea
              rows={3}
              placeholder="Describe what happened, hazards observed, civilian impact..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{
                width: '100%',
                background: colors.bgApp,
                border: `1px solid ${colors.borderSubtle}`,
                borderRadius: radii.md,
                padding: '9px 12px',
                color: colors.textPrimary,
                fontSize: '0.84rem',
                fontFamily: fonts.sans,
                outline: 'none',
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* LOCATION SECTION */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.45)',
              border: `1px solid ${colors.borderSubtle}`,
              borderRadius: radii.lg,
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '0.80rem', fontWeight: 800, color: colors.textPrimary, letterSpacing: '0.04em' }}>
                LOCATION
              </div>
              <span style={{ fontSize: '0.70rem', color: isOnline ? colors.low : colors.high }}>
                {isOnline ? '🌐 Connected' : '📡 Offline Mode'}
              </span>
            </div>

            {/* Location Acquisition Methods Bar */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={detectLocation}
                disabled={isLocating}
                style={{
                  flex: 1,
                  background: locationResult?.source !== 'MANUAL_MAP' && locationResult?.isWithin20m ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.1)',
                  border: `1px solid ${locationResult?.source !== 'MANUAL_MAP' && locationResult?.isWithin20m ? '#10b981' : 'rgba(56, 189, 248, 0.3)'}`,
                  color: locationResult?.source !== 'MANUAL_MAP' && locationResult?.isWithin20m ? '#34d399' : colors.accent,
                  borderRadius: radii.md,
                  padding: '8px 12px',
                  fontSize: '0.76rem',
                  fontWeight: '700',
                  cursor: isLocating ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <span>📡</span> {isLocating ? 'Acquiring Location...' : 'GPS / Device'}
              </button>

              <button
                type="button"
                onClick={() => setIsMapPickerOpen(true)}
                style={{
                  flex: 1,
                  background: locationResult?.source === 'MANUAL_MAP' ? 'rgba(245, 158, 11, 0.18)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${locationResult?.source === 'MANUAL_MAP' ? '#f59e0b' : colors.borderSubtle}`,
                  color: locationResult?.source === 'MANUAL_MAP' ? '#fbbf24' : colors.textPrimary,
                  borderRadius: radii.md,
                  padding: '8px 12px',
                  fontSize: '0.76rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <span>📍</span> {locationResult?.source === 'MANUAL_MAP' ? 'Change Pin on Map' : 'Pick on Map'}
              </button>
            </div>

            {/* Locating Spinner */}
            {isLocating && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 0', color: colors.accent }}>
                <span style={{ fontSize: '1.1rem', animation: 'spin 1s infinite' }}>📡</span>
                <span style={{ fontSize: '0.78rem' }}>Acquiring high-accuracy physical device location (GNSS / OS)...</span>
              </div>
            )}

            {/* Location Status Banners */}
            {!isLocating && locationResult?.source === 'MANUAL_MAP' && activeLat !== null && activeLon !== null && (
              /* State 1: Manual Map Pin Selected */
              <div
                style={{
                  background: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.35)',
                  borderRadius: radii.md,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: colors.accent, fontWeight: 800, fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>📍</span> MANUAL MAP SELECTION
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: colors.accent,
                      padding: '2px 8px',
                      borderRadius: radii.full,
                      fontWeight: 700,
                    }}
                  >
                    Source: MAP PIN
                  </span>
                </div>
                <div style={{ fontFamily: fonts.mono, fontSize: '0.84rem', color: colors.textPrimary, fontWeight: 700 }}>
                  {activeLat.toFixed(6)}°, {activeLon.toFixed(6)}°
                </div>
                <div style={{ fontSize: '0.72rem', color: colors.textMuted }}>
                  Accuracy: <strong>Manual Selection (Not verified)</strong> • Sector: <strong>{resolvedAddress}</strong>
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                  <button
                    type="button"
                    onClick={() => setIsMapPickerOpen(true)}
                    style={{
                      background: 'rgba(56, 189, 248, 0.12)',
                      color: colors.accent,
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    ↺ Change Pin
                  </button>
                  <button
                    type="button"
                    onClick={detectLocation}
                    style={{
                      background: 'transparent',
                      color: colors.textMuted,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    📡 Use Device GPS Instead
                  </button>
                </div>
              </div>
            )}

            {!isLocating && locationResult?.source !== 'MANUAL_MAP' && locationResult && locationResult.latitude !== null && locationResult.longitude !== null && locationResult.isWithin20m && (
              /* State 2: Good GPS / GNSS Location (<= 20m) */
              <div
                style={{
                  background: 'rgba(6, 78, 59, 0.25)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: radii.md,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#34d399', fontWeight: 800, fontSize: '0.82rem' }}>
                    ✓ LOCATION VERIFIED
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#34d399',
                      padding: '2px 8px',
                      borderRadius: radii.full,
                      fontWeight: 700,
                    }}
                  >
                    Source: {locationResult.source}
                  </span>
                </div>

                <div style={{ fontFamily: fonts.mono, fontSize: '0.84rem', color: colors.textPrimary, fontWeight: 700 }}>
                  {locationResult.latitude.toFixed(6)}°, {locationResult.longitude.toFixed(6)}°
                </div>

                <div style={{ display: 'flex', gap: '16px', fontSize: '0.74rem', color: colors.textSecondary }}>
                  <div>
                    Accuracy: <strong style={{ color: '#34d399' }}>±{locationResult.accuracy} m</strong>
                  </div>
                  <div>
                    Status: <strong style={{ color: '#34d399' }}>Ready to broadcast</strong>
                  </div>
                  {locationResult.timestamp && (
                    <div style={{ color: colors.textMuted }}>Fix: {locationResult.timestamp}</div>
                  )}
                </div>

                {resolvedAddress && (
                  <div style={{ fontSize: '0.74rem', color: colors.textMuted }}>
                    📍 {resolvedAddress}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                  <button
                    type="button"
                    onClick={detectLocation}
                    style={{
                      background: 'rgba(56, 189, 248, 0.1)',
                      color: colors.accent,
                      border: `1px solid ${colors.accent}`,
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    ↺ Refresh Location
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsMapPickerOpen(true)}
                    style={{
                      background: 'transparent',
                      color: colors.textSecondary,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    🗺️ Pick on Map
                  </button>
                </div>
              </div>
            )}

            {!isLocating && locationResult?.source !== 'MANUAL_MAP' && locationResult && locationResult.latitude !== null && locationResult.longitude !== null && !locationResult.isWithin20m && (
              /* State 3: Low Accuracy Location (> 20m) */
              <div
                style={{
                  background: 'rgba(120, 53, 15, 0.25)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  borderRadius: radii.md,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '0.82rem' }}>
                    ⚠ LOW LOCATION ACCURACY
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#fbbf24',
                      padding: '2px 8px',
                      borderRadius: radii.full,
                      fontWeight: 700,
                    }}
                  >
                    Source: {locationResult.source}
                  </span>
                </div>

                <div style={{ fontFamily: fonts.mono, fontSize: '0.84rem', color: colors.textPrimary, fontWeight: 700 }}>
                  {locationResult.latitude.toFixed(6)}°, {locationResult.longitude.toFixed(6)}°
                </div>

                <div style={{ display: 'flex', gap: '16px', fontSize: '0.74rem', color: colors.textSecondary }}>
                  <div>
                    Current: <strong style={{ color: '#fbbf24' }}>±{locationResult.accuracy} m</strong>
                  </div>
                  <div>
                    Required: <strong style={{ color: colors.textPrimary }}>≤20 m</strong>
                  </div>
                  <div>
                    Status: <strong style={{ color: '#fbbf24' }}>Manual location recommended</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                  <button
                    type="button"
                    onClick={detectLocation}
                    style={{
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#fbbf24',
                      border: '1px solid rgba(245, 158, 11, 0.4)',
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    ↺ Retry Location
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsMapPickerOpen(true)}
                    style={{
                      background: colors.accent,
                      color: '#070B14',
                      border: 'none',
                      borderRadius: radii.sm,
                      padding: '4px 12px',
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    🗺️ Pick on Map
                  </button>
                </div>
              </div>
            )}

            {!isLocating && locationResult?.source !== 'MANUAL_MAP' && (!locationResult || locationResult.source === 'Unavailable' || locationResult.latitude === null) && (
              /* State 4: Location Unavailable */
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: radii.md,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: colors.critical, fontWeight: 800, fontSize: '0.82rem' }}>
                    ⚠ DEVICE LOCATION UNAVAILABLE
                  </span>
                </div>
                <div style={{ fontSize: '0.74rem', color: colors.textSecondary, lineHeight: 1.4 }}>
                  Unable to acquire physical device location (GNSS/GPS sensor not detected or permission denied).
                  Use the <strong>Pick on Map</strong> tool or enter the address and landmark details below.
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                  <button
                    type="button"
                    onClick={detectLocation}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: `1px solid ${colors.borderSubtle}`,
                      color: colors.textPrimary,
                      borderRadius: radii.sm,
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    ↺ Retry Location
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsMapPickerOpen(true)}
                    style={{
                      background: colors.accent,
                      color: '#070B14',
                      border: 'none',
                      borderRadius: radii.sm,
                      padding: '4px 12px',
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    🗺️ Pick on Map
                  </button>
                </div>
              </div>
            )}

            {/* MANUAL LOCATION DETAILS (ALWAYS AVAILABLE) */}
            <div
              style={{
                borderTop: `1px solid ${colors.borderSubtle}`,
                paddingTop: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: colors.accent, letterSpacing: '0.04em' }}>
                  MANUAL LOCATION DETAILS
                </div>
                <span style={{ fontSize: '0.68rem', color: colors.textMuted }}>
                  Always available for field landmarks & addresses
                </span>
              </div>

              {/* Address */}
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                  Address / Street
                </label>
                <input
                  type="text"
                  placeholder="Enter street / building / area"
                  value={manualAddress}
                  onChange={(e) => setManualAddress(e.target.value)}
                  style={{
                    width: '100%',
                    background: colors.bgApp,
                    border: `1px solid ${colors.borderSubtle}`,
                    borderRadius: radii.sm,
                    padding: '7px 10px',
                    color: colors.textPrimary,
                    fontSize: '0.80rem',
                    fontFamily: fonts.sans,
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* Local Landmark */}
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                  Local Landmark
                </label>
                <input
                  type="text"
                  placeholder="e.g. Near Apollo Hospital, opposite Railway Station"
                  value={manualLandmark}
                  onChange={(e) => setManualLandmark(e.target.value)}
                  style={{
                    width: '100%',
                    background: colors.bgApp,
                    border: `1px solid ${colors.borderSubtle}`,
                    borderRadius: radii.sm,
                    padding: '7px 10px',
                    color: colors.textPrimary,
                    fontSize: '0.80rem',
                    fontFamily: fonts.sans,
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* City & District Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                    City / Town
                  </label>
                  <input
                    type="text"
                    placeholder="Hyderabad"
                    value={manualCity}
                    onChange={(e) => setManualCity(e.target.value)}
                    style={{
                      width: '100%',
                      background: colors.bgApp,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '7px 10px',
                      color: colors.textPrimary,
                      fontSize: '0.80rem',
                      fontFamily: fonts.sans,
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                    District
                  </label>
                  <input
                    type="text"
                    placeholder="Rangareddy"
                    value={manualDistrict}
                    onChange={(e) => setManualDistrict(e.target.value)}
                    style={{
                      width: '100%',
                      background: colors.bgApp,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '7px 10px',
                      color: colors.textPrimary,
                      fontSize: '0.80rem',
                      fontFamily: fonts.sans,
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>

              {/* State & Pincode Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                    State
                  </label>
                  <input
                    type="text"
                    placeholder="Telangana"
                    value={manualState}
                    onChange={(e) => setManualState(e.target.value)}
                    style={{
                      width: '100%',
                      background: colors.bgApp,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '7px 10px',
                      color: colors.textPrimary,
                      fontSize: '0.80rem',
                      fontFamily: fonts.sans,
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                    Pincode (6 digits)
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="500001"
                    value={manualPincode}
                    onChange={(e) => setManualPincode(e.target.value.replace(/\D/g, ''))}
                    style={{
                      width: '100%',
                      background: colors.bgApp,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.sm,
                      padding: '7px 10px',
                      color: colors.textPrimary,
                      fontSize: '0.80rem',
                      fontFamily: 'monospace',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>

              {/* Additional Location Details */}
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: colors.textSecondary, marginBottom: '4px' }}>
                  Additional Location Details (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Behind the railway station, near the north gate"
                  value={manualDetails}
                  onChange={(e) => setManualDetails(e.target.value)}
                  style={{
                    width: '100%',
                    background: colors.bgApp,
                    border: `1px solid ${colors.borderSubtle}`,
                    borderRadius: radii.sm,
                    padding: '7px 10px',
                    color: colors.textPrimary,
                    fontSize: '0.80rem',
                    fontFamily: fonts.sans,
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>
          </div>

          {/* INCIDENT PHOTOS SECTION */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.45)',
              border: `1px solid ${colors.borderSubtle}`,
              borderRadius: radii.lg,
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '0.80rem', fontWeight: 800, color: colors.textPrimary, letterSpacing: '0.04em' }}>
                  INCIDENT PHOTOS
                </div>
                <div style={{ fontSize: '0.70rem', color: colors.textMuted }}>
                  Supported formats: JPG, JPEG, PNG, WEBP (Max 10MB each)
                </div>
              </div>
              <span style={{ fontSize: '0.72rem', color: colors.accentElectric, fontWeight: 700 }}>
                {selectedFiles.length} photo{selectedFiles.length !== 1 ? 's' : ''}
              </span>
            </div>

            {cameraError && (
              <div style={{ fontSize: '0.72rem', color: colors.critical, background: colors.criticalBg, padding: '4px 8px', borderRadius: radii.sm }}>
                ⚠ {cameraError}
              </div>
            )}

            {/* Hidden native inputs */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleCameraCapture}
              style={{ display: 'none' }}
            />

            {/* Prominent Action Buttons */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={handleTriggerCamera}
                style={{
                  flex: 1,
                  background: 'rgba(56, 189, 248, 0.12)',
                  border: `1px solid ${colors.accentElectric}`,
                  borderRadius: radii.md,
                  padding: '9px 14px',
                  color: colors.accentElectric,
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.2)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.12)')}
              >
                <span>📷</span>
                <span>Capture Photo</span>
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${colors.borderSubtle}`,
                  borderRadius: radii.md,
                  padding: '9px 14px',
                  color: colors.textPrimary,
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)')}
              >
                <span>📎</span>
                <span>Attach Photos</span>
              </button>
            </div>

            {/* Thumbnail Previews */}
            {filePreviews.length > 0 && (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '4px' }}>
                {filePreviews.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      position: 'relative',
                      width: '68px',
                      height: '68px',
                      borderRadius: radii.md,
                      overflow: 'hidden',
                      border: `1px solid ${colors.accentElectric}`,
                      background: '#070B14',
                    }}
                  >
                    <img
                      src={p.previewUrl}
                      alt={p.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <div
                      style={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        background: 'rgba(0, 0, 0, 0.75)',
                        fontSize: '0.55rem',
                        color: '#fff',
                        textAlign: 'center',
                        padding: '1px 2px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {p.size}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(p.id)}
                      style={{
                        position: 'absolute',
                        top: '2px',
                        right: '2px',
                        background: 'rgba(239, 68, 68, 0.9)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '50%',
                        width: '18px',
                        height: '18px',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        padding: 0,
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Form Action Buttons */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px',
              borderTop: `1px solid ${colors.borderSubtle}`,
              paddingTop: '16px',
            }}
          >
            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                color: colors.textSecondary,
                border: `1px solid ${colors.borderSubtle}`,
                padding: '9px 18px',
                borderRadius: radii.md,
                fontSize: '0.84rem',
                cursor: 'pointer',
                fontWeight: 700,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              style={{
                background: colors.critical,
                color: '#ffffff',
                border: 'none',
                padding: '9px 22px',
                borderRadius: radii.md,
                fontSize: '0.86rem',
                fontWeight: 800,
                cursor: submitting ? 'not-allowed' : 'pointer',
                opacity: submitting ? 0.7 : 1,
                boxShadow: '0 2px 10px rgba(239, 68, 68, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>🚨</span>
              <span>{submitting ? 'Broadcasting...' : 'Broadcast Incident'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Interactive 100% Offline Map Pin Picker Modal */}
      <LocationPickerModal
        isOpen={isMapPickerOpen}
        initialLat={activeLat}
        initialLon={activeLon}
        userLocation={activeLat && activeLon ? { lat: activeLat, lon: activeLon } : null}
        onConfirm={(coords) => {
          setActiveLat(coords.lat);
          setActiveLon(coords.lon);
          setActiveAccuracy(null);
          setResolvedAddress(coords.address || `${coords.lat.toFixed(5)}, ${coords.lon.toFixed(5)}`);
          setLocationResult({
            latitude: coords.lat,
            longitude: coords.lon,
            accuracy: null,
            source: 'MANUAL_MAP',
            timestamp: new Date().toLocaleTimeString(),
            rawTimestamp: Date.now(),
            isFresh: true,
            isWithin20m: false,
            accuracyLabel: 'MANUAL_SELECTION',
            resolvedAddress: coords.address,
          });
          setIsMapPickerOpen(false);
        }}
        onCancel={() => setIsMapPickerOpen(false)}
      />
    </div>
  );
};
