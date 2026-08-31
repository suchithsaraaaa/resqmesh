import React, { useState, useEffect, useRef } from 'react';
import { colors, radii, shadows, fonts } from '../styles/designTokens';
import { TacticalEventBus, TacticalActivityEvent, EventSeverity } from '../services/TacticalEventBus';

interface LiveTacticalActivityFeedProps {
  onSelectIncidentId?: (id: string) => void;
}

type FilterCategory = 'ALL' | 'INCIDENTS' | 'MESH' | 'RESOURCES' | 'SYSTEM';

export const LiveTacticalActivityFeed: React.FC<LiveTacticalActivityFeedProps> = ({
  onSelectIncidentId,
}) => {
  const [events, setEvents] = useState<TacticalActivityEvent[]>([]);
  const [filter, setFilter] = useState<FilterCategory>('ALL');
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isScrolledUp, setIsScrolledUp] = useState<boolean>(false);

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevEventCountRef = useRef<number>(0);

  // Subscribe to central TacticalEventBus
  useEffect(() => {
    const unsubscribe = TacticalEventBus.subscribe((updatedEvents) => {
      setEvents(updatedEvents);

      // If user is scrolled down/away from top and new events arrive, show new events pill
      if (isScrolledUp && updatedEvents.length > prevEventCountRef.current) {
        setUnreadCount((prev) => prev + (updatedEvents.length - prevEventCountRef.current));
      }
      prevEventCountRef.current = updatedEvents.length;
    });

    return unsubscribe;
  }, [isScrolledUp]);

  // Handle scroll detection
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop } = scrollContainerRef.current;
    if (scrollTop > 30) {
      setIsScrolledUp(true);
    } else {
      setIsScrolledUp(false);
      setUnreadCount(0);
    }
  };

  const scrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
    setUnreadCount(0);
    setIsScrolledUp(false);
  };

  // Filter events
  const filteredEvents = events.filter((evt) => {
    if (filter === 'ALL') return true;
    if (filter === 'INCIDENTS') {
      return (
        evt.type.startsWith('INCIDENT_') ||
        evt.type.startsWith('ALERT_') ||
        evt.type.startsWith('PHOTOS_') ||
        evt.type.startsWith('PHOTO_')
      );
    }
    if (filter === 'MESH') {
      return evt.type.startsWith('MESH_');
    }
    if (filter === 'RESOURCES') {
      return evt.type.startsWith('RESOURCE_');
    }
    if (filter === 'SYSTEM') {
      return (
        evt.type.startsWith('SYNC_') ||
        evt.type.startsWith('SYSTEM_') ||
        evt.type.startsWith('LOCATION_') ||
        evt.type.startsWith('AI_')
      );
    }
    return true;
  });

  const getSeverityIcon = (severity: EventSeverity): string => {
    switch (severity) {
      case 'CRITICAL':
        return '🔴';
      case 'WARNING':
        return '🟠';
      case 'SUCCESS':
        return '🟢';
      case 'INFO':
        return '🔵';
      case 'SYNC':
        return '🟣';
      default:
        return '⚪';
    }
  };

  const getSeverityColor = (severity: EventSeverity): string => {
    switch (severity) {
      case 'CRITICAL':
        return colors.critical;
      case 'WARNING':
        return colors.high;
      case 'SUCCESS':
        return colors.low;
      case 'INFO':
        return colors.accentElectric;
      case 'SYNC':
        return '#a855f7';
      default:
        return colors.textSecondary;
    }
  };

  return (
    <div
      style={{
        background: colors.bgSurface,
        border: `1px solid ${colors.borderSubtle}`,
        borderRadius: radii.xl,
        padding: '16px 20px',
        boxShadow: shadows.card,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        position: 'relative',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.15rem' }}>⚡</span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 800, color: colors.textPrimary }}>
                Live Tactical Activity Feed
              </h3>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  color: '#34d399',
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  padding: '2px 8px',
                  borderRadius: radii.full,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#34d399' }} />
                LIVE
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  color: colors.accentElectric,
                  background: 'rgba(56, 189, 248, 0.08)',
                  padding: '2px 6px',
                  borderRadius: radii.sm,
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                }}
              >
                REAL-TIME P2P
              </span>
            </div>
            <div style={{ fontSize: '0.70rem', color: colors.textMuted, marginTop: '2px' }}>
              Chronological operational stream across local node & connected mesh peers
            </div>
          </div>
        </div>

        {/* Filter Pills & Clear */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {(['ALL', 'INCIDENTS', 'MESH', 'RESOURCES', 'SYSTEM'] as FilterCategory[]).map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setFilter(cat)}
              style={{
                background: filter === cat ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                border: `1px solid ${filter === cat ? colors.accentElectric : colors.borderSubtle}`,
                color: filter === cat ? colors.accentElectric : colors.textMuted,
                borderRadius: radii.full,
                padding: '3px 9px',
                fontSize: '0.68rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {cat.charAt(0) + cat.slice(1).toLowerCase()}
            </button>
          ))}

          <button
            type="button"
            onClick={() => TacticalEventBus.clearFeed()}
            style={{
              background: 'transparent',
              border: 'none',
              color: colors.textMuted,
              fontSize: '0.70rem',
              cursor: 'pointer',
              textDecoration: 'underline',
              marginLeft: '4px',
            }}
          >
            Clear Feed
          </button>
        </div>
      </div>

      {/* Floating "X New Events" Pill when user scrolled up */}
      {unreadCount > 0 && isScrolledUp && (
        <div
          style={{
            position: 'absolute',
            top: '56px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
          }}
        >
          <button
            type="button"
            onClick={scrollToTop}
            style={{
              background: colors.accentElectric,
              color: '#070B14',
              border: 'none',
              borderRadius: radii.full,
              padding: '4px 14px',
              fontSize: '0.72rem',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(56, 189, 248, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'transform 0.15s ease',
            }}
          >
            <span>↓</span>
            <span>{unreadCount} new {unreadCount === 1 ? 'event' : 'events'}</span>
          </button>
        </div>
      )}

      {/* Event Stream List */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        style={{
          maxHeight: '260px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          paddingRight: '4px',
        }}
      >
        {filteredEvents.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '24px 0',
              color: colors.textMuted,
              fontSize: '0.78rem',
              fontStyle: 'italic',
            }}
          >
            No events match current filter.
          </div>
        ) : (
          filteredEvents.map((evt) => {
            const isExpanded = expandedEventId === evt.id;
            const icon = getSeverityIcon(evt.severity);
            const severityColor = getSeverityColor(evt.severity);

            return (
              <div
                key={evt.id}
                onClick={() => setExpandedEventId(isExpanded ? null : evt.id)}
                style={{
                  background: isExpanded ? 'rgba(56, 189, 248, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${isExpanded ? colors.accentElectric : colors.borderSubtle}`,
                  borderRadius: radii.lg,
                  padding: '10px 14px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
                onMouseEnter={(e) => {
                  if (!isExpanded) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isExpanded) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                  }
                }}
              >
                {/* Event Row Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.82rem' }}>{icon}</span>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        letterSpacing: '0.04em',
                        color: severityColor,
                        textTransform: 'uppercase',
                      }}
                    >
                      {evt.type.replace(/_/g, ' ')}
                    </span>
                    {evt.isRemote && (
                      <span
                        style={{
                          fontSize: '0.62rem',
                          background: 'rgba(99, 102, 241, 0.15)',
                          color: '#818cf8',
                          padding: '1px 5px',
                          borderRadius: radii.sm,
                          fontWeight: 700,
                        }}
                      >
                        REMOTE
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.70rem', color: colors.textMuted, fontFamily: 'monospace' }}>
                    {evt.timestamp}
                  </span>
                </div>

                {/* Event Title & Summary */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                  <div style={{ fontSize: '0.80rem', fontWeight: 600, color: colors.textPrimary, lineHeight: 1.4 }}>
                    {evt.title}
                  </div>
                  {evt.actor && (
                    <div style={{ fontSize: '0.70rem', color: colors.textMuted, flexShrink: 0 }}>
                      {evt.actor}
                    </div>
                  )}
                </div>

                {/* Expanded Detail View */}
                {isExpanded && (
                  <div
                    style={{
                      borderTop: `1px dashed ${colors.borderSubtle}`,
                      paddingTop: '8px',
                      marginTop: '4px',
                      fontSize: '0.75rem',
                      color: colors.textSecondary,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                    }}
                  >
                    <div style={{ lineHeight: 1.5 }}>{evt.description}</div>
                    {evt.nodeId && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <span style={{ color: colors.textMuted }}>Origin Node:</span>
                        <span style={{ color: colors.textPrimary, fontWeight: 700 }}>{evt.nodeId}</span>
                      </div>
                    )}
                    {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                      <div
                        style={{
                          background: 'rgba(15, 23, 42, 0.7)',
                          padding: '6px 8px',
                          borderRadius: radii.sm,
                          fontFamily: 'monospace',
                          fontSize: '0.68rem',
                          color: colors.accentElectric,
                        }}
                      >
                        {JSON.stringify(evt.metadata, null, 2)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
