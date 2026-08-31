import React from 'react';
import { colors, radii, shadows, fonts } from '../../styles/designTokens';

export interface RescueTeam {
  id: string;
  name: string;
  callsign: string;
  location: string;
  coordinates: { lat: number; lon: number };
  status: 'on_mission' | 'standby' | 'transit';
  personnelCount: number;
  assignedIncident?: string;
  channel: string;
}

export const TeamsView: React.FC = () => {
  const teams: RescueTeam[] = [
    {
      id: 'team-alpha',
      name: 'Alpha Tactical Squad',
      callsign: 'ALPHA-1',
      location: 'Hyderabad Sector',
      coordinates: { lat: 17.385, lon: 78.4867 },
      status: 'on_mission',
      personnelCount: 8,
      assignedIncident: 'Chemical Leak Hazmat Containment',
      channel: 'MESH-CH-01',
    },
    {
      id: 'team-bravo',
      name: 'Bravo Rapid Extraction Squad',
      callsign: 'BRAVO-2',
      location: 'Vijayawada Sector',
      coordinates: { lat: 16.5062, lon: 80.648 },
      status: 'on_mission',
      personnelCount: 6,
      assignedIncident: 'Structural Collapse Search & Rescue',
      channel: 'MESH-CH-02',
    },
    {
      id: 'team-charlie',
      name: 'Charlie Medical Evac Unit',
      callsign: 'CHARLIE-MED',
      location: 'Visakhapatnam Coast',
      coordinates: { lat: 17.6868, lon: 83.2185 },
      status: 'standby',
      personnelCount: 5,
      channel: 'MESH-CH-03',
    },
    {
      id: 'team-delta',
      name: 'Delta Drone Recon Squad',
      callsign: 'DELTA-UAV',
      location: 'Bengaluru Command Node',
      coordinates: { lat: 12.9716, lon: 77.5946 },
      status: 'standby',
      personnelCount: 4,
      channel: 'MESH-CH-04',
    },
    {
      id: 'team-echo',
      name: 'Echo Heavy Equipment Logistics',
      callsign: 'ECHO-HVY',
      location: 'Warangal Sector',
      coordinates: { lat: 17.9689, lon: 79.5941 },
      status: 'transit',
      personnelCount: 7,
      assignedIncident: 'Bridge Infrastructure Clearance',
      channel: 'MESH-CH-05',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
            Active Rescue Teams & Squad Deployment
          </h3>
          <p style={{ margin: 0, color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
            Live status of 5 field response squads operating across autonomous mesh sectors.
          </p>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '16px',
        }}
      >
        {teams.map((team) => {
          const isOnMission = team.status === 'on_mission';
          const isStandby = team.status === 'standby';
          return (
            <div
              key={team.id}
              style={{
                background: colors.bgSurface,
                border: `1px solid ${colors.borderSubtle}`,
                borderRadius: radii.lg,
                padding: '18px 20px',
                boxShadow: shadows.card,
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
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
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h4 style={{ margin: 0, color: colors.textPrimary, fontSize: '0.95rem', fontWeight: '800' }}>
                    {team.name}
                  </h4>
                  <span
                    style={{
                      fontFamily: fonts.mono,
                      fontSize: '0.7rem',
                      color: colors.accentElectric,
                      fontWeight: '700',
                    }}
                  >
                    {team.callsign}
                  </span>
                </div>

                <span
                  style={{
                    padding: '3px 8px',
                    borderRadius: radii.full,
                    fontSize: '0.68rem',
                    fontWeight: '800',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    background: isOnMission ? 'rgba(239, 68, 68, 0.15)' : isStandby ? 'rgba(16, 185, 129, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                    color: isOnMission ? colors.critical : isStandby ? colors.low : colors.medium,
                    border: `1px solid ${isOnMission ? colors.criticalBorder : isStandby ? colors.lowBorder : colors.mediumBorder}`,
                  }}
                >
                  ● {isOnMission ? 'On Mission' : isStandby ? 'Standby' : 'In Transit'}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: colors.textMuted }}>Operational Sector:</span>
                  <span style={{ color: colors.textSecondary, fontWeight: '600' }}>{team.location}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: colors.textMuted }}>Coordinates:</span>
                  <span style={{ color: colors.textSecondary, fontFamily: fonts.mono }}>
                    {team.coordinates.lat.toFixed(4)}°N, {team.coordinates.lon.toFixed(4)}°E
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: colors.textMuted }}>Field Personnel:</span>
                  <span style={{ color: colors.textPrimary, fontWeight: '700' }}>{team.personnelCount} Responders</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: colors.textMuted }}>Comms Link:</span>
                  <span style={{ color: colors.accentElectric, fontFamily: fonts.mono }}>{team.channel}</span>
                </div>

                {team.assignedIncident && (
                  <div
                    style={{
                      marginTop: '6px',
                      padding: '8px 10px',
                      borderRadius: radii.sm,
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: `1px solid ${colors.borderSubtle}`,
                    }}
                  >
                    <div style={{ color: colors.textMuted, fontSize: '0.68rem', textTransform: 'uppercase' }}>
                      Target Assignment
                    </div>
                    <div style={{ color: colors.textPrimary, fontSize: '0.78rem', fontWeight: '700', marginTop: '2px' }}>
                      {team.assignedIncident}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
