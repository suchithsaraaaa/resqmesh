import React from 'react';

export interface MeshActivityItem {
  id: string;
  type: 'incident_created' | 'incident_merged' | 'resource_dispatched' | 'peer_joined' | 'sync_verified';
  title: string;
  detail: string;
  timestamp: string;
  icon: string;
  badgeColor: string;
  sourceNode?: string;
}

interface LiveNotificationStreamProps {
  items: MeshActivityItem[];
  onClear?: () => void;
}

export const LiveNotificationStream: React.FC<LiveNotificationStreamProps> = ({
  items,
  onClear,
}) => {
  return (
    <div
      style={{
        background: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        padding: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Stream Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #1e293b',
          paddingBottom: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 10px #10b981',
              animation: 'pulse 1.8s infinite',
            }}
          />
          <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#f8fafc', fontWeight: '700' }}>
            ⚡ Live Tactical Mesh Stream & Activity Feed
          </h3>
          <span
            style={{
              fontSize: '0.7rem',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              padding: '2px 8px',
              borderRadius: '10px',
              fontWeight: '600',
            }}
          >
            REAL-TIME P2P
          </span>
        </div>

        {items.length > 0 && onClear && (
          <button
            onClick={onClear}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#64748b',
              fontSize: '0.75rem',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Clear Feed
          </button>
        )}
      </div>

      {/* Stream Activity List */}
      <div
        style={{
          maxHeight: '260px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          paddingRight: '4px',
        }}
      >
        {items.length === 0 ? (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              color: '#64748b',
              fontSize: '0.85rem',
              fontStyle: 'italic',
            }}
          >
            Listening to mesh broadcast traffic... Events will stream live as peers interact.
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              style={{
                background: '#1e293b',
                borderLeft: `4px solid ${item.badgeColor}`,
                borderRadius: '6px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                animation: 'fadeIn 0.3s ease-in',
              }}
            >
              <div
                style={{
                  fontSize: '1.2rem',
                  lineHeight: '1',
                  marginTop: '2px',
                }}
              >
                {item.icon}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '3px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        color: item.badgeColor,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      {item.title}
                    </span>
                    {item.sourceNode && (
                      <span
                        style={{
                          fontSize: '0.7rem',
                          background: 'rgba(51, 65, 85, 0.6)',
                          color: '#94a3b8',
                          padding: '1px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        {item.sourceNode}
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                    {item.timestamp}
                  </span>
                </div>

                <div
                  style={{
                    fontSize: '0.82rem',
                    color: '#e2e8f0',
                    lineHeight: '1.35',
                    wordBreak: 'break-word',
                  }}
                >
                  {item.detail}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
