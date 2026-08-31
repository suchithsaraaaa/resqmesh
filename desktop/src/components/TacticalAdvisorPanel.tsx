import React, { useState } from 'react';

interface TacticalAdvisorProps {
  apiUrl: string;
}

export const TacticalAdvisorPanel: React.FC<TacticalAdvisorProps> = ({ apiUrl }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sops, setSops] = useState<any[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAnswer(null);
    setSops([]);

    try {
      const res = await fetch(`${apiUrl}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setAnswer(data.recommendation || data.recommendations);
        setSops(data.retrieved_sops || []);
      }
    } catch {
      setAnswer('Unable to connect to local offline AI advisor.');
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'What should we do after an earthquake?',
    'Priorities during flood evacuation?',
    'Building collapse entry checklist',
    'Warning signs of dangerous heat stroke',
    'Chemical chlorine gas leak containment',
    'Mass casualty START triage protocol',
  ];

  return (
    <div
      style={{
        background: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '10px',
        padding: '20px',
        color: '#f8fafc',
        minHeight: '340px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.4rem' }}>🧠</span>
          <div>
            <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '800', color: '#38bdf8' }}>
              On-Device Tactical Advisor (Offline RAG)
            </h4>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Local Vector Search & Emergency SOP Retrieval (Zero Cloud Dependency)
            </span>
          </div>
        </div>
        <span
          style={{
            fontSize: '0.72rem',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            color: '#10b981',
            padding: '3px 8px',
            borderRadius: '12px',
            fontWeight: '700',
            border: '1px solid rgba(16, 185, 129, 0.3)',
          }}
        >
          ● OFFLINE READY
        </span>
      </div>

      {/* Query Search Form */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask disaster protocol SOP (e.g. severe bleeding, gas leak, building collapse)..."
          style={{
            flex: 1,
            padding: '10px 14px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#f8fafc',
            fontSize: '0.88rem',
            outline: 'none',
            boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)',
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            background: '#0284c7',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '700',
            fontSize: '0.88rem',
            cursor: loading ? 'wait' : 'pointer',
            boxShadow: '0 0 10px rgba(2, 132, 199, 0.3)',
          }}
        >
          {loading ? 'Analyzing...' : 'Query'}
        </button>
      </form>

      {/* Sample Quick Query Chips */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
        {sampleQueries.map((q) => (
          <button
            key={q}
            onClick={() => {
              setQuery(q);
            }}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#94a3b8',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Expanded RAG Information & Result Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {answer ? (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '8px',
              padding: '16px',
              fontSize: '0.9rem',
              lineHeight: '1.55',
              minHeight: '200px',
              maxHeight: '340px',
              overflowY: 'auto',
              boxShadow: 'inset 0 0 15px rgba(2, 6, 23, 0.5)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ fontWeight: '800', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.95rem' }}>
                <span>⚡</span> Tactical Guidance & Field Action Protocol:
              </div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Query: "{query}"
              </span>
            </div>

            <div style={{ whiteSpace: 'pre-line', color: '#f1f5f9', marginBottom: '14px' }}>
              {answer}
            </div>

            {sops.length > 0 && (
              <div style={{ marginTop: '14px', borderTop: '1px solid #334155', paddingTop: '10px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#38bdf8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>📚</span> Verified Authoritative SOP Sources & Field Citations:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {sops.map((s, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: '#1e293b',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        color: '#cbd5e1',
                        borderLeft: '4px solid #0ea5e9',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '2px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: '#f1f5f9', fontSize: '0.78rem' }}>{s.title}</strong>
                        <span
                          style={{
                            background: 'rgba(14, 165, 233, 0.2)',
                            color: '#38bdf8',
                            fontSize: '0.68rem',
                            fontWeight: '700',
                            padding: '1px 6px',
                            borderRadius: '4px',
                          }}
                        >
                          {s.organization || 'NDMA'}
                        </span>
                      </div>
                      {s.section && (
                        <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>
                          <strong>Section:</strong> {s.section} {s.page ? `| Page ${s.page}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              background: 'rgba(30, 41, 59, 0.4)',
              border: '1px dashed #334155',
              borderRadius: '8px',
              padding: '16px',
              minHeight: '180px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              color: '#94a3b8',
              fontSize: '0.82rem',
            }}
          >
            <div style={{ fontWeight: '700', color: '#cbd5e1', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>🛡️</span> On-Device Emergency SOP Knowledge Base
            </div>
            <div style={{ lineHeight: '1.5', marginBottom: '10px' }}>
              The Tactical Advisor runs fully on-device using quantized local embeddings to provide immediate clinical and disaster management SOP guidance when cellular and satellite networks are down.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.76rem' }}>
              <div style={{ background: '#1e293b', padding: '6px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                🩸 <strong>Trauma & Mass Casualty</strong>: Tourniquets, START Triage, airway management
              </div>
              <div style={{ background: '#1e293b', padding: '6px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                ☣️ <strong>Hazmat & Chem Decon</strong>: Chlorine leaks, radiation, isolation perimeters
              </div>
              <div style={{ background: '#1e293b', padding: '6px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                🔥 <strong>Structural & Wildfire</strong>: Evacuation zones, foam suppression, ICS command
              </div>
              <div style={{ background: '#1e293b', padding: '6px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                🌊 <strong>Flood & Water Rescue</strong>: Inflatable boat staging, swift water protocols
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
