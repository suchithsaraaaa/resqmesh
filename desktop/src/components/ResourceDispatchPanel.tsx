import React, { useState } from 'react';

export interface ResourceRequestItem {
  id: string;
  resourceType: string;
  quantity: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'dispatched' | 'fulfilled';
  requestedBy: string;
  incidentId?: string;
  incidentTitle?: string;
}

interface ResourceDispatchPanelProps {
  resources: ResourceRequestItem[];
  onDispatch: (id: string) => void;
  onRescind?: (id: string) => void;
  onOpenRequestModal?: () => void;
  nodeRole?: string;
}

export const ResourceDispatchPanel: React.FC<ResourceDispatchPanelProps> = ({
  resources,
  onDispatch,
  onRescind,
  onOpenRequestModal,
  nodeRole = 'responder',
}) => {
  const [filter, setFilter] = useState<'all' | 'pending'>('pending');

  const filtered = resources.filter((r) => (filter === 'pending' ? r.status === 'pending' : true));
  const isCommander = nodeRole.toLowerCase() === 'commander';

  return (
    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '8px', color: '#fff', border: '1px solid #334155' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '0.95rem' }}>
          {isCommander ? '🚑 Resource Dispatch (Commander)' : '📦 Resource Requests (Responder)'}
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {onOpenRequestModal && (
            <button
              onClick={onOpenRequestModal}
              style={{
                background: '#0284c7',
                color: '#fff',
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
              <span>+</span> Request
            </button>
          )}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #475569', borderRadius: '4px', padding: '4px 8px', fontSize: '0.75rem' }}
          >
            <option value="pending">Pending</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {filtered.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: '0.8rem', fontStyle: 'italic', padding: '8px 0' }}>
            No active resource requests.
          </div>
        ) : (
          filtered.map((r) => (
            <div key={r.id} style={{ background: '#1e293b', padding: '10px 12px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                  {r.quantity}x {r.resourceType.toUpperCase()}
                </div>
                {r.incidentTitle && (
                  <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>🎯 Tied Incident:</span>
                    <strong>{r.incidentTitle}</strong>
                  </div>
                )}
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  Requested by: {r.requestedBy} | Urgency: <span style={{ color: r.urgency === 'critical' ? '#ef4444' : '#f59e0b' }}>{r.urgency.toUpperCase()}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {r.status === 'pending' ? (
                  <>
                    {isCommander ? (
                      <button
                        onClick={() => onDispatch(r.id)}
                        style={{
                          background: '#10b981',
                          color: '#fff',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontSize: '0.8rem',
                        }}
                      >
                        Dispatch
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: '600' }}>
                        ⏳ Pending Command
                      </span>
                    )}

                    {onRescind && (
                      <button
                        onClick={() => onRescind(r.id)}
                        style={{
                          background: 'transparent',
                          color: '#ef4444',
                          border: '1px solid #ef4444',
                          padding: '5px 10px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontWeight: '600',
                          fontSize: '0.75rem',
                        }}
                        title="Rescind this resource request"
                      >
                        ✕ Rescind
                      </button>
                    )}
                  </>
                ) : (
                  <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 'bold' }}>✓ DISPATCHED</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
