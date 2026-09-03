/**
 * ResQMesh Mobile — Detailed Mesh Diagnostics & Peer Inspector Modal.
 * 
 * Provides full situational transparency into local node identity,
 * peer connections, live connection diagnostics, custom Commander IP pairing,
 * and manual sync controls.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { MeshStatusInfo, MeshService } from '../network/meshService';

interface Props {
  visible: boolean;
  status: MeshStatusInfo;
  onClose: () => void;
}

export default function MeshDetailModal({ visible, status, onClose }: Props) {
  const [manualIp, setManualIp] = useState(status.manualCommanderIp || '');
  const [isRetrying, setIsRetrying] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const meshService = MeshService.getInstance();

  const handleRetry = async () => {
    setIsRetrying(true);
    setTestResult(null);
    try {
      const connected = await meshService.discoverAndConnect();
      if (connected) {
        Alert.alert('✓ Mesh Connected', 'Successfully discovered and registered with Command Center!');
      } else {
        Alert.alert(
          'Standby / Offline',
          `No nearby Command Center nodes responded.\n\nLast probe: ${meshService.getStatus().lastProbeResult || 'Unreachable'}\n\nLocal offline mesh is operational.`
        );
      }
    } catch (e: any) {
      Alert.alert('Probe Notice', e.message || 'Discovery probe finished.');
    } finally {
      setIsRetrying(false);
    }
  };

  const handleTestAndPair = async () => {
    const target = manualIp.trim();
    if (!target) {
      Alert.alert('Invalid Address', 'Please enter a valid IP address (e.g. 192.168.68.109 or 192.168.137.1:8000).');
      return;
    }

    setIsRetrying(true);
    setTestResult('Probing target...');

    // 1. Direct TCP Probe to /node/status
    const probe = await meshService.testDirectConnection(target);
    if (!probe.success) {
      setIsRetrying(false);
      setTestResult(`❌ FAILED: ${probe.error}`);
      Alert.alert(
        'Connection Failed',
        `Unable to reach Command Center at ${target}.\n\nReason: ${probe.error}\n\nPlease check:\n1. Windows Laptop & Phone are on the same Wi-Fi or Hotspot.\n2. Windows Command Center is running.\n3. Port 8000 is open.`
      );
      return;
    }

    // 2. Set manual IP and execute full reciprocal registration
    meshService.setManualCommanderIp(target);
    const connected = await meshService.discoverAndConnect();
    setIsRetrying(false);

    if (connected) {
      setTestResult(`✓ CONNECTED: ${probe.data?.name || 'Commander'} (${probe.latencyMs}ms)`);
      Alert.alert('✓ Connected to Commander', `Successfully registered with ${target} (${probe.data?.name || 'Commander'})!`);
    } else {
      setTestResult(`❌ Registration Failed`);
      Alert.alert('Registration Error', `Reached ${target} but peer registration was not completed.`);
    }
  };

  const handleClearManualIp = () => {
    meshService.setManualCommanderIp(null);
    setManualIp('');
    setTestResult(null);
    Alert.alert('Reset', 'Manual Commander IP cleared. Using automatic candidate discovery.');
  };

  const handleForceSync = async () => {
    setIsSyncing(true);
    try {
      const synced = await meshService.syncAllPendingReports();
      Alert.alert('Sync Complete', `Synchronized ${synced} report(s) to Command Center.`);
    } catch (e: any) {
      Alert.alert('Sync Error', e.message || 'Failed to sync reports.');
    } finally {
      setIsSyncing(false);
    }
  };

  const formatTs = (ts: number | null) => {
    if (!ts) return 'None';
    return new Date(ts).toLocaleTimeString();
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>🕸 Mesh Diagnostics & Peers</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Text style={styles.closeBtnText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollBody} showsVerticalScrollIndicator={false}>
            {/* Status Pill Card */}
            <View style={styles.card}>
              <Text style={styles.cardSectionTitle}>OPERATIONAL STATE</Text>
              <View style={styles.stateRow}>
                <View
                  style={[
                    styles.stateIndicatorDot,
                    {
                      backgroundColor:
                        status.state === 'CONNECTED'
                          ? '#10B981'
                          : status.state === 'STANDALONE'
                          ? '#F59E0B'
                          : status.state === 'CONNECTING' || status.state === 'RECONNECTING'
                          ? '#38BDF8'
                          : '#EF4444',
                    },
                  ]}
                />
                <Text style={styles.stateText}>{status.state}</Text>
              </View>
              <Text style={styles.stateDetailText}>
                {status.state === 'CONNECTED'
                  ? 'Active bidirectional mesh transport established with Command Center.'
                  : status.state === 'STANDALONE'
                  ? 'Local offline node operational with local SQLite storage. Standing by for nearby peers.'
                  : status.state === 'CONNECTING' || status.state === 'RECONNECTING'
                  ? 'Probing local LAN interfaces and candidates...'
                  : 'Disconnected from mesh network.'}
              </Text>
            </View>

            {/* Connection Diagnostics (Explicit Real-Time Debug) */}
            <View style={styles.card}>
              <Text style={styles.cardSectionTitle}>CONNECTION DIAGNOSTICS</Text>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Node:</Text>
                <Text style={styles.infoValue}>{status.nodeName}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Status:</Text>
                <Text style={[styles.infoValue, { color: status.state === 'CONNECTED' ? '#10B981' : '#F59E0B' }]}>
                  {status.state}
                </Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Command Center:</Text>
                <Text style={styles.infoValue}>
                  {status.connectedCommander ? status.connectedCommander.name : 'None (Searching)'}
                </Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Target:</Text>
                <Text style={styles.infoValueMonospace}>
                  {status.connectedCommander
                    ? `${status.connectedCommander.ipAddress}:${status.connectedCommander.port}`
                    : status.lastProbeTarget || 'None'}
                </Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Transport:</Text>
                <Text style={styles.infoValue}>{status.activeTransport || 'HTTP/TCP'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Discovery:</Text>
                <Text style={styles.infoValue}>{status.discoveryMode || 'Standing By'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Last Probe:</Text>
                <Text style={styles.infoValue}>{formatTs(status.lastProbeTime)}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Last Result:</Text>
                <Text
                  style={[
                    styles.infoValue,
                    {
                      color:
                        status.lastProbeResult?.includes('200') || status.lastProbeResult?.includes('OK')
                          ? '#10B981'
                          : '#F87171',
                      fontSize: 11,
                    },
                  ]}
                  numberOfLines={1}
                >
                  {status.lastProbeResult || 'None'}
                </Text>
              </View>
              {status.lastError ? (
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Last Error:</Text>
                  <Text style={[styles.infoValue, { color: '#EF4444', fontSize: 11 }]} numberOfLines={2}>
                    {status.lastError}
                  </Text>
                </View>
              ) : null}
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Heartbeat:</Text>
                <Text style={styles.infoValue}>
                  {status.state === 'CONNECTED' && status.connectedCommander
                    ? `Healthy (${status.connectedCommander.latencyMs} ms)`
                    : 'Inactive'}
                </Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Last Successful Sync:</Text>
                <Text style={styles.infoValue}>{formatTs(status.lastSyncTime)}</Text>
              </View>
            </View>

            {/* Custom Commander IP Pair */}
            <View style={styles.card}>
              <Text style={styles.cardSectionTitle}>MANUAL COMMANDER IP PAIRING</Text>
              <Text style={styles.pairHelpText}>
                Enter the Windows Command Center LAN or Hotspot IPv4 address (e.g. 192.168.68.109 or 192.168.137.1):
              </Text>
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.ipInput}
                  placeholder="e.g. 192.168.68.109:8000"
                  placeholderTextColor="#64748B"
                  value={manualIp}
                  onChangeText={setManualIp}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <TouchableOpacity
                  style={styles.pairBtn}
                  onPress={handleTestAndPair}
                  disabled={isRetrying}
                >
                  <Text style={styles.pairBtnText}>Pair</Text>
                </TouchableOpacity>
                {status.manualCommanderIp ? (
                  <TouchableOpacity
                    style={styles.clearBtn}
                    onPress={handleClearManualIp}
                    disabled={isRetrying}
                  >
                    <Text style={styles.clearBtnText}>✕</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
              {testResult ? (
                <Text
                  style={[
                    styles.testResultText,
                    { color: testResult.startsWith('✓') ? '#10B981' : testResult.startsWith('❌') ? '#EF4444' : '#38BDF8' },
                  ]}
                >
                  {testResult}
                </Text>
              ) : null}
            </View>

            {/* Connected Commander & Peers */}
            <View style={styles.card}>
              <Text style={styles.cardSectionTitle}>
                CONNECTED PEERS ({status.activePeerCount})
              </Text>
              {status.peers.length > 0 ? (
                status.peers.map((peer, idx) => (
                  <View key={peer.nodeId || idx} style={styles.peerItem}>
                    <View style={styles.peerHeaderRow}>
                      <Text style={styles.peerName}>🛡️ {peer.name}</Text>
                      <Text style={styles.peerLatency}>{peer.latencyMs} ms</Text>
                    </View>
                    <Text style={styles.peerSub}>
                      {peer.role.toUpperCase()} • {peer.ipAddress}:{peer.port}
                    </Text>
                    <Text style={styles.peerTransport}>Transport: {peer.transport}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.emptyPeersText}>
                  No active peers discovered yet. Reports are safely persisted offline in SQLite.
                </Text>
              )}
            </View>
          </ScrollView>

          {/* Action Buttons Footer */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.actionBtn, styles.retryBtn]}
              onPress={handleRetry}
              disabled={isRetrying}
            >
              {isRetrying ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Text style={styles.actionBtnText}>🔄 Probe & Connect</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionBtn, styles.syncBtn]}
              onPress={handleForceSync}
              disabled={isSyncing || status.state !== 'CONNECTED'}
            >
              {isSyncing ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Text style={styles.actionBtnText}>⚡ Force Sync</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#0D1B2A',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderWidth: 1,
    borderColor: '#1E293B',
    maxHeight: '90%',
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  headerTitle: {
    color: '#38BDF8',
    fontSize: 16,
    fontWeight: '700',
  },
  closeBtn: {
    padding: 6,
    borderRadius: 8,
    backgroundColor: '#1E293B',
  },
  closeBtnText: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '700',
  },
  scrollBody: {
    padding: 16,
  },
  card: {
    backgroundColor: '#111E33',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1E293B',
    padding: 14,
    marginBottom: 12,
  },
  cardSectionTitle: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 8,
  },
  stateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  stateIndicatorDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  stateText: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '800',
  },
  stateDetailText: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 3,
  },
  infoLabel: {
    color: '#94A3B8',
    fontSize: 11,
  },
  infoValue: {
    color: '#F8FAFC',
    fontSize: 11,
    fontWeight: '600',
  },
  infoValueMonospace: {
    color: '#38BDF8',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  peerItem: {
    backgroundColor: '#1A2942',
    padding: 10,
    borderRadius: 8,
    marginBottom: 6,
    borderLeftWidth: 3,
    borderLeftColor: '#10B981',
  },
  peerHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  peerName: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '700',
  },
  peerLatency: {
    color: '#10B981',
    fontSize: 11,
    fontWeight: '700',
  },
  peerSub: {
    color: '#94A3B8',
    fontSize: 11,
    marginTop: 2,
  },
  peerTransport: {
    color: '#64748B',
    fontSize: 10,
    marginTop: 2,
  },
  emptyPeersText: {
    color: '#64748B',
    fontSize: 12,
    fontStyle: 'italic',
  },
  pairHelpText: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 8,
    lineHeight: 15,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ipInput: {
    flex: 1,
    backgroundColor: '#0A1220',
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: '#F8FAFC',
    fontSize: 12,
    marginRight: 8,
  },
  pairBtn: {
    backgroundColor: '#0284C7',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 8,
  },
  pairBtnText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
  },
  clearBtn: {
    backgroundColor: '#334155',
    paddingHorizontal: 10,
    paddingVertical: 9,
    borderRadius: 8,
    marginLeft: 4,
  },
  clearBtnText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
  },
  testResultText: {
    fontSize: 11,
    marginTop: 6,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 8,
    gap: 10,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retryBtn: {
    backgroundColor: '#0284C7',
  },
  syncBtn: {
    backgroundColor: '#059669',
  },
  actionBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
});
