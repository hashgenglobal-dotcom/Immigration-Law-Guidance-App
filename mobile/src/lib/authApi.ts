import * as SecureStore from 'expo-secure-store'
import { CHAT_REQUEST_TIMEOUT_MS, getApiBaseUrl } from '@/constants/api'
import { STORAGE_KEYS } from '@/constants/auth'

export type AuthUser = {
  id: string
  email: string
  display_name?: string | null
}

export type AuthTokenResponse = {
  status: string
  access_token: string
  token_type: string
  expires_in_minutes: number
  user: AuthUser
}

async function postAuth(path: string, body: object): Promise<AuthTokenResponse> {
  const baseUrl = getApiBaseUrl()
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), CHAT_REQUEST_TIMEOUT_MS)
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const msg =
        typeof data?.detail === 'object' && data.detail?.message
          ? String(data.detail.message)
          : 'Authentication failed.'
      throw new Error(msg)
    }
    return data as AuthTokenResponse
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function registerUser(
  displayName: string,
  email: string,
  password: string,
): Promise<AuthTokenResponse> {
  return postAuth('/api/auth/register', {
    email,
    password,
    display_name: displayName,
  })
}

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  return postAuth('/api/auth/login', { email, password })
}

export async function saveAuthToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(STORAGE_KEYS.accessToken, token)
}

export async function getAuthToken(): Promise<string | null> {
  return SecureStore.getItemAsync(STORAGE_KEYS.accessToken)
}

export async function clearAuthToken(): Promise<void> {
  await SecureStore.deleteItemAsync(STORAGE_KEYS.accessToken)
}
