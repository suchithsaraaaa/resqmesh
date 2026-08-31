import React from 'react';
import { colors, radii, fonts } from '../styles/designTokens';
import logoImg from '../assets/logo.png';

export type NavTab = 'dashboard' | 'globe' | 'incidents' | 'resources' | 'teams' | 'analytics' | 'advisor' | 'settings';

interface SidebarNavProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  incidentCount: number;
  criticalCount: number;
  pendingResourceCount: number;
  peerCount: number;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeTab,
  onSelectTab,
  incidentCount,
  criticalCount,
  pendingResourceCount,
  isCollapsed,
  onToggleCollapse,
}) => {
  const navItems: {
    id: NavTab;
    label: string;
    icon: string;
    badge?: number;
    badgeColor?: string;
  }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '▣' },
    { id: 'globe', label: '3D Globe', icon: '🌍' },
    {
      id: 'incidents',
      label: 'Incidents',
      icon: '⚠',
      badge: incidentCount > 0 ? incidentCount : undefined,
      badgeColor: criticalCount > 0 ? colors.critical : colors.high,
    },
    {
      id: 'resources',
      label: 'Resources',
      icon: '◇',
      badge: pendingResourceCount > 0 ? pendingResourceCount : undefined,
      badgeColor: colors.medium,
    },
    { id: 'teams', label: 'Active Teams', icon: '♙' },
    { id: 'analytics', label: 'Analytics', icon: '▥' },
    { id: 'advisor', label: 'Tactical Advisor', icon: '🧠' },
    { id: 'settings', label: 'Settings', icon: '⚙' },
  ];

  return (
    <aside
      style={{
        width: isCollapsed ? '72px' : '230px',
        transition: 'width 0.22s cubic-bezier(0.4, 0, 0.2, 1)',
        background: colors.bgSurface,
        borderRight: `1px solid ${colors.borderSubtle}`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: isCollapsed ? '20px 10px' : '20px 14px',
        boxSizing: 'border-box',
        zIndex: 20,
        userSelect: 'none',
      }}
    >
      {/* Top Section: Logo & Brand */}
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '4px 6px 24px 6px',
            borderBottom: `1px solid ${colors.borderSubtle}`,
            marginBottom: '16px',
            overflow: 'hidden',
          }}
        >
          <img
            src={logoImg}
            alt="ResQMesh AI"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: radii.md,
              objectFit: 'cover',
              flexShrink: 0,
              boxShadow: '0 0 14px rgba(56, 189, 248, 0.35)',
              border: `1px solid ${colors.borderMedium}`,
            }}
          />
          {!isCollapsed && (
            <div style={{ whiteSpace: 'nowrap', overflow: 'hidden' }}>
              <div
                style={{
                  fontFamily: fonts.sans,
                  fontSize: '1.05rem',
                  fontWeight: '800',
                  color: colors.textPrimary,
                  letterSpacing: '-0.3px',
                }}
              >
                ResQMesh AI
              </div>
              <div
                style={{
                  fontFamily: fonts.sans,
                  fontSize: '0.68rem',
                  color: colors.textMuted,
                  letterSpacing: '0.3px',
                  textTransform: 'uppercase',
                }}
              >
                Command Node
              </div>
            </div>
          )}
        </div>

        {/* Navigation Items List */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTab(item.id)}
                title={isCollapsed ? item.label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: isCollapsed ? 'center' : 'space-between',
                  padding: isCollapsed ? '10px 0' : '9px 12px',
                  borderRadius: radii.md,
                  border: 'none',
                  background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  color: isActive ? colors.accentElectric : colors.textSecondary,
                  cursor: 'pointer',
                  fontFamily: fonts.sans,
                  fontSize: '0.84rem',
                  fontWeight: isActive ? '700' : '500',
                  transition: 'all 0.15s ease',
                  width: '100%',
                  textAlign: 'left',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                    e.currentTarget.style.color = colors.textPrimary;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = colors.textSecondary;
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '11px' }}>
                  <span
                    style={{
                      fontSize: '1.05rem',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: isActive ? colors.accentElectric : colors.textMuted,
                    }}
                  >
                    {item.icon}
                  </span>
                  {!isCollapsed && <span>{item.label}</span>}
                </div>

                {!isCollapsed && item.badge !== undefined && (
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: '800',
                      padding: '2px 7px',
                      borderRadius: radii.full,
                      background: item.badgeColor || colors.accentElectric,
                      color: '#ffffff',
                      boxShadow: '0 2px 6px rgba(0, 0, 0, 0.3)',
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section: Collapse Toggle */}
      <div style={{ borderTop: `1px solid ${colors.borderSubtle}`, paddingTop: '14px' }}>
        <button
          type="button"
          onClick={onToggleCollapse}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'flex-start',
            gap: '10px',
            width: '100%',
            padding: '8px 10px',
            background: 'transparent',
            border: 'none',
            color: colors.textMuted,
            fontSize: '0.78rem',
            fontFamily: fonts.sans,
            cursor: 'pointer',
            borderRadius: radii.sm,
            transition: 'color 0.15s ease',
          }}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          <span>{isCollapsed ? '⇥' : '⇤'}</span>
          {!isCollapsed && <span>Collapse Sidebar</span>}
        </button>
      </div>
    </aside>
  );
};
