import { TacticalEventBus } from './TacticalEventBus';

export interface DuplicateCandidate {
  id: string; // unique pair id e.g. "dup-${id1}-${id2}"
  primaryIncident: {
    id: string;
    title: string;
    description?: string;
    summary?: string;
    category?: string;
    severity?: string;
    lat?: number | null;
    lon?: number | null;
    latitude?: number | null;
    longitude?: number | null;
    timestamp?: string;
    broadcasterName?: string;
    manualLocation?: any;
  };
  duplicateIncident: {
    id: string;
    title: string;
    description?: string;
    summary?: string;
    category?: string;
    severity?: string;
    lat?: number | null;
    lon?: number | null;
    latitude?: number | null;
    longitude?: number | null;
    timestamp?: string;
    broadcasterName?: string;
    manualLocation?: any;
  };
  similarity: number; // 0 to 100 %
  confidenceLevel: 'HIGH' | 'MEDIUM';
  distanceMeters: number | null;
  timeDiffMinutes: number;
  reasons: string[];
  detectedAt: string;
}

export interface ScanStatus {
  isScanning: boolean;
  totalAnalyzed: number;
  potentialMatchesCount: number;
  lastScanTime: string;
}

/**
 * Computes Haversine distance in meters between two coordinates.
 */
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

/**
 * Tokenizes text into meaningful lowercase word tokens (length >= 3, excluding common stop words).
 */
function tokenize(text: string): Set<string> {
  const stops = new Set(['the', 'and', 'for', 'with', 'near', 'area', 'from', 'reported', 'unit', 'incident']);
  return new Set(
    (text || '')
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length >= 3 && !stops.has(w))
  );
}

/**
 * Jaccard token similarity (0.0 to 1.0)
 */
function jaccardSimilarity(setA: Set<string>, setB: Set<string>): number {
  if (setA.size === 0 || setB.size === 0) return 0;
  let intersection = 0;
  setA.forEach((token) => {
    if (setB.has(token)) intersection++;
  });
  const union = new Set([...setA, ...setB]).size;
  return union > 0 ? intersection / union : 0;
}

/**
 * Active Incident Merge & Duplicate Correlation Engine.
 * Continuously evaluates active incidents across mesh nodes using multi-signal correlation.
 */
export class IncidentMergeAiEngine {
  private static dismissedPairs: Set<string> = new Set();
  private static notifiedCandidateIds: Set<string> = new Set();

  /**
   * Scans a list of active incidents and returns correlation candidate pairs.
   */
  public static scanIncidents(incidents: any[]): { candidates: DuplicateCandidate[]; status: ScanStatus } {
    const candidates: DuplicateCandidate[] = [];
    const valid = (incidents || []).filter((inc) => inc && (inc.id || inc.incident_id));

    for (let i = 0; i < valid.length; i++) {
      for (let j = i + 1; j < valid.length; j++) {
        const a = valid[i];
        const b = valid[j];
        const aId = a.id || a.incident_id;
        const bId = b.id || b.incident_id;

        const pairKey = aId < bId ? `${aId}__${bId}` : `${bId}__${aId}`;
        if (this.dismissedPairs.has(pairKey)) continue;

        const result = this.correlatePair(a, b);
        if (result && result.similarity >= 65) {
          candidates.push({
            id: pairKey,
            primaryIncident: a,
            duplicateIncident: b,
            similarity: result.similarity,
            confidenceLevel: result.similarity >= 85 ? 'HIGH' : 'MEDIUM',
            distanceMeters: result.distanceMeters,
            timeDiffMinutes: result.timeDiffMinutes,
            reasons: result.reasons,
            detectedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          });

          // Publish to TacticalEventBus if newly discovered
          if (!this.notifiedCandidateIds.has(pairKey)) {
            this.notifiedCandidateIds.add(pairKey);
            TacticalEventBus.publish({
              type: 'INCIDENT_DUPLICATE_DETECTED',
              severity: 'WARNING',
              actor: 'Merge AI Engine',
              title: `Duplicate Candidate: ${a.title || aId} ↔ ${b.title || bId}`,
              description: `Correlation confidence: ${result.similarity}%. Reasons: ${result.reasons.join(', ')}`,
              metadata: {
                primaryId: aId,
                duplicateId: bId,
                similarity: result.similarity,
                distanceMeters: result.distanceMeters,
              },
            });
          }
        }
      }
    }

    // Sort highest confidence first
    candidates.sort((c1, c2) => c2.similarity - c1.similarity);

    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    return {
      candidates,
      status: {
        isScanning: true,
        totalAnalyzed: valid.length,
        potentialMatchesCount: candidates.length,
        lastScanTime: nowStr,
      },
    };
  }

