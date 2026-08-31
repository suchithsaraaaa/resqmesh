import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ResQMesh ErrorBoundary] Caught error:', error, errorInfo);
  }

  private handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '24px',
            margin: '16px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #ef4444',
            borderRadius: '8px',
            color: '#f8fafc',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>⚠️</div>
          <h3 style={{ margin: '0 0 8px 0', color: '#ef4444' }}>
            {this.props.fallbackTitle || 'Component Display Error'}
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '16px', maxWidth: '500px', margin: '0 auto 16px auto' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>
          <button
            type="button"
            onClick={this.handleReload}
            style={{
              background: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 18px',
              fontSize: '0.85rem',
              fontWeight: '700',
              cursor: 'pointer',
            }}
          >
            ↺ Reload View
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
