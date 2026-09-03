import React, {useEffect, useState} from 'react';
import {View, Text, StyleSheet, StatusBar} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {SafeAreaProvider} from 'react-native-safe-area-context';

import ErrorBoundary from './src/components/ErrorBoundary';
import db from './src/db/sqlite';
import IncidentListScreen from './src/screens/IncidentListScreen';
import ReportIncidentScreen from './src/screens/ReportIncidentScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function initStorage() {
      try {
        await db.init();
        if (isMounted) {
          setDbReady(true);
        }
      } catch (err: any) {
        console.error('Local SQLite storage initialization error:', err);
        if (isMounted) {
          setDbError(err.message || 'Storage initialization warning');
        }
      }
    }
    initStorage();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <StatusBar barStyle="light-content" backgroundColor="#0D1B2A" />
        {dbError ? (
          <View style={styles.bannerError}>
            <Text style={styles.bannerErrorText}>⚠️ Local Storage Warning: {dbError}</Text>
          </View>
        ) : null}
        <NavigationContainer>
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
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  bannerError: {
    backgroundColor: '#7A1C24',
    paddingVertical: 6,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  bannerErrorText: {
    color: '#FFD1D1',
    fontSize: 12,
    fontWeight: '600',
  },
});
