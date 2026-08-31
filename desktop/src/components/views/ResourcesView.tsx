import React from 'react';
import { ResourceRequestItem } from '../ResourceDispatchPanel';
import { colors, radii, shadows, fonts } from '../../styles/designTokens';

interface ResourcesViewProps {
  resources: ResourceRequestItem[];
  onDispatch: (id: string) => void;
  onRescind: (id: string) => void;
  onOpenRequestModal: () => void;
  nodeRole: string;
}

export const ResourcesView: React.FC<ResourcesViewProps> = ({
  resources,
  onDispatch,
  onRescind,
  onOpenRequestModal,
  nodeRole,
}) => {
  const isCommander = nodeRole.toLowerCase() === 'commander';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: colors.bgSurface,
          padding: '16px 20px',
          borderRadius: radii.lg,
          border: `1px solid ${colors.borderSubtle}`,
          boxShadow: shadows.card,
        }}
      >
        <div>
          <h3 style={{ margin: 0, color: colors.textPrimary, fontSize: '1rem', fontWeight: '800' }}>
            Resource Inventory & Field Allocation
          </h3>
          <p style={{ margin: 0, color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
            {isCommander
              ? 'Authorized Commander Mode: Direct tactical dispatch of critical equipment and trauma assets.'
              : 'Responder Field Mode: Request emergency logistics and track squad delivery status.'}
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenRequestModal}
          style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: radii.sm,
            padding: '8px 18px',
            fontSize: '0.8rem',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: '0 2px 10px rgba(2, 132, 199, 0.35)',
          }}
        >
          <span>📦</span> Request Resources
        </button>
      </div>

      {/* Resources Table */}
      <div
        style={{
          background: colors.bgSurface,
          borderRadius: radii.xl,
          border: `1px solid ${colors.borderSubtle}`,
          boxShadow: shadows.elevated,
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${colors.borderSubtle}`, background: 'rgba(255, 255, 255, 0.02)' }}>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                RESOURCE ASSET
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                QTY
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                URGENCY
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                STATUS
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                REQUESTED BY
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700', textAlign: 'right' }}>
                TACTICAL ACTION
              </th>
            </tr>
          </thead>
          <tbody>
            {resources.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '40px 20px', textAlign: 'center', color: colors.textMuted }}>
                  No active resource requests in queue.
                </td>
              </tr>
            ) : (
              resources.map((item) => {
                const isPending = item.status.toLowerCase() === 'pending';
                const isDispatched = item.status.toLowerCase() === 'dispatched';
                return (
                  <tr key={item.id} style={{ borderBottom: `1px solid ${colors.borderSubtle}` }}>
                    <td style={{ padding: '14px 20px', color: colors.textPrimary, fontWeight: '700', fontSize: '0.86rem' }}>
                      {item.resourceType}
                    </td>
                    <td style={{ padding: '14px 20px', fontFamily: fonts.mono, color: colors.textSecondary, fontSize: '0.86rem' }}>
                      {item.quantity} units
                    </td>
                    <td style={{ padding: '14px 20px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: radii.full,
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          textTransform: 'uppercase',
                          background:
                            item.urgency === 'critical'
                              ? colors.criticalBg
                              : item.urgency === 'high'
                              ? colors.highBg
                              : colors.mediumBg,
                          color:
                            item.urgency === 'critical'
                              ? colors.critical
                              : item.urgency === 'high'
                              ? colors.high
                              : colors.medium,
                          border: `1px solid ${
                            item.urgency === 'critical'
                              ? colors.criticalBorder
                              : item.urgency === 'high'
                              ? colors.highBorder
                              : colors.mediumBorder
                          }`,
                        }}
                      >
                        {item.urgency}
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px' }}>
                      <span
                        style={{
                          fontSize: '0.74rem',
                          fontWeight: '700',
                          color: isDispatched ? colors.low : colors.medium,
                        }}
                      >
                        {isDispatched ? '● Dispatched / En Route' : '⏳ Pending Authorization'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px', color: colors.textMuted, fontSize: '0.78rem' }}>
                      {item.requestedBy || 'Field Unit'}
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      {isCommander ? (
                        isPending ? (
                          <button
                            type="button"
                            onClick={() => onDispatch(item.id)}
                            style={{
                              background: colors.low,
                              border: 'none',
                              color: '#ffffff',
                              padding: '5px 14px',
                              borderRadius: radii.sm,
                              fontSize: '0.74rem',
                              fontWeight: '700',
                              cursor: 'pointer',
                            }}
                          >
                            Authorize Dispatch
                          </button>
                        ) : (
                          <span style={{ color: colors.low, fontSize: '0.74rem', fontWeight: '700' }}>
                            ✓ Authorized
                          </span>
                        )
                      ) : (
                        isPending && (
                          <button
                            type="button"
                            onClick={() => onRescind(item.id)}
                            style={{
                              background: 'transparent',
                              border: `1px solid ${colors.critical}`,
                              color: colors.critical,
                              padding: '4px 12px',
                              borderRadius: radii.sm,
                              fontSize: '0.72rem',
                              fontWeight: '700',
                              cursor: 'pointer',
                            }}
                          >
                            Rescind
                          </button>
                        )
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
