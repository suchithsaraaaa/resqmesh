import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from 'react-native';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ResQMesh Uncaught Component Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />
          <View style={styles.card}>
            <Text style={styles.icon}>🚨</Text>
            <Text style={styles.title}>ResQMesh AI System Error</Text>
            <Text style={styles.subtitle}>
              An unexpected interface component error occurred. Core offline services remain operational.
            </Text>

            <View style={styles.errorBox}>
              <Text style={styles.errorText}>
                {this.state.error?.toString() || 'Unknown runtime error'}
              </Text>
            </View>

            <TouchableOpacity style={styles.button} onPress={this.handleReload}>
              <Text style={styles.buttonText}>🔄 Reload ResQMesh UI</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1B2A',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    backgroundColor: '#152131',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 420,
    borderWidth: 1,
    borderColor: '#1E3050',
    alignItems: 'center',
  },
  icon: {
    fontSize: 44,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#E8F4FD',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 13,
    color: '#7DB9DE',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 16,
  },
  errorBox: {
    backgroundColor: '#0D1B2A',
    borderRadius: 8,
    padding: 12,
    width: '100%',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E63946',
  },
  errorText: {
    color: '#F44336',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  button: {
    backgroundColor: '#E63946',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    width: '100%',
    alignItems: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
});

export default ErrorBoundary;
