import React, { useState, useEffect, useRef } from 'react';
import { colors, radii, shadows, fonts } from '../styles/designTokens';
import { IncidentMergeAiEngine, DuplicateCandidate, ScanStatus } from '../services/IncidentMergeAiEngine';

interface IncidentMergeAiCardProps {
  incidents: any[];
  onMerge: (primaryId: string, duplicateId: string) => Promise<void>;
  nodeName?: string;
}

export const IncidentMergeAiCard: React.FC<IncidentMergeAiCardProps> = ({
  incidents,
  onMerge,
  nodeName = 'Commander',
}) => {
  const [candidates, setCandidates] = useState<DuplicateCandidate[]>([]);
  const [scanStatus, setScanStatus] = useState<ScanStatus>({
    isScanning: false,
    totalAnalyzed: 0,
    potentialMatchesCount: 0,
    lastScanTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  });
  const [reviewCandidate, setReviewCandidate] = useState<DuplicateCandidate | null>(null);
  const [isMerging, setIsMerging] = useState(false);
  const scanTimerRef = useRef<any>(null);

  // Active continuous scanning with debouncing
  useEffect(() => {
    const runScan = () => {
      const result = IncidentMergeAiEngine.scanIncidents(incidents);
      setCandidates(result.candidates);
      setScanStatus(result.status);
    };

    // Initial immediate scan
    runScan();

    // Periodic automatic background scan every 12 seconds
    scanTimerRef.current = setInterval(runScan, 12000);

    return () => {
      if (scanTimerRef.current) clearInterval(scanTimerRef.current);
    };
  }, [incidents]);

  const handleDismiss = (candidate: DuplicateCandidate) => {
    IncidentMergeAiEngine.dismissCandidate(candidate.id, nodeName);
    setCandidates((prev) => prev.filter((c) => c.id !== candidate.id));
    if (reviewCandidate?.id === candidate.id) {
      setReviewCandidate(null);
    }
  };

  const handleConfirmMerge = async (candidate: DuplicateCandidate) => {
    setIsMerging(true);
    try {
      const pId = candidate.primaryIncident.id || (candidate.primaryIncident as any).incident_id;
      const dId = candidate.duplicateIncident.id || (candidate.duplicateIncident as any).incident_id;
      await onMerge(pId, dId);
      handleDismiss(candidate);
      setReviewCandidate(null);
    } catch (err) {
      console.error('[IncidentMergeAi] Merge failed:', err);
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <>
      <div
        style={{
          background: colors.bgSurface,
          border: `1px solid ${candidates.length > 0 ? 'rgba(234, 179, 8, 0.4)' : colors.borderSubtle}`,
          borderRadius: radii.xl,
          padding: '16px 18px',
          boxShadow: shadows.card,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          fontFamily: fonts.body,
        }}
      >
        {/* Panel Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1rem' }}>🧠</span>
              <span
                style={{
                  color: colors.textPrimary,
                  fontSize: '0.86rem',
                  fontWeight: '800',
                  letterSpacing: '0.04em',
                }}
              >
                INCIDENT MERGE AI
              </span>
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.72rem', marginTop: '2px' }}>
              Active Multi-Signal Incident Correlation
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: radii.full,
              padding: '3px 9px',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 8px #10b981',
                animation: 'pulse 2s infinite',
              }}
            />
            <span style={{ color: '#10b981', fontSize: '0.68rem', fontWeight: '700', letterSpacing: '0.04em' }}>
              SCANNING
            </span>
          </div>
        </div>

        {/* Scan Status Telemetry */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.7rem',
            color: colors.textMuted,
            borderBottom: `1px solid ${colors.borderSubtle}`,
            paddingBottom: '8px',
          }}
        >
          <span>{scanStatus.totalAnalyzed} incidents analyzed</span>
          <span>{candidates.length} potential {candidates.length === 1 ? 'match' : 'matches'}</span>
          <span>Last scan: {scanStatus.lastScanTime}</span>
        </div>

        {/* Candidates Content */}
        {candidates.length === 0 ? (
          <div
            style={{
              padding: '12px 14px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: `1px dashed ${colors.borderSubtle}`,
              borderRadius: radii.lg,
              color: colors.textMuted,
              fontSize: '0.75rem',
              textAlign: 'center',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <span style={{ color: '#10b981' }}>✓</span>
            <span>All active incidents distinct. Continuous correlation running.</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {candidates.slice(0, 2).map((cand) => {
              const p = cand.primaryIncident;
              const d = cand.duplicateIncident;
              const pId = (p.id || (p as any).incident_id || '').slice(0, 8);
              const dId = (d.id || (d as any).incident_id || '').slice(0, 8);

              return (
                <div
                  key={cand.id}
                  style={{
                    background: 'rgba(234, 179, 8, 0.05)',
                    border: '1px solid rgba(234, 179, 8, 0.3)',
                    borderRadius: radii.lg,
                    padding: '12px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  {/* Warning and Score badge */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span
                      style={{
                        color: '#eab308',
                        fontSize: '0.72rem',
                        fontWeight: '800',
                        letterSpacing: '0.04em',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      ⚠ POTENTIAL DUPLICATE
                    </span>
                    <span
                      style={{
                        background: cand.similarity >= 85 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                        border: `1px solid ${cand.similarity >= 85 ? '#ef4444' : '#eab308'}`,
                        color: cand.similarity >= 85 ? '#f87171' : '#fde047',
                        borderRadius: radii.sm,
                        padding: '2px 7px',
                        fontSize: '0.7rem',
                        fontWeight: '800',
                      }}
                    >
                      {cand.similarity}% SIMILAR
                    </span>
                  </div>

                  {/* Incident Pair Comparison */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: colors.accent, fontSize: '0.7rem', fontWeight: '700' }}>
                        #{pId}
                      </span>
                      <span
                        style={{
                          color: colors.textPrimary,
                          fontSize: '0.78rem',
                          fontWeight: '600',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {p.title}
                      </span>
                    </div>

                    <div style={{ textAlign: 'center', color: colors.textMuted, fontSize: '0.75rem', lineHeight: '1' }}>
                      ↕
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: colors.accent, fontSize: '0.7rem', fontWeight: '700' }}>
                        #{dId}
                      </span>
                      <span
                        style={{
                          color: colors.textPrimary,
                          fontSize: '0.78rem',
                          fontWeight: '600',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {d.title}
                      </span>
                    </div>
                  </div>

                  {/* Telemetry diff */}
                  <div
                    style={{
                      display: 'flex',
                      gap: '12px',
                      color: colors.textMuted,
                      fontSize: '0.7rem',
                      background: 'rgba(0, 0, 0, 0.2)',
                      padding: '4px 8px',
                      borderRadius: radii.sm,
                    }}
                  >
                    {cand.distanceMeters !== null && (
                      <span>📍 Distance: <strong>{cand.distanceMeters} m</strong></span>
                    )}
                    <span>⏱️ Time diff: <strong>{cand.timeDiffMinutes} min</strong></span>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                    <button
                      onClick={() => setReviewCandidate(cand)}
                      style={{
                        flex: 1,
                        background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: radii.md,
                        padding: '6px 12px',
                        fontSize: '0.74rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                      }}
                    >
                      <span>🔍</span> Review
                    </button>
                    <button
                      onClick={() => handleDismiss(cand)}
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: `1px solid ${colors.borderSubtle}`,
                        color: colors.textMuted,
                        borderRadius: radii.md,
                        padding: '6px 12px',
                        fontSize: '0.74rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                      }}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Side-by-Side Merge Review Modal */}
      {reviewCandidate && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            background: 'rgba(2, 6, 23, 0.82)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            fontFamily: fonts.body,
          }}
        >
          <div
            style={{
              background: colors.bgSurface,
              border: `1px solid ${colors.borderSubtle}`,
              borderRadius: radii.xl,
              width: '100%',
              maxWidth: '680px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: shadows.elevated,
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '16px 20px',
                borderBottom: `1px solid ${colors.borderSubtle}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ color: colors.textPrimary, fontSize: '0.96rem', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🧠</span> INCIDENT CORRELATION & MERGE REVIEW
                </div>
                <div style={{ color: colors.textMuted, fontSize: '0.75rem', marginTop: '2px' }}>
                  Compare candidate duplicates and confirm consolidation into master incident
                </div>
              </div>
              <button
                onClick={() => setReviewCandidate(null)}
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

            {/* Modal Body */}
            <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Similarity Summary Banner */}
              <div
                style={{
                  background: 'rgba(234, 179, 8, 0.08)',
                  border: '1px solid rgba(234, 179, 8, 0.3)',
                  borderRadius: radii.lg,
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ color: '#eab308', fontSize: '0.88rem', fontWeight: '800' }}>
                    {reviewCandidate.similarity}% CORRELATION CONFIDENCE
                  </div>
                  <div style={{ color: colors.textMuted, fontSize: '0.74rem', marginTop: '2px' }}>
                    Identified via multi-signal geographic, temporal, and lexical evaluation
                  </div>
                </div>
                <span
                  style={{
                    background: '#eab308',
                    color: '#000',
                    fontWeight: '900',
                    fontSize: '0.74rem',
                    padding: '4px 10px',
                    borderRadius: radii.sm,
                  }}
                >
                  {reviewCandidate.confidenceLevel} CONFIDENCE
                </span>
              </div>

              {/* Side-by-Side Comparison */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                {/* Primary Report */}
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${colors.borderSubtle}`,
                    borderRadius: radii.lg,
                    padding: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: colors.accent, fontSize: '0.75rem', fontWeight: '800' }}>
                      PRIMARY INCIDENT
                    </span>
                    <span style={{ color: colors.textMuted, fontSize: '0.7rem' }}>
                      #{(reviewCandidate.primaryIncident.id || '').slice(0, 8)}
                    </span>
                  </div>
                  <div style={{ color: colors.textPrimary, fontSize: '0.88rem', fontWeight: '700' }}>
                    {reviewCandidate.primaryIncident.title}
                  </div>
                  <div style={{ color: colors.textMuted, fontSize: '0.76rem', lineHeight: '1.4' }}>
                    {reviewCandidate.primaryIncident.description || reviewCandidate.primaryIncident.summary || 'No narrative provided.'}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: colors.textMuted, display: 'flex', flexDirection: 'column', gap: '4px', borderTop: `1px solid ${colors.borderSubtle}`, paddingTop: '8px' }}>
                    <div><strong>Category:</strong> {reviewCandidate.primaryIncident.category || 'General'}</div>
                    <div><strong>Severity:</strong> {(reviewCandidate.primaryIncident.severity || 'Medium').toUpperCase()}</div>
                    <div>
                      <strong>Location:</strong>{' '}
                      {reviewCandidate.primaryIncident.lat !== null && reviewCandidate.primaryIncident.lon !== null
                        ? `${reviewCandidate.primaryIncident.lat?.toFixed(5)}, ${reviewCandidate.primaryIncident.lon?.toFixed(5)}`
                        : reviewCandidate.primaryIncident.manualLocation?.address || 'Manual Text'}
                    </div>
                    <div><strong>Broadcaster:</strong> {reviewCandidate.primaryIncident.broadcasterName || 'Sector Responder'}</div>
                  </div>
                </div>

                {/* Duplicate Report */}
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${colors.borderSubtle}`,
                    borderRadius: radii.lg,
                    padding: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#f59e0b', fontSize: '0.75rem', fontWeight: '800' }}>
                      CANDIDATE REPORT
                    </span>
                    <span style={{ color: colors.textMuted, fontSize: '0.7rem' }}>
                      #{(reviewCandidate.duplicateIncident.id || '').slice(0, 8)}
                    </span>
                  </div>
                  <div style={{ color: colors.textPrimary, fontSize: '0.88rem', fontWeight: '700' }}>
                    {reviewCandidate.duplicateIncident.title}
                  </div>
                  <div style={{ color: colors.textMuted, fontSize: '0.76rem', lineHeight: '1.4' }}>
                    {reviewCandidate.duplicateIncident.description || reviewCandidate.duplicateIncident.summary || 'No narrative provided.'}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: colors.textMuted, display: 'flex', flexDirection: 'column', gap: '4px', borderTop: `1px solid ${colors.borderSubtle}`, paddingTop: '8px' }}>
                    <div><strong>Category:</strong> {reviewCandidate.duplicateIncident.category || 'General'}</div>
                    <div><strong>Severity:</strong> {(reviewCandidate.duplicateIncident.severity || 'Medium').toUpperCase()}</div>
                    <div>
                      <strong>Location:</strong>{' '}
                      {reviewCandidate.duplicateIncident.lat !== null && reviewCandidate.duplicateIncident.lon !== null
                        ? `${reviewCandidate.duplicateIncident.lat?.toFixed(5)}, ${reviewCandidate.duplicateIncident.lon?.toFixed(5)}`
                        : reviewCandidate.duplicateIncident.manualLocation?.address || 'Manual Text'}
                    </div>
                    <div><strong>Broadcaster:</strong> {reviewCandidate.duplicateIncident.broadcasterName || 'Peer Node'}</div>
                  </div>
                </div>
              </div>

              {/* Correlation Reasons */}
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${colors.borderSubtle}`,
                  borderRadius: radii.lg,
                  padding: '12px 14px',
                }}
              >
                <div style={{ color: colors.textPrimary, fontSize: '0.78rem', fontWeight: '700', marginBottom: '6px' }}>
                  Correlation Signals:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {reviewCandidate.reasons.map((r, i) => (
                    <div key={i} style={{ color: '#10b981', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>✓</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div
              style={{
                padding: '14px 20px',
                borderTop: `1px solid ${colors.borderSubtle}`,
                background: 'rgba(0, 0, 0, 0.2)',
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '10px',
              }}
            >
              <button
                onClick={() => handleDismiss(reviewCandidate)}
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: `1px solid ${colors.borderSubtle}`,
                  color: colors.textMuted,
                  borderRadius: radii.md,
                  padding: '8px 14px',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                ✕ Dismiss Match
              </button>
              <button
                onClick={() => handleDismiss(reviewCandidate)}
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: `1px solid ${colors.borderSubtle}`,
                  color: colors.textPrimary,
                  borderRadius: radii.md,
                  padding: '8px 14px',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                🛡️ Keep Separate
              </button>
              <button
                disabled={isMerging}
                onClick={() => handleConfirmMerge(reviewCandidate)}
                style={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: radii.md,
                  padding: '8px 18px',
                  fontSize: '0.78rem',
                  fontWeight: '700',
                  cursor: isMerging ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {isMerging ? 'Merging...' : '🔗 Merge Incidents'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
