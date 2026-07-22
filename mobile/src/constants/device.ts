/**
 * Static device identity constants.
 * In production these are derived from the device's public key fingerprint (Phase 13).
 * For Phase 3, we use a predictable placeholder.
 */
import {Platform} from 'react-native';

export const DEVICE_ID: string =
  `resqmesh-device-${Platform.OS}-${Math.random().toString(36).slice(2, 8)}`;

export const USER_ID: string = 'responder-01';
