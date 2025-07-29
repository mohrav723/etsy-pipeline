import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={styles.errorContainer}>
          <div style={styles.errorCard}>
            <h2 style={styles.errorTitle}>🚨 Something went wrong</h2>
            <p style={styles.errorMessage}>
              An unexpected error occurred. Please try refreshing the page.
            </p>
            <details style={styles.errorDetails}>
              <summary style={styles.errorSummary}>Technical Details</summary>
              <pre style={styles.errorPre}>
                {this.state.error?.message}
                {'\n'}
                {this.state.error?.stack}
              </pre>
            </details>
            <button style={styles.errorButton} onClick={() => window.location.reload()}>
              🔄 Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const styles = {
  errorContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
    padding: '20px',
  },
  errorCard: {
    backgroundColor: '#23272a',
    border: '1px solid #ed4245',
    borderRadius: '8px',
    padding: '24px',
    maxWidth: '500px',
    width: '100%',
    textAlign: 'center' as const,
  },
  errorTitle: {
    color: '#ed4245',
    margin: '0 0 16px 0',
    fontSize: '1.5rem',
  },
  errorMessage: {
    color: '#99aab5',
    margin: '0 0 20px 0',
    lineHeight: '1.5',
  },
  errorDetails: {
    textAlign: 'left' as const,
    marginBottom: '20px',
    backgroundColor: '#1a1a1a',
    border: '1px solid #40444b',
    borderRadius: '4px',
    padding: '12px',
  },
  errorSummary: {
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '0.9rem',
    marginBottom: '8px',
  },
  errorPre: {
    color: '#99aab5',
    fontSize: '0.8rem',
    margin: '8px 0 0 0',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
  },
  errorButton: {
    backgroundColor: '#5865f2',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '12px 24px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
};

export default ErrorBoundary;
