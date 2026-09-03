/**
 * Incident List screen — shows all locally stored field reports.
 * Pulls from local SQLite; no network required.
 */
import React, {useState, useCallback} from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  RefreshControl,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import db from '../db/sqlite';

const SEVERITY_COLORS: Record<string, string> = {
  low: '#4CAF50',
  medium: '#FF9800',
  high: '#F44336',
  critical: '#9C27B0',
};

const CATEGORY_ICONS: Record<string, string> = {
  fire: '🔥',
  flood: '🌊',
  structural: '🏚️',
  medical: '🏥',
  chemical: '☣️',
  general: '⚠️',
};

interface Props {
  navigation: any;
}

export default function IncidentListScreen({navigation}: Props) {
  const [reports, setReports] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadReports = useCallback(async () => {
    try {
      const data = await db.reports.list();
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadReports();
    }, [loadReports]),
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await loadReports();
    setRefreshing(false);
  };

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const renderItem = ({item}: {item: any}) => {
    const cat = item?.category ?? 'general';
    const sev = item?.severity ?? 'medium';
    return (
      <TouchableOpacity style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryIcon}>
              {CATEGORY_ICONS[cat] ?? '⚠️'}
            </Text>
            <Text style={styles.categoryText}>
              {cat.toUpperCase()}
            </Text>
          </View>
          <View
            style={[
              styles.severityDot,
              {backgroundColor: SEVERITY_COLORS[sev] ?? '#FF9800'},
            ]}
          />
        </View>

      <Text style={styles.description} numberOfLines={3}>
        {item.description}
      </Text>

      <View style={styles.metaRow}>
        <Text style={styles.metaText}>📱 {item.device_id}</Text>
        <Text style={styles.metaText}>🕐 {formatTime(item.timestamp)}</Text>
      </View>

      {item.latitude !== 0 || item.longitude !== 0 ? (
        <Text style={styles.gpsText}>
          📍 {Number(item.latitude).toFixed(4)}, {Number(item.longitude).toFixed(4)}
        </Text>
      ) : null}

      {item.incident_id ? (
        <View style={styles.linkedBadge}>
          <Text style={styles.linkedText}>✓ Linked to Incident</Text>
        </View>
      ) : (
        <View style={styles.unlinkedBadge}>
          <Text style={styles.unlinkedText}>⏳ Awaiting Correlation</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />

      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Field Reports</Text>
          <Text style={styles.headerSub}>{reports.length} report(s) stored locally</Text>
        </View>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate('ReportIncident')}>
          <Text style={styles.addBtnText}>+ Report</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={reports}
        keyExtractor={item => item.report_id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#7DB9DE"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📋</Text>
            <Text style={styles.emptyTitle}>No Reports Yet</Text>
            <Text style={styles.emptySubtitle}>
              Tap "+ Report" to file your first incident report. It will be saved
              offline and synced to nearby peers automatically.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {backgroundColor: '#0D1B2A', flex: 1},
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E3050',
  },
  headerTitle: {fontSize: 22, fontWeight: '700', color: '#E8F4FD'},
  headerSub: {fontSize: 12, color: '#5C6B7A', marginTop: 2},
  addBtn: {
    backgroundColor: '#E63946',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  addBtnText: {color: '#fff', fontWeight: '700', fontSize: 14},
  listContent: {padding: 16, gap: 12},
  card: {
    backgroundColor: '#152131',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E3050',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  categoryBadge: {flexDirection: 'row', alignItems: 'center', gap: 6},
  categoryIcon: {fontSize: 16},
  categoryText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7DB9DE',
    letterSpacing: 1,
  },
  severityDot: {width: 12, height: 12, borderRadius: 6},
  description: {color: '#C9DCE8', fontSize: 14, lineHeight: 20, marginBottom: 10},
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  metaText: {color: '#5C6B7A', fontSize: 11},
  gpsText: {color: '#5C6B7A', fontSize: 11, marginBottom: 8},
  linkedBadge: {
    backgroundColor: '#1A3A1A',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  linkedText: {color: '#4CAF50', fontSize: 11, fontWeight: '600'},
  unlinkedBadge: {
    backgroundColor: '#2A2A1A',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  unlinkedText: {color: '#FF9800', fontSize: 11, fontWeight: '600'},
  emptyContainer: {alignItems: 'center', paddingTop: 80, paddingHorizontal: 32},
  emptyIcon: {fontSize: 48, marginBottom: 16},
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#E8F4FD',
    marginBottom: 12,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#5C6B7A',
    textAlign: 'center',
    lineHeight: 20,
  },
});
