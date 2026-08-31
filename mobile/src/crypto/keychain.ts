/**
 * ResQMesh Mobile Keychain & Security Module.
 * Manages device identity keys, QR trust bootstrapping payloads, and verification helpers.
 */

export interface QRBootstrapPayload {
  version: string;
  protocol: 'resqmesh-auth';
  deviceId: string;
  role: 'responder' | 'commander' | 'relay';
  publicKey: string;
  timestamp: number;
}

export interface TrustedPeerInfo {
  deviceId: string;
  publicKey: string;
  role: string;
  verifiedViaQR: boolean;
  addedAt: number;
}

export class MobileKeychain {
  private localDeviceId: string;
  private localPublicKey: string;
  private localRole: QRBootstrapPayload['role'];
  private trustedPeers: Map<string, TrustedPeerInfo> = new Map();

  constructor(deviceId: string, publicKey: string = '', role: QRBootstrapPayload['role'] = 'responder') {
    this.localDeviceId = deviceId;
    this.localPublicKey = publicKey || `pub-key-${deviceId}`;
    this.localRole = role;
  }

  public getPublicKey(): string {
    return this.localPublicKey;
  }

  public generateQRCodePayload(): string {
    const payload: QRBootstrapPayload = {
      version: '1.0',
      protocol: 'resqmesh-auth',
      deviceId: this.localDeviceId,
      role: this.localRole,
      publicKey: this.localPublicKey,
      timestamp: Date.now() / 1000,
    };
    return JSON.stringify(payload);
  }

  public scanAndBootstrapPeer(qrJson: string): boolean {
    try {
      const data: QRBootstrapPayload = JSON.parse(qrJson);
      if (data.protocol !== 'resqmesh-auth' || !data.deviceId || !data.publicKey) {
        return false;
      }

      this.trustedPeers.set(data.deviceId, {
        deviceId: data.deviceId,
        publicKey: data.publicKey,
        role: data.role || 'responder',
        verifiedViaQR: true,
        addedAt: Date.now(),
      });
      return true;
    } catch {
      return false;
    }
  }

  public isPeerTrusted(deviceId: string): boolean {
    return this.trustedPeers.has(deviceId);
  }

  public getTrustedPeers(): TrustedPeerInfo[] {
    return Array.from(this.trustedPeers.values());
  }
}
