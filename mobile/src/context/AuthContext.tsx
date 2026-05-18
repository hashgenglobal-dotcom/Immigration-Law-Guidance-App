import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { GUEST_CHAT_LIMIT, STORAGE_KEYS } from '@/constants/auth'
import type { AppSession, GuestSession, UserSession } from '@/types/auth'

type AuthContextValue = {
  isReady: boolean
  onboardingComplete: boolean
  session: AppSession | null
  isGuest: boolean
  isUser: boolean
  guestChatsRemaining: number
  canSendGuestChat: boolean
  completeOnboarding: () => Promise<void>
  signInAsGuest: () => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signUp: (displayName: string, email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  recordGuestChat: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function readOnboarding(): Promise<boolean> {
  const v = await AsyncStorage.getItem(STORAGE_KEYS.onboardingComplete)
  return v === 'true'
}

async function readSession(): Promise<AppSession | null> {
  const raw = await AsyncStorage.getItem(STORAGE_KEYS.session)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AppSession
  } catch {
    return null
  }
}

async function persistSession(session: AppSession | null) {
  if (!session) {
    await AsyncStorage.removeItem(STORAGE_KEYS.session)
    return
  }
  await AsyncStorage.setItem(STORAGE_KEYS.session, JSON.stringify(session))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false)
  const [onboardingComplete, setOnboardingComplete] = useState(false)
  const [session, setSession] = useState<AppSession | null>(null)

  useEffect(() => {
    let mounted = true
    ;(async () => {
      const [onboarded, stored] = await Promise.all([readOnboarding(), readSession()])
      if (!mounted) return
      setOnboardingComplete(onboarded)
      setSession(stored)
      setIsReady(true)
    })()
    return () => {
      mounted = false
    }
  }, [])

  const completeOnboarding = useCallback(async () => {
    await AsyncStorage.setItem(STORAGE_KEYS.onboardingComplete, 'true')
    setOnboardingComplete(true)
  }, [])

  const signInAsGuest = useCallback(async () => {
    const guest: GuestSession = { mode: 'guest', guestChatsUsed: 0 }
    await persistSession(guest)
    setSession(guest)
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const trimmed = email.trim().toLowerCase()
    if (!trimmed || password.length < 6) {
      throw new Error('Enter a valid email and password (6+ characters).')
    }
    const user: UserSession = {
      mode: 'user',
      email: trimmed,
      displayName: trimmed.split('@')[0] ?? 'Member',
    }
    await persistSession(user)
    setSession(user)
  }, [])

  const signUp = useCallback(async (displayName: string, email: string, password: string) => {
    const name = displayName.trim()
    const trimmed = email.trim().toLowerCase()
    if (!name || !trimmed || password.length < 6) {
      throw new Error('Fill in all fields. Password must be at least 6 characters.')
    }
    const user: UserSession = { mode: 'user', email: trimmed, displayName: name }
    await persistSession(user)
    setSession(user)
  }, [])

  const signOut = useCallback(async () => {
    await persistSession(null)
    setSession(null)
  }, [])

  const recordGuestChat = useCallback(async (): Promise<boolean> => {
    if (!session || session.mode !== 'guest') return true
    if (session.guestChatsUsed >= GUEST_CHAT_LIMIT) return false
    const next: GuestSession = {
      mode: 'guest',
      guestChatsUsed: session.guestChatsUsed + 1,
    }
    await persistSession(next)
    setSession(next)
    return true
  }, [session])

  const guestChatsRemaining = useMemo(() => {
    if (!session || session.mode !== 'guest') return GUEST_CHAT_LIMIT
    return Math.max(0, GUEST_CHAT_LIMIT - session.guestChatsUsed)
  }, [session])

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      onboardingComplete,
      session,
      isGuest: session?.mode === 'guest',
      isUser: session?.mode === 'user',
      guestChatsRemaining,
      canSendGuestChat: session?.mode !== 'guest' || guestChatsRemaining > 0,
      completeOnboarding,
      signInAsGuest,
      signIn,
      signUp,
      signOut,
      recordGuestChat,
    }),
    [
      isReady,
      onboardingComplete,
      session,
      guestChatsRemaining,
      completeOnboarding,
      signInAsGuest,
      signIn,
      signUp,
      signOut,
      recordGuestChat,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
