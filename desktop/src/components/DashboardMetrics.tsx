import React from 'react';
import { colors, radii, shadows, fonts } from '../styles/designTokens';

interface DashboardMetricsProps {
  totalIncidents: number;
  criticalIncidents: number;
  activeTeamsCount?: number;
  dispatchedResourcesCount?: number;
}

export const DashboardMetrics: React.FC<DashboardMetricsProps> = ({
  totalIncidents,
  criticalIncidents,
  activeTeamsCount = 4,
  dispatchedResourcesCount = 14,
}) => {
  const metrics = [
    {
      label: 'TOTAL INCIDENTS',
      value: totalIncidents,
      change: '+12% from last 24h',
      accentColor: colors.accentElectric,
      icon: '📊',
    },
    {
      label: 'CRITICAL PRIORITY',
      value: criticalIncidents,
      change: criticalIncidents > 0 ? 'Requires immediate action' : 'All sectors stable',
      accentColor: colors.critical,
      icon: '🚨',
    },
    {
      label: 'ACTIVE RESCUE SQUADS',
      value: activeTeamsCount,
      change: '2 On Mission • 2 Standby',
      accentColor: colors.low,
      icon: '♙',
    },
    {
      label: 'RESOURCES DEPLOYED',
      value: dispatchedResourcesCount,
      change: '94% equipment availability',
      accentColor: colors.accentIndigo,
      icon: '📦',
    },
  ];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        width: '100%',
      }}
    >
      {metrics.map((metric, idx) => (
        <div
          key={idx}
          style={{
            background: colors.bgSurface,
            border: `1px solid ${colors.borderSubtle}`,
            borderRadius: radii.lg,
            padding: '16px 20px',
            boxShadow: shadows.card,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'transform 0.15s ease, border-color 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.borderColor = colors.borderMedium;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = colors.borderSubtle;
          }}
        >
          <div>
            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '0.68rem',
                fontWeight: '700',
                letterSpacing: '0.6px',
                color: colors.textMuted,
                textTransform: 'uppercase',
                marginBottom: '6px',
              }}
            >
              {metric.label}
            </div>

            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '1.75rem',
                fontWeight: '800',
                color: colors.textPrimary,
                lineHeight: 1,
              }}
            >
              {metric.value}
            </div>

            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '0.72rem',
                color: colors.textSecondary,
                marginTop: '6px',
              }}
            >
              {metric.change}
            </div>
          </div>

          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: radii.md,
              background: 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${colors.borderSubtle}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.25rem',
            }}
          >
            {metric.icon}
          </div>
        </div>
      ))}
    </div>
  );
};
