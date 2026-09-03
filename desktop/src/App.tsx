import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { MapIncidentMarker } from './components/MapView';
import { PendingReportCluster } from './components/IncidentReviewCard';
import { ResourceRequestItem } from './components/ResourceDispatchPanel';
import { FirstRunModal } from './components/FirstRunModal';
import { PeerTopologyModal, PeerNode } from './components/PeerTopologyModal';
import { CreateIncidentModal } from './components/CreateIncidentModal';
import { LiveNotificationStream, MeshActivityItem } from './components/LiveNotificationStream';
import { RequestResourceModal } from './components/RequestResourceModal';
import { IncidentDetailsModal } from './components/IncidentDetailsModal';
import { GlobeHeroView, GlobeHeroViewRef } from './components/GlobeHeroView';
import { SidebarNav, NavTab } from './components/SidebarNav';
import { TopHeader } from './components/TopHeader';
import { DashboardMetrics } from './components/DashboardMetrics';
import { IncidentsView } from './components/views/IncidentsView';
import { ResourcesView } from './components/views/ResourcesView';
import { TeamsView } from './components/views/TeamsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { AdvisorView } from './components/views/AdvisorView';
import { SettingsView } from './components/views/SettingsView';
import { OnDeviceAdvisorCard } from './components/OnDeviceAdvisorCard';
import { IncidentMergeAiCard } from './components/IncidentMergeAiCard';
import { LiveTacticalActivityFeed } from './components/LiveTacticalActivityFeed';
import { TacticalEventBus } from './services/TacticalEventBus';
import { colors, radii, shadows, fonts } from './styles/designTokens';

// Production Deployment Mode: No mock incidents. Incidents are sourced strictly from local user broadcasts or peer mesh sync.
const DEMO_GLOBAL_INCIDENTS: MapIncidentMarker[] = [];

