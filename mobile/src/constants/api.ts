import { Platform } from 'react-native'

/**
 * Backend base URL for mobile API calls (no trailing slash).
 *
 * Set in mobile/.env (not committed):
 *   EXPO_PUBLIC_API_BASE_URL=http://YOUR_LAN_IP:8000
 *
 * Simulator / emulator defaults (when env is unset):
 * - iOS Simulator: 127.0.0.1 reaches the Mac host running uvicorn.
 * - Android Emulator: 10.0.2.2 is the host loopback alias.
 * - Physical device: you must set EXPO_PUBLIC_API_BASE_URL to your machine's LAN IP;
 *   127.0.0.1 on a phone points at the phone itself, not your laptop.
 *
 * Backend should listen on all interfaces for device testing, e.g.:
 *   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
 */
const DEV_FALLBACK_IOS = 'http://127.0.0.1:8000'
const DEV_FALLBACK_ANDROID = 'http://10.0.2.2:8000'

function devFallbackBaseUrl(): string {
  if (Platform.OS === 'android') return DEV_FALLBACK_ANDROID
  return DEV_FALLBACK_IOS
}

export function getApiBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_BASE_URL?.trim()
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  return devFallbackBaseUrl()
}

export const CHAT_REQUEST_TIMEOUT_MS = 90_000
