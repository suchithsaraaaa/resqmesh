import React, { useState } from 'react';
import { colors, radii, shadows, fonts } from '../styles/designTokens';
import { TacticalEventBus } from '../services/TacticalEventBus';

interface OnDeviceAdvisorCardProps {
  apiUrl: string;
}

export const OnDeviceAdvisorCard: React.FC<OnDeviceAdvisorCardProps> = ({ apiUrl }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null);
  const [response, setResponse] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<string>('High');
  const [error, setError] = useState<string | null>(null);

  const quickQueries = [
    'What should we do after an earthquake?',
    'Severe bleeding protocol',
    'Flood evacuation priorities',
    'Building collapse checklist',
    'Chemical leak response',
    'START triage protocol',
  ];

  const handleAsk = async (questionToAsk?: string) => {
    const q = (questionToAsk || query).trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setSubmittedQuery(q);

    TacticalEventBus.publish({
      type: 'AI_QUERY',
      severity: 'INFO',
      actor: 'Commander Query',
      title: `AI Advisor Query: "${q}"`,
      description: `Consulting on-device emergency SOP vector index for: ${q}`,
    });

    try {
      const res = await fetch(`${apiUrl}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (res.ok) {
        const data = await res.json();
        const rec = data.recommendation || data.recommendations || 'Verified guidance retrieved.';
        setResponse(rec);
        const conf = data.retrieved_sops && data.retrieved_sops.length > 0 ? 'High' : 'Medium';
        setConfidence(conf);
        TacticalEventBus.publish({
          type: 'AI_RESPONSE',
          severity: 'SYNC',
          actor: 'Tactical Advisor',
          title: `SOP Guidance: "${q}"`,
          description: rec.length > 120 ? rec.slice(0, 120) + '...' : rec,
          metadata: { confidence: conf },
        });
      } else {
        setError('Local RAG query failed.');
      }
    } catch {
      setError('Unable to reach local offline AI advisor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: colors.bgSurface,
        border: `1px solid ${colors.borderSubtle}`,
        borderRadius: radii.xl,
        padding: '18px 20px',
        boxShadow: shadows.card,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.05rem' }}>🧠</span>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: colors.textPrimary }}>
              On-Device AI Advisor
            </h4>
          </div>
          <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginTop: '2px' }}>
            Emergency SOP & Tactical Knowledge
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: radii.full,
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              letterSpacing: '0.04em',
            }}
          >
            ● OFFLINE READY
          </span>
          <span style={{ fontSize: '0.62rem', color: colors.textMuted, letterSpacing: '0.05em' }}>
            LOCAL RAG • 100% ON-DEVICE
          </span>
        </div>
      </div>

      {/* Search Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk();
        }}
        style={{ display: 'flex', gap: '8px' }}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about an emergency protocol..."
          style={{
            flex: 1,
            background: colors.bgApp,
            border: `1px solid ${colors.borderSubtle}`,
            borderRadius: radii.md,
            padding: '8px 12px',
            color: colors.textPrimary,
            fontSize: '0.82rem',
            fontFamily: fonts.sans,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          style={{
            background: loading || !query.trim() ? colors.bgElevated : colors.accentElectric,
            color: loading || !query.trim() ? colors.textMuted : '#070b14',
            border: 'none',
            borderRadius: radii.md,
            padding: '8px 14px',
            fontSize: '0.80rem',
            fontWeight: 700,
            cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          {loading ? 'Thinking...' : 'Ask AI'}
        </button>
      </form>

      {/* Quick Query Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        {quickQueries.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              setQuery(chip);
              handleAsk(chip);
            }}
            style={{
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: radii.full,
              color: colors.accentElectric,
              padding: '3px 9px',
              fontSize: '0.70rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.16)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)')}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Response Area */}
      {submittedQuery && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.65)',
            border: `1px solid ${colors.borderSubtle}`,
            borderRadius: radii.lg,
            padding: '12px 14px',
            fontSize: '0.80rem',
            color: colors.textSecondary,
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            maxHeight: '220px',
            overflowY: 'auto',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: colors.accentElectric }}>
              Query: "{submittedQuery}"
            </span>
            <span
              style={{
                fontSize: '0.68rem',
                color: '#34d399',
                background: 'rgba(16, 185, 129, 0.12)',
                padding: '1px 6px',
                borderRadius: radii.sm,
                fontWeight: 700,
              }}
            >
              Confidence: {confidence}
            </span>
          </div>

          <div style={{ height: '1px', background: colors.borderSubtle }} />

          {loading ? (
            <div style={{ color: colors.textMuted, fontStyle: 'italic', padding: '6px 0' }}>
              Querying on-device emergency SOP vector index...
            </div>
          ) : error ? (
            <div style={{ color: colors.critical }}>{error}</div>
          ) : (
            <>
              <div
                style={{
                  color: colors.textPrimary,
                  lineHeight: 1.5,
                  fontSize: '0.80rem',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {response}
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.68rem',
                  color: colors.textMuted,
                  paddingTop: '4px',
                  borderTop: `1px dashed ${colors.borderSubtle}`,
                }}
              >
                <span>Source: Local Emergency SOP Knowledge Base</span>
                <span style={{ color: colors.textSecondary }}>100% Offline RAG</span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
