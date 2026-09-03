/**
 * ResQMesh Mobile — Compact Mesh Status Header Component.
 * 
 * Displays live, truthful mesh connection states directly on the main field dashboard.
 * Tapping the header opens the full Mesh Diagnostic & Peer Inspector modal.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { MeshStatusInfo } from '../network/meshService';

interface Props {
  status: MeshStatusInfo;
  onPress: () => void;
}

export default function MeshStatusHeader({ status, onPress }: Props) {
  const { state, connectedCommander, activePeerCount, lastSyncTime } = status;

  const formatLastSync = (ts: number | null) => {
    if (!ts) return 'Never';
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getStatusConfig = () => {
    switch (state) {
      case 'CONNECTED':
        return {
          title: '● MESH CONNECTED',
          badgeBg: '#064E3B',
          borderColor: '#10B981',
          textColor: '#34D399',
          subText: connectedCommander
            ? `Commander: ${connectedCommander.name} (${connectedCommander.latencyMs}ms) • Last sync: ${formatLastSync(lastSyncTime)}`
            : `${activePeerCount} peer(s) connected • Last sync: ${formatLastSync(lastSyncTime)}`,
          showSpinner: false,
        };
      case 'STANDALONE':
        return {
          title: '● MESH STANDALONE',
          badgeBg: '#451A03',
          borderColor: '#F59E0B',
          textColor: '#FBBF24',
          subText: '0 peers connected • Local mesh operational (offline ready)',
          showSpinner: false,
        };
      case 'CONNECTING':
        return {
          title: 'CONNECTING TO MESH...',
          badgeBg: '#082F49',
          borderColor: '#38BDF8',
          textColor: '#38BDF8',
          subText: 'Probing LAN and candidate gateways for Command Center...',
          showSpinner: true,
        };
      case 'RECONNECTING':
        return {
          title: 'RECONNECTING TO MESH...',
          badgeBg: '#431407',
          borderColor: '#F97316',
          textColor: '#FB923C',
          subText: 'Connection lost • Attempting automatic reconnect with backoff...',
          showSpinner: true,
        };
      case 'DISCONNECTED':
      case 'ERROR':
      default:
        return {
          title: '✕ MESH NOT CONNECTED',
          badgeBg: '#450A0A',
          borderColor: '#EF4444',
          textColor: '#F87171',
          subText: 'No active mesh link • Tap to inspect or retry connection',
          showSpinner: false,
        };
    }
  };

  const config = getStatusConfig();

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: config.badgeBg,
          borderColor: config.borderColor,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.topRow}>
        <View style={styles.titleContainer}>
          {config.showSpinner ? (
            <ActivityIndicator size="small" color={config.textColor} style={styles.spinner} />
          ) : null}
          <Text style={[styles.title, { color: config.textColor }]}>{config.title}</Text>
        </View>
        <Text style={styles.detailLink}>Details ➔</Text>
      </View>
      <Text style={[styles.subText, { color: config.textColor }]} numberOfLines={1}>
        {config.subText}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 4,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  spinner: {
    marginRight: 6,
  },
  title: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  detailLink: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  subText: {
    fontSize: 11,
    fontWeight: '500',
    opacity: 0.9,
  },
});
