import React from 'react';

interface SyncStatusBarProps {
  nodeName: string;
  nodeRole: string;
  nodeId: string;
  peerCount: number;
  outboxPendingCount: number;
  syncStatus: string;
  onOpenPeers: () => void;
  onOpenConfig: () => void;
  onTriggerSync: () => void;
}

export const SyncStatusBar: React.FC<SyncStatusBarProps> = ({
  nodeName,
  nodeRole,
  nodeId,
  peerCount,
  outboxPendingCount,
  syncStatus,
  onOpenPeers,
  onOpenConfig,
  onTriggerSync,
}) => {
  const isCommander = nodeRole === 'commander';
  const hasPending = outboxPendingCount > 0;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '10px',
        padding: '12px 20px',
        marginBottom: '20px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
      }}
    >
      {/* Node Info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: isCommander ? '#0284c7' : '#059669',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
          }}
        >
          {isCommander ? '🎯' : '🚒'}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: '700', fontSize: '1rem', color: '#f8fafc' }}>
              {nodeName || 'Unnamed Laptop'}
            </span>
            <span
              style={{
                fontSize: '0.7rem',
                padding: '2px 8px',
                borderRadius: '10px',
                fontWeight: 'bold',
                background: isCommander ? 'rgba(56, 189, 248, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                color: isCommander ? '#38bdf8' : '#10b981',
                border: `1px solid ${isCommander ? '#0284c7' : '#059669'}`,
              }}
            >
              {nodeRole.toUpperCase()}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            ID: {nodeId ? nodeId.slice(0, 18) : 'Initializing...'}...
          </div>
        </div>
      </div>

      {/* Network & Sync Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Peer Discovery Badge */}
        <button
          onClick={onOpenPeers}
          style={{
            background: peerCount > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${peerCount > 0 ? '#10b981' : '#f59e0b'}`,
            color: peerCount > 0 ? '#6ee7b7' : '#fcd34d',
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '0.82rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: peerCount > 0 ? '#10b981' : '#f59e0b',
            }}
          />
          {peerCount > 0 ? `${peerCount} Peers Connected [LAN]` : 'Searching for Peers...'}
        </button>

        {/* Store & Forward Outbox Badge */}
        <div
          style={{
            background: hasPending ? 'rgba(245, 158, 11, 0.12)' : 'rgba(16, 185, 129, 0.12)',
            border: `1px solid ${hasPending ? '#f59e0b' : '#10b981'}`,
            color: hasPending ? '#fbbf24' : '#34d399',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>{hasPending ? '⏳' : '✓'}</span>
          <span>{hasPending ? `${outboxPendingCount} Outbox Pending` : 'All Outbox ACKed'}</span>
        </div>

        {/* Quick Sync Button */}
        <button
          onClick={onTriggerSync}
          title="Force immediate delta sync exchange with active peers"
          style={{
            background: '#1e293b',
            border: '1px solid #334155',
            color: '#94a3b8',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '0.8rem',
            cursor: 'pointer',
          }}
        >
          🔄 Sync
        </button>

        {/* Settings / Config Button */}
        <button
          onClick={onOpenConfig}
          title="Edit node role or friendly name"
          style={{
            background: '#1e293b',
            border: '1px solid #334155',
            color: '#94a3b8',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '0.8rem',
            cursor: 'pointer',
          }}
        >
          ⚙️ Node Config
        </button>
      </div>
    </div>
  );
};
