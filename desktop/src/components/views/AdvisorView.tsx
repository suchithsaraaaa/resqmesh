import React from 'react';
import { TacticalAdvisorPanel } from '../TacticalAdvisorPanel';
import { colors, radii, shadows } from '../../styles/designTokens';

interface AdvisorViewProps {
  apiUrl: string;
}

export const AdvisorView: React.FC<AdvisorViewProps> = ({ apiUrl }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
          Autonomous AI Tactical Advisor & Verified SOPs
        </h3>
        <p style={{ margin: 0, color: colors.textMuted, fontSize: '0.76rem', marginTop: '2px' }}>
          On-device RAG decision support: instant offline retrieval of official NDMA, FEMA, Hazmat, and Trauma guidelines.
        </p>
      </div>

      <div
        style={{
          background: colors.bgSurface,
          borderRadius: radii.xl,
          border: `1px solid ${colors.borderSubtle}`,
          padding: '24px',
          boxShadow: shadows.elevated,
        }}
      >
        <TacticalAdvisorPanel apiUrl={apiUrl} />
      </div>
    </div>
  );
};
