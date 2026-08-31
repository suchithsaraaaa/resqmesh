import React, { useState, useEffect } from 'react';
import { MapIncidentMarker } from './MapView';
import { ResourceRequestItem } from './ResourceDispatchPanel';

export interface AttachmentItem {
  id: string;
  incident_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  created_at: string;
}

export interface RelatedReportItem {
  report_id: string;
  incident_id?: string;
  user_id?: string;
  device_id?: string;
  description: string;
  timestamp: string;
  category?: string;
}

interface IncidentDetailsModalProps {
  incident: MapIncidentMarker | null;
  isOpen: boolean;
  onClose: () => void;
  onRequestResources: (incidentId: string) => void;
  resources: ResourceRequestItem[];
  apiUrl?: string;
}

export const IncidentDetailsModal: React.FC<IncidentDetailsModalProps> = ({
  incident,
  isOpen,
  onClose,
  onRequestResources,
  resources,
  apiUrl = 'http://127.0.0.1:8000',
}) => {
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [reports, setReports] = useState<RelatedReportItem[]>([]);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [selectedPhoto, setSelectedPhoto] = useState<AttachmentItem | null>(null);

  // Fetch full incident details (including attachments and linked observer reports)
  useEffect(() => {
    if (isOpen && incident?.id) {
      setLoadingDetails(true);
      fetch(`${apiUrl}/incidents/${incident.id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setAttachments(data.attachments || []);
            setReports(data.reports || []);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingDetails(false));
    } else {
      setAttachments([]);
      setReports([]);
      setSelectedPhoto(null);
    }
  }, [isOpen, incident?.id, apiUrl]);

  if (!isOpen || !incident) return null;

  const tiedResources = resources.filter((r) => r.incidentId === incident.id);

  const getSeverityBadgeColor = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return '#ef4444';
      case 'high':
        return '#f97316';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#10b981';
      default:
        return '#64748b';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <>
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
        onClick={onClose}
      >
        <div
          style={{
            backgroundColor: '#0D1422',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '20px',
            padding: '24px',
            width: '100%',
            maxWidth: '640px',
            maxHeight: '88vh',
            overflowY: 'auto',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
            color: '#f8fafc',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '16px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              paddingBottom: '14px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '1.4rem' }}>🚨</span>
                <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.3px' }}>
                  {incident.title}
                </h2>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span
                  style={{
                    backgroundColor: getSeverityBadgeColor(incident.severity),
                    color: '#ffffff',
                    fontSize: '0.75rem',
                    fontWeight: '800',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    textTransform: 'uppercase',
                  }}
                >
                  {incident.severity}
                </span>
                <span
                  style={{
                    backgroundColor: '#1e293b',
                    color: '#94a3b8',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid #334155',
                    textTransform: 'capitalize',
                  }}
                >
                  Category: {incident.category}
                </span>
                <span
                  style={{
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    color: '#38bdf8',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                  }}
                >
                  Reports Linked: {reports.length > 0 ? reports.length : incident.reportCount}
                </span>
                {attachments.length > 0 && (
                  <span
                    style={{
                      backgroundColor: 'rgba(16, 185, 129, 0.1)',
                      color: '#34d399',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                    }}
                  >
                    📷 {attachments.length} Photo{attachments.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                fontSize: '1.3rem',
                cursor: 'pointer',
                padding: '4px',
              }}
            >
              ✕
            </button>
          </div>

          {/* Broadcaster & Geo Details Box */}
          <div
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '12px 14px',
              marginBottom: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>First Broadcasted By:</span>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  color: '#10b981',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span>📡</span> {incident.broadcasterName || 'Commander'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Geographic Coordinates:</span>
              <span style={{ fontSize: '0.85rem', color: '#cbd5e1', fontFamily: 'monospace' }}>
                {incident.lat !== null && incident.lon !== null
                  ? `🌐 ${incident.lat.toFixed(6)}°, ${incident.lon.toFixed(6)}°${incident.accuracy ? ` (±${incident.accuracy}m)` : ''}`
                  : '📍 Manual Selection / Coordinates unavailable'}
              </span>
            </div>

            {/* Human / Landmark Location */}
            {Boolean(
              (incident as any).manualLocation ||
                (incident.description || incident.summary || '').includes('Location Details:')
            ) && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '6px', padding: '8px 10px', marginTop: '2px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#38bdf8' }}>📍 Human / Landmark Location:</span>
                <div style={{ fontSize: '0.82rem', color: '#f1f5f9', lineHeight: '1.4' }}>
                  {(incident as any).manualLocation ? (
                    [
                      (incident as any).manualLocation.address,
                      (incident as any).manualLocation.landmark ? `Near ${(incident as any).manualLocation.landmark}` : '',
                      (incident as any).manualLocation.city,
                      (incident as any).manualLocation.district,
                      (incident as any).manualLocation.state,
                      (incident as any).manualLocation.pincode,
                      (incident as any).manualLocation.additionalDetails ? `(${(incident as any).manualLocation.additionalDetails})` : '',
                    ].filter(Boolean).join(', ')
                  ) : (
                    (incident.description || incident.summary || '').split('Location Details:')[1]?.trim() || ''
                  )}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Tactical Mesh Incident ID:</span>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
                #{incident.id.slice(0, 16)}
              </span>
            </div>
          </div>

          {/* Incident Description & Tactical Summary */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: '700', color: '#cbd5e1' }}>
                📝 Incident Description & Situation Summary:
              </span>
            </div>
            <div
              style={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '12px 14px',
                color: '#e2e8f0',
                fontSize: '0.85rem',
                lineHeight: '1.5',
                maxHeight: '100px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {incident.summary && incident.summary.trim().length > 0
                ? incident.summary
                : 'Initial broadcast report. Emergency responders deployed to ground zero; ongoing situation assessment.'}
            </div>
          </div>

          {/* Attached Incident Photos Section */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: '700', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>📷</span> Incident Evidence Photos ({attachments.length}):
              </span>
              {loadingDetails && (
                <span style={{ fontSize: '0.72rem', color: '#38bdf8' }}>Loading media...</span>
              )}
            </div>

            {attachments.length === 0 ? (
              <div
                style={{
                  background: '#1e293b',
                  border: '1px dashed #334155',
                  borderRadius: '8px',
                  padding: '12px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '0.8rem',
                }}
              >
                No photo evidence attached to this incident.
              </div>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
                  gap: '10px',
                }}
              >
                {attachments.map((att) => (
                  <div
                    key={att.id}
                    onClick={() => setSelectedPhoto(att)}
                    title={`Click to inspect ${att.filename}`}
                    style={{
                      position: 'relative',
                      height: '90px',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      border: '1px solid #334155',
                      background: '#020617',
                      cursor: 'pointer',
                      transition: 'transform 0.15s ease, border-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#38bdf8';
                      e.currentTarget.style.transform = 'scale(1.02)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#334155';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  >
                    <img
                      src={`${apiUrl}/attachments/${att.id}/file`}
                      alt={att.filename}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                      onError={(e) => {
                        // Fallback placeholder on loading error
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                    <div
                      style={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        background: 'linear-gradient(to top, rgba(0,0,0,0.85), transparent)',
                        padding: '4px 6px',
                        fontSize: '0.68rem',
                        color: '#cbd5e1',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {att.filename}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Related Merged Reports Section */}
          {reports.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: '700', color: '#cbd5e1' }}>
                  📋 Linked Field Reports ({reports.length}):
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  maxHeight: '120px',
                  overflowY: 'auto',
                }}
              >
                {reports.map((rep) => (
                  <div
                    key={rep.report_id}
                    style={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      fontSize: '0.78rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#38bdf8', marginBottom: '2px' }}>
                      <span style={{ fontWeight: '700' }}>#{rep.report_id.slice(0, 12)}</span>
                      <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>
                        {rep.device_id || 'Field-Responder'}
                      </span>
                    </div>
                    <div style={{ color: '#e2e8f0', lineHeight: '1.4' }}>{rep.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tied Resources Section */}
          <div style={{ marginBottom: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: '700', color: '#cbd5e1' }}>
                📦 Currently Tied Resources ({tiedResources.length}):
              </span>
            </div>

            {tiedResources.length === 0 ? (
              <div
                style={{
                  background: '#1e293b',
                  border: '1px dashed #334155',
                  borderRadius: '6px',
                  padding: '10px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '0.8rem',
                }}
              >
                No tactical resources requested for this incident yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '100px', overflowY: 'auto' }}>
                {tiedResources.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      background: '#1e293b',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '0.8rem',
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: '700' }}>{r.quantity}x {r.resourceType}</span>
                      <span style={{ color: '#94a3b8', marginLeft: '6px', fontSize: '0.72rem' }}>
                        ({r.urgency.toUpperCase()})
                      </span>
                    </div>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: '700',
                        color: r.status === 'dispatched' ? '#10b981' : '#f59e0b',
                      }}
                    >
                      {r.status === 'dispatched' ? '✓ DISPATCHED' : '⏳ PENDING'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Footer */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '10px',
              borderTop: '1px solid #1e293b',
              paddingTop: '16px',
            }}
          >
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: '1px solid #334155',
                backgroundColor: 'transparent',
                color: '#94a3b8',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '0.85rem',
              }}
            >
              Close
            </button>

            <button
              type="button"
              onClick={() => {
                onClose();
                onRequestResources(incident.id);
              }}
              style={{
                padding: '8px 18px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#0284c7',
                color: '#ffffff',
                cursor: 'pointer',
                fontWeight: '700',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 0 12px rgba(2, 132, 199, 0.4)',
              }}
            >
              <span>📦</span> Request Resources for this Incident
            </button>
          </div>
        </div>
      </div>

      {/* Lightbox Preview Modal for Full-Resolution Image Inspection */}
      {selectedPhoto && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.92)',
            zIndex: 2000,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            style={{
              maxWidth: '90vw',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px',
                color: '#f8fafc',
              }}
            >
              <div>
                <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>{selectedPhoto.filename}</span>
                <span style={{ color: '#94a3b8', fontSize: '0.8rem', marginLeft: '8px' }}>
                  ({formatFileSize(selectedPhoto.file_size)})
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPhoto(null)}
                style={{
                  background: '#334155',
                  border: 'none',
                  color: '#ffffff',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                }}
              >
                ✕ Close
              </button>
            </div>

            <img
              src={`${apiUrl}/attachments/${selectedPhoto.id}/file`}
              alt={selectedPhoto.filename}
              style={{
                maxWidth: '100%',
                maxHeight: '75vh',
                objectFit: 'contain',
                borderRadius: '8px',
                border: '1px solid #334155',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.8)',
              }}
            />

            <div
              style={{
                marginTop: '10px',
                fontSize: '0.72rem',
                color: '#64748b',
                fontFamily: 'monospace',
                textAlign: 'center',
              }}
            >
              SHA-256: {selectedPhoto.sha256_hash}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
