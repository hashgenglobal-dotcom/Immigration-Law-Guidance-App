export type AuthMode = 'guest' | 'user'

/** In-memory preview only — no email or display name stored */
export type UserSession = {
  mode: 'user'
}

export type GuestSession = {
  mode: 'guest'
  guestChatsUsed: number
}

export type AppSession = UserSession | GuestSession
