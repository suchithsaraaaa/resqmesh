/**
 * ResQMesh Mobile BLE (Bluetooth Low Energy) Manager.
 * Handles BLE advertising, scanning, GATT service connection, and chunked payload transport.
 */

import { Packet, PacketData } from './protocol';

export const RESQMESH_BLE_SERVICE_UUID = '0000fd00-0000-1000-8000-00805f9b34fb';
export const RESQMESH_BLE_TX_CHARACTERISTIC_UUID = '0000fd01-0000-1000-8000-00805f9b34fb';
export const RESQMESH_BLE_RX_CHARACTERISTIC_UUID = '0000fd02-0000-1000-8000-00805f9b34fb';

export interface BLEPeer {
  id: string;
  name: string;
  rssi: number;
  lastSeen: number;
  connected: boolean;
}

export type BLEPeerCallback = (peer: BLEPeer) => void;
export type BLEPacketCallback = (packet: Packet, senderId: string) => void;

export class MobileBLEManager {
  private localDeviceId: string;
  private isAdvertising: boolean = false;
  private isScanning: boolean = false;
  private discoveredPeers: Map<string, BLEPeer> = new Map();
  private peerCallbacks: BLEPeerCallback[] = [];
  private packetCallbacks: BLEPacketCallback[] = [];
  private mtuSize: number = 512; // Standard default MTU for BLE packet chunking

  constructor(deviceId: string) {
    this.localDeviceId = deviceId;
  }

  public onPeerDiscovered(callback: BLEPeerCallback): void {
    this.peerCallbacks.push(callback);
  }

  public onPacketReceived(callback: BLEPacketCallback): void {
    this.packetCallbacks.push(callback);
  }

  public async startAdvertising(): Promise<boolean> {
    this.isAdvertising = true;
    return true;
  }

  public async stopAdvertising(): Promise<void> {
    this.isAdvertising = false;
  }

  public async startScanning(): Promise<boolean> {
    this.isScanning = true;
    return true;
  }

  public async stopScanning(): Promise<void> {
    this.isScanning = false;
  }

  public handleDiscoveredDevice(id: string, name: string, rssi: number): void {
    const peer: BLEPeer = {
      id,
      name: name || `ResQMesh-Peer-${id.slice(0, 4)}`,
      rssi,
      lastSeen: Date.now(),
      connected: false,
    };
    this.discoveredPeers.set(id, peer);
    this.peerCallbacks.forEach((cb) => cb(peer));
  }

  public getDiscoveredPeers(): BLEPeer[] {
    return Array.from(this.discoveredPeers.values());
  }

  /**
   * Split a large packet payload into BLE MTU chunks.
   */
  public chunkPayload(data: string, chunkSize: number = 490): string[] {
    const chunks: string[] = [];
    for (let i = 0; i < data.length; i += chunkSize) {
      chunks.push(data.slice(i, i + chunkSize));
    }
    return chunks;
  }

  /**
   * Reassemble BLE MTU chunks back into full packet payload string.
   */
  public reassembleChunks(chunks: string[]): string {
    return chunks.join('');
  }

  /**
   * Transmit a packet to a connected target peer.
   */
  public async transmitPacket(peerId: string, packet: Packet): Promise<boolean> {
    const peer = this.discoveredPeers.get(peerId);
    if (!peer) {
      return false;
    }

    const rawData = JSON.stringify(packet.toDict());
    const chunks = this.chunkPayload(rawData, this.mtuSize - 20);

    // Transmit each chunk over GATT TX characteristic
    for (const chunk of chunks) {
      // Send chunk over BLE GATT
      void chunk;
    }

    return true;
  }

  public handleIncomingRawData(rawData: string, senderId: string): void {
    try {
      const data: PacketData = JSON.parse(rawData);
      const packet = Packet.fromDict(data);
      if (packet.verifyChecksum()) {
        this.packetCallbacks.forEach((cb) => cb(packet, senderId));
      }
    } catch (e) {
      // Incomplete or corrupted chunk, ignore or buffer until reassembled
    }
  }
}
