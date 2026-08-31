import React, { useState } from 'react';
import { ReviewIncidentModal } from './ReviewIncidentModal';

export interface PendingReportCluster {
  reportId: string;
  category: string;
  description: string;
  lat: number | null;
  lon: number | null;
  confidenceScore: number;
  targetIncidentId: string;
  targetIncidentTitle: string;
}

interface IncidentReviewCardProps {
  clusters: PendingReportCluster[];
  onApproveMerge: (reportId: string, incidentId: string) => void;
  onRejectAsNew: (reportId: string) => void;
}

export const IncidentReviewCard: React.FC<IncidentReviewCardProps> = ({
  clusters,
  onApproveMerge,
  onRejectAsNew,
}) => {
  const [reviewingCluster, setReviewingCluster] = useState<PendingReportCluster | null>(null);

  return (
    <div className="incident-review-card" style={{ background: '#0f172a', padding: '16px', borderRadius: '8px', color: '#fff', border: '1px solid #334155' }}>
      <h3 style={{ margin: '0 0 12px 0', color: '#f59e0b', fontSize: '0.95rem' }}>
        ⚠️ AI Duplicate Incident Correlation Review
      </h3>
      {clusters.length === 0 ? (
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No pending report correlation reviews.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {clusters.map((c) => (
            <div key={c.reportId} style={{ background: '#1e293b', padding: '12px', borderRadius: '6px', borderLeft: '4px solid #f59e0b' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', fontSize: '0.88rem' }}>
                  Candidate #{c.reportId.slice(0, 8)} ({c.category})
                </span>
                <span style={{ fontSize: '0.75rem', background: '#3b82f6', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontWeight: '700' }}>
                  {(c.confidenceScore * 100).toFixed(0)}% Match
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', margin: '4px 0 8px 0', lineHeight: '1.4' }}>
                "{c.description}"
              </p>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '10px' }}>
                Suggested Master: <strong style={{ color: '#38bdf8' }}>{c.targetIncidentTitle}</strong> (#{c.targetIncidentId.slice(0, 8)})
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => setReviewingCluster(c)}
                  style={{
                    background: '#0284c7',
                    color: '#fff',
                    border: 'none',
                    padding: '7px 14px',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontWeight: '700',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 0 8px rgba(2, 132, 199, 0.3)',
                  }}
                >
                  <span>🔍</span> Review Incident
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Full Incident Details & Correlation Review Pop-up Modal */}
      <ReviewIncidentModal
        cluster={reviewingCluster}
        isOpen={!!reviewingCluster}
        onClose={() => setReviewingCluster(null)}
        onMerge={onApproveMerge}
        onKeepSegregated={onRejectAsNew}
      />
    </div>
  );
};
