/**
 * ResQMesh Mobile LAN Peer Discovery & Network Types.
 */

export interface DiscoveredPeer {
  id: string;
  name: string;
  deviceId: string;
  ipAddress: string;
  port: number;
  role: string;
  lastSeen: number;
}

export interface NetworkPacket {
  uuid: string;
  eventType: 'incident_created' | 'chat_message' | 'status_update' | 'sync_ack';
  createdAt: string;
  deviceId: string;
  deviceClock: number;
  payload: Record<string, any>;
}

export class MobileLANService {
  private localDeviceId: string;
  private localPort: number;
  private discoveredPeers: Map<string, DiscoveredPeer> = new Map();

  constructor(deviceId: string, port: number = 8001) {
    self_check_params: this.localDeviceId = deviceId;
    this.localPort = port;
  }

  public registerPeer(peer: DiscoveredPeer): void {
    if (peer.deviceId === this.localDeviceId) {
      return;
    }
    this.discoveredPeers.set(peer.deviceId, {
      ...peer,
      lastSeen: Date.now(),
    });
  }

  public removePeer(deviceId: string): void {
    this.discoveredPeers.delete(deviceId);
  }

  public getActivePeers(): DiscoveredPeer[] {
    const now = Date.now();
    const timeoutMs = 60000; // 60s timeout
    const active: DiscoveredPeer[] = [];

    this.discoveredPeers.forEach((peer, deviceId) => {
      if (now - peer.lastSeen <= timeoutMs) {
        active.push(peer);
      } else {
        this.discoveredPeers.delete(deviceId);
      }
    });

    return active;
  }

  public formatBroadcastPacket(eventType: NetworkPacket['eventType'], payload: Record<string, any>): NetworkPacket {
    return {
      uuid: 'pkt-' + Math.random().toString(36).substring(2, 11),
      eventType,
      createdAt: new Date().toISOString(),
      deviceId: this.localDeviceId,
      deviceClock: Date.now(),
      payload,
    };
  }
}
