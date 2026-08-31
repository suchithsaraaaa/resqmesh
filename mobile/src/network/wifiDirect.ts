/**
 * ResQMesh Mobile Wi-Fi Direct (P2P) High-Throughput Transport Manager.
 * Manages Wi-Fi P2P Group Owner / Client roles, peer connection, and high-speed data stream socket transfers.
 */

import { Packet, PacketData } from './protocol';

export interface WiFiDirectPeer {
  deviceAddress: string;
  deviceName: string;
  isGroupOwner: boolean;
  status: 'available' | 'invited' | 'connected' | 'failed' | 'unavailable';
  groupFormed: boolean;
  groupOwnerAddress?: string;
}

export type WiFiPeerCallback = (peers: WiFiDirectPeer[]) => void;
export type WiFiPacketCallback = (packet: Packet, senderIp: string) => void;

export class MobileWiFiDirectManager {
  private localDeviceId: string;
  private isGroupOwner: boolean = false;
  private groupOwnerAddress: string | null = null;
  private discoveredPeers: Map<string, WiFiDirectPeer> = new Map();
  private peerCallbacks: WiFiPeerCallback[] = [];
  private packetCallbacks: WiFiPacketCallback[] = [];
  private port: number = 8002;

  constructor(deviceId: string, port: number = 8002) {
    this.localDeviceId = deviceId;
    this.port = port;
  }

  public onPeersDiscovered(callback: WiFiPeerCallback): void {
    this.peerCallbacks.push(callback);
  }

  public onPacketReceived(callback: WiFiPacketCallback): void {
    this.packetCallbacks.push(callback);
  }

  public async startPeerDiscovery(): Promise<boolean> {
    return true;
  }

  public async stopPeerDiscovery(): Promise<void> {
    this.discoveredPeers.clear();
  }

  public async createGroup(): Promise<boolean> {
    this.isGroupOwner = true;
    this.groupOwnerAddress = '192.168.49.1'; // Standard Wi-Fi Direct GO default IP
    return true;
  }

  public async removeGroup(): Promise<void> {
    this.isGroupOwner = false;
    this.groupOwnerAddress = null;
  }

  public async connectToPeer(deviceAddress: string): Promise<boolean> {
    const peer = this.discoveredPeers.get(deviceAddress);
    if (peer) {
      peer.status = 'connected';
      return true;
    }
    return false;
  }

  public updateDiscoveredPeers(peerList: WiFiDirectPeer[]): void {
    this.discoveredPeers.clear();
    peerList.forEach((p) => this.discoveredPeers.set(p.deviceAddress, p));
    this.peerCallbacks.forEach((cb) => cb(peerList));
  }

  public getDiscoveredPeers(): WiFiDirectPeer[] {
    return Array.from(this.discoveredPeers.values());
  }

  public handleIncomingPayload(rawJson: string, senderIp: string): void {
    try {
      const data: PacketData = JSON.parse(rawJson);
      const packet = Packet.fromDict(data);
      if (packet.verifyChecksum()) {
        this.packetCallbacks.forEach((cb) => cb(packet, senderIp));
      }
    } catch (e) {
      // Ignore malformed packet data
    }
  }
}
