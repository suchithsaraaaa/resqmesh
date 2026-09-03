/**
 * SQLite local storage service for ResQMesh mobile app.
 * Manages offline persistence for Reports, Incidents, Messages, Resources and SyncAcks.
 *
 * Usage:
 *   import db from './sqlite';
 *   await db.init();
 *   await db.reports.create({ ... });
 */
import SQLite, { SQLiteDatabase, Transaction } from 'react-native-sqlite-storage';

SQLite.enablePromise(true);

let database: SQLiteDatabase | null = null;

const DB_NAME = 'resqmesh.db';

// ─── Schema DDL ──────────────────────────────────────────────────────────────

const DDL = `
CREATE TABLE IF NOT EXISTS operational_incidents (
  incident_id   TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'open',
  severity      TEXT NOT NULL DEFAULT 'medium',
  category      TEXT NOT NULL DEFAULT 'general',
  latitude      REAL NOT NULL DEFAULT 0.0,
  longitude     REAL NOT NULL DEFAULT 0.0,
  summary       TEXT,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  report_id     TEXT PRIMARY KEY,
  incident_id   TEXT REFERENCES operational_incidents(incident_id),
  device_id     TEXT NOT NULL,
  user_id       TEXT NOT NULL,
  timestamp     TEXT NOT NULL,
  latitude      REAL NOT NULL DEFAULT 0.0,
  longitude     REAL NOT NULL DEFAULT 0.0,
  description   TEXT NOT NULL,
  category      TEXT NOT NULL DEFAULT 'general',
  attachments   TEXT,
  device_clock  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
  message_id        TEXT PRIMARY KEY,
  incident_id       TEXT REFERENCES operational_incidents(incident_id),
  sender_device_id  TEXT NOT NULL,
  sender_user_id    TEXT NOT NULL,
  text              TEXT NOT NULL,
  timestamp         TEXT NOT NULL,
  device_clock      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resource_requests (
  resource_id   TEXT PRIMARY KEY,
  incident_id   TEXT REFERENCES operational_incidents(incident_id),
  requester_id  TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  quantity      INTEGER NOT NULL DEFAULT 1,
  urgency       TEXT NOT NULL DEFAULT 'medium',
  status        TEXT NOT NULL DEFAULT 'pending',
  timestamp     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_acks (
  ack_id                TEXT PRIMARY KEY,
  source_device         TEXT NOT NULL,
  target_device         TEXT NOT NULL,
  last_sync_timestamp   TEXT NOT NULL,
  device_clock          INTEGER NOT NULL DEFAULT 0
);
`;

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init(): Promise<void> {
  if (!database) {
    database = await SQLite.openDatabase({ name: DB_NAME, location: 'default' });
  }

  const ddlStatements = [
    `CREATE TABLE IF NOT EXISTS operational_incidents (
      incident_id   TEXT PRIMARY KEY,
      title         TEXT NOT NULL,
      status        TEXT NOT NULL DEFAULT 'open',
      severity      TEXT NOT NULL DEFAULT 'medium',
      category      TEXT NOT NULL DEFAULT 'general',
      latitude      REAL NOT NULL DEFAULT 0.0,
      longitude     REAL NOT NULL DEFAULT 0.0,
      summary       TEXT,
      created_at    TEXT NOT NULL,
      updated_at    TEXT NOT NULL
    );`,
    `CREATE TABLE IF NOT EXISTS reports (
      report_id     TEXT PRIMARY KEY,
      incident_id   TEXT REFERENCES operational_incidents(incident_id),
      device_id     TEXT NOT NULL,
      user_id       TEXT NOT NULL,
      timestamp     TEXT NOT NULL,
      latitude      REAL NOT NULL DEFAULT 0.0,
      longitude     REAL NOT NULL DEFAULT 0.0,
      description   TEXT NOT NULL,
      category      TEXT NOT NULL DEFAULT 'general',
      attachments   TEXT,
      device_clock  INTEGER NOT NULL DEFAULT 0
    );`,
    `CREATE TABLE IF NOT EXISTS chat_messages (
      message_id        TEXT PRIMARY KEY,
      incident_id       TEXT REFERENCES operational_incidents(incident_id),
      sender_device_id  TEXT NOT NULL,
      sender_user_id    TEXT NOT NULL,
      text              TEXT NOT NULL,
      timestamp         TEXT NOT NULL,
      device_clock      INTEGER NOT NULL DEFAULT 0
    );`,
    `CREATE TABLE IF NOT EXISTS resource_requests (
      resource_id   TEXT PRIMARY KEY,
      incident_id   TEXT REFERENCES operational_incidents(incident_id),
      requester_id  TEXT NOT NULL,
      resource_type TEXT NOT NULL,
      quantity      INTEGER NOT NULL DEFAULT 1,
      urgency       TEXT NOT NULL DEFAULT 'medium',
      status        TEXT NOT NULL DEFAULT 'pending',
      timestamp     TEXT NOT NULL
    );`,
    `CREATE TABLE IF NOT EXISTS sync_acks (
      ack_id                TEXT PRIMARY KEY,
      source_device         TEXT NOT NULL,
      target_device         TEXT NOT NULL,
      last_sync_timestamp   TEXT NOT NULL,
      device_clock          INTEGER NOT NULL DEFAULT 0
    );`,
  ];

  for (const stmt of ddlStatements) {
    try {
      await database.executeSql(stmt, []);
    } catch (err) {
      console.warn('DDL statement execution warning:', err, stmt);
    }
  }
}

