import React, { useState, useEffect, useRef } from 'react';

interface FirstRunModalProps {
  isOpen: boolean;
  initialName?: string;
  initialRole?: string;
  onSave: (name: string, role: string) => Promise<void>;
  onContinueOffline?: (name: string, role: string) => void;
  onClose?: () => void;
  canClose?: boolean;
}

type OnboardingState = 'idle' | 'initializing' | 'success' | 'failed';

export const FirstRunModal: React.FC<FirstRunModalProps> = ({
  isOpen,
  initialName = '',
  initialRole = 'responder',
  onSave,
  onContinueOffline,
  onClose,
  canClose = false,
}) => {
  const [name, setName] = useState(initialName);
  const [role, setRole] = useState(initialRole);
  const [status, setStatus] = useState<OnboardingState>('idle');
  const [statusDetail, setStatusDetail] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<any>(null);

  useEffect(() => {
    const cleanName =
      initialName && !initialName.startsWith('Node-') && initialName !== 'Unnamed Laptop' && initialName !== 'ResQMesh-Node'
        ? initialName
        : '';
    setName(cleanName);
    setRole(initialRole || 'responder');
    setStatus('idle');
    setError(null);
  }, [initialName, initialRole, isOpen]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanName = name.trim();
    if (!cleanName) {
      setError('Please enter a friendly device name to identify this laptop across the mesh.');
      return;
    }

    setStatus('initializing');
    setStatusDetail('Configuring node identity & starting mesh services...');
    setError(null);

    // 5-second timeout safeguard to ensure UI NEVER remains stuck
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      if (status === 'initializing') {
        setStatus('failed');
        setError('Local mesh engine took longer than expected to respond. You may retry or continue in Offline Standalone mode.');
      }
    }, 5000);

    try {
      await onSave(cleanName, role);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setStatus('success');
      setStatusDetail('Identity configured! Initializing command center...');
    } catch (err: any) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setStatus('failed');
      setError(err.message || 'Failed to save node configuration. The backend daemon may still be initializing.');
    }
  };

  const handleOfflineMode = () => {
    const cleanName = name.trim() || `Laptop-Offline-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
    if (onContinueOffline) {
      onContinueOffline(cleanName, role);
    } else if (onClose) {
      onClose();
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.85)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      <div
        style={{
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '12px',
          width: '540px',
          maxWidth: '92vw',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            background: 'linear-gradient(90deg, #1e293b, #0f172a)',
            padding: '18px 24px',
            borderBottom: '1px solid #334155',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>🛰️</span>
            <div>
              <h3 style={{ margin: 0, color: '#38bdf8', fontSize: '1.15rem' }}>
                ResQMesh AI — Node Onboarding
              </h3>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.8rem' }}>
                Configure this laptop's identity on the offline emergency mesh
              </p>
            </div>
          </div>
          {canClose && onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                fontSize: '1.2rem',
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          {error && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #ef4444',
                color: '#fca5a5',
                padding: '12px 16px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '18px',
                lineHeight: '1.4',
              }}
            >
              <div style={{ fontWeight: '700', marginBottom: '4px' }}>⚠️ Setup Notice</div>
              {error}
            </div>
          )}

          {status === 'initializing' && (
            <div
              style={{
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid #38bdf8',
                color: '#bae6fd',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '18px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span style={{ animation: 'spin 1.5s linear infinite' }}>⏳</span>
              <span>{statusDetail || 'Initializing emergency mesh networking...'}</span>
            </div>
          )}

          {status === 'success' && (
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                color: '#6ee7b7',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '18px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>✅</span>
              <span>{statusDetail || 'Mesh initialized! Loading Tactical Dashboard...'}</span>
            </div>
          )}

          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                color: '#e2e8f0',
                fontSize: '0.85rem',
                fontWeight: '600',
                marginBottom: '6px',
              }}
            >
              Node Friendly Name
            </label>
            <input
              type="text"
              value={name}
              disabled={status === 'initializing'}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Laptop-Command-Center or Laptop-Squad-Alpha"
              style={{
                width: '100%',
                padding: '10px 14px',
                background: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '0.95rem',
                outline: 'none',
                boxSizing: 'border-box',
                opacity: status === 'initializing' ? 0.7 : 1,
              }}
            />
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Broadcasted across local Wi-Fi / LAN / BLE to identify this laptop.
            </span>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label
              style={{
                display: 'block',
                color: '#e2e8f0',
                fontSize: '0.85rem',
                fontWeight: '600',
                marginBottom: '8px',
              }}
            >
              Operational Role
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div
                onClick={() => status !== 'initializing' && setRole('commander')}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: `2px solid ${role === 'commander' ? '#38bdf8' : '#334155'}`,
                  background: role === 'commander' ? 'rgba(56, 189, 248, 0.1)' : '#1e293b',
                  cursor: status === 'initializing' ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: status === 'initializing' ? 0.7 : 1,
                }}
              >
                <div style={{ fontWeight: 'bold', color: '#38bdf8', marginBottom: '4px' }}>
                  🎯 Commander
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Headquarters laptop with full incident approval, resource dispatch, and master oversight.
                </div>
              </div>

              <div
                onClick={() => status !== 'initializing' && setRole('responder')}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: `2px solid ${role === 'responder' ? '#10b981' : '#334155'}`,
                  background: role === 'responder' ? 'rgba(16, 185, 129, 0.1)' : '#1e293b',
                  cursor: status === 'initializing' ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: status === 'initializing' ? 0.7 : 1,
                }}
              >
                <div style={{ fontWeight: 'bold', color: '#10b981', marginBottom: '4px' }}>
                  🚒 Field Responder
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Mobile field unit reporting raw ground conditions, hazards, and requesting supplies.
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
            <div>
              {status === 'failed' && (
                <button
                  type="button"
                  onClick={handleOfflineMode}
                  style={{
                    padding: '9px 16px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    color: '#fbbf24',
                    border: '1px solid #f59e0b',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  ⚡ Continue Offline
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              {canClose && onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  style={{
                    padding: '10px 18px',
                    background: '#334155',
                    color: '#cbd5e1',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
              )}

              {status === 'failed' ? (
                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  style={{
                    padding: '10px 20px',
                    background: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '600',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                  }}
                >
                  🔄 Retry Mesh
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={status === 'initializing'}
                  style={{
                    padding: '10px 22px',
                    background: status === 'initializing' ? '#475569' : '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '600',
                    fontSize: '0.9rem',
                    cursor: status === 'initializing' ? 'wait' : 'pointer',
                    transition: 'background 0.2s',
                  }}
                >
                  {status === 'initializing' ? 'Initializing Mesh...' : 'Join Emergency Mesh'}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

