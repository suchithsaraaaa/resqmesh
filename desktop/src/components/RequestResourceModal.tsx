import React, { useState, useEffect } from 'react';
import { MapIncidentMarker } from './MapView';

interface RequestResourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  incidents: MapIncidentMarker[];
  selectedIncidentId?: string | null;
  onSubmit: (data: {
    incident_id: string;
    resource_type: string;
    quantity: number;
    urgency: string;
  }) => Promise<void>;
}

const PRESET_RESOURCES = [
  'Advanced Life Support Ambulance',
  'Fire Suppression Foam Unit',
  'Heavy Duty Mobile Generator (25kW)',
  'Hazmat Decontamination Squad',
  'Search & Rescue Aerial Drone Team',
  'Swift Water Rescue Inflatable Boat',
  'Emergency Medical Trauma Kits',
  'High-Output Portable Water Pump',
];

export const RequestResourceModal: React.FC<RequestResourceModalProps> = ({
  isOpen,
  onClose,
  incidents,
  selectedIncidentId,
  onSubmit,
}) => {
  const [incidentId, setIncidentId] = useState<string>('');
  const [resourceType, setResourceType] = useState<string>('Advanced Life Support Ambulance');
  const [customType, setCustomType] = useState<string>('');
  const [quantity, setQuantity] = useState<number>(1);
  const [urgency, setUrgency] = useState<string>('high');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedIncidentId && incidents.some((i) => i.id === selectedIncidentId)) {
      setIncidentId(selectedIncidentId);
    } else if (incidents.length > 0) {
      setIncidentId(incidents[0].id);
    }
  }, [selectedIncidentId, incidents, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentId) {
      setError('Please select an active incident to tie this resource request to.');
      return;
    }

    const finalType = resourceType === 'custom' ? customType.trim() : resourceType;
    if (!finalType) {
      setError('Please specify a resource type or description.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        incident_id: incidentId,
        resource_type: finalType,
        quantity: Math.max(1, quantity),
        urgency,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to broadcast resource request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        style={{
          backgroundColor: '#0D1422',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '20px',
          padding: '24px',
          width: '100%',
          maxWidth: '520px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
          color: '#f8fafc',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            paddingBottom: '14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.4rem' }}>📦</span>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 'bold' }}>
              Request Incident Resources
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              fontSize: '1.2rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {error && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              padding: '10px',
              borderRadius: '6px',
              marginBottom: '16px',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Tied Incident Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>
              🎯 Tied Incident
            </label>
            <select
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid #334155',
                backgroundColor: '#1e293b',
                color: '#f8fafc',
                fontSize: '0.9rem',
              }}
            >
              <option value="new_auto">⚡ + Auto-Create & Broadcast New Incident for this Request</option>
              {incidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.title} ({inc.severity.toUpperCase()}) — Broadcaster: {inc.broadcasterName || 'Commander'}
                </option>
              ))}
            </select>
          </div>

          {/* Resource Preset / Selection */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>
              Resource Type / Equipment
            </label>
            <select
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid #334155',
                backgroundColor: '#1e293b',
                color: '#f8fafc',
                fontSize: '0.9rem',
                marginBottom: '8px',
              }}
            >
              {PRESET_RESOURCES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
              <option value="custom">-- Custom Equipment / Unit --</option>
            </select>

            {resourceType === 'custom' && (
              <input
                type="text"
                placeholder="e.g. Heavy Duty Hydraulic Rescue Cutters"
                value={customType}
                onChange={(e) => setCustomType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #334155',
                  backgroundColor: '#1e293b',
                  color: '#f8fafc',
                  fontSize: '0.9rem',
                  boxSizing: 'border-box',
                }}
              />
            )}
          </div>

          {/* Quantity & Urgency Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>
                Quantity Needed
              </label>
              <input
                type="number"
                min="1"
                max="99"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 1)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #334155',
                  backgroundColor: '#1e293b',
                  color: '#f8fafc',
                  fontSize: '0.9rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>
                Urgency Level
              </label>
              <select
                value={urgency}
                onChange={(e) => setUrgency(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #334155',
                  backgroundColor: '#1e293b',
                  color: '#f8fafc',
                  fontSize: '0.9rem',
                }}
              >
                <option value="low">Low (Standard Supply)</option>
                <option value="medium">Medium (Tactical Need)</option>
                <option value="high">High (Urgent Field Need)</option>
                <option value="critical">Critical (Life Threatening)</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '9px 16px',
                borderRadius: '6px',
                border: '1px solid #334155',
                backgroundColor: 'transparent',
                color: '#94a3b8',
                cursor: 'pointer',
                fontWeight: '600',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || incidents.length === 0}
              style={{
                padding: '9px 18px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#0284c7',
                color: '#ffffff',
                cursor: submitting || incidents.length === 0 ? 'not-allowed' : 'pointer',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 0 12px rgba(2, 132, 199, 0.4)',
              }}
            >
              {submitting ? 'Broadcasting across Mesh...' : '📡 Broadcast Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
