import React, { useState, useEffect, useRef } from 'react';

export interface PeerNode {
  node_id: string;
  name: string;
  role: string;
  ip_address: string;
  api_port: number;
  last_seen?: number;
  latency_ms?: number;
}

export interface MeshTopologyNode {
  id: string;
  name: string;
  role: string;
  is_local: boolean;
  hop_count: number;
  next_hop?: string;
  latency_ms?: number;
  link_quality?: string;
  status: string;
}

export interface MeshTopologyLink {
  source: string;
  target: string;
  hops: number;
  latency_ms: number;
  quality: string;
  direct: boolean;
}

export interface MeshRouteItem {
  dest_id: string;
  next_hop_id: string;
  hop_count: number;
  latency_ms: number;
  relay_path: string[];
  link_quality: string;
  last_updated: number;
  age_seconds: number;
}

export interface SyncNotification {
  type: 'success' | 'error';
  title: string;
  message: string;
  details?: string;
}

interface PeerTopologyModalProps {
  isOpen: boolean;
  onClose: () => void;
  peers: PeerNode[];
  onTriggerSync: () => Promise<any>;
  onConnectPeer?: (address: string) => Promise<void>;
  apiUrl?: string;
  nodeName?: string;
  nodeRole?: string;
}

export const PeerTopologyModal: React.FC<PeerTopologyModalProps> = ({
  isOpen,
  onClose,
  peers,
  onTriggerSync,
  onConnectPeer,
  apiUrl = 'http://127.0.0.1:8000',
  nodeName = 'Local Commander',
  nodeRole = 'commander',
}) => {
  const [activeTab, setActiveTab] = useState<'visual' | 'peers' | 'routes'>('visual');
  const [syncing, setSyncing] = useState(false);
  const [syncNotification, setSyncNotification] = useState<SyncNotification | null>(null);
  const [manualIp, setManualIp] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const autoDismissTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Live topology and routing data from backend
  const [topology, setTopology] = useState<{
    local_node_id: string;
    total_nodes: number;
    direct_peer_count: number;
    relayed_node_count: number;
    nodes: MeshTopologyNode[];
    links: MeshTopologyLink[];
    routes: MeshRouteItem[];
  } | null>(null);

  const fetchTopology = async () => {
    try {
      const res = await fetch(`${apiUrl}/node/topology`);
      if (res.ok) {
        const data = await res.json();
        setTopology(data);
      }
    } catch {
      // Fallback to peers if server route unreachable
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTopology();
      const interval = setInterval(fetchTopology, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen, apiUrl]);

  useEffect(() => {
    return () => {
      if (autoDismissTimerRef.current) {
        clearTimeout(autoDismissTimerRef.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  const handleSync = async () => {
    if (syncing) return; // Concurrency protection against double-click
    setSyncing(true);
    setSyncNotification(null);

    try {
      const result = await onTriggerSync();
      await fetchTopology();

      const changeCount = result?.applied_changes ?? 0;
      const peerCount = result?.peer_count ?? (topology?.direct_peer_count ?? peers.length);

      setSyncNotification({
        type: 'success',
        title: 'Operation Completed Successfully',
        message: 'Delta synchronization completed. Mesh topology and routing information updated.',
        details: `${changeCount} change(s) applied • ${peerCount} peer(s) active in mesh • Topology refreshed`,
      });

      if (autoDismissTimerRef.current) clearTimeout(autoDismissTimerRef.current);
      autoDismissTimerRef.current = setTimeout(() => {
        setSyncNotification(null);
      }, 4000);
    } catch (err: any) {
      setSyncNotification({
        type: 'error',
        title: 'Delta Sync Failed',
        message: err.message || 'Unable to synchronize with mesh peers.',
      });

      if (autoDismissTimerRef.current) clearTimeout(autoDismissTimerRef.current);
      autoDismissTimerRef.current = setTimeout(() => {
        setSyncNotification(null);
      }, 6000);
    } finally {
      setSyncing(false);
    }
  };

  const handleConnectManual = async () => {
    if (!manualIp.trim() || !onConnectPeer || connecting) return;
    setConnecting(true);
    setSyncNotification(null);
    try {
      await onConnectPeer(manualIp.trim());
      await fetchTopology();
      setSyncNotification({
        type: 'success',
        title: 'Operation Completed Successfully',
        message: `Connected to peer at ${manualIp.trim()} successfully!`,
      });
      if (autoDismissTimerRef.current) clearTimeout(autoDismissTimerRef.current);
      autoDismissTimerRef.current = setTimeout(() => {
        setSyncNotification(null);
      }, 4000);
      setManualIp('');
    } catch (err: any) {
      setSyncNotification({
        type: 'error',
        title: 'Connection Failed',
        message: err.message || 'Could not connect to manual peer address.',
      });
    } finally {
      setConnecting(false);
    }
  };

  // Combine direct peers and topology nodes dynamically
  const displayNodes: MeshTopologyNode[] = topology?.nodes && topology.nodes.length > 0
    ? topology.nodes
    : [
        {
          id: 'local-node',
          name: nodeName || 'Local Commander',
          role: nodeRole || 'commander',
          is_local: true,
          hop_count: 0,
          status: 'online',
        },
        ...peers.map((p) => ({
          id: p.node_id,
          name: p.name || p.node_id,
          role: p.role,
          is_local: false,
          hop_count: 1,
          latency_ms: p.latency_ms || 15.0,
          link_quality: 'EXCELLENT',
          status: 'online',
        })),
      ];

  const displayLinks: MeshTopologyLink[] = topology?.links && topology.links.length > 0
    ? topology.links
    : peers.map((p) => ({
        source: 'local-node',
        target: p.node_id,
        hops: 1,
        latency_ms: p.latency_ms || 15.0,
        quality: 'EXCELLENT',
        direct: true,
      }));

  const displayRoutes: MeshRouteItem[] = topology?.routes ?? peers.map((p) => ({
    dest_id: p.node_id,
    next_hop_id: p.node_id,
    hop_count: 1,
    latency_ms: p.latency_ms || 12.0,
    relay_path: [p.node_id],
    link_quality: 'EXCELLENT',
    last_updated: Date.now() / 1000,
    age_seconds: 2,
  }));

  const localNode = displayNodes.find((n) => n.is_local) || displayNodes[0];
  const directPeers = displayNodes.filter((n) => !n.is_local && n.hop_count === 1);
  const relayedNodes = displayNodes.filter((n) => !n.is_local && n.hop_count > 1);

  const totalNodesCount = topology?.total_nodes ?? displayNodes.length;
  const directPeersCount = topology?.direct_peer_count ?? directPeers.length;
  const relayedCount = topology?.relayed_node_count ?? relayedNodes.length;

  // Visual layout geometry for SVG graph
  const svgWidth = 620;
  const svgHeight = 280;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;

  // Node position map: id -> {x, y}
  const nodePositions: Record<string, { x: number; y: number }> = {};
  nodePositions[localNode.id] = { x: centerX, y: centerY };

  // Arrange direct peers on inner circle (radius 110/90)
  directPeers.forEach((p, idx) => {
    const total = directPeers.length || 1;
    const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
    nodePositions[p.id] = {
      x: centerX + 110 * Math.cos(angle),
      y: centerY + 90 * Math.sin(angle),
    };
  });

  // Arrange relayed nodes on outer circle (radius 210/115)
  relayedNodes.forEach((p, idx) => {
    const total = relayedNodes.length || 1;
    const angle = (idx / total) * 2 * Math.PI - Math.PI / 4;
    nodePositions[p.id] = {
      x: centerX + 210 * Math.cos(angle),
      y: centerY + 115 * Math.sin(angle),
    };
  });

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.85)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      <div
        style={{
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '12px',
          width: '720px',
          maxWidth: '94vw',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div
          style={{
            background: 'linear-gradient(90deg, #1e293b, #0f172a)',
            padding: '16px 24px',
            borderBottom: '1px solid #334155',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>🌐</span>
            <div>
              <h3 style={{ margin: 0, color: '#38bdf8', fontSize: '1.15rem', fontWeight: 700 }}>
                Multi-Hop Peer Mesh Topology & Route Visualizer
              </h3>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.78rem' }}>
                Live ad-hoc peer routing, dynamic hop counting, and multi-hop relay graph
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '1.2rem',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Quick Telemetry Bar */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            borderBottom: '1px solid #334155',
            padding: '10px 24px',
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
            fontSize: '0.76rem',
            overflowX: 'auto',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#94a3b8' }}>Total Nodes:</span>
            <strong style={{ color: '#f8fafc', background: '#334155', padding: '2px 8px', borderRadius: '10px' }}>
              {totalNodesCount}
            </strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#94a3b8' }}>Direct 1-Hop:</span>
            <strong style={{ color: '#34d399', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 8px', borderRadius: '10px' }}>
              {directPeersCount}
            </strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#94a3b8' }}>Multi-Hop Relays:</span>
            <strong style={{ color: '#38bdf8', background: 'rgba(56, 189, 248, 0.15)', padding: '2px 8px', borderRadius: '10px' }}>
              {relayedCount}
            </strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: totalNodesCount > 1 ? '#10b981' : '#38bdf8',
                display: 'inline-block',
                boxShadow: totalNodesCount > 1 ? '0 0 8px #10b981' : 'none',
              }}
            />
            <span style={{ color: totalNodesCount > 1 ? '#10b981' : '#38bdf8', fontWeight: '700' }}>
              {totalNodesCount > 1 ? 'Active Mesh Routing' : 'Standalone Mesh'}
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', background: '#0a0f1d', borderBottom: '1px solid #1e293b', padding: '0 24px' }}>
          {[
            { id: 'visual', label: '🌐 Mesh Topology & Relays' },
            { id: 'peers', label: `📋 Direct Peers (${directPeersCount})` },
            { id: 'routes', label: `🗺️ Routing Table (${displayRoutes.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                color: activeTab === tab.id ? '#38bdf8' : '#94a3b8',
                fontWeight: activeTab === tab.id ? '700' : '500',
                padding: '10px 16px',
                fontSize: '0.82rem',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Temporary Success / Failure Notification Popup */}
          {syncNotification && (
            <div
              style={{
                background: syncNotification.type === 'success'
                  ? 'linear-gradient(135deg, rgba(6, 78, 59, 0.95), rgba(15, 23, 42, 0.95))'
                  : 'linear-gradient(135deg, rgba(127, 29, 29, 0.95), rgba(15, 23, 42, 0.95))',
                border: `1px solid ${syncNotification.type === 'success' ? '#10b981' : '#ef4444'}`,
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '12px',
                boxShadow: syncNotification.type === 'success'
                  ? '0 8px 24px rgba(16, 185, 129, 0.25)'
                  : '0 8px 24px rgba(239, 68, 68, 0.25)',
                animation: 'fadeIn 0.2s ease-in-out',
              }}
            >
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span
                  style={{
                    background: syncNotification.type === 'success' ? '#10b981' : '#ef4444',
                    color: '#ffffff',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.85rem',
                    fontWeight: 'bold',
                    flexShrink: 0,
                  }}
                >
                  {syncNotification.type === 'success' ? '✓' : '⚠'}
                </span>
                <div>
                  <div
                    style={{
                      color: syncNotification.type === 'success' ? '#6ee7b7' : '#fca5a5',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      marginBottom: '2px',
                    }}
                  >
                    {syncNotification.title}
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: '0.78rem' }}>
                    {syncNotification.message}
                  </div>
                  {syncNotification.details && (
                    <div style={{ color: '#94a3b8', fontSize: '0.72rem', marginTop: '3px', fontStyle: 'italic' }}>
                      {syncNotification.details}
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSyncNotification(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  padding: '2px 6px',
                }}
              >
                ✕
              </button>
            </div>
          )}

          {/* TAB 1: INTERACTIVE SVG TOPOLOGY GRAPH */}
          {activeTab === 'visual' && (
            <div>
              <div
                style={{
                  background: '#070B14',
                  border: '1px solid #1e293b',
                  borderRadius: '10px',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <svg width="100%" height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
                  {/* Orbit rings */}
                  <circle cx={centerX} cy={centerY} r="95" fill="none" stroke="rgba(56, 189, 248, 0.12)" strokeDasharray="3 3" />
                  <circle cx={centerX} cy={centerY} r="185" fill="none" stroke="rgba(99, 102, 241, 0.10)" strokeDasharray="4 4" />

                  {/* Links */}
                  {displayLinks.map((link, idx) => {
                    const srcPos = nodePositions[link.source] || { x: centerX, y: centerY };
                    const tgtPos = nodePositions[link.target];
                    if (!tgtPos) return null;
                    const isDirect = link.direct;
                    return (
                      <g key={`link-${idx}`}>
                        <line
                          x1={srcPos.x}
                          y1={srcPos.y}
                          x2={tgtPos.x}
                          y2={tgtPos.y}
                          stroke={isDirect ? '#10b981' : '#38bdf8'}
                          strokeWidth={isDirect ? '2' : '1.5'}
                          strokeDasharray={isDirect ? 'none' : '4 3'}
                          opacity={0.75}
                        />
                        {/* Midpoint latency / hop tag */}
                        <rect
                          x={(srcPos.x + tgtPos.x) / 2 - 18}
                          y={(srcPos.y + tgtPos.y) / 2 - 8}
                          width="36"
                          height="16"
                          rx="4"
                          fill="#0f172a"
                          stroke="#334155"
                        />
                        <text
                          x={(srcPos.x + tgtPos.x) / 2}
                          y={(srcPos.y + tgtPos.y) / 2 + 3}
                          fill={isDirect ? '#34d399' : '#38bdf8'}
                          fontSize="9"
                          textAnchor="middle"
                          fontFamily="monospace"
                        >
                          {isDirect ? `${Math.round(link.latency_ms || 12)}ms` : `${link.hops}h`}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {displayNodes.map((node) => {
                    const pos = nodePositions[node.id];
                    if (!pos) return null;
                    const isLocal = node.is_local;
                    const isSelected = selectedNodeId === node.id;
                    const radius = isLocal ? 22 : 16;
                    const fill = isLocal ? '#0284c7' : node.hop_count === 1 ? '#059669' : '#6366f1';

                    return (
                      <g
                        key={node.id}
                        onClick={() => setSelectedNodeId(isSelected ? null : node.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        {isLocal && (
                          <circle cx={pos.x} cy={pos.y} r={radius + 6} fill="none" stroke="#38bdf8" opacity="0.35" />
                        )}
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r={radius}
                          fill={fill}
                          stroke={isSelected ? '#f8fafc' : '#0f172a'}
                          strokeWidth={isSelected ? '3' : '2'}
                        />
                        <text
                          x={pos.x}
                          y={pos.y + 4}
                          fill="#ffffff"
                          fontSize={isLocal ? '12' : '10'}
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          {isLocal ? 'CMD' : node.hop_count}
                        </text>
                        <text
                          x={pos.x}
                          y={pos.y + radius + 13}
                          fill="#cbd5e1"
                          fontSize="10"
                          fontWeight="600"
                          textAnchor="middle"
                        >
                          {node.name.length > 14 ? `${node.name.slice(0, 12)}...` : node.name}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* Graph Legend */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: '8px',
                    left: '12px',
                    display: 'flex',
                    gap: '12px',
                    fontSize: '0.68rem',
                    color: '#94a3b8',
                    background: 'rgba(15, 23, 42, 0.85)',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    border: '1px solid #334155',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#0284c7' }} /> Local Commander
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#059669' }} /> Direct 1-Hop
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1' }} /> Relayed Multi-Hop
                  </span>
                </div>
              </div>

              {/* Selected Node Details Card */}
              {selectedNodeId && (
                <div
                  style={{
                    marginTop: '12px',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ color: '#f8fafc', fontWeight: '700', fontSize: '0.88rem' }}>
                      {displayNodes.find((n) => n.id === selectedNodeId)?.name}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '0.74rem' }}>
                      ID: #{selectedNodeId.slice(0, 16)} • Role: {displayNodes.find((n) => n.id === selectedNodeId)?.role.toUpperCase()} • Hop Count: {displayNodes.find((n) => n.id === selectedNodeId)?.hop_count}
                    </div>
                  </div>
                  <span
                    style={{
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '0.72rem',
                      fontWeight: '700',
                    }}
                  >
                    Quality: {displayNodes.find((n) => n.id === selectedNodeId)?.link_quality || 'EXCELLENT'}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DIRECT PEER LIST */}
          {activeTab === 'peers' && (
            <div>
              {peers.length === 0 ? (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '30px 20px',
                    background: '#1e293b',
                    borderRadius: '8px',
                    border: '1px dashed #475569',
                  }}
                >
                  <div style={{ fontSize: '2rem', marginBottom: '6px' }}>📡</div>
                  <h4 style={{ margin: '0 0 4px 0', color: '#e2e8f0' }}>Scanning for Mesh Peers...</h4>
                  <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.8rem' }}>
                    No other ResQMesh laptops detected yet. Ensure devices are on the same network or hotspot.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {peers.map((peer) => (
                    <div
                      key={peer.node_id}
                      style={{
                        background: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        padding: '12px 16px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                          <span style={{ fontWeight: '600', color: '#f8fafc', fontSize: '0.92rem' }}>
                            {peer.name || peer.node_id}
                          </span>
                          <span
                            style={{
                              fontSize: '0.68rem',
                              padding: '2px 6px',
                              borderRadius: '10px',
                              fontWeight: 'bold',
                              background: peer.role === 'commander' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                              color: peer.role === 'commander' ? '#38bdf8' : '#10b981',
                            }}
                          >
                            {peer.role.toUpperCase()}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: '#94a3b8', display: 'flex', gap: '12px' }}>
                          <span>🆔 {peer.node_id.slice(0, 14)}...</span>
                          <span>🌐 {peer.ip_address}:{peer.api_port}</span>
                        </div>
                      </div>

                      <span
                        style={{
                          background: 'rgba(16, 185, 129, 0.1)',
                          color: '#10b981',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                        Direct Link
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Direct P2P Link / Cross-Subnet Peer Input */}
              <div
                style={{
                  marginTop: '16px',
                  padding: '12px 14px',
                  background: 'rgba(30, 41, 59, 0.7)',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                }}
              >
                <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginBottom: '6px', fontWeight: '700' }}>
                  🔗 DIRECT P2P LINK / CROSS-SUBNET MANUAL PEER
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="Enter IP:Port (e.g. 192.168.1.15:8000)"
                    value={manualIp}
                    onChange={(e) => setManualIp(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleConnectManual()}
                    style={{
                      flex: 1,
                      background: '#0f172a',
                      border: '1px solid #475569',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      padding: '7px 10px',
                      fontSize: '0.80rem',
                    }}
                  />
                  <button
                    onClick={handleConnectManual}
                    disabled={connecting || !manualIp.trim()}
                    style={{
                      padding: '7px 14px',
                      background: '#10b981',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.80rem',
                      fontWeight: 'bold',
                      cursor: connecting || !manualIp.trim() ? 'not-allowed' : 'pointer',
                      opacity: connecting || !manualIp.trim() ? 0.6 : 1,
                    }}
                  >
                    {connecting ? 'Connecting...' : 'Connect Peer'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: MULTI-HOP ROUTING TABLE */}
          {activeTab === 'routes' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.4fr 1.2fr 0.8fr 0.8fr 1fr',
                  padding: '8px 12px',
                  background: '#0f172a',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: '700',
                  color: '#64748b',
                }}
              >
                <div>DESTINATION</div>
                <div>NEXT-HOP RELAY</div>
                <div>HOPS</div>
                <div>LATENCY</div>
                <div>LINK QUALITY</div>
              </div>

              {displayRoutes.length === 0 ? (
                <div
                  style={{
                    padding: '24px',
                    textAlign: 'center',
                    background: '#1e293b',
                    borderRadius: '6px',
                    border: '1px dashed #334155',
                    color: '#94a3b8',
                    fontSize: '0.82rem',
                  }}
                >
                  No active routes discovered. Connect peers or force delta sync to populate multi-hop routes.
                </div>
              ) : (
                displayRoutes.map((route) => (
                  <div
                    key={route.dest_id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1.4fr 1.2fr 0.8fr 0.8fr 1fr',
                      padding: '10px 12px',
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      fontSize: '0.78rem',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ color: '#f8fafc', fontWeight: '600', fontFamily: 'monospace' }}>
                      #{route.dest_id.slice(0, 14)}
                    </div>
                    <div style={{ color: '#94a3b8', fontFamily: 'monospace' }}>
                      {route.next_hop_id === route.dest_id ? 'Direct (Self)' : `#${route.next_hop_id.slice(0, 10)}`}
                    </div>
                    <div>
                      <span
                        style={{
                          background: route.hop_count === 1 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                          color: route.hop_count === 1 ? '#34d399' : '#38bdf8',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '0.70rem',
                          fontWeight: '700',
                        }}
                      >
                        {route.hop_count} {route.hop_count === 1 ? 'hop' : 'hops'}
                      </span>
                    </div>
                    <div style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>
                      {route.latency_ms} ms
                    </div>
                    <div>
                      <span
                        style={{
                          color: route.link_quality === 'EXCELLENT' ? '#34d399' : '#fbbf24',
                          fontWeight: '700',
                          fontSize: '0.72rem',
                        }}
                      >
                        ● {route.link_quality}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '14px 24px',
            background: '#0a0f1d',
            borderTop: '1px solid #1e293b',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span style={{ fontSize: '0.76rem', color: '#64748b' }}>
            Routing: Dynamic Hop-Limit (TTL 5) • Zero Loop Broadcast Storm Suppression
          </span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleSync}
              disabled={syncing}
              style={{
                padding: '8px 18px',
                background: syncing ? '#0369a1' : '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: '600',
                cursor: syncing ? 'wait' : 'pointer',
                opacity: syncing ? 0.8 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'background 0.2s ease',
              }}
            >
              {syncing && (
                <span
                  style={{
                    display: 'inline-block',
                    width: '12px',
                    height: '12px',
                    border: '2px solid #ffffff',
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                  }}
                />
              )}
              {syncing ? 'Syncing...' : 'Force Delta Sync Now'}
            </button>
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                background: '#334155',
                color: '#cbd5e1',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.82rem',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
