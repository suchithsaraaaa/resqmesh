/**
 * Incident Report submission screen.
 * Field responders use this to record an emergency sighting.
 * Data is persisted locally to SQLite immediately (offline-first).
 */
import React, {useState} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  StatusBar,
} from 'react-native';
import 'react-native-get-random-values';
import {v4 as uuidv4} from 'uuid';
import db from '../db/sqlite';
import {DEVICE_ID, USER_ID} from '../constants/device';

const CATEGORIES = ['fire', 'flood', 'structural', 'medical', 'chemical', 'general'];
const SEVERITIES: Array<{label: string; value: string; color: string}> = [
  {label: 'Low', value: 'low', color: '#4CAF50'},
  {label: 'Medium', value: 'medium', color: '#FF9800'},
  {label: 'High', value: 'high', color: '#F44336'},
  {label: 'Critical', value: 'critical', color: '#9C27B0'},
];

const MOBILE_LANDMARKS = [
  {id: 'majestic', name: 'Majestic Transit Hub', lat: 12.9767, lng: 77.5713},
  {id: 'mg_road', name: 'MG Road Metro', lat: 12.9756, lng: 77.6066},
  {id: 'koramangala', name: 'Koramangala 5th Block', lat: 12.9352, lng: 77.6245},
  {id: 'indiranagar', name: 'Indiranagar 100ft Rd', lat: 12.9784, lng: 77.6408},
  {id: 'whitefield', name: 'Whitefield ITPL', lat: 12.9863, lng: 77.7302},
  {id: 'hebbal', name: 'Hebbal Flyover', lat: 13.0358, lng: 77.5970},
  {id: 'elec_city', name: 'Electronic City Toll', lat: 12.8452, lng: 77.6602},
  {id: 'sector_4', name: 'Sector 4 Warehouse', lat: 12.9716, lng: 77.5946},
  {id: 'hospital', name: 'City Civil Hospital', lat: 12.9650, lng: 77.5880},
  {id: 'custom', name: 'Other / Custom Landmark', lat: 12.9716, lng: 77.5946},
];

interface Props {
  navigation: any;
}

