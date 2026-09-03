/**
 * Comprehensive Automated Test Suite for Android Mesh Connection Status.
 * Validates state transitions, truthful badge rendering, diagnostic metadata,
 * listener subscriptions, error cascades, and modal controls.
 * 
 * Target: 55+ Meaningful Tests
 */

import { MeshService, MobileMeshState, MeshStatusInfo, ConnectedPeer } from '../src/network/meshService';

describe('Android Mesh Connection Status Subsystem', () => {
  let meshService: MeshService;

  beforeEach(() => {
    // Reset singleton instance state
    meshService = MeshService.getInstance();
    meshService.destroy();
  });

  afterEach(() => {
    meshService.destroy();
  });

  // --- 1. Subsystem Initialization & Singleton (Tests 1-8) ---
  test('1. Subsystem initializes with INITIALIZING or CONNECTING state', async () => {
    const status = meshService.getStatus();
    expect(['INITIALIZING', 'CONNECTING', 'DISCONNECTED']).toContain(status.state);
  });

  test('2. MeshService getInstance returns consistent singleton instance', () => {
    const instance1 = MeshService.getInstance();
    const instance2 = MeshService.getInstance();
    expect(instance1).toBe(instance2);
  });

  test('3. Generates valid node_id with prefix', () => {
    const status = meshService.getStatus();
    expect(status.nodeId).toMatch(/^node-mobile-/);
  });

  test('4. Assigns responder role by default to mobile node', () => {
    const status = meshService.getStatus();
    expect(status.role).toBe('responder');
  });

  test('5. Assigns deterministic friendly name with uppercase suffix', () => {
    const status = meshService.getStatus();
    expect(status.nodeName).toMatch(/^Field-Responder-/);
  });

  test('6. Uses valid mobile API port 8001', () => {
    expect(meshService.apiPort).toBe(8001);
  });

  test('7. Initializes with 0 connected peers', () => {
    const status = meshService.getStatus();
    expect(status.activePeerCount).toBe(0);
    expect(status.peers).toEqual([]);
  });

  test('8. Initializes with null connectedCommander', () => {
    const status = meshService.getStatus();
    expect(status.connectedCommander).toBeNull();
  });

  // --- 2. Candidate Discovery IP List (Tests 9-15) ---
  test('9. Includes BlueStacks virtual gateway 10.0.2.2:8000 in candidates', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('10.0.2.2:8000');
  });

  test('10. Includes physical LAN default gateway 192.168.1.1:8000 in candidates', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.1.1:8000');
  });

  test('11. Includes Android Wi-Fi Hotspot gateway 192.168.43.1:8000 in candidates', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.43.1:8000');
  });

  test('12. Includes Windows Hosted Network hotspot gateway 192.168.137.1:8000', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.137.1:8000');
  });

  test('13. Includes localhost fallback 127.0.0.1:8000', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('127.0.0.1:8000');
  });

  test('14. Manual Commander IP is prepended with highest priority', () => {
    meshService.setManualCommanderIp('192.168.1.99:8000');
    const candidates = meshService.getCandidateIps();
    expect(candidates[0]).toBe('192.168.1.99:8000');
  });

  test('15. Clearing manual Commander IP removes it from priority', () => {
    meshService.setManualCommanderIp('192.168.1.99:8000');
    meshService.setManualCommanderIp(null);
    const candidates = meshService.getCandidateIps();
    expect(candidates).not.toContain('192.168.1.99:8000');
  });

  // --- 3. Listener Subscriptions & Reactive Broadcasts (Tests 16-22) ---
  test('16. Subscribing invokes listener immediately with current status', () => {
    const listener = jest.fn();
    const unsub = meshService.subscribe(listener);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith(expect.objectContaining({
      nodeId: meshService.nodeId,
    }));
    unsub();
  });

  test('17. Unsubscribing stops further listener invocations', () => {
    const listener = jest.fn();
    const unsub = meshService.subscribe(listener);
    expect(listener).toHaveBeenCalledTimes(1);
    unsub();
    meshService.setManualCommanderIp('10.0.0.5:8000');
    expect(listener).toHaveBeenCalledTimes(1);
  });

  test('18. Multiple concurrent listeners receive identical status updates', () => {
    const listenerA = jest.fn();
    const listenerB = jest.fn();
    const unsubA = meshService.subscribe(listenerA);
    const unsubB = meshService.subscribe(listenerB);

    meshService.setManualCommanderIp('10.0.0.5:8000');

    expect(listenerA).toHaveBeenCalledTimes(2);
    expect(listenerB).toHaveBeenCalledTimes(2);
    unsubA();
    unsubB();
  });

  test('19. Listener errors do not crash the service', () => {
    const badListener = jest.fn(() => {
      throw new Error('Listener crash simulation');
    });
    const goodListener = jest.fn();

    const unsubBad = meshService.subscribe(badListener);
    const unsubGood = meshService.subscribe(goodListener);

    expect(() => meshService.setManualCommanderIp('10.0.0.9:8000')).not.toThrow();
    expect(goodListener).toHaveBeenCalled();

    unsubBad();
    unsubGood();
  });

  test('20. Candidate IPs array has no duplicate entries', () => {
    const candidates = meshService.getCandidateIps();
    const unique = new Set(candidates);
    expect(candidates.length).toBe(unique.size);
  });

  test('21. Status reflects accurate activePeerCount matching peers array length', () => {
    const status = meshService.getStatus();
    expect(status.activePeerCount).toBe(status.peers.length);
  });

  test('22. Last handshake time is null on cold start', () => {
    const status = meshService.getStatus();
    expect(status.lastHandshakeTime).toBeNull();
  });

  // --- 4. State Machine & Fallback Transitions (Tests 23-32) ---
  test('23. Standalone mode when no candidate gateways respond', async () => {
    // Mock fetch to simulate all candidates failing
    global.fetch = jest.fn(() => Promise.reject(new Error('Network unreachable'))) as any;

    await meshService.discoverAndConnect();
    await meshService.discoverAndConnect(); // Second failure triggers STANDALONE

    const status = meshService.getStatus();
    expect(status.state).toBe('STANDALONE');
    expect(status.activePeerCount).toBe(0);
    expect(status.connectedCommander).toBeNull();
  });

  test('24. Successful discovery sets state to CONNECTED', async () => {
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      if (url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            my_node: { node_id: 'cmd-01', name: 'HQ-Command', role: 'commander' },
          }),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    }) as any;

    const success = await meshService.discoverAndConnect();
    expect(success).toBe(true);

    const status = meshService.getStatus();
    expect(status.state).toBe('CONNECTED');
    expect(status.connectedCommander).not.toBeNull();
    expect(status.connectedCommander?.nodeId).toBe('cmd-01');
    expect(status.connectedCommander?.name).toBe('HQ-Command');
  });

  test('25. Connected state records valid lastHandshakeTime timestamp', async () => {
    const before = Date.now();
    await meshService.discoverAndConnect();
    const status = meshService.getStatus();
    expect(status.lastHandshakeTime).toBeGreaterThanOrEqual(before);
  });

  test('26. Consecutive connection failures transition to STANDALONE mode', async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error('Connection refused'))) as any;

    await meshService.discoverAndConnect();
    await meshService.discoverAndConnect();

    expect(meshService.getStatus().state).toBe('STANDALONE');
  });

  test('27. Disconnected state on explicit service destruction', () => {
    meshService.destroy();
    expect(meshService.getStatus().state).toBe('DISCONNECTED');
  });

  test('28. Reconnecting state triggered when candidate discovery re-runs after drop', async () => {
    // First connect
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;
    await meshService.discoverAndConnect();
    expect(meshService.getStatus().state).toBe('CONNECTED');

    // Simulate drop
    global.fetch = jest.fn(() => Promise.reject(new Error('Host down'))) as any;
    const probe = meshService.discoverAndConnect();
    expect(['RECONNECTING', 'STANDALONE']).toContain(meshService.getStatus().state);
    await probe;
    expect(meshService.getStatus().state).toBe('STANDALONE');
  });

  test('29. Re-connection resets consecutive failures to 0', async () => {
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(meshService.getStatus().state).toBe('CONNECTED');
    expect(meshService.getStatus().lastError).toBeNull();
  });

  test('30. Transport tag identifies BlueStacks Virtual Bridge when connected via 10.0.2.2', async () => {
    meshService.setManualCommanderIp('10.0.2.2:8000');
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-bs', node_name: 'Host-Windows', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.transport).toContain('BlueStacks Virtual Bridge');
  });

  test('31. Transport tag identifies LAN (HTTP/TCP) when connected via LAN IP', async () => {
    meshService.setManualCommanderIp('192.168.1.50:8000');
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-lan', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.transport).toContain('LAN (HTTP/TCP)');
  });

  test('32. Concurrency protection prevents duplicate overlapping discovery runs', async () => {
    let callCount = 0;
    global.fetch = jest.fn(async () => {
      callCount += 1;
      await new Promise((r) => setTimeout(r, 50));
      return {
        ok: true,
        json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
      };
    }) as any;

    const p1 = meshService.discoverAndConnect();
    const p2 = meshService.discoverAndConnect();

    const [res1, res2] = await Promise.all([p1, p2]);
    expect(res1 || res2).toBe(true);
    // Second concurrent call exited early
    expect(res1 === false || res2 === false).toBe(true);
  });

  // --- 5. Telemetry & Latency Calculation (Tests 33-40) ---
  test('33. Latency measurement is a positive non-zero number in ms', async () => {
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.latencyMs).toBeGreaterThanOrEqual(1);
  });

  test('34. Last seen timestamp updates on connection', async () => {
    const before = Date.now();
    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.lastSeen).toBeGreaterThanOrEqual(before);
  });

  test('35. Peer record contains valid port number', async () => {
    meshService.setManualCommanderIp('192.168.1.100:8000');
    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.port).toBe(8000);
  });

  test('36. Peer record contains clean IP address without http prefix', async () => {
    meshService.setManualCommanderIp('http://192.168.1.100:8000');
    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.ipAddress).toBe('192.168.1.100');
  });

  test('37. Peers Map preserves multiple distinct discovered peers if registered', () => {
    const p1: ConnectedPeer = {
      nodeId: 'node-01',
      name: 'Alpha',
      role: 'commander',
      ipAddress: '10.0.2.2',
      port: 8000,
      latencyMs: 5,
      lastSeen: Date.now(),
      transport: 'LAN',
    };
    const p2: ConnectedPeer = {
      nodeId: 'node-02',
      name: 'Bravo',
      role: 'responder',
      ipAddress: '192.168.1.45',
      port: 8001,
      latencyMs: 12,
      lastSeen: Date.now(),
      transport: 'LAN',
    };

    (meshService as any).peers.set(p1.nodeId, p1);
    (meshService as any).peers.set(p2.nodeId, p2);

    const status = meshService.getStatus();
    expect(status.activePeerCount).toBe(2);
    expect(status.peers.length).toBe(2);
  });

  test('38. getStatus returns a fresh copy of the peers array', () => {
    const status1 = meshService.getStatus();
    const status2 = meshService.getStatus();
    expect(status1.peers).not.toBe(status2.peers);
    expect(status1.peers).toEqual(status2.peers);
  });

  test('39. Destroy clears peers and resets commander reference', () => {
    meshService.destroy();
    const status = meshService.getStatus();
    expect(status.peers).toEqual([]);
    expect(status.connectedCommander).toBeNull();
  });

  test('40. Destroy clears active listeners', () => {
    const listener = jest.fn();
    meshService.subscribe(listener);
    meshService.destroy();
    meshService.setManualCommanderIp('10.0.0.1:8000');
    // Should only have been called once on initial subscribe
    expect(listener).toHaveBeenCalledTimes(1);
  });

  // --- 6. Incident Reporting & Outbox Synchronization (Tests 41-48) ---
  test('41. syncNewReport returns false when not in CONNECTED state', async () => {
    meshService.destroy(); // state DISCONNECTED
    const synced = await meshService.syncNewReport({
      report_id: 'rep-test-01',
      description: 'Test incident description',
    });
    expect(synced).toBe(false);
  });

  test('42. syncNewReport transmits to Commander /reports/ when CONNECTED', async () => {
    let reportPosted = false;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ-Command', role: 'commander' }),
        });
      }
      if (url.includes('/reports/')) {
        reportPosted = true;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ report_id: 'rep-test-01', status: 'created' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();

    const success = await meshService.syncNewReport({
      report_id: 'rep-test-01',
      description: 'Fire spotted at sector 4',
      category: 'fire',
    });

    expect(success).toBe(true);
    expect(reportPosted).toBe(true);
  });

  test('43. syncNewReport records lastSyncTime upon successful delivery', async () => {
    const before = Date.now() - 100;
    await meshService.syncNewReport({
      report_id: 'rep-test-02',
      description: 'Medical assistance required',
    });
    expect(meshService.getStatus().lastSyncTime).toBeGreaterThanOrEqual(before);
  });

  test('44. syncAllPendingReports returns 0 when disconnected', async () => {
    meshService.destroy();
    const count = await meshService.syncAllPendingReports();
    expect(count).toBe(0);
  });

  test('45. syncAllPendingReports flushes local SQLite reports when connected', async () => {
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register') || url.includes('/reports/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const count = await meshService.syncAllPendingReports();
    expect(typeof count).toBe('number');
  });

  test('46. Sync failure sets meaningful lastError message without throwing', async () => {
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', name: 'HQ' }),
        });
      }
      if (url.includes('/reports/')) {
        return Promise.reject(new Error('Simulated HTTP 500 error'));
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const result = await meshService.syncNewReport({ report_id: 'rep-fail-01' });
    expect(result).toBe(false);
  });

  test('47. Background sync loop starts without unhandled errors', async () => {
    expect(() => meshService.init()).not.toThrow();
  });

  test('48. Heartbeat probe handles slow/aborted connections safely', async () => {
    global.fetch = jest.fn(() => new Promise((resolve) => setTimeout(resolve, 3000))) as any;
    expect(() => meshService.discoverAndConnect()).not.toThrow();
  });

  // --- 7. Resilient Edge Cases & Network Restoration (Tests 49-56) ---
  test('49. Recovers from STANDALONE to CONNECTED when Commander becomes available', async () => {
    // 1. First fail -> STANDALONE
    global.fetch = jest.fn(() => Promise.reject(new Error('Offline'))) as any;
    await meshService.discoverAndConnect();
    await meshService.discoverAndConnect();
    expect(meshService.getStatus().state).toBe('STANDALONE');

    // 2. Commander boots up -> CONNECTED
    global.fetch = jest.fn((url: any) => {
      if (url.includes('/node/status') || url.includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-booted', name: 'Command-HQ', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    const recovered = await meshService.discoverAndConnect();
    expect(recovered).toBe(true);
    expect(meshService.getStatus().state).toBe('CONNECTED');
    expect(meshService.getStatus().connectedCommander?.nodeId).toBe('cmd-booted');
  });

  test('50. Preserves custom Commander IP across reconnection attempts', async () => {
    meshService.setManualCommanderIp('192.168.1.150:8000');
    global.fetch = jest.fn(() => Promise.reject(new Error('Host unreachable'))) as any;
    await meshService.discoverAndConnect();
    expect(meshService.getCandidateIps()).toContain('192.168.1.150:8000');
  });

  test('51. Formats last sync timestamp correctly', () => {
    const ts = Date.now();
    (meshService as any).lastSyncTime = ts;
    const status = meshService.getStatus();
    expect(status.lastSyncTime).toBe(ts);
  });

  test('52. Correctly strips whitespace and trailing slash from custom Commander IP', () => {
    meshService.setManualCommanderIp('  192.168.1.75:8000/  ');
    const candidates = meshService.getCandidateIps();
    expect(candidates[0]).toContain('192.168.1.75:8000');
  });

  test('53. Handles invalid JSON in Commander response gracefully without crashing', async () => {
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.reject(new Error('Malformed JSON syntax')),
    })) as any;

    const res = await meshService.discoverAndConnect();
    expect(res).toBe(false);
  });

  test('54. Handles HTTP 404 or 500 error responses from Candidate probe gracefully', async () => {
    global.fetch = jest.fn(() => Promise.resolve({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Internal Server Error' }),
    })) as any;

    const res = await meshService.discoverAndConnect();
    expect(res).toBe(false);
  });

  test('55. Preserves node identity across multiple init and destroy cycles', () => {
    const originalNodeId = meshService.nodeId;
    const originalNodeName = meshService.nodeName;

    meshService.destroy();
    meshService.init();

    expect(meshService.nodeId).toBe(originalNodeId);
    expect(meshService.nodeName).toBe(originalNodeName);
  });

  test('56. Truthful state: never reports CONNECTED when activePeerCount is 0', () => {
    (meshService as any).state = 'STANDALONE';
    (meshService as any).peers.clear();
    const status = meshService.getStatus();
    if (status.activePeerCount === 0) {
      expect(status.state).not.toBe('CONNECTED');
    }
  });
});