export const App: React.FC = () => {
  // Base API configuration
  const [apiPort, setApiPort] = useState<number>(8000);
  const getApiUrl = useCallback(() => `http://127.0.0.1:${apiPort}`, [apiPort]);

  // Node Core State
  const [nodeId, setNodeId] = useState<string>('');
  const [nodeName, setNodeName] = useState<string>('');
  const [nodeRole, setNodeRole] = useState<string>('responder');
  const [isConfigured, setIsConfigured] = useState<boolean>(true);

  // Mesh Network & Sync State
  const [peers, setPeers] = useState<PeerNode[]>([]);
  const [meshState, setMeshState] = useState<string>('INITIALIZING');
  const [outboxCount, setOutboxCount] = useState<number>(0);
  const [syncStatus, setSyncStatus] = useState<string>('synchronized');

  // Live Tactical Mesh Notification Stream State & Tracking Refs
  const [notifications, setNotifications] = useState<MeshActivityItem[]>([
    {
      id: 'init-mesh-1',
      type: 'sync_verified',
      title: 'Tactical Mesh Active',
      detail: 'ResQMesh tactical consensus engine initialized in offline-first mode',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      icon: '🛡️',
      badgeColor: '#10b981',
    },
  ]);
  const prevPeerIdsRef = useRef<Set<string>>(new Set());
  const prevIncidentIdsRef = useRef<Set<string>>(new Set());
  const prevDispatchedIdsRef = useRef<Set<string>>(new Set());
  const prevOutboxCountRef = useRef<number | null>(null);
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const dismissedReportIdsRef = useRef<Set<string>>(new Set());

  // Modals
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [showPeersModal, setShowPeersModal] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showRequestResourceModal, setShowRequestResourceModal] = useState<boolean>(false);
  const [detailsModalIncident, setDetailsModalIncident] = useState<MapIncidentMarker | null>(null);

  // Offline Location Picking State
  const [isPickingLocation, setIsPickingLocation] = useState<boolean>(false);
  const [pickedCoords, setPickedCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);

  // Incident & Dispatch State
  const [incidents, setIncidents] = useState<MapIncidentMarker[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [clusters, setClusters] = useState<PendingReportCluster[]>([]);

  // Master Shell Navigation & Tactical Globe Refs
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [showNotificationsDrawer, setShowNotificationsDrawer] = useState<boolean>(false);
  const globeHeroRef = useRef<GlobeHeroViewRef | null>(null);

  const [resources, setResources] = useState<ResourceRequestItem[]>([
    {
      id: 'res-101',
      resourceType: 'Medical Trauma Kit',
      quantity: 4,
      urgency: 'critical',
      status: 'pending',
      requestedBy: 'Laptop-Squad-1',
    },
    {
      id: 'res-102',
      resourceType: 'Emergency Portable Generator',
      quantity: 1,
      urgency: 'high',
      status: 'pending',
      requestedBy: 'Laptop-Squad-2',
    },
  ]);

  // Determine port from Electron preload if available
  useEffect(() => {
    const api = (window as any).resqmeshAPI || (window as any).electronAPI;
    if (api && typeof api.getNodePort === 'function') {
      api.getNodePort().then((port: number) => {
        if (port) setApiPort(port);
      }).catch(() => {});
    } else if (api && typeof api.getServerPort === 'function') {
      api.getServerPort().then((port: number) => {
        if (port) setApiPort(port);
      }).catch(() => {});
    }
  }, []);

  // Fetch node status with timeout protection
  const fetchNodeStatus = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${getApiUrl()}/node/status`, { signal: controller.signal });
      clearTimeout(timeout);
      if (res.ok) {
        const data = await res.json();
        setNodeId(data.node_id || '');
        setNodeName(data.name || '');
        setNodeRole(data.role || 'responder');

        const isNodeConfigured = Boolean(data.is_configured || data.configured);
        const hasCustomName =
          Boolean(data.name) &&
          !data.name.startsWith('Node-') &&
          data.name !== 'Unnamed Laptop' &&
          data.name !== 'ResQMesh-Node';

        if (!isNodeConfigured || !hasCustomName) {
          const offlineData = localStorage.getItem('resqmesh_offline_node');
          if (offlineData) {
            try {
              const parsed = JSON.parse(offlineData);
              if (parsed.name) {
                setNodeName(parsed.name);
                setNodeRole(parsed.role || 'responder');
                setIsConfigured(true);
                setShowConfigModal(false);
                return;
              }
            } catch {}
          }
          setIsConfigured(false);
          setShowConfigModal(true);
        } else {
          setIsConfigured(true);
        }
      }
    } catch {
      // Backend starting up or unreachable
    }
  }, [getApiUrl]);

  // Fetch live mesh network status
  const fetchMeshStatus = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${getApiUrl()}/node/mesh-status`, { signal: controller.signal });
      clearTimeout(timeout);
      if (res.ok) {
        const data = await res.json();
        setMeshState(data.state || (peers.length > 0 ? 'CONNECTED' : 'DEGRADED'));
      }
    } catch {
      setMeshState(peers.length > 0 ? 'CONNECTED' : 'DEGRADED');
    }
  }, [getApiUrl, peers.length]);

  // Fetch active peers & track join notifications
  const fetchPeers = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/peers/`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setPeers(data);
          data.forEach((p: any) => {
            if (p.node_id && !prevPeerIdsRef.current.has(p.node_id) && p.node_id !== nodeId) {
              const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              setNotifications((prev) => [
                {
                  id: `notif-peer-${p.node_id}-${Date.now()}`,
                  type: 'peer_joined',
                  title: 'Peer Joined Mesh',
                  detail: `${p.role === 'commander' ? '🎯 Commander' : '🚒 Responder'} "${p.name || p.node_id}" joined emergency mesh link (${p.ip_address || 'LAN'}:${p.api_port || 8000})`,
                  timestamp: timeStr,
                  icon: '🌐',
                  badgeColor: '#38bdf8',
                  sourceNode: p.name,
                },
                ...prev.slice(0, 39),
              ]);
              TacticalEventBus.publish({
                type: 'MESH_NODE_JOINED',
                severity: 'SUCCESS',
                nodeId: p.node_id,
                actor: p.name || p.node_id,
                title: `Mesh node joined: ${p.name || p.node_id}`,
                description: `${p.role === 'commander' ? 'Commander' : 'Responder'} connected to tactical mesh via ${p.ip_address || 'LAN'}:${p.api_port || 8000}`,
                metadata: { role: p.role, ip: p.ip_address, port: p.api_port },
              });
            }
          });
          prevPeerIdsRef.current = new Set(data.map((p: any) => p.node_id));
        }
      }
    } catch {
      // Ignore poll error
    }
  }, [getApiUrl, nodeId]);

  // Fetch sync metrics & track 2-way ACK verification
  const fetchSyncMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/sync/status`);
      if (res.ok) {
        const data = await res.json();
        const pendingCount = data.pending_outbox_count || 0;
        setOutboxCount(pendingCount);
        setSyncStatus(data.status || 'synchronized');

        if (prevOutboxCountRef.current !== null && prevOutboxCountRef.current > 0 && pendingCount === 0) {
          const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setNotifications((prev) => [
            {
              id: `notif-sync-ack-${Date.now()}`,
              type: 'sync_verified',
              title: '2-Way Handshake Verified',
              detail: 'Bidirectional Delta Sync ACK confirmed: all pending outbox events acknowledged across mesh!',
              timestamp: timeStr,
              icon: '✅',
              badgeColor: '#10b981',
            },
            ...prev.slice(0, 39),
          ]);
        }
        prevOutboxCountRef.current = pendingCount;
      }
    } catch {
      // Ignore poll error
    }
  }, [getApiUrl]);

  // Fetch pending AI correlation clusters synchronized from backend
  const fetchClusters = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/incidents/clusters/pending`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setClusters(data.filter((c: any) => !dismissedReportIdsRef.current.has(c.reportId)));
        }
      }
    } catch {
      // ignore
    }
  }, [getApiUrl]);

  // Fetch incidents & track incoming creations
  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/incidents/`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          const markers: MapIncidentMarker[] = data.map((item: any) => ({
            id: item.incident_id || item.id || `inc-${Math.random()}`,
            title: item.title || 'Untitled Incident',
            category: item.category || 'general',
            severity: (item.severity?.toLowerCase() as any) || 'medium',
            lat: item.latitude !== undefined && item.latitude !== null ? item.latitude : null,
            lon: item.longitude !== undefined && item.longitude !== null ? item.longitude : null,
            accuracy: item.accuracy,
            locationSource: item.location_source,
            reportCount: item.report_count || (1 + (item.reports && Array.isArray(item.reports) ? item.reports.length : 0)),
            broadcasterName: item.broadcaster_name || 'Commander',
            summary: item.summary || '',
          }));
          setIncidents(markers);
          if (!selectedIncidentId && markers.length > 0) {
            setSelectedIncidentId(markers[0].id);
          }

          data.forEach((item: any) => {
            const incId = item.incident_id || item.id;
            if (incId && !prevIncidentIdsRef.current.has(incId)) {
              const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              setNotifications((prev) => [
                {
                  id: `notif-inc-${incId}-${Date.now()}`,
                  type: 'incident_created',
                  title: 'Incident Synced',
                  detail: `Incident "${item.title}" (${(item.severity || 'medium').toUpperCase()}) active on tactical mesh map`,
                  timestamp: timeStr,
                  icon: '🚨',
                  badgeColor: item.severity?.toLowerCase() === 'critical' ? '#ef4444' : '#f59e0b',
                },
                ...prev.slice(0, 39),
              ]);
            }
          });
          prevIncidentIdsRef.current = new Set(data.map((item: any) => item.incident_id || item.id));
        }
      }
    } catch {
      // Fallback
    }
  }, [getApiUrl, selectedIncidentId]);

  // Fetch resource requests from backend
  const fetchResources = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/comms/resources`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setResources(
            data.map((item: any) => ({
              id: item.resource_id,
              resourceType: item.resource_type,
              quantity: item.quantity,
              urgency: item.urgency,
              status: item.status,
              requestedBy: item.requester_id || 'Field-Squad',
              incidentId: item.incident_id,
              incidentTitle: item.incident_title,
            }))
          );

          data.forEach((item: any) => {
            const rId = item.resource_id;
            if (item.status === 'dispatched' && !prevDispatchedIdsRef.current.has(rId)) {
              const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              setNotifications((prev) => [
                {
                  id: `notif-disp-${rId}-${Date.now()}`,
                  type: 'resource_dispatched',
                  title: 'Resource Dispatched',
                  detail: `Resource "${item.resource_type}" (Qty: ${item.quantity}) dispatched${item.incident_title ? ` for ${item.incident_title}` : ''}`,
                  timestamp: timeStr,
                  icon: '📦',
                  badgeColor: '#10b981',
                },
                ...prev.slice(0, 39),
              ]);
              prevDispatchedIdsRef.current.add(rId);
            }
          });
        }
      }
    } catch {
      // Ignore poll error
    }
  }, [getApiUrl]);

  // Fetch distributed event feed for remote merges, dispatches, and requests
  const fetchEventsFeed = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/events/feed`);
      if (res.ok) {
        const events = await res.json();
        if (Array.isArray(events)) {
          events.reverse().forEach((ev: any) => {
            if (ev.event_id && !seenEventIdsRef.current.has(ev.event_id)) {
              seenEventIdsRef.current.add(ev.event_id);
              const timeStr = new Date(ev.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              const payload = ev.payload || {};

              if (ev.event_type === 'incident.merged') {
                // Immediately remove merged report cluster from review list
                setClusters((prev) => prev.filter((c) => c.reportId !== payload.report_id && c.reportId !== 'rep-mesh-demo-1'));
                fetchIncidents();
                setNotifications((prev) => [
                  {
                    id: `notif-feed-merge-${ev.event_id}`,
                    type: 'incident_merged',
                    title: 'Incident Merged',
                    detail: `Report #${(payload.report_id || '').slice(0, 8)} merged into "${payload.title || 'Incident'}" by ${payload.merged_by || 'Peer'} (Reports linked: ${payload.report_count || 2})`,
                    timestamp: timeStr,
                    icon: '🔗',
                    badgeColor: '#a855f7',
                    sourceNode: payload.merged_by,
                  },
                  ...prev.slice(0, 39),
                ]);
              } else if (ev.event_type === 'resource.created') {
                fetchResources();
                setNotifications((prev) => [
                  {
                    id: `notif-feed-res-req-${ev.event_id}`,
                    type: 'resource_dispatched',
                    title: 'Resource Requested',
                    detail: `Resource "${payload.resource_type || 'Equipment'}" (Qty: ${payload.quantity || 1}) requested for "${payload.incident_title || 'Incident'}" by ${payload.requester_id || 'Unit'}`,
                    timestamp: timeStr,
                    icon: '📦',
                    badgeColor: '#38bdf8',
                    sourceNode: payload.requester_id,
                  },
                  ...prev.slice(0, 39),
                ]);
              } else if (ev.event_type === 'incident.segregated') {
                if (payload.candidate_id) {
                  dismissedReportIdsRef.current.add(payload.candidate_id);
                  setClusters((prev) => prev.filter((c) => c.reportId !== payload.candidate_id));
                }
              }
            }
          });
        }
      }
    } catch {
      // ignore
    }
  }, [getApiUrl, fetchIncidents, fetchResources]);

  // Periodic polling & 10-second automatic mesh sync loop
  useEffect(() => {
    fetchNodeStatus();
    fetchMeshStatus();
    fetchPeers();
    fetchSyncMetrics();
    fetchClusters();
    fetchIncidents();
    fetchResources();
    fetchEventsFeed();

    // 3-second rapid UI refresh interval
    const refreshInterval = setInterval(() => {
      fetchNodeStatus();
      fetchMeshStatus();
      fetchPeers();
      fetchSyncMetrics();
      fetchClusters();
      fetchIncidents();
      fetchResources();
      fetchEventsFeed();
    }, 3000);

    // 10-second automatic distributed delta sync interval
    const syncInterval = setInterval(async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 4000);
        await fetch(`${getApiUrl()}/sync/vector`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ vector: {} }),
          signal: controller.signal,
        });
        clearTimeout(timeout);
        fetchSyncMetrics();
        fetchClusters();
        fetchIncidents();
        fetchResources();
        fetchEventsFeed();
      } catch {
        // ignore
      }
    }, 10000);

    return () => {
      clearInterval(refreshInterval);
      clearInterval(syncInterval);
    };
  }, [fetchNodeStatus, fetchMeshStatus, fetchPeers, fetchSyncMetrics, fetchClusters, fetchIncidents, fetchResources, fetchEventsFeed, getApiUrl]);

  // Save Node Setup with AbortController timeout protection
  const handleSaveNodeConfig = async (name: string, role: string) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4500);
    try {
      const res = await fetch(`${getApiUrl()}/node/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, role }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned error (${res.status})`);
      }
      const data = await res.json();
      setNodeId(data.node_id);
      setNodeName(data.name);
      setNodeRole(data.role);
      setIsConfigured(true);
      setShowConfigModal(false);
      // Publish real MESH_INITIALIZED activity event to TacticalEventBus
      const peerCount = peers.length;
      TacticalEventBus.publish({
        type: 'MESH_INITIALIZED',
        severity: 'SUCCESS',
        nodeId: data.node_id,
        actor: data.name || 'Commander',
        title: '🕸 Mesh Initialized',
        description: `Commander node "${data.name}" initialized the emergency mesh.\nStatus: ${peerCount > 0 ? `${peerCount} peers connected` : 'Standalone — 0 peers'}`,
        metadata: { role: data.role, peers: peerCount, api_port: data.api_port || 8000 },
      });

      fetchMeshStatus();
      fetchPeers();
    } catch (err: any) {
      clearTimeout(timeout);
      throw new Error(err.name === 'AbortError' ? 'Connection to local mesh daemon timed out.' : (err.message || 'Failed to save node configuration.'));
    }
  };

  // Continue in Offline Standalone Mode
  const handleContinueOffline = (name: string, role: string) => {
    setNodeName(name);
    setNodeRole(role);
    setIsConfigured(true);
    setShowConfigModal(false);
    setMeshState('OFFLINE');
    localStorage.setItem('resqmesh_offline_node', JSON.stringify({ name, role }));
    TacticalEventBus.publish({
      type: 'MESH_INITIALIZED',
      severity: 'SUCCESS',
      nodeId: nodeId || 'Local-Commander',
      actor: name || 'Commander',
      title: '🕸 Mesh Initialized',
      description: `Commander node "${name}" initialized the emergency mesh in standalone mode.\nStatus: Standalone — 0 peers`,
      metadata: { role, peers: 0, offline: true },
    });
  };

  // Trigger Force Sync
  const handleTriggerSync = async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const res = await fetch(`${getApiUrl()}/node/sync/force`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned error (${res.status})`);
      }
      const syncResult = await res.json();

      // Refresh all dependent states
      await Promise.all([
        fetchSyncMetrics(),
        fetchClusters(),
        fetchIncidents(),
        fetchResources(),
        fetchEventsFeed(),
        fetchPeers(),
        fetchMeshStatus(),
      ]);

      // Publish MESH_DELTA_SYNC_COMPLETED event to TacticalEventBus
      const appliedCount = syncResult.applied_changes || 0;
      const peerCount = syncResult.peer_count || peers.length;
      TacticalEventBus.publish({
        type: 'MESH_DELTA_SYNC_COMPLETED',
        severity: 'SUCCESS',
        nodeId: nodeId || syncResult.node_id || 'Commander',
        actor: nodeName || syncResult.node_name || 'Commander',
        title: '✓ Delta Sync Completed',
        description: `Delta synchronization completed for ${nodeName || 'Command-Center'}.\n${appliedCount} change(s) applied • ${peerCount} peer(s) active • Mesh topology refreshed.`,
        metadata: {
          applied_changes: appliedCount,
          peer_count: peerCount,
          delivered_outbox: syncResult.delivered_outbox || 0,
          timestamp: syncResult.timestamp || Date.now() / 1000,
        },
      });

      return syncResult;
    } catch (err: any) {
      clearTimeout(timeout);
      const msg = err.name === 'AbortError' ? 'Delta sync timed out after 8 seconds.' : (err.message || 'Delta synchronization failed.');
      throw new Error(msg);
    }
  };

  // Manual Direct Peer Connection
  const handleConnectPeer = async (address: string) => {
    const res = await fetch(`${getApiUrl()}/peers/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ peer_address: address }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to connect to peer.');
    }
    await fetchPeers();
    await fetchSyncMetrics();
    await fetchIncidents();
  };

  // Create Incident
  const handleCreateIncident = async (data: any) => {
    const { files, ...incidentPayload } = data;
    const res = await fetch(`${getApiUrl()}/incidents/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(incidentPayload),
    });
    if (!res.ok) {
      throw new Error('Failed to broadcast incident.');
    }
    const created = await res.json();
    const incId = created.incident_id || created.id;

    // Upload attached photos if selected
    if (files && files.length > 0 && incId) {
      try {
        const formData = new FormData();
        for (const f of files) {
          formData.append('files', f);
        }
        await fetch(`${getApiUrl()}/incidents/${incId}/attachments`, {
          method: 'POST',
          body: formData,
        });
      } catch (attErr) {
        console.error('[ResQMesh] Failed to upload incident photos:', attErr);
      }
    }

    await fetchIncidents();
    await fetchClusters();
    await fetchSyncMetrics();
    // Force immediate delta sync so all active peers receive this incident instantly
    await handleTriggerSync();
  };

  // Create Resource Request Tied to Incident (Auto-creating Incident if requested)
  const handleCreateResourceRequest = async (data: {
    incident_id: string;
    resource_type: string;
    quantity: number;
    urgency: string;
  }) => {
    let finalIncId = data.incident_id;
    let incTitle = 'Active Incident';

    if (data.incident_id === 'new_auto' || !incidents.some((i) => i.id === data.incident_id)) {
      const autoTitle = `Incident: ${data.resource_type} Emergency`;
      try {
        const incRes = await fetch(`${getApiUrl()}/incidents/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: autoTitle,
            category: 'general',
            severity: data.urgency,
            latitude: 12.9716,
            longitude: 77.5946,
            summary: `Tactical emergency incident automatically created for requested resource: ${data.quantity}x ${data.resource_type}`,
            broadcaster_name: nodeName || 'Responder',
          }),
        });
        if (incRes.ok) {
          const createdInc = await incRes.json();
          finalIncId = createdInc.incident_id || createdInc.id;
          incTitle = createdInc.title;
          await fetchIncidents();
        }
      } catch {
        // Continue with local assignment
      }
    } else {
      const targetInc = incidents.find((i) => i.id === data.incident_id);
      if (targetInc) incTitle = targetInc.title;
    }

    const res = await fetch(`${getApiUrl()}/comms/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...data,
        incident_id: finalIncId,
        requester_id: nodeName || 'Field-Unit',
        status: 'pending',
      }),
    });
    if (!res.ok) {
      throw new Error('Failed to broadcast resource request.');
    }

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotifications((prev) => [
      {
        id: `notif-local-res-${Date.now()}`,
        type: 'resource_dispatched',
        title: 'Resource Requested',
        detail: `Resource "${data.resource_type}" (Qty: ${data.quantity}) requested for "${incTitle}"`,
        timestamp: timeStr,
        icon: '📦',
        badgeColor: '#38bdf8',
        sourceNode: nodeName,
      },
      ...prev.slice(0, 39),
    ]);

    TacticalEventBus.publish({
      type: 'RESOURCE_REQUESTED',
      severity: 'WARNING',
      actor: nodeName || 'Field Unit',
      title: `Resource Requested: ${data.resource_type} ×${data.quantity}`,
      description: `Urgent supply/personnel request logged for "${incTitle}". Urgency: ${data.urgency.toUpperCase()}.`,
      metadata: { item: data.resource_type, quantity: data.quantity, urgency: data.urgency, incidentTitle: incTitle },
    });

    await fetchResources();
    await fetchSyncMetrics();
    await handleTriggerSync();
  };

  // Rescind Resource Request
  const handleRescindResource = async (id: string) => {
    const resItem = resources.find((r) => r.id === id);
    const resTitle = resItem ? resItem.resourceType : 'Resource';

    setResources((prev) => prev.filter((r) => r.id !== id));

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotifications((prev) => [
      {
        id: `notif-rescind-${Date.now()}`,
        type: 'resource_dispatched',
        title: 'Resource Rescinded',
        detail: `Tactical request for "${resTitle}" was rescinded across mesh`,
        timestamp: timeStr,
        icon: '🗑️',
        badgeColor: '#ef4444',
        sourceNode: nodeName,
      },
      ...prev.slice(0, 39),
    ]);

    try {
      await fetch(`${getApiUrl()}/comms/resources/${id}?status_val=rescinded`, {
        method: 'PATCH',
      });
      await fetchResources();
      await fetchSyncMetrics();
      await handleTriggerSync();
    } catch {
      // ignore
    }
  };

  // Cluster Merge Handler
  const handleApproveMerge = async (reportId: string, incidentId: string) => {
    const targetInc = incidents.find((i) => i.id === incidentId) || incidents[0];
    const targetTitle = targetInc ? targetInc.title : 'Active Incident';
    const targetCluster = clusters.find((c) => c.reportId === reportId);

    setClusters(clusters.filter((c) => c.reportId !== reportId));
    setIncidents(
      incidents.map((inc) =>
        inc.id === incidentId ? { ...inc, reportCount: inc.reportCount + 1 } : inc
      )
    );

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotifications((prev) => [
      {
        id: `notif-merge-${reportId}-${Date.now()}`,
        type: 'incident_merged',
        title: 'Incident Merged',
        detail: `Candidate #${reportId.slice(0, 8)} approved and merged into "${targetTitle}"`,
        timestamp: timeStr,
        icon: '🔗',
        badgeColor: '#a855f7',
        sourceNode: nodeName,
      },
      ...prev.slice(0, 39),
    ]);

    TacticalEventBus.publish({
      type: 'INCIDENT_MERGED',
      severity: 'SUCCESS',
      actor: nodeName || 'Commander',
      title: `Incidents Merged: "${targetTitle}"`,
      description: `Report #${reportId.slice(0, 8)} approved & merged into "${targetTitle}". Reports linked: ${targetInc ? targetInc.reportCount + 1 : 2}.`,
      metadata: { reportId, incidentId, title: targetTitle },
    });

    try {
      await fetch(`${getApiUrl()}/incidents/${incidentId}/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: reportId,
          summary_note: targetCluster ? targetCluster.description : 'Duplicate incident verified & merged into master incident',
        }),
      });
      await fetchIncidents();
      await fetchClusters();
      await fetchSyncMetrics();
      await handleTriggerSync();
    } catch {
      // ignore
    }
  };

  // Dedicated handler for IncidentMergeAiCard
  const handleMergeCandidatePair = async (primaryId: string, duplicateId: string) => {
    const primary = incidents.find((i) => i.id === primaryId);
    const dup = incidents.find((i) => i.id === duplicateId);
    const title = primary ? primary.title : 'Active Incident';

    // Remove duplicate from active list and increment primary count
    setIncidents((prev) =>
      prev
        .filter((i) => i.id !== duplicateId)
        .map((i) => (i.id === primaryId ? { ...i, reportCount: (i.reportCount || 1) + 1 } : i))
    );

    TacticalEventBus.publish({
      type: 'INCIDENT_MERGED',
      severity: 'SUCCESS',
      actor: nodeName || 'Commander',
      title: `Incidents Merged: "${title}"`,
      description: `Report #${duplicateId.slice(0, 8)} consolidated into #${primaryId.slice(0, 8)} ("${title}").`,
      metadata: { primaryId, duplicateId, title },
    });

    try {
      await fetch(`${getApiUrl()}/incidents/${primaryId}/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: duplicateId,
          summary_note: `Consolidated via Incident Merge AI: ${dup?.title || ''}`,
        }),
      });
      await fetchIncidents();
      await fetchClusters();
      await fetchSyncMetrics();
      await handleTriggerSync();
    } catch {
      // ignore
    }
  };

  const handleRejectAsNew = async (reportId: string) => {
    const cluster = clusters.find((c) => c.reportId === reportId);
    if (!cluster) return;

    dismissedReportIdsRef.current.add(reportId);
    setClusters((prev) => prev.filter((c) => c.reportId !== reportId));

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotifications((prev) => [
      {
        id: `notif-segregated-${reportId}-${Date.now()}`,
        type: 'incident_created',
        title: 'Incident Kept Segregated',
        detail: `Incident #${reportId.slice(0, 8)} confirmed as independent operational event`,
        timestamp: timeStr,
        icon: '🛡️',
        badgeColor: '#38bdf8',
        sourceNode: nodeName,
      },
      ...prev.slice(0, 39),
    ]);

    try {
      await fetch(`${getApiUrl()}/incidents/clusters/dismiss`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: reportId,
          target_incident_id: cluster.targetIncidentId,
        }),
      });
      await fetchClusters();
      await handleTriggerSync();
    } catch {
      // ignore
    }
  };

  const handleDispatchResource = async (id: string) => {
    const resItem = resources.find((r) => r.id === id);
    const resTitle = resItem ? resItem.resourceType : 'Resource';

    setResources(
      resources.map((r) => (r.id === id ? { ...r, status: 'dispatched' } : r))
    );

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotifications((prev) => [
      {
        id: `notif-local-disp-${Date.now()}`,
        type: 'resource_dispatched',
        title: 'Resource Dispatched',
        detail: `Tactical dispatch authorized for "${resTitle}" across mesh`,
        timestamp: timeStr,
        icon: '📦',
        badgeColor: '#10b981',
        sourceNode: nodeName,
      },
      ...prev.slice(0, 39),
    ]);

    TacticalEventBus.publish({
      type: 'RESOURCE_DISPATCHED',
      severity: 'SUCCESS',
      actor: nodeName || 'Commander',
      title: `Resource Dispatched: "${resTitle}"`,
      description: `Tactical dispatch authorized for "${resTitle}". Unit en route to emergency sector.`,
      metadata: { resourceId: id, item: resTitle },
    });

    try {
      await fetch(`${getApiUrl()}/comms/resources/${id}?status_val=dispatched`, {
        method: 'PATCH',
      });
      await fetchResources();
      await fetchSyncMetrics();
      await handleTriggerSync();
    } catch {
      // ignore
    }
  };

  // Operational incidents strictly from live mesh and local node (Memoized)
  const displayIncidents: MapIncidentMarker[] = useMemo(() => {
    return incidents;
  }, [incidents]);

  const criticalIncidents = useMemo(
    () => displayIncidents.filter((i) => i.severity.toLowerCase() === 'critical'),
    [displayIncidents]
  );
  const pendingResources = useMemo(
    () => resources.filter((r) => r.status.toLowerCase() === 'pending'),
    [resources]
  );
  const dispatchedResourcesCount = useMemo(
    () => resources.filter((r) => r.status.toLowerCase() === 'dispatched').length,
    [resources]
  );

  return (
    <div
      style={{
        background: colors.bgApp,
        minHeight: '100vh',
        maxHeight: '100vh',
        color: colors.textPrimary,
        fontFamily: fonts.sans,
        display: 'flex',
        overflow: 'hidden',
        boxSizing: 'border-box',
      }}
    >
      {/* 1. Left Vertical Navigation Sidebar */}
      <SidebarNav
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
        }}
        incidentCount={displayIncidents.length}
        criticalCount={criticalIncidents.length}
        pendingResourceCount={pendingResources.length}
        peerCount={peers.length}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* 2. Main Content Wrapper */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Top Header Bar */}
        <TopHeader
          activeTab={activeTab}
          nodeName={nodeName}
          nodeRole={nodeRole}
          peerCount={peers.length}
          meshState={meshState}
          unreadNotificationCount={notifications.length}
          onOpenNotifications={() => setShowNotificationsDrawer(!showNotificationsDrawer)}
          onOpenBroadcastModal={() => setShowCreateModal(true)}
          onOpenConfigModal={() => setShowConfigModal(true)}
          onOpenPeersModal={() => setShowPeersModal(true)}
        />

        {/* Dynamic Body Content */}
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px 28px',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            gap: '24px',
          }}
        >
          {/* TAB 1: DASHBOARD (Hero 3D Globe + Right Column Panels + Bottom Metrics) */}
          {activeTab === 'dashboard' && (
            <>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(500px, 1.7fr) minmax(320px, 1fr)',
                  gap: '24px',
                  alignItems: 'stretch',
                }}
              >
                {/* Center Column: 3D Earth Globe + Live Tactical Activity Feed */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
                  <div style={{ height: '460px', width: '100%' }}>
                    <GlobeHeroView
                      ref={globeHeroRef}
                      incidents={displayIncidents}
                      selectedIncidentId={selectedIncidentId}
                      onSelectIncident={(id) => setSelectedIncidentId(id)}
                      onOpenDetailsModal={(inc) => setDetailsModalIncident(inc)}
                      height="100%"
                    />
                  </div>

                  {/* Live Tactical Activity Feed directly below 3D globe */}
                  <LiveTacticalActivityFeed
                    onSelectIncidentId={(id) => setSelectedIncidentId(id)}
                  />
                </div>

                {/* Right Column: Recent Incidents, Active Teams, Quick Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Recent Incidents Panel */}
                  <div
                    style={{
                      background: colors.bgSurface,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.xl,
                      padding: '18px 20px',
                      boxShadow: shadows.card,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: '800', color: colors.textPrimary }}>
                        Recent Incidents
                      </h3>
                      <button
                        type="button"
                        onClick={() => setActiveTab('incidents')}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: colors.accentElectric,
                          fontSize: '0.74rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        View All ({displayIncidents.length}) →
                      </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                      {displayIncidents.length === 0 ? (
                        <div style={{ padding: '24px 12px', textAlign: 'center', color: colors.textMuted, fontSize: '0.78rem' }}>
                          <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>🛡️</div>
                          <div style={{ fontWeight: '700', color: colors.textSecondary }}>No Active Incidents</div>
                          <div style={{ fontSize: '0.70rem', marginTop: '2px' }}>System standing by. Use "Broadcast Alert" to log an incident or await mesh sync.</div>
                        </div>
                      ) : (
                        displayIncidents.slice(0, 4).map((inc) => {
                        const isCritical = inc.severity.toLowerCase() === 'critical';
                        const isHigh = inc.severity.toLowerCase() === 'high';
                        const dotColor = isCritical ? colors.critical : isHigh ? colors.high : inc.severity.toLowerCase() === 'medium' ? colors.medium : colors.low;
                        return (
                          <div
                            key={inc.id}
                            onClick={() => {
                              setSelectedIncidentId(inc.id);
                              if (inc.lat && inc.lon) {
                                globeHeroRef.current?.flyToIncident(inc.lat, inc.lon, 900);
                              }
                            }}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '8px 10px',
                              borderRadius: radii.md,
                              background: selectedIncidentId === inc.id ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                              border: `1px solid ${selectedIncidentId === inc.id ? colors.accentElectric : colors.borderSubtle}`,
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                            }}
                            onMouseEnter={(e) => {
                              if (selectedIncidentId !== inc.id) {
                                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (selectedIncidentId !== inc.id) {
                                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                              }
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                              <span
                                style={{
                                  width: '8px',
                                  height: '8px',
                                  borderRadius: '50%',
                                  background: dotColor,
                                  flexShrink: 0,
                                }}
                              />
                              <div style={{ overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                                <div style={{ color: colors.textPrimary, fontSize: '0.82rem', fontWeight: '700', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                  {inc.title}
                                </div>
                                <div style={{ color: colors.textMuted, fontSize: '0.7rem' }}>
                                  {inc.lat !== null && inc.lon !== null
                                    ? (inc.broadcasterName || 'Field Sector')
                                    : 'Location: Manual / Coordinates unavailable'}
                                </div>
                              </div>
                            </div>
                            <span style={{ color: colors.textMuted, fontSize: '0.7rem', flexShrink: 0 }}>
                              Active
                            </span>
                          </div>
                        );
                      }))}
                    </div>
                  </div>

                  {/* Incident Duplicate / Merge AI Panel */}
                  <IncidentMergeAiCard
                    incidents={incidents}
                    onMerge={handleMergeCandidatePair}
                    nodeName={nodeName}
                  />

                  {/* On-Device AI Advisor Panel */}
                  <OnDeviceAdvisorCard apiUrl={getApiUrl()} />

                  {/* Quick Actions Panel */}
                  <div
                    style={{
                      background: colors.bgSurface,
                      border: `1px solid ${colors.borderSubtle}`,
                      borderRadius: radii.xl,
                      padding: '16px 20px',
                      boxShadow: shadows.card,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                    }}
                  >
                    <h3 style={{ margin: 0, fontSize: '0.88rem', fontWeight: '800', color: colors.textPrimary }}>
                      Quick Actions
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        style={{
                          padding: '8px 10px',
                          borderRadius: radii.sm,
                          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%)',
                          border: `1px solid ${colors.criticalBorder}`,
                          color: colors.critical,
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          justifyContent: 'center',
                        }}
                      >
                        <span>🚨</span> Broadcast Alert
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowRequestResourceModal(true)}
                        style={{
                          padding: '8px 10px',
                          borderRadius: radii.sm,
                          background: 'rgba(56, 189, 248, 0.08)',
                          border: `1px solid ${colors.borderFocus}`,
                          color: colors.accentElectric,
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          justifyContent: 'center',
                        }}
                      >
                        <span>📦</span> Request Logistics
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowPeersModal(true)}
                        style={{
                          padding: '8px 10px',
                          borderRadius: radii.sm,
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: `1px solid ${colors.borderSubtle}`,
                          color: colors.textSecondary,
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          justifyContent: 'center',
                        }}
                      >
                        <span>📡</span> Mesh Peers
                      </button>

                      <button
                        type="button"
                        onClick={() => setActiveTab('advisor')}
                        style={{
                          padding: '8px 10px',
                          borderRadius: radii.sm,
                          background: 'rgba(99, 102, 241, 0.1)',
                          border: '1px solid rgba(99, 102, 241, 0.35)',
                          color: '#a5b4fc',
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          justifyContent: 'center',
                        }}
                      >
                        <span>🧠</span> AI Advisor
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Metrics Statistics */}
              <DashboardMetrics
                totalIncidents={displayIncidents.length}
                criticalIncidents={criticalIncidents.length}
                activeTeamsCount={5}
                dispatchedResourcesCount={dispatchedResourcesCount}
              />
            </>
          )}

          {/* TAB 2: FULL VIEWPORT 3D GLOBE */}
          {activeTab === 'globe' && (
            <div style={{ height: 'calc(100vh - 130px)', width: '100%' }}>
              <GlobeHeroView
                ref={globeHeroRef}
                incidents={displayIncidents}
                selectedIncidentId={selectedIncidentId}
                onSelectIncident={(id) => setSelectedIncidentId(id)}
                onOpenDetailsModal={(inc) => setDetailsModalIncident(inc)}
                height="100%"
              />
            </div>
          )}

          {/* TAB 3: INCIDENTS STREAM */}
          {activeTab === 'incidents' && (
            <IncidentsView
              incidents={displayIncidents}
              clusters={clusters}
              onSelectIncident={(id) => setSelectedIncidentId(id)}
              onOpenDetailsModal={(inc) => setDetailsModalIncident(inc)}
              onApproveMerge={handleApproveMerge}
              onRejectAsNew={handleRejectAsNew}
              onOpenCreateModal={() => setShowCreateModal(true)}
            />
          )}

          {/* TAB 4: RESOURCES & LOGISTICS */}
          {activeTab === 'resources' && (
            <ResourcesView
              resources={resources}
              onDispatch={handleDispatchResource}
              onRescind={handleRescindResource}
              onOpenRequestModal={() => setShowRequestResourceModal(true)}
              nodeRole={nodeRole}
            />
          )}

          {/* TAB 5: ACTIVE RESCUE TEAMS */}
          {activeTab === 'teams' && <TeamsView />}

          {/* TAB 6: ANALYTICS & INSIGHTS */}
          {activeTab === 'analytics' && (
            <AnalyticsView
              incidents={displayIncidents}
              dispatchedResourceCount={dispatchedResourcesCount}
            />
          )}

          {/* TAB 7: AI TACTICAL ADVISOR */}
          {activeTab === 'advisor' && <AdvisorView apiUrl={getApiUrl()} />}

          {/* TAB 8: NODE & SYSTEM SETTINGS */}
          {activeTab === 'settings' && (
            <SettingsView
              nodeId={nodeId}
              nodeName={nodeName}
              nodeRole={nodeRole}
              apiPort={apiPort}
              peerCount={peers.length}
              syncStatus={syncStatus}
              onOpenConfigModal={() => setShowConfigModal(true)}
              onTriggerSync={handleTriggerSync}
            />
          )}
        </main>
      </div>

      {/* Slide-Over Drawer: Live Tactical Notification Stream */}
      {showNotificationsDrawer && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            right: 0,
            bottom: 0,
            width: '380px',
            background: colors.bgGlassElevated,
            backdropFilter: 'blur(24px)',
            borderLeft: `1px solid ${colors.borderMedium}`,
            boxShadow: shadows.elevated,
            zIndex: 900,
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>🔔</span>
              <h3 style={{ margin: 0, color: colors.textPrimary, fontSize: '1rem', fontWeight: '800' }}>
                Live Tactical Stream
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setShowNotificationsDrawer(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: colors.textMuted,
                fontSize: '1.2rem',
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <LiveNotificationStream
              items={notifications}
              onClear={() => setNotifications([])}
            />
          </div>
        </div>
      )}

      {/* First Run Onboarding Modal */}
      <FirstRunModal
        isOpen={showConfigModal}
        initialName={nodeName}
        initialRole={nodeRole}
        canClose={isConfigured}
        onClose={() => setShowConfigModal(false)}
        onSave={handleSaveNodeConfig}
        onContinueOffline={handleContinueOffline}
      />

      {/* Peer Mesh Topology Modal */}
      <PeerTopologyModal
        isOpen={showPeersModal}
        onClose={() => setShowPeersModal(false)}
        peers={peers}
        onTriggerSync={handleTriggerSync}
        onConnectPeer={handleConnectPeer}
        apiUrl={getApiUrl()}
        nodeName={nodeName}
        nodeRole={nodeRole}
      />

      {/* Broadcast Incident Modal */}
      <CreateIncidentModal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setIsPickingLocation(false);
        }}
        onSubmit={handleCreateIncident}
        onStartPickOnMap={() => {
          setShowCreateModal(false);
          setActiveTab('globe');
        }}
        externalPickedCoords={pickedCoords}
        onClearPickedCoords={() => setPickedCoords(null)}
      />

      {/* Request Resource Tied to Incident Modal */}
      <RequestResourceModal
        isOpen={showRequestResourceModal}
        onClose={() => setShowRequestResourceModal(false)}
        incidents={displayIncidents}
        selectedIncidentId={selectedIncidentId}
        onSubmit={handleCreateResourceRequest}
      />

      {/* Incident Details & Resource Request Quick Trigger Modal */}
      <IncidentDetailsModal
        incident={detailsModalIncident}
        isOpen={!!detailsModalIncident}
        onClose={() => setDetailsModalIncident(null)}
        onRequestResources={(incId) => {
          setSelectedIncidentId(incId);
          setShowRequestResourceModal(true);
        }}
        resources={resources}
        apiUrl={getApiUrl()}
      />
    </div>
  );
};

export default App;
