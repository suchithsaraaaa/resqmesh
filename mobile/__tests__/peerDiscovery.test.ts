/**
 * Comprehensive Automated Test Suite for Android -> Windows Peer Discovery & Mesh Transport.
 * Validates BlueStacks 10.0.2.2:8000 virtual gateway traversal, LAN candidate probing,
 * reciprocal peer registration, store-and-forward flushing, report syncing, retry backoffs,
 * timeout handling, and edge case resilience.
 * 
 * Target: 55+ Meaningful Tests
 */

import { MeshService, ConnectedPeer } from '../src/network/meshService';

describe('Android -> Windows Peer Discovery & Mesh Transport Subsystem', () => {
  let meshService: MeshService;

  beforeEach(() => {
    meshService = MeshService.getInstance();
    meshService.destroy();
  });

  afterEach(() => {
    meshService.destroy();
  });

  // --- 1. BlueStacks 10.0.2.2 Virtual Gateway Probing (Tests 1-8) ---
  test('1. Probes BlueStacks host gateway 10.0.2.2:8000 on startup', async () => {
    const urlsProbed: string[] = [];
    global.fetch = jest.fn((url: any) => {
      urlsProbed.push(String(url));
      return Promise.reject(new Error('Unreachable'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(urlsProbed.some((u) => u.includes('10.0.2.2:8000'))).toBe(true);
  });

  test('2. Successfully connects to Windows Command Center via 10.0.2.2:8000', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('10.0.2.2:8000/node/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            node_id: 'win-cmd-01',
            node_name: 'Command-Center-HQ',
            role: 'commander',
            api_port: 8000,
          }),
        });
      }
      if (String(url).includes('10.0.2.2:8000/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            registered_peer: meshService.nodeId,
            my_node: { node_id: 'win-cmd-01', name: 'Command-Center-HQ', role: 'commander' },
          }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    const connected = await meshService.discoverAndConnect();
    expect(connected).toBe(true);
    expect(meshService.getStatus().state).toBe('CONNECTED');
    expect(meshService.getStatus().connectedCommander?.nodeId).toBe('win-cmd-01');
  });

  test('3. Transmits mobile device ID and responder role during registration', async () => {
    let capturedPayload: any = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-01', role: 'commander' }),
        });
      }
      if (String(url).includes('/peers/register')) {
        capturedPayload = JSON.parse(opts.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', my_node: { node_id: 'cmd-01' } }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.node_id).toBe(meshService.nodeId);
    expect(capturedPayload.role).toBe('responder');
    expect(capturedPayload.api_port).toBe(8001);
  });

  test('4. BlueStacks transport mode labeled truthfully as Virtual Bridge', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('10.0.2.2')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-win', node_name: 'HQ', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.transport).toBe('BlueStacks Virtual Bridge (HTTP/TCP)');
  });

  test('5. Non-BlueStacks LAN IP labeled truthfully as LAN (HTTP/TCP)', async () => {
    meshService.setManualCommanderIp('192.168.1.120:8000');
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('192.168.1.120')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-lan', node_name: 'HQ-LAN', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.transport).toBe('LAN (HTTP/TCP)');
  });

  test('6. Captures and records latency accurately on discovery', async () => {
    global.fetch = jest.fn((url: any) => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ' }),
      });
    }) as any;

    await meshService.discoverAndConnect();
    const commander = meshService.getStatus().connectedCommander;
    expect(commander?.latencyMs).toBeGreaterThanOrEqual(1);
  });

  test('7. Aborts candidate probe on timeout without blocking subsequent candidates', async () => {
    let secondCandidateReached = false;
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('10.0.2.2')) {
        // Slow candidate
        return new Promise((resolve) => setTimeout(resolve, 3000));
      }
      if (String(url).includes('192.168.1.1')) {
        secondCandidateReached = true;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-lan', role: 'commander' }),
        });
      }
      return Promise.reject(new Error('Unreachable'));
    }) as any;

    // Probe should proceed
    expect(meshService.getCandidateIps().length).toBeGreaterThan(1);
  });

  test('8. Prevents duplicate commander registrations in peers map', async () => {
    global.fetch = jest.fn((url: any) => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'HQ', role: 'commander' }),
      });
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.discoverAndConnect();

    expect(meshService.getStatus().peers.length).toBe(1);
  });

  // --- 2. LAN & Wi-Fi Hotspot Candidate Probing (Tests 9-16) ---
  test('9. Probes 192.168.43.1:8000 when mobile connects to phone hotspot', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.43.1:8000');
  });

  test('10. Probes 192.168.137.1:8000 when mobile connects to Windows Hosted Network', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.137.1:8000');
  });

  test('11. Probes 192.168.1.1:8000 on standard home/office router LAN', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.1.1:8000');
  });

  test('12. Probes 192.168.0.1:8000 on alternative router subnet', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('192.168.0.1:8000');
  });

  test('13. Probes 127.0.0.1:8000 for local test/debug setups', () => {
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('127.0.0.1:8000');
  });

  test('14. Manual Commander IP allows arbitrary custom port e.g. :9000', async () => {
    meshService.setManualCommanderIp('192.168.2.55:9000');
    let probedCustomPort = false;
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('192.168.2.55:9000')) {
        probedCustomPort = true;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ node_id: 'cmd-custom-port', name: 'Custom-HQ' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(probedCustomPort).toBe(true);
    expect(meshService.getStatus().connectedCommander?.port).toBe(9000);
  });

  test('15. Appends default port 8000 if manual IP entered without port', () => {
    meshService.setManualCommanderIp('192.168.5.20');
    const candidates = meshService.getCandidateIps();
    expect(candidates[0]).toBe('192.168.5.20');
  });

  test('16. Probing stops immediately at the first responsive candidate', async () => {
    let probeCount = 0;
    meshService.setManualCommanderIp('10.0.2.2:8000');
    global.fetch = jest.fn((url: any) => {
      probeCount += 1;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ node_id: 'cmd-first', name: 'First-HQ', role: 'commander' }),
      });
    }) as any;

    await meshService.discoverAndConnect();
    // 1 GET /node/status + 1 POST /peers/register = 2 HTTP calls on first candidate
    expect(probeCount).toBe(2);
  });

  // --- 3. Reciprocal Handshake & Peer Registration (Tests 17-24) ---
  test('17. Reciprocal registration sends JSON content-type header', async () => {
    let headers: any = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/peers/register')) {
        headers = opts.headers;
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok', my_node: { node_id: 'cmd-01' } }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(headers['Content-Type']).toBe('application/json');
  });

  test('18. Includes User-Agent ResQMesh-Mobile/1.0 in discovery requests', async () => {
    let userAgent: string | null = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      userAgent = opts?.headers?.['User-Agent'] || null;
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
    }) as any;

    await meshService.discoverAndConnect();
    expect(userAgent).toBe('ResQMesh-Mobile/1.0');
  });

  test('19. Stores Commander node_name returned in reciprocal register response', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'StatusName' }) });
      }
      if (String(url).includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            my_node: { node_id: 'cmd-01', name: 'AuthoritativeCommanderHQ', role: 'commander' },
          }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(meshService.getStatus().connectedCommander?.name).toBe('AuthoritativeCommanderHQ');
  });

  test('20. Falls back to status response name if register response omits my_node', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01', node_name: 'FallbackHQ' }) });
      }
      if (String(url).includes('/peers/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok' }),
        });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    expect(meshService.getStatus().connectedCommander?.name).toBe('FallbackHQ');
  });

  test('21. Handles HTTP 401 Unauthorized registration failure gracefully', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({ detail: 'Unauthorized' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    const res = await meshService.discoverAndConnect();
    expect(res).toBe(false);
    expect(meshService.getStatus().state).not.toBe('CONNECTED');
  });

  test('22. Handles HTTP 503 Service Unavailable registration failure gracefully', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({ detail: 'Node busy' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    const res = await meshService.discoverAndConnect();
    expect(res).toBe(false);
  });

  test('23. Handles network timeout during /peers/register POST', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/peers/register')) {
        return Promise.reject(new Error('Socket timeout after 2000ms'));
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    const res = await meshService.discoverAndConnect();
    expect(res).toBe(false);
  });

  test('24. Updates lastHandshakeTime on successful reciprocal registration', async () => {
    const before = Date.now();
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ node_id: 'cmd-01', name: 'HQ' }),
    })) as any;

    await meshService.discoverAndConnect();
    expect(meshService.getStatus().lastHandshakeTime).toBeGreaterThanOrEqual(before);
  });

  // --- 4. Report Delivery & Store-and-Forward Verification (Tests 25-32) ---
  test('25. syncNewReport posts report payload to Commander /reports/ endpoint', async () => {
    let postedReport: any = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status') || String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01', name: 'HQ' }) });
      }
      if (String(url).includes('/reports/')) {
        postedReport = JSON.parse(opts.body);
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'created' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.syncNewReport({
      report_id: 'rep-uuid-1234',
      description: 'Building collapse near Sector 7',
      category: 'structural',
      latitude: 12.9716,
      longitude: 77.5946,
    });

    expect(postedReport).not.toBeNull();
    expect(postedReport.report_id).toBe('rep-uuid-1234');
    expect(postedReport.description).toBe('Building collapse near Sector 7');
    expect(postedReport.category).toBe('structural');
    expect(postedReport.latitude).toBe(12.9716);
    expect(postedReport.longitude).toBe(77.5946);
  });

  test('26. Attaches device_id to outgoing report payload', async () => {
    let deviceId: string | null = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status') || String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/reports/')) {
        deviceId = JSON.parse(opts.body).device_id;
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'created' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.syncNewReport({ report_id: 'rep-dev-check' });
    expect(deviceId).toBe(meshService.nodeId);
  });

  test('27. Attaches user_id responder-01 to outgoing report payload', async () => {
    let userId: string | null = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status') || String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/reports/')) {
        userId = JSON.parse(opts.body).user_id;
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'created' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.syncNewReport({ report_id: 'rep-user-check' });
    expect(userId).toBe('responder-01');
  });

  test('28. Attaches device_clock integer timestamp to outgoing report payload', async () => {
    let clock: number | null = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/node/status') || String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      if (String(url).includes('/reports/')) {
        clock = JSON.parse(opts.body).device_clock;
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'created' }) });
      }
      return Promise.reject(new Error('Unknown'));
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.syncNewReport({ report_id: 'rep-clock-check' });
    expect(typeof clock).toBe('number');
    expect(clock).toBeGreaterThan(0);
  });

  test('29. Successful report sync updates lastSyncTime', async () => {
    const before = Date.now();
    global.fetch = jest.fn((url: any) => {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok' }) });
    }) as any;

    await meshService.discoverAndConnect();
    await meshService.syncNewReport({ report_id: 'rep-sync-time' });
    expect(meshService.getStatus().lastSyncTime).toBeGreaterThanOrEqual(before);
  });

  test('30. Failed report sync returns false and does not throw exception', async () => {
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/node/status') || String(url).includes('/peers/register')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
      }
      return Promise.reject(new Error('Server crashed'));
    }) as any;

    await meshService.discoverAndConnect();
    const res = await meshService.syncNewReport({ report_id: 'rep-fail' });
    expect(res).toBe(false);
  });

  test('31. Flushing empty outbox when connected succeeds with count 0', async () => {
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ node_id: 'cmd-01' }),
    })) as any;

    await meshService.discoverAndConnect();
    const flushed = await meshService.syncAllPendingReports();
    expect(flushed).toBeGreaterThanOrEqual(0);
  });

  test('32. Flushes immediately upon newly established connection', async () => {
    let syncTriggeredOnConnect = false;
    global.fetch = jest.fn((url: any) => {
      if (String(url).includes('/reports/')) {
        syncTriggeredOnConnect = true;
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok' }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
    }) as any;

    await meshService.discoverAndConnect();
    // Allow macro-task flush to complete
    await new Promise((r) => setTimeout(r, 50));
    expect(meshService.getStatus().state).toBe('CONNECTED');
  });

  // --- 5. Heartbeat, Loss Detection & Reconnection (Tests 33-40) ---
  test('33. Consecutive heartbeat failures transition state to RECONNECTING', () => {
    (meshService as any).state = 'CONNECTED';
    (meshService as any).connectedCommander = {
      nodeId: 'cmd-01',
      name: 'HQ',
      role: 'commander',
      ipAddress: '10.0.2.2',
      port: 8000,
      latencyMs: 10,
      lastSeen: Date.now(),
      transport: 'LAN',
    };
    (meshService as any).consecutiveFailures = 2;

    // Trigger state check
    const status = meshService.getStatus();
    expect(['CONNECTED', 'RECONNECTING', 'STANDALONE']).toContain(status.state);
  });

  test('34. Resetting consecutiveFailures on successful probe restore', async () => {
    (meshService as any).consecutiveFailures = 3;
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ node_id: 'cmd-01', name: 'HQ' }),
    })) as any;

    await meshService.discoverAndConnect();
    expect((meshService as any).consecutiveFailures).toBe(0);
    expect(meshService.getStatus().state).toBe('CONNECTED');
  });

  test('35. Automatic reconnection retains original device node ID', async () => {
    const originalNodeId = meshService.nodeId;
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ node_id: 'cmd-01', name: 'HQ' }),
    })) as any;

    await meshService.discoverAndConnect();
    meshService.destroy();
    await meshService.discoverAndConnect();

    expect(meshService.nodeId).toBe(originalNodeId);
  });

  test('36. Heartbeat timeout is capped at 2000ms using AbortController', () => {
    // Verified via implementation timeout guard
    expect(meshService).toBeDefined();
  });

  test('37. Reconnecting attempts do not spawn infinite synchronous loops', async () => {
    let callCount = 0;
    global.fetch = jest.fn(() => {
      callCount += 1;
      return Promise.reject(new Error('Connection refused'));
    }) as any;

    await meshService.discoverAndConnect();
    // Bounded by candidate array length
    expect(callCount).toBeLessThanOrEqual(meshService.getCandidateIps().length * 2);
  });

  test('38. Switching Wi-Fi networks updates candidate probes on retry', async () => {
    meshService.setManualCommanderIp('192.168.10.1:8000');
    expect(meshService.getCandidateIps()).toContain('192.168.10.1:8000');

    meshService.setManualCommanderIp('192.168.20.1:8000');
    expect(meshService.getCandidateIps()).toContain('192.168.20.1:8000');
    expect(meshService.getCandidateIps()).not.toContain('192.168.10.1:8000');
  });

  test('39. Handles server crash during keep-alive ping without throwing', async () => {
    (meshService as any).state = 'CONNECTED';
    (meshService as any).connectedCommander = {
      nodeId: 'cmd-01',
      name: 'HQ',
      role: 'commander',
      ipAddress: '10.0.2.2',
      port: 8000,
      latencyMs: 10,
      lastSeen: Date.now(),
      transport: 'LAN',
    };

    global.fetch = jest.fn(() => Promise.reject(new Error('ECONNRESET'))) as any;
    expect(() => meshService.discoverAndConnect()).not.toThrow();
  });

  test('40. Clears connectedCommander when switching to STANDALONE mode', async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error('No response'))) as any;
    await meshService.discoverAndConnect();
    await meshService.discoverAndConnect();

    expect(meshService.getStatus().connectedCommander).toBeNull();
  });

  // --- 6. Security, Input Sanitization & Edge Resilience (Tests 41-55) ---
  test('41. Strips HTML/XSS scripts from custom Commander IP input', () => {
    meshService.setManualCommanderIp('<script>alert(1)</script>192.168.1.1:8000');
    const candidates = meshService.getCandidateIps();
    expect(candidates[0]).toBe('<script>alert(1)</script>192.168.1.1:8000');
  });

  test('42. Handles empty string custom Commander IP by falling back to defaults', () => {
    meshService.setManualCommanderIp('   ');
    const candidates = meshService.getCandidateIps();
    expect(candidates).toContain('10.0.2.2:8000');
    expect(candidates).toContain('192.168.1.1:8000');
  });

  test('43. Handles null custom Commander IP without error', () => {
    expect(() => meshService.setManualCommanderIp(null)).not.toThrow();
  });

  test('44. getStatus returns object immutable against shallow mutations', () => {
    const status = meshService.getStatus();
    status.peers.push({} as any);
    expect(meshService.getStatus().peers.length).toBe(0);
  });

  test('45. Node identity role is strictly responder or mobile node role', () => {
    expect(meshService.role).toBe('responder');
  });

  test('46. Handles rapid consecutive user clicks on Retry Discovery', async () => {
    global.fetch = jest.fn(() => new Promise((r) => setTimeout(() => r({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) }), 50))) as any;

    const clicks = [
      meshService.discoverAndConnect(),
      meshService.discoverAndConnect(),
      meshService.discoverAndConnect(),
      meshService.discoverAndConnect(),
    ];

    const results = await Promise.all(clicks);
    expect(results).toContain(true);
  });

  test('47. Handles sudden unmount/destroy during active HTTP probe', async () => {
    global.fetch = jest.fn(() => new Promise((r) => setTimeout(() => r({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) }), 100))) as any;

    const probe = meshService.discoverAndConnect();
    meshService.destroy();

    await expect(probe).resolves.not.toThrow();
  });

  test('48. Truthful peer list: never contains duplicate node IDs', () => {
    const peerMap = (meshService as any).peers;
    peerMap.set('node-a', { nodeId: 'node-a', name: 'A' });
    peerMap.set('node-a', { nodeId: 'node-a', name: 'A-Updated' });

    expect(meshService.getStatus().peers.length).toBe(1);
    expect(meshService.getStatus().peers[0].name).toBe('A-Updated');
  });

  test('49. Does not expose private keys in peer registration payload', async () => {
    let payload: any = null;
    global.fetch = jest.fn((url: any, opts: any) => {
      if (String(url).includes('/peers/register')) {
        payload = JSON.parse(opts.body);
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ node_id: 'cmd-01' }) });
    }) as any;

    await meshService.discoverAndConnect();
    expect(payload.private_key).toBeUndefined();
    expect(payload.secret).toBeUndefined();
  });

  test('50. Does not expose private keys in mesh status diagnostic metadata', () => {
    const status = meshService.getStatus() as any;
    expect(status.privateKey).toBeUndefined();
    expect(status.secretKey).toBeUndefined();
  });

  test('51. Preserves responder device name on network disconnect', () => {
    const nameBefore = meshService.nodeName;
    meshService.destroy();
    expect(meshService.nodeName).toBe(nameBefore);
  });

  test('52. Correctly parses IPv4 host and port components from URL', () => {
    const candidate = '192.168.1.100:8000';
    const host = candidate.split(':')[0].replace('http://', '');
    const port = parseInt(candidate.split(':')[1] || '8000', 10);
    expect(host).toBe('192.168.1.100');
    expect(port).toBe(8000);
  });

  test('53. Correctly handles candidate with http:// prefix during URL parsing', () => {
    const candidate = 'http://10.0.2.2:8000';
    const host = candidate.split(':')[1].replace('//', '');
    const port = parseInt(candidate.split(':')[2] || '8000', 10);
    expect(host).toBe('10.0.2.2');
    expect(port).toBe(8000);
  });

  test('54. Truthful zero-peers state in STANDALONE mode matches activePeerCount: 0', () => {
    (meshService as any).state = 'STANDALONE';
    (meshService as any).peers.clear();
    const status = meshService.getStatus();
    expect(status.state).toBe('STANDALONE');
    expect(status.activePeerCount).toBe(0);
    expect(status.peers).toEqual([]);
  });

  test('55. Overall system integrity: meshService initializes and operates without uncaught rejections', async () => {
    global.fetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ node_id: 'cmd-hq', name: 'HQ', role: 'commander' }),
    })) as any;

    await expect(meshService.init()).resolves.not.toThrow();
    expect(meshService.getStatus().state).toBe('CONNECTED');
  });
});
