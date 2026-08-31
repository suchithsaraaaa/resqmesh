import React from 'react';
import { PendingReportCluster } from './IncidentReviewCard';

interface ReviewIncidentModalProps {
  cluster: PendingReportCluster | null;
  isOpen: boolean;
  onClose: () => void;
  onMerge: (reportId: string, incidentId: string) => void;
  onKeepSegregated: (reportId: string) => void;
}

export const ReviewIncidentModal: React.FC<ReviewIncidentModalProps> = ({
  cluster,
  isOpen,
  onClose,
  onMerge,
  onKeepSegregated,
}) => {
  if (!isOpen || !cluster) return null;

  const matchPercent = (cluster.confidenceScore * 100).toFixed(0);

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
        zIndex: 1050,
      }}
    >
      <div
        style={{
          backgroundColor: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '24px',
          width: '100%',
          maxWidth: '650px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          color: '#f8fafc',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '16px',
            borderBottom: '1px solid #1e293b',
            paddingBottom: '12px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '1.4rem' }}>🔍</span>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.3px', color: '#f8fafc' }}>
                AI Incident Correlation Review
              </h2>
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8' }}>
              Screening comparison between incoming duplicate broadcast and existing master incident
            </p>
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

        {/* AI Match Confidence Score Pill */}
        <div
          style={{
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '8px',
            padding: '10px 14px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>⚡</span>
            <div>
              <div style={{ fontWeight: '800', color: '#f59e0b', fontSize: '0.88rem' }}>
                AI Similarity Match: {matchPercent}% Multi-Factor Correlation
              </div>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                Spatial proximity, categorical match, and semantic text overlap indicate potential duplicate sighting.
              </div>
            </div>
          </div>
          <span
            style={{
              backgroundColor: '#f59e0b',
              color: '#0f172a',
              fontWeight: '800',
              fontSize: '0.75rem',
              padding: '4px 8px',
              borderRadius: '4px',
              textTransform: 'uppercase',
            }}
          >
            {matchPercent}% Match
          </span>
        </div>

        {/* Side-by-Side Comparison Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '14px',
            marginBottom: '18px',
          }}
        >
          {/* Incoming Candidate Incident Card */}
          <div
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#f59e0b', textTransform: 'uppercase' }}>
                Incoming Duplicate Candidate
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  backgroundColor: '#334155',
                  color: '#94a3b8',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}
              >
                #{cluster.reportId.slice(0, 8)}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Category:</span>
              <span style={{ fontWeight: '700', fontSize: '0.85rem', color: '#38bdf8', textTransform: 'capitalize' }}>
                {cluster.category}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Reported Coordinates:</span>
              <span style={{ fontSize: '0.82rem', fontFamily: 'monospace', color: '#cbd5e1' }}>
                {cluster.lat !== null && cluster.lon !== null
                  ? `📍 ${cluster.lat.toFixed(4)}, ${cluster.lon.toFixed(4)}`
                  : '📍 Location: Unavailable'}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Observation Narrative:</span>
              <div
                style={{
                  background: '#0f172a',
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  color: '#e2e8f0',
                  lineHeight: '1.4',
                  maxHeight: '70px',
                  overflowY: 'auto',
                }}
              >
                "{cluster.description}"
              </div>
            </div>
          </div>

          {/* Master Incident Card */}
          <div
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #0284c7',
              borderRadius: '8px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#38bdf8', textTransform: 'uppercase' }}>
                Target Master Incident
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  backgroundColor: '#0369a1',
                  color: '#ffffff',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}
              >
                #{cluster.targetIncidentId.slice(0, 8)}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Master Incident Title:</span>
              <span style={{ fontWeight: '800', fontSize: '0.9rem', color: '#f8fafc' }}>
                {cluster.targetIncidentTitle}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Consolidation Status:</span>
              <span style={{ fontSize: '0.82rem', color: '#10b981', fontWeight: '600' }}>
                Active Command Incident
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>Merge Impact:</span>
              <div
                style={{
                  background: '#0f172a',
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  color: '#94a3b8',
                  lineHeight: '1.4',
                }}
              >
                Approving will link this observation into "{cluster.targetIncidentTitle}", transfer tied resources, and update the master report count.
              </div>
            </div>
          </div>
        </div>

        {/* Action Decision Footer */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
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
            Cancel
          </button>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={() => {
                onKeepSegregated(cluster.reportId);
                onClose();
              }}
              style={{
                padding: '9px 18px',
                borderRadius: '6px',
                border: '1px solid #64748b',
                backgroundColor: '#334155',
                color: '#f8fafc',
                cursor: 'pointer',
                fontWeight: '700',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
              title="Keep this incident separate as an independent operational event"
            >
              <span>🛡️</span> Keep Segregated
            </button>

            <button
              type="button"
              onClick={() => {
                onMerge(cluster.reportId, cluster.targetIncidentId);
                onClose();
              }}
              style={{
                padding: '9px 20px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#10b981',
                color: '#ffffff',
                cursor: 'pointer',
                fontWeight: '800',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 0 12px rgba(16, 185, 129, 0.4)',
              }}
              title="Consolidate duplicate incident into master incident"
            >
              <span>🔗</span> Merge
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
