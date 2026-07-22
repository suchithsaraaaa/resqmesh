/**
 * ResQMesh Mobile App Entry Point
 * Offline-First Emergency Response Field Tool
 */
import React, {useEffect, useState} from 'react';
import {View, Text, ActivityIndicator, StyleSheet, StatusBar} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import db from './src/db/sqlite';
import IncidentListScreen from './src/screens/IncidentListScreen';
import ReportIncidentScreen from './src/screens/ReportIncidentScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initDb() {
      try {
        await db.init();
        setDbReady(true);
      } catch (err: any) {
        console.error('Failed to initialize local SQLite database:', err);
        setError(err.message || 'Database initialization error');
      }
    }
    initDb();
  }, []);

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>🚨 Database Error</Text>
        <Text style={styles.subText}>{error}</Text>
      </View>
    );
  }

  if (!dbReady) {
    return (
      <View style={styles.center}>
        <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />
        <ActivityIndicator size="large" color="#7DB9DE" />
        <Text style={styles.loadingText}>Initializing Local Storage...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />
      <Stack.Navigator
        initialRouteName="IncidentList"
        screenOptions={{
          headerStyle: {backgroundColor: '#0D1B2A'},
          headerTintColor: '#7DB9DE',
          headerTitleStyle: {fontWeight: '700'},
          contentStyle: {backgroundColor: '#0D1B2A'},
        }}>
        <Stack.Screen
          name="IncidentList"
          component={IncidentListScreen}
          options={{title: 'ResQMesh Field App', headerBackVisible: false}}
        />
        <Stack.Screen
          name="ReportIncident"
          component={ReportIncidentScreen}
          options={{title: 'File Incident Report'}}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    backgroundColor: '#0D1B2A',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    color: '#7DB9DE',
    marginTop: 16,
    fontSize: 14,
    fontWeight: '600',
  },
  errorText: {
    color: '#E63946',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  subText: {
    color: '#5C6B7A',
    fontSize: 14,
    textAlign: 'center',
  },
});