export default function ReportIncidentScreen({navigation}: Props) {
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [severity, setSeverity] = useState('medium');
  const [selectedLandmark, setSelectedLandmark] = useState('majestic');
  const [landmarkDetail, setLandmarkDetail] = useState('');
  const [latitude, setLatitude] = useState('12.9767');
  const [longitude, setLongitude] = useState('77.5713');
  const [loading, setLoading] = useState(false);

  const handleLandmarkSelect = (id: string) => {
    setSelectedLandmark(id);
    const lm = MOBILE_LANDMARKS.find(l => l.id === id);
    if (lm && id !== 'custom') {
      setLatitude(String(lm.lat));
      setLongitude(String(lm.lng));
    }
  };

  const handleSubmit = async () => {
    if (!description.trim()) {
      Alert.alert('Missing Information', 'Please enter an incident description.');
      return;
    }

    setLoading(true);
    try {
      const reportId = uuidv4();
      await db.reports.create({
        report_id: reportId,
        device_id: DEVICE_ID,
        user_id: USER_ID,
        latitude: parseFloat(latitude) || 0.0,
        longitude: parseFloat(longitude) || 0.0,
        description: description.trim(),
        category,
        attachments: null,
        device_clock: Date.now(),
      });

      Alert.alert(
        'Report Submitted',
        'Your incident report has been saved locally and will sync when peers are available.',
        [
          {
            text: 'OK',
            onPress: () => {
              setDescription('');
              setCategory('general');
              setSeverity('medium');
              setLatitude('');
              setLongitude('');
              navigation.navigate('IncidentList');
            },
          },
        ],
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to save report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>🚨 Report Incident</Text>
        <Text style={styles.headerSub}>Saved offline — syncs automatically</Text>
      </View>

      {/* Description */}
      <View style={styles.card}>
        <Text style={styles.label}>Description *</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Describe what you see..."
          placeholderTextColor="#5C6B7A"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
        />
      </View>

      {/* Category */}
      <View style={styles.card}>
        <Text style={styles.label}>Incident Category</Text>
        <View style={styles.chipRow}>
          {CATEGORIES.map(cat => (
            <TouchableOpacity
              key={cat}
              style={[styles.chip, category === cat && styles.chipActive]}
              onPress={() => setCategory(cat)}>
              <Text
                style={[styles.chipText, category === cat && styles.chipTextActive]}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Severity */}
      <View style={styles.card}>
        <Text style={styles.label}>Severity</Text>
        <View style={styles.severityRow}>
          {SEVERITIES.map(s => (
            <TouchableOpacity
              key={s.value}
              style={[
                styles.severityBtn,
                severity === s.value && {
                  backgroundColor: s.color,
                  borderColor: s.color,
                },
              ]}
              onPress={() => setSeverity(s.value)}>
              <Text
                style={[
                  styles.severityText,
                  severity === s.value && styles.severityTextActive,
                ]}>
                {s.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Locality & Landmarks */}
      <View style={styles.card}>
        <Text style={styles.label}>📍 Locality / Landmark Sector</Text>
        <View style={styles.chipRow}>
          {MOBILE_LANDMARKS.map(lm => (
            <TouchableOpacity
              key={lm.id}
              style={[styles.chip, selectedLandmark === lm.id && styles.chipActive]}
              onPress={() => handleLandmarkSelect(lm.id)}>
              <Text
                style={[
                  styles.chipText,
                  selectedLandmark === lm.id && styles.chipTextActive,
                ]}>
                {lm.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TextInput
          style={[styles.input, {marginTop: 10}]}
          placeholder="Specific landmark / street details (e.g. Near Gate 2)"
          placeholderTextColor="#5C6B7A"
          value={landmarkDetail}
          onChangeText={setLandmarkDetail}
        />
      </View>

      {/* GPS (Optional / Advanced) */}
      <View style={styles.card}>
        <Text style={styles.label}>GPS Coordinates (Auto-filled from landmark)</Text>
        <View style={styles.gpsRow}>
          <TextInput
            style={[styles.input, styles.gpsInput]}
            placeholder="Latitude"
            placeholderTextColor="#5C6B7A"
            keyboardType="numeric"
            value={latitude}
            onChangeText={setLatitude}
          />
          <TextInput
            style={[styles.input, styles.gpsInput]}
            placeholder="Longitude"
            placeholderTextColor="#5C6B7A"
            keyboardType="numeric"
            value={longitude}
            onChangeText={setLongitude}
          />
        </View>
      </View>

      <TouchableOpacity
        style={[styles.submitBtn, loading && styles.submitBtnDisabled]}
        onPress={handleSubmit}
        disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitText}>Submit Report</Text>
        )}
      </TouchableOpacity>

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {backgroundColor: '#0D1B2A', flex: 1},
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E3050',
  },
  headerTitle: {fontSize: 24, fontWeight: '700', color: '#E8F4FD'},
  headerSub: {fontSize: 13, color: '#5C6B7A', marginTop: 4},
  card: {
    backgroundColor: '#152131',
    borderRadius: 12,
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E3050',
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#7DB9DE',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  textArea: {
    color: '#E8F4FD',
    fontSize: 15,
    minHeight: 100,
    lineHeight: 22,
  },
  input: {
    color: '#E8F4FD',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#1E3050',
    borderRadius: 8,
    padding: 10,
  },
  chipRow: {flexDirection: 'row', flexWrap: 'wrap', gap: 8},
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#1E3050',
    backgroundColor: '#0D1B2A',
  },
  chipActive: {borderColor: '#4A90D9', backgroundColor: '#1A3A5C'},
  chipText: {color: '#5C6B7A', fontSize: 13},
  chipTextActive: {color: '#7DB9DE', fontWeight: '600'},
  severityRow: {flexDirection: 'row', gap: 8},
  severityBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1E3050',
    alignItems: 'center',
  },
  severityText: {color: '#5C6B7A', fontSize: 13, fontWeight: '600'},
  severityTextActive: {color: '#fff'},
  gpsRow: {flexDirection: 'row', gap: 10},
  gpsInput: {flex: 1},
  submitBtn: {
    backgroundColor: '#E63946',
    marginHorizontal: 16,
    marginTop: 24,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  submitBtnDisabled: {backgroundColor: '#7A1C24'},
  submitText: {color: '#fff', fontSize: 16, fontWeight: '700'},
  bottomSpacer: {height: 40},
});