  /**
   * Correlates two incidents across geographic, semantic, category, and temporal signals.
   */
  private static correlatePair(a: any, b: any): { similarity: number; distanceMeters: number | null; timeDiffMinutes: number; reasons: string[] } | null {
    const reasons: string[] = [];
    let score = 0;

    const latA = a.lat ?? a.latitude;
    const lonA = a.lon ?? a.longitude;
    const latB = b.lat ?? b.latitude;
    const lonB = b.lon ?? b.longitude;

    let distanceMeters: number | null = null;

    // 1. Geographic Proximity Signal (Max 42 pts)
    if (latA !== null && lonA !== null && latB !== null && lonB !== null && !isNaN(latA) && !isNaN(latB)) {
      distanceMeters = haversineDistance(latA, lonA, latB, lonB);
      if (distanceMeters <= 100) {
        score += 42;
        reasons.push(`Very close location (${distanceMeters} m apart)`);
      } else if (distanceMeters <= 300) {
        score += 35;
        reasons.push(`Proximity match (${distanceMeters} m apart)`);
      } else if (distanceMeters <= 1000) {
        score += 24;
        reasons.push(`Nearby sector (${distanceMeters} m)`);
      } else if (distanceMeters <= 3000) {
        score += 12;
        reasons.push(`Same municipal zone (${(distanceMeters / 1000).toFixed(1)} km)`);
      } else if (distanceMeters > 8000) {
        score -= 25; // Far apart penalty
      }
    } else {
      // Check shared textual landmark/address tokens if one or both coordinates are missing
      const textLocA = `${a.manualLocation?.address || ''} ${a.manualLocation?.landmark || ''} ${a.summary || ''}`;
      const textLocB = `${b.manualLocation?.address || ''} ${b.manualLocation?.landmark || ''} ${b.summary || ''}`;
      const locOverlap = jaccardSimilarity(tokenize(textLocA), tokenize(textLocB));
      if (locOverlap > 0.25) {
        score += 30;
        reasons.push(`Shared textual landmark or address references`);
      }
    }

    // 2. Semantic Title & Description Overlap (Max 36 pts)
    const textA = `${a.title || ''} ${a.description || a.summary || ''}`;
    const textB = `${b.title || ''} ${b.description || b.summary || ''}`;
    const tokensA = tokenize(textA);
    const tokensB = tokenize(textB);

    const titleA = (a.title || '').toLowerCase();
    const titleB = (b.title || '').toLowerCase();

    // Exact title match or substring
    if (titleA && titleB && (titleA.includes(titleB) || titleB.includes(titleA))) {
      score += 25;
      reasons.push(`Highly aligned incident title`);
    } else {
      const textSim = jaccardSimilarity(tokensA, tokensB);
      if (textSim >= 0.5) {
        score += 32;
        reasons.push(`High lexical similarity (${Math.round(textSim * 100)}% terms matched)`);
      } else if (textSim >= 0.25) {
        score += 20;
        reasons.push(`Significant descriptive overlap (${Math.round(textSim * 100)}%)`);
      } else if (textSim >= 0.15) {
        score += 10;
        reasons.push(`Partial narrative match`);
      }
    }

    // 3. Category Match (Max 14 pts)
    const catA = (a.category || '').toLowerCase().trim();
    const catB = (b.category || '').toLowerCase().trim();
    if (catA && catB && catA === catB) {
      score += 14;
      reasons.push(`Identical emergency category (${catA})`);
    }

    // 4. Severity Compatibility (Max 8 pts)
    const sevA = (a.severity || '').toLowerCase().trim();
    const sevB = (b.severity || '').toLowerCase().trim();
    if (sevA && sevB && sevA === sevB) {
      score += 8;
      reasons.push(`Matching emergency severity (${sevA.toUpperCase()})`);
    }

    // 5. Temporal Proximity (Max 10 pts)
    let timeDiffMinutes = 0;
    try {
      const timeA = new Date(a.timestamp || a.created_at || Date.now()).getTime();
      const timeB = new Date(b.timestamp || b.created_at || Date.now()).getTime();
      if (!isNaN(timeA) && !isNaN(timeB)) {
        timeDiffMinutes = Math.round(Math.abs(timeA - timeB) / 60000);
        if (timeDiffMinutes <= 15) {
          score += 10;
          reasons.push(`Close reporting interval (${timeDiffMinutes} min difference)`);
        } else if (timeDiffMinutes <= 60) {
          score += 5;
          reasons.push(`Reported within 1 hour`);
        }
      }
    } catch {
      // ignore date parse
    }

    const similarity = Math.max(10, Math.min(99, Math.round(score)));

    return {
      similarity,
      distanceMeters,
      timeDiffMinutes,
      reasons,
    };
  }

  /**
   * Dismisses a candidate pair so it will not appear in future scans.
   */
  public static dismissCandidate(pairId: string, actorName = 'Commander') {
    this.dismissedPairs.add(pairId);
    TacticalEventBus.publish({
      type: 'DUPLICATE_MATCH_DISMISSED',
      severity: 'INFO',
      actor: actorName,
      title: 'Duplicate Match Dismissed',
      description: `Correlation candidate (${pairId}) dismissed and marked as separate incident.`,
      metadata: { pairId },
    });
  }

  /**
   * Clears dismissed pairs cache (e.g. for complete rescan).
   */
  public static resetDismissed() {
    this.dismissedPairs.clear();
    this.notifiedCandidateIds.clear();
  }
}
