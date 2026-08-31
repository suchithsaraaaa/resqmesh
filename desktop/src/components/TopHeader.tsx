import React, { useEffect, useState } from 'react';
import { colors, radii, fonts } from '../styles/designTokens';
import { NavTab } from './SidebarNav';

interface TopHeaderProps {
  activeTab: NavTab;
  nodeName: string;
  nodeRole: string;
  peerCount: number;
  unreadNotificationCount: number;
  onOpenNotifications: () => void;
  onOpenBroadcastModal: () => void;
  onOpenConfigModal: () => void;
  onOpenPeersModal: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  nodeName,
  nodeRole,
  peerCount,
  unreadNotificationCount,
  onOpenNotifications,
  onOpenBroadcastModal,
  onOpenConfigModal,
  onOpenPeersModal,
}) => {
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = (tab: NavTab): { title: string; subtitle: string } => {
    switch (tab) {
      case 'dashboard':
        return { title: 'Global Overview', subtitle: 'Strategic 3D Incident Situation & Mesh Coordination' };
      case 'globe':
        return { title: '3D Planetary Situational Earth', subtitle: 'Full-Screen Interactive Orbit Visualization' };
      case 'incidents':
        return { title: 'Operational Incident Stream', subtitle: 'Triage, Prioritization & Evidence Logs' };
      case 'resources':
        return { title: 'Emergency Resource Dispatch', subtitle: 'Equipment, Rations & Personnel Logistics' };
      case 'teams':
        return { title: 'Active Response Squads', subtitle: 'Field Deployment & Unit Assignment' };
      case 'analytics':
        return { title: 'Tactical Analytics', subtitle: 'Severity Distributions & Incident Response Velocity' };
      case 'advisor':
        return { title: 'AI Tactical Advisor & SOPs', subtitle: 'Offline RAG Protocol Intelligence & SITREPs' };
      case 'settings':
        return { title: 'Node System & Network Configuration', subtitle: 'Identity, Mesh Ports & Local Database' };
      default:
        return { title: 'Global Overview', subtitle: 'Emergency Command Center' };
    }
  };

  const { title, subtitle } = getPageTitle(activeTab);

  return (
    <header
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 28px',
        background: colors.bgSurface,
        borderBottom: `1px solid ${colors.borderSubtle}`,
        boxSizing: 'border-box',
        gap: '20px',
        flexWrap: 'wrap',
      }}
    >
      {/* Left: Page Title & Live Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1
              style={{
                margin: 0,
                fontFamily: fonts.sans,
                fontSize: '1.28rem',
                fontWeight: '800',
                letterSpacing: '-0.3px',
                color: colors.textPrimary,
              }}
            >
              {title}
            </h1>

            {/* ● LIVE Pulsing Indicator */}
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 9px',
                borderRadius: radii.full,
                background: 'rgba(16, 185, 129, 0.15)',
                border: `1px solid ${colors.lowBorder}`,
                color: colors.low,
                fontSize: '0.68rem',
                fontWeight: '800',
                letterSpacing: '0.6px',
                textTransform: 'uppercase',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: colors.low,
                  boxShadow: '0 0 8px #10b981',
                  animation: 'pulse 2s infinite',
                }}
              />
              LIVE
            </span>
          </div>

          <p
            style={{
              margin: 0,
              fontFamily: fonts.sans,
              fontSize: '0.76rem',
              color: colors.textMuted,
              marginTop: '2px',
            }}
          >
            {subtitle}
          </p>
        </div>
      </div>

      {/* Right: Operational Status, Clock, Profile & Primary Action */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        {/* Status: Operational */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 10px',
            borderRadius: radii.sm,
            background: 'rgba(255, 255, 255, 0.03)',
            border: `1px solid ${colors.borderSubtle}`,
            fontSize: '0.74rem',
            fontFamily: fonts.sans,
            color: colors.textSecondary,
          }}
        >
          <span style={{ color: colors.low }}>●</span>
          <span>System Operational</span>
        </div>

        {/* Status: Mesh Network */}
        <button
          type="button"
          onClick={onOpenPeersModal}
          title="Inspect Connected Peer Nodes"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 11px',
            borderRadius: radii.sm,
            background: peerCount > 0 ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.03)',
            border: `1px solid ${peerCount > 0 ? colors.borderFocus : colors.borderSubtle}`,
            fontSize: '0.74rem',
            fontFamily: fonts.sans,
            color: peerCount > 0 ? colors.accentElectric : colors.textMuted,
            cursor: 'pointer',
            fontWeight: '600',
            transition: 'all 0.15s ease',
          }}
        >
          <span>📡</span>
          <span>{peerCount > 0 ? `Mesh: ${peerCount} Connected` : 'Mesh: Local Mode'}</span>
        </button>

        {/* Digital Clock */}
        <div
          style={{
            fontFamily: fonts.mono,
            fontSize: '0.82rem',
            color: colors.textSecondary,
            padding: '5px 10px',
            borderRadius: radii.sm,
            background: 'rgba(255, 255, 255, 0.03)',
            border: `1px solid ${colors.borderSubtle}`,
            letterSpacing: '1px',
          }}
        >
          {currentTime || '00:00:00'}
        </div>

        {/* Notification Bell */}
        <button
          type="button"
          onClick={onOpenNotifications}
          title="Open Live Tactical Activity Feed"
          style={{
            position: 'relative',
            width: '34px',
            height: '34px',
            borderRadius: radii.sm,
            background: 'rgba(255, 255, 255, 0.03)',
            border: `1px solid ${colors.borderSubtle}`,
            color: colors.textSecondary,
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🔔</span>
          {unreadNotificationCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                width: '14px',
                height: '14px',
                borderRadius: '50%',
                background: colors.critical,
                color: '#ffffff',
                fontSize: '0.62rem',
                fontWeight: '800',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {unreadNotificationCount > 9 ? '9+' : unreadNotificationCount}
            </span>
          )}
        </button>

        {/* Commander Profile Pill */}
        <button
          type="button"
          onClick={onOpenConfigModal}
          title="Configure Node Identity & Role"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '9px',
            padding: '4px 10px 4px 6px',
            borderRadius: radii.full,
            background: 'rgba(255, 255, 255, 0.04)',
            border: `1px solid ${colors.borderMedium}`,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontSize: '0.72rem',
              fontWeight: '800',
            }}
          >
            {nodeName ? nodeName.charAt(0).toUpperCase() : 'C'}
          </div>
          <div style={{ textAlign: 'left' }}>
            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '0.78rem',
                fontWeight: '700',
                color: colors.textPrimary,
                lineHeight: 1.1,
              }}
            >
              {nodeName || 'Commander Node'}
            </div>
            <div
              style={{
                fontFamily: fonts.sans,
                fontSize: '0.65rem',
                color: colors.textMuted,
                textTransform: 'capitalize',
              }}
            >
              {nodeRole || 'Incident Commander'}
            </div>
          </div>
          <span style={{ fontSize: '0.65rem', color: colors.textMuted }}>▼</span>
        </button>

        {/* Primary Action: Broadcast Alert */}
        <button
          type="button"
          onClick={onOpenBroadcastModal}
          style={{
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: radii.md,
            padding: '8px 18px',
            fontSize: '0.82rem',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: '0 4px 14px rgba(239, 68, 68, 0.35)',
            transition: 'transform 0.15s ease, box-shadow 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = '0 6px 18px rgba(239, 68, 68, 0.45)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 14px rgba(239, 68, 68, 0.35)';
          }}
        >
          <span>🚨</span> Broadcast Alert
        </button>
      </div>
    </header>
  );
};
