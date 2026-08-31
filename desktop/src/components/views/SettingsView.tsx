import React from 'react';
import { colors, radii, shadows, fonts } from '../../styles/designTokens';

interface SettingsViewProps {
  nodeId: string;
  nodeName: string;
  nodeRole: string;
  apiPort: number;
  peerCount: number;
  syncStatus: string;
  onOpenConfigModal: () => void;
  onTriggerSync: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  nodeId,
  nodeName,
  nodeRole,
  apiPort,
  peerCount,
  syncStatus,
  onOpenConfigModal,
  onTriggerSync,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '800px' }}>
      <div
        style={{
          background: colors.bgSurface,
          padding: '16px 20px',
          borderRadius: radii.lg,
          border: `1px solid ${colors.borderSubtle}`,
          boxShadow: shadows.card,
        }}
      >
        <h3 style={{ margin: 0, color: colors.textPrimary, fontSize: '1rem', fontWeight: '800' }}>
          Node Operational Configuration & Mesh Parameters
        </h3>
        <p style={{ margin: 0, color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
          Manage local command identity, cryptographic node identifier, peer connectivity, and local storage.
        </p>
      </div>

      <div
        style={{
          background: colors.bgSurface,
          borderRadius: radii.xl,
          border: `1px solid ${colors.borderSubtle}`,
          padding: '24px',
          boxShadow: shadows.elevated,
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ color: colors.textPrimary, fontSize: '0.92rem', fontWeight: '700' }}>
              Command Node Identity
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
              Name: <strong style={{ color: colors.textPrimary }}>{nodeName || 'Unnamed Node'}</strong> • Role:{' '}
              <strong style={{ color: colors.accentElectric, textTransform: 'capitalize' }}>{nodeRole}</strong>
            </div>
          </div>
          <button
            type="button"
            onClick={onOpenConfigModal}
            style={{
              background: 'rgba(56, 189, 248, 0.12)',
              border: `1px solid ${colors.accentElectric}`,
              color: colors.accentElectric,
              padding: '7px 16px',
              borderRadius: radii.sm,
              fontSize: '0.78rem',
              fontWeight: '700',
              cursor: 'pointer',
            }}
          >
            Edit Profile
          </button>
        </div>

        <hr style={{ border: 'none', borderTop: `1px solid ${colors.borderSubtle}`, margin: 0 }} />

        <div>
          <div style={{ color: colors.textMuted, fontSize: '0.74rem', textTransform: 'uppercase' }}>
            Cryptographic Node ID
          </div>
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: '0.84rem',
              color: colors.textSecondary,
              padding: '8px 12px',
              borderRadius: radii.sm,
              background: 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${colors.borderSubtle}`,
              marginTop: '6px',
              userSelect: 'all',
            }}
          >
            {nodeId || 'Generating...'}
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: `1px solid ${colors.borderSubtle}`, margin: 0 }} />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <div style={{ color: colors.textMuted, fontSize: '0.74rem', textTransform: 'uppercase' }}>
              Backend Daemon Port
            </div>
            <div
              style={{
                fontFamily: fonts.mono,
                fontSize: '0.84rem',
                color: colors.textPrimary,
                padding: '8px 12px',
                borderRadius: radii.sm,
                background: 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${colors.borderSubtle}`,
                marginTop: '6px',
              }}
            >
              127.0.0.1:{apiPort} (TCP Active)
            </div>
          </div>

          <div>
            <div style={{ color: colors.textMuted, fontSize: '0.74rem', textTransform: 'uppercase' }}>
              Mesh Consensus Status
            </div>
            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '0.84rem',
                color: colors.low,
                padding: '8px 12px',
                borderRadius: radii.sm,
                background: 'rgba(16, 185, 129, 0.08)',
                border: `1px solid ${colors.lowBorder}`,
                marginTop: '6px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>● {syncStatus}</span>
              <button
                type="button"
                onClick={onTriggerSync}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: colors.accentElectric,
                  fontSize: '0.74rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                Force Sync
              </button>
            </div>
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: `1px solid ${colors.borderSubtle}`, margin: 0 }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ color: colors.textPrimary, fontSize: '0.84rem', fontWeight: '700' }}>
              ResQMesh AI Command Suite
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.74rem', marginTop: '2px' }}>
              Release Version v1.0.19 • Next-Gen Mission Control Architecture
            </div>
          </div>
          <span
            style={{
              padding: '3px 10px',
              borderRadius: radii.full,
              fontSize: '0.68rem',
              fontWeight: '800',
              background: 'rgba(56, 189, 248, 0.12)',
              color: colors.accentElectric,
              border: `1px solid ${colors.borderFocus}`,
            }}
          >
            Production Ready
          </span>
        </div>
      </div>
    </div>
  );
};