function getDb(): SQLiteDatabase {
  if (!database) {
    throw new Error('Database not initialized. Call db.init() first.');
  }
  return database;
}

// ─── Reports ──────────────────────────────────────────────────────────────────

type CreateReportInput = {
  report_id: string;
  incident_id?: string | null;
  device_id: string;
  user_id: string;
  latitude: number;
  longitude: number;
  description: string;
  category: string;
  attachments?: string | null;
  device_clock: number;
};

async function createReport(input: CreateReportInput): Promise<void> {
  const dbInstance = getDb();
  const now = new Date().toISOString();
  await dbInstance.executeSql(
    `INSERT INTO reports
     (report_id, incident_id, device_id, user_id, timestamp, latitude, longitude,
      description, category, attachments, device_clock)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      input.report_id || `report-${Date.now()}`,
      input.incident_id ?? null,
      input.device_id || 'unknown-device',
      input.user_id || 'unknown-user',
      now,
      typeof input.latitude === 'number' && !isNaN(input.latitude) ? input.latitude : 0.0,
      typeof input.longitude === 'number' && !isNaN(input.longitude) ? input.longitude : 0.0,
      input.description || '',
      input.category || 'general',
      input.attachments ?? null,
      typeof input.device_clock === 'number' ? input.device_clock : Date.now(),
    ],
  );
}

async function getReports(incident_id?: string): Promise<any[]> {
  const db = getDb();
  const [result] = incident_id
    ? await db.executeSql('SELECT * FROM reports WHERE incident_id = ? ORDER BY timestamp DESC', [incident_id])
    : await db.executeSql('SELECT * FROM reports ORDER BY timestamp DESC');
  const rows: any[] = [];
  for (let i = 0; i < result.rows.length; i++) {
    rows.push(result.rows.item(i));
  }
  return rows;
}

// ─── Operational Incidents ────────────────────────────────────────────────────

type CreateIncidentInput = {
  incident_id: string;
  title: string;
  status?: string;
  severity?: string;
  category?: string;
  latitude?: number;
  longitude?: number;
  summary?: string | null;
};

async function createIncident(input: CreateIncidentInput): Promise<void> {
  const db = getDb();
  const now = new Date().toISOString();
  await db.executeSql(
    `INSERT INTO operational_incidents
     (incident_id, title, status, severity, category, latitude, longitude, summary, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      input.incident_id,
      input.title,
      input.status ?? 'open',
      input.severity ?? 'medium',
      input.category ?? 'general',
      input.latitude ?? 0.0,
      input.longitude ?? 0.0,
      input.summary ?? null,
      now,
      now,
    ],
  );
}

async function getIncidents(): Promise<any[]> {
  const db = getDb();
  const [result] = await db.executeSql(
    'SELECT * FROM operational_incidents ORDER BY created_at DESC',
  );
  const rows: any[] = [];
  for (let i = 0; i < result.rows.length; i++) {
    rows.push(result.rows.item(i));
  }
  return rows;
}

async function getIncidentById(incident_id: string): Promise<any | null> {
  const db = getDb();
  const [result] = await db.executeSql(
    'SELECT * FROM operational_incidents WHERE incident_id = ?',
    [incident_id],
  );
  if (result.rows.length === 0) {
    return null;
  }
  return result.rows.item(0);
}

// ─── Chat Messages ────────────────────────────────────────────────────────────

type CreateMessageInput = {
  message_id: string;
  incident_id?: string | null;
  sender_device_id: string;
  sender_user_id: string;
  text: string;
  device_clock: number;
};

async function createMessage(input: CreateMessageInput): Promise<void> {
  const db = getDb();
  const now = new Date().toISOString();
  await db.executeSql(
    `INSERT INTO chat_messages
     (message_id, incident_id, sender_device_id, sender_user_id, text, timestamp, device_clock)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [
      input.message_id,
      input.incident_id ?? null,
      input.sender_device_id,
      input.sender_user_id,
      input.text,
      now,
      input.device_clock,
    ],
  );
}

async function getMessages(incident_id?: string): Promise<any[]> {
  const db = getDb();
  const [result] = incident_id
    ? await db.executeSql('SELECT * FROM chat_messages WHERE incident_id = ? ORDER BY timestamp ASC', [incident_id])
    : await db.executeSql('SELECT * FROM chat_messages ORDER BY timestamp ASC');
  const rows: any[] = [];
  for (let i = 0; i < result.rows.length; i++) {
    rows.push(result.rows.item(i));
  }
  return rows;
}

// ─── Sync Acks ────────────────────────────────────────────────────────────────

async function upsertSyncAck(
  ack_id: string,
  source_device: string,
  target_device: string,
  device_clock: number,
): Promise<void> {
  const db = getDb();
  const now = new Date().toISOString();
  await db.executeSql(
    `INSERT OR REPLACE INTO sync_acks
     (ack_id, source_device, target_device, last_sync_timestamp, device_clock)
     VALUES (?, ?, ?, ?, ?)`,
    [ack_id, source_device, target_device, now, device_clock],
  );
}

// ─── Export ───────────────────────────────────────────────────────────────────

const db = {
  init,
  reports: { create: createReport, list: getReports },
  incidents: {
    create: createIncident,
    list: getIncidents,
    getById: getIncidentById,
  },
  messages: { create: createMessage, list: getMessages },
  syncAcks: { upsert: upsertSyncAck },
};

export default db;
