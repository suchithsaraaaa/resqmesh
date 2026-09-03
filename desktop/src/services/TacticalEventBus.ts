/**
 * ResQMesh AI - Central Tactical Activity Event Bus
 * Provides real-time event publishing, subscription, deduplication, and ring-buffer management.
 */

export type TacticalEventType =
  | 'INCIDENT_REPORTED'
  | 'INCIDENT_RECEIVED'
  | 'INCIDENT_ACKNOWLEDGED'
  | 'INCIDENT_MERGED'
  | 'INCIDENT_DUPLICATE_DETECTED'
  | 'DUPLICATE_MATCH_DISMISSED'
  | 'INCIDENT_UPDATED'
  | 'INCIDENT_ASSIGNED'
  | 'MESH_NODE_JOINED'
  | 'MESH_PACKET_RELAYED'
  | 'MESH_NODE_DISCONNECTED'
  | 'MESH_NODE_RECONNECTED'
  | 'MESH_PEER_DISCOVERED'
  | 'MESH_HANDSHAKE_COMPLETED'
  | 'RESOURCE_REQUESTED'
  | 'RESOURCE_ACCEPTED'
  | 'RESOURCE_DISPATCHED'
  | 'RESOURCE_COMPLETED'
  | 'ALERT_BROADCAST'
  | 'ALERT_ACKNOWLEDGED'
  | 'LOCATION_UPDATED'
  | 'LOCATION_ACCURACY_CHANGED'
  | 'PHOTOS_ATTACHED'
  | 'PHOTO_CAPTURED'
  | 'AI_QUERY'
  | 'AI_RESPONSE'
  | 'SYNC_STARTED'
  | 'SYNC_COMPLETED'
  | 'SYSTEM_ONLINE'
  | 'SYSTEM_OFFLINE'
  | 'MESH_STANDALONE_INIT';

export type EventSeverity = 'CRITICAL' | 'WARNING' | 'INFO' | 'SUCCESS' | 'SYNC';

export interface TacticalActivityEvent {
  id: string;
  type: TacticalEventType;
  timestamp: string; // e.g. "19:14:32"
  rawTimestamp: number;
  severity: EventSeverity;
  nodeId?: string;
  actor?: string;
  title: string;
  description: string;
  isRemote?: boolean;
  metadata?: Record<string, any>;
}

const MAX_EVENT_HISTORY = 500;

export class TacticalEventBus {
  private static listeners: Set<(events: TacticalActivityEvent[]) => void> = new Set();
  private static seenIds: Set<string> = new Set();
  private static events: TacticalActivityEvent[] = [
    {
      id: 'sys-init-01',
      type: 'SYSTEM_ONLINE',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      rawTimestamp: Date.now(),
      severity: 'INFO',
      nodeId: 'Local-Commander',
      actor: 'Command System',
      title: 'ResQMesh AI Command Center Initialized',
      description: 'System online in offline-first mode. Mesh networking daemon active; standing by for alerts.',
      metadata: {},
    },
  ];

  static {
    // Populate initial seen IDs
    this.events.forEach((e) => this.seenIds.add(e.id));
  }

  /**
   * Format current time as HH:MM:SS
   */
  static formatTime(date: Date = new Date()): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /**
   * Publish a structured operational event to the activity stream
   */
  static publish(
    event: Omit<TacticalActivityEvent, 'id' | 'timestamp' | 'rawTimestamp'> & {
      id?: string;
      timestamp?: string;
      rawTimestamp?: number;
    }
  ) {
    const rawTime = event.rawTimestamp || Date.now();
    const id = event.id || `evt-${rawTime}-${Math.random().toString(36).slice(2, 7)}`;

    // Deduplication check
    if (this.seenIds.has(id)) {
      return;
    }
    this.seenIds.add(id);

    const fullEvent: TacticalActivityEvent = {
      ...event,
      id,
      timestamp: event.timestamp || this.formatTime(new Date(rawTime)),
      rawTimestamp: rawTime,
    };

    // Prepend to front of array (chronological, newest at top)
    this.events = [fullEvent, ...this.events];

    // Enforce memory limit
    if (this.events.length > MAX_EVENT_HISTORY) {
      this.events = this.events.slice(0, MAX_EVENT_HISTORY);
    }

    this.notify();
  }

  /**
   * Subscribe to the real-time event stream
   */
  static subscribe(listener: (events: TacticalActivityEvent[]) => void): () => void {
    this.listeners.add(listener);
    // Immediately emit current state
    listener([...this.events]);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Clears visible activity feed
   */
  static clearFeed() {
    this.events = [];
    this.notify();
  }

  /**
   * Get snapshot of events
   */
  static getEvents(): TacticalActivityEvent[] {
    return [...this.events];
  }

  private static notify() {
    const snapshot = [...this.events];
    this.listeners.forEach((fn) => {
      try {
        fn(snapshot);
      } catch {
        // Ignore subscriber error
      }
    });
  }
}
