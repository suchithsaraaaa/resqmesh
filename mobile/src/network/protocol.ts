/**
 * ResQMesh Reliable Messaging Protocol for React Native Mobile Client.
 * Implements CRC32 checksums, sequence numbering, stream framing, and ACK tracking.
 */

export const PACKET_TYPE_DATA = 'DATA';
export const PACKET_TYPE_ACK = 'ACK';
export const PACKET_TYPE_HEARTBEAT = 'HEARTBEAT';

export interface PacketData {
  packet_id: string;
  sender_id: string;
  packet_type: string;
  seq_num: number;
  total_frags: number;
  frag_idx: number;
  checksum: string;
  timestamp: number;
  payload: Record<string, any>;
}

// Basic CRC32 implementation for React Native / TS
export function computeCRC32(str: string): string {
  let crc = 0 ^ (-1);
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    crc = (crc >>> 8) ^ crcTable[(crc ^ code) & 0xff];
  }
  const result = (crc ^ (-1)) >>> 0;
  return result.toString(16).padStart(8, '0');
}

const crcTable: number[] = (() => {
  const table: number[] = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c;
  }
  return table;
})();

export class Packet {
  public packetId: string;
  public senderId: string;
  public packetType: string;
  public seqNum: number;
  public totalFrags: number;
  public fragIdx: number;
  public checksum: string;
  public timestamp: number;
  public payload: Record<string, any>;

  constructor(opts: {
    packetId: string;
    senderId: string;
    packetType?: string;
    seqNum?: number;
    totalFrags?: number;
    fragIdx?: number;
    payload?: Record<string, any>;
    checksum?: string;
    timestamp?: number;
  }) {
    this.packetId = opts.packetId;
    this.senderId = opts.senderId;
    this.packetType = opts.packetType || PACKET_TYPE_DATA;
    this.seqNum = opts.seqNum || 1;
    this.totalFrags = opts.totalFrags || 1;
    this.fragIdx = opts.fragIdx || 0;
    this.payload = opts.payload || {};
    this.timestamp = opts.timestamp || Date.now() / 1000;

    if (opts.checksum) {
      this.checksum = opts.checksum;
    } else {
      this.checksum = this.generateChecksum();
    }
  }

  public generateChecksum(): string {
    const sortedStr = JSON.stringify(this.payload, Object.keys(this.payload).sort());
    return computeCRC32(sortedStr);
  }

  public verifyChecksum(): boolean {
    return this.checksum === this.generateChecksum();
  }

  public toDict(): PacketData {
    return {
      packet_id: this.packetId,
      sender_id: this.senderId,
      packet_type: this.packetType,
      seq_num: this.seqNum,
      total_frags: this.totalFrags,
      frag_idx: this.fragIdx,
      checksum: this.checksum,
      timestamp: this.timestamp,
      payload: this.payload,
    };
  }

  public static fromDict(data: PacketData): Packet {
    return new Packet({
      packetId: data.packet_id,
      senderId: data.sender_id,
      packetType: data.packet_type,
      seqNum: data.seq_num,
      totalFrags: data.total_frags,
      fragIdx: data.frag_idx,
      checksum: data.checksum,
      timestamp: data.timestamp,
      payload: data.payload,
    });
  }
}

export class ACKTrackerMobile {
  private senderId: string;
  private seqCounter: number = 0;
  private pendingAcks: Map<string, { packet: Packet; sentAt: number; retries: number }> = new Map();
  private timeoutMs: number;
  private maxRetries: number;

  constructor(senderId: string, timeoutMs: number = 5000, maxRetries: number = 3) {
    this.senderId = senderId;
    this.timeoutMs = timeoutMs;
    this.maxRetries = maxRetries;
  }

  public getNextSeqNum(): number {
    this.seqCounter += 1;
    return this.seqCounter;
  }

  public trackPacket(packet: Packet): void {
    if (packet.packetType === PACKET_TYPE_DATA) {
      this.pendingAcks.set(packet.packetId, {
        packet,
        sentAt: Date.now(),
        retries: 0,
      });
    }
  }

  public processAck(ackPacket: Packet): string | null {
    if (ackPacket.packetType === PACKET_TYPE_ACK) {
      const ackedId = ackPacket.payload['acked_packet_id'];
      if (ackedId && this.pendingAcks.has(ackedId)) {
        this.pendingAcks.delete(ackedId);
        return ackedId;
      }
    }
    return null;
  }

  public getDueRetransmissions(): Packet[] {
    const now = Date.now();
    const due: Packet[] = [];

    this.pendingAcks.forEach((item, pktId) => {
      if (now - item.sentAt >= this.timeoutMs) {
        if (item.retries < this.maxRetries) {
          item.retries += 1;
          item.sentAt = now;
          due.push(item.packet);
        } else {
          this.pendingAcks.delete(pktId);
        }
      }
    });

    return due;
  }

  public createAckPacket(dataPacket: Packet): Packet {
    return new Packet({
      packetId: `ack-${dataPacket.packetId}`,
      senderId: this.senderId,
      packetType: PACKET_TYPE_ACK,
      payload: {
        acked_packet_id: dataPacket.packetId,
        acked_seq_num: dataPacket.seqNum,
      },
    });
  }
}
