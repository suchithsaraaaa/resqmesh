/**
 * ResQMesh Mobile Mesh Network & Discovery Service.
 * 
 * Provides real-time mesh connection management, multi-candidate discovery,
 * reciprocal peer registration, keep-alive heartbeat, store-and-forward report sync,
 * and truthful state machine transitions for Android / BlueStacks field nodes.
 */

import { Platform } from 'react-native';
import { generateUniqueId } from '../utils/id';
import db from '../db/sqlite';

export type MobileMeshState =
  | 'INITIALIZING'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'STANDALONE'
  | 'RECONNECTING'
  | 'DISCONNECTED'
  | 'ERROR';

export interface ConnectedPeer {
  nodeId: string;
  name: string;
  role: string;
  ipAddress: string;
  port: number;
  latencyMs: number;
  lastSeen: number;
  transport: string;
}

export interface MeshStatusInfo {
  state: MobileMeshState;
  nodeId: string;
  nodeName: string;
  role: string;
  localIp: string;
  activePeerCount: number;
  peers: ConnectedPeer[];
  connectedCommander: ConnectedPeer | null;
  lastHandshakeTime: number | null;
  lastSyncTime: number | null;
  pendingOutboxCount: number;
  lastError: string | null;
  candidateIps: string[];
}

type MeshStateListener = (status: MeshStatusInfo) => void;

export class MeshService {
  private static instance: MeshService | null = null;

  public nodeId: string;
  public nodeName: string;
  public role: string;
  public localIp: string;
  public apiPort: number;

  private state: MobileMeshState = 'INITIALIZING';
  private peers: Map<string, ConnectedPeer> = new Map();
  private connectedCommander: ConnectedPeer | null = null;
  private lastHandshakeTime: number | null = null;
  private lastSyncTime: number | null = null;
  private lastError: string | null = null;

  private manualCommanderIp: string | null = null;
  private heartbeatInterval: any = null;
  private syncInterval: any = null;
  private isConnecting: boolean = false;
  private consecutiveFailures: number = 0;
  private listeners: Set<MeshStateListener> = new Set();

  private constructor() {
    this.nodeId = `node-mobile-${Math.random().toString(36).slice(2, 8)}`;
    this.nodeName = `Field-Responder-${this.nodeId.slice(-4).toUpperCase()}`;
    this.role = 'responder';
    this.localIp = Platform.OS === 'android' ? '10.0.2.15' : '127.0.0.1';
    this.apiPort = 8001;
  }

  public static getInstance(): MeshService {
    if (!MeshService.instance) {
      MeshService.instance = new MeshService();
    }
    return MeshService.instance;
  }

  /**
   * Initialize mesh subsystem and begin automatic discovery.
   */
  public async init(): Promise<void> {
    this.state = 'CONNECTING';
    this.notifyListeners();

    // Start background loops
    this.startHeartbeatLoop();
    this.startSyncLoop();

    // Execute initial discovery probe
    await this.discoverAndConnect();
  }

