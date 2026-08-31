import React, { useState } from 'react';
import { TacticalGisMap } from './TacticalGisMap';
import { ErrorBoundary } from './ErrorBoundary';

export interface MapIncidentMarker {
  id: string;
  title: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  lat: number | null;
  lon: number | null;
  accuracy?: number | null;
  locationSource?: string | null;
  reportCount: number;
  broadcasterName?: string;
  summary?: string;
  description?: string;
  manualLocation?: any;
}

interface MapViewProps {
  incidents: MapIncidentMarker[];
  selectedIncidentId?: string | null;
  onSelectIncident: (id: string) => void;
  onOpenDetailsModal?: (incident: MapIncidentMarker) => void;
  isPickingLocation?: boolean;
  onLocationPicked?: (coords: { lat: number; lon: number }) => void;
  pickedCoords?: { lat: number; lon: number } | null;
  onCancelPickLocation?: () => void;
  userLocation?: { lat: number; lon: number } | null;
}

export const MapView: React.FC<MapViewProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onOpenDetailsModal,
  isPickingLocation,
  onLocationPicked,
  pickedCoords,
  onCancelPickLocation,
  userLocation,
}) => {
  const [viewMode, setViewMode] = useState<'globe' | 'grid'>('globe');
  const [severityFilter, setSeverityFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');

  const counts = {
    all: incidents.length,
    critical: incidents.filter((i) => i.severity.toLowerCase() === 'critical').length,
    high: incidents.filter((i) => i.severity.toLowerCase() === 'high').length,
    medium: incidents.filter((i) => i.severity.toLowerCase() === 'medium').length,
    low: incidents.filter((i) => i.severity.toLowerCase() === 'low').length,
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (severityFilter === 'all') return true;
    return inc.severity.toLowerCase() === severityFilter;
  });

  const mappedCount = filteredIncidents.filter((i) => i.lat !== null && i.lon !== null).length;

  return (
    <div
      className="map-view-container"
      style={{
        width: '100%',
        height: '100%',
        minHeight: '480px',
        background: '#1e293b',
        borderRadius: '8px',
        padding: '16px',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* View Header with Mode Toggles */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0 }}>Incident Situational Map</h3>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            Showing: <strong>{filteredIncidents.length}</strong> / {incidents.length} (Mapped: {mappedCount})
          </span>
        </div>

        <div style={{ display: 'flex', gap: '6px', background: '#0f172a', padding: '3px', borderRadius: '6px', border: '1px solid #334155' }}>
          <button
            type="button"
            onClick={() => setViewMode('globe')}
            style={{
              background: viewMode === 'globe' ? '#0284c7' : 'transparent',
              color: viewMode === 'globe' ? '#ffffff' : '#94a3b8',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <span>🗺️</span> Tactical 3D Map
          </button>
          <button
            type="button"
            onClick={() => setViewMode('grid')}
            style={{
              background: viewMode === 'grid' ? '#0284c7' : 'transparent',
              color: viewMode === 'grid' ? '#ffffff' : '#94a3b8',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <span>📋</span> Card Grid
          </button>
        </div>
      </div>

      {/* Severity Filter Bar */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid #334155',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: '600', marginRight: '4px' }}>
          Severity Filter:
        </span>
        <button
          type="button"
          onClick={() => setSeverityFilter('all')}
          style={{
            background: severityFilter === 'all' ? '#0284c7' : 'transparent',
            border: `1px solid ${severityFilter === 'all' ? '#38bdf8' : '#334155'}`,
            color: severityFilter === 'all' ? '#ffffff' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            fontWeight: '700',
            cursor: 'pointer',
          }}
        >
          All ({counts.all})
        </button>
        <button
          type="button"
          onClick={() => setSeverityFilter('critical')}
          style={{
            background: severityFilter === 'critical' ? 'rgba(239, 68, 68, 0.25)' : 'transparent',
            border: `1px solid ${severityFilter === 'critical' ? '#ef4444' : '#334155'}`,
            color: severityFilter === 'critical' ? '#ef4444' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            fontWeight: '700',
            cursor: 'pointer',
          }}
        >
          🔴 Critical ({counts.critical})
        </button>
        <button
          type="button"
          onClick={() => setSeverityFilter('high')}
          style={{
            background: severityFilter === 'high' ? 'rgba(249, 115, 22, 0.25)' : 'transparent',
            border: `1px solid ${severityFilter === 'high' ? '#f97316' : '#334155'}`,
            color: severityFilter === 'high' ? '#f97316' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            fontWeight: '700',
            cursor: 'pointer',
          }}
        >
          🟠 High ({counts.high})
        </button>
        <button
          type="button"
          onClick={() => setSeverityFilter('medium')}
          style={{
            background: severityFilter === 'medium' ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
            border: `1px solid ${severityFilter === 'medium' ? '#f59e0b' : '#334155'}`,
            color: severityFilter === 'medium' ? '#f59e0b' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            fontWeight: '700',
            cursor: 'pointer',
          }}
        >
          🟡 Medium ({counts.medium})
        </button>
        <button
          type="button"
          onClick={() => setSeverityFilter('low')}
          style={{
            background: severityFilter === 'low' ? 'rgba(16, 185, 129, 0.25)' : 'transparent',
            border: `1px solid ${severityFilter === 'low' ? '#10b981' : '#334155'}`,
            color: severityFilter === 'low' ? '#10b981' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.72rem',
            fontWeight: '700',
            cursor: 'pointer',
          }}
        >
          🟢 Low ({counts.low})
        </button>
      </div>

      {/* Main View Area: Persistent Map Canvas */}
      <div style={{ flex: 1, minHeight: '480px', position: 'relative' }}>
        {/* Tactical 3D Map Container (PERSISTENT: Never unmounted during filter/view changes) */}
        <div
          style={{
            width: '100%',
            height: '100%',
            minHeight: '480px',
            display: viewMode === 'globe' ? 'block' : 'none',
            position: 'relative',
          }}
        >
          <ErrorBoundary fallbackTitle="Tactical 3D Map Rendering Notice">
            <TacticalGisMap
              incidents={filteredIncidents}
              selectedIncidentId={selectedIncidentId}
              onSelectIncident={onSelectIncident}
              onOpenDetailsModal={onOpenDetailsModal}
              isPickingLocation={isPickingLocation}
              onLocationPicked={onLocationPicked}
              pickedCoords={pickedCoords}
              onCancelPickLocation={onCancelPickLocation}
              userLocation={userLocation}
            />
          </ErrorBoundary>

          {filteredIncidents.length === 0 && (
            <div
              style={{
                position: 'absolute',
                top: '58px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1px solid #f59e0b',
                color: '#fbbf24',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                fontWeight: '700',
                boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
                zIndex: 20,
                pointerEvents: 'none',
              }}
            >
              ⚠ No incidents matching filter '{severityFilter.toUpperCase()}'. Base tactical map active.
            </div>
          )}
        </div>

        {/* Card Grid View (Rendered in parallel when active, without destroying the map) */}
        {viewMode === 'grid' && (
          <div
            className="map-grid"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: '12px',
              maxHeight: '480px',
              overflowY: 'auto',
            }}
          >
            {filteredIncidents.length === 0 ? (
              <div
                style={{
                  gridColumn: '1 / -1',
                  textAlign: 'center',
                  padding: '30px',
                  background: '#0f172a',
                  borderRadius: '6px',
                  border: '1px dashed #334155',
                  color: '#94a3b8',
                }}
              >
                No incidents matching filter '{severityFilter.toUpperCase()}'.
              </div>
            ) : (
              filteredIncidents.map((inc) => {
                const isSelected = inc.id === selectedIncidentId;
                const severityColors = {
                  low: '#10b981',
                  medium: '#f59e0b',
                  high: '#f97316',
                  critical: '#ef4444',
                };

                return (
                  <div
                    key={inc.id}
                    onClick={() => {
                      onSelectIncident(inc.id);
                      if (onOpenDetailsModal) {
                        onOpenDetailsModal(inc);
                      }
                    }}
                    style={{
                      background: isSelected ? '#334155' : '#0f172a',
                      border: `2px solid ${isSelected ? '#38bdf8' : severityColors[inc.severity] || '#64748b'}`,
                      borderRadius: '6px',
                      padding: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{inc.title}</span>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: severityColors[inc.severity],
                          color: '#fff',
                          fontWeight: 'bold',
                        }}
                      >
                        {inc.severity.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: '600', marginBottom: '4px' }}>
                      📡 Broadcaster: {inc.broadcasterName || 'Commander'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                      {inc.lat !== null && inc.lon !== null
                        ? `📍 ${inc.lat.toFixed(4)}, ${inc.lon.toFixed(4)}${inc.accuracy ? ` (±${inc.accuracy}m)` : ''}`
                        : '📍 Location: Unavailable'}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                      <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                        Reports Linked: <strong>{inc.reportCount}</strong>
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#38bdf8', textDecoration: 'underline' }}>
                        Details ↗
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
};
