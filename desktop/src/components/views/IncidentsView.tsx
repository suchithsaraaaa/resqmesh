import React, { useState } from 'react';
import { MapIncidentMarker } from '../MapView';
import { PendingReportCluster, IncidentReviewCard } from '../IncidentReviewCard';
import { colors, radii, shadows, fonts } from '../../styles/designTokens';

interface IncidentsViewProps {
  incidents: MapIncidentMarker[];
  clusters: PendingReportCluster[];
  onSelectIncident: (id: string) => void;
  onOpenDetailsModal: (inc: MapIncidentMarker) => void;
  onApproveMerge: (reportId: string, incidentId: string) => void;
  onRejectAsNew: (reportId: string) => void;
  onOpenCreateModal: () => void;
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({
  incidents,
  clusters,
  onOpenDetailsModal,
  onApproveMerge,
  onRejectAsNew,
  onOpenCreateModal,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filtered = incidents.filter((inc) => {
    const matchesSeverity =
      filterSeverity === 'all' || inc.severity.toLowerCase() === filterSeverity.toLowerCase();
    const matchesSearch =
      searchQuery.trim() === '' ||
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inc.category && inc.category.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (inc.summary && inc.summary.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSeverity && matchesSearch;
  });

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return { color: colors.critical, bg: colors.criticalBg, border: colors.criticalBorder };
      case 'high':
        return { color: colors.high, bg: colors.highBg, border: colors.highBorder };
      case 'medium':
        return { color: colors.medium, bg: colors.mediumBg, border: colors.mediumBorder };
      default:
        return { color: colors.low, bg: colors.lowBg, border: colors.lowBorder };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* AI Duplicate Screening Section if clusters exist */}
      {clusters.length > 0 && (
        <IncidentReviewCard
          clusters={clusters}
          onApproveMerge={onApproveMerge}
          onRejectAsNew={onRejectAsNew}
        />
      )}

      {/* Control Bar: Search & Severity Filters */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'wrap',
          background: colors.bgSurface,
          padding: '14px 20px',
          borderRadius: radii.lg,
          border: `1px solid ${colors.borderSubtle}`,
          boxShadow: shadows.card,
        }}
      >
        {/* Search */}
        <div style={{ position: 'relative', minWidth: '260px', flex: 1, maxWidth: '420px' }}>
          <span
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: colors.textMuted,
              fontSize: '0.85rem',
            }}
          >
            🔍
          </span>
          <input
            type="text"
            placeholder="Search operational incidents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 36px',
              borderRadius: radii.sm,
              background: colors.bgElevated,
              border: `1px solid ${colors.borderMedium}`,
              color: colors.textPrimary,
              fontSize: '0.82rem',
              fontFamily: fonts.sans,
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Severity Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => {
            const isActive = filterSeverity === sev;
            const count =
              sev === 'all'
                ? incidents.length
                : incidents.filter((i) => i.severity.toLowerCase() === sev).length;
            return (
              <button
                key={sev}
                type="button"
                onClick={() => setFilterSeverity(sev)}
                style={{
                  padding: '6px 12px',
                  borderRadius: radii.sm,
                  border: `1px solid ${isActive ? colors.accentElectric : colors.borderSubtle}`,
                  background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  color: isActive ? colors.accentElectric : colors.textSecondary,
                  fontFamily: fonts.sans,
                  fontSize: '0.74rem',
                  fontWeight: '700',
                  textTransform: 'capitalize',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{sev}</span>
                <span
                  style={{
                    fontSize: '0.66rem',
                    padding: '1px 6px',
                    borderRadius: radii.full,
                    background: 'rgba(255, 255, 255, 0.08)',
                    color: colors.textPrimary,
                  }}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Broadcast Trigger */}
        <button
          type="button"
          onClick={onOpenCreateModal}
          style={{
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: radii.sm,
            padding: '7px 16px',
            fontSize: '0.78rem',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: '0 2px 10px rgba(239, 68, 68, 0.3)',
          }}
        >
          <span>🚨</span> Report Incident
        </button>
      </div>

      {/* Incidents Table */}
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
            <tr
              style={{
                borderBottom: `1px solid ${colors.borderSubtle}`,
                background: 'rgba(255, 255, 255, 0.02)',
              }}
            >
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                SEVERITY
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                INCIDENT TITLE
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                CATEGORY
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                COORDINATES / SECTOR
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700' }}>
                BROADCASTER
              </th>
              <th style={{ padding: '14px 20px', fontSize: '0.72rem', color: colors.textMuted, fontWeight: '700', textAlign: 'right' }}>
                ACTION
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '40px 20px', textAlign: 'center', color: colors.textMuted }}>
                  No operational incidents matching the selected criteria.
                </td>
              </tr>
            ) : (
              filtered.map((inc) => {
                const sStyle = getSeverityStyle(inc.severity);
                return (
                  <tr
                    key={inc.id}
                    style={{
                      borderBottom: `1px solid ${colors.borderSubtle}`,
                      transition: 'background 0.15s ease',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                    }}
                    onClick={() => onOpenDetailsModal(inc)}
                  >
                    <td style={{ padding: '14px 20px' }}>
                      <span
                        style={{
                          padding: '3px 9px',
                          borderRadius: radii.full,
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          textTransform: 'uppercase',
                          background: sStyle.bg,
                          color: sStyle.color,
                          border: `1px solid ${sStyle.border}`,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                        }}
                      >
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: sStyle.color }} />
                        {inc.severity}
                      </span>
                    </td>

                    <td style={{ padding: '14px 20px' }}>
                      <div style={{ color: colors.textPrimary, fontSize: '0.86rem', fontWeight: '700' }}>
                        {inc.title}
                      </div>
                      {inc.summary && (
                        <div style={{ color: colors.textMuted, fontSize: '0.72rem', marginTop: '2px' }}>
                          {inc.summary.slice(0, 90)}...
                        </div>
                      )}
                    </td>

                    <td style={{ padding: '14px 20px', color: colors.textSecondary, fontSize: '0.78rem' }}>
                      {inc.category || 'General'}
                    </td>

                    <td style={{ padding: '14px 20px', fontFamily: fonts.mono, fontSize: '0.76rem', color: colors.textSecondary }}>
                      {inc.lat !== null && inc.lon !== null
                        ? `📍 ${inc.lat.toFixed(4)}°N, ${inc.lon.toFixed(4)}°E`
                        : 'Unmapped'}
                    </td>

                    <td style={{ padding: '14px 20px', fontSize: '0.78rem', color: colors.textMuted }}>
                      {inc.broadcasterName || 'Autonomous Node'}
                    </td>

                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenDetailsModal(inc);
                        }}
                        style={{
                          background: 'rgba(56, 189, 248, 0.12)',
                          border: `1px solid ${colors.accentElectric}`,
                          color: colors.accentElectric,
                          padding: '5px 12px',
                          borderRadius: radii.sm,
                          fontSize: '0.72rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        Inspect
                      </button>
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