  /**
   * Subscribe to live mesh status updates.
   */
  public subscribe(listener: MeshStateListener): () => void {
    this.listeners.add(listener);
    try {
      listener(this.getStatus());
    } catch (err) {
      console.debug('Initial subscriber notice:', err);
    }
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get current comprehensive mesh diagnostic status.
   */
  public getStatus(): MeshStatusInfo {
    const peersList = Array.from(this.peers.values());
    return {
      state: this.state,
      nodeId: this.nodeId,
      nodeName: this.nodeName,
      role: this.role,
      localIp: this.localIp,
      activePeerCount: peersList.length,
      peers: peersList,
      connectedCommander: this.connectedCommander,
      lastHandshakeTime: this.lastHandshakeTime,
      lastSyncTime: this.lastSyncTime,
      pendingOutboxCount: 0,
      lastError: this.lastError,
      candidateIps: this.getCandidateIps(),
    };
  }

  /**
   * Candidate IPs to probe for Command Center desktop:
   * 1. Manual user override if set.
   * 2. BlueStacks / Android Emulator host gateway (10.0.2.2:8000).
   * 3. Standard LAN / Wi-Fi Hotspot gateways (192.168.1.1, 192.168.43.1, 192.168.0.1, 192.168.137.1).
   * 4. Localhost fallback (127.0.0.1:8000).
   */
  public getCandidateIps(): string[] {
    const candidates: string[] = [];
    if (this.manualCommanderIp && this.manualCommanderIp.trim()) {
      candidates.push(this.manualCommanderIp.trim());
    }
    // BlueStacks / Emulator default host alias
    candidates.push('10.0.2.2:8000');
    // Local subnet gateways
    candidates.push('192.168.1.1:8000');
    candidates.push('192.168.43.1:8000'); // Android Wi-Fi Hotspot gateway
    candidates.push('192.168.137.1:8000'); // Windows Hosted Network hotspot
    candidates.push('192.168.0.1:8000');
    candidates.push('127.0.0.1:8000');

    // Filter duplicates
    return Array.from(new Set(candidates));
  }

  /**
   * Set a manual Commander IP address or hostname.
   */
  public setManualCommanderIp(ip: string | null): void {
    this.manualCommanderIp = ip;
    this.notifyListeners();
  }

  /**
   * Perform discovery probe against candidates and execute reciprocal registration.
   */
  public async discoverAndConnect(): Promise<boolean> {
    if (this.isConnecting) {
      return false;
    }
    this.isConnecting = true;
    this.lastError = null;

    this.state = this.state === 'CONNECTED' ? 'RECONNECTING' : (this.consecutiveFailures > 0 ? 'RECONNECTING' : 'CONNECTING');
    this.notifyListeners();

    const candidates = this.getCandidateIps();

    for (const candidate of candidates) {
      const url = candidate.startsWith('http://') || candidate.startsWith('https://') ? candidate : `http://${candidate}`;
      const cleanCandidate = candidate.replace(/^https?:\/\//, '').replace(/\/+$/, '');
      const ipPart = cleanCandidate.split(':')[0];
      const portPart = parseInt(cleanCandidate.split(':')[1] || '8000', 10);

      try {
        const startTime = Date.now();
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const statusRes = await fetch(`${url}/node/status`, {
          method: 'GET',
          headers: { 'User-Agent': 'ResQMesh-Mobile/1.0', Accept: 'application/json' },
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (statusRes.ok) {
          const statusData = await statusRes.json();
          const latencyMs = Math.max(1, Date.now() - startTime);

          // Found Command Center node! Proceed to reciprocal handshake / registration
          const regRes = await fetch(`${url}/peers/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'User-Agent': 'ResQMesh-Mobile/1.0',
            },
            body: JSON.stringify({
              node_id: this.nodeId,
              name: this.nodeName,
              role: this.role,
              ip_address: this.localIp,
              api_port: this.apiPort,
              latency_ms: latencyMs,
            }),
          });

          if (regRes.ok) {
            const regData = await regRes.json();
            const cmdNode = regData.my_node || statusData;

            const commanderPeer: ConnectedPeer = {
              nodeId: cmdNode.node_id || statusData.node_id || 'commander-01',
              name: cmdNode.name || statusData.node_name || 'HQ-Command-01',
              role: cmdNode.role || statusData.role || 'commander',
              ipAddress: ipPart,
              port: portPart,
              latencyMs,
              lastSeen: Date.now(),
              transport: candidate.includes('10.0.2.2') ? 'BlueStacks Virtual Bridge (HTTP/TCP)' : 'LAN (HTTP/TCP)',
            };

            this.peers.set(commanderPeer.nodeId, commanderPeer);
            this.connectedCommander = commanderPeer;
            this.state = 'CONNECTED';
            this.consecutiveFailures = 0;
            this.lastHandshakeTime = Date.now();
            this.lastError = null;

            this.notifyListeners();
            this.isConnecting = false;

            // Immediately flush pending reports
            this.syncAllPendingReports().catch(() => {});
            return true;
          }
        }
      } catch (err: any) {
        // Candidate unreachable, continue to next candidate
      }
    }

    // No candidates responded
    this.consecutiveFailures += 1;
    this.state = 'STANDALONE';
    this.peers.clear();
    this.connectedCommander = null;
    this.isConnecting = false;
    this.notifyListeners();
    return false;
  }

  /**
   * Synchronize all unsynced local SQLite reports to the Command Center.
   */
  public async syncAllPendingReports(): Promise<number> {
    if (!this.connectedCommander || this.state !== 'CONNECTED') {
      return 0;
    }

    const commanderUrl = `http://${this.connectedCommander.ipAddress}:${this.connectedCommander.port}`;
    let syncedCount = 0;

    try {
      await db.init();
      const reports = await db.reports.list();

      for (const rep of reports) {
        try {
          const res = await fetch(`${commanderUrl}/reports/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'User-Agent': 'ResQMesh-Mobile/1.0',
            },
            body: JSON.stringify({
              report_id: rep.report_id,
              device_id: rep.device_id || this.nodeId,
              user_id: rep.user_id || 'responder-01',
              timestamp: rep.timestamp || new Date().toISOString(),
              latitude: Number(rep.latitude) || 0.0,
              longitude: Number(rep.longitude) || 0.0,
              description: rep.description || '',
              category: rep.category || 'general',
              attachments: rep.attachments || null,
              device_clock: rep.device_clock || Date.now(),
            }),
          });

          if (res.ok) {
            syncedCount += 1;
          }
        } catch {
          // Individual sync failed, continue
        }
      }

      if (syncedCount > 0) {
        this.lastSyncTime = Date.now();
        this.notifyListeners();
      }
    } catch (err: any) {
      this.lastError = `Sync error: ${err.message}`;
    }

    return syncedCount;
  }

  /**
   * Sync a newly created report immediately if connected.
   */
  public async syncNewReport(report: any): Promise<boolean> {
    if (!this.connectedCommander || this.state !== 'CONNECTED') {
      return false;
    }

    const commanderUrl = `http://${this.connectedCommander.ipAddress}:${this.connectedCommander.port}`;
    try {
      const res = await fetch(`${commanderUrl}/reports/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'ResQMesh-Mobile/1.0',
        },
        body: JSON.stringify({
          report_id: report.report_id,
          device_id: report.device_id || this.nodeId,
          user_id: report.user_id || 'responder-01',
          timestamp: report.timestamp || new Date().toISOString(),
          latitude: Number(report.latitude) || 0.0,
          longitude: Number(report.longitude) || 0.0,
          description: report.description || '',
          category: report.category || 'general',
          attachments: report.attachments || null,
          device_clock: report.device_clock || Date.now(),
        }),
      });

      if (res.ok) {
        this.lastSyncTime = Date.now();
        this.notifyListeners();
        return true;
      }
    } catch (e) {
      // Offline fallback: report remains persisted in SQLite
    }
    return false;
  }

  /**
   * Periodic keep-alive heartbeat loop.
   */
  private startHeartbeatLoop(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(async () => {
      if (this.state === 'CONNECTED' && this.connectedCommander) {
        const url = `http://${this.connectedCommander.ipAddress}:${this.connectedCommander.port}`;
        try {
          const startTime = Date.now();
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 2000);

          const res = await fetch(`${url}/node/status`, {
            method: 'GET',
            signal: controller.signal,
          });
          clearTimeout(timeoutId);

          if (res.ok) {
            this.connectedCommander.latencyMs = Math.max(1, Date.now() - startTime);
            this.connectedCommander.lastSeen = Date.now();
            this.consecutiveFailures = 0;
            this.notifyListeners();
            return;
          }
        } catch {
          // Heartbeat missed
        }

        this.consecutiveFailures += 1;
        if (this.consecutiveFailures >= 2) {
          this.state = 'RECONNECTING';
          this.notifyListeners();
          this.discoverAndConnect().catch(() => {});
        }
      } else if (this.state === 'STANDALONE' || this.state === 'RECONNECTING' || this.state === 'DISCONNECTED') {
        // Periodically attempt to find Command Center
        this.discoverAndConnect().catch(() => {});
      }
    }, 5000);
  }

  /**
   * Periodic store-and-forward outbox sync loop.
   */
  private startSyncLoop(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.syncInterval = setInterval(() => {
      if (this.state === 'CONNECTED') {
        this.syncAllPendingReports().catch(() => {});
      }
    }, 12000);
  }

  private notifyListeners(): void {
    const status = this.getStatus();
    this.listeners.forEach((listener) => {
      try {
        listener(status);
      } catch (err) {
        console.error('Error notifying mesh listener:', err);
      }
    });
  }

  /**
   * Stop background loops and clean up.
   */
  public destroy(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
    this.listeners.clear();
    this.peers.clear();
    this.connectedCommander = null;
    this.isConnecting = false;
    this.consecutiveFailures = 0;
    this.state = 'DISCONNECTED';
  }
}

export default MeshService;
