/**
 * ResQMesh Mobile DTN Sync Engine.
 * Implements local outbox store-and-forward queue, delta sync handshakes, and Last-Writer-Wins (LWW) resolution.
 */

export interface OutboxItemMobile {
  itemId: string;
  entityType: string;
  entityId: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  payload: Record<string, any>;
  deviceClock: number;
  timestamp: number;
  status: 'PENDING' | 'ACKNOWLEDGED';
}

export function resolveLWWConflictMobile(
  localRecord: Record<string, any>,
  remoteRecord: Record<string, any>
): { winner: Record<string, any>; source: 'LOCAL' | 'REMOTE' } {
  const localTs = localRecord['timestamp'] || 0;
  const remoteTs = remoteRecord['timestamp'] || 0;

  if (remoteTs > localTs) return { winner: remoteRecord, source: 'REMOTE' };
  if (localTs > remoteTs) return { winner: localRecord, source: 'LOCAL' };

  const localClock = localRecord['deviceClock'] || 0;
  const remoteClock = remoteRecord['deviceClock'] || 0;

  if (remoteClock > localClock) return { winner: remoteRecord, source: 'REMOTE' };
  if (localClock > remoteClock) return { winner: localRecord, source: 'LOCAL' };

  const localDev = String(localRecord['deviceId'] || '');
  const remoteDev = String(remoteRecord['deviceId'] || '');

  if (remoteDev > localDev) return { winner: remoteRecord, source: 'REMOTE' };
  return { winner: localRecord, source: 'LOCAL' };
}

export class MobileSyncEngine {
  private localDeviceId: string;
  private outbox: Map<string, OutboxItemMobile> = new Map();
  private peerSyncVector: Map<string, number> = new Map();

  constructor(deviceId: string) {
    this.localDeviceId = deviceId;
  }

  public enqueueChange(
    itemId: string,
    entityType: string,
    entityId: string,
    action: OutboxItemMobile['action'],
    payload: Record<string, any>
  ): OutboxItemMobile {
    const item: OutboxItemMobile = {
      itemId,
      entityType,
      entityId,
      action,
      payload,
      deviceClock: Date.now(),
      timestamp: Date.now() / 1000,
      status: 'PENDING',
    };
    this.outbox.set(itemId, item);
    return item;
  }

  public generateDeltaBundle(sinceTimestamp: number): OutboxItemMobile[] {
    const delta: OutboxItemMobile[] = [];
    this.outbox.forEach((item) => {
      if (item.timestamp > sinceTimestamp) {
        delta.push(item);
      }
    });
    return delta;
  }

  public processSyncAck(peerId: string, ackedItemIds: string[], syncTimestamp: number): void {
    this.peerSyncVector.set(peerId, syncTimestamp);
    ackedItemIds.forEach((id) => {
      this.outbox.delete(id);
    });
  }

  public getPendingOutboxCount(): number {
    return this.outbox.size;
  }
}
