/**
 * ResQMesh Mobile Multi-Hop Mesh Router.
 * Handles duplicate packet suppression, TTL hop count management, and multi-hop relay forwarding.
 */

import { Packet, PacketData } from './protocol';

export const DEFAULT_MOBILE_TTL = 5;
export const SEEN_CACHE_EXPIRY_MS = 300000; // 5 minutes

export interface RoutingTableEntry {
  destId: string;
  nextHopId: string;
  hopCount: number;
  lastUpdated: number;
}

export interface RouterDecision {
  shouldProcessLocally: boolean;
  shouldForward: boolean;
  updatedPacket: Packet | null;
  reason: 'DUPLICATE_PACKET' | 'TTL_EXPIRED' | 'PROCESSED_LOCALLY_TTL_EXPIRED' | 'OK_FORWARD';
}

export class MobileMeshRouter {
  private localDeviceId: string;
  private defaultTTL: number;
  private seenPackets: Map<string, number> = new Map();
  private routingTable: Map<string, RoutingTableEntry> = new Map();

  constructor(deviceId: string, defaultTTL: number = DEFAULT_MOBILE_TTL) {
    this.localDeviceId = deviceId;
    this.defaultTTL = defaultTTL;
  }

  public updateRoute(destId: string, nextHopId: string, hopCount: number): void {
    if (destId === this.localDeviceId) return;

    const existing = this.routingTable.get(destId);
    if (!existing || hopCount <= existing.hopCount) {
      this.routingTable.set(destId, {
        destId,
        nextHopId,
        hopCount,
        lastUpdated: Date.now(),
      });
    }
  }

  public processIncomingPacket(packet: Packet, arrivedFromId: string): RouterDecision {
    const packetId = packet.packetId;
    const now = Date.now();

    // 1. Duplicate Suppression Check
    this.cleanupSeenCache();
    if (this.seenPackets.has(packetId)) {
      return {
        shouldProcessLocally: false,
        shouldForward: false,
        updatedPacket: null,
        reason: 'DUPLICATE_PACKET',
      };
    }

    this.seenPackets.set(packetId, now);

    // Update reverse route back to sender
    if (packet.senderId !== this.localDeviceId) {
      this.updateRoute(packet.senderId, arrivedFromId, 1);
    }

    const targetDest = packet.payload['target_device_id'];
    const isForMe = !targetDest || targetDest === this.localDeviceId;

    // 2. TTL Check
    const currentTTL = packet.payload['ttl'] ?? this.defaultTTL;
    const currentHops = packet.payload['hop_count'] ?? 0;

    if (currentTTL <= 1) {
      return {
        shouldProcessLocally: isForMe,
        shouldForward: false,
        updatedPacket: null,
        reason: isForMe ? 'PROCESSED_LOCALLY_TTL_EXPIRED' : 'TTL_EXPIRED',
      };
    }

    // 3. Prepare Packet for Forwarding
    const forwardPayload = {
      ...packet.payload,
      ttl: currentTTL - 1,
      hop_count: currentHops + 1,
    };

    const forwardPacket = new Packet({
      packetId: packet.packetId,
      senderId: packet.senderId,
      packetType: packet.packetType,
      seqNum: packet.seqNum,
      totalFrags: packet.totalFrags,
      fragIdx: packet.fragIdx,
      payload: forwardPayload,
      timestamp: packet.timestamp,
    });

    return {
      shouldProcessLocally: isForMe,
      shouldForward: true,
      updatedPacket: forwardPacket,
      reason: 'OK_FORWARD',
    };
  }

  private cleanupSeenCache(): void {
    const now = Date.now();
    this.seenPackets.forEach((timestamp, packetId) => {
      if (now - timestamp > SEEN_CACHE_EXPIRY_MS) {
        this.seenPackets.delete(packetId);
      }
    });
  }

  public getKnownRoutes(): RoutingTableEntry[] {
    return Array.from(this.routingTable.values());
  }
}
